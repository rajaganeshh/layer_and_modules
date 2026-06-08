variable "cluster_name" {
  type        = string
  description = "The name of the ECS Cluster"
}

variable "enable_container_insights" {
  type        = bool
  description = "Enable CloudWatch Container Insights for the ECS Cluster"
}
