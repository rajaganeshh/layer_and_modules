variable "region" {
  description = "AWS region that will be used to create resources in."
  type        = string
  default     = ""
}

variable "aws_account_id" {
  type        = string
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default     = ""
}

variable "stack_account_role" {
  type        = string
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default     = "RoleForTerraform"
}


variable "env_type" {
  description = "AWS region that will be used to create resources in."
  type        = string
  default     = ""
}

variable "CostOwnerTeam" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = string
  default     = "Cloud Operation team"
}


variable "bedrock_username" {
  description = "AWS region that will be used to create resources in."
  type        = string
  default     = "bedrock-user"
}

variable "costcentre_id" {
  description = "CostCentre - 5 digit number"
  type        = string
  default     = ""
}

variable "costcentre_num" {
  type        = map(any)
  description = "CostCentre - 5 digit number"
  default     = {
     DEV = ""
     PROD = ""
  }
}


variable "instance_profile" {
  type        = map(any)
  description = "CostCentre - 5 digit number"
  default     = {
     ecs_role = "false"
     ecs_task_role = "false"
	 lambda_role  = "false"
  }
}

variable "Compliance" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = string
  default     = ""
}

variable "gdpr_compliance" {
  description = "Is the infrastructure GDPR compliant?"
  type        = string
  default     = ""
}

variable "pci_compliance" {
  description = "Is the infrastructure PCI compliant?"
  type        = string
  default     = ""
}

variable "nis_d_compliance" {
  description = "Is the infrastructure NIS_D compliant?"
  type        = string
  default     = ""
}

variable "app_type" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = string
  default     = "backend"
}

variable "tags" {
  description = "Common tags for all"
  type        = map(any)
  default = {
    TechnicalOwner = "DevOPs_Team"
    Owner          = "project_owner"
    DeployedBy     = "Terraform"
  }
}

variable "SupportTeam" {
  type        = map(string)
  default     = {}
  description = "description"
}


variable "Application" {
  type        = string
  description = "description"
  default     = ""
}

variable "Criticality" {
  type        = map(any)
  description = "Map of Criticality variables"
  default = {
    DEV     = "4"
    PROD    = "2"
  }
}

variable "patchgroup" {
  description = "AWS region that will be used to create resources in."
  type        = map
  default     = {
    DEV       = "off"
    PROD      = "off"
  }
}

variable "vpc_prefix" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = string
  default     = ""

}

variable "stopstart_value" {
  description = "SSM Value"
  type        = map(any)
  default = {
    DEV      = "06:00-18:00 Mon-Fri Dublin"
    PROD     = ""
  }
}


######## Structure variables

# Common Variables

variable "lambda_sg_type" {
  description = "Map of instance details"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}


variable "db_sg_type" {
  description = "Map of instance details"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "bedrock_sg_type" {
  description = "Map of instance details"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "app_sg_type_DEV" {
  description = "Map of instance details"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "app_sg_type_PROD" {
  description = "Map of instance details"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}


variable "lb_sg_rules_public" {
  description = "App Application Security group Rules"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "lb_sg_rules_public_PROD" {
  description = "App Application Security group Rules"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "lb_sg_rules_private_PROD" {
  description = "App Application Security group Rules"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "lb_sg_rules_private" {
  description = "App Application Security group Rules"
  type = map(object({
    type        = string
    protocol    = string
    from_port   = number
    to_port     = number
    cidr_block  = list(string)
    description = string
    })
  )
  default = {}
}

variable "app_sg_rules_allow_public" {
  type        = map(any)
  description = "App Application Security group Rules"
  default     = {}
}

variable "app_sg_rules_allow_private" {
  type        = map(any)
  description = "App Application Security group Rules"
  default     = {}
}


variable "lb_sg_rules_allow" {
  type        = map(any)
  description = "App Application Security group Rules"
  default     = {}
}

variable "iam_roles" {
  description = "Map of IAM roles to create"
  type = map(object({
    role_name            = string
    assume_role_policy   = string
    instance_profile     = bool
    iam_policy           = any
    policy_attach_role   = list(string)
  }))
  default = {}
}

######## Common Variables End

######## LB Variables Start

variable "app_lb_cert_enabled" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {
    DEV      = "false"
    PROD     = "false"
  }
}

variable "app_lb_ext_cert_enabled" {
  type = map
  description = "AWS LB certificate required true or false"
  default = {
    DEV      = "false"
    PROD     = "false"
  }
}

variable "int_lb_enabled" {
  type        = map(any)
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default    = {
    DEV      = "false"
    PROD     = "false"
  }
}


variable "public_lb_enabled" {
  type        = map(any)
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default    = {
    DEV      = "false"
    PROD     = "false"
  }
}

variable "private_lb_enabled" {
  type        = map(any)
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default    = {
    DEV      = "false"
    PROD     = "false"
  }
}


variable "listener_80_enabled" {
  description = "External LB creation"
  type        = map(any)
  default     = {
    DEV 	 = "true"
	PROD     = "false"
  }
}

variable "listener_443_enabled" {
  description = "External LB creation"
  type        = map(any)
  default     = {
    DEV 	 = "false"
	PROD     = "false"
  }
}


variable "disable_capacity_change_timeout" {
  type        = bool
  description = "Disables ASG capacity change waiting time."
  default     = false
}



variable "lb_enable_deletion_protection" {
  description = "If true this will prevent Terraform from deleting the load balancer."
  type        = map(any)
  default     = {
    DEV       = "false"
    PROD      = "true"
  }
}

variable "hostnamewithip" {
  description = "Hostname with ip required"
  type        = map(any)
  default     = {
    DEV       = "false"
    PROD      = "false"
  }
}


variable "app_alb" {
  description = "Map of instance details"
  type = map(any)
  default    = {}
}

variable "app_alb_PROD" {
  description = "Map of instance details"
  type = map(any)
  default    = {}
}

variable "alb_rules" {
  description = "Map of instance details"
  type = map(object({
      target_key           = string
      target_arn           = string
      priority             = string
      static_action        = optional(bool,true)
      service_path_pattern = list(string)
      host_header_pattern  = list(string)
      })
    )
  default    = {}
}


variable "app_tg_type" {
  description = "Map of instance details"
  type = map(map(object({
        port                = number
	    protocol            = string
	    healthy_threshold   = number
	    unhealthy_threshold = number
	    path                = string
        target_type         = string
    }))
  )
  default    = {
    "COMMON" = {}
    "DEV"    = {}
    "PROD"   = {}
  }
}

variable "app_tg_type_PROD" {
  description = "Map of instance details"
  type = map(map(object({
        port                = number
        protocol            = string
        healthy_threshold   = number
        unhealthy_threshold = number
        path                = string
        target_type         = string
    }))
  )
  default    = {
	COMMON   = {}
    DEV    = {}
    PROD   = {}
  }
}

variable "sticky_session_type" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = map
  default     = {
    DEV       = "lb_cookie"
    PROD      = "lb_cookie"
  }
}


variable "sticky_session_enabled" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = map
  default     = {
    DEV       = "false"
    PROD      = "false"
  }
}

variable "sticky_session_duration" {
  description = "The type of EC2 Instances to run (e.g. t2.micro)"
  type        = map
  default     = {
    DEV       = 8600
    PROD      = 8600
  }
}


variable "app_target_group_arn" {
  type        = map
  description = "Target group Arn for Load Balancer"
  default     = {
    COMMON    = []
    DEV       = []
    PROD      = []
  }
}


######## LB Variables End




##### ASG Variables Start

variable "host_envprefix" {
  type        = map(any)
  description = "AWS accounts ids where stack infrastructure will be deployed"
  default     = {
    DEV       = "DEV"
    PROD     = "PRO"
  }
}


variable "source_market" {
  description = "The source market for company-name"
  type        = string
  default     = ""
}

variable "service_name" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "cpu" {
  type        = map(number)
  description = "AWS LB certificate required true or false"
  default = {
	frontend = 0.5
	backend  = 0.5
	middleware = 1
	interface = 1
  }
}



variable "memory" {
  type        = map(number)
  description = "AWS LB certificate required true or false"
  default = {
	frontend = 1
	backend  = 1
	middleware = 2
	interface = 2
  }
}

variable "container_name" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "container_port" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "assign_public_ip" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "create_time_out" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {
    frontend = "5m"
    middleware = "5m"
    backend = "5m"
    interface = "5m"
  }
}

variable "update_time_out" {
  type        = map(any)
  default = {
    frontend = "5m"
    middleware = "5m"
    backend = "5m"
    interface = "5m"
  }
}

variable "delete_time_out" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {
    frontend = "5m"
    middleware = "5m"
    backend = "5m"
    interface = "5m"
  }
}

variable "image_name" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "image_tag" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "log_group" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}

variable "log_stream_prefix" {
  type        = map(any)
  description = "AWS LB certificate required true or false"
  default = {}
}


##### VPC Selection

data "aws_vpc" "main" {
  provider = aws.ai_stack
  filter {
    name   = "tag:Name"
    values = ["*${var.env_type}"]
  }
}

##### Subnet Selection  Public

data "aws_subnets" "lb_subnets_public" {
  provider = aws.ai_stack
  filter {
    name   = "tag:Name"
    values = ["*${var.env_type}_Pub_${var.region}*"]
  }
}



##### Subnet Selection  Private

data "aws_subnets" "lb_subnets_private" {
  provider = aws.ai_stack
  filter {
    name   = "tag:Name"
    values = [""]
  }
}

##### Subnet Selection  Private

data "aws_subnets" "app_subnets" {
  provider = aws.ai_stack
  filter {
    name   = "tag:Name"
    values = [""]
  }
}

data "aws_subnets" "rds_subnets" {
  provider = aws.ai_stack
  filter {
    name   = "tag:Name"
    values = [""]
  }
}


locals {

  # Select VPC tag  for static(PREPROD, PROD) and Dynamic ( DEV/TEST )

  vpc_prefix = {
       DEV     = var.vpc_prefix
       PROD    = var.vpc_prefix
  }

  costcentre_tag = {
        DEV     = var.costcentre_id
		PROD    = var.costcentre_id
  }

  tg_env_specific = {
    DEV     = replace(lower(terraform.workspace), "dcp-", "")
    PROD    = lower(terraform.workspace)
  }
  tg_env  = local.tg_env_specific[var.env_type]



  default_tags = {
    Application     = var.Application
    EnvironmentType = var.env_type,
    EnvName         = terraform.workspace,
    CostCentre      = lookup(local.costcentre_tag, var.env_type),
  }

  app_target_group_arn = var.app_target_group_arn["COMMON"]

}

# Multiple secrets variable

#variable "secrets" {
#  type        = map(any)
#  description = "Secrets"
#  default     = {}
#}


variable "workspace_all_app_cidr" {
  type        = map(any)
  description = "workspace_all_app_cidr"
  default     = {}
}



variable "healthcheck_interval" {
  description = "Tg health check interval in PREPROD, PROD environment."
  type        = map(any)
  default = {
    DEV       = 30
    PROD      = 30
  }
}



variable "SSM_PARAM" {
  description = "SSM Parameter"
  type        = map
  default     = {
     DEV      = {}
     PROD     = {}
  }
}

variable "cluster_name" {
  description = "SSM Parameter"
  type        = map
  default     = {
     DEV      = "dev-cluster"
     PROD     = "prod-cluster"
  }
}

variable "container_insights" {
  description = "SSM Parameter"
  type        = map
  default     = {
     DEV      = "false"
     PROD     = "true"
  }
}



variable "user_data_custom" {
  description = "SSM Parameter"
  type        = map
  default     = {
     DEV      = false
     PROD     = false
  }
}

variable "vpc_endpoint_nics_private_ips" {
  type = map(list(string))
  description = "VPC Endpoint NICs Private IPs per environment"
  default = {}
}


variable "tg_matcher" {
  description = "The target group matcher"
  type        = string
  default     = "200"
}

variable "additional_app_alb" {
  description = "Additional app ALB"
  type        = map
  default     = {
     DEV      = {}
     PROD     = {}
  }
}

variable "secrets" {
  type        = map(any)
  description = "Secrets"
  default     = {}
}

variable "vpce_map" {
	type = map(string)
	description = "VPC Endpoint IP map"
	default = {}
}

variable "app_lb_listener_cert_enabled" {
  type = map
  description = "AWS LB certificate required true or false"
  default = {
    DEV 	    = "false"
    PROD      = "false"
  }
}

variable "disable_api_termination" {
  type        = bool
  description = "Protects manually ec2 deletion"
  default     = false
}

