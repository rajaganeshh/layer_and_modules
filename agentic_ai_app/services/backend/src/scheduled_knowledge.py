import sys
# sys.path.append("/bin/day0-knowledge/presidio/python")
import os
import io
import re
import json
import boto3
import threading
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


        # ======== Launch All Sources in Parallel Threads =========
        threads = [
            threading.Thread(target=run_servicenow_created),
            threading.Thread(target=run_servicenow_updated),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(5)  # wait for all threads to complete

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