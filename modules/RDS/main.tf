################################################################################
# DB Subnet Group
################################################################################

resource "aws_db_subnet_group" "auroradb_subnet" {
  count = var.create_db_subnet_group ? 1 : 0

  name        = var.db_subnet_group_name
  description = "For Aurora cluster ${var.db_name}"
  subnet_ids  = var.subnets

  tags = var.tags
}


resource "aws_rds_cluster_parameter_group" "auroradb_cpg" {
  count = var.create_db_cluster_parameter_group ? 1 : 0

  name        = var.db_cluster_parameter_group_name
  description = var.db_cluster_parameter_group_description
  family      = var.db_cluster_parameter_group_family

  dynamic "parameter" {
    for_each = var.db_cluster_parameter_group_parameters

    content {
      name         = parameter.value.name
      value        = parameter.value.value
      apply_method = try(parameter.value.apply_method, "immediate")
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = var.tags
}

################################################################################
# DB Parameter Group
################################################################################

resource "aws_db_parameter_group" "auroradb_pg" {
  count = var.create_db_parameter_group ? 1 : 0

  name        = var.db_parameter_group_name
  description = var.db_parameter_group_description
  family      = var.db_parameter_group_family

  dynamic "parameter" {
    for_each = var.db_parameter_group_parameters

    content {
      name         = parameter.value.name
      value        = parameter.value.value
      apply_method = try(parameter.value.apply_method, "immediate")
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = var.tags
}


resource "aws_rds_cluster" "aurora" {
  cluster_identifier                    = "${var.db_name}-cluster"
  allow_major_version_upgrade           = var.allow_major_version_upgrade  
  apply_immediately                     = var.apply_immediately
  backup_retention_period               = var.backup_retention_period
  engine                                = var.engine
  engine_version                        = var.engine_version
  master_username                       = var.master_username
  master_password                       = var.master_password
  database_name                         = var.database_name
  db_subnet_group_name                  = aws_db_subnet_group.auroradb_subnet[0].name
  vpc_security_group_ids                = var.vpc_security_group_ids
  monitoring_interval                   = var.cluster_monitoring_interval
  monitoring_role_arn                   = var.cluster_monitoring_interval == 0 ? null : var.monitoring_role_arn
  database_insights_mode                = var.database_insights_mode  
  preferred_maintenance_window          = var.preferred_maintenance_window  
  skip_final_snapshot                   = true
  storage_encrypted                     = var.storage_encrypted
  db_cluster_parameter_group_name       = var.create_db_cluster_parameter_group ? aws_rds_cluster_parameter_group.auroradb_cpg[0].id : var.db_cluster_parameter_group_name
  db_instance_parameter_group_name      = var.allow_major_version_upgrade ? var.db_cluster_db_instance_parameter_group_name : null
  storage_type                          = var.storage_type  

  dynamic "restore_to_point_in_time" {
    for_each = length(var.restore_to_point_in_time) > 0 ? [var.restore_to_point_in_time] : []

    content {
      restore_to_time            = try(restore_to_point_in_time.value.restore_to_time, null)
      restore_type               = try(restore_to_point_in_time.value.restore_type, null)
      source_cluster_identifier  = try(restore_to_point_in_time.value.source_cluster_identifier, null)
      source_cluster_resource_id = try(restore_to_point_in_time.value.source_cluster_resource_id, null)
      use_latest_restorable_time = try(restore_to_point_in_time.value.use_latest_restorable_time, null)
    }
  }

  dynamic "s3_import" {
    for_each = length(var.s3_import) > 0 && !var.is_serverless ? [var.s3_import] : []

    content {
      bucket_name           = s3_import.value.bucket_name
      bucket_prefix         = try(s3_import.value.bucket_prefix, null)
      ingestion_role        = s3_import.value.ingestion_role
      source_engine         = "mysql"
      source_engine_version = s3_import.value.source_engine_version
    }
  }

  dynamic "scaling_configuration" {
    for_each = length(var.scaling_configuration) > 0 && var.is_serverless ? [var.scaling_configuration] : []

    content {
      auto_pause               = try(scaling_configuration.value.auto_pause, null)
      max_capacity             = try(scaling_configuration.value.max_capacity, null)
      min_capacity             = try(scaling_configuration.value.min_capacity, null)
      seconds_until_auto_pause = try(scaling_configuration.value.seconds_until_auto_pause, null)
      seconds_before_timeout   = try(scaling_configuration.value.seconds_before_timeout, null)
      timeout_action           = try(scaling_configuration.value.timeout_action, null)
    }
  }

  dynamic "serverlessv2_scaling_configuration" {
    for_each = length(var.serverlessv2_scaling_configuration) > 0 && var.engine_mode == "provisioned" ? [var.serverlessv2_scaling_configuration] : []

    content {
      max_capacity             = serverlessv2_scaling_configuration.value.max_capacity
      min_capacity             = serverlessv2_scaling_configuration.value.min_capacity
      seconds_until_auto_pause = try(serverlessv2_scaling_configuration.value.seconds_until_auto_pause, null)
    }
  }
  
  
}

resource "aws_rds_cluster_instance" "aurora_instance" {
  count = var.auroradb_instance_create ? var.auroradb_instance_count : 0
  identifier            = "${var.db_name}-instance-${count.index + 1}"
  cluster_identifier    = aws_rds_cluster.aurora.id
  instance_class        = var.instance_class
  engine                = var.engine
  engine_version        = var.engine_version
  publicly_accessible   = false
}


data "aws_route53_zone" "selected" {
#  count    = var.create_dns ? 1 : 0
  provider = aws.dnszone
  name     = var.route53_zone_name
  private_zone = true
}

resource "aws_route53_record" "alb_wildcard" {
  provider = aws.dnszone
  zone_id  = data.aws_route53_zone.selected.zone_id
  name     = var.aurora_dns_name
  type     = "CNAME"
  ttl      = 300

  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      zone_id
    ]
  }

  records = [aws_rds_cluster.aurora.endpoint]

  depends_on = [data.aws_route53_zone.selected]
}

