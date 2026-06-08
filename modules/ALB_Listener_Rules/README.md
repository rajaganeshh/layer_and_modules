# ALB_Listener_Rules

This module adds a listener rule to an existing ALB listener created by [ALB](../ALB).
Exactly one rule type is created per module invocation, selected by a boolean flag:

| Flag            | Rule behaviour                                                                                                                         |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `host_forward`  | Forwards matching host headers (and optionally path patterns) to a weighted pair of target groups — useful for blue/green deployments. |
| `host_path`     | Forwards matching path patterns to a weighted pair of target groups.                                                                   |
| `static_action` | Simple forward to a single target group, matching by optional host header and/or path pattern.                                         |
| `host_redirect` | Redirects a matching host header to HTTPS port 443.                                                                                    |

## Usage

```hcl
# Forward by host header — typical Blue/Green deployment
module "listener_rule" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/ALB_Listener_Rules?ref=<release_tag>"

  lb_listener_arn = module.alb.port443_listener_arn
  priority        = 10
  host_forward    = true

  service_host_header = ["my-service.example.company-marketcloud.net"]

  target_group_arn        = module.target_group_blue.target_group_arn
  target_group_arn_weight = 100

  target_group_arn_green        = module.target_group_green.target_group_arn
  target_group_arn_green_weight = 0
}

# Simple static forward by path pattern
module "listener_rule_api" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/ALB_Listener_Rules?ref=<release_tag>"

  lb_listener_arn = module.alb.port443_listener_arn
  priority        = 20
  static_action   = true

  service_host_header  = ["my-service.example.company-marketcloud.net"]
  service_path_pattern = ["/api/*"]
  target_group_arn     = module.target_group.target_group_arn
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
| [aws_lb_listener_rule.host_forward](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule) | resource |
| [aws_lb_listener_rule.path_pattern](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule) | resource |
| [aws_lb_listener_rule.redirect_http_to_https](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule) | resource |
| [aws_lb_listener_rule.static](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Common tags for resources | `map(any)` | `{}` | no |
| <a name="input_host_forward"></a> [host\_forward](#input\_host\_forward) | n/a | `bool` | `false` | no |
| <a name="input_host_path"></a> [host\_path](#input\_host\_path) | n/a | `bool` | `false` | no |
| <a name="input_host_redirect"></a> [host\_redirect](#input\_host\_redirect) | n/a | `bool` | `false` | no |
| <a name="input_lb_listener_arn"></a> [lb\_listener\_arn](#input\_lb\_listener\_arn) | the name of the load balancer | `string` | `""` | no |
| <a name="input_lb_sticky_duration"></a> [lb\_sticky\_duration](#input\_lb\_sticky\_duration) | Alb rules for the listener | `number` | `86400` | no |
| <a name="input_lb_sticky_enabled"></a> [lb\_sticky\_enabled](#input\_lb\_sticky\_enabled) | Alb stickiness enabled or disabled | `bool` | `false` | no |
| <a name="input_priority"></a> [priority](#input\_priority) | The subnets for the Loadbalancer | `number` | `null` | no |
| <a name="input_service_host_header"></a> [service\_host\_header](#input\_service\_host\_header) | The subnets for the Loadbalancer | `list(string)` | `[]` | no |
| <a name="input_service_host_redirect"></a> [service\_host\_redirect](#input\_service\_host\_redirect) | The subnets for the Loadbalancer | `string` | `""` | no |
| <a name="input_service_path_pattern"></a> [service\_path\_pattern](#input\_service\_path\_pattern) | Alb rules for the listener | `list(string)` | `[]` | no |
| <a name="input_static_action"></a> [static\_action](#input\_static\_action) | Alb stickiness enabled or disabled | `bool` | `false` | no |
| <a name="input_target_group_arn"></a> [target\_group\_arn](#input\_target\_group\_arn) | Application LB type Enable | `string` | `""` | no |
| <a name="input_target_group_arn_green"></a> [target\_group\_arn\_green](#input\_target\_group\_arn\_green) | Application LB type Enable | `string` | `""` | no |
| <a name="input_target_group_arn_green_weight"></a> [target\_group\_arn\_green\_weight](#input\_target\_group\_arn\_green\_weight) | Application LB type Enable | `number` | `null` | no |
| <a name="input_target_group_arn_weight"></a> [target\_group\_arn\_weight](#input\_target\_group\_arn\_weight) | Application LB type Enable | `number` | `100` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
