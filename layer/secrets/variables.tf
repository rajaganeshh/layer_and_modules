variable "bedrock_name" {
  description = "Bedrock LLM name"
  type        = string
  default     = "anthropic.claude-3-7-sonnet-20250219-v1:0"
}

variable "bedrock_embeddings" {
  description = "Bedrock LLM name"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "vpc_endpoint_id" {
  description = "VPC Endpoint id"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}


variable "servicenow_clientid" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "servicenow_secret" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "servicenow_baseurl" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "servicenow_tokenurl" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}


variable "sharepoint_clientid" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = "="
  }  
  sensitive   = true
}

variable "sharepoint_secret" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "sharepoint_baseurl" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "sharepoint_tokenurl" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}


variable "confluence_user" {
  description = "Bedrock LLM name"
  type        = string
  default     = "Github.App@company-name.com"
}

variable "confluence_token" {
  description = "Bedrock LLM name"
  type        = string
  default     = ""
  sensitive   = true
}

variable "confluence_url" {
  description = "Bedrock LLM name"
  type        = string
  default     = ""
  sensitive   = true
}

variable "office_client_id" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "office_secret_id" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = "TH5SOFF+MEdKSXpubk1BeHJ6RzY3MVN2RlRRNG9PZ0lucGJLfmJROAo="
    PROD      = "OGdsOFF+NXRQTUpBZlF0R0hqbTR4eTdpZjdpMmttLW5FTTVia2FkdA=="
  }  
  sensitive   = true
}

variable "office_token_id" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "interface_user" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = ""
  }  
  sensitive   = true
}

variable "interface_pass" {
  description = "Bedrock LLM name"
  type        = map
  default     = {
    DEV       = ""
    PROD      = "="
  }  
  sensitive   = true
}
