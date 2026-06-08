##################  Service Linked Role Creation ##################

resource "aws_iam_service_linked_role" "ecs" {

  provider                         = aws.ai_stack
  aws_service_name                 = "ecs.amazonaws.com"
  description      = "Service-linked role for ECS service and capacity providers"  
}



##################  Application IAM Role Creation ##################

module "iam_roles" {

   for_each = var.iam_roles

  providers                       = {
    aws                           = aws.ai_stack
  }

  source                          = "git@github.com:company_org/company_module.git//Source/IAM"

  role_name                       = "${var.source_market}_${lower(terraform.workspace)}_simon_${each.value.role_name}"
  assume_role_policy              = local.assume_policy[each.value.assume_role_policy]
  instance_profile_enabled        = each.value.instance_profile
  iam_policy                      = local.custom_roles_application[each.value.iam_policy]
  policy_attach_role              = [for name in each.value.policy_attach_role : local.policy_roles_attach[name]] 

  common_tags = merge(
    local.common_tags,
    { Name = "${var.source_market}_${lower(terraform.workspace)}_simon_${each.value.role_name}" },
    { Account = var.aws_account_id }
  )
}


##################  ALB Security group Creation ##################

#module "loadbalancer_security_group_public" {
#
#  providers                     = {
#    aws                         = aws.ai_stack
#  }                             
#								
#  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"
#  count                         = length(local.lb_security_rules_public) > 0 ? 1 : 0
#  vpc_id                        = data.aws_vpc.main.id
#  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-alb-public"
#  sg_rule_details               = local.lb_security_rules_public
#								
#  tags                          = merge(local.common_tags,
#                                        { Name = "SG-${var.source_market}-${lower(terraform.workspace)}-alb-${var.app_type}" },
#                                        { Account = var.aws_account_id })
#}

### Additional ALB security group creation ####

module "loadbalancer_security_group_private" {

  providers                     = {
    aws                         = aws.ai_stack
  }

  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"
  count                         = length(local.dynamic_cidr_all_app_lb) > 0 ? 1 : 0
  vpc_id                        = data.aws_vpc.main.id
  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-alb-private"
  sg_rule_details               = local.dynamic_cidr_all_app_lb
  tags                          = merge(local.common_tags,
                                       { Name            = "SG-${var.source_market}-${lower(terraform.workspace)}-alb-private" },
                                       { Account         = var.aws_account_id })
}


##################  Application Security Group Creation ##################

module "application_security_group" {

  providers                     = {
    aws                         = aws.ai_stack
  }

  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"

  vpc_id                        = data.aws_vpc.main.id
  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-ecs-common"
  sg_rule_details               = local.dynamic_cidr

  tags                          = merge(local.common_tags, 
                                       { Name = "SG-${var.source_market}-${lower(terraform.workspace)}-ecs-common" },
                                       { Account = var.aws_account_id })
}

##################  Application Security Group Creation ##################

module "db_security_group" {

  providers                     = {
    aws                         = aws.ai_stack
  }

  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"

  vpc_id                        = data.aws_vpc.main.id
  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-auroradb"
  sg_rule_details               = local.dynamic_cidr_all_db

  tags                          = merge(local.common_tags, 
                                       { Name = "SG-${var.source_market}-${lower(terraform.workspace)}-auroradb" },
                                       { Account = var.aws_account_id })
}

##################  Bedrock Security group Creation ##################

module "bedrock_security_group" {

  providers                     = {
    aws                         = aws.ai_stack
  }

  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"

  vpc_id                        = data.aws_vpc.main.id
  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-bedrock"
  sg_rule_details               = local.dynamic_cidr_all_bg

  tags                          = merge(local.common_tags, 
                                       { Name = "SG-${var.source_market}-${lower(terraform.workspace)}-bedrock" },
                                       { Account = var.aws_account_id })
}

##################  Lambda Security group Creation ##################

module "lambda_security_group" {

  providers                     = {
    aws                         = aws.ai_stack
  }

  source                        = "git@github.com:company_org/company_module.git//Source/SecurityGroup"

  vpc_id                        = data.aws_vpc.main.id
  name                          = "SG-${var.source_market}-${lower(terraform.workspace)}-lambda"
  sg_rule_details               = var.lambda_sg_type

  tags                          = merge(local.common_tags, 
                                       { Name = "SG-${var.source_market}-${lower(terraform.workspace)}-lambda" },
                                       { Account = var.aws_account_id })
}



####### Public LB to private LB SecurityGroup rule creation ====
##
##module "application_security_group_sg_lb_public" {
##
##  count = length(var.app_sg_rules_allow_private) > 0 ? 1 : 0
##
##  providers = {
##    aws = aws.ai_stack
##  }
##
##  source                 = "git@github.com:company_org/company_module.git//Source/SecurityGroup_Rules"
##
##  security_group_id      = module.application_security_group.server_security_group_id
##  source_sg_default      = module.additional_loadbalancer_security_group_private[0].server_security_group_id
##  sg_rule_details        = var.app_sg_rules_allow_private
##
##}



####   ##################  LB security group Rule Creation ##################
####   
####   module "application_security_group_sg_lb_public" {
####   
####     count = length(var.app_sg_rules_allow) > 0 ? 1 : 0
####   
####     providers = {
####       aws = aws.ai_stack
####     }
####   
####     source = "../../company_module//Source/SecurityGroup_Rules"
####   
####     security_group_id = module.application_security_group.server_security_group_id
####     source_sg_default = module.loadbalancer_security_group_public[0].server_security_group_id
####     sg_rule_details   = var.app_sg_rules_allow_public
####   
####   }

### Commented  ################## SSM Parameter for Application account ##################
### Commented  
### Commented  module "ssm_parameter_store" {
### Commented    for_each = local.ssm_param
### Commented    source   = "../../company_module//Source/SSM"
### Commented    providers = {
### Commented      aws = aws.ai_stack
### Commented    }
### Commented    ssm_name        = each.value.name
### Commented    ssm_description = each.value["name"]
### Commented    ssm_value       = each.value["value"]
### Commented    ssm_type        = each.value["type"]
### Commented    encrypt_enabled = each.value["encrypt"]
### Commented    ssm_host        = each.value["host"]
### Commented    ssm_kms_id      = each.value["encrypt"] == "true" ? data.aws_kms_key.kms.arn : ""
### Commented  
### Commented    common_tags = merge(local.common_tags,
### Commented      { Name = each.value["name"] },
### Commented    { Account = var.aws_account_id })
### Commented  }


## resource "aws_iam_service_linked_role" "autoscaling" {
## 
##   provider                         = aws.ai_stack
##   aws_service_name                 = "autoscaling.amazonaws.com"
## }


## commented    ##################  KMS Key Creation ##################
## commented    
## commented    module "kms_key" {
## commented    
## commented      providers                      = {
## commented        aws                          = aws.ai_stack
## commented      }
## commented      source                         = "../../company_module//Source/KMS"
## commented    
## commented      kms_description                = "${lower(var.app_type)}_kms_ssm_parameter_desccription"
## commented      kms_policy                     = data.template_file.ssm_kms_policy.rendered
## commented      kms_alias                      = "${lower(var.app_type)}_kms_ssm_parameter"
## commented    
## commented      common_tags                    = merge(local.common_tags,
## commented                                            { Name = "${lower(var.app_type)}_kms_ssm_parameter" },
## commented                                            { Account = var.aws_account_id })
## commented    										
## commented      depends_on = [aws_iam_service_linked_role.autoscaling]
## commented    }