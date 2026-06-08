################  LB


##### Security Group Selection

data "aws_security_group" "public_alb" {
  provider = aws.ai_stack
  count    = lookup(var.public_lb_enabled, var.env_type) == "true" ? 1 : 0
  vpc_id   = data.aws_vpc.main.id
  name     = "SG-company-name-${lower(terraform.workspace)}-alb-public"
}

data "aws_security_group" "private_alb" {
  provider = aws.ai_stack
  count    = lookup(var.private_lb_enabled,var.env_type) == "true"  ? 1 : 0
  vpc_id   = data.aws_vpc.main.id
  name     = "SG-company-name-${lower(terraform.workspace)}-alb-private"
}



