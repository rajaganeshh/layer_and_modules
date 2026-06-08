{
	"bedrock": {
		"llm": "${bedrock_name}",
		"embedding": "${bedrock_embeddings}",
		"key": ""
	},
	"serviceNow": {
		"clientId": "${sn_client}",
		"clientSecret": "${sn_secret}",
		"baseUrl": "${sn_baseurl}",
		"tokenUrl": "${sn_tokenurl}"
	},
	"confluence": {
		"user": "${cf_user}",
		"token": "${cf_token}",
		"url": "${cf_url}"
	},
	"sharePoint": {
		"clientId": "${sp_client}",
		"clientSecret": "${sp_secret}",
		"baseUrl": "${sp_baseurl}",
		"tokenUrl": "${sp_tokenurl}"
	},
	"database": {
		"host": "${db_host}",
		"user": "${db_user}",
		"password": "${db_pass}",
		"name": "database1",
		"schema": "public",
		"port": 5432
	},
	"lambdaLog": {
		"bucket": "${s3_bucket}",
		"prefix": "lambda-logs"
	},
	"interfaceLog": {
		"bucket": "${s3_bucket}",
		"prefix": "interface-logs"
	},
	"pythonBackendLog": {
		"bucket": "${s3_bucket}",
		"prefix": "interface-logs"
	},
	"awsRegion": "${region}"
}