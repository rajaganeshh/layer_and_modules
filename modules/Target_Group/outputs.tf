output "tg_arn" {
  value = aws_lb_target_group.lb_target_group.arn
}

#output "security_group_id" {
#  value = aws_security_group.lb_sg.id
#}

output "tg_arn_suffix" {
  value = aws_lb_target_group.lb_target_group.arn_suffix
}

output "tg_id" {
  value = aws_lb_target_group.lb_target_group.id
}