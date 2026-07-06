import psycopg2  
  
# Database connection details  
db_config = {  
    'dbname': 'postgres',  
    'user': 'postgres',  
    'password': 'rXtkKLpkt?~77e[TetRVEz.Wjpaj',  
    'host': 'easyjet-db-1.cluster-cvyokiskw2z0.ap-south-1.rds.amazonaws.com',  
    'port': '5432'  # Default PostgreSQL port  
}  
  
# Function to insert data into the database  
# def fetch_agent_run_status(incId, db_config):
#     try:
#         conn = psycopg2.connect(**db_config)  
#         cursor = conn.cursor()  
  
#         cursor.execute("SELECT Run_Status FROM public.agent_run_status WHERE incident_id = %s;", (incId,))
#         record = cursor.fetchone()
        
#         return record[0]
        
        
#     except Exception as e:  
#        print(e)
  
#     finally:  
#         # Close the connection  
#         if conn:  
#             cursor.close()  
#             conn.close()  
            
# print(fetch_agent_run_status('INC0010016', db_config))


def fetch_agent_run_status(db_config):
    try:
        conn = psycopg2.connect(**db_config)  
        cursor = conn.cursor()  
  
        cursor.execute("select t1.incident_id, t2.short_description, t2.raised_date, t2.raised_date, t2.state, t1.run_status  from agent_run_status t1 left join p1p2_incidents t2 on t1.incident_id = t2.inc_id")
        record = cursor.fetchall()
        
        return record
        
        
    except Exception as e:  
       print(e)
  
    finally:  
        # Close the connection  
        if conn:  
            cursor.close()  
            conn.close()  
            
print(fetch_agent_run_status(db_config))