# ECS Cluster

module "ecs_task" {

  providers                       = {
    aws                           = aws.ai_stack
  }

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/ECS?ref=main"
  
  service_name            = lookup(var.service_name, var.app_type)
  memory                  = tostring(lookup(var.memory, var.app_type) * 1024)
  cpu                     = tostring(lookup(var.cpu, var.app_type) * 1024)
  execution_role_arn      = data.aws_iam_role.ecsrole.arn
  task_role_arn           = data.aws_iam_role.ecstaskrole.arn
  container_definitions   = data.template_file.custom_policy_service.rendered
  ecs_cluster_id          = data.aws_ecs_cluster.ecs_cluster.arn 
  desired_count           = 1
  enable_execute_command  = "true"
  force_new_deployment    = true
  lb_target_group_arn     = data.aws_lb_target_group.service.arn
  container_name          = lookup(var.container_name, var.app_type)
  container_port          = lookup(var.container_port, var.app_type)
  security_group_id       = data.aws_security_group.app_sg.id
  subnet_ids              = data.aws_subnets.lb_subnets_private.ids
  assign_public_ip        = lookup(var.assign_public_ip,var.app_type)
  create_time_out         = lookup(var.create_time_out, var.app_type)
  delete_time_out         = lookup(var.delete_time_out, var.app_type)
  update_time_out         = lookup(var.update_time_out, var.app_type)

}




