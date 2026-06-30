output "rds_endpoint" {
  description = "The RDS instance endpoint"
  value       = aws_rds_cluster.aurora.endpoint
}