terraform {

  required_providers {
    aws      = ">= 5.4.0"
    dns      = "~> 3.1.0"
    template = "~> 2.2"
    null = {
      source  = "hashicorp/null"
      version = "3.2.2"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.0"
    }
  }

 backend "s3" {
   bucket         = ""
   region         = ""
   encrypt        = true
   dynamodb_table = ""
 }

  required_version = ">= 0.15"
}

