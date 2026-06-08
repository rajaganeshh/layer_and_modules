output "alb_arn" {
  value       = aws_lb.alb.arn
  description = "ARN of the Application Load Balancer created"
}

output "port80_listener_arn" {
  description = "ARN of the port 80 listener if created, otherwise null"
  value       = var.add_port_80_listener ? aws_lb_listener.port80[0].arn : null
}

output "port443_listener_arn" {
  description = "ARN of the port 443 listener if created, otherwise null"
  value       = var.add_port_443_listener ? aws_lb_listener.port443[0].arn : null
}

output "port4431_listener_arn" {
  description = "ARN of the port 4431 listener if created, otherwise null"
  value       = var.add_port_4431_listener ? aws_lb_listener.port4431[0].arn : null
}

output "hosted_zone" {
  description = "ID of the Route 53 hosted zone associated with the ALB records"
  value       = data.aws_route53_zone.selected.zone_id
}

output "alb_dns_name" {
  description = "Internal DNS name of the Application Load Balancer created"
  value       = aws_lb.alb.dns_name
}

output "route53_record_names" {
  description = "Fully qualified domain names created for the ALB"
  value       = [for record in aws_route53_record.alb_wildcard : record.fqdn]
}
