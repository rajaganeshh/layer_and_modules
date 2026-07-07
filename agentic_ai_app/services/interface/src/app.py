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
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
import secrets
from typing import Optional
import watchtower
import sys
 
sys.tracebacklimit = 0

# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']

#=====================LOGGING==========================
# # Set up in-memory logging
# log_capture_string = io.StringIO()
# ch = logging.StreamHandler(log_capture_string)
# ch.setLevel(logging.DEBUG)

# # Get logger
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(ch)

##################LOGGING##############################
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)



# Get logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)

# s3_client = boto3.client('s3')


app = FastAPI()
security = HTTPBasic()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class newIncidentRequest(BaseModel):
   number: str
   cmdb_ci: str
   state: str
   sys_created_on: str

class updateWorknote(BaseModel):
   number: str
   user_name: Optional[str] = None
   work_note: str

class refreshIncidentRequest(BaseModel):
   number: str


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
log_bucket = configPythonSecrets['interfaceLog']['bucket']
log_prefix = configPythonSecrets['interfaceLog']['prefix']
sn_client_id = configPythonSecrets['serviceNow']['clientId']
sn_client_secret = configPythonSecrets['serviceNow']['clientSecret']
sn_token_url = configPythonSecrets['serviceNow']['tokenUrl']
sn_base_url = configPythonSecrets['serviceNow']['baseUrl']
interface_user = configPythonSecrets['interfaceEndpoint']['username']
interface_pwd = configPythonSecrets['interfaceEndpoint']['password']
agentId = configPythonSecrets['bedrockAgent']['agentId']
agentAliasId = configPythonSecrets['bedrockAgent']['agentAliasId']
supervisorLambda = configPythonSecrets['supervisorLambda']

##################LOGGING##############################
def instantiate_logger():
   log_buffer = io.StringIO()
   logger = logging.getLogger(log_prefix)
   logger.setLevel(logging.INFO)

   # Local buffer handler
   buffer_handler = logging.StreamHandler(log_buffer)
   formatter = logging.Formatter('{"asctime": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "pathname": "%(pathname)s", "lineno": %(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S')
   buffer_handler.setFormatter(formatter)
   logger.addHandler(buffer_handler)

   # CloudWatch handler
   cloudwatch_handler = watchtower.CloudWatchLogHandler(log_group=log_group, stream_name=log_stream)
   cloudwatch_handler.setFormatter(formatter)
   logger.addHandler(cloudwatch_handler)

   return logger, log_buffer

########################DB_CONFIF###############################
db_config = {  
         'dbname': db_name,  
         'user': db_user,  
         'password': db_password,  
         'host': db_host,  
         'port': db_port
      } 

# ====================== AUTHENTICATE ============================
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, interface_user)
    correct_password = secrets.compare_digest(credentials.password, interface_pwd)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/interface/health")
def health():
   return{'msg':f'Connected to server on {datetime.today().date()} at {datetime.today().strftime('%H:%M:%S')}'}

#api exposing to service now
@app.post('/interface/newIncident')
async def newIncident(request:newIncidentRequest, username: str = Depends(authenticate)):
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger, log_buffer = instantiate_logger()
   logger.info('processing /interface/newIncident')
   try:
      s3_client = boto3.client('s3')
      logger.info(f'Incident is {request.number}')
      logger.info(f'Configuration Item is {request.cmdb_ci}')

      #check agent run status
      agent_run_status = fetch_agent_run_status(request.number, db_config)
      logger.info(f"Agent Run Status for {request.number} is {agent_run_status}")

      if agent_run_status in ('New Incident'):
            if request.cmdb_ci is not "":
                    Agent_Run_Status = {
                           "Entry_Time_STAMP" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                           "Incident_ID" : request.number,
                           "Run_Status" : 'Incident Received',
                        }
            else:
                    Agent_Run_Status = {
                           "Entry_Time_STAMP" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                           "Incident_ID" : request.number,
                           "Run_Status" : 'CI Unavailable',
                        }
      else:
            if request.cmdb_ci is not "":
                    Agent_Run_Status = {
                           "Entry_Time_STAMP" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                           "Incident_ID" : request.number,
                           "Run_Status" : 'Processing Updates',
                        }
            else:
                    Agent_Run_Status = {
                           "Entry_Time_STAMP" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                           "Incident_ID" : request.number,
                           "Run_Status" : 'CI Unavailable',
                        }
 
      #Agent_run_Status either New Incident 
      if agent_run_status not in ('Incident Received' ,'Processing Updates',  'Incident Processing', 'Incident Processed'):
            #insert in action run status table
            insert_agent_run_status_rdbms_data(Agent_Run_Status, db_config)
            #fetch all available inc details from snow
            incident = fetch_inc_detail_from_snow(request.number, sn_base_url, sn_client_id, sn_client_secret, sn_token_url)
            #format details from snow for p1p2_incidents table insertion
            P1P2_IncidentTable_Item = format_data(incident, agent_run_status, request.number, db_config)
            #insert formatted data to p1p2_incidents table
            insert_rdbms_data(P1P2_IncidentTable_Item, db_config)
            
            #invoke bedrocksupervisor agent
            if request.cmdb_ci is not "":
                   logger.info(f'Triggering Supervisor Lambda for {request.number}')
                   lambda_return = invoke_lambda_supervisor(supervisorLambda, request.number)
                   logger.info(f'Supervisor Lambda return - {lambda_return}')
                   return JSONResponse(content = {"message": "P1/P2 Incident Received"}, status_code = 200)
            else:
                   return JSONResponse(content = {"message": "Configuration Item Empty"}, status_code = 200)
      #Agent Run Status is Incident Processed
      elif agent_run_status not in ('Incident Received' ,'Processing Updates',  'Incident Processing', 'New Incident'):
            #insert in action run status table
            insert_agent_run_status_rdbms_data(Agent_Run_Status, db_config)
            #fetch all available inc details from snow
            incident = fetch_inc_detail_from_snow(request.number, sn_base_url, sn_client_id, sn_client_secret, sn_token_url)
            #format details from snow for p1p2_incidents table insertion
            P1P2_IncidentTable_Item = format_data(incident, agent_run_status, request.number, db_config)
            #insert formatted data to p1p2_incidents table
            insert_rdbms_data(P1P2_IncidentTable_Item, db_config)
            
            #invoke bedrocksupervisor agent
            if request.cmdb_ci is not "":
                  logger.info(f'Triggering Supervisor Lambda for {request.number}')
                  lambda_return = invoke_lambda_supervisor(supervisorLambda, request.number)
                  logger.info(f'Supervisor Lambda return - {lambda_return}')
                  return JSONResponse(content = {"message": "Reprocessing an already processed incident"}, status_code = 200)
            else:
                  return JSONResponse(content = {"message": "Configuration Item Empty"}, status_code = 200)
      else:
            if request.cmdb_ci is not "":
                  logger.info('Request has been queued')
                  queue_incident_update(request, db_config)
                  return JSONResponse(content = {"message": "P1/P2 Incident in Processing or already Processed"}, status_code = 200)
            else:
                  return JSONResponse(content = {"message": "Configuration Item Empty"}, status_code = 200)
            
      
   except Exception as e:
      logger.exception(e, exc_info=False)
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
      
   finally:
     
      log_contents = log_buffer.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_newIncident.log"
        
      s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,    
            Body=log_contents,
            ContentType='text/plain'
        )
      s3_client.close()
      
@app.post('/interface/refreshIncident')
def refreshIncident(request:refreshIncidentRequest):
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger, log_buffer = instantiate_logger()
   logger.info('processing /interface/refreshIncident')
   try:
      s3_client1 = boto3.client('s3')
      logger.info(f'Incident is {request.number}')  
      
      #fetch all available inc details from snow
      incident = fetch_inc_detail_from_snow(request.number, sn_base_url, sn_client_id, sn_client_secret, sn_token_url)
      #format details from snow for p1p2_incidents table insertion
      P1P2_IncidentTable_Item = format_data(incident, 'Incident Processed', request.number, db_config)
      #insert formatted data to p1p2_incidents table
      insert_rdbms_data(P1P2_IncidentTable_Item, db_config)

      return JSONResponse(content = {"message": "Incident Refreshed"}, status_code = 200)
            
      
   except Exception as e:
      logger.exception(e, exc_info=False)
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
      
   finally:
      
      log_contents = log_buffer.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_refreshIncident.log"
        
      s3_client1.put_object(
            Bucket=log_bucket,
            Key=log_key,    
            Body=log_contents,
            ContentType='text/plain'
        )
      s3_client1.close()
      

@app.post('/interface/updateWorknote')
def updateWorknote(request:updateWorknote):
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger, log_buffer = instantiate_logger()
   logger.info('processing /interface/updateWorknote')
   try:
      s3_client2 = boto3.client('s3')
      logger.info(f'Incident is {request.number}')
      logger.info(f'WorkNote is {request.work_note}')

      sys_id = fetch_sys_id(request.number, sn_base_url, sn_client_id, sn_client_secret, sn_token_url)

      update_worknotes(sys_id, request.work_note, request.user_name, sn_base_url, sn_client_id, sn_client_secret, sn_token_url)
      
      return JSONResponse(content = {"message": "Updated to ServiceNow Worknotes"}, status_code = 200)
      
   except Exception as e:
      logger.exception(e, exc_info=False)
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
      
   finally:

      log_contents = log_buffer.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_updateWorknote.log"
        
      s3_client2.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
      s3_client2.close()
