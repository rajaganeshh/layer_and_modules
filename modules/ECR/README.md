# ECR

> ⚠️ **Deprecated.** ECR repositories should now be declared in the [company-market-sdlc-ecr](https://github.com/company-org/company-market-sdlc-ecr) repository. 
> Do not use this module for new ECR repositories.

This module creates an Amazon ECR repository with a repository access policy and a lifecycle policy to manage image retention.

## Usage

```hcl
module "ecr" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/ECR?ref=<release_tag>"

  ecr_repo_name = "my-service"
  mutability    = "MUTABLE"

  ecr_repo_lifecycle_policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 3.36 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 3.36 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_ecr_repository](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository) | resource |
| [aws_ecr_repository_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository_policy) | resource |
| [aws_ecr_lifecycle_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_lifecycle_policy) | resource |


## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_ecr_repo_name"></a> [ecr\_repo\_name](#input\_ecr\_repo\_name) | Name of ECR Repository | `string` | `""` | yes |
| <a name="input_mutability"></a> [mutability](#input\_mutability) | Image Tag Mutability | `string` | `""` | yes |
| <a name="input_ecr_repo_policy"></a> [ecr\_repo\_policy](#input\_ecr\_repo\_policy) | The name of the policy document for ECR Repository | `string` | `""` | no |
| <a name="input_application"></a> [application](#input\_application) | Repo Tag application | `string` | `""` | yes |
| <a name="input_ecr_repo_lifecycle_policy"></a> [ecr\_repo\_lifecycle\_policy](#input\_ecr\_repo\_lifecycle\_policy) | The name of the lifecycle policy document for ECR Repository | `string` | `""` | no |

## Examples

[Example](../../Examples/Re-ECR/)

<!-- END_TF_DOCS -->