import json
import asyncio
import aiohttp
import boto3
from datetime import datetime, timedelta
import logging
import os
from typing import List, Dict, Any, Optional
import io
import urllib3
from urllib.parse import urlencode
from botocore.exceptions import ClientError
import psycopg2
import warnings
from time import sleep
import traceback
import re

http = urllib3.PoolManager()
 
# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']
# ====================== LOGGER ============================
 
# Configuration
# bucket_name = os.environ.get('LOG_BUCKET_NAME', 'easyjet-app-logs')
# log_prefix = os.environ.get('LOG_PREFIX', 'lambda-logs')
 
# Set up in-memory logging
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)

#formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
formatter = logging.Formatter('{"asctime": "%(asctime)s", "levelname": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "pathname": "%(pathname)s", "lineno": %(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S') 
ch.setFormatter(formatter)

# Get logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
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
bedrockKey = configPythonSecrets['bedrock']['key']
log_bucket = configPythonSecrets['lambdaLog']['bucket']
log_prefix = configPythonSecrets['lambdaLog']['prefix']
 
# ====================== LAMBDA HANDLER ===========================
 
def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
 
    # Business logic
    try:
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")

        # ========== Initialize logger here ================

        inc_id = event["parameters"][0]["value"]
        logger.info(f"====EVENT ID===={inc_id}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{inc_id}_{timestamp}_{context.aws_request_id}.log"

        log_contents = log_capture_string.getvalue()

        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )

        result = fetch_relevant_changes(inc_id)
        logger.info(f"Lambda Processing completed!!")
       
        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]
 
        response_body = {
        'TEXT': {
            'body': "Success"
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

        logger.info(f"\n===================RETURNING PAYLOAD==========\n{lambda_response}")
        
        logger.info(f"Uploading logs to s3://{log_bucket}/{log_key}")
        
        log_contents = log_capture_string.getvalue()
        
        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
        
        logger.removeHandler(ch)
 
        return lambda_response
       
       
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        # Still try to upload logs even if there's an error
        log_contents = log_capture_string.getvalue()
        # timestamp = datetime.strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/error_{inc_id}_{timestamp}_{context.aws_request_id}.log"
       
        session_attributes = event['sessionAttributes']
        prompt_session_attributes = event['promptSessionAttributes']    

        lambda_response = {
            "messageVersion": "1.0",
            "response": traceback.format_exc(),
            "sessionAttributes": session_attributes,
            "promptSessionAttributes": prompt_session_attributes,
        }

        logger.info(f"\n===================RETURNING PAYLOAD==========\n{lambda_response}")
        
        action_response = {
        "actionGroup": event["actionGroup"],
        "responseBody": traceback.format_exc(),
        }
 
        try:
            s3_client.put_object(
                Bucket=log_bucket,
                Key=log_key,
                Body=log_contents,
                ContentType='text/plain'
            )
        except:
            pass  # If S3 upload fails, don't crash the function
       
        return lambda_response
 
    finally:
        # Clean up
        logger.removeHandler(ch)
 
# ================= API CALLS ===============================
 
def get_access_token(client_id, client_secret, token_url):
   
    token_params = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
   
    encoded_params = urlencode(token_params)
   
    # response = requests.post(token_url, data = paylaod, auth=(client_id, client_secret), verify=False)
    response = http.request('POST', token_url, body = encoded_params,
                            headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status == 200:
        token_data = json.loads(response.data.decode('utf-8'))
        return token_data['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status} - {response.data}")
 
# ================= UTILS ===============================

email_pii = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
phone_pii = r"\+\d{8,}[\d\s\-\(\)]*"

def _llm_(prompt, region_name = region_name , llm_model = llm_model):
   
    input_text = re.sub(email_pii, "[EMAIL_REDACTED]", prompt)
    prompt = re.sub(phone_pii, "[PHONE_REDACTED]", input_text)

    client = boto3.client("bedrock-runtime", region_name=region_name)
    
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

def _get_embeddings(embedding_model, bedrockKey, region_name, input_text):
   
    input_text = re.sub(email_pii, "[EMAIL_REDACTED]", input_text)
    input_text = re.sub(phone_pii, "[PHONE_REDACTED]", input_text)
 
    #os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bedrockKey
    client = boto3.client("bedrock-runtime", region_name=region_name)
 
    # Create the request for the model.
    native_request = {"inputText": input_text}
 
    # Convert the native request to JSON.
    request = json.dumps(native_request)
 
    # Invoke the model with the request.
    response = client.invoke_model(modelId=embedding_model, body=request)
 
    # Decode the model's native response body.
    model_response = json.loads(response["body"].read())
 
    # Extract and print the generated embedding and the input text token count.
    embedding = model_response["embedding"]
    return embedding
 
def _format_(response):
   
    VecJson = []
    #print(json.dumps(response,indent=3))
    for item in response["changes"]:
       
        # Need to change this
        _chunk = {
            "sys_id": item["sys_id"],
            "number": item["number"],
            "start_date": item["start_date"],
            "end_date": item["end_date"],
            "sys_updated_on": item["sys_updated_on"],
            "sys_created_on": item["sys_created_on"],
            "cmdb_ci": item["cmdb_ci"],
            "business_service": item["business_service"],
            "assignment_group": item["assignment_group"],
            "category": item["category"],
            "impact": item["impact"],
            "priority": item["priority"],
            "short_description": item["short_description"],
            "description": item["description"],
            "justification": item["justification"],
            "risk_impact_analysis": item["risk_impact_analysis"],
            "implementation_plan": item["implementation_plan"],
            "backout_plan": item["backout_plan"],
            "test_plan": item["test_plan"],
            # "u_post_implementation_testing": item["u_post_implementation_testing"],
            # "u_relevant_documentation_updated": item["u_relevant_documentation_updated"],
            # "comments_and_work_notes": item["comments_and_work_notes"],
            # "upon_reject": item["upon_reject"]
        }
 
        # Need to change this
        if item["cmdb_ci"]:
            _summary = f"Configuration item {item['cmdb_ci']['display_value']} has been raised with a change: {item['short_description']}"
            _chunk_sent = f"Configuration item {item['cmdb_ci']['display_value']} has: {item['short_description']}, as given in:{item["description"]}. raised on: {item['sys_created_on']}. "
        else:
            _summary = f"New change without CI has been raised: {item['short_description']}"
            _chunk_sent = f"Configuration item None has: {item['short_description']}, as given in:{item["description"]}. raised on: {item['sys_created_on']}. "
       
        try:
            cin = "None"
            if item["cmdb_ci"]:
                cin = item["cmdb_ci"]["display_value"]
            VecItem  = {
                "chg_id": item["number"],
                "chunk": str(_chunk),
                "embedding": _get_embeddings(embedding_model, bedrockKey, region_name, _chunk_sent),
                "ci": cin,
                "link":f"{sn_base_url}/nav_to.do?uri=change_request.do?sys_id={item['sys_id']}",
                "summary":_summary
            }
            VecJson.append(VecItem)
        except Exception as e:
            logger.error(f"Error occured while formatting the data bob!! : {e}")
   
    return VecJson
 
# ================== Database Insert ==================
 
def insert_vector_data(data, db_config):  
    try:  
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
 
        # SQL Insert Statement  
        insert_query = """  
        INSERT INTO change_history_vec (  
            chg_id,  
            chunk,  
            embedding,  
            ci,  
            link,  
            summary  
        ) VALUES (  
            %(chg_id)s,  
            %(chunk)s,  
            %(embedding)s,  
            %(ci)s,  
            %(link)s,  
            %(summary)s
        )  
       
        ON CONFLICT (chg_id) DO UPDATE SET
            chunk = EXCLUDED.chunk,
            embedding = EXCLUDED.embedding,
            ci = EXCLUDED.ci,
            link = EXCLUDED.link,
            summary = EXCLUDED.summary;
 
        """  
 
        # Execute the query  
        for row in data:  
            cursor.execute(insert_query, row)  
 
        # Commit the transaction  
        conn.commit()  
        logger.info("Data inserted successfully!")  
 
    except Exception as e:  
        logger.error("An error occurred:", e)  
 
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()
 
# ================= Main Logic ===============================
 
class ServiceNowChangesProcessor:
    def __init__(self, instance_url: str, access_token: str):
        self.base_url = f"{instance_url}/api/now/table"
        self.session = None
        self.semaphore = asyncio.Semaphore(10)  # Reduced for Lambda
       
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
       
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
       
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
           
    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make API request with error handling and rate limiting"""
        async with self.semaphore:
            try:
                url = f"{self.base_url}/{endpoint}"
                logger.debug(f"Making request to: {endpoint}")
               
                async with self.session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                   
                    result_count = len(data.get('result', []))
                    logger.debug(f"Request to {endpoint} returned {result_count} records")
                   
                    return data
                   
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error for {endpoint}: {e}")
                return {"result": []}
            except Exception as e:
                logger.error(f"Unexpected error for {endpoint}: {e}")
                return {"result": []}
 
    async def get_changes_updated_last(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all changes that were updated since the last call
        """
        # Calculate time frame from 3:30
        end_time = datetime.utcnow()
        #start_time = end_time - timedelta(hours=24)
        start_time = end_time.replace(hour=3, minute=30, second=0, microsecond=0)
 
        if end_time < start_time:
            start_time -= timedelta(days=1)
 
        # Format for ServiceNow (they use local time, but we'll use UTC)
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
 
        logger.info(f"Fetching changes updated since: {start_time_str}")
       
        params = {
            'sysparm_query': f'sys_updated_on>={start_time_str}',
            'sysparm_fields': 'sys_id,start_date,end_date,number,upon_reject, sys_updated_on, test_plan, cmdb_ci, impact, priority, implementation_plan, short_description, u_post_implementation_testing, comments_and_work_notes, backout_plan, business_service, assignment_group, description, justification, risk_impact_analysis, sys_created_on,u_relevant_documentation_updated,category',
            'sysparm_limit': batch_size,
            'sysparm_offset': 0,
            'sysparm_display_value':"True"
        }
       
        all_changes = []
        total_fetched = 0
       
        while True:
            response = await self._make_request('change_request', params)
            changes = response.get('result', [])
           
            if not changes:
                logger.info("No more changes to fetch")
                break
               
            all_changes.extend(changes)
            total_fetched += len(changes)
           
            logger.info(f"Fetched batch: {len(changes)} changes (total: {total_fetched})")
           
            # If we got fewer than batch_size, we're done
            if len(changes) < batch_size:
                break
               
            # Update offset for next batch
            params['sysparm_offset'] += batch_size
           
            # Safety check to prevent infinite loops
            if total_fetched >= 10000:  # Adjust as needed
                logger.warning(f"Reached maximum fetch limit of 10000 records")
                break
       
        logger.info(f"Total changes fetched: {len(all_changes)}")
        return all_changes
    
    async def process_changes(self,incident_ci) -> Dict[str, Any]:
        """
        Main processing method that gets changes and their tasks
        """
        try:
            
            changes = await self.get_changes_updated_last()
           
            if not changes:
                logger.info("No changes found since the last processing")
                return {
                    'changes_count': 0,
                    'processed_at': datetime.utcnow().isoformat(),
                    'changes': []
                }
           
            summary = {
                'changes_count': len(changes),
                'processed_at': datetime.utcnow().isoformat(),
                'changes': changes
            }
           
            logger.info(f"Processing complete: {summary['changes_count']} changes")
           
            # return summary,all_cis
            return summary

        except Exception as e:
            logger.error(f"Error in process_changes: {e}")
            raise
 
def _sql_(query):
    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,  
        'host': db_host,  
        'port': db_port
    } 
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(query)
    out = cursor.fetchall()
    if conn:
            cursor.close()
            conn.close()
    return out
    
def update_table(db_config,incident_ci):
 
    access_token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
   
    # Get changes
    processor = ServiceNowChangesProcessor(sn_base_url, access_token)
   
    async def main():
        async with processor:
            # summary,cis = await processor.process_changes(incident_ci)
            # return summary,cis
            summary = await processor.process_changes(incident_ci)
            return summary
   
    # Run the async processing
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
   
    try:
        # summary,cis = loop.run_until_complete(main())
        summary = loop.run_until_complete(main())

    except Exception as e:
        logger.error(f"Error in process_changes: {e}")
        raise
    finally:
        loop.close()
   
    if summary["changes_count"] != 0:
        vector = _format_(response=summary)
 
        # Push vector data
           
        insert_vector_data(vector, db_config)
    # return cis
 
# ================== Historical Changes ==============
def historical_changes(db_config,incident_id,ci_list):
    # Fetching data from vector d_b
    try:
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
       
        # Fetch embedding
        _fetch_embed = f"""
            SELECT embedding from ticket_history_vec
            where inc_id = '{incident_id}';
        """
        cursor.execute(_fetch_embed)
        _embed_rows = cursor.fetchall()
        if not _embed_rows:
            logger.warning(f"No embedding found in ticket_history_vec for incident {incident_id}. Skipping historical_changes.")
            return []
        new_embed_vec = _embed_rows[0][0]
        logger.info(f"Embedding pulled for {incident_id} for searching through DB")

        _fetch_date = f"""
            SELECT raised_date from P1P2_Incidents
            where inc_id = '{incident_id}';
            """
       
        cursor.execute(_fetch_date)
        inc_date = cursor.fetchall()[0][0]
       
        ci_values = "', '".join(ci_list)
        logger.debug(f"Embedding : {new_embed_vec}")
        logger.debug(f"Incident date : {inc_date}")
        # logger.info(f"CI list : {ci_values}")
 
        # VectorSearch
        # _query = f"""
        #     SELECT chg_id, ci, summary, Score, created_ts
        #     FROM (
        #         SELECT chg_id, ci, summary,
        #             1 - POWER((embedding <-> '{new_embed_vec}'), 2) AS Score,
        #             TO_TIMESTAMP(
        #         SUBSTRING(chunk FROM '''sys_updated_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
        #         'DD-MM-YYYY HH24:MI:SS'
        #     ) AS created_ts
        #         FROM change_history_vec
        #         WHERE ci IN ('{ci_values}')
        #     ) AS sub
        #     ORDER BY created_ts DESC
        #     LIMIT 10;
        #     """

        _query = f"""
        SELECT chg_id, ci, summary, Score, created_ts
            FROM (
                SELECT chg_id, ci, chunk, summary,
                    1 - POWER((embedding <-> '{new_embed_vec}'), 2) AS Score,
                    TO_TIMESTAMP(
                SUBSTRING(chunk FROM '''sys_updated_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                'DD-MM-YYYY HH24:MI:SS'
            ) AS created_ts
                FROM change_history_vec
                WHERE ci IN ('{ci_values}')
            ) AS sub
            WHERE created_ts >= TO_TIMESTAMP('{inc_date}','YYYY-MM-DD HH24:MI:SS') - INTERVAL '3 days'
            AND TO_TIMESTAMP('{inc_date}','YYYY-MM-DD HH24:MI:SS') >= TO_TIMESTAMP(
                SUBSTRING(chunk FROM '''start_date'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                'DD-MM-YYYY HH24:MI:SS'
            )
            ORDER BY created_ts DESC
            LIMIT 10;
        """
        logger.info(f"SQL Query for filtering changes: {_query}")
        
        cursor.execute(_query)  
        obj  = cursor.fetchall()
        if obj:
            logger.info(f"Found similar changes : {len(obj)}")
        else:
            logger.info(f"No relevant changes found")
        return obj
 
    except Exception as e:
        logger.error(f"An error occurred in historical_change(): {e}")
        obj = None
       
    finally:
        if conn:
            cursor.close()
            conn.close()
            return obj
 
# ================== Suspected Changes ===============
def sus_changes(inc_id, db_config, out_sim_changes, all_cis):
    try:
        # Connect to the database  
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
 
        _fetch_new = f"""
            SELECT short_description ,description , configuration_item from P1P2_Incidents
            where inc_id = '{inc_id}';
            """
       
        cursor.execute(_fetch_new)
        _inc_rows = cursor.fetchall()
        if not _inc_rows:
            logger.warning(f"No incident record found in P1P2_Incidents for inc_id {inc_id}. Skipping sus_changes.")
            return []
        _short_desc ,_desc, _cfg = _inc_rows[0]
 
        scoring = []
        for item in out_sim_changes:
            
            #logger.info(f"Change : {item}")
            rel_ci= None
            for key, value in all_cis.items():
                if item[1] in value:
                    rel_ci = key
                    break

            _respon = _llm_(f"""You are a system analyst reviewing a set of change records and an incident report. Each change includes a Change ID, Configuration Item (CI), and a summary of the change. The incident includes a CI, a short description, and a detailed description.
            Your task is to rank the changes in order of how likely they are to have caused the incident. Consider factors such as:
 
            -Matching or related Configuration Items (CI)
            -Overlapping keywords or concepts between the incident and change summaries
            -Security, performance, or configuration-related changes
            -Ignore the score field.
            -Same ci will have first preferance, followed my parent, child in level 1 and finally child in level 2. At last will be the extra cis.
            -CI relations: parents,incident_ci,children_level1,children_level2,extra_cis
            
            -Change CI relation to incident CI : {rel_ci}
 
            Incident Details:
            CI: {_cfg}
            Short Description: {_short_desc}
            Description: {_desc[:3500]}
 
            Change Records:
            List format : [(change_id,ci,summary,score)]
            {str(item)}
 
           Output Format:
            Return the result as a JSON object with the following structure:
            STRICT OUTPUT RULES: 
            - Return ONLY the raw JSON object, nothing else
            - ALL keys and values must have double quotes. eg: "change_id" and not change_id
            - ALL string must have double quotes. eg "Akamai AS" and not Akamai AS
            - NO single quotes anywhere
            - NO markdown, NO codefences like ```json
            - NO explanation text befor or after
            - NO newlines and return compact single line json

            Example of CORRECT OUTPUT:

            
            {{
            "change_id": "{{change_id_1}}",
            "ci": "{{ci_1}}",
            "summary": "{{summary_1}}",
            "suspicion_rank": 1,
            "reason": "{{reason_1}}"
            }}
            Ensure the output is valid JSON and suspicion_rank is in the range 1 - 5 (1 = most suspicious). Do not include any extra commentary outside the JSON.""")
            logger.info(f"LLM Resp : {_respon}")
            json_str = _respon[_respon.find('{'):_respon.rfind('}')+1]
            json_str = json.loads(json_str)
            logger.info(f"JSON {json_str}")
            #print(json.dumps(json_str))
            scoring.append(json_str)
       
        fin = []
        same_cfg = []
        rel_cfg = []

        for i in scoring:
            if i["ci"] == _cfg:
                same_cfg.append(i)
            else:
                rel_cfg.append(i)

        same_cfg.sort(key=lambda x: x["suspicion_rank"])
        rel_cfg.sort(key=lambda x: x["suspicion_rank"])
        fin.extend(same_cfg)
        fin.extend(rel_cfg)

        logger.info("Sus Changes Output:")
        logger.info(fin)
        return fin
 
    except Exception as e:
        logger.error(f"Error encountered while fetching suspected changes: {e}")
        results = e
   
    finally:
        if conn:
            cursor.close()
            conn.close()
 
def get_changes(access_token, api_url):
 
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
   
    # response = requests.get(api_url, headers = headers, verify = False)
    response = http.request('GET', api_url, headers = headers)
    if response.status == 200:
        data = json.loads(response.data.decode('utf-8'))
       
        return data
    else:
        logger.info(f"Failed to get changes: {response.status} - {response.data}")
 
def sync_blob(org_inc , results):
   
    try:
 
        db_config = {
            'dbname': db_name,
            'user': db_user,
            'password': db_password,
            'host': db_host,
            'port': db_port
        }
 
        token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        sus_out = []
        for item in results:
            _query = f"""
            Select link from change_history_vec where chg_id = '{item['change_id']}'
            """
            cursor.execute(_query)
            _link_rows = cursor.fetchall()
            link = _link_rows[0][0] if _link_rows else ""
            logger.debug(f"Link fetched for {item['change_id']}")


            change = get_changes(token, f'{sn_base_url}/api/now/table/change_request?sysparm_display_value=true&sysparm_query=number%3D{item["change_id"]}&sysparm_limit=1')["result"][0]
            logger.debug(f"Change fetched for {item['change_id']}")
            try: ast = change['assigned_to']['display_value']
            except: ast = None
            suspectedChanges = {
                "changeId":change["number"],
                "description":change["description"],
                "shortDescription": change["short_description"],
                "category": change["category"],
                #Check while deploying in EJ environment
                "state": change["state"],
                "implimentationPlan": change["implementation_plan"],
                # Change this while deploying
                # "postImplementation":change["test_plan"],
                "postImplementation":None,
                "assignedTo":ast,
                "plannedStartDate":change["start_date"],
                #"plannedStartDate":change["sys_created_on"],
                #"plannedEndData":change["end_date"],
                "plannedEndDate":change["end_date"],
                "summary":change["description"],
                "backout":change["backout_plan"],
                # Need to change this or diskus,
                "impactedServices": change["description"],
                "configurationItem": change["cmdb_ci"]["display_value"],
                #"link": link
                "link":f"{sn_base_url}/nav_to.do?uri=change_request.do?sys_id={change['sys_id']}",

            }
            # print(json.dumps(suspectedChanges,indent=3))
            sus_out.append(suspectedChanges)
 
        # conn = psycopg2.connect(**db_config)
        # cursor = conn.cursor()  
 
        # Fetch Statement
        fetch_query = f"""
        Select MIM_agent_output_blob from P1P2_Incidents WHERE inc_id = '{org_inc}'
        """
 
        cursor.execute(fetch_query)
        cursor_return = cursor.fetchall()
        logger.debug(f"Cursor read for blob returned \n{cursor_return}\n")
       
        try:
            op_blob = (cursor_return[0][0])
        except:
            op_blob = None

        logger.info(f"op_blob:\n{op_blob}")
 
        if op_blob == None:
            mimjson ={
                'ticketDetails':{},
                'suspectedIncidents':[],
                'similarIncidents':[],
                'suspectedChanges':[],
                'incidentResponse':[],
                'knowledgebase':[],
                'worknotes': ''
            }
        else:
            mimjson = json.loads(op_blob.tobytes().decode('utf-8'))
        #logger.debug(json.dumps(mimjson,indent=3))
       
        mimjson["suspectedChanges"] = sus_out
 
        #print("== Output json blob ==")
       
        #print(json.dumps(mimjson,indent=3))
        #logger.info('After')
        logger.info(json.dumps(mimjson,indent=3))
 
        # Push data back to the table
        json_bytes = json.dumps(mimjson).encode('utf-8')
        insert_query = f"""              
            UPDATE P1P2_Incidents
            SET MIM_agent_output_blob = %s
            WHERE inc_id = %s;
        """
        cursor.execute(insert_query,(json_bytes,org_inc))
        conn.commit()
        logger.debug(f"json_bytes - {json_bytes}")
        logger.info(f"Blob updated successfully for {org_inc}")
        return mimjson
 
    except Exception as e:
        logger.error(f"An error occurred in sync_blob(): {e}")

# ================== New table =======================
def rel_ci2(_cfg : str):
    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    _inc_ci = _sql_("""select distinct ci from change_history_vec
    where ci != 'NULL';""")
    _inc = []
    for i in _inc_ci:
        _inc.append(i[0])

    query= f"{sn_base_url}/api/now/table/cmdb_key_value?sysparm_query=value%3D{_cfg}%5EkeySTARTSWITHApplication%5Econfiguration_item.sys_class_name%3Dcmdb_ci_vm_instance&sysparm_display_value=true"
    _response = get_changes(token,query)["result"]
    _values = []
    for i in _response:
        _values.append(i["configuration_item"]["display_value"])

    # unique items

    inc_cfg = list(set(_inc))
    cmdb_cfg = list(set(_values))
    overlap_cfg = list(set(inc_cfg) & set(cmdb_cfg))
    overlap_cfg.append(_cfg)
    logger.info(f"""
    ==== Related CI Search ====
    Searching for CI: {_cfg}
    CIs that are in incidents: {inc_cfg}
    CIs that are in CMDC: {cmdb_cfg}
    overlapping CIs: {overlap_cfg.__len__()}

    CIs: {overlap_cfg}

    ===========================
    """)

    return overlap_cfg
 
# ================== Entry function ==================
 
def fetch_relevant_changes(incident_id):
 
    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,
        'host': db_host,  
        'port': db_port
    }
    try:
        #print("In fetch_rel_changes function")
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
 
        # get details of self
        _query = f"""    
            SELECT category,configuration_item,MIM_agent_output_blob FROM P1P2_Incidents
            WHERE inc_id = '{incident_id}'
            """
        cursor.execute(_query)
        _main_rows = cursor.fetchall()
        if not _main_rows:
            logger.error(f"No record found in P1P2_Incidents for incident {incident_id}. Cannot proceed with fetch_changes.")
            raise ValueError(f"Incident {incident_id} not found in P1P2_Incidents table.")
        _ctg , _cfg, all_cis  = _main_rows[0]
        # logger.info(all_cis)
        all_cis = json.loads(all_cis.tobytes().decode('utf-8'))["all_cis"]
        #logger.info(type(all_cis))

        #updating table before processing
        #logger.info(json.dumps(all_cis,indent=3))
        update_table(db_config,_cfg)
        ci_list =  all_cis["incident_ci"]+all_cis["parents"] +all_cis["children_level1"] +all_cis["children_level2"]
        logger.info(f"CI list from cmdb_rel_ci: {ci_list}")

        ci_set = set(ci_list)
        logger.info(f"Initial ci list : {ci_list}")
        extra_cis = rel_ci2(_cfg)
        filtered_extra_cis = [item for item in extra_cis if item not in ci_set]

        logger.info(f"Filtered extra CIs : {filtered_extra_cis}")

        all_cis["extra_ci"] = filtered_extra_cis
        logger.info(f"All rel ci : {json.dumps(all_cis,indent = 3)}")
        ci_list = ci_list + filtered_extra_cis
        #print("table updated")
        #print(json.dumps(all_cis,indent=3))
        logger.info(f"Fetched {len(ci_list)} relevant cis")
 
        #print("sleeping for 1 seconds to wait for update")
        sleep(1)
       
        logger.info("Update complete. Proceeding with change logic...")
       
        # First find the top 10 similar changes
        out_sim_changes = historical_changes(db_config,incident_id,ci_list)
        if out_sim_changes:
            logger.info(f"Found {len(out_sim_changes)} similar changes")
    
            logger.info(f"Checking for suspected changes")
            out_sus_changes = sus_changes(incident_id, db_config, out_sim_changes, all_cis)
            logger.info(f"Found the suspected changes")
            #pprint.pprint(out_sus_changes)
            logger.info(f"Storing in blob")
            blob_resp = sync_blob(incident_id, out_sus_changes)
            response = {
                "status": "success",
                "message": json.dumps(blob_resp)
            }
        
        else:
            logger.info(f"Skipping suspected changes process, as no relevant changes found....")
            blob_resp = sync_blob(incident_id, [])
            response = {
                "status": "success",
                "message": json.dumps(blob_resp)
            }
 
    except Exception as e:
        logger.error(f"An error occurred in fetch_changes(): {e}")
        response = {
            "status": "error",
            "message": traceback.format_exc()
        }
        #traceback.print_exc()
 
       
    finally:
        if conn:
            cursor.close()
            conn.close()
        return response