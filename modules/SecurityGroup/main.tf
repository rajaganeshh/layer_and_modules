locals {
  any_port     = 0
  any_protocol = "-1"
}

resource "aws_security_group" "secGroup" {
  count  = var.name != "" ? 1 : 0
  name   = var.name
  vpc_id = var.vpc_id
  tags   = var.tags
}



resource "aws_security_group_rule" "ec2_sg_allow_sg_rules" {
 for_each           = var.sg_rule_details
 
  security_group_id = aws_security_group.secGroup[0].id

  type                      = lookup(each.value, "type", null)
  from_port                 = lookup(each.value, "from_port", null)
  to_port                   = lookup(each.value, "to_port", null)
  protocol                  = lookup(each.value, "protocol", null)
  description               = lookup(each.value, "description", null)
  cidr_blocks               = lookup(each.value, "cidr_block", null)
  source_security_group_id  = lookup(each.value, "source_sg_id", null)
  ipv6_cidr_blocks          = lookup(each.value, "ipv6_cidr_blocks", null)
  prefix_list_ids           = lookup(each.value, "prefix_list_ids", null)
}


#resource "aws_security_group_rule" "b_from_a" {
#  count                    = var.allow_rule_enable
#  security_group_id        = "sg-0def732aedcf671fe" #module.application_security_group["app"].server_security_group_id
#  type                     = "ingress"
#  from_port                = 22
#  to_port                  = 22
#  protocol                 = "tcp"
#  source_security_group_id = "sg-020929f6ca1bb03aa" #module.loadbalancer_security_group.server_security_group_id
#  depends_on               = [aws_security_group_rule.ec2_sg_allow_sg_rules]
#}


#resource "aws_security_group_rule" "allow_octopus_deploy" {
#  
#  dynamic
#  type              = var.sg_type
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = "10933"
#  to_port     = "10933"
#  protocol    = "tcp"
#  description = "Allow Octopus deploy to connect to tentacle"
#  cidr_blocks = ["172.17.0.0/23", "172.17.6.0/23", "172.17.8.0/23"]
#}

#resource "aws_security_group_rule" "allow_http_inbound" {
#  type              = "ingress"
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = "80"
#  to_port     = "80"
#  protocol    = "tcp"
#  description = "Allows inbound http access"
#  cidr_blocks = ["172.0.0.0/8", "10.0.0.0/8"]
#}
#
#resource "aws_security_group_rule" "allow_https_inbound" {
#  type              = "ingress"
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = "443"
#  to_port     = "443"
#  protocol    = "tcp"
#  description = "Allows inbound https access"
#  cidr_blocks = ["172.0.0.0/8", "10.0.0.0/8"]
#}
#
#resource "aws_security_group_rule" "allow_RDP_inbound" {
#  type              = "ingress"
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = "3389"
#  to_port     = "3389"
#  protocol    = "tcp"
#  description = "Allows inbound RDP access"
#  cidr_blocks = ["172.0.0.0/8", "10.0.0.0/8"]
#}
#
#resource "aws_security_group_rule" "allow_ICMP_inbound" {
#  type              = "ingress"
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = local.any_port
#  to_port     = local.any_port
#  protocol    = "ICMP"
#  description = "Allows inbound ICMP access"
#  cidr_blocks = ["172.0.0.0/8", "10.0.0.0/8"]
#}
#
#resource "aws_security_group_rule" "allow_all_outbound" {
#  type              = "egress"
#  security_group_id = aws_security_group.secGroup.id
#
#  from_port   = local.any_port
#  to_port     = local.any_port
#  protocol    = local.any_protocol
#  description = "Allows all outbound access"
#  cidr_blocks = ["0.0.0.0/0"]
#}
#