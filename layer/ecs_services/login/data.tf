################  ECR

data "template_file" "custom_policy_service" {

  template = file("${path.module}/policies/container.json")

  vars = {
    container_name    = lookup(var.container_name, var.app_type)
    image_name        = lookup(var.image_name, var.app_type)
	container_port    = lookup(var.container_port, var.app_type)
    image_tag         = lookup(var.image_tag, var.app_type)
    cpu               = tostring(lookup(var.cpu,var.app_type) * 1024)
    memory            = tostring(lookup(var.memory, var.app_type) * 1024)
    log_group         = lookup(var.log_group, var.app_type)
    region            = var.region
    log_stream_prefix = lookup(var.log_stream_prefix, var.app_type)
	account           = var.aws_account_id
  }
}

data "aws_iam_role" "ecsrole" {
  provider = aws.ai_stack
  name = "${lower(terraform.workspace)}_RoleForECS"
}

data "aws_iam_role" "ecstaskrole" {
  provider = aws.ai_stack
  name = "${lower(terraform.workspace)}_RoleForECSTask"
}


data "aws_ecs_cluster" "ecs_cluster" {
  provider = aws.ai_stack
  cluster_name = lookup(var.cluster_name, var.env_type)
}

data "aws_security_group" "app_sg" {
  provider = aws.ai_stack
  vpc_id   = data.aws_vpc.main.id
  name     = "SG-company-name-${lower(terraform.workspace)}-ec2-app"
}

data "aws_lb_target_group" "service" {
  provider = aws.ai_stack
  name = "company-name-${lower(var.env_type)}-tg-${lower(var.app_type)}-80"
}