variable "role_name" {
  type        = string
  description = "Name of the IAM role"
}

variable "assume_role_policy" {
  type        = string
  description = "assume ploicy for the role"
  default     = ""
}

variable "instance_profile_enabled" {
  type        = bool
  description = "create the instance profile"
  default     = false
}


variable "policy_attach_role"{
	description = "Number of Policies to be attached" 
	default = []
    type = list(string)
}


variable "iam_policy"{
	description = "Number of Policies to be attached" 
	default = {}
    type = map
}

variable "max_session_duration" {
  type        = number
  description = "Maximum session duration (in seconds) that you want to set for the specified role. If you do not specify a value for this setting, the default maximum of one hour is applied. This setting can have a value from 1 hour to 12 hours"
  default 	  = 3600	
}


variable "common_tags"{
	description = "Number of Policies to be attached" 
	default = {}
    type = map
}
