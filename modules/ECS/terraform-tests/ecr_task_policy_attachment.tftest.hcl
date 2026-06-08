mock_provider "aws" {}

variables {

  execution_role_arn = "arn:aws:iam::123456789012:role/test-ecs-execution-role"

  service_name = "test-service"
    cpu          = 256
    memory       = 512

    container_name = "test-container"
    container_port = 8080

    ecs_cluster_id      = "test-cluster"
    lb_target_group_arn = "arn:aws:elasticloadbalancing:eu-west-1:123456789012:targetgroup/test/123456"

    security_group_id = "sg-12345678"
    subnet_ids        = ["subnet-12345", "subnet-67890"]

    container_definitions = jsonencode([
      {
        name      = "test-container"
        image     = "nginx"
        essential = true
      }
    ])
}

run "ecs_task_execution_ecr_policy_attachment_test" {
  command = plan

   assert {
    condition = aws_iam_role_policy_attachment.ecs_task_execution_ecr_pull_only.role == "test-ecs-execution-role"
    error_message = "Execution role name is not wired correctly for PullOnly policy"
  }
  assert {
    condition = aws_iam_role_policy_attachment.ecs_task_execution_ecr_read_only.policy_arn == "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    error_message = "ECR ReadOnly policy is not attached"
  }

  assert {
    condition = aws_iam_role_policy_attachment.ecs_task_execution_ecr_pull_only.policy_arn == "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly"
    error_message = "ECR PullOnly policy is not attached"
  }
}