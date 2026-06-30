terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
	  configuration_aliases = [aws.dnszone]
    }
    template = {
      source = "hashicorp/template"
    }
  }
  required_version = ">= 0.13"
}