# Exported Output values of ECR
output "ecr_repo_arn" {
  description = "ARN for ecr"
  value = aws_ecr_repository.core_ecr.arn
}

output "ecr_repository_url" {
  description = "URL for cloning the repository with http"
  value = aws_ecr_repository.core_ecr.repository_url
}

output "ecr_repository_id" {
  description = "URL for cloning the repository with http"
  value = aws_ecr_repository.core_ecr.registry_id
}