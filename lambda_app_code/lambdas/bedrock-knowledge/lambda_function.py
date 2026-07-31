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
import shutil
import tempfile
import numpy as np
import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from time import perf_counter
from botocore.exceptions import ClientError
import sharepoint_sum as sp_sum_mod  # day0 sharepoint summarizer
from summarize import summarize_text
import pdfplumber
from pdf2image import convert_from_path
from urllib3.util import make_headers

# ====================== LOGGER ============================
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('{"asctime": "%(asctime)s", "levelname": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "pathname": "%(pathname)s", "lineno": %(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S') 
ch.setFormatter(formatter) 

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)

# increase pool size to avoid "Connection pool is full" errors
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
conf_url = configPythonSecrets["confluence"]["url"]

# SharePoint
SHAREPOINT_TENANT_ID = configPythonSecrets["sharePoint"]["tenantId"]
SHAREPOINT_CLIENT_ID = configPythonSecrets["sharePoint"]["clientId"]
SHAREPOINT_CLIENT_SECRET = configPythonSecrets["sharePoint"]["clientSecret"]
SHAREPOINT_THRESHOLD = configPythonSecrets["config"]["sharePoint"]["threshold"]

# S3 Logging
log_bucket = configPythonSecrets["lambdaLog"]["bucket"]
log_prefix = configPythonSecrets["lambdaLog"]["prefix"]

# Simon Base URL
simon_base_url = configPythonSecrets["baseUrl"]
simon_interface_url = configPythonSecrets["interfaceAPI"]
interface_user = configPythonSecrets['interfaceEndpoint']['username']
interface_pwd = configPythonSecrets['interfaceEndpoint']['password']

# ====================== GLOBALS ============================
 
# Compute time window dynamically (since last scheduled run at 2:30 AM)
def get_hours_since_last_schedule(schedule_hour=2, schedule_minute=30):
    """Compute how many hours have passed since the last scheduled ingestion run (2:30 AM UTC)."""
    now = datetime.now(timezone.utc)
    today_schedule = now.replace(hour=schedule_hour, minute=schedule_minute, second=0, microsecond=0)
    if now < today_schedule:
        last_schedule = today_schedule - timedelta(days=1)
    else:
        last_schedule = today_schedule
    diff = now - last_schedule
    return round(diff.total_seconds() / 3600, 2)
 
# Define as global (cap to 24h just for safety)
time_window_hours = min(get_hours_since_last_schedule(), 24)
 
# logger.info(f"Dynamic ingestion window initialized: {time_window_hours} hours since last 2:30 AM schedule.")
 

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

    # Mask Emails using regex
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    text = re.sub(email_pattern, "[EMAIL_REDACTED]", text)

    # Mask Phone Numbers only if + followed by >7 digits
    phone_pattern = r"\+\d{8,}[\d\s\-\(\)]*"
    text = re.sub(phone_pattern, "[PHONE_REDACTED]", text)

    return text

#--------------------- LLM call -------------------------------------0
def _llm_(prompt, region_name = region_name , llm_model = llm_model):
   
    prompt = mask_pii(prompt)

    client = boto3.client("bedrock-runtime", region_name=region_name)
    
    #logger.info(f"Prompt: {prompt}")
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }
 
    request = json.dumps(native_request)
    response = client.invoke_model(modelId=llm_model, body=request)
    model_response = json.loads(response["body"].read())
 
    return model_response["content"][0]["text"].strip()

#---------------------- Kb SQL Query helper -------------------------
def _kb_sql_sharepoint(ci , keystr):
    llmout = _llm_(f"""
        you are a keyword extractor with a particular set of strict instructions. You will recieve some details about a system , followed by a description of an event.
        your task is to extract distinct words that have significance to the event.
        1- Extract names and configurations of systems , especially words that are unique and arent common words. Also extract Words that sound like abbreviations or company / software names (office365 , citrix etc). add 1 word in this category that defines the type of event this is (outage , unavailable , degrading etc). This will be category 1
        2- Extract search keywords that are related to the description that may help to search for articles that have useful content. avoid generic terms and do not have more than 6 words. This will be category 2
 
        Seperate all keywords with a space, but add a pipe symbol "|" between category 1 and category 2.
 
        Do not add any other text content , since this will be run through regex.
        Prioritize single word keywords.
 
        Item: "{ci}"
        Description: {keystr} 
        """)
    kwlist , supportWords = llmout.split("|")    

 
    stop_words = {'the', 'and', 'then', 'a', 'an', 'in', 'on', 'at', 'of', 'to', 'for', 'by', 'is', 'it','as','AS','Application','Website','Service','article'}
 
    kwlist = [word for word in kwlist.split() if len(word) >= 2 and word.lower() not in stop_words] + [ci]
    supportWords = [word for word in supportWords.split() if len(word) > 2 and word.lower() not in stop_words]
 
 
    matchstr = f"""(CASE WHEN summary ILIKE '%{"%' THEN 4 ELSE 0 END + CASE WHEN summary ILIKE '%".join(kwlist)}%' THEN 3 ELSE 0 END + CASE WHEN summary ILIKE '%{"%' THEN 1 ELSE 0 END + CASE WHEN summary ILIKE '%".join(supportWords)}%' THEN 1 ELSE 0 END)"""
    sqlSearch = f"""SELECT knowledge_id, link, source ,
        {matchstr} AS match_score , summary
    FROM knowledge_vec
    WHERE source = 'Sharepoint' AND {matchstr} >= (select max({matchstr}) from knowledge_vec where source = 'Sharepoint')*{SHAREPOINT_THRESHOLD/10}
    ORDER BY match_score DESC
    limit 10"""
 
    return sqlSearch , llmout

def _kb_sql_Confluence(ci , keystr):
    llmout = _llm_(f"""
        you are a keyword extractor with a particular set of strict instructions. You will recieve some details about a system , followed by a description of an event.
        your task is to extract distinct words that have significance to the event.
        1- Extract names and configurations of systems , especially words that are unique and arent common words. Also extract Words that sound like abbreviations or company / software names (office365 , citrix etc). add 1 word in this category that defines the type of event this is (outage , unavailable , degrading etc). This will be category 1
        2- Extract search keywords that are related to the description that may help to search for articles that have useful content. avoid generic terms and do not have more than 6 words. This will be category 2
 
        Seperate all keywords with a space, but add a pipe symbol "|" between category 1 and category 2.
 
        Do not add any other text content , since this will be run through regex.
        Prioritize single word keywords.
 
        Item: "{ci}"
        Description: {keystr} 
        """)
    kwlist , supportWords = llmout.split("|")    

 
    stop_words = {'the', 'and', 'then', 'a', 'an', 'in', 'on', 'at', 'of', 'to', 'for', 'by', 'is', 'it','as','AS','Application','Website','Service','article'}
 
    kwlist = [word for word in kwlist.split() if len(word) >= 2 and word.lower() not in stop_words] + [ci]
    supportWords = [word for word in supportWords.split() if len(word) > 2 and word.lower() not in stop_words]
 
 
    matchstr = f"""(CASE WHEN summary ILIKE '%{"%' THEN 4 ELSE 0 END + CASE WHEN summary ILIKE '%".join(kwlist)}%' THEN 3 ELSE 0 END + CASE WHEN summary ILIKE '%{"%' THEN 1 ELSE 0 END + CASE WHEN summary ILIKE '%".join(supportWords)}%' THEN 1 ELSE 0 END)"""
    sqlSearch = f"""SELECT knowledge_id, link, source ,
        {matchstr} AS match_score , summary
    FROM knowledge_vec
    WHERE source = 'Confluence' AND {matchstr} >= (select max({matchstr}) from knowledge_vec where source = 'Confluence')*0.8
    ORDER BY match_score DESC
    limit 10"""
 
    return sqlSearch , llmout



#----------------------Embedding (Day0 unified)-----------------------
MAX_CHARS = 6000
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

#============= DB insert & upsert/update (delete+insert for update_mode) ======================
def insert_knowledge_vec(data, db_config, update_mode=False):
    """
    Batched insert/update into knowledge_vec.
    - update_mode=False: Insert mode (insert all records; duplicates will cause DB constraint errors if present)
    - update_mode=True:  Delete old records with same (knowledge_id, source) then insert new
    """
    if not data:
        logger.info("No records to insert/update.")
        return

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        if update_mode:
            # ---- UPDATE MODE ----
            for record in data:
                try:
                    cursor.execute(
                        """
                        DELETE FROM knowledge_vec
                        WHERE knowledge_id = %s AND source = %s
                        """,
                        (record["knowledge_id"], record["source"]),
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete existing record for {record['source']}:{record['knowledge_id']}: {e}")
            conn.commit()

            insert_query = """
            INSERT INTO knowledge_vec (
                ci, chunk, embedding, knowledge_id, knowledge_type, source, link, summary
            )
            VALUES (%(ci)s, %(chunk)s, %(embedding)s, %(knowledge_id)s,
                    %(knowledge_type)s, %(source)s, %(link)s, %(summary)s)
            """
            psycopg2.extras.execute_batch(cursor, insert_query, data, page_size=50)
            conn.commit()
            logger.info(f"Batch update completed: {len(data)} records updated ")
        else:
            # ---- INSERT MODE ----
            insert_query = """
            INSERT INTO knowledge_vec (
                ci, chunk, embedding, knowledge_id, knowledge_type, source, link, summary
            )
            VALUES (%(ci)s, %(chunk)s, %(embedding)s, %(knowledge_id)s,
                    %(knowledge_type)s, %(source)s, %(link)s, %(summary)s)
            """
            psycopg2.extras.execute_batch(cursor, insert_query, data, page_size=50)
            conn.commit()
            logger.info(f"Batch insert completed: {len(data)} records inserted.")
    except Exception as e:
        logger.exception(f"Error inserting/updating data: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#-----------------Config Function --------------------------
def update_ci_from_config_secret(db_config, configPythonSecrets, overwrite_existing=False):
    """
    Updates the 'ci' column in knowledge_vec for ServiceNow, SharePoint, and Confluence.
    For Confluence: fetches all descendant *pages only* for each configured parent ID
    and applies the same CI to them (no attachments included).

    Args:
        db_config (dict): Database connection settings.
        configPythonSecrets (dict): Secrets Manager data (already loaded).
        overwrite_existing (bool): If True, overwrites existing CI values.
    """
    try:
        config_section = configPythonSecrets.get("config", {})
        if not config_section:
            logger.warning("No 'config' section found in Secrets Manager data.")
            return

        # Use Confluence credentials
        conf_user_local = configPythonSecrets["confluence"]["user"]
        conf_token_local = configPythonSecrets["confluence"]["token"]

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        total_updates = 0

        # Loop through all configured sources
        for source, ci_map in config_section.items():
            if source not in ["serviceNow", "sharePoint", "confluence"]:
                logger.debug(f"Skipping unsupported source: {source}")
                continue

            logger.info(f"Processing CI updates for source: {source}")

            # Loop through each CI (e.g. aims_as, ejet_holiday_homes)
            for ci_name, id_list in ci_map.items():
                if not id_list:
                    continue

                logger.info(f"  Updating CI '{ci_name}' for {len(id_list)} IDs in '{source}'")

                # Iterate over each configured ID for that CI
                for ci_id in id_list:
                    try:
                        # --- CONFLUENCE SPECIAL LOGIC ---
                        if source == "confluence":
                            base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
                            url = f"{base_api}/rest/api/content/{ci_id}/descendant/page"

                            descendants = []
                            logger.info(f"Fetching descendant pages for Confluence parent {ci_id}...")

                            while url:
                                resp = requests.get(url, auth=(conf_user_local, conf_token_local))
                                if resp.status_code != 200:
                                    logger.warning(f"Failed to fetch descendants for {ci_id}: {resp.status_code} - {resp.text}")
                                    break
                                data = resp.json()
                                results = data.get("results", [])
                                for r in results:
                                    if r.get("type") == "page" and r.get("id"):
                                        descendants.append(r["id"])
                                next_link = (data.get("_links") or {}).get("next")
                                url = base_api + next_link if next_link else None

                            # Include parent page too
                            all_ids = [ci_id] + descendants
                            logger.info(f"  Changing CI for Confluence parent {ci_id} and {len(descendants)} descendant pages.")
                            if descendants:
                                logger.debug(f"    Descendant page IDs: {descendants}")

                            for page_id in all_ids:
                                if overwrite_existing:
                                    cursor.execute(
                                        """
                                        UPDATE knowledge_vec
                                        SET ci = %s
                                        WHERE knowledge_id = %s::text
                                          AND source ILIKE 'confluence'
                                        """,
                                        (ci_name, str(page_id))
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        UPDATE knowledge_vec
                                        SET ci = %s
                                        WHERE knowledge_id = %s::text
                                          AND source ILIKE 'confluence'
                                          AND (ci IS NULL OR ci = '')
                                        """,
                                        (ci_name, str(page_id))
                                    )

                                if cursor.rowcount > 0:
                                    total_updates += cursor.rowcount
                                    logger.debug(f"Updated CI for Confluence page {page_id} (from parent {ci_id}) → {ci_name}")

                        # --- NORMAL SOURCES (ServiceNow, SharePoint) ---
                        else:
                            if overwrite_existing:
                                cursor.execute(
                                    """
                                    UPDATE knowledge_vec
                                    SET ci = %s
                                    WHERE knowledge_id = %s::text
                                      AND source ILIKE %s
                                    """,
                                    (ci_name, str(ci_id), source)
                                )
                            else:
                                cursor.execute(
                                    """
                                    UPDATE knowledge_vec
                                    SET ci = %s
                                    WHERE knowledge_id = %s::text
                                      AND source ILIKE %s
                                      AND (ci IS NULL OR ci = '')
                                    """,
                                    (ci_name, str(ci_id), source)
                                )

                            if cursor.rowcount > 0:
                                total_updates += cursor.rowcount
                                logger.debug(f"Updated CI for {source}:{ci_id} → {ci_name}")

                    except Exception as e:
                        logger.warning(f"Error updating CI for {source}:{ci_id} ({ci_name}): {e}")
                        continue

        conn.commit()
        logger.info(f" CI update from secret config completed. Total records updated: {total_updates}")

    except Exception as e:
        logger.exception(f"Error in CI update pipeline: {e}")
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

# ----------------- Upload logs helper --------------------
def upload_logs_to_s3(context,inc_id=None):
    try:
        # log_contents = log_capture_string.getvalue()
        # timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        # log_key = f"{log_prefix}/{context.function_name}/{datetime.utcnow().strftime('%Y-%m-%d')}/{timestamp}_{context.aws_request_id}.log"
        # boto3.client("s3").put_object(Bucket=log_bucket, Key=log_key, Body=log_contents, ContentType="text/plain")
        # return f"s3://{log_bucket}/{log_key}"
        for handler in logging.getLogger().handlers:
            handler.flush()
        log_contents = log_capture_string.getvalue()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S") 
        #  Always include incident ID in the log file name if provided
        incident_part = f"{inc_id}_" if inc_id else ""
        log_key = f"{log_prefix}/{context.function_name}/{datetime.utcnow().strftime('%Y-%m-%d')}/{incident_part}{timestamp}_{context.aws_request_id}.log" 
        boto3.client("s3").put_object(

            Bucket=log_bucket,

            Key=log_key,

            Body=log_contents.encode("utf-8"),

            ContentType="text/plain"

        )
        logger.info(f"Uploaded logs to s3://{log_bucket}/{log_key}")
        return f"s3://{log_bucket}/{log_key}" 
    except Exception:
        logger.exception("Failed uploading logs to S3")
        return None

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

# Fetch created
def get_sn_articles_created_h(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    sysparm_query = f"sys_created_on>=javascript:gs.hoursAgo({time_window_hours})^workflow_state=published"
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
    logger.info(f"Total ServiceNow created articles fetched in last {time_window_hours} hours: {len(all_articles)}")
    return all_articles

# Fetch updated 
def get_sn_articles_updated_h(token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    sysparm_query = f"sys_updated_on>=javascript:gs.hoursAgo({time_window_hours})^workflow_state=published"
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
    logger.info(f"Total ServiceNow updated articles fetched in last {time_window_hours} hours: {len(all_articles)}")
    return all_articles

# We will parallelize the heavy per-article ops (summarize + embed) using ThreadPoolExecutor.
from concurrent.futures import ThreadPoolExecutor, as_completed

SN_MAX_WORKERS = 8
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
            "chunk": "",  # for SN Day0 you used chunk empty and stored summary & embedding
            "embedding": embedding,
            "knowledge_id": knowledge_id,
            "knowledge_type": article.get("kb_knowledge_base", {}).get("display_value") if isinstance(article.get("kb_knowledge_base", {}), dict) else str(article.get("kb_knowledge_base") or ""),
            "source": "ServiceNow",
            "link": f"{sn_base_url}/nav_to.do?uri=kb_knowledge.do?sys_id={article.get('sys_id')}" if article.get('sys_id') else "",
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

# ====================== CONFLUENCE  ============================
MAX_WORKERS = 10
MAX_SUMMARY_INPUT = 5000  # limit text length sent for summarization

def process_confluence_page(result):
    """Worker: summarize, embed, and format a single Confluence page."""
    try:
        if result.get("type") != "page":
            return None
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
            "ci": "",
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

def get_confluence_pages_created_h(db_config):
    """Fetch and insert Confluence pages created — parallel + optimized."""
    response = {}
    eof = False
    total = 0

    base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
    initial_url = f"{base_api}/rest/api/content/search"
    params = {
    "expand": "title,body.view,version",
    "cql": f'created >= now("-{int(time_window_hours)}h")'
    }
    try:
        while not eof:
            next_link = (response.get("_links") or {}).get("next")
            if response and not next_link:
                eof = True
                break

            url = base_api + next_link if next_link else initial_url
            resp = requests.get(url, auth=(conf_user, conf_token), params=None if next_link else params)
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

            if total >= 300:  # safety cutoff to prevent long runs
                logger.info("Reached Confluence created-page cap (300). Stopping early.")
                break

        logger.info(f" Completed Confluence created ingestion. Total inserted: {total}")
        return total

    except Exception as e:
        logger.exception(f" Error during Confluence created ingestion: {e}")
        return total

def get_confluence_pages_updated_h(db_config):
    """Fetch and update Confluence pages modified  — parallel + optimized."""
    response = {}
    eof = False
    total = 0

    base_api = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
    initial_url = f"{base_api}/rest/api/content/search"
    params = {
    "expand": "title,body.view,version",
    "cql": f'lastModified >= now("-{int(time_window_hours)}h")'
    }

    try:
        while not eof:
            next_link = (response.get("_links") or {}).get("next")
            if response and not next_link:
                eof = True
                break

            url = base_api + next_link if next_link else initial_url
            resp = requests.get(url, auth=(conf_user, conf_token), params=None if next_link else params)
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
                # updated-case: upsert modeled as delete+insert
                insert_knowledge_vec(batch_records, db_config, update_mode=True)
                total += len(batch_records)
                logger.info(f"Updated {len(batch_records)} Confluence pages (Total: {total})")

            if total >= 300:
                logger.info("Reached Confluence updated-page cap (300). Stopping early.")
                break

        logger.info(f" Completed Confluence updated ingestion. Total updated: {total}")
        return total

    except Exception as e:
        logger.exception(f" Error during Confluence updated ingestion: {e}")
        return total

# ====================== SHAREPOINT  ============================
DOWNLOAD_PATH = "/tmp/downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

def get_graph_token(tenant_id, client_id, client_secret):
    """Obtain Microsoft Graph API token for SharePoint."""
    auth_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    data = urlencode({
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    })
    resp = http.request("POST", auth_url, body=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status != 200:
        raise Exception(f"Graph token fetch failed: {resp.status} - {resp.data}")
    logger.info("SharePoint access token received successfully")
    return json.loads(resp.data.decode("utf-8"))['access_token']

def get_all_sites(graph_headers):
    sites = []
    url = "https://graph.microsoft.com/v1.0/sites?search=*"
    while url:
        r = requests.get(url, headers=graph_headers)
        res_json = r.json()
        sites.extend(res_json.get('value', []))
        url = res_json.get('@odata.nextLink')
    return sites

def get_subsites(site_id, graph_headers):
    subsites = []
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/sites"
    r = requests.get(url, headers=graph_headers)
    subsites.extend(r.json().get('value', []))
    return subsites

def get_drives(site_id, graph_headers):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    r = requests.get(url, headers=graph_headers)
    return r.json().get('value', [])

def get_files_recursive(drive_id, graph_headers, time_filter=None, mode="created", folder_id=None):
    """
    Recursively find PDF files and filter them by time_filter.
    mode="created" -> include files where created >= time_filter
    mode="updated" -> include files where lastModified >= time_filter
    """
    files = []
    if folder_id:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
    else:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"

    r = requests.get(url, headers=graph_headers)
    if r.status_code != 200:
        logger.debug(f"Failed to list folder children for drive {drive_id} folder {folder_id}: {r.status_code}")
        return files

    res_json = r.json()
    for item in res_json.get('value', []):
        if item.get('folder'):
            files.extend(get_files_recursive(drive_id, graph_headers, time_filter, mode, item['id']))
        else:
            name = item.get('name', '')
            if not name:
                continue
            if name.lower().endswith('.pdf'):
                try:
                    created = datetime.fromisoformat(item['createdDateTime'].replace('Z', '+00:00'))
                except Exception:
                    created = None
                try:
                    modified = datetime.fromisoformat(item['lastModifiedDateTime'].replace('Z', '+00:00'))
                except Exception:
                    modified = None

                include = False
                if mode == "created" and created and time_filter and created >= time_filter:
                    include = True
                if mode == "updated" and modified and time_filter and modified >= time_filter:
                    include = True

                if include:
                    # Attach list item fields if available (Day0)
                    item_id = item.get('id')
                    try:
                        listitem_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/listItem?$expand=fields'
                        lr = requests.get(listitem_url, headers=graph_headers)
                        if lr.status_code == 200:
                            fields = lr.json().get('fields', {})
                            if "ConfigurationItem" in fields:
                                item["ConfigurationItem"] = fields["ConfigurationItem"]
                    except Exception:
                        logger.debug(f"Could not fetch listItem fields for {item_id}")
                    files.append(item)
    return files

def _download_sharepoint_pdf(item, download_dir):
    """Download a single SharePoint PDF and verify it's valid (Day0 logic)."""
    download_url = item.get('@microsoft.graph.downloadUrl')
    if not download_url:
        raise ValueError(f"No download URL available for item: {item.get('id')}")
    safe_name = item.get('name') or item.get('id')
    file_path = os.path.join(download_dir, safe_name)

    with requests.get(download_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        content_type = r.headers.get('Content-Type', '').lower()
        if 'pdf' not in content_type:
            logger.warning(f"Skipping file {safe_name}: not a PDF (Content-Type={content_type})")
            raise ValueError("Invalid PDF content returned from SharePoint")
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # Quick check for valid PDF signature
    with open(file_path, 'rb') as f:
        header = f.read(5)
        if not header.startswith(b'%PDF'):
            logger.warning(f"Skipping file {safe_name}: invalid PDF header ({header})")
            raise ValueError("Downloaded file is not a valid PDF")

    return file_path

def _cleanup_download_and_images(local_pdf_path):
    try:
        if not local_pdf_path:
            return
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
        image_dir = getattr(sp_sum_mod, "IMAGE_SAVE_DIR", "pdf_images")
        base = os.path.splitext(os.path.basename(local_pdf_path))[0]
        if os.path.isdir(image_dir):
            for fname in os.listdir(image_dir):
                # Day0 used both base and base + "_" patterns
                if fname.startswith(base + "_") or fname.startswith(base):
                    try:
                        os.remove(os.path.join(image_dir, fname))
                    except Exception:
                        logger.debug(f"Could not remove image file {fname}")
            if not os.listdir(image_dir):
                try:
                    shutil.rmtree(image_dir)
                except Exception:
                    logger.debug(f"Could not remove image directory {image_dir}")
    except Exception as e:
        logger.warning(f"Cleanup error for {local_pdf_path}: {e}")

async def process_sharepoint_pdf_item(item, graph_headers, db_config, update_mode=False):
    """
    Process a single SharePoint PDF item:
    - download
    - summarize (using sp_sum_mod)
    - generate embeddings
    - insert or update in DB according to update_mode
    """
    knowledge_id = item.get('id')
    web_link = item.get('webUrl', "")
    name = item.get('name', knowledge_id)
    ci_value = item.get("ConfigurationItem", "")

    logger.info(f"Processing SharePoint PDF: {name} ({knowledge_id}) update_mode={update_mode}")

    temp_dir = tempfile.mkdtemp(prefix=f"sp_{knowledge_id}_", dir=DOWNLOAD_PATH)
    local_pdf_path = None
    try:
        try:
            local_pdf_path = _download_sharepoint_pdf(item, temp_dir)
            logger.info(f"Downloaded to {local_pdf_path}")
        except ValueError as e:
            logger.warning(f"Skipping file {item.get('name')}: {e}")
            return  # skip invalid file

        # Try multiple summarizer function names that Day0 used / scheduled used
        summary = None
        try:
            # prefer async bedrock variant if present
            if hasattr(sp_sum_mod, "summarize_pdf_with_bedrock_async"):
                summary = await sp_sum_mod.summarize_pdf_with_bedrock_async(local_pdf_path, region_name, llm_model)
            elif hasattr(sp_sum_mod, "summarize_pdf"):
                loop = asyncio.get_running_loop()
                summary = await loop.run_in_executor(None, sp_sum_mod.summarize_pdf, local_pdf_path, region_name, llm_model)
            else:
                if hasattr(sp_sum_mod, "summarize_pdf_with_bedrock"):
                    loop = asyncio.get_running_loop()
                    summary = await loop.run_in_executor(None, sp_sum_mod.summarize_pdf_with_bedrock, local_pdf_path, region_name, llm_model)
        except Exception as e:
            logger.exception(f"Summarization failed for {knowledge_id}: {e}")
            summary = None

        if not summary:
            logger.warning(f"No summary returned for SharePoint PDF {knowledge_id} - skipping")
            return

        embedding = generate_embeddings(summary)

        record = {
            "ci": ci_value or "",
            "chunk": "" ,
            "embedding": embedding,
            "knowledge_id": knowledge_id,
            "knowledge_type": "",
            "source": "SharePoint",
            "link": web_link,
            "summary": summary,
        }

        # Use unified insert_knowledge_vec with update_mode flag to differentiate created vs updated
        insert_knowledge_vec([record], db_config, update_mode=update_mode)
        logger.info(f"Inserted/Updated SharePoint PDF record: {knowledge_id} (update_mode={update_mode})")

    except Exception as e:
        logger.exception(f"Error processing SharePoint file {knowledge_id}: {e}")
    finally:
        try:
            _cleanup_download_and_images(local_pdf_path)
        except Exception:
            logger.debug("Cleanup encountered an error")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            logger.debug(f"Could not remove temp dir {temp_dir}")

async def process_all_sharepoint_files(files, graph_headers, db_config, update_mode=False):
    """Process all SharePoint PDFs concurrently with update_mode flag."""
    tasks = [process_sharepoint_pdf_item(item, graph_headers, db_config, update_mode) for item in files]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"Completed async processing for {len(files)} SharePoint PDFs (update_mode={update_mode}).")

# ====================== ACTION LAMBDA HANDLER & SEARCH ============================

# Helper: convert embedding list to Postgres vector literal string for pgvector
def embedding_list_to_pgvector_literal(embedding):
    # embedding should be list of floats
    if embedding is None:
        return None
    try:
        # limit formatting to reasonable precision
        elems = ",".join([str(float(x)) for x in embedding])
        return f"[{elems}]"
    except Exception:
        # fallback json dumps
        return "[" + ",".join(map(str, embedding)) + "]"

# Search using pgvector <-> operator, filter by CI or blank CI; return top N
def search_top_k_by_embedding_pgvector(embedding, ci_value, short_description, top_k=6):
    """
    Modified search logic:
    - Only search where ci matches exactly (no null or blank CI)
    - Run three separate searches for each source (ServiceNow, Confluence, SharePoint)
    - Return combined list of results (each source can return 0..6 items)
    """
    conn = None
    cur = None
    combined_results = []
    sn_token = get_access_token_sn()
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
 
        vec_literal = embedding_list_to_pgvector_literal(embedding)
        if vec_literal is None:
            return combined_results

        #-------------------ServiceNow--------------------
        sources = ["ServiceNow"]
 
        for src in sources:
            sql = """
                SELECT 
                    knowledge_id, link, summary, source, ci, 
                    (embedding <-> %s::vector) AS distance
                FROM knowledge_vec
                WHERE ci ILIKE %s AND source ILIKE %s
                ORDER BY distance ASC
                LIMIT %s
            """
            cur.execute(sql, (vec_literal, ci_value, src, top_k))
            rows = cur.fetchall()
 
            for r in rows:
                headers = {"Authorization": f"Bearer {sn_token}", "Accept": "application/json"}
                sys_id = r.get("link")[-32:]
                params = {
                    "sysparm_query": f"sys_id={sys_id}",
                    "sysparm_display_value": "True",
                    "sysparm_limit": 1,
                    "sysparm_offset": 0,
                    # "workflow_state": "published"
                }
                resp = http.request("GET", f"{sn_base_url}/api/now/table/kb_knowledge", headers=headers, fields=params)                    
                if resp.status == 200:
                    short_desc = ""
                    data = json.loads(resp.data.decode("utf-8"))
                    results = data.get("result", [])
                    if len(results)>0:
                        results = results[0]
                        short_desc = results.get("short_description")
                else:
                    raise Exception(f"Failed to fetch knowledge article - {sys_id}: {resp.status} - {resp.data}")

                combined_results.append({
                    "knowledgeId": r.get("knowledge_id"),
                    "link": r.get("link"),
                    "summary": r.get("summary"),
                    "source": r.get("source"),
                    "ci": r.get("ci"),
                    "distance": float(r.get("distance") or 0.0),
                    "short_description": short_desc
                })

        # ------------------ CONFLUENCE  ------------------
        db_config = {
                "dbname": db_name,
                "user": db_user,
                "password": db_password,
                "host": db_host,
                "port": db_port,
            }

        try:

            # Step 1: Format CI for Confluence Search
            # e.g. "Simon As" -> "simon-as"
            ci_for_conf = ci_value.lower().replace(" ", "-")

            # Step 2: Fetch pages via Confluence API (label search)
            # conf_base = "https://api.atlassian.com/ex/confluence/45c68744-a379-4908-9bef-efb9c1ba643d/wiki"
            # conf_url = f"{conf_base}/rest/api/content/search"           
            params = {
                "expand": "metadata.labels",
                "cql": f'type=page AND label="{ci_for_conf}"'
            }
            # getting conf_url from config file 
            conf_resp = requests.get(url=conf_url, auth=(conf_user, conf_token), params=params, verify=False)

            logger.info('\n')
            logger.info("=========Results==========")
            logger.info(f"Results: {conf_resp}")
            logger.info("\n")

            conf_page_ids = []
            conf_api_title = {}
            if conf_resp.status_code == 200:
                conf_data = conf_resp.json()
                conf_results = conf_data.get("results", [])
                for r in conf_results:
                    pid = r.get("id")
                    conf_title = r.get("title", "NA")
                    if pid:
                        conf_page_ids.append(pid)
                        conf_api_title[pid] = {
                            "title" : conf_title
                        }
                logger.info(f"Confluence API returned {len(conf_page_ids)} pages for label '{ci_for_conf}'")
            else:
                logger.warning(f"Confluence API failed for '{ci_for_conf}': {conf_resp.status_code} - {conf_resp.text}")
 
            # Step 3: Vector DB search by CI  
            conf_ci_results = []
            
            try:
                
                if ci_for_conf:
                    sql_conf_subset = """
                        SELECT knowledge_id, link, summary, source, ci
                        FROM knowledge_vec
                        WHERE source = 'Confluence' AND LOWER(ci) LIKE %s
                    """
                    like_pattern = f"%{ci_for_conf}%"
                    cur.execute(sql_conf_subset, (like_pattern,))
                    conf_ci_results = cur.fetchall()

 
                    logger.info(
                        f"Matched {len(conf_ci_results)} Confluence DB rows where CI field contains '{ci_for_conf}'"
                    )
                else:
                    logger.info("Incident CI is blank — skipping Confluence CI DB search.")
            except Exception as e:
                logger.warning(f"Confluence CI DB search failed: {e}")
 
            # Step 4: Keyword search 
            conf_keyword_sql, llmout = _kb_sql_Confluence(ci_value, short_description)
            logger.info(f"Keyword SQL: {conf_keyword_sql}")
            logger.info(f"Keyword SQL: {llmout}")
            cur.execute(conf_keyword_sql)
            conf_keyword_results = cur.fetchall()
            logger.info(f"Keyword results {conf_keyword_results}")
 
            # Step 5: Combine and de-duplicate by knowledgeId
            all_conf = [] 
            def add_unique(record_list, record):
                if record and record["knowledgeId"] not in {r["knowledgeId"] for r in record_list}:
                    record_list.append(record) 
            # Add API pages (highest priority)
            for pid in conf_page_ids:
                summary_from_db = ""
                try:
                    # Always open a short-lived dedicated connection to ensure clean context
                    with psycopg2.connect(**db_config) as conn_check:
                        with conn_check.cursor() as cur_check:
                            cur_check.execute("""
                                SELECT summary
                                FROM knowledge_vec
                                WHERE TRIM(knowledge_id::text) = TRIM(%s)
                                  AND source ILIKE 'Confluence'
                                LIMIT 1;
                            """, (str(pid),))
                            row = cur_check.fetchone()
                            if row and row[0]:
                                summary_from_db = row[0]
                            else:
                                logger.debug(f"No summary found in DB for Confluence ID {pid}")
                except Exception as e:
                    logger.warning(f"DB summary lookup failed for Confluence page {pid}: {e}")

                # fetch short desc for api search 



                add_unique(all_conf, {
                    "knowledgeId": str(pid),
                    "link": f"https://easyjet.atlassian.net/wiki/pages/viewpage.action?pageId={pid}",
                    "summary": summary_from_db,  # Use DB summary if found; else blank
                    "source": "Confluence",
                    "ci": ci_for_conf if ci_for_conf else "CI Not Tagged",
                    "distance": 0.0,
                    # Add title for result based on API search, if label exist
                    "short_description" : conf_api_title.get(pid,{}).get("title") 
                })            
            # Add DB CI matches

            if len(conf_ci_results)  != 0 :

                conf_title = fetch_conf_title(conf_ci_results)

           

            for r in conf_ci_results:

               



                add_unique(all_conf, {
                    "knowledgeId": r.get("knowledge_id"),
                    "link": r.get("link"),
                    "summary": r.get("summary"),
                    "source": "Confluence",
                    "ci": r.get("ci"),
                    "distance": 0.0,
                    "short_description" : conf_title.get(r.get("knowledge_id"),{}).get("title")
                })


                
 
            # Add keyword search results

            if len(conf_keyword_results) !=0 : 
                conf_title = fetch_conf_title(conf_keyword_results)
                logger.info(f"Keyword search title {conf_title}")


            for r in conf_keyword_results:
                logger.info(f"title {conf_title.get(r.get("knowledge_id"),{}).get("title")}")
                add_unique(all_conf, {
                    "knowledgeId": r.get("knowledge_id"),
                    "link": r.get("link"),
                    "summary": r.get("summary"),
                    "source": "Confluence",
                    "ci": r.get("ci"),
                    "distance": 0.0,
                    "short_description" : conf_title.get(r.get("knowledge_id"),{}).get("title")
                })
 
            # Step 6: Limit total to 6 results
            deduped_conf = all_conf[:6]
 
            # Step 7: Add to final combined results
            combined_results.extend(deduped_conf)
            logger.info(f"Added {len(deduped_conf)} Confluence results (after merge/de-dupe)")
 
        except Exception as e:
            logger.exception(f"Confluence  failed: {e}")
 
        #-----------------------Sharepoint-----------------------

        # SQL Keyword search
        extra_sql,out = _kb_sql_sharepoint(ci_value,short_description)
        logger.info(f"Sharepoint SQL: {extra_sql}")
        logger.info(f"Sharepoint llm's out: {out}")
        cur.execute(extra_sql)
        rows = cur.fetchall()
        for r in rows:
            summary = r.get("summary", "")
            pattern = r"^(.*?)\.(docx|doc|xlsx|pdf|txt)"
            match = re.match(pattern, summary, flags=re.IGNORECASE)
            title = match.group(1) if match else ""

            record = {
                "knowledgeId": r.get("knowledge_id"),
                "link": r.get("link"),
                "summary": r.get("summary") if r.get("summary") != 'NIL' else "Non technical document and hence summary is not generated",
                "source": r.get("source"),
                "ci": r.get("ci"),
                "distance": 0.0,
                "short_description": title
            }
            if record not in combined_results:
                combined_results.append(record)
        
        sql = f"""
            SELECT knowledge_id, link, summary, source, ci
            FROM knowledge_vec
            WHERE source ='Sharepoint' AND ci ILIKE '%{ci_value}%';
        """
        cur.execute(sql)
        rows = cur.fetchall()

        for r in rows:
            summary = r.get("summary", "")
            pattern = r"^(.*?)\.(docx|doc|xlsx|pdf|txt)"
            match = re.match(pattern, summary, flags=re.IGNORECASE)
            title = match.group(1) if match else ""

            combined_results.append({
                "knowledgeId": r.get("knowledge_id"),
                "link": r.get("link"),
                "summary": r.get("summary") if r.get("summary") != 'NIL' else "Non technical document and hence summary is not generated",
                "source": r.get("source"),
                "ci": ci_value,
                "distance": 0.0,
                "short_description": title
            })
 
    except Exception as e:
        logger.exception(f"Error running vector similarity search: {e}")
    finally:
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
        except Exception:
            pass
 
    return combined_results

# Utility: get full incident details from ServiceNow
# def fetch_incident(inc_id, token):
#     headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
#     url = f"{sn_base_url}/api/now/table/incident"
#     params = {"sysparm_query": f"number={inc_id}", "sysparm_display_value": "true"}
#     resp = http.request("GET", url, headers=headers, fields=params)
#     if resp.status != 200:
#         raise Exception(f"Failed to fetch incident {inc_id}: {resp.status} - {resp.data}")
#     data = json.loads(resp.data.decode("utf-8"))
#     results = data.get("result", [])
#     if not results:
#         raise Exception(f"Incident {inc_id} not found")
#     return results[0]

def get_conf_id (conf_result):
    conf_id = []
    for r in conf_result:
        id= r.get("knowledge_id")
        conf_id.append(id)

    return conf_id

def build_cql (conf_id):
    cql_query = f"type = page AND id IN ({', '.join(map(str, conf_id))})"


    return cql_query

def fetch_conf_title(conf_results): 
    conf_id =  get_conf_id(conf_results)
    cql = build_cql(conf_id) 

    params = {
        "expand": "metadata.labels",
        "cql": cql
    }
    logger.info(f"Inside fetch title CQL {cql}")

    conf_title_dict = {}
    conf_resp = requests.get(url=conf_url, auth=(conf_user, conf_token), params=params, verify=False)
    if conf_resp.status_code == 200:
        conf_data = conf_resp.json()
        conf_results = conf_data.get("results", [])
        for r in conf_results:
            pid = r.get("id")
            conf_title = r.get("title", "NA")
            if pid:
                conf_title_dict[pid] = {
                    "title" : conf_title
                }
                logger.info(f"Confluence db title fetched")
    else:
        logger.warning(f"Confluence API failed ")
    
    return conf_title_dict
    


def fetch_incident_from_db(incident_id, db_config):
    """
    Fetch incident details directly from p1p2_incidents table.
    Returns a dict with configuration_item, short_description, comments_worknotes, description.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = """
            SELECT configuration_item, short_description, comments_worknotes, description
            FROM p1p2_incidents
            WHERE inc_id = %s
        """
        cur.execute(sql, (incident_id,))
        row = cur.fetchone()
        if not row:
            raise Exception(f"No incident found in DB for inc_id={incident_id}")
        return row
    except Exception as e:
        logger.exception(f"Failed to fetch incident from DB: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Build combined text that merges short_description, description, comments_and_work_notes, work_notes
# def build_incident_combined_text(inc_record):
#     parts = []
#     # short_description
#     sd = inc_record.get("short_description") or ""
#     if sd:
#         parts.append(sd)
#     # description
#     desc = inc_record.get("description") or ""
#     if desc:
#         parts.append(desc)
#     # comments_and_work_notes (may be a field in your instance)
#     comments_and_work_notes = inc_record.get("comments_and_work_notes") or ""
#     if comments_and_work_notes:
#         parts.append(comments_and_work_notes)
#     # work_notes field
#     work_notes = inc_record.get("work_notes") or ""
#     if work_notes:
#         parts.append(work_notes)
#     # join with newline
#     combined = "\n".join([p for p in parts if p])
#     # safety: fallback to incident number if empty
#     if not combined.strip():
#         combined = f"Incident {inc_record.get('number', '')}"
#     return combined

def build_incident_combined_text(short_description, comments_worknotes, description):
    """
    Build combined text using only these three fields from p1p2_incidents.
    """
    parts = []
    if short_description:
        parts.append(short_description)
    if description:
        parts.append(description)
    if comments_worknotes:
        parts.append(comments_worknotes)
    combined = "\n".join(p.strip() for p in parts if p)
    return combined.strip()

# Now integrate ingestion code into action lambda flow
def action_lambda_run_h_ingestion(db_config):
    """
    Run the  ingestion pipeline for ServiceNow, Confluence, SharePoint.
    This reuses the same functions and logic from the scheduled lambda (kept intact).
    """
    try:
        sn_token = get_access_token_sn()

        # ========== ServiceNow Threads (Created + Updated) ==========
        def run_servicenow_created():
            try:
                logger.info(f"Fetching ServiceNow created articles (last {time_window_hours} hours)")
                sn_created = get_sn_articles_created_h(sn_token)
                if sn_created:
                    sn_created_records = format_sn_records_parallel(sn_created)
                    if sn_created_records:
                        insert_knowledge_vec(sn_created_records, db_config, update_mode=False)
                else:
                    logger.info(f"No ServiceNow created records found in last {time_window_hours} hours.")
            except Exception as e:
                logger.exception(f"ServiceNow created thread failed: {e}")

        def run_servicenow_updated():
            try:
                logger.info(f"Fetching ServiceNow updated articles (last {time_window_hours} hours)...")
                sn_updated = get_sn_articles_updated_h(sn_token)
                if sn_updated:
                    sn_updated_records = format_sn_records_parallel(sn_updated)
                    if sn_updated_records:
                        insert_knowledge_vec(sn_updated_records, db_config, update_mode=True)
                else:
                    logger.info(f"No ServiceNow updated records found in last {time_window_hours} hours")
            except Exception as e:
                logger.exception(f"ServiceNow updated thread failed: {e}")

        # ========== Confluence Threads (Created + Updated) ==========
        def run_confluence_created():
            try:
                get_confluence_pages_created_h(db_config)
            except Exception as e:
                logger.exception(f"Confluence created thread failed: {e}")

        def run_confluence_updated():
            try:
                get_confluence_pages_updated_h(db_config)
            except Exception as e:
                logger.exception(f"Confluence updated thread failed: {e}")

        # ========== SharePoint Threads (Created + Updated) ==========
        def run_sharepoint_created_updated():
            try:
                logger.info(f"Fetching SharePoint documents (last {time_window_hours} hours)...")
                access_token = get_graph_token(SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET)
                graph_headers = {"Authorization": f"Bearer {access_token}"}

                time_filter = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
                sites = get_all_sites(graph_headers)
                created_files, updated_files = [], []

                logger.info(f"Found {len(sites)} SharePoint sites. Enumerating drives and files...")

                for site in sites:
                    site_id = site.get("id")
                    try:
                        drives = get_drives(site_id, graph_headers)
                    except Exception:
                        drives = []
                    for drive in drives:
                        try:
                            created = get_files_recursive(drive["id"], graph_headers, time_filter, mode="created")
                            updated = get_files_recursive(drive["id"], graph_headers, time_filter, mode="updated")
                            created_files.extend(created or [])
                            updated_files.extend(updated or [])
                        except Exception:
                            logger.debug(f"Could not list files for drive {drive.get('id')}")

                if created_files:
                    logger.info(f"Total SharePoint PDFs created in last {time_window_hours} hours: {len(created_files)}")
                    asyncio.run(process_all_sharepoint_files(created_files, graph_headers, db_config, update_mode=False))
                else:
                    logger.info(f"No new SharePoint PDFs created in the last {time_window_hours} hours")

                if updated_files:
                    logger.info(f"Total SharePoint PDFs updated in last {time_window_hours} hours: {len(updated_files)}")
                    asyncio.run(process_all_sharepoint_files(updated_files, graph_headers, db_config, update_mode=True))
                else:
                    logger.info(f"No SharePoint PDFs updated in the last {time_window_hours} hours")

            except Exception as e:
                logger.exception(f"SharePoint thread failed: {e}")

        # ======== Launch All Sources in Parallel Threads =========
        threads = [
            threading.Thread(target=run_servicenow_created),
            threading.Thread(target=run_servicenow_updated),
            threading.Thread(target=run_confluence_created),
            threading.Thread(target=run_confluence_updated),
            threading.Thread(target=run_sharepoint_created_updated),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # After ingestion, update CI mapping using secrets' config
        update_ci_from_config_secret(db_config, configPythonSecrets, overwrite_existing=False)

        logger.info("===  ingestion threads completed successfully ===")

    except Exception:
        logger.exception(" ingestion pipeline failed")

# ====================== IRP AND MIM UTILITIES  ============================
def parse_irp_html(html_text):
    """
    Parse IRP KB article HTML tables into structured dictionaries.
    - Dynamically detects header names and normalizes to standard fields.
    - Skips header row in output.
    - Handles inconsistent column naming across articles.
 
    Expected output format:
    {
        "scenario": "",
        "priority": "",
        "outage": "",
        "applicationService": "",
        "impact": "",
        "MIMactions": "",
        "information": "",
    }
    """
    from bs4 import BeautifulSoup
    import re
 
    if not html_text:
        return []
 
    soup = BeautifulSoup(html_text, "html.parser")
    tables = soup.find_all("table")
    results = []
 
    # Canonical regex patterns for header matching (flexible + semantic)
    field_patterns = {
        "scenario": [
            r"\bscenario\b"
        ],
        "priority": [
            r"\bpriority\b", r"incident\s*priority"
        ],
        "outage": [
            r"outage", r"degradation", r"temp\s*tolerate", r"partial", r"failure"
        ],
        "applicationService": [
            r"application\s*service", r"how\s*identified", r"service\s*name", r"app\s*service"
        ],
        # Impact → matches any header with 'impact'
        "impact": [
            r"\bImpact\b", r"impact\s*on", r"direct\s*impact", r"customer\s*impact"
        ],
        # MIMactions → matches any header mentioning mim/actions/errors
        "MIMactions": [
            r"\bmim\b", r"mim\s*action", r"mim\s*actions", r"error\s*codes",
            r"direct\s*impact\s*on\s*customer", r"customer\s*actions?", r"actions?"
        ],
        # Information → broader list now includes 'ITSD Actions'
        "information": [
            r"ITSD\s*Actions", r"it\s*sd\s*actions", r"notes?", r"workaround",
            r"remarks?", r"info", r"information", r"actions\s*taken"
        ],
    }
 
    def normalize_header(header_text):
        """Return canonical field name for a given header text using regex matching."""
        text = header_text.strip().lower()
        for field, patterns in field_patterns.items():
            for pat in patterns:
                if re.search(pat, text):
                    return field
        return None
 
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
 
        # --- First row is header row ---
        header_cells = [c.get_text(separator=" ", strip=True) for c in rows[0].find_all(["th", "td"])]
        if not header_cells:
            continue
 
        # Build a column-to-field mapping
        header_map = {}
        for idx, header_text in enumerate(header_cells):
            field = normalize_header(header_text)
            if field:
                header_map[idx] = field
 
        # --- Process table data rows ---
        for row in rows[1:]:
            cols = [c.get_text(separator=" ", strip=True) for c in row.find_all("td")]
            if not cols or all(not c.strip() for c in cols):
                continue
 
            row_data = {
                "scenario": "",
                "priority": "",
                "outage": "",
                "applicationService": "",
                "impact": "",
                "MIMactions": "",
                "information": "",
            }
 
            for idx, val in enumerate(cols):
                mapped_field = header_map.get(idx)
                if mapped_field:
                    row_data[mapped_field] = val
 
            # Include only rows with at least one meaningful value
            if any(v.strip() for v in row_data.values()):
                results.append(row_data)
 
    return results
 

def fetch_irp_for_ci(impacted_ci, token):
    """
    Fetch Incident Response Plan (IRP) KB articles for a given CI
    from the IRP knowledge base (ID = 190b80d81b33c6503eb343f6dc4bcb25).
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    irp_base_id = "190b80d81b33c6503eb343f6dc4bcb25"
    api_url = f"{sn_base_url}/api/now/table/kb_knowledge"
 
    all_irp_articles = []
    total_fetched = 0
    offset = 0
    limit = 200
 
    try:
        logger.info(f"Fetching IRP KB articles from base ID {irp_base_id} for CI: {impacted_ci}")
 
        while True:
            query = f"workflow_state=published^kb_knowledge_base={irp_base_id}"
            params = {
                "sysparm_query": query,
                "sysparm_display_value": "true",
                "sysparm_limit": limit,
                "sysparm_offset": offset
            }
 
            #  Using requests instead of urllib3 to ensure proper encoding
            resp = requests.get(api_url, headers=headers, params=params, timeout=30)
            logger.info(resp)
            if resp.status_code != 200:
                logger.warning(f"IRP fetch failed: {resp.status_code} - {resp.text}")
                break
 
            batch = resp.json().get("result", [])
            if not batch:
                break
 
            all_irp_articles.extend(batch)
            total_fetched += len(batch)
            logger.debug(f"Fetched {len(batch)} IRP KB articles (offset {offset})")
 
            if len(batch) < limit:
                break
            offset += limit
 
        logger.info(f"Fetched total {total_fetched} IRP KB articles from ServiceNow.")
 
        # --- Match articles by CI ---
        matched_irp = []
        for art in all_irp_articles:
            ci_field = art.get("cmdb_ci") or {}
            ci_value = ""
            if isinstance(ci_field, dict):
                ci_value = (ci_field.get("display_value") or ci_field.get("value") or "").strip()
            elif isinstance(ci_field, str):
                ci_value = ci_field.strip()
 
            # match directly on CI or fallback to title/text mention
            if impacted_ci and impacted_ci.lower() in ci_value.lower():
                matched_irp.append(art)
            # elif impacted_ci and (
            #     impacted_ci.lower() in (art.get("short_description") or "").lower()
            #     or impacted_ci.lower() in (art.get("text") or "").lower()
            # ):
            #     matched_irp.append(art)
 
        logger.info(f"Matched {len(matched_irp)} IRP articles for CI: {impacted_ci}")
 
        # --- Parse the HTML into structured IRP entries ---
        irp_articles = []
        for art in matched_irp:
            html_text = art.get("text", "")
            short_description = art.get("short_description","")

            kb_sys_id = art.get("sys_id", "")
            parsed_rows = parse_irp_html(html_text)

            # Create ServiceNow KB link (if sys_id exists)
            kb_link = f"{sn_base_url}/nav_to.do?uri=kb_view.do?sys_kb_id={kb_sys_id}" if kb_sys_id else ""
    
            # Add 'short description' to IRP
            shortDescription = art.get("short_description", "")
                
            # Add 'link' field to every parsed row from this article
            for row in parsed_rows:
                row["link"] = kb_link
                row["shortDescription"] = shortDescription
            
            if parsed_rows:
                irp_articles.extend(parsed_rows)
 
        if not irp_articles:
            logger.warning(f"No IRP plan rows parsed for CI {impacted_ci} as table is not present in article body")
 
        return irp_articles
    except Exception as e:
        logger.exception(f"Failed to fetch/parse IRP articles for CI {impacted_ci}: {e}")
        return [{
            "scenario": "",
            "shortDescription": "",
            "priority": "",
            "outage": "",
            "applicationService": impacted_ci or "",
            "impact": "",
            "MIMactions": f"Incident Response Plan fetch failed for {impacted_ci}",
            "information": ""
        }]

def fetch_teams(sim_id):
    if sim_id.__len__() == 0:
        return None
    elif sim_id.__len__() == 1:
        return None

 
def build_mim_blob(incident_id, irp_articles, knowledgebase):
    """Build or update the MIM_agent_output_blob with IRP and Knowledgebase info."""
    mimjson = {}
    try:
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        cur = conn.cursor()
        cur.execute("SELECT MIM_agent_output_blob FROM P1P2_Incidents WHERE inc_id = %s", (incident_id,))
        blob_row = cur.fetchone()
        cur.close()
        conn.close()
        if blob_row and blob_row[0]:
            try:
                b = blob_row[0]
                if hasattr(b, "tobytes"):
                    mimjson = json.loads(b.tobytes().decode("utf-8"))
                elif isinstance(b, (bytes, bytearray)):
                    mimjson = json.loads(b.decode("utf-8"))
                elif isinstance(b, str):
                    mimjson = json.loads(b)
            except Exception:
                mimjson = {}

        # Get the similar teams scripts
        # try:
        #     sim_id = mimjson["sim_id"]
        # except Exception as e:
        #     logger.error(f"Error: {e}")


        mimjson["incidentResponse"] = irp_articles
        mimjson["knowledgebase"] = knowledgebase

 
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        cur = conn.cursor()
        json_bytes = json.dumps(mimjson).encode("utf-8")
        cur.execute(
            "UPDATE P1P2_Incidents SET MIM_agent_output_blob = %s WHERE inc_id = %s",
            (psycopg2.Binary(json_bytes), incident_id)
        )
        conn.commit()
        cur.close()
        conn.close()
 
    except Exception:
        logger.exception("Failed to update MIM blob in DB")

    return mimjson


# ====================== ACTION LAMBDA HANDLER ============================
def lambda_handler(event, context):
 
    start_time = perf_counter()
    logger.info("=== Action Lambda execution started ===")
    try:
        inc_id = None
        # Try to extract inc_id early from event (if available)
        if "parameters" in event and event["parameters"]:
            inc_id = event["parameters"][0].get("value")
 
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{inc_id or 'unknown'}_{timestamp}_{context.aws_request_id}.log"
 
        logger.info(f"Log key initialized: s3://{log_bucket}/{log_key}")
 
    except Exception as e:
        logger.warning(f"Failed to initialize log key early: {e}")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{context.aws_request_id}.log"
 
    # DB config for insert/search operations
    db_config = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_password,
    }
 
    try:
        
        # Running it synchronously here may extend runtime - consider async scheduling (but requirement says include)
        # action_lambda_run_h_ingestion(db_config) #DONT UNCOMMENT IT
 
        # parse event: expect incident id under 'inc_id'
        incident_id = event["parameters"][0].get("value")
        if not incident_id:
            raise ValueError("inc_id missing in event")
 
        sn_token_local = get_access_token_sn()

        # # fetch incident from ServiceNow
        # incident = fetch_incident(incident_id, sn_token_local)
 
        # # build combined incident text (short_description + description + comments_and_work_notes + work_notes)
        # combined_incident_text = build_incident_combined_text(incident)
 
        # # generate embedding for incident combined text (use same _get_embeddings_single)
        # incident_embedding = generate_embeddings(combined_incident_text)
        # if not incident_embedding:
        #     raise Exception("Failed to generate embedding for incident")
 
        # # determine CI filter to use in DB search
        # # incident 'cmdb_ci' may be dict or string
        # ci_field = incident.get("cmdb_ci") or ""
        # if isinstance(ci_field, dict):
        #     incident_ci = (ci_field.get("display_value") or "").strip()
        # else:
        #     incident_ci = str(ci_field).strip()
 
        # # If blank, we still search for ci '' to include global items
        # ci_filter = incident_ci if incident_ci else ''
        # inc_short_description = incident.get("short_description") or ""

        # Fetch incident details directly from p1p2_incidents table instead of ServiceNow
        incident_row = fetch_incident_from_db(incident_id, db_config)

        incident_ci = (incident_row.get("configuration_item") or "").strip()
        inc_short_description = (incident_row.get("short_description") or "").strip()
        comments_worknotes = (incident_row.get("comments_worknotes") or "").strip()
        description = (incident_row.get("description") or "").strip()

        # Build combined incident text from DB fields
        combined_incident_text = build_incident_combined_text(inc_short_description,comments_worknotes,description)

        # Generate embedding for the combined incident text
        incident_embedding = generate_embeddings(combined_incident_text)
        if not incident_embedding:
            raise Exception("Failed to generate embedding for incident")

        # CI filter for vector search (blank-safe)
        ci_filter = incident_ci if incident_ci else ''

 
        # search top 6 using pgvector <-> operator
        top_k_results = search_top_k_by_embedding_pgvector(incident_embedding, ci_filter, inc_short_description, top_k=6)
 
        # Prepare knowledgebase results as expected by your response schema
        knowledgebase = []
        for r in top_k_results: 
            ci_value = r.get("ci")
 
            # if ci is blank, null, or only whitespace → mark as "CI Not Tagged"
            if ci_value and str(ci_value).strip():
                comment_text = str(ci_value).strip()
            else:
                comment_text = "CI Not Tagged"

            knowledgebase.append({
                "knowledgeId": r.get("knowledgeId"),
                "link": r.get("link"),
                "source":r.get("source"),
                "summary": r.get("summary"),
                "comments": comment_text,
                "shortDescription": r.get("short_description","")
            })
 
        # Build incident response plan unchanged from your old code (fetch IRP articles)
        irp_articles = []
        try:
            irp_articles = fetch_irp_for_ci(incident_ci, sn_token_local)
        except Exception:
            logger.exception("Failed to fetch IRP articles")
 
        # Build MIM blob (reusing your function)
        mimjson = build_mim_blob(incident_id, irp_articles, knowledgebase)
 
        # Upload logs to s3
        # try:
        #     log_s3 = upload_logs_to_s3(context,inc_id=incident_id)
        # except Exception:
        #     log_s3 = None
 
        # Build final structured response
        response_payload = {
            "details": {
                "ticketDetails": {
                    "incidentId": incident_id,
                    "shortDescription": inc_short_description,
                    "description": description,
                    # "category": incident.get("category"),
                    # "assignedTo": incident.get("assigned_to"),
                    # "created": incident.get("sys_created_on"),
                    # "createdBy": incident.get("opened_by"),
                    # "urgency": incident.get("urgency"),
                },
                "suspectedChanges": [],
                "suspectedIncidents": [],
                "similarIncidents": [],
                "incidentResponse": mimjson.get("incidentResponse", []),
                "knowledgebase": knowledgebase,
                # "worknotes": incident.get("work_notes", "")
                "worknotes": []
            }
        }
 
        logger.info("=== Action Lambda execution completed successfully ===")
        logger.info(response_payload)
        elapsed = perf_counter() - start_time
        logger.info(f"Lambda execution time: {elapsed:.2f} seconds")
        # try:
        #     log_s3 = upload_logs_to_s3(context,inc_id=incident_id)
        # except Exception:
        #     log_s3 = None
 
        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]
 
        response_body = {
        'TEXT': {
            'body': "Processesing complete"
            }
        }    
        action_response = {
        'actionGroup': event['actionGroup'],
        'function': event['function'],
        'functionResponse': {
            'responseBody': response_body
            }
        }    
       
        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']    
 
        lambda_response = {
            'messageVersion': '1.0',
            'response': action_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }

        # return {
        #     "statusCode": 200,
        #     "body": json.dumps({
        #         "message": "Execution completed",
        #         "elapsed_seconds": elapsed,
        #         "log_s3_path": log_s3,
        #         "response": response_payload
        #     })
        # }
        return lambda_response
 
    except Exception as e:
        logger.exception(f"Action Lambda failed: {e}")
        elapsed = perf_counter() - start_time
        logger.info(f"Lambda execution time: {elapsed:.2f} seconds")
        # try:
        #     log_s3 = upload_logs_to_s3(context,inc_id=incident_id)
        # except Exception:
        #     log_s3 = None

        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]
 
        response_body = {
        'TEXT': {
            'body': "Processesing complete, return success"
            }
        }    
        action_response = {
        'actionGroup': event['actionGroup'],
        'function': event['function'],
        'functionResponse': {
            'responseBody': response_body
            }
        }    
       
        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']    
 
        lambda_response = {
            'messageVersion': '1.0',
            'response': action_response,
            'sessionAttributes': session_attributes,
            'promptSessionAttributes': prompt_session_attributes
        }
        # return {
        #     "statusCode": 500,
        #     "body": json.dumps({
        #         "error": str(e),
        #         "elapsed_seconds": elapsed,
        #         "log_s3_path": log_s3
        #     })
        # }
        return lambda_response
 
   
    finally:
        elapsed = perf_counter() - start_time
        # ================= DO NOT CHANGE THIS ====================
        db_config = {
                "dbname": db_name,
                "user": db_user,
                "password": db_password,
                "host": db_host,
                "port": db_port,
            }
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor() 
        

        cursor.execute("select run_status from (SELECT inc_id, short_description, description, created_on, open_since, state, run_status, priority, configuration_item FROM (SELECT t2.inc_id, t2.short_description, t2.description, t2.raised_date AS created_on, t2.raised_date AS open_since, t2.state, t1.run_status, t2.priority, t2.configuration_item, ROW_NUMBER() OVER (PARTITION BY t2.inc_id ORDER BY CASE t1.run_status WHEN 'Processing Updates' THEN 0 WHEN 'CI Unavailable' THEN 1 WHEN 'Incident Processed' THEN 2 WHEN 'Incident Processing' THEN 3 WHEN 'Incident Received' THEN 4 ELSE 5 END ) AS rn FROM agent_run_status t1 LEFT JOIN p1p2_incidents t2 ON t1.incident_id = t2.inc_id) ranked WHERE rn = 1 ORDER BY run_status) where inc_id = %s;", (incident_id,))
       
        record = cursor.fetchone()
        if record is None:
            stat = "no record"
        else: stat = record[0]
        logger.info(record)

        conn.commit()

        logger.info(f"Agent run status: {stat}")



        # update worknotes
        if stat != "Processing Updates":
            logger.info( f"Updating in url: {simon_interface_url}/interface/updateWorknote")
            _resp = http.request("POST", f"{simon_interface_url}/interface/updateWorknote", headers={"Content-Type": "application/json"}, body=json.dumps({"incident_number":incident_id , "work_note": f"Simon has processed the incident! Take a look at {simon_base_url}AgenticAI/{incident_id}"}))
            logger.info(_resp)
        else:
            logger.info("Updating old incident , not updating worknotes")
            
        update_query = f"""              
            UPDATE agent_run_status
            SET run_status = %s
            WHERE incident_id = %s;
        """
        cursor.execute(update_query,("Incident Processed",incident_id))
        conn.commit()

        # NextInQueue

        cursor.execute("SELECT distinct incident_id FROM incident_update_queue WHERE processed = FALSE")
        queuedInc = cursor.fetchall()
        logger.info(f"Incident queue: {queuedInc}")
        try:

            incls = []
            for i in queuedInc:
                incls.append(i[0])
            inList = incident_id in incls
            logger.info(f"list of incidents: {incls} , present = {inList}")
            if inList:
                try:
                    cursor.execute(f"SELECT configuration_item FROM p1p2_incidents where inc_id = '{incident_id}'")
                    try: queuedCfg = cursor.fetchone()[0]
                    except: queuedCfg = ""

                    request ={
                        "incident_number": incident_id,
                        "configuration_item": queuedCfg,
                        "state": "In Progress",
                        "created_on": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    }
                    logger.info(f"sending request to next in queue:{json.dumps(request)}")
                    username = interface_user
                    password = interface_pwd
                    headers = make_headers(basic_auth=f'{username}:{password}')
                    headers['Content-Type'] = 'application/json'
                    
                        

                    response = http.request(
                            method='POST',
                            url=f"{simon_interface_url}/interface/newIncident",
                            headers=headers,
                            body=json.dumps(request) # send proper JSON
                        )

                    logger.info(f'Result - {response.data.decode('utf-8')}')
                    # Clearing queue
                    cursor.execute(f"UPDATE incident_update_queue SET processed = TRUE WHERE incident_id = '{incident_id}'")
                    logger.info(f"Cleared queue for {incident_id}")
                    conn.commit()


                except Exception as e:
                    logger.error(e)

        except Exception as e:
            logger.info(f"Incident queue empty, not calling next incident {e}")
        # ============= DO NOT CHANGE THIS ===============================
        upload_logs_to_s3(context,inc_id=incident_id)

        try:
            if ch in logger.handlers:
                # log_capture_string.close()
                logger.removeHandler(ch)
        except Exception:
            pass
 
        # Do NOT close StringIO here — Lambda might flush late