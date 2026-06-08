locals{
  execution_role_name       = element(split("/", var.execution_role_arn), length(split("/", var.execution_role_arn)) - 1)
}
resource "aws_ecs_task_definition" "ecs_task_definition" {
  family                   = var.service_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  memory                   = var.memory
  cpu                      = var.cpu
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn
  container_definitions    = var.container_definitions
}


resource "aws_ecs_service" "ecs_services" {
  name                   = var.service_name
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.ecs_task_definition.arn
  desired_count          = var.desired_count
  launch_type            = "FARGATE"
  wait_for_steady_state  = true
  enable_execute_command = var.enable_execute_command
  force_new_deployment   = var.force_new_deployment


  lifecycle {
    ignore_changes = [desired_count]
  }

  load_balancer {
    target_group_arn = var.lb_target_group_arn
    container_name   = var.container_name
    container_port   = var.container_port
  }

  network_configuration {
    security_groups  = [var.security_group_id]
    subnets          = var.subnet_ids
    assign_public_ip = var.assign_public_ip

  }
  timeouts {
    create = var.create_time_out
    delete = var.delete_time_out
    update = var.update_time_out
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_ecr_read_only" {
  role       = local.execution_role_name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
resource "aws_iam_role_policy_attachment" "ecs_task_execution_ecr_pull_only" {
  role       = local.execution_role_name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"
}


