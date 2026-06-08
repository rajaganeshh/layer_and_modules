# ALB

This module creates an Application Load Balancer with optional listeners on ports 80, 443, and 4431.
All listeners return a default 404 fixed response — traffic is routed by adding listener rules via the
[ALB_Listener_Rules](../ALB_Listener_Rules) module. It also creates Route53 alias records pointing
to the ALB, supporting cross-account setups where the hosted zone lives in a separate AWS account via the
`aws.dnszone` provider alias.

## Usage

```hcl
module "alb" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/ALB?ref=<release_tag>"

  providers = {
    aws         = aws
    aws.dnszone = aws.dnszone
  }

  lb_name            = "my-service-alb"
  lb_subnet_ids      = data.aws_subnets.private.ids
  lb_security_groups = [aws_security_group.alb.id]

  add_port_443_listener = true
  certificate_arn       = module.acm.acm_certificate_arn

  route53_zone_name = "example.company-marketcloud.net"
  lb_dns_name       = "my-service-alb"
  lb_dns_entry      = ["nonprod.", "prod."]
}
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 6.0 |
| <a name="provider_aws.dnszone"></a> [aws.dnszone](#provider\_aws.dnszone) | >= 6.0 |
| <a name="provider_null"></a> [null](#provider\_null) | n/a |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_lb.alb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb) | resource |
| [aws_lb_listener.port443](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_listener.port4431](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_listener.port80](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_listener_certificate.https_additional_certs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_certificate) | resource |
| [aws_route53_record.alb_wildcard](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [null_resource.octo_env](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [aws_route53_zone.selected](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/route53_zone) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_add_port_4431_listener"></a> [add\_port\_4431\_listener](#input\_add\_port\_4431\_listener) | (Optional) Whether to add a listener on port 4431 with a fixed response action that returns a 404 status code. | `bool` | `false` | no |
| <a name="input_add_port_443_listener"></a> [add\_port\_443\_listener](#input\_add\_port\_443\_listener) | (Optional) Whether to add a listener on port 443 with a fixed response action that returns a 404 status code. | `bool` | `false` | no |
| <a name="input_add_port_80_listener"></a> [add\_port\_80\_listener](#input\_add\_port\_80\_listener) | (Optional) Whether to add a listener on port 80 with a fixed response action that returns a 404 status code. | `bool` | `false` | no |
| <a name="input_additional_certificate_arn"></a> [additional\_certificate\_arn](#input\_additional\_certificate\_arn) | List of ARNs of additional SSL certificates to use for the HTTPS listener on port 443 only. This allows you to associate multiple certificates with the same listener, which can be useful for hosting multiple domains on the same load balancer. | `list(string)` | `[]` | no |
| <a name="input_certificate_arn"></a> [certificate\_arn](#input\_certificate\_arn) | ARN of the SSL certificate to use for the HTTPS listener on port 443 and 4431 | `string` | `""` | no |
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Common tags for resources | `map(any)` | `{}` | no |
| <a name="input_enable_deletion_protection"></a> [enable\_deletion\_protection](#input\_enable\_deletion\_protection) | Application LB deletion protection | `bool` | `false` | no |
| <a name="input_idle_timeout"></a> [idle\_timeout](#input\_idle\_timeout) | (Optional) Time in seconds that the connection is allowed to be idle. | `string` | `"60"` | no |
| <a name="input_lb_dns_entry"></a> [lb\_dns\_entry](#input\_lb\_dns\_entry) | List of DNS entry to use for the ALB. This will be used together with lb\_dns\_name for the DNS record created in the specified Route53 zone. For example, if you specify 'preprod', and your lb\_dns\_entry is '.my-alb', and your Route53 zone is 'example.com', the resulting DNS record will be 'preprodmy-alb.example.com'. | `set(string)` | `[]` | no |
| <a name="input_lb_dns_name"></a> [lb\_dns\_name](#input\_lb\_dns\_name) | The DNS name to use for the ALB. This will be used as the prefix together with lb\_dns\_entry for the DNS record created in the specified Route53 zone. For example, if you specify 'my-alb' and your Route53 zone is 'example.com', the resulting DNS record will be 'my-alb.example.com'. | `string` | `""` | no |
| <a name="input_lb_internal"></a> [lb\_internal](#input\_lb\_internal) | (Optional) If true, the LB will be internal | `bool` | `true` | no |
| <a name="input_lb_name"></a> [lb\_name](#input\_lb\_name) | (Optional) The name of the LB. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric characters or hyphens, and must not begin or end with a hyphen. If not specified, Terraform will autogenerate a name beginning with tf-lb. | `string` | `""` | no |
| <a name="input_lb_security_groups"></a> [lb\_security\_groups](#input\_lb\_security\_groups) | The subnets for the Loadbalancer | `set(string)` | <pre>[<br/>  ""<br/>]</pre> | no |
| <a name="input_lb_subnet_ids"></a> [lb\_subnet\_ids](#input\_lb\_subnet\_ids) | The subnets for the Loadbalancer | `set(string)` | <pre>[<br/>  ""<br/>]</pre> | no |
| <a name="input_lb_type"></a> [lb\_type](#input\_lb\_type) | (Optional) The type of load balancer to create. Possible values are application, gateway, or network. The default value is application. | `string` | `"application"` | no |
| <a name="input_route53_zone_name"></a> [route53\_zone\_name](#input\_route53\_zone\_name) | The DNS zone in which to create the ALB DNS records | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_alb_arn"></a> [alb\_arn](#output\_alb\_arn) | ARN of the Application Load Balancer created |
| <a name="output_alb_dns_name"></a> [alb\_dns\_name](#output\_alb\_dns\_name) | Internal DNS name of the Application Load Balancer created |
| <a name="output_hosted_zone"></a> [hosted\_zone](#output\_hosted\_zone) | ID of the Route 53 hosted zone associated with the ALB records |
| <a name="output_port4431_listener_arn"></a> [port4431\_listener\_arn](#output\_port4431\_listener\_arn) | ARN of the port 4431 listener if created, otherwise null |
| <a name="output_port443_listener_arn"></a> [port443\_listener\_arn](#output\_port443\_listener\_arn) | ARN of the port 443 listener if created, otherwise null |
| <a name="output_port80_listener_arn"></a> [port80\_listener\_arn](#output\_port80\_listener\_arn) | ARN of the port 80 listener if created, otherwise null |
| <a name="output_route53_record_names"></a> [route53\_record\_names](#output\_route53\_record\_names) | Fully qualified domain names created for the ALB |
<!-- END_TF_DOCS -->