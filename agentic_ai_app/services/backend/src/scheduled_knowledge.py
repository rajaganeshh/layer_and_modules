import sys
# sys.path.append("/bin/day0-knowledge/presidio/python")
import os
import io
import re
import json
import boto3
import threading
import requests
import urllib3
import psycopg2
import psycopg2.extras
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from time import perf_counter
from botocore.exceptions import ClientError
from summarize import summarize_text
import time
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine
import spacy
import logging


class LoadedSpacyNlpEngine(SpacyNlpEngine):
    def __init__(self, loaded_spacy_model):
        super().__init__()
        self.nlp = {"en": loaded_spacy_model}

# Load a model a-priori
nlp = spacy.load("./en_core_web_md-3.8.0")

# Pass the loaded model to the new LoadedSpacyNlpEngine
loaded_nlp_engine = LoadedSpacyNlpEngine(loaded_spacy_model = nlp)


analyzer = AnalyzerEngine(nlp_engine = loaded_nlp_engine)



# ====================== LOGGER ============================



logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove any existing handlers (especially Lambda-style ones)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add a StreamHandler that prints to the console (stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Console logging initialized ")

http = urllib3.PoolManager(num_pools=10, maxsize=10, block=True)

# ====================== SECRETS ============================
secret_name = os.environ.get("secret_name", "")
region_name_env = os.environ.get("region_name", "")

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.exception("Unable to fetch secret")
        raise e
    secret = json.loads(get_secret_value_response["SecretString"])
    configPythonSecrets = json.loads(secret["configPythonSecrets"])
    return configPythonSecrets

configPythonSecrets = get_secret(secret_name, region_name_env)

# ----------------- Extract secrets -----------------
region_name = configPythonSecrets["awsRegion"]

# DB
db_host = configPythonSecrets["database"]["host"]
db_port = configPythonSecrets["database"]["port"]
db_name = configPythonSecrets["database"]["name"]
db_user = configPythonSecrets["database"]["user"]
db_password = configPythonSecrets["database"]["password"]

# Bedrock
llm_model = configPythonSecrets["bedrock"]["llm"]
embedding_model = configPythonSecrets["bedrock"]["embedding"]

# ServiceNow
sn_client_id = configPythonSecrets["serviceNow"]["clientId"]
sn_client_secret = configPythonSecrets["serviceNow"]["clientSecret"]
sn_token_url = configPythonSecrets["serviceNow"]["tokenUrl"]
sn_base_url = configPythonSecrets["serviceNow"]["baseUrl"]

# Confluence
conf_user = configPythonSecrets["confluence"]["user"]
conf_token = configPythonSecrets["confluence"]["token"]
conf_url=configPythonSecrets["confluence"]["url"]

# ====================== UTILITIES ============================
#---------------------html to text----------
def html_to_text(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split())

#------------------------mask pii (regex-based similar to Day0)---------------------

def mask_pii(text: str) -> str:
    if not text:
        return text

    # Mask Names using Presidio
    results = analyzer.analyze(text=text, entities=["PERSON"], language="en")
    #Sort by start index descending to avoid shifting issues
    results = sorted(results, key=lambda x: x.start, reverse=True)
    for r in results:
        start, end = r.start, r.end
        text = text[:start] + "[NAME_REDACTED]" + text[end:]

    # Step 2: Mask Emails using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    text = re.sub(email_pattern, "[EMAIL_REDACTED]", text)

    # Step 3: Mask Phone Numbers only if + followed by >7 digits
    phone_pattern = r"\+\d{8,}[\d\s\-\(\)]*"
    text = re.sub(phone_pattern, "[PHONE_REDACTED]", text)

    return text




#----------------------Embedding (Day0 unified)-----------------------
MAX_CHARS = 8000
OVERLAP = 500

def chunk_text(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    if not text:
        return []
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + max_chars, text_length)
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks

def _get_embeddings_single(model_id, input_text):
    if not input_text:
        return []
    client = boto3.client("bedrock-runtime", region_name=region_name)
    chunks = chunk_text(input_text)
    chunk_embeddings = []
    for chunk in chunks:
        req = json.dumps({"inputText": chunk})
        resp = client.invoke_model(modelId=model_id, body=req)
        model_response = json.loads(resp["body"].read())
        emb = model_response.get("embedding")
        if emb:
            chunk_embeddings.append(emb)
    if not chunk_embeddings:
        return []
    return np.mean(chunk_embeddings, axis=0).tolist()

def generate_embeddings(text):
    return _get_embeddings_single(embedding_model, text)

#============= DB insert & upsert/update ======================
def insert_knowledge_vec(data, db_config, update_mode=False):
    """
    Batched insert/update into knowledge_vec (no ON CONFLICT constraint required).
    Thread-safe for multi-threaded ingestion.
    Prevents duplicates by checking (knowledge_id, source) before insert.
    """
    if not data:
        logger.info("No records to insert/update.")
        return

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Step 1: Deduplicate data within this batch
        unique_records = {}
        for record in data:
            key = (record["knowledge_id"], record["source"].lower())
            unique_records[key] = record  # latest wins

        data = list(unique_records.values())

        # Step 2: For each record — update if exists, else insert
        inserted, updated = 0, 0
        for record in data:
            try:
                cursor.execute(
                    """
                    SELECT 1 FROM knowledge_vec
                    WHERE knowledge_id = %s AND LOWER(source) = LOWER(%s)
                    """,
                    (record["knowledge_id"], record["source"]),
                )
                exists = cursor.fetchone() is not None

                if exists:
                    cursor.execute(
                        """
                        UPDATE knowledge_vec
                        SET ci = %s,
                            chunk = %s,
                            embedding = %s,
                            knowledge_type = %s,
                            link = %s,
                            summary = %s
                        WHERE knowledge_id = %s AND LOWER(source) = LOWER(%s)
                        """,
                        (
                            record["ci"], record["chunk"], record["embedding"],
                            record["knowledge_type"], record["link"], record["summary"],
                            record["knowledge_id"], record["source"],
                        ),
                    )
                    updated += 1
                else:
                    cursor.execute(
                        """
                        INSERT INTO knowledge_vec (
                            ci, chunk, embedding, knowledge_id, knowledge_type, source, link, summary
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            record["ci"], record["chunk"], record["embedding"],
                            record["knowledge_id"], record["knowledge_type"],
                            record["source"], record["link"], record["summary"],
                        ),
                    )
                    inserted += 1

            except Exception as e:
                logger.error(f"Insert/Update failed for {record.get('source')}:{record.get('knowledge_id')} - {e}")
                continue

        conn.commit()
        logger.info(f"Batch processed: {inserted} inserted, {updated} updated (mode={'update' if update_mode else 'insert'})")

    except Exception as e:
        logger.exception(f"Error inserting/updating data: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#-----------------Config Function --------------------------
def update_ci_from_config_secret(db_config, configPythonSecrets, overwrite_existing=False):
    """
    Updates the 'ci' column in knowledge_vec for SharePoint and Confluence,
    based on URLs provided in the 'config' section of Secrets Manager.

    For Confluence:
        - Extracts the page ID from the URL (segment after '/pages/')
        - Fetches all descendant *pages only* and updates CI for them
        - Logs any URL whose ID is not found in the DB

    For SharePoint:
        - Matches the provided link directly in the DB (column 'link')
        - If the link exists, updates CI; otherwise logs missing link
    """

    try:
        config_section = configPythonSecrets.get("config", {})
        if not config_section:
            logger.warning("No 'config' section found in Secrets Manager data.")
            return

        # Confluence credentials (for descendant fetch)
        conf_user = configPythonSecrets["confluence"]["user"]
        conf_token = configPythonSecrets["confluence"]["token"]

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        total_updates = 0
        total_missing = 0

        for source, ci_map in config_section.items():
            if source not in ["confluence"]: #, "sharePoint"
                logger.debug(f"Skipping unsupported source: {source}")
                continue

            logger.info(f"Processing CI updates for source: {source}")

            for ci_name, url_list in ci_map.items():
                if not url_list:
                    continue

                logger.info(f"  Updating CI '{ci_name}' for {len(url_list)} URLs in '{source}'")

                for link in url_list:
                    try:
                        # ================== CONFLUENCE ==================
                        if source == "confluence":
                            # Extract page ID from URL (pattern: .../pages/{id}/...)
                            match = re.search(r"/pages/(\d+)", link)
                            if not match:
                                logger.warning(f"Invalid Confluence URL (no ID found): {link}")
                                total_missing += 1
                                continue

                            page_id = match.group(1)
                            base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
                            url = f"{base_api}/rest/api/content/{page_id}/descendant/page"
                            descendants = []

                            logger.info(f"Fetching descendant pages for Confluence parent {page_id}...")

                            while url:
                                resp = requests.get(url, auth=(conf_user, conf_token))
                                if resp.status_code != 200:
                                    logger.warning(f"Failed to fetch descendants for {page_id}: {resp.status_code} - {resp.text}")
                                    break

                                data = resp.json()
                                results = data.get("results", [])
                                for r in results:
                                    if r.get("type") == "page" and r.get("id"):
                                        descendants.append(r["id"])

                                next_link = (data.get("_links") or {}).get("next")
                                url = base_api + next_link if next_link else None

                            # Include parent page too
                            all_ids = [page_id] + descendants
                            logger.info(f"  Changing CI for Confluence parent {page_id} and {len(descendants)} descendant pages.")

                            updated_any = False
                            for pid in all_ids:
                                
                                cursor.execute(
                                    """
                                    UPDATE knowledge_vec
                                    SET ci = %s
                                    WHERE knowledge_id = %s::text
                                      AND source ILIKE 'Confluence'
                                    """,
                                    (ci_name, str(pid))
                                )
                                

                                if cursor.rowcount > 0:
                                    total_updates += cursor.rowcount
                                    updated_any = True

                            if not updated_any:
                                logger.warning(f"Confluence page ID {page_id} (from link {link}) not found in DB.")
                                total_missing += 1

                        
                    except Exception as e:
                        logger.warning(f"Error updating CI for {source}:{link} ({ci_name}): {e}")
                        continue

        conn.commit()
        logger.info(f"CI update from secret config completed. Total records updated: {total_updates}, Missing links/IDs: {total_missing}")

    except Exception as e:
        logger.exception(f"Error in CI update pipeline: {e}")
        raise

    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

# ====================== SERVICENOW  ============================
def get_access_token_sn():
    data = {
        "grant_type": "client_credentials",
        "client_id": sn_client_id,
        "client_secret": sn_client_secret,
    }
    resp = http.request("POST", sn_token_url, body=urlencode(data), headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status == 200:
        token_data = json.loads(resp.data.decode("utf-8"))
        return token_data["access_token"]
    else:
        raise Exception(f"Failed to get access token: {resp.status} - {resp.data}")

# Fetch created (created in last 24h)
def get_sn_articles_created_24h(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    sysparm_query = f"sys_created_on>=javascript:gs.hoursAgo(24)^workflow_state=published"
    params = {
        "sysparm_query": sysparm_query,
        "sysparm_display_value": "true",
        "sysparm_limit": 100,
        "sysparm_offset": 0,
    }
    all_articles = []
    total_fetched = 0
    while True:
        resp = http.request("GET", f"{sn_base_url}/api/now/table/kb_knowledge", headers=headers, fields=params)
        if resp.status != 200:
            raise Exception(f"Failed to fetch knowledge articles (created): {resp.status} - {resp.data}")
        data = json.loads(resp.data.decode("utf-8"))
        results = data.get("result", [])
        if not results:
            break
        all_articles.extend(results)
        total_fetched += len(results)
        logger.info(f"Fetched {len(results)} ServiceNow created articles (total {total_fetched})")
        if len(results) < params["sysparm_limit"]:
            break
        params["sysparm_offset"] += params["sysparm_limit"]
        if total_fetched >= 50000:
            logger.warning("Reached maximum fetch limit of 50000 records")
            break
    logger.info(f"Total ServiceNow created articles fetched (24h): {len(all_articles)}")
    return all_articles

# Fetch updated (modified in last 24h)
def get_sn_articles_updated_24h(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    sysparm_query = f"sys_updated_on>=javascript:gs.hoursAgo(24)^workflow_state=published"
    params = {
        "sysparm_query": sysparm_query,
        "sysparm_display_value": "true",
        "sysparm_limit": 100,
        "sysparm_offset": 0,
    }
    all_articles = []
    total_fetched = 0
    while True:
        resp = http.request("GET", f"{sn_base_url}/api/now/table/kb_knowledge", headers=headers, fields=params)
        if resp.status != 200:
            raise Exception(f"Failed to fetch knowledge articles (updated): {resp.status} - {resp.data}")
        data = json.loads(resp.data.decode("utf-8"))
        results = data.get("result", [])
        if not results:
            break
        all_articles.extend(results)
        total_fetched += len(results)
        logger.info(f"Fetched {len(results)} ServiceNow updated articles (total {total_fetched})")
        if len(results) < params["sysparm_limit"]:
            break
        params["sysparm_offset"] += params["sysparm_limit"]
        if total_fetched >= 50000:
            logger.warning("Reached maximum fetch limit of 50000 records")
            break
    logger.info(f"Total ServiceNow updated articles fetched (24h): {len(all_articles)}")
    return all_articles

# We will parallelize the heavy per-article ops (summarize + embed) using ThreadPoolExecutor.


SN_MAX_WORKERS = 4
SN_MAX_SUMMARY_INPUT = 5000

def _process_sn_article(article):
    """Worker for ServiceNow article: convert html, mask PII, summarize, embed, format record."""
    try:
        knowledge_id = article.get("number")
        ci_value = article.get("cmdb_ci", "")
        if isinstance(ci_value, dict):
            ci = ci_value.get("display_value", "") or ""
        elif isinstance(ci_value, str):
            ci = ci_value.strip()
        else:
            ci = ""

        t = article.get("text")
        if not t or not t.strip():
            logger.warning(f"Skipping SN article {knowledge_id} due to missing/empty text")
            return None

        text = html_to_text(t).strip()
        if not text:
            logger.warning(f"Skipping SN article {knowledge_id} after cleaning — empty content")
            return None

        # Limit input size for summarization
        text_for_summary = text[:SN_MAX_SUMMARY_INPUT]

        summary = summarize_text(text_for_summary, region_name, llm_model)
        if not summary or not summary.strip():
            logger.warning(f"Skipping SN article {knowledge_id} due to empty summary")
            return None

        embedding = generate_embeddings(summary)

        record = {
            "ci": ci,
            "chunk": "", 
            "embedding": embedding,
            "knowledge_id": knowledge_id,
            "knowledge_type": article.get("kb_knowledge_base", {}).get("display_value") if isinstance(article.get("kb_knowledge_base", {}), dict) else str(article.get("kb_knowledge_base") or ""),
            "source": "ServiceNow",
            "link": f"{sn_base_url}/nav_to.do?uri=kb_view.do?sys_kb_id={article.get('sys_id')}" if article.get('sys_id') else "",
            "summary": summary,
        }
        return record
    except Exception as e:
        logger.error(f"Error processing SN article {article.get('number')}: {e}")
        return None

def format_sn_records_parallel(articles):
    """Parallel formatting for SN articles (returns list of records)."""
    KI_push = []
    if not articles:
        return KI_push
    with ThreadPoolExecutor(max_workers=SN_MAX_WORKERS) as executor:
        futures = [executor.submit(_process_sn_article, a) for a in articles]
        for f in as_completed(futures):
            rec = f.result()
            if rec:
                KI_push.append(rec)
    logger.info(f"Formatted {len(KI_push)} valid ServiceNow articles (skipped {len(articles) - len(KI_push)})")
    return KI_push

# ====================== CONFLUENCE ============================

def safe_request(url, auth, params=None, max_retries=3):
    for attempt in range(max_retries):
        resp = requests.get(url, auth=auth, params=params)
        if resp.status_code == 200:
            return resp
        elif resp.status_code in [502, 503, 504]:
            wait_time = (2 ** attempt)*4
            logger.warning(f"Retrying Confluence request (attempt {attempt+1}) after {wait_time}s: {resp.status_code}")
            time.sleep(wait_time)
        else:
            resp.raise_for_status()
    raise Exception(f"Confluence API failed after {max_retries} retries: {resp.status_code}")
 
 
MAX_WORKERS = 4
MAX_SUMMARY_INPUT = 5000  # limit text length sent for summarization

def process_confluence_page(result):
    """Worker: summarize, embed, and format a single Confluence page."""
    try:
        if result.get("type") != "page":
            return None

        # --- Extract CI from labels ---
        ci = ""
        try:
            labels_info = result.get("metadata", {}).get("labels", {}).get("results", [])
            if labels_info and isinstance(labels_info, list):
                label_names = [lbl.get("name", "").strip() for lbl in labels_info if lbl.get("name")]
                if label_names:
                    ci = ",".join(label_names)
        except Exception as e:
            logger.debug(f"Label extraction failed for Confluence page {result.get('id')}: {e}")
            ci = ""


        html_content = result["body"]["view"].get("value", "")
        if not html_content or not html_content.strip():
            return None

        text = html_to_text(html_content)
        text = mask_pii(text)
        text = text[:MAX_SUMMARY_INPUT]  # limit size for faster LLM processing

        summary = summarize_text(text, region_name, llm_model)
        if not summary or not summary.strip():
            return None

        embedding = generate_embeddings(summary)

        self_link = result.get("_links", {}).get("self")
        webui_path = result.get("_links", {}).get("webui")
        link = ""
        if self_link and webui_path:
            base_part = self_link.split("/wiki")[0] + "/wiki"
            link = f"{base_part}{webui_path}"

        return {
            "ci": ci,
            "chunk": '',
            "embedding": embedding,
            "knowledge_id": result["id"],
            "knowledge_type": "",
            "source": "Confluence",
            "link": link,
            "summary": summary,
        }
    except Exception as e:
        logger.error(f"Error processing Confluence page {result.get('id')}: {e}")
        return None

def get_confluence_pages_created_24h(db_config):
    """Fetch and insert Confluence pages created in last 24h — parallel + optimized."""
    response = {}
    eof = False
    total = 0

    base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
    initial_url = conf_url
    params = {"expand": "title,body.view,version,metadata.labels", "cql": 'type=page AND created >= now("-24h")'}

    try:
        while not eof:
            next_link = (response.get("_links") or {}).get("next")
            if response and not next_link:
                eof = True
                break

            url = base_api + next_link if next_link else initial_url
            resp = safe_request(url, auth=(conf_user, conf_token), params=None if next_link else params)
            if resp.status_code != 200:
                logger.error(f"Confluence API request failed: {resp.status_code} - {resp.text}")
                break

            response = resp.json()
            results = response.get("results", [])
            if not results:
                break

            # --- Parallel summarization and embedding ---
            batch_records = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_confluence_page, r) for r in results]
                for f in as_completed(futures):
                    rec = f.result()
                    if rec:
                        batch_records.append(rec)

            if batch_records:
                # created-case: insert only if not exists
                insert_knowledge_vec(batch_records, db_config, update_mode=False)
                total += len(batch_records)
                logger.info(f"Inserted {len(batch_records)} Confluence pages (Total: {total})")



        logger.info(f" Completed Confluence created ingestion. Total inserted: {total}")
        return total

    except Exception as e:
        logger.exception(f" Error during Confluence created ingestion: {e}")
        return total

def get_confluence_pages_updated_24h(db_config):
    """Fetch and update Confluence pages modified in last 24h — parallel + optimized."""
    response = {}
    eof = False
    total = 0

    base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
    initial_url = conf_url
    params = {"expand": "title,body.view,version,metadata.labels", "cql": 'type=page AND lastModified >= now("-24h")'}

    try:
        while not eof:
            next_link = (response.get("_links") or {}).get("next")
            if response and not next_link:
                eof = True
                break

            url = base_api + next_link if next_link else initial_url
            resp = safe_request(url, auth=(conf_user, conf_token), params=None if next_link else params)
            if resp.status_code != 200:
                logger.error(f"Confluence API request failed: {resp.status_code} - {resp.text}")
                break

            response = resp.json()
            results = response.get("results", [])
            if not results:
                break

            # --- Parallel summarization and embedding ---
            batch_records = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_confluence_page, r) for r in results]
                for f in as_completed(futures):
                    rec = f.result()
                    if rec:
                        batch_records.append(rec)

            if batch_records:
                # updated-case: upsert (insert or update)
                insert_knowledge_vec(batch_records, db_config, update_mode=True)
                total += len(batch_records)
                logger.info(f"Updated {len(batch_records)} Confluence pages (Total: {total})")


        logger.info(f" Completed Confluence updated ingestion. Total updated: {total}")
        return total

    except Exception as e:
        logger.exception(f" Error during Confluence updated ingestion: {e}")
        return total


# ====================== MAIN HANDLER ============================
def knowledge_handler(event=None, context=None):
    if context is None:
        import uuid
        class DummyContext:
            function_name = "ecs_ingestion_script"
            aws_request_id = str(uuid.uuid4())
        context = DummyContext()
    start_time = perf_counter()

    db_config = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_password,
    }

    try:
        sn_token = get_access_token_sn()

        # ========== ServiceNow Threads (Created + Updated) ==========
        def run_servicenow_created():
            try:
                logger.info("Fetching ServiceNow created articles (last 24h)...")
                sn_created = get_sn_articles_created_24h(sn_token)
                if sn_created:
                    sn_created_records = format_sn_records_parallel(sn_created)
                    if sn_created_records:
                        insert_knowledge_vec(sn_created_records, db_config, update_mode=False)
                else:
                    logger.info("No ServiceNow created records found in last 24h.")
            except Exception as e:
                logger.exception(f"ServiceNow created thread failed: {e}")
                raise

        def run_servicenow_updated():
            try:
                logger.info("Fetching ServiceNow updated articles (last 24h)...")
                sn_updated = get_sn_articles_updated_24h(sn_token)
                if sn_updated:
                    sn_updated_records = format_sn_records_parallel(sn_updated)
                    if sn_updated_records:
                        insert_knowledge_vec(sn_updated_records, db_config, update_mode=True)
                else:
                    logger.info("No ServiceNow updated records found in last 24h.")
            except Exception as e:
                logger.exception(f"ServiceNow updated thread failed: {e}")
                raise

        # ========== Confluence Threads (Created + Updated) ==========
        def run_confluence_created():
            try:
                get_confluence_pages_created_24h(db_config)
            except Exception as e:
                logger.exception(f"Confluence created thread failed: {e}")
                raise

        def run_confluence_updated():
            try:
                get_confluence_pages_updated_24h(db_config)
            except Exception as e:
                logger.exception(f"Confluence updated thread failed: {e}")
                raise

        
        # ======== Launch All Sources in Parallel Threads =========
        threads = [
            threading.Thread(target=run_servicenow_created),
            threading.Thread(target=run_servicenow_updated),
            threading.Thread(target=run_confluence_created),
            threading.Thread(target=run_confluence_updated),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(5)  # wait for all threads to complete

        update_ci_from_config_secret(db_config, configPythonSecrets, overwrite_existing=False)

        logger.info("=== All data source threads completed successfully ===")

    except Exception as e:
        logger.exception(f"Lambda execution failed: {e}")
        raise

    finally:
        elapsed = perf_counter() - start_time
        logger.info(f"Lambda execution time: {elapsed:.2f} seconds")


        # return {
        #     "statusCode": 200,
        #     "body": json.dumps({
        #         "message": "Execution completed",
        #         "elapsed_seconds": elapsed,
        #     }),
        # }

#------------Invoke Entry Point-------------------
# main_handler()