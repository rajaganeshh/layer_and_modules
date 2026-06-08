output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = try(aws_lambda_function.lambda_function_file[0].function_name, null)
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = try(aws_lambda_function.lambda_function_file[0].arn, null)
}

output "lambda_function_invoke_arn" {
  description = "The ARN to be used for invoking Lambda function"
  value       = try(aws_lambda_function.lambda_function_file[0].invoke_arn, null)
}

output "lambda_function_s3_name" {
  description = "The name of the Lambda function deployed via S3"
  value       = try(aws_lambda_function.lambda_function_s3[0].function_name, null)
}

output "lambda_function_s3_arn" {
  description = "The ARN of the Lambda function deployed via S3"
  value       = try(aws_lambda_function.lambda_function_s3[0].arn, null)
}

output "lambda_function_image_name" {
  description = "The name of the Lambda function deployed via Docker image"
  value       = try(aws_lambda_function.lambda_function_image[0].function_name, null)
}

output "lambda_function_image_arn" {
  description = "The ARN of the Lambda function deployed via Docker image"
  value       = try(aws_lambda_function.lambda_function_image[0].arn, null)
}

output "lambda_function_file_layers" {
  description = "The Lambda layers attached to the ZIP file deployment"
  value       = try(aws_lambda_function.lambda_function_file[0].layers, null)
}

output "lambda_function_s3_layers" {
  description = "The Lambda layers attached to the S3 deployment"
  value       = try(aws_lambda_function.lambda_function_s3[0].layers, null)
}

output "lambda_function_image_layers" {
  description = "The Lambda layers attached to the Docker image deployment"
  value       = try(aws_lambda_function.lambda_function_image[0].layers, null)
}
