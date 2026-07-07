from fastapi import FastAPI
from datetime import datetime
import boto3
import json
from botocore.exceptions import ClientError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import *
from chatUtils import *
import logging
import io
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse
import os
import traceback
import json
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from scheduled_knowledge import knowledge_handler
from session_scheduler import session_scheduler
import watchtower
import sys
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
   session = boto3.Session(region_name=region_name)  # Change region as needed
   cloudwatch_handler = watchtower.CloudWatchLogHandler(log_group=log_group, stream_name=log_stream)
   cloudwatch_handler.setFormatter(formatter)
   logger.addHandler(cloudwatch_handler)

   return logger, log_buffer

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
      logger.info(f"all incident - {allIncidents}")
      keys = ['incidentId', 'shortDescription', 'description', 'createdOn', 'openSince', 'state', 'agentRunStatus', 'priority', 'configurationItem']
      # dict_list = [dict(zip(keys, incidents)) for incidents in allIncidents]
      dict_list = [
         {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in zip(keys, incidents)
         }
         for incidents in allIncidents]
      logger.info(dict_list)
      return JSONResponse(content={"message": dict_list}, status_code=200)
   except Exception as e:
      logger.error(e, exc_info = False) 
      return JSONResponse(content = {"message": "Some issue at our side"}, status_code = 400)
   finally:
      log_contents = log_buffer.getvalue()
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
   logger, log_buffer = instantiate_logger()
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
      status = fetch_agent_run_status(incId, db_config)
      mimAgentOutput["status"]=status
      logger.info(f"status : {mimAgentOutput["status"]}")
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

@app.post('/backend/chatbot')
async def chatbot(body:Dict[Any,Any]):
   #body = json.loads(body)
   print(body)
   incId = body.get('incId')
   #mode = body.get('mode')
   user_message = body.get('user_message')
   logger, log_buffer = instantiate_logger()
   logger.info(f"Payload body: {body}")
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger.info('processing /backend/chatbot')
   logger.info(f'======== CHATBOT RECIEVED PAYLOAD ========\n{user_message}')
   user_message = user_message["message"]
   try:
      db_config = {
         'dbname': db_name,
         'user': db_user,
         'password': db_password,
         'host': db_host,
         'port': db_port
      }
      _fetch_inci = f"""
            SELECT ci, summary from ticket_history_vec
            where inc_id = '{incId}';
        """
      print(json.dumps(db_config,indent=3))
      print(_fetch_inci)
      incident_ci , incident_desc = sql(_fetch_inci , db_config)[0]
      incident_desc_clean = incident_desc.replace("'", "").replace('"', '')
      logger.info(f"Incident des {incident_desc}\n Cleaned desc {incident_desc_clean}")

      outstr = ""
      outjson = []

      if user_message == "Recent Changes":
         query = f"""SELECT chg_id, summary, TO_TIMESTAMP(
               SUBSTRING(chunk FROM '''sys_updated_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
               'DD-MM-YYYY HH24:MI:SS'
            ) as date
            FROM change_history_vec
            WHERE ci = '{incident_ci}'
            AND TO_TIMESTAMP(
               SUBSTRING(chunk FROM '''sys_updated_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
               'DD-MM-YYYY HH24:MI:SS'
            ) >= NOW() - INTERVAL '7 days'
            """
         out = sql(query,db_config)

         if out.__len__() == 0:
            outstr = f"No recent changes found in the last 7 days for {incident_ci}"
         else:
            outstr = f"{out.__len__()} Changes found for {incident_ci}, here are some of the changes"
            
            for item in out:
               logger.info(f"Chat Endpoint Response: {item} ")
               _content = {
                  "id": item[0],
                  "summary": item[1],
                  "time": item[2].strftime(" %H:%M:%S , %d-%m-%Y")
               }
               outjson.append(_content)

      elif user_message == "Recent Incidents":
            outstr , outjson , chatlog = call(f"Get the recent incidents related to the Configuration item : {incident_ci} . For the last 7 days" ,  db_config = db_config)
            logger.info(f"===============================================\n Chatbot has done the following actions and tools :\n {chatlog} ===")
      elif user_message == "Knowledge Articles":
            outstr = "Knowledge articles are still in development"
            outjson = []
            outstr , outjson , chatlog = call(f"Getting Relavant Knowledge articles: {incident_desc_clean}" , incident_ci , db_config = db_config )
            logger.info(f"===============================================\n Chatbot has done the following actions and tools :\n {chatlog} ===")

      else:
         if user_message:
               if len(user_message) > 1000:
                  outstr = "Your message is too long. Please shorten it and try again."

               else:
                  logger.info(f"=== Custom message sent: {user_message} ===")
                  #remove quotes in user msg
                  user_message_clean = user_message.replace("'", "").replace('"', '')
                  outstr , outjson , chatlog = call(user_message_clean , incident_ci , db_config = db_config )
                  logger.info(f"===============================================\n Chatbot has done the following actions and tools :\n {chatlog} ===")
         else:
               outstr = "Both mode and User message is empty"
               outjson = []
      #added chatlog for debug -remove later
      response = {
         "message":{
            "role":"assistant",
            "message": outstr ,
            "content": outjson,
         }
      }
      logger.info(f"Chat Endpoint Response: \n{response} ")
      return JSONResponse(content = response , status_code = 200)

   except Exception as e:
      logger.error(e, exc_info = False)   
      return JSONResponse(content = {"message": f"Some issue at our side: {e}"}, status_code = 400)

   finally:
      log_contents = log_buffer.getvalue()
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      log_key = f"{log_prefix}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{request_id}_chatbot.log"

      s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
      
# ====================== KNOWLEDGE SCHEDULER ============================
def scheduled_task():
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger, log_buffer = instantiate_logger()
   logger.info("Scheduled task started.")
   logger.info("Knowledge processing...")
   try:
      knowledge_handler()
      logger.info("Knowledge processing completed.")
   except Exception as e:
      err_msg = f"Error in Knowledge processing- {str(e).replace(':', ' - ').replace('\"', '\'')}"
      logger.error(err_msg, exc_info = False)

   finally:
      s3_client = boto3.client('s3')
      log_key = f"{log_prefix}/scheduledKnowledge/{datetime.today().strftime('%Y-%m-%d')}.log"
      log_contents = log_buffer.getvalue()
      s3_client.put_object(
         Bucket=log_bucket,
         Key=log_key,
         Body=log_contents,
         ContentType='text/plain'
      )      


#======================= SESSION SCHEDULER ==============================
def session_scheduled_task():
   request_id = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4()}"
   logger, log_buffer = instantiate_logger()
   logger.info("Session Scheduling task started...")
   try:
      db_config = {
         'dbname': db_name,
         'user': db_user,
         'password': db_password,
         'host': db_host,
         'port': db_port
      }
      session_scheduler(db_config)
      logger.info("Old session deletion completed..")
   except Exception as e:
      logger.error(f"Error in Old session deleting- {str(e).replace(':', ' - ').replace('\"', '\'')}", exc_info = False)
   finally:
      s3_client = boto3.client('s3')
      log_key = f"{log_prefix}/clearingOldSessions/{datetime.today().strftime('%Y-%m-%d')}.log"
      log_contents = log_buffer.getvalue()
      s3_client.put_object(
         Bucket=log_bucket,
         Key=log_key,
         Body=log_contents,
         ContentType='text/plain'
      )

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, 'cron',hour=2,minute=30)
# scheduler.add_job(scheduled_task, 'cron',hour=9,minute=30)
scheduler.add_job(session_scheduled_task,'cron',hour=2,minute=20)
# scheduler.add_job(session_scheduled_task,'cron',hour=7,minute=10)
@app.on_event("startup")
def startup_event():
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()      