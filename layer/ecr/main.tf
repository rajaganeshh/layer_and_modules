# ECR


module "ecr" {

  providers                       = {
    aws                           = aws.ai_stack
  }

  for_each = local.ecr_repos

  source = "git@github.com:company-org/company-name-iac-modules.git//Source/ECR?ref=main"
  
  ecr_repo_name  			= each.value.name
  mutability     			= each.value.mutability
  scan_on_push   			= each.value.scan_on_push
  ecr_repo_policy			= each.value.ecr_repo_policy
  ecr_repo_lifecycle_policy = each.value.ecr_repo_lifecycle_policy
 
  additional_tags           = var.tags
}


