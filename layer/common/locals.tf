locals {

 domain   = var.env_type == "PROD" ? "prod.domaint" : "nonprod.domain"

# IAM role Attach

  custom_roles_application = {
    ecs_role      = { 
	   role1 = { name = "simon_${lower(terraform.workspace)}_ecs_custom_policy",  description="simon_${lower(terraform.workspace)}_ecs_custom_policy",  policy=data.template_file.custom_policy_ecs.rendered }
	}
	ecs_task_role = { 
	   role1 = { name = "simon_${lower(terraform.workspace)}_task_custom_policy", description="simon_${lower(terraform.workspace)}_task_custom_policy",  policy=data.template_file.custom_policy_task.rendered }
	}
	lambda_role   = { 
	   role1 = { name = "simon_${lower(terraform.workspace)}_lambda_custom_policy", description="simon_${lower(terraform.workspace)}_lambda_custom_policy",policy=data.template_file.custom_policy_lambda.rendered }
    }
  auroradb_role = {}  
  bedrock_role   = { 
	   role1 = { name = "simon_${lower(terraform.workspace)}_bedrock_custom_policy", description="simon_${lower(terraform.workspace)}_bedrock_custom_policy",policy=data.template_file.custom_policy_bedrock.rendered }
    }
  }

  policy_roles_attach = {
    cloudwatch            = data.aws_iam_policy.cloudwatch.arn
	  s3readonlyaccess      = data.aws_iam_policy.s3readonlyaccess.arn
	  ssminstancecore       = data.aws_iam_policy.ssminstancecore.arn
	  ecs_execution_attach  = data.aws_iam_policy.ecs_execution_attach.arn
    auroradb_policy       = data.aws_iam_policy.auroradb_policy.arn
    bedrock_full          = data.aws_iam_policy.bedrock_full.arn
  }

  assume_policy = {
    ecs_role_assume_policy      = data.aws_iam_policy_document.task_assume_policy.json
	  ecs_task_role_assume_policy = data.aws_iam_policy_document.task_assume_policy.json
	  lambda_role_assume_policy   = data.aws_iam_policy_document.lambda_assume_policy.json
    auroradb_role_assume_policy   = data.aws_iam_policy_document.aurora_monitoring_policy.json
    bedrock_role_assume_policy   = data.aws_iam_policy_document.bedrock_assume_policy.json
  }
  
    db_sg_rules = [data.aws_vpc.main.cidr_block]

  ##### LB Rules
    lb_rules = var.env_type == "PROD" ? var.lb_sg_rules_private_PROD : var.lb_sg_rules_private


    dynamic_cidr_all_app_lb = { for k, a in local.lb_rules : k => merge(a,{
     cidr_block = a.cidr_block == tolist(["dynamic_vpc_cidr"]) ? local.db_sg_rules : a.cidr_block
     	 })
        }
  
 app_sg_type                     = {
		DEV                       =  var.app_sg_type_DEV
		PROD                      =  var.app_sg_type_PROD
 }




 ### Dynamic VPC CIDR for app Security Group
 
    dynamic_cidr_all_app = { for k, a in local.app_sg_type[var.env_type] : k => merge(a,{
     cidr_block = a.cidr_block == tolist(["dynamic_vpc_cidr"]) ? local.db_sg_rules : a.cidr_block
     	 })
        }
 
    dynamic_cidr = { for k, a in local.dynamic_cidr_all_app : k => merge(a,{
     cidr_block = a.cidr_block == tolist(["workspace_all_app_cidr"]) ? lookup(var.workspace_all_app_cidr, terraform.workspace) : a.cidr_block
     	 })
        }
 
  ### Dynamic VPC CIDR for DB Security Group
 
    dynamic_cidr_all_db = { for k, a in var.db_sg_type : k => merge(a,{
     cidr_block = a.cidr_block == tolist(["dynamic_vpc_cidr"]) ? local.db_sg_rules : a.cidr_block
     	 })
        }
 
  ### Dynamic VPC CIDR for bedrock Security Group
 
    dynamic_cidr_all_bg = { for k, a in var.bedrock_sg_type : k => merge(a,{
     cidr_block = a.cidr_block == tolist(["dynamic_vpc_cidr"]) ? local.db_sg_rules : a.cidr_block
     	 })
        }

  locals {
  	assume_role_accounts = var.env_type == "prod" ? [
    		"arn:aws:iam::XXXX:root"
  		] : [
    	"arn:aws:iam::XXXXX:root",
    	"arn:aws:iam::XXXX:root",
    	"arn:aws:iam::XXX:root"
  		]
	}
  # Tags
  common_tags = merge(var.tags, { CostOwnerTeam = var.CostOwnerTeam, SupportTeam = var.SupportTeam[var.env_type] })

}     ##### End of Locals


### new-item -path .\secrets\global_variables.tf -ItemType SymbolicLink -value .\global_variables.tf
### new-item -path .\common\providers.tf -ItemType SymbolicLink -value .\providers.tf
