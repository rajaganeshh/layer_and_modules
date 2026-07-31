import psycopg2
import json

def fetch_all_incidents(db_config):
    """Fetches Incident Status from Agent Run Status"""
    try:
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
        cursor.execute("SELECT inc_id, short_description, description, created_on, open_since, state, run_status, priority, configuration_item FROM (SELECT t2.inc_id, t2.short_description, t2.description, t2.raised_date AS created_on, t2.raised_date AS open_since, t2.state, t1.run_status, t2.priority, t2.configuration_item, ROW_NUMBER() OVER (PARTITION BY t2.inc_id ORDER BY CASE t1.run_status WHEN 'Processing Updates' THEN 0 WHEN 'CI Unavailable' THEN 1 WHEN 'Incident Processed' THEN 2 WHEN 'Incident Processing' THEN 3 WHEN 'Incident Received' THEN 4 ELSE 5 END ) AS rn FROM agent_run_status t1 LEFT JOIN p1p2_incidents t2 ON t1.incident_id = t2.inc_id) ranked WHERE rn = 1 ORDER BY created_on desc;")
        record = cursor.fetchall()

        cursor.close()  
        conn.close()  

        return record
        
    except Exception as e:  
       print(f"Error with Fetch ALL Incidents {e}")
  

def fetch_mim_agent_output(incId, db_config):
    try:
        
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        cursor.execute("select MIM_agent_output_Blob from p1p2_incidents where inc_id = %s;", (incId,))
        record = cursor.fetchone()

        cursor.close()  
        conn.close() 
        return json.loads(record[0].tobytes().decode('utf-8'))
        
        
    except Exception as e:  
        print(f"Error with Fetch mim agent output {e}")

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
  

        
        
