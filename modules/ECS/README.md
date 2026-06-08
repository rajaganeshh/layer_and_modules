# ECS

> ⚠️ **Deprecated.** Use [ECS_Service](../ECS_Service) for all new ECS services — it provides the same core functionality plus OTEL, AppDynamics, eRes certificate, Orca, and Graviton support.

This module creates a Fargate ECS task definition and ECS service attached to a load balancer target group.

## Usage

```hcl
module "ecs" {
  source = "git@github.com:company-org/company-market-iac-modules.git//Source/ECS?ref=<release_tag>"

  service_name          = "my-service"
  cpu                   = 512
  memory                = 1024
  execution_role_arn    = aws_iam_role.execution.arn
  task_role_arn         = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name      = "my-service"
    image     = "123456789.dkr.ecr.eu-west-1.amazonaws.com/my-service:latest"
    essential = true
    portMappings = [{ containerPort = 8080 }]
  }])

  ecs_cluster_id      = module.cluster.ecs_cluster_id
  lb_target_group_arn = module.target_group.target_group_arn
  container_name      = "my-service"
  container_port      = 8080
  security_group_id   = aws_security_group.ecs.id
  subnet_ids          = data.aws_subnets.private.ids
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
| [aws_ecs_service.ecs_services](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service) | resource |
| [aws_ecs_task_definition.ecs_task_definition](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition) | resource |
| [aws_iam_role_policy_attachment.ecs_task_execution_ecr_pull_only](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.ecs_task_execution_ecr_read_only](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_assign_public_ip"></a> [assign\_public\_ip](#input\_assign\_public\_ip) | n/a | `bool` | `false` | no |
| <a name="input_container_definitions"></a> [container\_definitions](#input\_container\_definitions) | n/a | `string` | n/a | yes |
| <a name="input_container_name"></a> [container\_name](#input\_container\_name) | n/a | `string` | n/a | yes |
| <a name="input_container_port"></a> [container\_port](#input\_container\_port) | n/a | `number` | n/a | yes |
| <a name="input_cpu"></a> [cpu](#input\_cpu) | n/a | `number` | n/a | yes |
| <a name="input_create_time_out"></a> [create\_time\_out](#input\_create\_time\_out) | n/a | `string` | `"20m"` | no |
| <a name="input_delete_time_out"></a> [delete\_time\_out](#input\_delete\_time\_out) | n/a | `string` | `"20m"` | no |
| <a name="input_desired_count"></a> [desired\_count](#input\_desired\_count) | n/a | `number` | `1` | no |
| <a name="input_ecs_cluster_id"></a> [ecs\_cluster\_id](#input\_ecs\_cluster\_id) | n/a | `string` | n/a | yes |
| <a name="input_enable_execute_command"></a> [enable\_execute\_command](#input\_enable\_execute\_command) | n/a | `bool` | `false` | no |
| <a name="input_execution_role_arn"></a> [execution\_role\_arn](#input\_execution\_role\_arn) | n/a | `string` | n/a | yes |
| <a name="input_force_new_deployment"></a> [force\_new\_deployment](#input\_force\_new\_deployment) | Provide true or false for force new deployment | `bool` | `false` | no |
| <a name="input_lb_target_group_arn"></a> [lb\_target\_group\_arn](#input\_lb\_target\_group\_arn) | n/a | `string` | n/a | yes |
| <a name="input_memory"></a> [memory](#input\_memory) | n/a | `number` | n/a | yes |
| <a name="input_security_group_id"></a> [security\_group\_id](#input\_security\_group\_id) | n/a | `string` | n/a | yes |
| <a name="input_service_name"></a> [service\_name](#input\_service\_name) | n/a | `string` | n/a | yes |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | n/a | `list(string)` | n/a | yes |
| <a name="input_task_role_arn"></a> [task\_role\_arn](#input\_task\_role\_arn) | n/a | `string` | `null` | no |
| <a name="input_update_time_out"></a> [update\_time\_out](#input\_update\_time\_out) | n/a | `string` | `"20m"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
