
##### Security Group Selection

data "aws_security_group" "auroradb" {
  provider = aws.ai_stack
  vpc_id   = data.aws_vpc.main.id
  name     = "SG-company-name-${lower(terraform.workspace)}-auroradb"
}

data "aws_secretsmanager_secret" "db_password" {
  provider = aws.ai_stack
  name = "/MIM/auroradb"
}


data "aws_secretsmanager_secret_version" "db_password" {
  provider = aws.ai_stack
  secret_id = data.aws_secretsmanager_secret.db_password.id
}