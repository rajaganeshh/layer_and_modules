################  ECR

 data "template_file" "custom_policy_frontend_repo" {
   template = file("${path.module}/policies/custom_policy_frontend_repo.json")
   vars = {
     account = var.aws_account_id
   }
 }
  
  
 data "template_file" "custom_policy_frontend_lifecycle" {
   template = file("${path.module}/policies/custom_policy_frontend_lifecycle.json")
 }
  

 data "template_file" "custom_policy_backend_repo" {
   template = file("${path.module}/policies/custom_policy_backend_repo.json")
   vars = {
     account = var.aws_account_id
   }
 }
  

 data "template_file" "custom_policy_backend_lifecycle" {
   template = file("${path.module}/policies/custom_policy_backend_lifecycle.json")
 }
    

 data "template_file" "custom_policy_middleware_repo" {
   template = file("${path.module}/policies/custom_policy_middleware_repo.json")
   vars = {
     account = var.aws_account_id
   }
 }
  
  
 data "template_file" "custom_policy_middleware_lifecycle" {
   template = file("${path.module}/policies/custom_policy_middleware_lifecycle.json")
 }


 data "template_file" "custom_policy_interface_repo" {
   template = file("${path.module}/policies/custom_policy_interface_repo.json")
   vars = {
     account = var.aws_account_id
   }
 }
  
  
 data "template_file" "custom_policy_interface_lifecycle" {
   template = file("${path.module}/policies/custom_policy_interface_lifecycle.json")
 } 