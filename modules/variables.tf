variable "lb_name" {
  type        = string
  description = "(Optional) The name of the LB. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric characters or hyphens, and must not begin or end with a hyphen. If not specified, Terraform will autogenerate a name beginning with tf-lb."
  default     = ""
}

variable "lb_type" {
  type        = string
  description = "(Optional) The type of load balancer to create. Possible values are application, gateway, or network. The default value is application."
  default     = "application"

  validation {
    condition     = contains(["application", "gateway", "network"], var.lb_type)
    error_message = "lb_type must be one of 'application', 'gateway', or 'network'."
  }
}

variable "idle_timeout" {
  type        = string
  description = "(Optional) Time in seconds that the connection is allowed to be idle."
  default     = "60"
}

variable "lb_subnet_ids" {
  description = "The subnets for the Loadbalancer"
  type        = set(string)
  default     = [""]
}

variable "enable_deletion_protection" {
  type        = bool
  description = "Application LB deletion protection"
  default     = false
}

variable "lb_security_groups" {
  description = "The subnets for the Loadbalancer"
  type        = set(string)
  default     = [""]
}


variable "lb_internal" {
  type        = bool
  description = "(Optional) If true, the LB will be internal"
  default     = true
}

variable "common_tags" {
  type        = map(any)
  description = "Common tags for resources"
  default     = {}
}


variable "add_port_80_listener" {
  description = "(Optional) Whether to add a listener on port 80 with a fixed response action that returns a 404 status code."
  type        = bool
  default     = false
}

variable "add_port_443_listener" {
  description = "(Optional) Whether to add a listener on port 443 with a fixed response action that returns a 404 status code."
  type    = bool
  default = false
}

variable "add_port_4431_listener" {
  description = "(Optional) Whether to add a listener on port 4431 with a fixed response action that returns a 404 status code."
  type        = bool
  default     = false
}

variable "route53_zone_name" {
  description = "The DNS zone in which to create the ALB DNS records"
  type        = string
  default     = ""
}

variable "lb_dns_name" {
  description = "The DNS name to use for the ALB. This will be used as the prefix together with lb_dns_entry for the DNS record created in the specified Route53 zone. For example, if you specify 'my-alb' and your Route53 zone is 'example.com', the resulting DNS record will be 'my-alb.example.com'."
  type        = string
  default     = ""
}


variable "lb_dns_entry" {
  description = "List of DNS entry to use for the ALB. This will be used together with lb_dns_name for the DNS record created in the specified Route53 zone. For example, if you specify 'preprod', and your lb_dns_entry is '.my-alb', and your Route53 zone is 'example.com', the resulting DNS record will be 'preprodmy-alb.example.com'."
  type        = set(string)
  default     = []
}


variable "certificate_arn" {
  description = "ARN of the SSL certificate to use for the HTTPS listener on port 443 and 4431"
  type    = string
  default = ""
}

variable "additional_certificate_arn" {
  description = "List of ARNs of additional SSL certificates to use for the HTTPS listener on port 443 only. This allows you to associate multiple certificates with the same listener, which can be useful for hosting multiple domains on the same load balancer."
  type    = list(string)
  default = []
}
