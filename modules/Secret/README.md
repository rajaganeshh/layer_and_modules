# AWS Secrets Manager Terraform Module

Terraform module to create [Amazon Secrets Manager](https://aws.amazon.com/secrets-manager/) resources.

AWS Secrets Manager helps you protect secrets needed to access your applications, services, and IT resources. The service enables you to easily rotate, manage, and retrieve database credentials, API keys, and other secrets throughout their lifecycle.

## Examples

Check the [examples](./example) folder where you can see the complete compilation of snippets to create secrets for plain texts, keys/values and binary data.

## Versions

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 5.0 |
| <a name="terraform"></a> [terraform](#terraform) | >= 1.1.0 |


## Resources

| Name | Type |
|------|------|
| [aws_secretsmanager_secret.secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |
| [aws_secretsmanager_secret_rotation.secret_rotation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_name"></a> [name](#input\_name) | Name of the secrets manager. | `string` | null | conditional (conflicts with <b><u><i>name_prefix</b></u></i>) |
| <a name="input_name_prefix"></a> [name\_prefix](#name\_prefix) | Prefix name of the secrets manager. | `string` | null | conditional (conflicts with <b><u><i>name</b></u></i>) |
| <a name="input_description"></a> [description](#input\_description) | Description for the secrets manager. | `string` | null | no | 
| <a name="input_kms_key_id"></a> [kms\_key\_id](#input\_kms\_key\_id) | KMS Key Id or ARN for the secrets manager. | `string` | null | no |
| <a name="input_policy"></a> [policy](#input\_policy) | Policy for the secrets manager. | `string` | null | no |
| <a name="input_recovery_window_in_days"></a> [recovery\_window\_in\_days](#input\_recovery\_window\_in\_days) | Specifies the number of days that AWS Secrets Manager waits before it can delete the secret. This value can be 0 to force deletion without recovery or range from 7 to 30 days. | `number` | `30` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Specifies a key-value map of user-defined tags that are attached to the secrets manager. | `any` | `{}` | no |
| <a name="input_replica"></a> [replica](#input\_replica) | Configuration block to support secret replication to the secrets manager. [See details below](#input_configutation_replica). | `any` | `{}` | no |
| [secret_string](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_PutSecretValue.html#SecretsManager-PutSecretValue-request-SecretString) | Specifies text data that you want to encrypt and store in secret version. | `string` | null | conditional (conflicts with <b><u><i>secret_key_value or secret_binary</b></u></i>) |
| [secret_key_value](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_PutSecretValue.html#SecretsManager-PutSecretValue-request-SecretString) | Specifies key value data that you want to encrypt and store in secret version. | `any` | `{}` | conditional (conflicts with <b><u><i>secret_string or secret_binary</b></u></i>) |
| [secret_binary](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_PutSecretValue.html#SecretsManager-PutSecretValue-request-SecretBinary) | Specifies binary data that you want to encrypt and store in secret version. | `string` | null | conditional (conflicts with <b><u><i>secret_key_value or secret_string</b></u></i>) |
| <a name="input_rotation"></a> [rotation](#input\_rotation) | To enable automatic secret rotation, the Secrets Manager service requires usage of a Lambda function. [See details below](#input\_configutation\_rotation). | `any` | `{}` | no |

### <a name="input_configutation_replica"></a> replica
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_region"></a> [region](#input\_region) | KMS Key Id or ARN for the secrets manager. | `string` | null | yes |
| <a name="input_kms_key_id"></a> [kms\_key\_id](#input\_kms\_key\_id) | Specifies the number of days between automatic scheduled rotations of the secrets manager. | `number` | null | no |

### <a name="input_configutation_rotation"></a> rotation
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_rotation_lambda_arn"></a> [rotation\_lambda\_arn](#input\_rotation\_lambda\_arn) | Specifies the ARN of the Lambda function that can rotate the secret of the secret rotation. | `string` | null | yes |
| <a name="input_automatically_after_days"></a> [automatically\_after\_days](#input\_automatically\_after\_days) | Specifies the number of days between automatic scheduled rotations of the secret rotation. | `number` | `30` | no |

<br>

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_secret_id"></a> [secret\_id](#output\_secret\_id) | Secret id map |
| <a name="output_secret_arn"></a> [secret\_arn](#output\_secret\_arn) | Secret arn map |
| <a name="output_secret_string"></a> [secret\_string](#output\_secret\_string) | Secret string map |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.15 |
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
| [aws_secretsmanager_secret.secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Map of secrets to keep in AWS Secrets Manager | `any` | `{}` | no |
| <a name="input_secret"></a> [secret](#input\_secret) | Map of secrets to keep in AWS Secrets Manager | `any` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_secret_arn"></a> [secret\_arn](#output\_secret\_arn) | Secrets arn |
| <a name="output_secret_id"></a> [secret\_id](#output\_secret\_id) | Secret id |
<!-- END_TF_DOCS -->