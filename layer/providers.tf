# Below provider is to create resources in the release engineering accounts

provider "aws" {
  alias               = "ai_stack"
  region              = var.region
  allowed_account_ids = [var.aws_account_id]

  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.stack_account_role}"
  }

  default_tags {
    tags = local.default_tags

  }
  ignore_tags {
    keys = [
      "map-migrated"
    ]
  }
}



provider "aws" {
  alias               = "ai_stack_dns_zone"
  region              = "us-east-1"
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = local.default_tags
  }

  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.stack_account_role}"
  }
}


provider "null" {
}


