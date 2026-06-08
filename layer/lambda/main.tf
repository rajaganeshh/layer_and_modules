
module "lambda_function" {

  providers = {
    aws = aws.ai_stack
  }

  source                         = "git@github.com:company-org/company-name-iac-modules-lambda.git?ref=develop"

  filename                       = var.lambda_function_file
  function_name                  = "${var.source_market}-${lower(terraform.workspace)}-${lookup(var.function_name, var.app_type)}"
  description                    = lookup(var.description,var.app_type)
  memory_size                    = lookup(var.memory_size, var.app_type)
  handler                        = lookup(var.handler,var.app_type)
  role_arn                       = "arn:aws:iam::${var.aws_account_id}:role/mim_${lower(terraform.workspace)}_lambda_role"
  runtime                        = var.runtime
  architectures                  = lookup(var.architectures, var.app_type)
  timeout                        = var.runtime_timeout[var.app_type]
  timeouts                       = var.timeouts[var.app_type]
  lambda_rollback                = var.lambda_publish
  reserved_concurrency           = lookup(var.reserved_concurrency, var.app_type)
  vpc_subnet_ids                 = data.aws_subnets.lb_subnets_private.ids
  vpc_security_group_ids         = [data.aws_security_group.app_sg.id]
  tracing_mode                   = lookup(var.tracing_mode, var.app_type)
  logging_log_format             = var.log_format
  logging_log_group              = "/lambda/${var.app_type}"
  logging_application_log_level  = lookup(var.log_level, var.app_type)
  logging_system_log_level       = lookup(var.log_level, var.app_type)
  layers                         = local.lambda_layers_app[var.app_type]
  env_vars                       = local.lambda_secret[var.app_type]
  common_tags                    = merge(local.common_tags,
                                         { Name = "${var.source_market}-${lower(terraform.workspace)}-${lookup(var.function_name, var.app_type)}" })

}