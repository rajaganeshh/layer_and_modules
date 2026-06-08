output "secret_id" {
  description = "Secret id"
  value       = aws_secretsmanager_secret.secret.id
}

output "secret_arn" {
  description = "Secrets arn"
  value       = aws_secretsmanager_secret.secret.arn
}
