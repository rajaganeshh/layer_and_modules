# IAM

This module creates an IAM role with a configurable assume-role policy, optional EC2 instance profile,
custom inline/managed policies, and direct managed policy attachments.

## Usage

```hcl
module "iam_role" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/IAM?ref=<release_tag>"

  role_name           = "my-service-role"
  assume_role_policy  = data.aws_iam_policy_document.assume.json

  iam_policy = {
    s3_access = {
      name        = "my-service-s3-policy"
      description = "Allow read access to the artefacts bucket"
      policy      = data.aws_iam_policy_document.s3.json
    }
  }
}
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 6.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_instance_profile.serive_iam_role_instance_profile](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_instance_profile) | resource |
| [aws_iam_policy.iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.policy_attach](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.policy_attach_direct](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_assume_role_policy"></a> [assume\_role\_policy](#input\_assume\_role\_policy) | assume ploicy for the role | `string` | `""` | no |
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Number of Policies to be attached | `map` | `{}` | no |
| <a name="input_iam_policy"></a> [iam\_policy](#input\_iam\_policy) | Number of Policies to be attached | `map` | `{}` | no |
| <a name="input_instance_profile_enabled"></a> [instance\_profile\_enabled](#input\_instance\_profile\_enabled) | create the instance profile | `bool` | `false` | no |
| <a name="input_max_session_duration"></a> [max\_session\_duration](#input\_max\_session\_duration) | Maximum session duration (in seconds) that you want to set for the specified role. If you do not specify a value for this setting, the default maximum of one hour is applied. This setting can have a value from 1 hour to 12 hours | `number` | `3600` | no |
| <a name="input_policy_attach_role"></a> [policy\_attach\_role](#input\_policy\_attach\_role) | Number of Policies to be attached | `list(string)` | `[]` | no |
| <a name="input_role_name"></a> [role\_name](#input\_role\_name) | Name of the IAM role | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_iam_arn"></a> [iam\_arn](#output\_iam\_arn) | n/a |
| <a name="output_instance_profile_arn"></a> [instance\_profile\_arn](#output\_instance\_profile\_arn) | n/a |
<!-- END_TF_DOCS -->