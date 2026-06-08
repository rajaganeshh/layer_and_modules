output "iam_arn" {
  value = aws_iam_role.iam_role.arn
}


output "instance_profile_arn" {
  value = var.instance_profile_enabled == true ? aws_iam_instance_profile.serive_iam_role_instance_profile[0].arn : null
}