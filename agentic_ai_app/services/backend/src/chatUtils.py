import json
from datetime import datetime
import psycopg2
import os
import boto3
from botocore.exceptions import ClientError
import traceback
import re
# ====================== ENV ============================
secret_name = os.environ['secret_name']
region_name = os.environ['region_name']

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
llm_model = configPythonSecrets['bedrock']['llm']

# =================== Chat Util Function =============================
def _llm_(prompt, region_name = region_name , llm_model = llm_model):

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
#-------------- UTILS ----------------

def sql(query , db_config):
    print(query)
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute(query)
    out = cursor.fetchall()
    print(f"Sql output : {out}")
    return out

def clean_desc(_text : str):
    _temp = _text.replace("CAUTION: This email originated from outside of the organisation. Do not click links or open attachments unless you recognise the sender and know the content is safe.", "")
    _temp = _temp.replace("The information in this e-mail and any attachments is confidential and may be legally privileged. It is intended solely for the addressee(s) named above. If you are not an intended recipient, please notify the sender and delete the message and any attachments from your system. Any use, copying or disclosure of the contents of either is unauthorised unless expressly permitted. Any views expressed in this message are those of the sender unless expressly stated as to be those of easyJet. Virus checking of emails and attachments is the responsibility of the recipient. easyJet Airline Company Limited Registered in England with Registered number: 3034606 Subsidiary of easyJet Plc Registered in England with registered number: 3959649 Registered Office: Hangar 89, London Luton Airport, Luton, Bedfordshire LU2 9PF Click here to report this email as spam.","")
    return _temp

#===================== Tools ==============================
#----------- Tickets timestamp -------------

def inc_timestamp(query , ci = None , db_config = None):
    chatlog = "===\n"
    current_time = datetime.now()
    time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
    day = current_time.strftime("%A")

    prompt = f"""
    You are a tool for an SQL query generator, and you need to extract start and end timestamps from a sentence that the user gives to you
    - Current time : {time_string}
    - Current day : {day}

    - If the user provides a time frame, parse it with respect to current date and time in 'YYYY-MM-DD HH24:MI:SS' format, and give the timestamps seperated by a pipe symbol '|' .
    Example:
        <start_time>|<end_time>
    do not surround it with any quotes

    - If the user says "last N days/months/hours" etc, calculate the start time as NOW() - INTERVAL 'N days' and use NOW() as the end time.
    - make sure if the "last N days/months" is more than an a day, you should include today in the timestamp
    - if the user asks for a rough timestamp (around 3 days back / about 4am) , add 1 unit of time (day or hour based on what was asked) before and after specific date/time to account for approximation.
    

    - If the user provides a date range, use those dates formatted directly as start and end timestamps.
    - only provide the timestamps, do not give anything else.
    - while calculating timestamp, keep in mind things like months having different number of days, leap years etc.

    User's query = {query}
    """

    timestamp = _llm_(prompt)

    chatlog = chatlog.__add__(f"Extracted timestamps : {timestamp} \n")    

    stamps = timestamp.split('|')
    if ci != None:
        out = sql(f"""
            select inc_id , short_description , raised_date from p1p2_incidents
            where previous_update between '{stamps[0]}' and '{stamps[1]}'
            and configuration_item = '{ci}'
            order by raised_date desc
                """,db_config)
        chatlog = chatlog.__add__(f"Extracted for CI : {ci} \n")

    else:
        out = sql(f"""
            select inc_id , short_description , raised_date from p1p2_incidents
            where previous_update between '{stamps[0]}' and '{stamps[1]}'
            order by raised_date desc
                """,db_config)
    return out , chatlog


# ---------- ticket ID ---------------------

def _get_inc_id(id , db_config):

    out = sql(f"""
        select inc_id , configuration_item , short_description , description , resolution_notes , raised_date from p1p2_incidents
        where inc_id = '{id}'
                """, db_config)
    summary = ""
    item = out[0]
    if item[1]!="": summary = summary.__add__(f"For configuration Item: {item[1]}, ")
    if item[2]!="": summary = summary.__add__(f"{item[2]}\n")
    if item[3]!="": summary = summary.__add__(f"{item[3]}\n")
    if item[4]!="": summary = summary.__add__(f"Resolution notes: {item[4]}\n")

    return [[item[0] , clean_desc(summary) , item[5]]]


# ----------- Change timestamp -------------

# def chg_timestamp(u_prompt , db_config):
#     current_time = datetime.now()
#     time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
#     day = current_time.strftime("%A")

#     prompt = f"""You are a SQL query generator for a chatbot that retrieves records from a table named change_history_vec.
#     - Current time : {time_string}
#     - Current day : {day}

#     Based on the user's input, generate a valid SQL query to fetch relevant records. The user may ask for:
#     - A specific record using the primary key chg_id.
#     - A group of records filtered by a time frame (e.g., "last 10 days", "from Sept 1 to Sept 10", etc.).
#     - A group of records filtered based on a particular 'ci'
#     - A group of records based on a combination of any of the above

#     Rules:
#     - If the user provides a chg_id, generate a query like:
#             SELECT chg_id, summary, TO_TIMESTAMP(
#                     SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
#                     'DD-MM-YYYY HH24:MI:SS'
#                 ) as timestamp FROM change_history_vec WHERE chg_id = '<chg_id>';
#     - If the user provides a time frame, parse it and generate a query using TO_TIMESTAMP and sys_updated_on extracted from the chunk field. Example:
#             SELECT chg_id, summary, TO_TIMESTAMP(
#                     SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
#                     'DD-MM-YYYY HH24:MI:SS'
#                 ) as timestamp
#             FROM change_history_vec
#             WHERE TO_TIMESTAMP(
#                     SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
#                     'DD-MM-YYYY HH24:MI:SS'
#                 ) BETWEEN '<start_time>' AND '<end_time>';

#     - If 'ci' is provided in the query, add that condition to the where clause also. Example:
#             SELECT chg_id, summary, TO_TIMESTAMP(
#                     SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
#                     'DD-MM-YYYY HH24:MI:SS'
#                 ) as timestamp
#             FROM change_history_vec
#             WHERE TO_TIMESTAMP(
#                     SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
#                     'DD-MM-YYYY HH24:MI:SS'
#                 ) BETWEEN '<start_time>' AND '<end_time>'
#             AND ci = '<given_ci>;
#     - If the user says "last N days", calculate the start time as NOW() - INTERVAL 'N days' and use NOW() as the end time.

#     - If the user provides a date range, use those dates directly in the BETWEEN clause.

#     - Always sanitize and validate user inputs before injecting them into the query.

#     User's query = {u_prompt}

#     Finally give the sql query as the response, dont add any extra texts, just the sql query.
#     """

#     sql_query = _llm_(prompt)

#     out = sql(sql_query , db_config)
#     return out


def chg_timestamp(query , ci = None , db_config = None):

    current_time = datetime.now()
    time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
    day = current_time.strftime("%A")

    prompt = f"""
    You are a tool for an SQL query generator, and you need to extract start and end timestamps from a sentence that the user gives to you
    - Current time : {time_string}
    - Current day : {day}

    - If the user provides a time frame, parse it with respect to current date and time in 'YYYY-MM-DD HH24:MI:SS' format, and give the timestamps seperated by a pipe symbol '|' .
    Example:
        <start_time>|<end_time>
    do not surround it with any quotes

    - If the user says "last N days/months/hours" etc, calculate the start time as NOW() - INTERVAL 'N days' and use NOW() as the end time.
    - if the user asks for a rough timestamp (around 3 days back / about 4am) , add 1 unit of time (day or hour based on what was asked) before and after specific date/time to account for approximation.
    - make sure if the "last N days/months" is more than an a day, you should include today in the timestamp
    
    - If the user provides a date range, use those dates formatted directly as start and end timestamps.
    - only provide the timestamps, do not give anything else.
    - while calculating timestamp, keep in mind things like months having different number of days, leap years etc.

    User's query = {query}
    """

    timestamp = _llm_(prompt)

    stamps = timestamp.split('|')
    if ci != None:
        query = f"""SELECT chg_id, summary, TO_TIMESTAMP(
                    SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                    'DD-MM-YYYY HH24:MI:SS'
                ) as timestamp FROM change_history_vec WHERE 
                TO_TIMESTAMP(
                    SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                    'DD-MM-YYYY HH24:MI:SS'
                ) BETWEEN '{stamps[0]}' AND '{stamps[1]}'
                AND 
                ci = '{ci}' order by timestamp desc;"""
        out = sql(query,db_config)

    else:
        query = f"""SELECT chg_id, summary, TO_TIMESTAMP(
                    SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                    'DD-MM-YYYY HH24:MI:SS'
                ) as timestamp FROM change_history_vec WHERE 
                TO_TIMESTAMP(
                    SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                    'DD-MM-YYYY HH24:MI:SS'
                ) BETWEEN '{stamps[0]}' AND '{stamps[1]}'
                order by timestamp desc;"""
        out = sql(query,db_config)
    return out


# ---------- ticket ID ---------------------

def _get_chg_id(id , db_config):

    prompt = f"""SELECT chg_id, summary, TO_TIMESTAMP(
                    SUBSTRING(chunk FROM '''sys_created_on'': ''([0-9]{{2}}-[0-9]{{2}}-[0-9]{{4}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}})'''),
                    'DD-MM-YYYY HH24:MI:SS'
                ) as timestamp FROM change_history_vec WHERE chg_id = '{id}';""" 
    out = sql(prompt, db_config)
    return out








# ----------- Knowledge Article Query -------------

def _kb_sql(ci , keystr):
    
    llmout = _llm_(f"""
        you are a keyword extractor with a particular set of strict instructions. You will recieve some details about a system , followed by a description of an event.
        your task is to extract distinct words that have significance to the event.
        1- Extract names and configurations of systems , especially words that are unique and arent common words. Also extract Words that sound like abbreviations or company / software names (office365 , citrix etc). add 1 word in this category that defines the type of event this is (outage , unavailable , degrading etc). This will be category 1
        2- Extract search keywords that are related to the description that may help to search for articles that have useful content. avoid generic terms and do not have more than 6 words. This will be category 2

        Seperate all keywords with a space, but add a pipe symbol "|" between category 1 and category 2.

        Do not add any other text content , since this will be run through regex.
        Prioritize single word keywords.

        Item: "{ci}"
        Description: {keystr} 
        """)
    
    kwlist , supportWords = llmout.split("|")    
    

    stop_words = {'the', 'and', 'then', 'a', 'an', 'in', 'on', 'at', 'of', 'to', 'for', 'by', 'is', 'it','as','AS','Application','Website','Service','article'}

    kwlist = [word for word in kwlist.split() if len(word) >= 2 and word.lower() not in stop_words] + [ci]
    supportWords = [word for word in supportWords.split() if len(word) > 2 and word.lower() not in stop_words]



    matchstr = f"""(CASE WHEN summary ILIKE '%{"%' THEN 4 ELSE 0 END + CASE WHEN summary ILIKE '%".join(kwlist)}%' THEN 3 ELSE 0 END + CASE WHEN summary ILIKE '%{"%' THEN 1 ELSE 0 END + CASE WHEN summary ILIKE '%".join(supportWords)}%' THEN 1 ELSE 0 END)"""
    
    sqlSearch = f"""SELECT knowledge_id, source ,
        {matchstr} AS match_score , summary
    FROM knowledge_vec
    WHERE {matchstr} >= (select max({matchstr}) from knowledge_vec)*0.8
    ORDER BY match_score DESC
    limit 10"""

    return sqlSearch , llmout


def _query_article(question , ci = None , db_config = None  ):
    
    chatlog = "===\n"

    sql_query , llmout = _kb_sql(ci , question)
    chatlog = chatlog.__add__(f"Extracted keywords and search query : {llmout} \n")

    if ci != None:
        outstr = sql(sql_query,db_config)
        chatlog = chatlog.__add__(f"Fetched {outstr}")

    else:
        outstr = "No configuration item provided , cannot search knowledge base"

    

    return outstr , chatlog


def _kb_qa(question , article_text):
    response = _llm_(f"""
    You are a knowledge base question answering bot. You will be given some text from a knowledge base, followed by a question.
    Your task is to read the knowledge text and answer the question as accurately as possible based on.
    If the answer isnt available , say that you dont have the information in your knowledge base, you do not have to make something up.
    if the exact answer is not available BUT there is some very closely related knowledge to it that you thing will be helpful, mention the knowledge base article ONLY if it is relavant.
    give the knowledge id and source of the article if you are mentioning it.
    Keep your answer concise and to the point.
    Do not hallucinate or use online/model data , ONLY stick to article text provided.
                     
    Knowledge base: {article_text}
    
    
    Question: {question}

                     """)
    return response














# ------------- toolstring ---------------

def decide_tool(query):
    prompt = f"""
    Given to you below is a query given to you by a user.
    Query: {query}

    Your task is to pick from a set of tools and parameters to give them.
    Tools given to you:

    'get_data': This will read database for incidents , tickets or changes
        parameters:
            dataset - should be a 1 word string of either "incident" , "ticket" or "change"
            timeframe(option 1) - should be a short string that has a phrase about what timeframe is expected for example "last week" , "3 days ago" , "last tuesday" , "latest"
            id(option 2) - ID of a change , ticket or incident. incident/tickets will start with INC , change with CHG
            ci (optional) - If there is a particular system mentioned, add that as a string
    note that for 'get_data' function, either timeframe or id MUST be present. if none can be extracted , block it.

    'query_article' : this tool will read transcripts , manuals , articles , webpages , Knowledge articles and documents that are there in the database. If the user asks for details WITHOUT any incident ID or Change ID , Default to this. Do not use it if there are generic , political or unsafe questions asked.
        parameters:
            'question' - this is a string that has the actual question that is asked for by the user, pass the entire query here
            'ci' - (optional) - if there is a particular system mentioned, add that as a string
            'isQuestion' - set True if the user is asking a direct question , set false if the user is only asking for knowledge articles. always default this to false if unsure.


    If the given query is irrelavant or does not follow any of the given tool formats , return:
    {{
    "tool" : "blocked",
    "parameters" : {{
        "reason": short description about why the given query is blocked
    }}
    }}
    That blocking of responses json should be returned for these cases: if the user asks for a root cause , reasoning , any "why" questions , generic questions , details of logs or analytics.


    STRICT OUTPUT RULES: 
    - Return ONLY the raw JSON object, nothing else
    - ALL keys must have double quotes. eg: "tool" and not tool
    - ALL string must have double quotes. eg "get_data" and not get_data
    - NO single quotes anywhere
    - NO markdown, NO codefences like ```json
    - NO explanation text befor or after
    - NO newlines and return compact single line json
    
    Example of CORRECT OUTPUT:
    {{
        "tool": "get_data",
        "parameters":{{
            "dataset": "ticket",
            "timeframe": "last week"
        }}
    }}

    {{
    "tool": "query_article",
        "parameters": {{
            "question": "Getting Relevant Knowledge articles: Configuration item Ground Crew Application AS has been raised with the issue Agresso Not Working. Facing issues",
            "ci": "Ground Crew Application AS",
            "isQuestion": false
        }}
    }}

    Only call a single tool. If multiple tools are requested, only return the last one. Do not add 'json' before or any other formatting. only curly braces and plain text
    """

    tooljson = _llm_(prompt)

    #tooljson cleanup incase of non compatible formats

    #strip markdown fences
    # tooljson = re.sub(r'```json|```','',tooljson).strip()

    # #extract only json if extra text is present

    # match = re.search(r'\{.*\}',tooljson,re.DOTALL)
    # if match:
    #     tooljson= match.group(0)
    
    # #fix unquoted keys

    # tooljson= re.sub(r'([{,\s])(\w+)(\s*):',r'\1"\2"\3:', tooljson)

    # #fix single quote 

    # tooljson = re.sub(r"'([^']*)'", r'"\1"', tooljson)

    # # if double quoted twice

    # tooljson = re.sub(r'""(\w+)""', r'"\1"', tooljson)



    try:
        toolstr = json.loads(tooljson)
    except:

        toolstr = f"invalid toolstring: \n{tooljson}"

    return tooljson, toolstr








#===============================================================
# ======================== Main Call ===========================

def call(query , cfg = None , db_config = None):
    chatlog = "==chat call==\n"
    tooljson, toolstr = decide_tool(query)
    chatlog = chatlog.__add__(f"Decided tool : {toolstr} \n")
    chatlog = chatlog.__add__(f"LLM Json : {tooljson} \n")
    content_list = []
    outstr = ""
    try:
        # ---- irrelavant or unnecessay query ---------
        if toolstr["tool"] == 'blocked':
            outstr = _llm_(f"""
                        You are an llm chatbot that helps with getting details about incidents and changes that happen in software. In certain cases, you may get junk queries that are not meant to be answered. This is one of those queries:
                        Query : {query}
                        Reason for Blocking this response: {toolstr['parameters']['reason']}

                            write a kind single sentence output for why this query was blocked , but dont directly mention the internal reason word to word
    """)

        # ---- Asking for data about ticket or change
        if toolstr['tool'] == 'get_data':

            #------ Asking for Incident -----
            if toolstr['parameters']['dataset'] == 'ticket' or toolstr['parameters']['dataset'] == 'incident':
                if 'id' in toolstr['parameters']:
                    chatlog = chatlog.__add__(f"Fetching incident details for id : {toolstr['parameters']['id']} \n")
                    out = _get_inc_id(toolstr['parameters']['id'] , db_config = db_config )
                    chatlog = chatlog.__add__(str(out))

                elif 'timeframe' in toolstr['parameters']:
                    chatlog = chatlog.__add__(f"Fetching incident details for Timeframe : {toolstr['parameters']['timeframe']} \n")
                    if 'ci' in toolstr['parameters']:
                        out , outlog = inc_timestamp(toolstr['parameters']['timeframe'] , toolstr['parameters']['ci'] , db_config = db_config)
                    else:
                        out , outlog = inc_timestamp(toolstr['parameters']['timeframe'] , cfg, db_config = db_config)
                    chatlog = chatlog.__add__(outlog)


            outstr = ""
            #------ Asking for Change -----
            # elif toolstr['parameters']['dataset'] == 'change':
            #     out = chg_timestamp(query , db_config)
            if toolstr['parameters']['dataset'] == 'change':
                if 'id' in toolstr['parameters']:
                    out = _get_chg_id(toolstr['parameters']['id'] , db_config = db_config )
                    chatlog = chatlog.__add__(f"Fetching change details for id : {toolstr['parameters']['id']} \n")

                elif 'timeframe' in toolstr['parameters']:
                    chatlog = chatlog.__add__(f"Fetching change details for Timeframe : {toolstr['parameters']['timeframe']} \n")
                    if 'ci' in toolstr['parameters']:
                        out = chg_timestamp(toolstr['parameters']['timeframe'] , toolstr['parameters']['ci'] , db_config = db_config)
                        chatlog = chatlog.__add__(f"Fetching incident details for CI : {toolstr['parameters']['ci']} \n")
                    else:
                        out = chg_timestamp(toolstr['parameters']['timeframe'] , cfg, db_config = db_config)


            # --- return the ticket/change data ---
            
            if out.__len__() == 0: # no details found
                outstr = f"No {toolstr['parameters']['dataset']} details"
                if 'id' in toolstr['parameters']: outstr = outstr.__add__(f" of {toolstr['parameters']['id']} ")
                elif 'timeframe' in toolstr['parameters']: 
                    outstr = outstr.__add__(f" from {toolstr['parameters']['timeframe']} ")
                if 'ci' in toolstr['parameters']:
                    outstr = outstr.__add__(f" in {toolstr['parameters']['ci']} ")
                else:
                    outstr = outstr.__add__(f" in {cfg} ")


            else: # details found
                outstr = f"Here are {toolstr['parameters']['dataset']} details"
                if 'id' in toolstr['parameters']: outstr = outstr.__add__(f" of {toolstr['parameters']['id']}\n")
                elif 'timeframe' in toolstr['parameters']: 
                    outstr = outstr.__add__(f" from {toolstr['parameters']['timeframe']}\n")
                if 'ci' in toolstr['parameters']:
                    outstr = outstr.__add__(f" in {toolstr['parameters']['ci']} ")
                else:
                    outstr = outstr.__add__(f" in {cfg} ")

            if out.__len__() > 10:
                outstr = outstr.__add__(f"\nNote: {out.__len__()-10} other results found, showing only latest 10 results.\n")
                out = out[0:10]
            for item in out:
                _content = {
                    "id": item[0],
                    "summary": item[1],
                    "time": item[2].strftime(" %H:%M:%S , %d-%m-%Y")
                }
                content_list.append(_content)


        # ---- Asking for Knowledge Articles

        if toolstr['tool'] == 'query_article':
            if 'ci' not in toolstr['parameters']:
                toolstr['parameters']['ci'] = cfg
            out , chatlog = _query_article(toolstr['parameters']['question'] , toolstr['parameters']['ci'] , db_config = db_config )
            
            if out.__len__() == 0:
                outstr = "No relevant knowledge articles found for the given query."
            else:
                if toolstr['parameters']['isQuestion']:
                    outstr = "Here are some knowledge articles that may help answer your question:\n"
                else:
                    outstr = "Here are some relevant knowledge articles:\n"

            for item in out:
                _content = {
                    "id": item[0],
                    "source": item[1],
                    "match_score": item[2],
                    "summary": item[3]
                }
            outstr = outstr.__add__(f"----------\nArticle ID: {item[0]} , From {item[1]} \nSummary: {item[3]}\n\n")
            


            if toolstr['parameters']['isQuestion']:
                try:
                    chatlog = chatlog.__add__(f"Answering question based on articles fetched {outstr}\n")
                    outstr = _kb_qa(toolstr['parameters']['question'],outstr)
                    outstr = outstr.__add__(f"\nnote: Question answering by llms may not be accurate\n")
                except:
                    pass
            content_list = []
    except Exception as e:
        outstr = f"Error occured while processing the query, Please contact an admin with the message '{e} \nDecided tool : {toolstr} \nLLM json : {tooljson}\n"
        content_list = []
        chatlog = traceback.format_exc()
    return outstr , content_list , chatlog
