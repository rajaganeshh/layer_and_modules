resource "aws_ecs_cluster" "ecs_cluster" {
  name = var.cluster_name

  lifecycle {
    create_before_destroy = true
  }

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }
}
