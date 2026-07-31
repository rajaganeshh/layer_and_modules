import os
import json
import boto3
import logging
import psycopg2
import requests
import tempfile
import shutil
import numpy as np
import asyncio
from datetime import datetime, timedelta, timezone
from time import perf_counter
from botocore.exceptions import ClientError
from sharepointProcess import *
import requests
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
import traceback
import os
from urllib.parse import urlparse, unquote
import logging
import io
import json

# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']
# ====================== LOGGER ============================
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)

# Get logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)

# =====================================================
# RETRIEVE SECRETS
# =====================================================
def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)
    secret = json.loads(client.get_secret_value(SecretId=secret_name)["SecretString"])
    return json.loads(secret['configPythonSecrets'])

config = get_secret(secret_name, region_name)

region_name = config['awsRegion']
db_conf = config['database']
llm_model = config['bedrock']['llm']
embedding_model = config['bedrock']['embedding']

db_config = {
    "dbname": db_conf['name'],
    "user": db_conf['user'],
    "password": db_conf['password'],
    "host": db_conf['host'],
    "port": db_conf['port'],
}

TENANT_ID = config['sharePoint']['tenantId']
CLIENT_ID = config['sharePoint']['clientId']
CLIENT_SECRET = config['sharePoint']['clientSecret']
SITE_NAMES = config['config']['sharePoint']
HOST_NAME = config['sharePoint']['baseUrl']

all_sites = SITE_NAMES['sites']

# =====================================================
# DATABASE INSERT
# =====================================================
def insert_knowledge_vec(data, db_config):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
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
            check_query = f"SELECT uid FROM knowledge_vec WHERE knowledge_id = '{row['knowledge_id']}'"
            cur.execute(check_query)
            result = cur.fetchone()
            if result:
                logger.info(f"Record with knowledge_id {row['knowledge_id']} already exists. Updating the record.")
                delete_query = f"DELETE FROM knowledge_vec WHERE knowledge_id = '{row['knowledge_id']}'"
                cur.execute(delete_query)
                conn.commit()
                cur.execute(insert_query, row)
                conn.commit()
            
            else:
                cur.execute(insert_query, row)
                conn.commit()
        
        # logger.info("Inserted record(s) successfully.")
    except Exception as e:
        # logger.exception(f"Database insertion error: {e}")
        logger.info(f"Database insertion error: {e}")
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

# =====================================================
# BEDROCK EMBEDDINGS
# =====================================================
MAX_CHARS = 18000
OVERLAP = 500

def chunk_text(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    chunks, start, text_len = [], 0, len(text)
    while start < text_len:
        end = min(start + max_chars, text_len)
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks

def _get_embeddings_single(model_id, input_text):
    client = boto3.client("bedrock-runtime", region_name=region_name)
    chunks = chunk_text(input_text)
    embeddings = []
    for chunk in chunks:
        body = json.dumps({"inputText": chunk})
        response = client.invoke_model(modelId=model_id, body=body)
        model_response = json.loads(response["body"].read())
        embeddings.append(model_response["embedding"])
    return np.mean(embeddings, axis=0).tolist()

# =====================================================
# TEAMS GRAPH API HELPERS
# =====================================================
 
# Time filter: 3 years ago
#three_years_ago = datetime.now(timezone.utc) - timedelta(days=3*365)
last_24_hours = datetime.now(timezone.utc) - timedelta(hours=24)

def get_site(HOSTNAME, SITE_PATH, headers):
    url = f"https://graph.microsoft.com/v1.0/sites/{HOSTNAME}:/{SITE_PATH}"
    res = requests.get(url, headers=headers).json()
    return res

def get_subsites(site_id, headers):
    subsites = []
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/sites"
    res = requests.get(url, headers=headers).json()
    subsites.extend(res.get('value', []))
    return subsites
 
def get_drives(site_id, headers):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    res = requests.get(url, headers=headers).json()
    return res.get('value', [])
 
def get_files_recursive(drive_id, headers, folder_id=None):
    files = []
    if folder_id:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
    else:
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
 
    res = requests.get(url, headers=headers).json()
    for item in res.get('value', []):
        if item.get('folder'):
            files.extend(get_files_recursive(drive_id, headers, item['id']))
        #elif item['name'].lower().endswith('.pdf') or item['name'].lower().endswith('.docx') or item['name'].lower().endswith('.xlsx') or item['name'].lower().endswith('.pptx'):
        else:
            created = datetime.fromisoformat(item['createdDateTime'].replace('Z', '+00:00'))
            modified = datetime.fromisoformat(item['lastModifiedDateTime'].replace('Z', '+00:00'))
           
            if created >= last_24_hours or modified >= last_24_hours:
                files.append(item)
   
    for file in files:
        item_id = file['id']
        listitem_url = f'https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/listItem?$expand=fields'
        listitem_response = requests.get(listitem_url, headers=headers)
        if listitem_response.status_code == 200:
            fields = listitem_response.json().get('fields', {})
            #logger.info(json.dumps(fields,indent=3))
            if "ConfigurationItem" in fields:
                file["ConfigurationItem"] = fields["ConfigurationItem"]
            elif "ITTags" in fields:
                ittags = fields["ITTags"]
                cis = "_".join(ittags.split("\n"))
                file["ConfigurationItem"] = cis
            else:
                file["ConfigurationItem"] = ""
    return files


def download_file_from_url(item, download_path):
    site_id = item['parentReference']['siteId']
    drive_id = item['parentReference']['driveId']

    item_id = item['id']
    download_url = item.get('@microsoft.graph.downloadUrl')
 
    if not download_url:
        #logger.info(f"No download URL for item ID: {item_id}")
        return
 
    # Create a unique filename
    unique_filename = f"{site_id}_{drive_id}_{item_id}"
    file_extension = os.path.splitext(item['name'])[1]  # Preserve original extension
    full_filename = unique_filename + file_extension
 
    os.makedirs(download_path, exist_ok=True)
    file_path = os.path.join(download_path, full_filename)
 
    try:
        response = requests.get(download_url, stream=True, verify=False)
        response.raise_for_status()
 
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded: {full_filename}")
        summary = sharepoint_helper(file_path)
        
        return summary
        
    except Exception as e:
        logger.info(f"Download failed for {full_filename}: {str(e)}")

def sharepoint_invoker(download_path:str = "files/"):
    try:
        # Authenticate and get the access token
        auth_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(auth_url, data=auth_data)
        
        access_token = response.json()['access_token']
        if response.status_code==200: 
            logger.info(f"Fetched access token")
        else:
            logger.error(f"Error in fetching access token")
        #logger.info(f"Access Token retrieved successfully")
        
        # headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Prefer': 'HonorNonIndexedQueriesWarningMayFailRandomly'
        }

        # ======================= SHAREPOINT & TEAMS PROCESSING =======================
        all_files = []
        # For given sites
        logger.info(f"Processing given sites...")
        for site_uri in tqdm(all_sites):

            parsed = urlparse(site_uri)
            paths = parsed.path.strip("/").split("/")
            site_path = "/".join(paths[1:])
            logger.info(f"Processing SharePoint Site path : {site_path}")
            site = get_site(HOST_NAME, site_path, headers)
            site_id = site['id']
            logger.info(f"Processing site: {site['name']}")

            # Include subsites
            subsites = get_subsites(site_id, headers)
            all_site_ids = [site_id] + [s['id'] for s in subsites]
    
            for sid in all_site_ids:
                drives = get_drives(sid, headers)
                logger.info(f"  Found {len(drives)} drives in site ID {sid}")
                for drive in tqdm(drives):
                    logger.info(f"  Drive: {drive['name']}")
                    files = get_files_recursive(drive['id'], headers)
                    logger.info(f"    Found {len(files)} files in drive '{drive['name']}'")
                    for file in tqdm(files):
                        logger.info(f"Processing file: {file['name']}")
                        if file['name'].lower().endswith('.pdf') or file['name'].lower().endswith('.docx') or file['name'].lower().endswith('.xlsx') or file['name'].lower().endswith('.pptx'):
                            try:
                                summary = download_file_from_url(file, download_path=download_path)
                                embedding = _get_embeddings_single(embedding_model, summary)
                                record = {
                                    "ci": file["ConfigurationItem"],
                                    "chunk": "",
                                    "embedding": embedding,
                                    "knowledge_id": file['id'],
                                    "knowledge_type": "",
                                    "source": "Sharepoint",
                                    "link": file['webUrl'],
                                    "summary": f"{file['name']}:{summary}",
                                }
                            except Exception as e:
                                logger.info(f"Error processing file {file['name']}: {traceback.format_exc()}")
                                continue
                        else:
                            record = {
                                "ci": file["ConfigurationItem"],
                                "chunk": "",
                                "embedding": None,
                                "knowledge_id": file['id'],
                                "knowledge_type": "",
                                "source": "Sharepoint",
                                "link": file['webUrl'],
                                "summary": f"{file['name']}: Unsupported file type for summary.",
                            }
                        insert_knowledge_vec([record], db_config)
                        logger.info(f"Inserted data for file: {file['name']}")
                    all_files.extend(files)

        logger.info(f"Total files found (last 24 hrs): {len(all_files)}")
        
        if os.path.exists(download_path) and os.path.isdir(download_path):
            shutil.rmtree(download_path)
        #shutil.rmtree(download_path)

        # ======================= CONFLUENCE & SNOW PROCESSING =======================
        # Add kaustavs code here

    except Exception as e:
        logger.info(f"Error in sharepoint invoker : {traceback.format_exc()}")
        raise
    
    # finally:
    #     return log_capture_string

# Discuss during deployment
# main(full_site_run=False, download_path="files/")
