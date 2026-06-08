resource "aws_ecr_repository" "core_ecr" {
  name                 = var.ecr_repo_name
  image_tag_mutability = var.mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  tags = merge(
    var.additional_tags,
    tomap({ Name = var.ecr_repo_name,
    service = "ECR" })
  )
  lifecycle {
    ignore_changes = [
      tags["Purpose"]
    ]
  }
}

resource "aws_ecr_repository_policy" "core_ecr_policy" {
  repository = var.ecr_repo_name
  policy     = var.ecr_repo_policy
  depends_on = [aws_ecr_repository.core_ecr]
}

resource "aws_ecr_lifecycle_policy" "core_ecr_lifecycle_policy" {

  repository = var.ecr_repo_name
  policy     = var.ecr_repo_lifecycle_policy
  depends_on = [aws_ecr_repository.core_ecr]

}
