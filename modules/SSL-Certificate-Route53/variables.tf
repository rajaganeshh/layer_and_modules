variable "domain_name" {
  type = string
  description = "domain name for the certificate"
}

variable "tags" {
  type        = map
}

variable "route53_zone_name" {
  type = string
}

variable "route53_private_zone" {
  type    = bool
  default = false
  description = "Indicates whether this is a private hosted zone"
}