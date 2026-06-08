#variable "name"{
#    type        = string
#	description = "Security group Name"
#	default     = ""
#}
#
#variable "vpc_id"{
#    type        = string
#	description = "VPC ID to create Security Group"
#	default     = ""
#}
#
#variable "tags"{
#    type        = map
#	description = "Security Group Tags"
#	default     = {}
#}


variable "security_group_id"{
    type        = string
	description = "VPC ID to create Security Group"
	default     = ""
}


variable "sg_rule_details" {
    type = map
   description = "Security group rule: ingress or egress"
   default = {}
}   



variable "source_sg_default"{
    type        = string
	description = "VPC ID to create Security Group"
	default     = null
}

