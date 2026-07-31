import json
import boto3
import logging
import os
from datetime import datetime , timedelta
import io
import urllib3
from urllib.parse import urlencode
from botocore.exceptions import ClientError
import psycopg2
from datetime import datetime
import re
 
http = urllib3.PoolManager()
 
 
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
 
log_bucket = configPythonSecrets['lambdaLog']['bucket']
log_prefix = configPythonSecrets['lambdaLog']['prefix']
 
# ====================== LAMBDA HANDLER ===========================
 
def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
   
    try:
        # Your business logic here
        
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")
       
        # Example processing
        result = fetch_inc()
        logger.info(f"Processing completed")
       

       
        # Upload logs to S3
        log_contents = log_capture_string.getvalue()
        # timestamp = datetime.strftime('%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/{timestamp}_{context.aws_request_id}.log"
       
        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
    
        logger.info(f"Logs uploaded to s3://{log_bucket}/{log_key}")
       
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': "done" ,
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
   
   
    response = http.request('POST', token_url, body = encoded_params,
                            headers={"Content-Type": "application/x-www-form-urlencoded"})
    if response.status == 200:
        token_data = json.loads(response.data.decode('utf-8'))
        return token_data['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status} - {response.data}")
       
# --------- Get Incidents ----------------
       
 
def get_incidents(access_token, api_url):
 
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
   
    # response = requests.get(api_url, headers = headers, verify = False)
    response = http.request('GET', api_url, headers = headers)
    if response.status == 200:
        data = json.loads(response.data.decode('utf-8'))
        #logger.info(data)
        return data
    else:
        raise Exception(f"Failed to get incidents: {response.status} - {response.data}")
   

 
# ===================== Utils ========================
 
email_pii = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
phone_pii = r"\+\d{8,}[\d\s\-\(\)]*"
 
def _get_embeddings(embedding_model, region_name, input_text):
    
    input_text = re.sub(email_pii, "[EMAIL_REDACTED]", input_text)
    input_text = re.sub(phone_pii, "[PHONE_REDACTED]", input_text)

    client = boto3.client("bedrock-runtime", region_name=region_name)

    native_request = {"inputText": input_text[:8000]}

    request = json.dumps(native_request)

    response = client.invoke_model(modelId=embedding_model, body=request)

    model_response = json.loads(response["body"].read())

    embedding = model_response["embedding"]
    return embedding

def clean_desc(_text : str):
    _temp = _text.replace("CAUTION: This email originated from outside of the organisation. Do not click links or open attachments unless you recognise the sender and know the content is safe.", "")
    _temp = _temp.replace("The information in this e-mail and any attachments is confidential and may be legally privileged. It is intended solely for the addressee(s) named above. If you are not an intended recipient, please notify the sender and delete the message and any attachments from your system. Any use, copying or disclosure of the contents of either is unauthorised unless expressly permitted. Any views expressed in this message are those of the sender unless expressly stated as to be those of easyJet. Virus checking of emails and attachments is the responsibility of the recipient. easyJet Airline Company Limited Registered in England with Registered number: 3034606 Subsidiary of easyJet Plc Registered in England with registered number: 3959649 Registered Office: Hangar 89, London Luton Airport, Luton, Bedfordshire LU2 9PF Click here to report this email as spam.","")
    return _temp


def _format_(response , token):

    RDBMSJson = []
    VecJson = []
    logger.info(f"{response['result'].__len__()} items found")

    for item in response["result"]:

        # ==========  preprocessing

        logger.info(f'updating ticket: {item["number"]}')

        # business value
        try: _bi = item["business_service"]["value"]
        except: _bi = None

        # Config item
        try: _cfg = item["cmdb_ci"]["display_value"]
        except: _cfg = None

        # Problems
        try:
            prb_id = item["problem_id"]["display_value"]
            problem = get_incidents(token, f'{sn_base_url}/api/now/table/problem?sysparm_query=number%3D{prb_id}')['result'][0]
            problemAppend = f"Work Notes for problem: {problem['description']} {problem['comments_and_work_notes']} ,"

        except:
            prb_id = ''
            problemAppend = ''

        ptsk_id = ""
        try: 
            if prb_id!='':
                p_sysid = item["problem_id"]['link'].split("problem/")[1]
                
                ptasks = get_incidents(token, f'{sn_base_url}/api/now/table/problem_task?sysparm_query=problem%3D{p_sysid}%5E')['result']
                for i in ptasks:
                    problemAppend = problemAppend.__add__(f" Task : {i['short_description']} , {i['work_notes']}")
                    ptsk_id = f"{i['number']},{ptsk_id}"
            else: ptasks = ""
        except: 
            ptasks = ""


        _summary = f'Configuration item {_cfg} has been raised with the issue: {item["short_description"]} '
        _chunk = f'Configuration item {_cfg} has: {item["short_description"]}, as given in: {clean_desc(item["description"])}. raised on {item["opened_at"]}. {item["business_impact"]} {item["comments_and_work_notes"]}'



        #======= Format for p1p2 table
        try:
            RDBMSJItem = {
                "Inc_id" : item["number"],
                "Raised_Date" : item["opened_at"] ,
                "Priority" : item["priority"] , 
                "Configuration item" : _cfg,
                "Short description" : item["short_description"], 
                "State": item["state"],
                "Business area impact": item["business_impact"] , 
                "Business category" : None, # not in call
                "Business service": _bi, 
                "Category": item["category"], 
                "Comments/Worknotes": item["comments_and_work_notes"], 
                "Description": item["description"], 
                "Probable cause": item["cause"] ,
                "Previous update": item["sys_updated_on"] ,
                "Problem": problemAppend.rstrip(','), 
                "Resolution notes": item["close_notes"] , 
                "Severity": item["severity"], 
                "MIM_agent_output_Blob": None
            }


            #=== Format for Ticket History table

            VecItem = {
                "inc_id" : item["number"], 
                "chunk": _chunk,
                "embedding": _get_embeddings(embedding_model, region_name, _chunk),
                "ci" : _cfg,
                "prb_id": prb_id, 
                "ptask_id": ptsk_id.rstrip(','),
                "link": f'{sn_base_url}/nav_to.do?uri=incident.do?sys_id={item["sys_id"]}', 
                "summary": _summary 
                }
            RDBMSJson.append(RDBMSJItem)
            VecJson.append(VecItem)



        except Exception as e:
            logger.info(f"Error in processing, no CI or business service in incident , dropping:{e}")

    return RDBMSJson , VecJson

# ================== Database Insert ==================
 
def insert_vector_data(data, db_config):  
    try:  
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        # SQL Insert Statement  
        insert_query = """  
        INSERT INTO ticket_history_vec (  
            inc_id,   
            chunk,   
            embedding,   
            ci,   
            prb_id,   
            ptask_id,   
            link,   
            summary  
        ) VALUES (  
            %(inc_id)s,   
            %(chunk)s,   
            %(embedding)s,   
            %(ci)s,   
            %(prb_id)s,   
            %(ptask_id)s,   
            %(link)s,   
            %(summary)s
        )  
        
        ON CONFLICT (inc_id) DO UPDATE SET
            chunk = EXCLUDED.chunk,
            embedding = EXCLUDED.embedding,
            ci = EXCLUDED.ci,
            prb_id = EXCLUDED.prb_id,
            ptask_id = EXCLUDED.ptask_id,
            link = EXCLUDED.link,
            summary = EXCLUDED.summary;

        """  
  
        # Execute the query  
        for row in data:  
            cursor.execute(insert_query, row)  
  
        # Commit the transaction  
        conn.commit()  
        
  
    except Exception as e:  
        logger.error(f"An error occurred:{e}")  
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()
 
 
 
 
 
 
# --------- RDBMS -----------
 
 
def insert_rdbms_data(data, db_config):  
    try:  
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        # SQL Insert Statement  
        insert_query = """  
        INSERT INTO P1P2_Incidents (  
            business_area_impact,   
            business_category,   
            business_service,   
            category,   
            comments_worknotes,   
            configuration_item,   
            description,   
            inc_id,   
            previous_update,   
            priority,   
            probable_cause,   
            problem,   
            raised_date,   
            resolution_notes,   
            severity,   
            short_description,   
            state  
        ) VALUES (  
            %(Business area impact)s,  
            %(Business category)s,  
            %(Business service)s,  
            %(Category)s,  
            %(Comments/Worknotes)s,  
            %(Configuration item)s,  
            %(Description)s,  
            %(Inc_id)s,   
            to_timestamp(%(Previous update)s , 'DD-MM-YYYY HH24:MI:SS'),  
            %(Priority)s,  
            %(Probable cause)s,  
            %(Problem)s,  
            to_timestamp(%(Raised_Date)s , 'DD-MM-YYYY HH24:MI:SS'), 
            %(Resolution notes)s,  
            %(Severity)s,  
            %(Short description)s,  
            %(State)s 
        )  
        
        ON CONFLICT (inc_id) DO UPDATE SET
            business_area_impact = EXCLUDED.business_area_impact,
            business_category = EXCLUDED.business_category,
            business_service = EXCLUDED.business_service,
            category = EXCLUDED.category,
            comments_worknotes = EXCLUDED.comments_worknotes,
            configuration_item = EXCLUDED.configuration_item,
            description = EXCLUDED.description,
            previous_update = EXCLUDED.previous_update,
            priority = EXCLUDED.priority,
            probable_cause = EXCLUDED.probable_cause,
            problem = EXCLUDED.problem,
            raised_date = EXCLUDED.raised_date,
            resolution_notes = EXCLUDED.resolution_notes,
            severity = EXCLUDED.severity,
            short_description = EXCLUDED.short_description,
            state = EXCLUDED.state;

        """  
  
        # Execute the query  
        for row in data:  
            cursor.execute(insert_query, row)  
  
        # Commit the transaction  
        conn.commit()  
        
  
    except Exception as e:  
        logger.error(f"An error occurred:{e}")  
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()  
# ================== Fetch ==================
 
def fetch_inc():
 
    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
 
    #
    timestamp = f"sys_updated_onBETWEENjavascript:gs.dateGenerate('{datetime.today().date() - timedelta(days=1) }','{datetime.now().time().strftime('%H:%M:%S')}')@javascript:gs.dateGenerate('{datetime.today().date()}','{datetime.now().time().strftime('%H:%M:%S')}')"
    #timestamp = "sys_updated_on%3Ejavascript%3Ags.beginningOfLast6Months()" 
    logger.info(f"API call for timestamp details: {timestamp}")
    # use this for final
    incidents = get_incidents(token, f'{sn_base_url}/api/now/table/incident?sysparm_display_value=true&sysparm_query={timestamp}^numberININC1495423,INC1495424,INC1495425')
    

    T1_push , TH_push = _format_(incidents , token)
   
    # Push here to T1 rdbms table
 
    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,  
        'host': db_host,  
        'port': db_port
    }

    insert_rdbms_data(T1_push, db_config)
    insert_vector_data(TH_push, db_config)
   
 
 

#=============== Knowledge Article ================
llm_model = configPythonSecrets['bedrock']['llm']
def _llm_(prompt, region_name = region_name , llm_model = llm_model):
    
    input_text = re.sub(email_pii, "[EMAIL_REDACTED]", prompt)
    prompt = re.sub(phone_pii, "[PHONE_REDACTED]", input_text[:2000])
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
    