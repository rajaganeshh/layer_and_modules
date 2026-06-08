output "ecs_cluster_id" {
  value = aws_ecs_cluster.ecs_cluster.id
}

output "ecs_cluster_name" {
 description = "Cluster Name"
 value = aws_ecs_cluster.ecs_cluster.name
}

output "ecs_cluster_arn" {
 description = "Cluster ARN"
 value = aws_ecs_cluster.ecs_cluster.arn
}
