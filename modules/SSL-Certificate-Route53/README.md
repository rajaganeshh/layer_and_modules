# SSL-Certificate-Route53

This module issues an ACM certificate for a domain (automatically adding a wildcard SAN `*.domain`) and validates it
via DNS records in a Route53 hosted zone. It supports cross-account setups where the hosted zone lives in a separate
AWS account via the `aws.dnszone` provider alias.

> For more flexible certificate issuance (custom SANs, EMAIL validation, external DNS), use [ACM](../ACM) instead.

## Usage

```hcl
module "ssl_cert" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/SSL-Certificate-Route53?ref=<release_tag>"

  providers = {
    aws         = aws
    aws.dnszone = aws.dnszone
  }

  domain_name           = "my-service.company-marketcloud.net"
  route53_zone_name     = "company-marketcloud.net"
  route53_private_zone  = false
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

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_acm_certificate.cert](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate) | resource |
| [aws_route53_record.example](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_zone.example](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/route53_zone) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_domain_name"></a> [domain\_name](#input\_domain\_name) | domain name for the certificate | `string` | n/a | yes |
| <a name="input_route53_private_zone"></a> [route53\_private\_zone](#input\_route53\_private\_zone) | Indicates whether this is a private hosted zone | `bool` | `false` | no |
| <a name="input_route53_zone_name"></a> [route53\_zone\_name](#input\_route53\_zone\_name) | n/a | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | n/a | `map` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_certificate_arn"></a> [certificate\_arn](#output\_certificate\_arn) | Certificate value for ALB |
<!-- END_TF_DOCS -->
