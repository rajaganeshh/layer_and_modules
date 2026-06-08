# SecurityGroup

This module creates a security group with configurable ingress and egress rules supplied as a map.

## Usage

```hcl
module "security_group" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/SecurityGroup?ref=<release_tag>"

  name   = "my-service-sg"
  vpc_id = data.aws_vpc.default.id
  tags   = var.common_tags

  sg_rule_details = {
    http_in = {
      type        = "ingress"
      from_port   = 8080
      to_port     = 8080
      protocol    = "tcp"
      description = "Allow HTTP from ALB"
      source_sg_id = module.alb_sg.security_group_id
    }
    all_out = {
      type        = "egress"
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      description = "Allow all outbound"
      cidr_block  = ["0.0.0.0/0"]
    }
  }
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
| [aws_security_group.secGroup](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group_rule.ec2_sg_allow_sg_rules](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_name"></a> [name](#input\_name) | Security group Name | `string` | `""` | no |
| <a name="input_security_group_id"></a> [security\_group\_id](#input\_security\_group\_id) | VPC ID to create Security Group | `string` | `""` | no |
| <a name="input_sg_rule_details"></a> [sg\_rule\_details](#input\_sg\_rule\_details) | Security group rule: ingress or egress | `map` | `{}` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Security Group Tags | `map` | `{}` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID to create Security Group | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_server_security_group_id"></a> [server\_security\_group\_id](#output\_server\_security\_group\_id) | The ID of the Security Group |
<!-- END_TF_DOCS -->