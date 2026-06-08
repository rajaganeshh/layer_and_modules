
variable "function_name" {
  type = map
  description = "Map of Lambda function names by app type."
  default = {
    scheduled-1630 = "scheduled-1630"
    scheduled-ticket = "snow-incident-sync-rds-daily"
    scheduled-change = "snow-cr-sync-rds-daily"
    scheduled-knowledge = "kb-sync-rds-daily"
    bedrock-ticket = "snow-p1p2-inc-trigger-bedrock"
    bedrock-change = "snow-p1p2-cr-fetch-bedrock"
    bedrock-knowledge = "snow-p1p2-kb-trigger-bedrock"
  }
}

variable "lambda_function_file" {
  type = string
  description = "Map of Lambda function zip file paths by app type."
  default = ""
}

variable "description" {
  type = map
  description = "Map of Lambda function descriptions by app type."
  default = {
    scheduled-1630 = "scheduled-1630 function"
    scheduled-1530 = "scheduled-1530 funtion"
    scheduled-ticket = "Once in a Day ServiceNow all tickets incidents details will be processed and updated in AuroraRDS"
    scheduled-change = "Once in a Day ServiceNow all Change Requests details will be processed and updated in AuroraRDS"
    scheduled-knowledge = "Once in a Day all KB articles conf, shareppoint, teams details will be processed and updated in AuroraRDS"
    bedrock-change = "Trigger the Change request details collection once P1 P2 tickets created"
    bedrock-knowledge = "Trigger the KB articles collection once P1 P2 tickets created"
    bedrock-ticket = "ServiceNow will trigger the lambda once P1 P2 tickets created"
  }
}

variable "memory_size" {
  type = map
  description = "Map of Lambda memory sizes by app type."
  default = {
    scheduled-1630 = 512
    scheduled-ticket = 512
    scheduled-change = 512
    scheduled-knowledge = 512
    bedrock-change = 512
    bedrock-knowledge =  512   
    bedrock-ticket = 512
  }
}

variable "runtime_timeout" {
  type = map
  description = "Map of Lambda memory sizes by app type."
  default = {
    scheduled-1630 = 120
    scheduled-ticket = 120
    scheduled-change = 120
    scheduled-knowledge = 120
    bedrock-change = 60
    bedrock-knowledge =  60   
    bedrock-ticket = 120
  }
}

variable "handler" {
  type = map
  description = "Map of Lambda handler names by app type."
  default = {
    scheduled-1630 = "lambda_function.lambda_handler"
    scheduled-ticket = "lambda_function.lambda_handler"
    scheduled-change = "lambda_function.lambda_handler"
    scheduled-knowledge = "lambda_function.lambda_handler"
    bedrock-change = "lambda_function.lambda_handler"
    bedrock-knowledge = "lambda_function.lambda_handler"
    bedrock-ticket = "lambda_function.lambda_handler"
  }
}


variable "runtime" {
  type = string
  description = "Map of Lambda runtimes by app type."
  default = "python3.13"
}

variable "architectures" {
  type = map
  description = "Map of Lambda architectures by app type."
  default = {
    scheduled-1630 = ["x86_64"]
    scheduled-ticket = ["x86_64"]
    scheduled-change = ["x86_64"]
    scheduled-knowledge = ["x86_64"]
    bedrock-change = ["x86_64"]
    bedrock-knowledge = ["x86_64"]   
    bedrock-ticket = ["x86_64"]
  }  
}

variable "timeouts" {
  type = map
  description = "Map of Lambda timeouts by app type."
  default = {
    scheduled-1630 = { create = "5m", update = "5m", delete = "5m" }
    scheduled-ticket =  { create = "5m", update = "5m", delete = "5m" }
    scheduled-change =  { create = "5m", update = "5m", delete = "5m" }
    scheduled-knowledge =  { create = "5m", update = "5m", delete = "5m" }
    bedrock-change =  { create = "5m", update = "5m", delete = "5m" }
    bedrock-knowledge =  { create = "5m", update = "5m", delete = "5m" }
    bedrock-ticket = { create = "5m", update = "5m", delete = "5m" }
  }
}

variable "lambda_publish" {
  type = string
  description = "Lambda publish/rollback option."
  default = "true"
}

variable "reserved_concurrency" {
  type = map
  description = "Map of reserved concurrency by app type."
  default = {
    scheduled-1630 = 5
    scheduled-ticket = 1
    scheduled-change = 1
    scheduled-knowledge = 1
    bedrock-change = 1
    bedrock-knowledge = 1    
    bedrock-ticket = 1
  }
}

variable "tracing_mode" {
  type = map
  description = "Map of tracing modes by app type."
  default = {
    scheduled-1630 = null
    scheduled-ticket = null
    scheduled-change = null
    scheduled-knowledge = null
    bedrock-change = null
    bedrock-knowledge = null  
    bedrock-ticket = null
  }
}

variable "log_format" {
  type = string
  description = "Log format for Lambda."
  default = "Text"
}

variable "log_level" {
  type = map
  description = "Map of log levels by app type."
  default = {
    scheduled-1630 = "INFO"
    scheduled-ticket = "INFO"
    scheduled-change = "INFO"
    scheduled-knowledge = "INFO"
    bedrock-ticket = "INFO"
    bedrock-change = "INFO"
    bedrock-knowledge = "INFO"   
  }  
}


variable "lambda_layers" {
  type = map
  description = "Map of Lambda timeouts by app type."
  default = {
    psycopg2 = { create = "5m", update = "5m", delete = "5m" }
    aiohttp  = { create = "5m", update = "5m", delete = "5m" }
  }
}
