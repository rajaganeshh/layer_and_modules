
#output "iam_role_arn_ecs" {
#  description = "IAM Role ARN"
#  value       = module.iam_roleforecs.iam_arn
#}

#output "iam_role_arn_task" {
#  description = "IAM Role ARN"
#  value       = module.iam_rolefortask.iam_arn
#}


#output "lb_sg_id_public" {
#  description = "IAM Role ARN"
#  value       = length(local.lb_security_rules_public) > 0 ? module.loadbalancer_security_group_public[0].server_security_group_id : null
#}

output "lb_sg_id_private" {
  description = "IAM Role ARN"
  value       = length(var.lb_sg_rules_private) > 0 ? module.loadbalancer_security_group_private[0].server_security_group_id : null
}

output "app_sg_id" {
  description = "IAM Role ARN"
  value       = module.application_security_group.server_security_group_id
}


