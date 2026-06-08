####################  Core    #####################

data "aws_iam_policy_document" "task_assume_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
  statement {
    sid    = "Statement1"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = local.assume_role_accounts
    }

    actions = ["sts:AssumeRole"]
  } 
}

data "aws_iam_policy_document" "lambda_assume_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "bedrock_assume_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}


data "aws_iam_policy_document" "aurora_monitoring_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy" "auroradb_policy" {
  provider = aws.ai_stack
  arn      = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

data "aws_iam_policy" "cloudwatch" {
  provider = aws.ai_stack
  arn      = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

data "aws_iam_policy" "bedrock_full" {
  provider = aws.ai_stack
  arn      = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}


data "aws_iam_policy" "s3readonlyaccess" {
  provider = aws.ai_stack
  arn      = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

data "aws_iam_policy" "ssminstancecore" {
  provider = aws.ai_stack
  arn      = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy" "ecs_execution_attach" {
  provider       = aws.ai_stack
  arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

 data "template_file" "custom_policy_ecs" {
   template = file("${path.module}/policies/custom_policy_ecs.json")
   vars = {
     account = var.aws_account_id
   }
 }
 
 data "template_file" "custom_policy_task" {
   template = file("${path.module}/policies/custom_policy_ecs_task.json")
   vars = {
     account = var.aws_account_id
   }
 }

  data "template_file" "custom_policy_lambda" {
   template = file("${path.module}/policies/custom_policy_lambda.json")
   vars = {
     account = var.aws_account_id
   }
 }
  
  data "template_file" "custom_policy_bedrock" {
   template = file("${path.module}/policies/custom_policy_bedrock.json")
 } 

data "template_file" "rds_access" {
  template = file("${path.module}/policies/rds_policy.json")
  vars = {
    account = var.aws_account_id
  }
}
 
 
 
######  KMS Grant Creation

#data "aws_kms_key" "ebs_kms" {
#  provider   = aws.ai_stack
#  key_id     = "alias/DefaultEBSEncryptionKey"
##  depends_on = [module.kms_key]
#}


### Roles to attach in IAM
##
##data "template_file" "s3_read_write_policy" {
##  template = file("${path.module}/policies/s3_read_write_policy.json")
##  vars = {
##    s3Bucket = "company-name-support-files"
##  }
##}
##
##data "template_file" "s3_preprod1_specific_policy" {
##  template = file("${path.module}/policies/s3_preprod1_specific_policy.json")
##
##}



## data "template_file" "kms_iam_policy" {
##   template = file("${path.module}/policies/kms_policy.json")
##   vars = {
##     kms_id     = data.aws_kms_key.kms.arn
##     ebs_kms_id = data.aws_kms_key.ebs_kms.arn
##     asg_arn    = aws_iam_service_linked_role.autoscaling.arn
##   }
##   depends_on = [module.kms_key]
## }




## # Only for seating RDS
## 
## data "template_file" "seating_rds_access" {
##   template = file("${path.module}/policies/seating_rds_policy.json")
##   vars = {
##     account = var.aws_account_id
##   }
## }

## ###### KMS Creation
## 
## data "template_file" "ssm_kms_policy" {
##   template = file("${path.module}/policies/ebs.json")
##   vars = {
##     account          = var.aws_account_id
##     re_role          = var.stack_account_role
##     application_role = "${var.app_type}_RoleForSSM"
##     asg_arn          = aws_iam_service_linked_role.autoscaling.arn
##   }
## }


########################## 


## data "aws_iam_policy_document" "s3_read_backup_role_policy_document" {
##   statement {
##     actions = [
##       "s3:ListBucket",
##     "s3:GetBucketLocation"]
##     effect = "Allow"
##     resources = [
##       "arn:aws:s3:::${var.s3_bucket_name}"
##     ]
##   }
##   statement {
##     actions = [
##       "s3:GetObjectAttributes",
##       "s3:GetObject",
##       "s3:PutObject",
##       "s3:ListMultipartUploadParts",
##       "s3:AbortMultipartUpload"
##     ]
##     effect = "Allow"
##     resources = [
##       "arn:aws:s3:::${var.s3_bucket_name}/*"
##     ]
##   }
## }
