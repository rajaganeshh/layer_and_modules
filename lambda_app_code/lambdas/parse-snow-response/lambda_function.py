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
    Forward the parsed ServiceNow incident payload to the newIncident interface endpoint.
    """
    try:
        print(f"Received event: {json.dumps(event)}")

        request_body_data = event

        url = f'{mim_base_url}/interface/newIncident'
        headers = make_headers(basic_auth=f'{interface_user}:{interface_pwd}')
        headers['Content-Type'] = 'application/json'

        print(f'Forwarding payload: {json.dumps(request_body_data)}')
        # response = http.request(
        #     method='POST',
        #     url=url,
        #     headers=headers,
        #     body=json.dumps(request_body_data)
        # )

        # result = response.data.decode('utf-8')
        # print(f'Result - {result}')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'request_body': request_body_data
            })
        }

    except Exception as e:
        print(f'HTTP request failed: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }