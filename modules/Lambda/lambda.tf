
resource "aws_lambda_layer_version" "lambda_layer" {
  for_each             = var.lambda_layers
  filename             = each.value.filename
  layer_name           = each.value.layer_name
  description          = each.value.description
  compatible_runtimes  = each.value.compatible_runtimes
  license_info         = each.value.license_info
  source_code_hash     = filebase64sha256(each.value.filename)
}

locals {
  #lambda_merged_layers = [for l in aws_lambda_layer_version.lambda_layer : l.value.arn]
  # Optionally merge with var.layers if you want to add static layers:
   lambda_merged_layers = length(var.lambda_layers) > 0 ? concat([for l in aws_lambda_layer_version.lambda_layer : l.value.arn], var.layers) : var.layers
}

resource "aws_lambda_function" "lambda_function_file" {
  count            = var.filename != "" ? 1 : 0
  filename         = var.filename
  function_name    = var.function_name
  description      = var.description
  memory_size      = var.memory_size
  handler          = var.handler
  role             = var.role_arn
  runtime          = var.runtime
  architectures    = var.architectures
  timeout          = var.timeout
  source_code_hash = filebase64sha256(var.filename)
  tags             = var.common_tags
  publish                        = !(var.lambda_rollback) ? var.publish_version : false
  reserved_concurrent_executions = var.reserved_concurrency
  layers           = local.lambda_merged_layers

  # ...existing dynamic blocks...
  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null && var.vpc_security_group_ids != null ? [true] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }
  
  environment {
    variables = var.env_vars
  }

  dynamic "tracing_config" {
    for_each = var.tracing_mode == null ? [] : [true]
    content {
      mode = var.tracing_mode
    }
  }
  dynamic "logging_config" {
    for_each = var.logging_log_format != null ? [true] : []
    content {
      log_group             = var.logging_log_group == null ? null : var.logging_log_group
      log_format            = var.logging_log_format
      application_log_level = var.logging_log_format == "Text" ? null : var.logging_application_log_level
      system_log_level      = var.logging_log_format == "Text" ? null : var.logging_system_log_level
    }
  }
  dynamic "dead_letter_config" {
    for_each = var.lambda_dlq_arn != "" ? [true] : []
    content {
      target_arn = var.lambda_dlq_arn
    }
  }
  dynamic "timeouts" {
    for_each = length(var.timeouts) > 0 ? [true] : []
    content {
      create = try(var.timeouts.create, null)
      update = try(var.timeouts.update, null)
      delete = try(var.timeouts.delete, null)
    }
  }
}

# Lambda via S3
resource "aws_lambda_function" "lambda_function_s3" {
  count = var.s3_bucket != "" && var.s3_key != "" ? 1 : 0
  s3_bucket        = var.s3_bucket
  s3_key           = var.s3_key
  s3_object_version = var.s3_object_version
  function_name    = var.function_name
  description      = var.description
  memory_size      = var.memory_size
  handler          = var.handler
  role             = var.role_arn
  runtime          = var.runtime
  architectures    = var.architectures
  timeout          = var.timeout
  source_code_hash = var.s3_source_code_hash
  tags             = var.common_tags
  publish                        = !(var.lambda_rollback) ? var.publish_version : false
  reserved_concurrent_executions = var.reserved_concurrency
  layers           = local.lambda_merged_layers

  # ...existing dynamic blocks...
  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null && var.vpc_security_group_ids != null ? [true] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }
  dynamic "environment" {
    for_each = length(keys(var.env_vars)) == 0 ? [] : [true]
    content {
      variables = environment.value
    }
  }
  dynamic "tracing_config" {
    for_each = var.tracing_mode == null ? [] : [true]
    content {
      mode = var.tracing_mode
    }
  }
  dynamic "logging_config" {
    for_each = var.logging_log_format != null ? [true] : []
    content {
      log_group             = var.logging_log_group == null ? null : var.logging_log_group
      log_format            = var.logging_log_format
      application_log_level = var.logging_log_format == "Text" ? null : var.logging_application_log_level
      system_log_level      = var.logging_log_format == "Text" ? null : var.logging_system_log_level
    }
  }
  dynamic "dead_letter_config" {
    for_each = var.lambda_dlq_arn != "" ? [true] : []
    content {
      target_arn = var.lambda_dlq_arn
    }
  }
  dynamic "timeouts" {
    for_each = length(var.timeouts) > 0 ? [true] : []
    content {
      create = try(var.timeouts.create, null)
      update = try(var.timeouts.update, null)
      delete = try(var.timeouts.delete, null)
    }
  }
}

# Lambda via Docker Image
resource "aws_lambda_function" "lambda_function_image" {
  count = var.image_uri != "" ? 1 : 0
  package_type     = "Image"
  image_uri        = var.image_uri
  function_name    = var.function_name
  description      = var.description
  memory_size      = var.memory_size
  role             = var.role_arn
  architectures    = var.architectures
  timeout          = var.timeout
  tags             = var.common_tags
  publish                        = !(var.lambda_rollback) ? var.publish_version : false
  reserved_concurrent_executions = var.reserved_concurrency
  layers           = local.lambda_merged_layers

  # ...existing dynamic blocks...
  dynamic "vpc_config" {
    for_each = var.vpc_subnet_ids != null && var.vpc_security_group_ids != null ? [true] : []
    content {
      subnet_ids         = var.vpc_subnet_ids
      security_group_ids = var.vpc_security_group_ids
    }
  }
  dynamic "environment" {
    for_each = length(keys(var.env_vars)) == 0 ? [] : [true]
    content {
      variables = environment.value
    }
  }
  dynamic "tracing_config" {
    for_each = var.tracing_mode == null ? [] : [true]
    content {
      mode = var.tracing_mode
    }
  }
  dynamic "logging_config" {
    for_each = var.logging_log_format != null ? [true] : []
    content {
      log_group             = var.logging_log_group == null ? null : var.logging_log_group
      log_format            = var.logging_log_format
      application_log_level = var.logging_log_format == "Text" ? null : var.logging_application_log_level
      system_log_level      = var.logging_log_format == "Text" ? null : var.logging_system_log_level
    }
  }
  dynamic "dead_letter_config" {
    for_each = var.lambda_dlq_arn != "" ? [true] : []
    content {
      target_arn = var.lambda_dlq_arn
    }
  }
  dynamic "timeouts" {
    for_each = length(var.timeouts) > 0 ? [true] : []
    content {
      create = try(var.timeouts.create, null)
      update = try(var.timeouts.update, null)
      delete = try(var.timeouts.delete, null)
    }
  }
}

# Lambda Resource-Based Policy
resource "aws_lambda_permission" "allow_bedrock" {
  for_each       = var.lambda_resource_policy
  statement_id   = each.value["statement_id"]
  action         = each.value["action"]
  function_name  = each.value["function_name"]
  principal      = each.value["principal"]
  source_arn     = each.value["source_arn"]
  source_account = try(each.value["source_account"], null)  # Optional
}
