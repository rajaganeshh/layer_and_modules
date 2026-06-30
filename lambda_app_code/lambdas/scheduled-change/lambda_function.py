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
import traceback

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
    client = session.client("secretsmanager")

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
    s3_client = boto3.client('s3',region_name=region_name)

    # Business logic
    try:
        logger.info("Lambda function started")
        logger.debug(f"Event received: {json.dumps(event)}")

        result = fetch_changes()
        
        logger.info(f"Processing completed")
        
        # Upload logs to S3
        log_contents = log_capture_string.getvalue()
        # timestamp = datetime.strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{context.aws_request_id}.log"
        
        logger.info(f"Uploading logs to s3://{log_bucket}/{log_key}")
        
        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )


        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'log_location': f's3://{log_bucket}/{log_key}'
            })
        }
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        # Still try to upload logs even if there's an error
        log_contents = log_capture_string.getvalue()
        # timestamp = datetime.strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/error_{timestamp}_{context.aws_request_id}.log"
        
        try:
            s3_client.put_object(
                Bucket=log_bucket,
                Key=log_key,
                Body=log_contents,
                ContentType='text/plain'
            )
        except:
            pass  # If S3 upload fails, don't crash the function
            
        raise e
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

def _get_embeddings(embedding_model, bedrockKey, region_name, input_text):
    
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
            "u_post_implementation_testing": item["u_post_implementation_testing"],
            "u_relevant_documentation_updated": item["u_relevant_documentation_updated"],
            "comments_and_work_notes": item["comments_and_work_notes"],
            "upon_reject": item["upon_reject"]
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
            print("Error occured while formatting the data bob!!")
   
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
        logger.debug("Data inserted successfully!")  
  
    except Exception as e:  
        logger.exception("An error occurred:", e)  
  
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
                logger.error(f"Unexpected error for {endpoint}: {traceback.format_exc()}")
                return {"result": []}

    async def get_changes_updated_last_24h(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Get all changes that were updated in the last 24 hours
        """
        # Calculate 24 hours ago
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
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
                logger.debug("No more changes to fetch")
                break
                
            all_changes.extend(changes)
            total_fetched += len(changes)
            
            logger.debug(f"Fetched batch: {len(changes)} changes (total: {total_fetched})")
            
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

    async def process_changes(self) -> Dict[str, Any]:
        """
        Main processing method that gets changes and their tasks
        """
        try:
            # Get changes updated in last 24 hours
            changes = await self.get_changes_updated_last_24h()
            
            if not changes:
                logger.info("No changes found in the last 24 hours")
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
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in process_changes: {e}")
            raise

# ================== Entry function ==================

def fetch_changes():
    
    access_token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    
    # Get changes
    processor = ServiceNowChangesProcessor(sn_base_url, access_token)
    
    async def main():
        async with processor:
            return await processor.process_changes()
    
    # Run the async processing
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(main())
    finally:
        loop.close()

    vector = _format_(response=results)

    # Push vector data

    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,
        'host': db_host,  
        'port': db_port
    } 
        
    insert_vector_data(vector, db_config)