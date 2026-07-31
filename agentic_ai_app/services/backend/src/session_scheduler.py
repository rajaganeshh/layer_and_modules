import psycopg2

def session_scheduler(db_config):
    # need to connect with DB
    try:
      conn = psycopg2.connect(**db_config)
      cursor = conn.cursor()
      cursor.execute("""DELETE FROM sessions WHERE "createdAt"::date < CURRENT_DATE;""")
      conn.commit()
    except Exception as e:
      raise Exception(f"Error occured while deleting old sessions {e}")
    finally:
      #close the connection
      if conn:
         cursor.close()
         conn.close()
