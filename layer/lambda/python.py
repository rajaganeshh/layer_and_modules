import json
import boto3
import logging
import psycopg2
import urllib3
from urllib.parse import urlencode
from botocore.exceptions import ClientError
from datetime import datetime
from time import perf_counter


from kg_generator import create_triplet_kg
from summarize import summarize_text


http = urllib3.PoolManager()

# ====================== ENV ============================
secret_name = "arn:aws:secretsmanager:eu-west-1:XXXXXX:secret:SecretName"
region_name = "eu-west-1"

# ====================== LOGGER ============================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ====================== SECRETS ============================

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e

    secret = json.loads(get_secret_value_response["SecretString"])
    configPythonSecrets = json.loads(secret['configPythonSecrets'])
    return configPythonSecrets


configPythonSecrets = get_secret(secret_name, region_name)

region_name = configPythonSecrets['awsRegion']
sn_client_id = configPythonSecrets['serviceNow']['clientId']
sn_client_secret = configPythonSecrets['serviceNow']['clientSecret']
sn_token_url = configPythonSecrets['serviceNow']['tokenUrl']
sn_base_url = configPythonSecrets['serviceNow']['baseUrl']
db_host = configPythonSecrets['database']['host']
db_port = configPythonSecrets['database']['port']
db_name = configPythonSecrets['database']['name']
db_user = configPythonSecrets['database']['user']
db_password = configPythonSecrets['database']['password']
llm_model = configPythonSecrets['bedrock']['llm']
embedding_model = configPythonSecrets['bedrock']['embedding']


# ================= API CALLS ===============================

def get_access_token(client_id, client_secret, token_url):
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

def get_day0_knowledge_articles(access_token, ci_list=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    if ci_list and len(ci_list) > 0:
        ci_query = "^OR".join([f"cmdb_ci={ci}" for ci in ci_list])
        sysparm_query = f"workflow_state=published^{ci_query}"
    else:
        sysparm_query = "workflow_state=published"

    params = {
        "sysparm_query": sysparm_query,
        "sysparm_display_value": "true",
        "sysparm_limit": 2000,
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
            break

        all_articles.extend(results)
        total_fetched += len(results)
        logger.info(f"Fetched batch: {len(results)} (total: {total_fetched})")

        if len(results) < params["sysparm_limit"]:
            break

        params["sysparm_offset"] += params["sysparm_limit"]

        if total_fetched >= 50000:
            logger.warning("Reached maximum fetch limit of 50000 records")
            break

    logger.info(f"Total knowledge articles fetched (Day0): {len(all_articles)}")
    return all_articles

# ===================== UTILS ==================

def _get_embeddings( model_id, input_text):
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
        ci = item.get("cmdb_ci")
        logger.info(f"Contents of ci : {str(ci)}")
        if item.get("cmdb_ci"):
            ci = ci.get("display_value")
        text = item.get("text")

        kg_data = create_triplet_kg(text, region_name, llm_model)
        knowledge_id = item.get("number")
        embedding = generate_json_embeddings(text)
        summary = summarize_text(text, region_name, llm_model)
        kb_knowledge_base = item.get("kb_knowledge_base", {}).get("display_value")

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

def generate_json_embeddings(text):
    kg_data = create_triplet_kg(text, region_name, llm_model)
    kg_text = json.dumps(kg_data, ensure_ascii=False)
    embedding = _get_embeddings(embedding_model, kg_text)
    return embedding

# ================== DATABASE INSERT ==================

def insert_knowledge_vec(data, db_config):
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
        VALUES (
            %(ci)s,
            %(chunk)s,
            %(embedding)s,
            %(knowledge_id)s,
            %(knowledge_type)s,
            %(source)s,
            %(link)s,
            %(summary)s
        )
        """

        for row in data:
            cursor.execute(insert_query, row)

        conn.commit()
        logger.info("Knowledge articles with embeddings inserted successfully!")

    except Exception as e:
        logger.exception(f"Error inserting data: {e}")

    finally:
        if conn:
            cursor.close()
            conn.close()

# ================== MAIN EXECUTION ==================

def update_table():
    try:
        logger.info("Starting Day0 script...")
        token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)


        # for company-name testing 
        # ci_test_list = [
        #     "e4cf2c921b011d10d91ba792f54bcb47",
        #     "347ffccec316a2108d66fd2a0501312d",
        #     "5d34844247a342d4922be359736d439d",
        #     "1dd9e33ac33faa14d229d4a6050131f0",
        #     "0401e5d51b029614d80a83a5464bcb9b",
        #     "411f811ac390ae548d66fd2a050131f9",
        # ]

        #for tcs testing
        ci_test_list = ["b0c4030ac0a800090152e7a4564ca36c",
                        "281a4d5fc0a8000b00e4ba489a83eedc"
        ]

        # for inserting all document present in servicenow 
        # ci_test_list = []

        t_start = perf_counter()
        articles = get_day0_knowledge_articles(token, ci_test_list)
        KI_push = _format_ki_snow(articles)

        db_config = {
            "dbname": db_name,
            "user": db_user,
            "password": db_password,
            "host": db_host,
            "port": db_port,
        }

        insert_knowledge_vec(KI_push, db_config)

        t_end = perf_counter()
        logger.info(f"Inserted {len(KI_push)} knowledge articles")
        logger.info(f"Elapsed time: {t_end - t_start:.2f} seconds")

    except Exception as e:
        logger.error(f"Error: {e}")

# ================== LAMBDA HANDLER ==================
def lambda_handler(event, context):
    update_table()
    return {"statusCode": 200, "body": "Inserted knowledge articles"}
