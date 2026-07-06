from fastapi import FastAPI
from datetime import datetime
import boto3
import json
from botocore.exceptions import ClientError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import *
import logging
import io
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse
import os
# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']

#=====================LOGGING==========================
# Set up in-memory logging
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)

# Get logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
s3_client = boto3.client('s3')


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

   
   
class fetchProcessedIncident(BaseModel):
   pass


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
db_host = configPythonSecrets['database']['host']
db_port = configPythonSecrets['database']['port']
db_name = configPythonSecrets['database']['name']
db_user = configPythonSecrets['database']['user']
db_password = configPythonSecrets['database']['password']
log_bucket = configPythonSecrets['pythonBackendLog']['bucket']
log_prefix = configPythonSecrets['pythonBackendLog']['prefix']




@app.get("/backend/health")
def health():
   return{'msg':f'Connected to server on {datetime.today().date()} at {datetime.today().strftime('%H:%M:%S')}'}


@app.get('/backend/getAllIncidents', response_model=fetchProcessedIncident)
async def getAllIncidents():
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger.info('processing /backend/getAllIncidents')
   
   try:
      db_config = {  
         'dbname': db_name,  
         'user': db_user,  
         'password': db_password,  
         'host': db_host,  
         'port': db_port
      } 
      allIncidents = fetch_all_incidents(db_config)
      keys = ['incidentId', 'shortDescription', 'createdOn', 'openSince', 'state', 'agentRunStatus']
      # dict_list = [dict(zip(keys, incidents)) for incidents in allIncidents]
      dict_list = [
         {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in zip(keys, incidents)
         }
         for incidents in allIncidents]
      return JSONResponse(content={"message": dict_list}, status_code=200)
   except Exception as e:
      logger.exception(e)
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
   finally:
      log_contents = log_capture_string.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_getAllIncidents.log"
        
      s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )


@app.get('/backend/getIncident', response_model=fetchProcessedIncident)
async def getIncident(incId : str):
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger.info('processing /backend/getIncident')
   
   try:
      db_config = {  
         'dbname': db_name,  
         'user': db_user,  
         'password': db_password,  
         'host': db_host,  
         'port': db_port
      } 
      mimAgentOutput = fetch_mim_agent_output(incId, db_config)
      return JSONResponse(content={"message": mimAgentOutput}, status_code=200)
   except Exception as e:
      logger.exception(e)
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
   finally:
      log_contents = log_capture_string.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_getIncident.log"
        
      s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )

