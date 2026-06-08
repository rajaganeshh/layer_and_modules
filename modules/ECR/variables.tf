variable "ecr_repo_name" {
  description = "Name of ECR Repository"
}

variable "mutability" {
  description = "Image Tag Mutability"
}

variable "ecr_repo_policy" {
  description = "The name of the policy document for ECR Repository"
  default     = ""
}

variable "scan_on_push" {
  default     = true
}

variable "ecr_repo_lifecycle_policy" {
  description = "The name of the lifecycle policy document for ECR Repository"
  default     = ""
}

variable "additional_tags" {
  type = map(string)
  description = "(Optional) A map of tags to assign to the resource."
  default = {}
}
