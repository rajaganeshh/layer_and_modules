import os
import re
import json
from time import timezone
import boto3
import logging
import io
import urllib3
from urllib.parse import urlencode
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import psycopg2

try:
    from new_kg_generator import create_triplet_kg
    from new_summarize import summarize_text
except ImportError:
    from kg_generator import create_triplet_kg
    from summarize import summarize_text

http = urllib3.PoolManager()

# ====================== ENV ============================

secret_name = os.environ["secret_name"]
region_name = os.environ["region_name"]

# Hard-coded CI allowlist requested for scheduled execution.
ALLOWED_CIS = {"TBox (Travelbox)", "VAA WebSite"}


def _normalize_text(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _build_ci_signatures(ci_name):
    signatures = set()

    base = _normalize_text(ci_name)
    if base:
        signatures.add(base)

    # Include both outer and inner parts: "TBox (Travelbox)" -> "tbox", "travelbox"
    inner_parts = re.findall(r"\((.*?)\)", ci_name)
    for part in inner_parts:
        norm = _normalize_text(part)
        if norm:
            signatures.add(norm)

    outer = re.sub(r"\(.*?\)", " ", ci_name)
    outer_norm = _normalize_text(outer)
    if outer_norm:
        signatures.add(outer_norm)

    for part in re.split(r"[-/,&]|\band\b", ci_name, flags=re.IGNORECASE):
        norm = _normalize_text(part)
        if norm:
            signatures.add(norm)

    return {sig for sig in signatures if len(sig) >= 3}


ALLOWED_CI_SIGNATURES = {
    ci_name: _build_ci_signatures(ci_name) for ci_name in ALLOWED_CIS
}

# ====================== LOGGER ============================

# Set up in-memory logging
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)

# Get logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

# ====================== SECRETS ============================

def get_secret(secret_name, region_name):
    # Fetch a secret from AWS Secrets Manager
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response["SecretString"])
    configPythonSecrets = json.loads(secret["configPythonSecrets"])
    return configPythonSecrets


configPythonSecrets = get_secret(secret_name, region_name)

# db_secret_name = configPythonSecrets['database'][]
region_name = configPythonSecrets["awsRegion"]
sn_client_id = configPythonSecrets["serviceNow"]["clientId"]
sn_client_secret = configPythonSecrets["serviceNow"]["clientSecret"]
sn_token_url = configPythonSecrets["serviceNow"]["tokenUrl"]
sn_base_url = configPythonSecrets["serviceNow"]["baseUrl"]
db_host = configPythonSecrets["database"]["host"]
db_port = configPythonSecrets["database"]["port"]
db_name = configPythonSecrets["database"]["name"]
db_user = configPythonSecrets["database"]["user"]
db_password = configPythonSecrets["database"]["password"]
llm_model = configPythonSecrets["bedrock"]["llm"]
embedding_model = configPythonSecrets["bedrock"]["embedding"]
log_bucket = configPythonSecrets["lambdaLog"]["bucket"]
log_prefix = configPythonSecrets["lambdaLog"]["prefix"]

# ====================== LAMBDA HANDLER ===========================

def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client("s3")

    try:
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")

        # === Fetch knowledge articles with broad published query ===
        # Then enforce CI in code using ALLOWED_CIS.
        target_query = "workflow_state=Published"
        token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
        articles = get_knowledge_articles(token, query=target_query)
        logger.info(f"Fetched {len(articles)} specific knowledge articles for embedding")

        extracted_ci_candidates = [_extract_ci_name(item) for item in articles]
        filtered_articles = [
            item
            for item, ci_name in zip(articles, extracted_ci_candidates)
            if _is_allowed_ci(ci_name)
        ]
        logger.info(
            "Filtered to allowed CIs: %s -> %s",
            sorted(ALLOWED_CIS),
            len(filtered_articles),
        )
        if not filtered_articles:
            logger.warning(
                "No CI matches found. Sample extracted CI values: %s",
                extracted_ci_candidates[:10],
            )

        # === Format and embed (KI_push) ===
        KI_push = _format_ki_snow(filtered_articles)
        logger.info(f"Formatted {len(KI_push)} knowledge articles")
        logger.info(KI_push)

        # === Insert into knowledge_vec DB ===
        # db_secret = get_secret(db_secret_name, region_name)
        db_config = {
            "dbname": db_name,
            "user": db_user,
            "password": db_password,
            "host": db_host,
            "port": db_port,
        }
        insert_knowledge_vec(KI_push, db_config)

        logger.info("Processing completed")

        # Upload logs to s3
        log_contents = log_capture_string.getvalue()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{context.aws_request_id}.log"

        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType="text/plain",
        )

        logger.info(f"Logs uploaded to s3://{log_bucket}/{log_key}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Knowledge articles embedded & stored",
                    "count": len(KI_push),
                    "allowed_cis": sorted(ALLOWED_CIS),
                    "log_location": f"s3://{log_bucket}/{log_key}",
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")

        # Upload error logs
        log_contents = log_capture_string.getvalue()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = (
            f"{log_prefix}/{context.function_name}/"
            f"{datetime.today().strftime('%Y-%m-%d')}/"
            f"error_{timestamp}_{context.aws_request_id}.log"
        )
        try:
            s3_client.put_object(
                Bucket=log_bucket,
                Key=log_key,
                Body=log_contents,
                ContentType="text/plain",
            )
        except:
            pass

        raise e

    finally:
        logger.removeHandler(ch)


# ================= API CALLS ===============================

def get_access_token(client_id, client_secret, token_url):
    # Retrieve OAuth2 access token
    token_params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    encoded_params = urlencode(token_params)

    response = http.request(
        "POST",
        token_url,
        body=encoded_params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status == 200:
        token_data = json.loads(response.data.decode("utf-8"))
        return token_data["access_token"]
    else:
        raise Exception(
            f"Failed to get access token: {response.status} - {response.data}"
        )


def get_knowledge_articles(access_token, query=None):

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    # Calculate 72 hours ago
    # end_time = datetime.now(timezone.utc)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=72)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    if query:
        logger.info(f"Fetching knowledge articles with custom query: {query}")
    else:
        logger.info(f"Fetching knowledge articles updated since: {start_time_str}")

    params = {
        "sysparm_query": query if query else f"sys_updated_on>={start_time_str}^workflow_state=published",
        "sysparm_display_value": "True",
        "sysparm_limit": 1000,
        "sysparm_offset": 0,
    }

    all_articles = []
    total_fetched = 0

    while True:
        api_url = f"{sn_base_url}/api/now/table/kb_knowledge"
        response = http.request("GET", api_url, headers=headers, fields=params)

        if response.status != 200:
            raise Exception(
                f"Failed to fetch knowledge articles: {response.status} - {response.data}"
            )

        data = json.loads(response.data.decode("utf-8"))
        results = data.get("result", [])

        if not results:
            logger.info("No more knowledge articles to fetch")
            break

        all_articles.extend(results)
        total_fetched += len(results)

        logger.info(f"Fetched batch: {len(results)} (total: {total_fetched})")

        if len(results) < params["sysparm_limit"]:
            break

        params["sysparm_offset"] += params["sysparm_limit"]

        if total_fetched >= 10000:  # safety cutoff
            logger.warning("Reached maximum fetch limit of 10000 records")
            break

    logger.info(f"Total knowledge articles fetched: {len(all_articles)}")
    return all_articles


def _extract_ci_name(item):
    ci = item.get("cmdb_ci")
    if isinstance(ci, dict):
        ci_display = (ci.get("display_value") or "").strip()
        if ci_display:
            canonical_ci = _canonical_ci_from_text(ci_display)
            return canonical_ci if canonical_ci else ci_display
    if isinstance(ci, str):
        ci_str = ci.strip()
        if ci_str:
            canonical_ci = _canonical_ci_from_text(ci_str)
            return canonical_ci if canonical_ci else ci_str

    # Fallback when cmdb_ci is not available in KB records.
    short_description = item.get("short_description")
    if isinstance(short_description, dict):
        short_description = short_description.get("display_value") or ""

    if isinstance(short_description, str):
        short_description = short_description.strip()
        if not short_description:
            return ""

        canonical_ci = _canonical_ci_from_text(short_description)
        if canonical_ci:
            return canonical_ci

    return ""


def _canonical_ci_from_text(text):
    text_norm = _normalize_text(text)
    if not text_norm:
        return ""

    padded_text = f" {text_norm} "
    for canonical_ci, signatures in ALLOWED_CI_SIGNATURES.items():
        for signature in signatures:
            if text_norm == signature or f" {signature} " in padded_text:
                return canonical_ci

    return ""


def _is_allowed_ci(ci_name):
    return bool(_canonical_ci_from_text(ci_name))


# ===================== UTILS ==================

def _get_embeddings(model_id, input_text):

    client = boto3.client("bedrock-runtime", region_name=region_name)

    native_request = {"inputText": input_text}
    request = json.dumps(native_request)

    response = client.invoke_model(modelId=model_id, body=request)
    model_response = json.loads(response["body"].read())
    embedding = model_response["embedding"]

    return embedding


def _format_ki_snow(articles):

    KI_push = []
    source = "ServiceNow"

    for item in articles:

        ci = _extract_ci_name(item)
        logger.info(f"Contents of ci : {str(ci)}")
        logger.info(f"Data type of ci : {type(ci)}")
        text = item.get("text")
        logger.info(f"Data type of text : {type(text)}")
        kg_data = json.dumps(create_triplet_kg(text, region_name, llm_model))
        logger.info(f"Data type of kg_data : {type(kg_data)}")
        knowledge_id = item.get("number")
        logger.info(f"Data type of knowledge_id : {type(knowledge_id)}")
        embedding = generate_json_embeddings(text)
        logger.info(f"Data type of embedding : {type(embedding)}")
        summary = summarize_text(text, region_name, llm_model)
        logger.info(f"Data type of summary : {type(summary)}")
        # link = item.get("kb_knowledge_base", {}).get("link")
        kb_knowledge_base = item.get("kb_knowledge_base", {}).get("display_value")
        logger.info(f"Data type of kb_knowledge_base : {type(kb_knowledge_base)}")

        record = {
            "ci": ci,
            "chunk": str(kg_data),
            "embedding": embedding,
            "knowledge_id": knowledge_id,
            "knowledge_type": kb_knowledge_base,
            "source": source,
            "link": "",
            "summary": summary,
        }
        KI_push.append(record)

    return KI_push


def _format_ki_confluene():
    pass


def _format_ki_sharepoint():
    pass


# ================== EMBEDDING ==================

def generate_json_embeddings(text):
    # Generate embeddings for KG JSON representation
    kg_data = create_triplet_kg(text, region_name, llm_model)
    kg_text = json.dumps(kg_data, ensure_ascii=False)
    embedding = _get_embeddings(embedding_model, kg_text)
    return embedding


# ================== DATABASE INSERT ==================

def insert_knowledge_vec(data, db_config):
    # Insert embedded knowledge articles into Postgres
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO knowledge_vec (
            ci,
            chunk,
            embedding,
            knowledge_id,
            knowledge_type,
            source,
            link,
            summary
        )
        SELECT
            %(ci)s,
            %(chunk)s,
            %(embedding)s,
            %(knowledge_id)s,
            %(knowledge_type)s,
            %(source)s,
            %(link)s,
            %(summary)s
        WHERE NOT EXISTS (
            SELECT 1
            FROM knowledge_vec kv
            WHERE kv.source = %(source)s
              AND kv.knowledge_id = %(knowledge_id)s
        )
        """

        seen_keys = set()
        rows_to_insert = []
        skipped_in_batch = 0
        inserted_count = 0

        for row in data:
            dedupe_key = (row.get("source"), row.get("knowledge_id"))
            if dedupe_key in seen_keys:
                skipped_in_batch += 1
                continue
            seen_keys.add(dedupe_key)
            rows_to_insert.append(row)

        for row in rows_to_insert:

            cursor.execute(insert_query, row)
            inserted_count += cursor.rowcount

        conn.commit()
        skipped_existing = len(rows_to_insert) - inserted_count
        logger.info(
            "Knowledge insert summary - received: %s, inserted: %s, skipped_existing: %s, skipped_in_batch: %s",
            len(data),
            inserted_count,
            skipped_existing,
            skipped_in_batch,
        )

    except Exception as e:
        logger.exception(f"Error inserting data: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()
