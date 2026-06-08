# Secrets
variable "secret" {
  description = "Map of secrets to keep in AWS Secrets Manager"
  type        = any
  default     = {}
}


variable "common_tags" {
  description = "Map of secrets to keep in AWS Secrets Manager"
  type        = any
  default     = {}
}