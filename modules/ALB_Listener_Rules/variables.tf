variable "lb_listener_arn" {
  type        = string
  description = "the name of the load balancer"
  default = ""
}

variable "host_forward" {
  type    = bool
  default = false
}

variable "host_redirect" {
  type    = bool
  default = false
}

variable "host_path" {
  type    = bool
  default = false
}

variable "service_host_header" {
  description = "The subnets for the Loadbalancer"
  type = list(string)
  default     = []
}



variable "service_host_redirect" {
  description = "The subnets for the Loadbalancer"
  type        = string
  default     = ""
}

 
variable "priority" {
  description = "The subnets for the Loadbalancer"
  type        = number
  default     = null
}


variable "target_group_arn" {
  type    = string
  description = "Application LB type Enable"
  default  = ""
}

variable "target_group_arn_weight" {
  type    = number
  description = "Application LB type Enable"
  default  = 100
}


variable "target_group_arn_green" {
  type    = string
  description = "Application LB type Enable"
  default  = ""
}


variable "target_group_arn_green_weight" {
  type    = number
  description = "Application LB type Enable"
  default  = null
}

variable "service_path_pattern" {
 type = list(string)
  description = "Alb rules for the listener"
  default = []
}

variable "lb_sticky_duration" {
 type = number
  description = "Alb rules for the listener"
  default = 86400
}

variable "lb_sticky_enabled" {
  type    = bool
  description = "Alb stickiness enabled or disabled"
  default = false
}

variable "static_action" {
  type    = bool
  description = "Alb stickiness enabled or disabled"
  default = false
}


variable "common_tags" {
  type        = map(any)
  description = "Common tags for resources"
  default = {}
}
