import json
import boto3
import logging
import os
from datetime import datetime , timedelta
import io
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime
import traceback
import uuid
 
# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']
# ====================== LOGGER ============================
 
# Set up in-memory logging
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)
 
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
 
 
log_bucket = configPythonSecrets['lambdaLog']['bucket']
log_prefix = configPythonSecrets['lambdaLog']['prefix']
agents = configPythonSecrets['Agents']
 
import json
 
# Initialize the Bedrock Agent Runtime client
config = Config(
    read_timeout=120,
    connect_timeout=120, # Optional: connect timeout
)
client = boto3.client('bedrock-agent-runtime', config = config)
 
def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
   
    try:
        # Your business logic here
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")
 
        # ====== Initialize logger here =====
 
        inc_id = str(event["inc_id"])
        logger.info(f"===EVENT ID===={inc_id}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{inc_id}_{timestamp}_{context.aws_request_id}.log"
 
        log_contents = log_capture_string.getvalue()
 
        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
 
 
        logger.info(f"{agents} secret of type {type(agents)}")
        # ============= REMEMBER TO UNCOMMENT BEFORE ENDING ===============
 
       
 
 
        responses = []
        sessionId = str(uuid.uuid4())
 
        for agent in agents:
            try:
                logger.info((f"======================\nInvoking agent {agent['agentId']} with alias {agent['agentAliasId']} for incident: {inc_id}"))
                log_contents = log_capture_string.getvalue()
                s3_client.put_object(
                    Bucket=log_bucket,
                    Key=log_key,
                    Body=log_contents,
                    ContentType='text/plain'
                )
                # Invoke the agent
                response = client.invoke_agent(
                    agentId=agent["agentId"],
                    agentAliasId=agent["agentAliasId"],
                    sessionId=sessionId,
                    inputText=inc_id
                )
                # Read the streaming response
                response_text = ""
                for event_stream in response['completion']:
                    if 'chunk' in event_stream:
                        response_text += event_stream['chunk']['bytes'].decode('utf-8')
 
                responses.append({
                    "agentId": agent["agentId"],
                    "response": response_text
                })
                logger.info(f"Agent {agent['agentId']} response: {response_text}")
            except Exception as e:
                responses.append({
                    "agentId": agent["agentId"],
                    "error": str(e)
                })
       
        logger.info(responses)
        logger.info(f"Logs uploaded to s3://{log_bucket}/{log_key}")
 
        log_contents = log_capture_string.getvalue()
 
        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
 
        logger.removeHandler(ch)
 
        return {
            "status": "success",
            "body": json.dumps(responses)
        }
       
    except Exception as e:
 
        return {
            "status": "error",
            "body": f"Error encountered: {traceback.format_exc()}"
        }
    finally:
        # Clean
 
        logger.removeHandler(ch)
       