# SecurityGroup_Rules

This module adds security group rules to an existing security group.
Use it to attach additional rules post-creation without managing the security group itself — for example,
to allow access between two modules that create their own security groups.

## Usage

```hcl
module "sg_rules" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/SecurityGroup_Rules?ref=<release_tag>"

  security_group_id = module.rds.rds_security_group_id

  sg_rule_details = {
    lambda_in = {
      type        = "ingress"
      from_port   = 1433
      to_port     = 1433
      protocol    = "tcp"
      description = "Allow SQL Server access from Lambda"
    }
  }

  source_sg_default = module.lambda_sg.security_group_id
}
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_security_group_rule.ec2_sg_allow_sg_rules](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_security_group_id"></a> [security\_group\_id](#input\_security\_group\_id) | VPC ID to create Security Group | `string` | `""` | no |
| <a name="input_sg_rule_details"></a> [sg\_rule\_details](#input\_sg\_rule\_details) | Security group rule: ingress or egress | `map` | `{}` | no |
| <a name="input_source_sg_default"></a> [source\_sg\_default](#input\_source\_sg\_default) | VPC ID to create Security Group | `string` | `null` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->