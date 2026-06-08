

##################  LB Certificate creation ##################
module "cert" {

  count = lookup(var.app_lb_cert_enabled, var.env_type) == "true" ? 1 : 0

  providers = {
    aws         = aws.ai_stack
    aws.dnszone = aws.ai_stack_dns_zone
  }


  source            = "git@github.com:company-org/company-name-iac-modules.git//Source/SSL-Certificate-Route53?ref=feature/route53_entry"
  domain_name       = var.env_type == "PROD" ? "mim.domain" : "mimdev.domain"
  route53_zone_name = var.env_type == "PROD" ? "mim.domain" : "mimdev.domain"
  private_zone_enabled = true
  tags = merge(local.common_tags,
  { Account = var.aws_account_id })
}

###################### application ALB creation #######

module "application_lb" {

  for_each = var.env_type == "PROD" ? var.app_alb_PROD : var.app_alb

  providers = {
    aws         = aws.ai_stack
    aws.dnszone = aws.ai_stack_dns_zone
  }

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/ALB?ref=main"

  lb_name                    = "${var.source_market}-${lower(terraform.workspace)}-${each.value.lb_name}"
  lb_internal                = each.value.lb_category == "private" ? "true" : "false"
  lb_subnet_ids              = each.value.lb_category == "private" ? data.aws_subnets.lb_subnets_private.ids : data.aws_subnets.lb_subnets_public.ids
  lb_security_groups         = each.value.lb_category == "private" ? [data.aws_security_group.private_alb[0].id] : [data.aws_security_group.public_alb[0].id]
  lb_type                    = each.value.lb_type
  certificate_arn            = each.value.certificate_enabled == "true" ?  module.cert[0].certificate_arn : ""
  additional_certificate_arn = []
  lb_dns_name                = var.env_type == "PROD" ? ".mim.domain" : ".mimdev.domain"
  lb_dns_entry               = ["simon"]
  route53_zone_name          = var.env_type == "PROD" ? "mim.domain" : "mimdev.domain"
  add_port_80_listener       = lookup(var.listener_80_enabled, var.env_type)
  add_port_443_listener      = lookup(var.listener_443_enabled, var.env_type)
  enable_deletion_protection = lookup(var.lb_enable_deletion_protection, var.env_type)

  common_tags = merge(local.common_tags,
					  { Name = "${var.source_market}-${lower(terraform.workspace)}-${each.value.lb_name}" },
					  { Account = var.aws_account_id })
  }


################## Target Group creation ##################

module "lb_target_group" {

  providers = {
    aws = aws.ai_stack
  }

  # Merge common TGs with env specific ones. Tries to fetch using env name first, then falls back to env_type, then {}, if non found

  for_each = local.app_tg_type

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/Target_Group?ref=main"

  tg_name                = "${var.source_market}-${local.tg_env}-tg-${lower(each.key)}"
  tg_port                = each.value.port
  tg_protocol            = each.value.protocol
  tg_healthy_threshold   = each.value.healthy_threshold
  tg_unhealthy_threshold = each.value.unhealthy_threshold
  tg_path                = each.value.path
  target_type            = each.value.target_type
  tg_health_interval     = lookup(var.healthcheck_interval, var.env_type)
  vpc_id                 = data.aws_vpc.main.id
  tg_sticky_type         = lookup(var.sticky_session_type, var.env_type)
  tg_sticky_enabled      = lookup(var.sticky_session_enabled, var.env_type)
  tg_sticky_duration     = lookup(var.sticky_session_duration, var.env_type)
  common_tags = merge(local.common_tags,
    { Name = "${var.source_market}-${local.tg_env}-tg-${lower(each.key)}" },
    { Account = var.aws_account_id },
    { Service = "Target Group" },
    { Target_Type = each.value.target_type })
}


################## Load Balancer Rule 443 & 80 creation in Private Subnet ##################

module "lb_listener_rule" {

  providers = {
    aws = aws.ai_stack
  }

  for_each = var.alb_rules

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/ALB_Listener_Rules?ref=main"

  lb_listener_arn               = local.tg_app_arn[each.value.target_arn]
  priority                      = each.value.priority
  target_group_arn              = module.lb_target_group[each.value.target_key].tg_arn
  service_path_pattern          = each.value.service_path_pattern
  static_action                 = each.value.static_action

  common_tags = merge(local.common_tags,
    { Name = "${var.source_market}-${lower(terraform.workspace)}-443-${lower(each.key)}" },
  { Account = var.aws_account_id })

}


module "ecs_cluster_layer" {
  
  providers = {
    aws = aws.ai_stack
  }

 source = "git@github.com:company-org/company-name-iac-modules.git//Source/ECS_Cluster?ref=main"
  
  cluster_name = "${lookup(var.cluster_name, var.env_type)}"
  enable_container_insights = lookup(var.container_insights, var.env_type)
}


################## Target Group GREEN creation ##################

###  Target group commented  module "lb_target_group_private" {
###  Target group commented  
###  Target group commented    providers = {
###  Target group commented      aws = aws.ai_stack
###  Target group commented    }
###  Target group commented  
###  Target group commented    # Merge common TGs with env specific ones. Tries to fetch using env name first, then falls back to env_type, then {}, if non found
###  Target group commented    for_each = local.app_tg_type_green
###  Target group commented  
###  Target group commented    source = "git@github.com:company-org/company-name-iac-modules.git//Source/Target_Group?ref=main"
###  Target group commented  
###  Target group commented    tg_name                = "${var.source_market}-${local.tg_env}-tg-${lower(each.key)}-green"
###  Target group commented    tg_port                = each.value.port
###  Target group commented    tg_protocol            = each.value.protocol
###  Target group commented    tg_healthy_threshold   = each.value.healthy_threshold
###  Target group commented    tg_unhealthy_threshold = var.green_443_weight == "0" ? "10" : each.value.unhealthy_threshold
###  Target group commented    tg_path                = each.value.path
###  Target group commented    target_type            = each.value.target_type
###  Target group commented    tg_health_interval     = var.green_443_weight == "0" ? "300" : lookup(var.healthcheck_interval, var.env_type)
###  Target group commented    vpc_id                 = data.aws_vpc.main.id
###  Target group commented    tg_sticky_type         = lookup(var.sticky_session_type, var.env_type)
###  Target group commented    tg_sticky_enabled      = lookup(var.sticky_session_enabled, var.env_type)
###  Target group commented    tg_sticky_duration     = lookup(var.sticky_session_duration, var.env_type)
###  Target group commented    tg_matcher                   = var.app_type == "VT100SSH" ? var.tg_matcher : null
###  Target group commented  
###  Target group commented    common_tags = merge(local.common_tags,
###  Target group commented      { Name = "${var.source_market}-${local.tg_env}-tg-${lower(each.key)}-green" },
###  Target group commented      { Account = var.aws_account_id },
###  Target group commented      { Service = "Target Group" },
###  Target group commented    { Target_Type = each.value.target_type })
###  Target group commented  }




## LB  commented  ################## Load Balancer creation private Subnet ##################
## LB  commented  
## LB  commented  module "application_lb_private" {
## LB  commented  
## LB  commented    count = lookup(var.int_lb_enabled, var.env_type) == "true" ? 1 : 0
## LB  commented  
## LB  commented    providers = {
## LB  commented      aws         = aws.ai_stack
## LB  commented      aws.dnszone = aws.ai_stack_dns_zone
## LB  commented    }
## LB  commented  
## LB  commented    source = "git@github.com:company-org/company-name-iac-modules.git//Source/ALB?ref=main"
## LB  commented  
## LB  commented    lb_name                    = "${var.source_market}-${lower(terraform.workspace)}-${lower(var.app_type)}-int-alb"
## LB  commented    lb_internal                = "1"
## LB  commented    lb_subnet_ids              = data.aws_subnets.lb_subnets_private.ids
## LB  commented    lb_security_groups         = [data.aws_security_group.alb[0].id]
## LB  commented    lb_type                    = "application"
## LB  commented    certificate_arn            = lookup(var.app_lb_cert_enabled, var.env_type) == "true" ? module.cert[0].certificate_arn : data.aws_acm_certificate.amazon_issued[0].arn
## LB  commented    additional_certificate_arn = lookup(var.app_lb_listener_cert_enabled, var.env_type) == "true" ? [data.aws_acm_certificate.imported[0].arn] : []
## LB  commented    lb_dns_name                   = (var.env_type == "PROD" || (var.app_type == "VT100SSH" && var.env_type == "TRN")) ? ".prod.dcp.domain" : "-${lower(terraform.workspace)}.nonprod.dcp.domain"
## LB  commented    lb_dns_entry               = local.lb_dns_entry[var.app_type]
## LB  commented    route53_zone_name             = (var.env_type == "PROD" || (var.app_type == "VT100SSH" && var.env_type == "TRN")) ? "prod.dcp.domain" :"nonprod.dcp.domain"
## LB  commented    add_port_4431_listener     = lookup(var.listener_4431_enabled, var.env_type)
## LB  commented    add_port_443_listener      = lookup(var.listener_443_enabled, var.env_type)
## LB  commented    enable_deletion_protection = lookup(var.lb_enable_deletion_protection, var.env_type)
## LB  commented  
## LB  commented    common_tags = merge(local.common_tags,
## LB  commented      { Name = "${var.source_market}-${lower(terraform.workspace)}-${lower(var.app_type)}-int-alb" },
## LB  commented    { Account = var.aws_account_id })
## LB  commented  }
