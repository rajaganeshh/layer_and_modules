variable "filename" {
  description = "Path to local ZIP file for Lambda deployment"
  type        = string
  default     = ""
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = ""
}



variable "description" {
  description = "Description of the Lambda function"
  type        = string
  default     = ""
}

variable "memory_size" {
  description = "Amount of memory in MB"
  type        = number
  default     = 128
}

variable "handler" {
  description = "Lambda handler (for ZIP/S3)"
  type        = string
  default     = ""
}

variable "role_arn" {
  description = "IAM role ARN for Lambda"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime (for ZIP/S3)"
  type        = string
  default     = "python3.8"
}

variable "architectures" {
  description = "Lambda architectures"
  type        = list(string)
  default     = ["x86_64"]
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 3
}

variable "common_tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "publish_version" {
  description = "Whether to publish a new version"
  type        = bool
  default     = false
}

variable "lambda_rollback" {
  description = "Enable rollback for Lambda"
  type        = bool
  default     = false
}

variable "reserved_concurrency" {
  description = "Reserved concurrency for Lambda"
  type        = number
  default     = -1
}

variable "vpc_subnet_ids" {
  description = "List of VPC subnet IDs"
  type        = list(string)
  default     = null
}

variable "vpc_security_group_ids" {
  description = "List of VPC security group IDs"
  type        = list(string)
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for VPC config"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for VPC config"
  type        = list(string)
  default     = []
}

variable "env_vars" {
  description = "Environment variables for Lambda"
  type        = map(string)
  default     = {}
}

variable "tracing_mode" {
  description = "X-Ray tracing mode"
  type        = string
  default     = null
}

variable "logging_log_format" {
  description = "Log format. Valid values: Text, JSON."
  type        = string
  default     = null
}

variable "logging_log_group" {
  description = "Log group for Lambda logging"
  type        = string
  default     = null
}

variable "logging_application_log_level" {
  description = "Detail level of application logs. Valid values: TRACE, DEBUG, INFO, WARN, ERROR, FATAL."
  type        = string
  default     = null
}

variable "logging_system_log_level" {
  description = "Detail level of Lambda platform logs. Valid values: DEBUG, INFO, WARN."
  type        = string
  default     = null
}

variable "lambda_dlq_arn" {
  description = "ARN for Lambda dead letter queue"
  type        = string
  default     = ""
}

variable "timeouts" {
  description = "Timeouts for Lambda resource operations"
  type        = map(any)
  default     = {}
}

variable "layers" {
  description = "List of Lambda layer ARNs"
  type        = list(string)
  default     = []
}

variable "s3_bucket" {
  description = "S3 bucket for Lambda code"
  type        = string
  default     = ""
}

variable "s3_key" {
  description = "S3 key for Lambda code"
  type        = string
  default     = ""
}

variable "s3_object_version" {
  description = "S3 object version for Lambda code"
  type        = string
  default     = ""
}

variable "s3_source_code_hash" {
  description = "Source code hash for S3 object"
  type        = string
  default     = ""
}

variable "image_uri" {
  description = "URI of Docker image for Lambda"
  type        = string
  default     = ""
}

variable "lambda_layers" {
  description = "Path to the ZIP file for the Lambda layer"
  type        = map(any)
  default     = {}
}


variable "lambda_resource_policy" {
  description = "resource based policy variable map"
  type        = map(any)
  default     = {}
}

