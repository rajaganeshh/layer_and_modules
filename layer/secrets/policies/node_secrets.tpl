{
    "port": "80",
    "app": {
		"interface_url": "https://app-app.${domain}.company-domain.net/interface",
		"BASE_URL": "https://app-app.${domain}.company-domain.net/backend",
        "origin": [
            "http://localhost"
        ]
    },
    "allowedMethods": [
        "GET",
        "POST"
    ],
    "csrfTokenSecret": "EASYJET-CSRF-TOKEN",
    "errorStack": [
        "local"
    ],
    "cookie": {
        "domain": "app-app.${domain}.company-domain.net",
        "httpOnly": true,
        "secure": true,
        "sameSite": "Strict",
        "tokenLife": 3600,
        "refreshTokenLife": 2000,
        "accessTokenLife": 1000,
        "csrfCookieName": "__localhost.x-csrf-token",
        "csrfCookie": "x-csrf-token",
        "path": "/middleware"
    },
    "database": {
        "host": "${db_host}",
        "user": "${db_user}",
        "password": "${db_pass}",
        "database": "database1",
        "port": 5432,
        "schema": "public"
    },
    "officeCredentials": {
        "clientId": "${office_clientid}",
        "clientSecret": "${office_secretid}",
        "tenantId": "${office_tokenid}",
        "groupId" : "",
        "tokenPath": "/oauth2/v2.0/token",
        "authorizePath": "/oauth2/v2.0/authorize",
        "apiendpoint": "https://graph.microsoft.com",
        "endpoint": "https://login.microsoftonline.com/",
        "scopes": [
            "https://graph.microsoft.com/.default",
            "offline_access"
        ],
        "scope": "https://graph.microsoft.com/.default",
        "users": "/v1.0/users/",
        "userProfile": "/v1.0/me",
        "redirecturi": "https://app-app.${domain}.company-domain.net/login"
    },
    "interfaceEndpoint": {
        "username": "${interface_user}",
        "password": "${interface_pass}"
    },
    "s3": {
        "bucket": "${s3_bucket}",
        "endpoint": "${vpc_endpoint}",
        "prefix": "middleware-logs"
    },
	"pythonApi": {
		"getAllIncident": "/getAllIncidents",
		"getIncident": "/getIncident",
		"updateWorknote": "/updateWorknote",
		"refreshWorkNote": "/refreshIncident",
		"chatBot": "/chatbot"
	}	
}
