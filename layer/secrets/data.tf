# Declare the data source
#data "aws_vpc_endpoint" "s3" {
#  provider = aws.ai_stack
  
#  filter {
#    name   = "vpc-id"
#    values = data.aws_vpc.main.id
#  }

 # filter {
 #   name   = "service-name"
 #   values = ["com.amazonaws.${var.region}.s3"]
 # }
#}

data "aws_secretsmanager_secret" "db_password" {
  provider = aws.ai_stack
  name = "/SIMON/auroradb"
}


data "aws_secretsmanager_secret_version" "db_password" {
  provider = aws.ai_stack
  secret_id = data.aws_secretsmanager_secret.db_password.id
}

locals {
  db_host     = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["host"]
  db_username = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["username"]
  db_password = sensitive(jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"])
}


data "template_file" "lambda_secret" {
  template = file("${path.module}/policies/lambda_secrets.tpl")
  vars = {
    bedrock_name        = "arn:aws:bedrock:${var.region}:${var.aws_account_id}:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
    bedrock_embeddings  = var.bedrock_embeddings
    sn_client           = base64decode(lookup(var.servicenow_clientid,terraform.workspace))
    sn_secret           = base64decode(lookup(var.servicenow_secret,terraform.workspace))
    sn_baseurl          = base64decode(lookup(var.servicenow_baseurl,terraform.workspace))
    sn_tokenurl         = base64decode(lookup(var.servicenow_tokenurl,terraform.workspace))
    sp_client           = base64decode(lookup(var.servicenow_clientid,terraform.workspace))
    sp_secret           = base64decode(lookup(var.servicenow_secret,terraform.workspace))
    sp_baseurl          = base64decode(lookup(var.servicenow_baseurl,terraform.workspace))
    sp_tokenurl         = base64decode(lookup(var.servicenow_tokenurl,terraform.workspace))
    cf_user             = var.confluence_user
    cf_token            = base64decode(var.confluence_token)
    cf_url              = base64decode(var.confluence_url)
    db_host             = local.db_host
    db_user             = local.db_username
    db_pass             = local.db_password
    region              = var.region
    s3_bucket           = "${var.source_market}-${lower(terraform.workspace)}-simon-bucket"
  }
}


data "template_file" "node_secret" {
  template = file("${path.module}/policies/node_secrets.tpl")
  vars = {
    domain              = var.env_type == "PROD" ? "mim" : "mimdev"
    db_host             = local.db_host
    db_user             = local.db_username
    db_pass             = local.db_password
    office_clientid     = base64decode(lookup(var.office_client_id,terraform.workspace))
    office_secretid     = base64decode(lookup(var.office_secret_id,terraform.workspace))
    office_tokenid      = base64decode(lookup(var.office_token_id,terraform.workspace))
    interface_user      = lookup(var.interface_user,terraform.workspace)
    interface_pass      = base64decode(lookup(var.interface_pass,terraform.workspace))
    vpc_endpoint        =  base64decode(lookup(var.vpc_endpoint_id, terraform.workspace))
    s3_bucket           = "${var.source_market}-${lower(terraform.workspace)}-simon-bucket"
  }
}
