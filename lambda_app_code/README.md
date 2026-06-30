# simon_agentic_ai_lambda
S.I.M.O.N agentic AI Lambda function


| Github Folder Map name  | Lambda function name                   | Description                                                                 
|-------------------------|----------------------------------------|-----------------------------------------------------------------------------
| scheduled-ticket        | ej-<env>-snow-incident-sync-rds-daily  | Once in a Day ServiceNow all tickets incidents details will be processed and updated in AuroraRDS 
| scheduled-change        | ej-<env>-snow-cr-sync-rds-daily        | Once in a Day ServiceNow all Change Requests details will be processed and updated in AuroraRDS 
| scheduled-knowledge     | ej-<env>-kb-sync-rds-daily             | Once in a Day all KB articles conf, shareppoint, teams details will be processed and updated in AuroraRDS 
| bedrock-ticket          | ej-<env>-snow-p1p2-inc-trigger-bedrock | ServiceNow will trigger the lambda once P1 P2 tickets created               
| bedrock-change          | ej-<env>-snow-p1p2-cr-fetch-bedrock    | Trigger the Change request details collection once P1 P2 tickets created    
| bedrock-knowledge       | ej-<env>-snow-p1p2-kb-trigger-bedrock  | Trigger the KB articles collection once P1 P2 tickets created               
