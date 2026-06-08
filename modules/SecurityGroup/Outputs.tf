output "server_security_group_id" {
    value = aws_security_group.secGroup[0].id
    description = "The ID of the Security Group"
}