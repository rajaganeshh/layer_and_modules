variable "tg_name" {
  type        = string
  description = "the name of the target_group"
  default     = ""
}

variable "tg_port" {
  type        = number
  description = "the target group port"
  default     = null
}

variable "tg_protocol" {
  description = "The target group protocol"
  type        = string
  default     = ""
}

variable "hc_protocol" {
  description = "The target group protocol"
  type        = string
  default     = null
}

variable "vpc_id" {
  description = "The vpc id"
  type        = string
  default     = ""
}

variable "tg_healthy_threshold" {
  description = "The target group health check threshold"
  type        = number
  default     = null
}

variable "tg_unhealthy_threshold" {
  description = "The target group health check unhealthy threshold"
  type        = number
  default     = null
}

variable "tg_path" {
  description = "The target group health check path"
  type        = string
  default     = null
}

variable "target_type" {
  description = "The target group target type"
  type        = string
  default     = "instance"
}

variable "tg_sticky_type" {
  description = "The target group sticky type"
  type        = string
  default     = ""
}

variable "tg_sticky_enabled" {
  description = "The target group sticky enabled"
  type        = bool
  default     = false
}

variable "tg_sticky_duration" {
  description = "The target group sticky duration"
  type        = number
  default     = 86400
}

variable "common_tags" {
  description = "Name tag for NLB resources"
  type        = map
  default     = {}
}


variable "tg_health_interval" {
  description = " (Optional) Approximate amount of time, in seconds, between health checks of an individual target. The range is 5-300."
  type        = number
  default     = null
}

variable "tg_preserve_client_ip" {
  description = " (Optional) Whether client IP preservation is enabled."
  type        = string
  default     = null
}

variable "tg_health_timeout" {
  description = "(optional) Amount of time, in seconds, during which no response from a target means a failed health check. The range is 2–120 seconds. For target groups with a protocol of HTTP, the default is 6 seconds. For target groups with a protocol of TCP, TLS or HTTPS, the default is 10 seconds"
  type        = number
  default     = null
}

variable "deregistration_delay" {
  description = "(Optional) Provides De-registration delay in seconds max 3600"
  type        = number
  default     = 300
}

variable "tg_matcher" {
  description = "The target group matcher"
  type        = string
  default     = "200"
}

variable "tg_slow_start" {
  type        = number
  description = "(Optional) Amount time for targets to warm up before the load balancer sends them a full share of requests. The range is 30-900 seconds or 0 to disable. The default value is 0 seconds."
  default     = null
}