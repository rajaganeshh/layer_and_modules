import psycopg2
import json

def fetch_all_incidents(db_config):
    """Fetches Incident Status from Agent Run Status"""
    try:
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
        cursor.execute("select t1.incident_id, t2.short_description, t2.raised_date, t2.raised_date, t2.state, t1.run_status  from agent_run_status t1 left join p1p2_incidents t2 on t1.incident_id = t2.inc_id")
        record = cursor.fetchall()
        return record
        
    except Exception as e:  
       raise Exception(f"Error with Fetch ALL Incidents {e}")
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()  

def fetch_mim_agent_output(incId, db_config):
    try:
        
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        cursor.execute("select MIM_agent_output_Blob from p1p2_incidents where inc_id = %s;", (incId,))
        record = cursor.fetchone()
        return json.loads(record[0].tobytes().decode('utf-8'))
        
        
    except Exception as e:  
        raise Exception(f"Error with Fetch mim agent output {e}")
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()  
        
        
