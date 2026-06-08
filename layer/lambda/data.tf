####################  Core    #####################

data "aws_lambda_layer_version" "psycopg2_layer" {
  provider = aws.ai_stack
  layer_name = "psycopg2"
}

data "aws_lambda_layer_version" "aiohttp_layer" {
  provider = aws.ai_stack
  layer_name = "aiohttp"
}

data "aws_lambda_layer_version" "kb_layer" {
  provider = aws.ai_stack
  layer_name = "bs4"
}

data "aws_security_group" "app_sg" {
  provider = aws.ai_stack
  vpc_id   = data.aws_vpc.main.id
  name     = "SG-${var.source_market}-${lower(terraform.workspace)}-lambda"
}


data "aws_secretsmanager_secret" "secret-lambda" {
  provider = aws.ai_stack
  name = "manual_lambda_secret"
}

