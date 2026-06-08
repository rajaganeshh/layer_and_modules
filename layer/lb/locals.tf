locals {


  tg_app_arn = {
    port_alb_443    = lookup(var.listener_443_enabled, var.env_type) == "true" ? module.application_lb["lb"].port443_listener_arn : ""
    port_alb_80   = lookup(var.listener_80_enabled, var.env_type) == "true" ? module.application_lb["lb"].port80_listener_arn : ""
  }

  # Tags
  common_tags = merge(var.tags,  { CostOwnerTeam = var.CostOwnerTeam, SupportTeam = var.SupportTeam[var.env_type] })


  app_tg_type = var.env_type == "PROD" ? var.app_tg_type_PROD["COMMON"] : var.app_tg_type["COMMON"]
  
}
