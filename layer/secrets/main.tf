locals {
    common_tags = merge(var.tags, { CostOwnerTeam = var.CostOwnerTeam, SupportTeam = var.SupportTeam[var.env_type] })
    node_secret_json = jsondecode(
      replace(
        replace(data.template_file.node_secret.rendered, "\n", ""),
        "\t", ""
      )
    )
}



resource "random_password" "db_password" {
  length  = 16
  special = true
  override_special = "!#$%^&*()-_=+[]{}<>?:"
}

module "multiple_secret" {
  for_each = var.secrets #local.secrets

  providers = {
    aws = aws.ai_stack
  }

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/Secret?ref=main"

  secret = {
    name       = each.key
    kms_key_id = ""
    secret_key_value = merge(
      { username = each.value["${var.env_type}_username"] },
      { password = random_password.db_password.result },
      { engine = each.value.engine },
      { dbname = each.value.dbname },
      { host = var.env_type == "PROD" ? "app-app-auroradb.mim.company-domain.net" : "app-app-auroradb.mimdev.company-domain.net" },
    { port = each.value.port })
  }

  common_tags = merge(local.common_tags,
  { Name = each.key })
}


module "multiple_secret_node" {
  
  providers = {
    aws = aws.ai_stack
  }
  source = "git@github.com:company-org/company-name-iac-modules.git//Source/Secret?ref=main"
  secret = {
    name       = "company-name-${lower(var.env_type)}-node-secret"
    kms_key_id = ""
    secret_key_value = {
      nodeSecrets = replace(
        replace(data.template_file.node_secret.rendered, "\n", ""),
        "\t", ""
      )
    }
  }
  common_tags = merge(local.common_tags, { Name = "company-name-${var.env_type}-node-secret" })
}

module "multiple_secret_lambda" {
  
  providers = {
    aws = aws.ai_stack
  }
  source = "git@github.com:company-org/company-name-iac-modules.git//Source/Secret?ref=main"
  secret = {
    name       = "company-name-${lower(var.env_type)}-lambda-secret"
    kms_key_id = ""
    secret_key_value = {
      configPythonSecrets = replace(
        replace(data.template_file.lambda_secret.rendered, "\n", ""),
        "\t", ""
      )
    }
  }
  common_tags = merge(local.common_tags, { Name = "company-name-${var.env_type}-lambda-secret" })
}