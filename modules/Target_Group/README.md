# Target_Group

This module creates an ALB or NLB target group with configurable health check settings, stickiness, and deregistration delay.

## Usage

```hcl
module "target_group" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/Target_Group?ref=<release_tag>"

  tg_name     = "my-service-tg"
  tg_port     = 8080
  tg_protocol = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  tg_path               = "/health"
  tg_healthy_threshold   = 2
  tg_unhealthy_threshold = 3
  tg_health_interval    = 30
  tg_health_timeout     = 5
  tg_matcher            = "200"

  common_tags = var.common_tags
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

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_lb_target_group.lb_target_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Name tag for NLB resources | `map` | `{}` | no |
| <a name="input_deregistration_delay"></a> [deregistration\_delay](#input\_deregistration\_delay) | (Optional) Provides De-registration delay in seconds max 3600 | `number` | `300` | no |
| <a name="input_hc_protocol"></a> [hc\_protocol](#input\_hc\_protocol) | The target group protocol | `string` | `null` | no |
| <a name="input_target_type"></a> [target\_type](#input\_target\_type) | The target group target type | `string` | `"instance"` | no |
| <a name="input_tg_health_interval"></a> [tg\_health\_interval](#input\_tg\_health\_interval) | (Optional) Approximate amount of time, in seconds, between health checks of an individual target. The range is 5-300. | `number` | `null` | no |
| <a name="input_tg_health_timeout"></a> [tg\_health\_timeout](#input\_tg\_health\_timeout) | (optional) Amount of time, in seconds, during which no response from a target means a failed health check. The range is 2–120 seconds. For target groups with a protocol of HTTP, the default is 6 seconds. For target groups with a protocol of TCP, TLS or HTTPS, the default is 10 seconds | `number` | `null` | no |
| <a name="input_tg_healthy_threshold"></a> [tg\_healthy\_threshold](#input\_tg\_healthy\_threshold) | The target group health check threshold | `number` | `null` | no |
| <a name="input_tg_matcher"></a> [tg\_matcher](#input\_tg\_matcher) | The target group matcher | `string` | `"200"` | no |
| <a name="input_tg_name"></a> [tg\_name](#input\_tg\_name) | the name of the target\_group | `string` | `""` | no |
| <a name="input_tg_path"></a> [tg\_path](#input\_tg\_path) | The target group health check path | `string` | `null` | no |
| <a name="input_tg_port"></a> [tg\_port](#input\_tg\_port) | the target group port | `number` | `null` | no |
| <a name="input_tg_preserve_client_ip"></a> [tg\_preserve\_client\_ip](#input\_tg\_preserve\_client\_ip) | (Optional) Whether client IP preservation is enabled. | `string` | `null` | no |
| <a name="input_tg_protocol"></a> [tg\_protocol](#input\_tg\_protocol) | The target group protocol | `string` | `""` | no |
| <a name="input_tg_slow_start"></a> [tg\_slow\_start](#input\_tg\_slow\_start) | (Optional) Amount time for targets to warm up before the load balancer sends them a full share of requests. The range is 30-900 seconds or 0 to disable. The default value is 0 seconds. | `number` | `null` | no |
| <a name="input_tg_sticky_duration"></a> [tg\_sticky\_duration](#input\_tg\_sticky\_duration) | The target group sticky duration | `number` | `86400` | no |
| <a name="input_tg_sticky_enabled"></a> [tg\_sticky\_enabled](#input\_tg\_sticky\_enabled) | The target group sticky enabled | `bool` | `false` | no |
| <a name="input_tg_sticky_type"></a> [tg\_sticky\_type](#input\_tg\_sticky\_type) | The target group sticky type | `string` | `""` | no |
| <a name="input_tg_unhealthy_threshold"></a> [tg\_unhealthy\_threshold](#input\_tg\_unhealthy\_threshold) | The target group health check unhealthy threshold | `number` | `null` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | The vpc id | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_tg_arn"></a> [tg\_arn](#output\_tg\_arn) | n/a |
| <a name="output_tg_arn_suffix"></a> [tg\_arn\_suffix](#output\_tg\_arn\_suffix) | n/a |
| <a name="output_tg_id"></a> [tg\_id](#output\_tg\_id) | n/a |
<!-- END_TF_DOCS -->
