

resource "aws_security_group_rule" "ec2_sg_allow_sg_rules" {
 for_each           = var.sg_rule_details 

  security_group_id         = var.security_group_id 

  type                      = lookup(each.value, "type", null)
  from_port                 = lookup(each.value, "from_port", null)
  to_port                   = lookup(each.value, "to_port", null)
  protocol                  = lookup(each.value, "protocol", null)
  description               = lookup(each.value, "description", null)
  cidr_blocks               = lookup(each.value, "cidr_block", null)
  source_security_group_id  = var.source_sg_default
  ipv6_cidr_blocks          = lookup(each.value, "ipv6_cidr_blocks", null)
  prefix_list_ids           = lookup(each.value, "prefix_list_ids", null)
}
