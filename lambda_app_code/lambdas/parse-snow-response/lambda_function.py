import json
import os
from botocore.exceptions import ClientError
import urllib3
from urllib3.util import make_headers
import boto3

secret_name = os.environ.get("secret_name", "")
region_name_env = os.environ.get("region_name", "")


def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print("Unable to fetch secret")
        raise e
    secret = json.loads(get_secret_value_response["SecretString"])
    configPythonSecrets = json.loads(secret["configPythonSecrets"])
    return configPythonSecrets

configPythonSecrets = get_secret(secret_name, region_name_env)

# ----------------- Extract secrets -----------------
region_name = configPythonSecrets["awsRegion"]


# mim Base URL
mim_base_url = configPythonSecrets["baseUrl"]
interface_user = configPythonSecrets['interfaceEndpoint']['username']
interface_pwd = configPythonSecrets['interfaceEndpoint']['password']

http = urllib3.PoolManager()

def lambda_handler(event, context):
    """
    Parse API Gateway response and extract only request_body information
   
    Args:
        event: The Lambda event containing API Gateway response (or empty for testing)
        context: Lambda context object
   
    Returns:
        Parsed request_body data only
    """
   
    try:
        # Hardcoded API Gateway response for testing
        # Replace this with actual event when integrating with Kong
        if not event or event == {}:
            print("Using hardcoded API Gateway response for testing")
            aws_api_response = {}
        else:
            # Parse incoming event from Kong
            print("Processing API Gateway response from event")
           
            # Case 1: Event is the Kong response dict directly
            if isinstance(event, dict) and 'request_body' in event:
                aws_api_response = event
                print("Event is Kong response dict")
           
            # Case 2: Event has 'body' key (API Gateway integration)
            elif isinstance(event, dict) and 'body' in event:
                body_content = event['body']
                print(f"Event has body key, type: {type(body_content)}")
               
                if isinstance(body_content, str):
                    aws_api_response = json.loads(body_content)
                else:
                    aws_api_response = body_content
           
            # Case 3: Event itself is a JSON string
            elif isinstance(event, str):
                print("Event is a string")
                aws_api_response = json.loads(event)
           
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Unable to parse event',
                        'event_type': str(type(event)),
                        'event_keys': list(event.keys()) if isinstance(event, dict) else 'Not a dict'
                    })
                }
       
        # Extract request_body from Kong response
        if not aws_api_response or 'request_body' not in aws_api_response:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'request_body not found in Kong response',
                    'available_keys': list(aws_api_response.keys()) if aws_api_response else 'None'})
              }
       
        request_body_str = aws_api_response['request_body']
        print(f"request_body type: {type(request_body_str)}")
        print(f"request_body value: {request_body_str[:100]}...")  # Print first 100 chars
       
        # Parse request_body if it's a string
        if isinstance(request_body_str, str):  
            request_body_data = json.loads(request_body_str)
        elif isinstance(request_body_str, dict):
            request_body_data = request_body_str
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'request_body is not a valid type',
                    'type': str(type(request_body_str))
                })
            }
       

        # Return only the request_body data
        url = f'{mim_base_url}/interface/newIncident'
   
        username = interface_user
        password = interface_pwd
        headers = make_headers(basic_auth=f'{username}:{password}')
        headers['Content-Type'] = 'application/json'
 
        print(f'Parsed request_body: {request_body_data}')
        response = http.request(
                method='POST',
                url=url,
                headers=headers,
                body=json.dumps(request_body_data) # send proper JSON
            )
 
 
        print(f'Result - {response.data.decode('utf-8')}')
       
        return {
            'statusCode': 200,
            'body': json.dumps({
                'request_body': response.data.decode('utf-8')
            })
        }
   
    except Exception as e:
        print(f'HTTP request failed: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }