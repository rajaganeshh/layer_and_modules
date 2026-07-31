import psycopg2
import urllib3
from urllib.parse import urlencode
import json
import boto3


http = urllib3.PoolManager()

def invoke_lambda_supervisor(functionName, incId):
    try:
        client = boto3.client('lambda')

        # Invoke the function
        response = client.invoke(
        FunctionName=functionName,
        InvocationType='Event', 
        Payload=json.dumps({"inc_id":incId}).encode('utf-8')
        )
        return response
    except Exception as e:
        raise Exception(f"Error calling lambda supervisor {e}")

def queue_incident_update(request, db_config):
    queue_entry = {
        "incident_id": request.incident_number,
        "request_payload": json.dumps(request.dict())
    }
    insert_into_queue_table(queue_entry, db_config)


def insert_into_queue_table(queue_entry, db_config):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        query = """
            INSERT INTO incident_update_queue (incident_id, request_payload)
            VALUES (%s, %s)
        """
        cursor.execute(query, (queue_entry["incident_id"], queue_entry["request_payload"]))
        conn.commit()
    except Exception as e:
        raise(f'Error in inserting to quewue table {e}')
    finally:
        if conn:
            cursor.close()
            conn.close()


def fetch_queued_incident_updates(db_config):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        query = """
            SELECT distinct incident_id FROM incident_update_queue WHERE processed = FALSE
        """
        cursor.execute(query)
        record = cursor.fetchall()
        if len(record) != 0:
            return record
        else:
            return None
    
    except Exception as e:
        raise(f'Error in Fetching Queued Incident {e}')
    
    finally:
        if conn:  
            cursor.close()  
            conn.close()



def clear_queue(incident_id, db_config):
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        query = """
            UPDATE incident_update_queue
            SET processed = TRUE
            WHERE incident_id = %s
        """
        cursor.execute(query, (incident_id,))
        conn.commit()
    except Exception as e:
        raise(f'Error in clearing queue {e}')
    finally:
        if conn:
            cursor.close()
            conn.close()


def fetch_agent_run_status(incId, db_config):
    try:
        
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        # cursor.execute("select run_status from agent_run_status where incident_id = %s;", (incId,))
        cursor.execute("select run_status from (SELECT inc_id, short_description, description, created_on, open_since, state, run_status, priority, configuration_item FROM (SELECT t2.inc_id, t2.short_description, t2.description, t2.raised_date AS created_on, t2.raised_date AS open_since, t2.state, t1.run_status, t2.priority, t2.configuration_item, ROW_NUMBER() OVER (PARTITION BY t2.inc_id ORDER BY CASE t1.run_status WHEN 'Processing Updates' THEN 0 WHEN 'CI Unavailable' THEN 1 WHEN 'Incident Processed' THEN 2 WHEN 'Incident Processing' THEN 3 WHEN 'Incident Received' THEN 4 ELSE 5 END ) AS rn FROM agent_run_status t1 LEFT JOIN p1p2_incidents t2 ON t1.incident_id = t2.inc_id) ranked WHERE rn = 1 ORDER BY run_status) where inc_id = %s;", (incId,))
        record = cursor.fetchone()
        if record is not None:
            return record[0]
        else:
            return 'New Incident'
        
        
    except Exception as e:  
        raise Exception(f"Error with Fetch mim agent output {e}")
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()

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
            mim_agent_output_blob = EXCLUDED.mim_agent_output_blob,
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
        cursor.execute(insert_query, data)  
  
        # Commit the transaction  
        conn.commit()  
        print("Data inserted successfully!")  

    except SyntaxError:
        pass
  
    except Exception as e:  
        raise Exception(f"p1p2_incidents_table insert error due to {e}")  
  
    finally:  
        if conn:  
            cursor.close()  
            conn.close()  
            
            
def format_data(response, agent_run_status, incId, db_config):
    #fetch run status for simon status in inc details page
    conn = psycopg2.connect(**db_config)  
    cursor = conn.cursor()
    # cursor.execute("select run_status from (SELECT inc_id, run_status FROM (SELECT t2.inc_id, t1.run_status, ROW_NUMBER() OVER (PARTITION BY t2.inc_id ORDER BY CASE t1.run_status WHEN 'Processing Updates' THEN 0 WHEN 'CI Unavailable' THEN 1 WHEN 'Incident Processed' THEN 2 WHEN 'Incident Processing' THEN 3 WHEN 'Incident Received' THEN 4 ELSE 5 END ) AS rn FROM agent_run_status t1 LEFT JOIN p1p2_incidents t2 ON t1.incident_id = t2.inc_id) ranked WHERE rn = 1 ORDER BY run_status) where inc_id = %s;", (incId,))

    # status = cursor.fetchone()

    if agent_run_status in ('New Incident', 'CI Unavailable'):
        status = fetch_agent_run_status (incId, db_config)


        RDBMSJson = []
    
        # For each incident returned
        for item in response["result"]:
    
            # business value
            try: _bi = item["business_service"]["value"]
            except: _bi = None
    
            # Config item
            try: _cfg = item["cmdb_ci"]["display_value"]
            except: _cfg = None
            # AssignedTo
            try: _asgTo = item["assigned_to"]["display_value"]
            except: _asgTo = None
    
            #======= Format for p1p2 table
            try:
                mimJson={
                    'ticketDetails':
                        {
                        'incidentId': item["number"],
                        'shortDescription': item["short_description"],
                        'decription': item["description"],
                        'category':item["category"],
                        'assignedTo':_asgTo,
                        'created':item['sys_created_on'],
                        'createdBy':item['sys_created_by'],
                        'urgency':item['urgency'],
                        'status' : status

                        },
                    'suspectedIncidents':[],
                    'similarIncidents':[],
                    'suspectedChanges':[],
                    'incidentResponse':[],
                    'knowledgebase':[],
                    'worknotes':item['work_notes']
                }
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
                    "Problem": "", 
                    "Resolution notes": item["close_notes"] , 
                    "Severity": item["severity"], 
                    "MIM_agent_output_Blob": json.dumps(mimJson).encode('utf-8')
                }
    
    
                RDBMSJson.append(RDBMSJItem)
                
            except Exception as e:  
                raise Exception(f"Error in processing {e}") 
    
        return RDBMSJson[0]
    elif agent_run_status in ('Incident Processed'):
        #read the existing mimJson from the p1p2_incidents table
        try:
        
            conn = psycopg2.connect(**db_config)  
            cursor = conn.cursor()  
    
            cursor.execute("select MIM_agent_output_Blob from p1p2_incidents where inc_id = %s;", (incId,))
            record = cursor.fetchone()

            status = fetch_agent_run_status (incId, db_config)

            # cursor.execute("select run_status from agent_run_status where incident_id = %s;", (incId,))
            # status = cursor.fetchone()

            mimJson = json.loads(record[0].tobytes().decode('utf-8'))

        except Exception as e:  
            raise Exception(f"Error with Fetch mim agent output {e}")
    
        finally:  
            # Close the connection  
            if conn:  
                cursor.close()  
                conn.close()  


        RDBMSJson = []
    
        # For each incident returned
        for item in response["result"]:
    
            # business value
            try: _bi = item["business_service"]["value"]
            except: _bi = None
    
            # Config item
            try: _cfg = item["cmdb_ci"]["display_value"]
            except: _cfg = None
            # AssignedTo
            try: _asgTo = item["assigned_to"]["display_value"]
            except: _asgTo = None
    
            #======= Format for p1p2 table with only updated records of incident
            try:
                mimJson['ticketDetails']['incidentId'] = item["number"]
                mimJson['ticketDetails']['shortDescription'] = item["short_description"]
                mimJson['ticketDetails']['decription'] = item["description"]
                mimJson['ticketDetails']['category'] = item["category"]
                mimJson['ticketDetails']['assignedTo'] = _asgTo
                mimJson['ticketDetails']['created'] = item["sys_created_on"]
                mimJson['ticketDetails']['createdBy'] = item['sys_created_by']
                mimJson['ticketDetails']['urgency'] = item["urgency"]
                mimJson['ticketDetails']['status'] = status


                mimJson['worknotes'] = item['work_notes']

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
                    "Problem": "", 
                    "Resolution notes": item["close_notes"] , 
                    "Severity": item["severity"], 
                    "MIM_agent_output_Blob": json.dumps(mimJson).encode('utf-8')
                }
    
    
                RDBMSJson.append(RDBMSJItem)
                
            except Exception as e:  
                raise Exception(f"Error in processing {e}") 
    
        return RDBMSJson[0]

def insert_agent_run_status_rdbms_data(data, db_config):
    
    try:  
        # Connect to the database  
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        # SQL Insert Statement  
        insert_query = """  
        INSERT INTO agent_run_status (     
            Entry_Time_STAMP,   
            Incident_ID,
            Run_Status     
        ) VALUES (    
            %(Entry_Time_STAMP)s::timestamp,  
            %(Incident_ID)s,  
            %(Run_Status)s     
        )  
        """
  
        # Execute the query  
        cursor.execute(insert_query, data)  
  
        # Commit the transaction  
        conn.commit()  
        print("Data inserted successfully!")  
  
    except Exception as e:  
        raise Exception(e)
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()  
            
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
      
def fetch_inc_detail_from_snow(incId, sn_base_url, sn_client_id, sn_client_secret, sn_token_url):
    
    api_url = f'{sn_base_url}/api/now/table/incident?sysparm_query=number%3D{incId}&sysparm_display_value=true'
    access_token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    response = http.request('GET', api_url, headers = headers)
    if response.status == 200:
        data = json.loads(response.data.decode('utf-8'))
        return data
    else:
        raise Exception(f"Failed to fetch incidents: {response.status} - {response.data}")
    


def fetch_sys_id(incId, sn_base_url, sn_client_id, sn_client_secret, sn_token_url):

    api_url = f"{sn_base_url}/api/now/table/incident?sysparm_query=number%3D{incId}&sysparm_fields=sys_id"
    access_token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    response = http.request('GET', api_url, headers = headers)
    if response.status == 200:
        data = json.loads(response.data.decode('utf-8'))
        return data['result'][0]['sys_id']
    else:
        raise Exception(f"Failed to fetch sys_id: {response.status} - {response.data}")

def update_worknotes(sys_id, worknote, user_name, sn_base_url, sn_client_id, sn_client_secret, sn_token_url):

    api_url = f"{sn_base_url}/api/now/table/incident/{sys_id}"
    access_token = get_access_token(sn_client_id, sn_client_secret, sn_token_url)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }

    if user_name is not None:
        worknote_update = user_name + ' - ' + worknote
        data = json.dumps({"work_notes":worknote_update})
        response = http.request('PUT', api_url, headers = headers, body = data)
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            return data
        else:
            raise Exception(f"Failed to Update incidents: {response.status} - {response.data}")
        
    elif user_name is None:
        worknote_update = worknote
        data = json.dumps({"work_notes":worknote_update})
        response = http.request('PUT', api_url, headers = headers, body = data)
        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            return data
        else:
            raise Exception(f"Failed to Update incidents: {response.status} - {response.data}")
