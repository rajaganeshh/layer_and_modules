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

try:
    cutoff = configPythonSecrets['incThreshold']
except:
    cutoff = [-0.2 , 0.4, 20]
    """
    cut offs in order:
    Suspected incidents cutoff score
    Similar incident cutoff score
    Similar incidents hard cutoff
    """



import traceback
# ====================== LAMBDA HANDLER ===========================

def lambda_handler(event, context):
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    try:
        # Your business logic here
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")

        # ====== Initialize logger here =====


        outBlob = None
        inc_id = event["parameters"][0]["value"]
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


        # ============= Main code ================





        # ============= REMEMBER TO UNCOMMENT BEFORE ENDING ===============
        result = lambda_main(inc_id)
        logger.info(f"Processing completed")

        if result["code"]:  
            logger.info(f"\n\n======Results from algorithim========\nSuspected: {result['body']['suspected']}\n=====\nSimilar: {result['body']['similar']}\n=================================\n\n")
        else:   logger.error(result)

        outBlob = sync_blob(result,inc_id)
        update_blob(inc_id , outBlob["suspectedIncidents"] , outBlob["similarIncidents"])


        #=========== end =======================
        # outblob should be output


        # test === remove before sending
        #outBlob = test(inc_id)

        #===========================

        logger.info(f"MIM blob sync message sent to agent")

        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]

        response_body = {
        'TEXT': {
            'body': "Processesing complete"
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

        logger.info(f"========RETURNING PAYLOAD========\n{lambda_response}")

        log_contents = log_capture_string.getvalue()

        s3_client.put_object(
            Bucket=log_bucket,
            Key=log_key,
            Body=log_contents,
            ContentType='text/plain'
        )
        
        logger.info(f"Logs uploaded to s3://{log_bucket}/{log_key}")
        logger.removeHandler(ch)

        return lambda_response
        
    except Exception as e:

        # Still try to upload logs even if there's an error

        action_response = {
        "actionGroup": event["actionGroup"],
        "responseBody": traceback.format_exc(),
        }

        session_attributes = event["sessionAttributes"]
        prompt_session_attributes = event["promptSessionAttributes"]

        lambda_response = {
        "messageVersion": "1.0",
        "response": traceback.format_exc(),
        "sessionAttributes": session_attributes,
        "promptSessionAttributes": prompt_session_attributes,
        }

        logger.info(f"========RETURNING PAYLOAD========\n{lambda_response}")

        log_contents = log_capture_string.getvalue()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_key = f"{log_prefix}/{context.function_name}/{datetime.today().strftime('%Y-%m-%d')}/error_{inc_id}_{timestamp}_{context.aws_request_id}.log"
        

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
        # Clean 
        logger.removeHandler(ch)
        

def start_agentUpdate(inc_id):
    try:
        db_config = {  
            'dbname': db_name,  
            'user': db_user,  
            'password': db_password,  
            'host': db_host,  
            'port': db_port
        } 

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor() 
        
        update_query = f"""              
            UPDATE agent_run_status
            SET run_status = %s
            WHERE incident_id = %s;
        """

        cursor.execute(update_query,("Incident Processing",inc_id))

        # Commit the transaction  
        conn.commit()   
        return True
    except:
        return False     
    


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
        logger.debug(data)
        return data
    else:
        raise Exception(f"Failed to get incidents: {response.status} - {response.data}")
    


#====================================================
# ===================== Utils =======================


#---------------- Related CIs ----------------------

# ------------ DB ------------

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

# -------- CI grab ------------


def rel_ci2(_cfg : str):
    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    _inc_ci = _sql_("""select distinct ci from ticket_history_vec
    where ci != 'NULL';""")
    _inc = []
    for i in _inc_ci:
        _inc.append(i[0])

    classtype = ["cmdb_ci_vm_instance","cmdb_ci_lb_pool"]

    query= f"{sn_base_url}/api/now/table/cmdb_key_value?sysparm_query=value%3D{_cfg}%5EkeySTARTSWITHApplication%5Econfiguration_item.sys_class_name%3D{"%5EORconfiguration_item.sys_class_name%3D".join(classtype)}&sysparm_display_value=true"
    _response = get_incidents(token,query)["result"]
    _values = []
    for i in _response:
        _values.append(i["configuration_item"]["display_value"])

    # unique items

    inc_cfg = list(set(_inc))
    cmdb_cfg = list(set(_values))
    overlap_cfg = list(set(inc_cfg) & set(cmdb_cfg))
    overlap_cfg.append(_cfg)
    logger.info(f"""
==== Related CI Search Logic 2 ====
Searching for CI: {_cfg}
CIs that are in incidents: {inc_cfg}
CIs that are in CMDC: {cmdb_cfg}
overlapping CIs: {overlap_cfg.__len__()}

CIs: {overlap_cfg}


===========================
""")

    return tuple(overlap_cfg)
    

# Using Parent Child logic

def _related_ci(inc_ci):
    
    all_c1 = list()
    all_c2 = list()
    all_parent = list()

    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    ci_set = tuple([f'{inc_ci}'])

    logger.info("\n===============================\n========= Related CI Logic 1 =======")

    # get sysid
    ci_sysid = get_incidents(token, f'{sn_base_url}/api/now/table/cmdb_ci?sysparm_query=name%3D{inc_ci}&sysparm_fields=sys_id')["result"][0]["sys_id"]
    
    #  parent   

    parent1 = get_incidents(token, f'{sn_base_url}/api/now/table/cmdb_rel_ci?sysparm_query=child%3D{ci_sysid}&sysparm_display_value=all&sysparm_fields=parent')["result"]
    for _ci in parent1:
        ci_set = ci_set + (f'{_ci["parent"]["display_value"]}',)
        all_parent.append(f'{_ci["parent"]["display_value"]}')

    logger.info( f" \n==== Parent CIs =====\n {ci_set}")


    # child gen 1   
    child1 = get_incidents(token, f'{sn_base_url}/api/now/table/cmdb_rel_ci?sysparm_query=parent%3D{ci_sysid}&sysparm_display_value=all&sysparm_fields=child')["result"]
    
    
    child_sysparam = []
    
    for _ci in child1:
        _child_sys = _ci["child"]["value"]
        ci_set = ci_set + tuple([f'{_ci["child"]["display_value"]}'])
        child_sysparam.append(_child_sys)
        all_c1.append(f'{_ci["child"]["display_value"]}')


    logger.info(f"Child1 - {child_sysparam.__len__()} children found")
    logger.info( f"  \n==== Children Level 1 Added =====\n  {ci_set}")
    
    

    chunk_size = 30
    split_lists = [child_sysparam[i:i + chunk_size] for i in range(0, len(child_sysparam), chunk_size)]
    #logger.info(f"Split lists: {split_lists}")
    try:
        for chunk_item in split_lists:
            param = "parent%3D"+"%5EORparent%3D".join(list(set(chunk_item)))
            #logger.info(f"Going for: {chunk_item}")
            child2 = get_incidents(token, f'{sn_base_url}/api/now/table/cmdb_rel_ci?sysparm_query={param}&sysparm_display_value=all&sysparm_fields=child')["result"]
                
            for _ci in child2:
                _child_sys = _ci["child"]["value"]
                ci_set = ci_set + tuple([f'{_ci["child"]["display_value"]}'])
                all_c2.append(f'{_ci["child"]["display_value"]}')


        logger.info(f"Child2 - {child2.__len__()} children found")
        logger.info( f"  \n==== Children Level 2 Added =====\n  {ci_set}")
    except Exception as e:
        logger.info( f"no level 2 children: {e}")

    # return overlap
    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    _inc_ci = _sql_("""select distinct ci from ticket_history_vec
    where ci != 'NULL';""")
    _inc = []
    for i in _inc_ci:
        _inc.append(i[0])
    

    inc_cfg = list(set(_inc))
    overlap_cfg = list(set(inc_cfg) & set(ci_set))
    logger.info(f"\n ==== Overlapping CIs ====\n{overlap_cfg.__len__()} Items,\n{overlap_cfg}")

    all_cis = {
        "incident_ci": [inc_ci] ,
        "parents": list(set(all_parent)) ,
        "children_level1": list(set(all_c1)) ,
        "children_level2": list(set(all_c2))
    }

    return tuple(overlap_cfg) , all_cis


# ----------- Get embeddings ----------

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


# -------------- LLM --------------------------

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

#=========================================================


# store some temp data

def tempData(inc_id , field , data):
    db_config = {
        'dbname': db_name,
        'user': db_user,
        'password': db_password,
        'host': db_host,
        'port': db_port
    }
    conn = psycopg2.connect(**db_config)  
    cursor = conn.cursor()

    # pull the latest blob
    blob_query = f"""              
                Select  MIM_agent_output_blob from P1P2_Incidents
                WHERE inc_id = '{inc_id}';
        """



    cursor.execute(blob_query)
    cursor_return = cursor.fetchall()


    try:
        op_blob = (cursor_return[0][0])
    except:
        op_blob = None
    
    # rare case if blob is empty
    if op_blob == None:
        pass
    else:
        mimjson = json.loads(op_blob.tobytes().decode('utf-8'))
        mimjson[field] = data

        json_bytes = json.dumps(mimjson).encode('utf-8')
        insert_query = f"""              
            UPDATE P1P2_Incidents
            SET MIM_agent_output_blob = %s
            WHERE inc_id = %s;
        """
        
        cursor.execute(insert_query,(json_bytes,inc_id))
        conn.commit()
        logger.info(f"====== ADDED TEMP DATA TO FIELD {field} =======")

    # Close the connection  
    if conn:
        cursor.close()
        conn.close()





#==========================================================

def clean_desc(_text : str):
    _temp = _text.replace("CAUTION: This email originated from outside of the organisation. Do not click links or open attachments unless you recognise the sender and know the content is safe.", "")
    _temp = _temp.replace("The information in this e-mail and any attachments is confidential and may be legally privileged. It is intended solely for the addressee(s) named above. If you are not an intended recipient, please notify the sender and delete the message and any attachments from your system. Any use, copying or disclosure of the contents of either is unauthorised unless expressly permitted. Any views expressed in this message are those of the sender unless expressly stated as to be those of easyJet. Virus checking of emails and attachments is the responsibility of the recipient. easyJet Airline Company Limited Registered in England with Registered number: 3034606 Subsidiary of easyJet Plc Registered in England with registered number: 3959649 Registered Office: Hangar 89, London Luton Airport, Luton, Bedfordshire LU2 9PF Click here to report this email as spam.","")
    return _temp

def _format_(response , token):

    RDBMSJson = []
    VecJson = []

    for item in response["result"]:

        # ==========  preprocessing

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
            logger.info(f"Error in processing, {traceback.format_exc()}:")

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
        logger.error(f"An error occurred:{traceback.format_exc()}")  
  
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
            mim_agent_output_blob,   
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
            %(MIM_agent_output_Blob)s,  
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

def update_table():

    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)

    # ============Update The table first=======

    end_time = datetime.utcnow()
    #start_time = end_time - timedelta(hours=24)
    start_time = end_time.replace(hour=3, minute=30, second=0, microsecond=0)
    
    if end_time < end_time.replace(hour=18, minute=30, second=0, microsecond=0):
        start_time -= timedelta(days=1)
    logger.info(f"UTC TIME FUNCTION HAS RUN FROM: {end_time}")
    timestamp = f"sys_updated_on%3Ejavascript%3Ags.dateGenerate('{start_time.date()}'%2C'04%3A30%3A00')"

    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,  
        'host': db_host,  
        'port': db_port
    }

    BATCH_SIZE = 500
    offset = 0
    total_updated = 0

    while True:
        # Fetch one batch from ServiceNow using sysparm_limit + sysparm_offset
        batch_url = (
            f'{sn_base_url}/api/now/table/incident'
            f'?sysparm_display_value=true'
            f'&sysparm_query={timestamp}^priorityIN1,2,3'
            f'&sysparm_limit={BATCH_SIZE}'
            f'&sysparm_offset={offset}'
        )
        incidents = get_incidents(token, batch_url)
        batch_results = incidents.get("result", [])

        if not batch_results:
            logger.info(f"No more incidents at offset {offset}. Pagination complete.")
            break

        logger.info(f"Processing batch: offset={offset}, count={len(batch_results)}")

        T1_push, TH_push = _format_({"result": batch_results}, token)
        insert_rdbms_data(T1_push, db_config)
        insert_vector_data(TH_push, db_config)

        total_updated += len(T1_push)
        logger.info(f"Batch inserted. Running total: {total_updated} items")

        # If fewer results than BATCH_SIZE came back, we've reached the last page
        if len(batch_results) < BATCH_SIZE:
            logger.info("Last batch reached. Pagination complete.")
            break

        offset += BATCH_SIZE

    logger.info(f"Table update complete for Timestamp: {timestamp}. Total items updated: {total_updated}")

#=================== Ticket Logic ===================





# --- Similar incidents ----

def historical_tickets(_new_incident , db_config):


    flag = False

    try:  
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  

        # get details of self
        _query = f"""    
            SELECT category,configuration_item FROM P1P2_Incidents
            WHERE inc_id = '{_new_incident}'
            """

        cursor.execute(_query)  
        _ctg , _cfg  = cursor.fetchall()[0]
        

        # SQL Query Statement  
        _query = f"""
            SELECT inc_id,short_description FROM P1P2_Incidents
            WHERE configuration_item = '{_cfg}'
                AND inc_id != '{_new_incident}'
            ORDER BY raised_date DESC;
            """  

        cursor.execute(_query)  
        rows = cursor.fetchall()

        


        # removing self
        
        results = []
        search_l = []
        for row in rows:
            
            results.append(row)
            search_l.append(f'{row[0]}')

        search_inc = tuple(search_l)



        # Flagging Results
        if search_inc.__len__()==0:
            return {"code" : False , "body": "no incidents in history"}
        else: flag = True


        # Read embeds - GoalTicket
    
        _fetch_embed = f"""
            SELECT embedding from ticket_history_vec
            where inc_id = '{_new_incident}';
        """
        cursor.execute(_fetch_embed)
        new_embed_vec = cursor.fetchall()[0][0]
        logger.info("Similar / Historical Tickets")
        # VectorSearch
        score_table = "==============================================================================\n============= Similarity Table =================\n"


        if search_inc.__len__() == 1:

            _vec_search = f"""
            select inc_id , summary , 1 - POWER(( embedding <-> '{new_embed_vec}' ),2)
            from ticket_history_vec
            where inc_id = '{search_inc[0]}'
            order by embedding <-> '{new_embed_vec}'
            limit {cutoff[2]}
            """

        else:
            _vec_search = f"""
            select inc_id , summary , 1 - POWER(( embedding <-> '{new_embed_vec}' ),2)
            from ticket_history_vec
            where inc_id in {search_inc}
            order by embedding <-> '{new_embed_vec}'
            limit {cutoff[2]}
        """
        

        cursor.execute(_vec_search)
        search_results = cursor.fetchall()
        search_dict = {}
        # Flagging Results
        if search_results.__len__()!=0:
                for row in search_results:

                    score_table += f"{row[0]} | {row[2]} | {row[1]}\n"
                    search_dict[row[0]] = row
                flag = True
                score_table += (f"\n=========== found { rows.__len__() } results==============\n")
        score_table += "==============================================================================\n=============================================================================="
        logger.info(score_table)


        time_results = []
        for t_i in search_inc:
            try:
                time_results.append( search_dict[t_i] )
            except:
                pass


        if search_results.__len__()==0:
            flag = False
        else: 
            flag = True
            search_results = [time_results]

    except Exception as e:  
        logger.error(f"An error occurred:{e}")  
        flag = False
        search_results = traceback.format_exc()
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()
    return {
                "code": flag,
                "body": search_results
                
                }




# ---------- Suspected Incidents --------------
 

def sus_tickets( inc_id , db_config):
    flag = False
    result = []
    try:
        # Connect to the database  
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()


        _fetch_new = f"""
            SELECT short_description , configuration_item from P1P2_Incidents
            where inc_id = '{inc_id}';
            """
        cursor.execute(_fetch_new)
        _desc , _cfg = cursor.fetchall()[0]

    # --- fetch upstream-downstream

        direct_ci , allCI = _related_ci(_cfg)
        key_ci = rel_ci2(_cfg)

        _cfgs = tuple(set( direct_ci + key_ci ))
        # - send to Change agent
        tempData(inc_id , "all_cis" , allCI)



    # --- SQL Query Statement  

        if _cfgs.__len__()==1:
            _query = f"""
            SELECT inc_id,short_description FROM P1P2_Incidents
            WHERE inc_id != '{inc_id}'
                AND configuration_item = '{_cfgs[0]}'
                AND previous_update > (SELECT raised_date - INTERVAL '3 days' FROM P1P2_Incidents
            		WHERE inc_id = '{inc_id}' limit 1)
            ORDER BY raised_date DESC
            LIMIT 150;
            """

        else:
            _query = f"""
            SELECT inc_id,short_description FROM P1P2_Incidents
            WHERE inc_id != '{inc_id}'
                AND configuration_item in {_cfgs}
                AND previous_update > (SELECT raised_date - INTERVAL '3 days' FROM P1P2_Incidents
            		WHERE inc_id = '{inc_id}' limit 1)
            ORDER BY raised_date DESC
            LIMIT 150;
            """


        cursor.execute(_query)
        rows = cursor.fetchall()

        search_inc = []
        for row in rows:
            search_inc.append(f'{row[0]}')

        # Cap to 150 most-recent incidents to avoid runaway LLM + embedding calls.
        # The SQL already orders by raised_date DESC so we keep the most relevant ones.
        MAX_INCIDENTS = 150
        if len(search_inc) > MAX_INCIDENTS:
            logger.info(f"Capping search_inc from {len(search_inc)} to {MAX_INCIDENTS} to prevent timeout")
            search_inc = search_inc[:MAX_INCIDENTS]

        search_inc = tuple(search_inc)

        if search_inc.__len__()==0:
            logger.info("no tickets in suspected CIs")
            if conn:
                cursor.close()
                conn.close()
            return {"code": False,
                    "body": f"no tickets within CIs:{_cfgs}" }


        # # LESS THAN 30
        # if search_inc.__len__()<30:
        #     flag = True
        #     logger.info("Less than 30 incidents, passing with no failure")
        #     if search_inc.__len__()==1:
            
        #         _vec_search = f"""
        #         select inc_id , summary , 1
        #         from ticket_history_vec
        #         where inc_id = '{search_inc[0]}'
        #         order by inc_id desc
        #         """

        #     else:

        #         _vec_search = f"""
        #         select inc_id , summary , 1
        #         from ticket_history_vec
        #         where inc_id in {search_inc}
        #         order by inc_id desc
        #         """
        #     logger.info(_vec_search)
        #     try:
        #         cursor.execute(_vec_search)
        #         rows = cursor.fetchall()

        #         result = []
        #         for row in rows:
        #             result.append(row)

        #     except Exception as e:
        #         result = traceback.format_exc()
        #         flag = False

        #     logger.info(result)
        #     return {"code": flag,
        #             "body": result}
        # else:
        #     logger.info("more than 30 incidents Processing")



        _causes = _llm_(f"""
        What kind of upstream downstream software failures may cause {_desc}? 
        list 8 possible specific systems failing that may cause them in about 20 words per system in detail.
        split each reason/system using the pipe symbol "|".
        Do not give any other irrelevant text before or after, only give the reasons as the output text will go through regex.
        Do not overrepeat the name of the system.
        Additionally, here are some of the systems in the network that could be relavant: {" , ".join(direct_ci)} , Virtual machines , Load balancers
        using the same instructions, additionally generate 1 reason for system failure similar to the other 5 , but now 1 per system given in the list above
        Here are some examples of failures, include these as well:
            - "Web server issue, memory and cpu utillization is high"
            - "Alert signals sent by hardware"
            - "Virtual Machine has shut down causing host not showing details on website"
        
        some details about the systems:
            - Anything with "AS" at the end is an application service.
            - ip adresses should be treated as gateways
            - All applications run on virtual machines, Which all are codes that start with D
            - All load balancers are codes that start with E
            - For rest of the systems, assume AWS based systems

        do not just say "failure" , Give a proper reason or cause for each point of failure , since it will be used for semantic search
            """.replace(_cfg , " "))

        # loop over causes
        score_table = "==============================================================================\n============= Score Table ================="
        logger.info(f"Searching for reasons: {_causes}")
        results = []
        flag = False
        for cause in _causes.split('|'):
            if cause.__len__()<3: pass
            chunk = f'{cause} { datetime.today().date() - timedelta(days=3) }.'
            search_embed = _get_embeddings(embedding_model, region_name, chunk)        
            
            if search_inc.__len__()==1:
            
                _vec_search = f"""
                select inc_id , summary , 1 - ( embedding <-> '{search_embed}' )
                from ticket_history_vec
                where inc_id = '{search_inc[0]}'
                order by embedding <-> '{search_embed}'
                """

            else:

                _vec_search = f"""
                select inc_id , summary , 1 - ( embedding <-> '{search_embed}' )
                from ticket_history_vec
                where inc_id in {search_inc}
                order by embedding <-> '{search_embed}'
                """

            cursor.execute(_vec_search)
            rows = cursor.fetchall()
            score_table += (f"\nSearching for reason:{cause}\n")
            if rows.__len__()!=0:
                for row in rows:
                    results.append([(row[0],row[1],row[2])])
                    score_table += f"{row[0]} | {row[2]} | {row[1]}\n"
                flag = True
                score_table += (f"\n=========== found { rows.__len__() } results==============\n")
        score_table += "==============================================================================\n=============================================================================="
        logger.info(score_table)

        # score unification            
        best_scores = {}
        for row in results:
            pk, desc, score = row[0][0] , row[0][1] , row[0][2]
            if (pk not in best_scores) or (score > best_scores[pk][2]):
                best_scores[pk] = (pk, desc, score)

        #combined_list = sorted(best_scores.values(), key=lambda x: x[2], reverse=True)
        combined_list = []
        for tempInc in search_inc:
            try:
                combined_list.append(best_scores[tempInc])
            except:
                pass

        logger.info(combined_list)
        result = combined_list
        
        
    except Exception as e:
        flag = False
        logger.error(e)
        result = traceback.format_exc()
        
    
    finally:
        if conn:
            cursor.close()
            conn.close()
        return {"code": flag,
                "body": result}


#-------------- Blob Formatter ---------------

def __get_summary__(inc_id , db_config):
    
    conn = psycopg2.connect(**db_config)  
    cursor = conn.cursor()
    
    _fetch_embed = f"""
            SELECT summary from ticket_history_vec
            where inc_id = '{inc_id}';
        """
    cursor.execute(_fetch_embed)
    
    summary = cursor.fetchall()


    cursor.close()  
    conn.close()
    return summary[0][0]

#---------- get transcripts ----------

# Send this to kaustav's code when needed
def teams_fetch(inc_list):
    try:
        logger.info(f"===Transcripts fetch for similar incidents===\n{inc_list}\n===")
        
        #reformat
        sim_l = []
        for i in inc_list:
            sim_l.append(f'{i}')
        sim_inc = tuple(sim_l)

        
        if sim_inc.__len__() == 1:

            ts_search = f"""
            select knowledge_id , link , summary
            from knowledge_vec
            where knowledge_id = '{sim_inc[0]}'
            """

        else:
            ts_search = f"""
            select knowledge_id , link , summary
            from knowledge_vec
            where knowledge_id in {sim_inc}
        """
        logger.info(f"==== Transcript search results: {ts_search}")
        outResult = _sql_(ts_search)


        out = []
        for row in outResult:
            item = {
                "source":"Teams Transcripts",
                "incidentId": row[0],
                "link": row[1],
                "summary": row[2]
            }
            out.append(item)
        
        return out
    except:
        logger.info(traceback.format_exc())
        return []


# ========== blob ===================

def update_blob(inc_id , sus , sim): # pass any other params if you want to update

    db_config = {
        'dbname': db_name,
        'user': db_user,
        'password': db_password,
        'host': db_host,
        'port': db_port
    }


    # pull the latest blob
    blob_query = f"""              
                Select  MIM_agent_output_blob from P1P2_Incidents
                WHERE inc_id = '{inc_id}';
        """
    conn = psycopg2.connect(**db_config)  
    cursor = conn.cursor()  
    cursor.execute(blob_query)
    cursor_return = cursor.fetchall()
    
    try:
        op_blob = (cursor_return[0][0])
    except:
        op_blob = None
    
    # rare case if blob is empty
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

    # change this based on your requirement
    # make your updates here like updating to a dict
    
    mimjson['suspectedIncidents'] = sus

    mimjson['similarIncidents'] = sim
    
    try:
        mimjson['transcripts'] = teams_fetch(mimjson['sim_id']) # push this to kaustav
    except:
        mimjson['transcripts'] = []
    
    
    json_bytes = json.dumps(mimjson).encode('utf-8')

    # ======== uncomment this part if you want to update the blob ============
    insert_query = f"""              
        UPDATE P1P2_Incidents
        SET MIM_agent_output_blob = %s
        WHERE inc_id = %s;
    """
    cursor.execute(insert_query,(json_bytes,inc_id))
    conn.commit()
    # ========================================================================

    # Close the connection  
    if conn:
        cursor.close()
        conn.close()
    logger.info(json.dumps(mimjson , indent=3))
    # =========== USE THIS TO RETURN THE BLOB =======
    #return json_bytes # write this to mim blob



def sync_blob(results , inc_id):
    
    db_config = {
        'dbname': db_name,
        'user': db_user,
        'password': db_password,
        'host': db_host,
        'port': db_port
    }

    sus_out = []
    sim_out = []
        

    token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)

    try:
        if results["code"]:
            logger.info(f"Cut off scores:\nsus>{cutoff[0]}\nsim>{cutoff[1]}")
            _sus = results["body"]["suspected"] 
            _sim = results["body"]["similar"]

            if _sus["code"]:
                _done = []
                for _inc in _sus["body"]:
                    if (_inc[0]  not in _done) and (_inc[2] > cutoff[0]):
                        _done.append(_inc[0])
                    

                        incident = get_incidents(token, f'{sn_base_url}/api/now/table/incident?sysparm_display_value=true&sysparm_query=number%3D{_inc[0]}&sysparm_limit=1')["result"][0]
                    
                        try: asg = incident['assignment_group']['display_value']
                        except: asg = None
                        try: bss = incident['business_service']['display_value']
                        except: bss = None
                        try: _cfg = incident["cmdb_ci"]["display_value"]
                        except: _cfg = None
                        

                        suspectedIncidents = {
                            "incidentId":incident['number'],
                            "shortDescription":incident['short_description'],
                            "createdOn": incident['sys_created_on'],
                            "priority":incident['priority'],
                            "assignedGroup":asg,
                            "businessService":bss,
                            "summary":incident['description'],
                            "workNotes":incident['comments_and_work_notes'],
                            "resolution":incident['close_notes'],
                            "impactedServices":incident['business_impact'],
                            "description": incident['description'],
                            "category": incident['category'],
                            "link":f"{sn_base_url}/nav_to.do?uri=incident.do?sys_id={incident['sys_id']}",
                            "configurationItem" : _cfg
                        }
                        sus_out.append(suspectedIncidents)
            else:
                logger.info(f"====Tracebck for suspected===={results}")

            simID = [inc_id]
            if _sim["code"]:
                
                for _inc in _sim["body"][0]:
                    if _inc[2]>= cutoff[1]:
                        simID.append(_inc[0])
                        incident = get_incidents(token, f'{sn_base_url}/api/now/table/incident?sysparm_display_value=true&sysparm_query=number%3D{_inc[0]}&sysparm_limit=1')["result"][0]
                        
                        try: asg = incident['assignment_group']['display_value']
                        except: asg = None
                        try: bss = incident['business_service']['display_value']
                        except: bss = None
                        try: _cfg = incident["cmdb_ci"]["display_value"]
                        except: _cfg = None
                        
                        similarIncidents = {
                            "incidentId":incident['number'],
                            "shortDescription":incident['short_description'],
                            "createdOn": incident['sys_created_on'],
                            "priority":incident['priority'],
                            "assignedGroup":asg,
                            "businessService":bss,
                            "summary":incident['description'],
                            "workNotes":incident['comments_and_work_notes'],
                            "resolution":incident['close_notes'],
                            "impactedServices":incident['business_impact'],
                            "description": incident['description'],
                            "category": incident['category'],
                            "link":f"{sn_base_url}/nav_to.do?uri=incident.do?sys_id={incident['sys_id']}",
                            "configurationItem" : _cfg
                        }
                        sim_out.append(similarIncidents)
                tempData(inc_id, "sim_id",simID)
            else: 
                tempData(inc_id, "sim_id",simID)
                logger.info(f"====Tracebck for Similar===={results}")
        else:
            logger.info(f"====Tracebck for Overall===={results}")

    except Exception as e:
        logger.error(traceback.format_exc())
    return {"suspectedIncidents" : sus_out , "similarIncidents" : sim_out}


# ------------- Main function -----------------
def lambda_main(new_inc):

    # update the table first, similar to what was done in the earlier function
    update_table()

    logger.info("Update complete. Proceeding with ticket logic...")

    db_config = {  
        'dbname': db_name,  
        'user': db_user,  
        'password': db_password,  
        'host': db_host,  
        'port': db_port
    } 

    try:
        # similar incidents
        out_sim = historical_tickets( new_inc , db_config )
        out_sus = sus_tickets(new_inc , db_config)
        logger.info("========= Outcomes ==========")
        logger.info(out_sim)
        logger.info(out_sus)
        return {
            "code" : True,
            "body":{
                "suspected": out_sus,
                "similar": out_sim
                    }
        }
    except Exception as e:
        logger.info(traceback.format_exc())
        return {
            "code" : False,
            "body" : traceback.format_exc()
        }




