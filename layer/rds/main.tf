locals {
  db_username = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["username"]
  db_password = sensitive(jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"])
}

################## RDS Creation ##################
module "aws_rds" {


  providers = {
    aws = aws.ai_stack
    aws.dnszone = aws.ai_stack_dns_zone
  }

  source                              = "git@github.com:company-org/company-name-iac-modules-auroradb.git?ref=develop"

  auroradb_cluster_create                       = lookup(var.auroradb_cluster_create, terraform.workspace)
  auroradb_instance_create                      = lookup(var.auroradb_cluster_create, terraform.workspace)
  create_db_subnet_group                        = lookup(var.create_db_subnet_group, terraform.workspace)
  subnets                                       = data.aws_subnets.rds_subnets.ids
  create_db_parameter_group                     = false
  is_serverless                                 = lookup(var.auroradb_serverless_enabled, terraform.workspace)
  route53_zone_name                             = 
  aurora_dns_name                               = 
  allow_major_version_upgrade                   = lookup(var.allow_major_version_upgrade, terraform.workspace)
  apply_immediately                             = lookup(var.auroradb_apply_immediately, terraform.workspace)
  availability_zones                            = data.aws_subnets.rds_subnets.ids
  backup_retention_period                       = var.env_type == "PROD" ? var.auroradb_backup_retention_period : null
  backtrack_window                              = null
  cluster_ca_cert_identifier                    = "rds-ca-rsa2048-g1"
  db_name                                       = "${var.source_market}-${lower(terraform.workspace)}-mim-auroradb"
  database_name                                 = "database1"
  cluster_use_name_prefix                       = true
  cluster_members                               = null
  cluster_scalability_type                      = null
  copy_tags_to_snapshot                         = true
  database_insights_mode                        = lookup(var.auroradb_insights_mode, terraform.workspace)
  is_primary_cluster                            = true
  db_cluster_instance_class                     = lookup(var.auroradb_instance_class, terraform.workspace)
  create_db_cluster_parameter_group             = false
  db_cluster_parameter_group_name               = "default.aurora-postgresql17"
  db_parameter_group_name                       = "default.aurora-postgresql17"
  db_security_group_ids                         = [data.aws_security_group.auroradb.id]
  delete_automated_backups                      = false
  deletion_protection                           = lookup(var.db_deletion_protection, terraform.workspace)
  enable_global_write_forwarding                = null      
  enable_local_write_forwarding                 = null
  enabled_cloudwatch_logs_exports               = lookup(var.cloudwatch_log_exports, terraform.workspace)
  enable_http_endpoint                          = false
  engine                                        = lookup(var.auroradb_engine, terraform.workspace)
  engine_mode                                   = lookup(var.auroradb_engine_mode, terraform.workspace)
  engine_version                                = lookup(var.auroradb_engine_version, terraform.workspace)
  engine_lifecycle_support                      = null
  final_snapshot_identifier                     = lookup(var.auroradb_final_snapshot_identifier, terraform.workspace)
  global_cluster_identifier                     = null
  domain                                        = 
  iam_database_authentication_enabled           = true
  iops                                          = null
  kms_key_id                                    = null
  manage_master_user_password                   = false
  master_user_secret_kms_key_id                 = null
  master_password                               = "${local.db_password}"
  master_username                               = local.db_username
  cluster_monitoring_interval                   = lookup(var.auroradb_monitor_interval, terraform.workspace)
  network_type                                  = null
  cluster_performance_insights_enabled          = lookup(var.performance_insights_enabled, terraform.workspace)
  cluster_performance_insights_kms_key_id       = null
  cluster_performance_insights_retention_period = lookup(var.performance_insights_period, terraform.workspace)
  port                                          = contains(["aurora-postgresql", "postgres"], lookup(var.auroradb_engine, terraform.workspace)) ? 5432 : 3306
  preferred_backup_window                       = lookup(var.auroradb_backup_window, terraform.workspace)
  preferred_maintenance_window                  = lookup(var.auroradb_maintenance_window, terraform.workspace)
  replication_source_identifier                 = null
  auto_minor_version_upgrade                    = lookup(var.auroradb_auto_minor_version_upgrade, terraform.workspace)
  skip_final_snapshot                           = true
  snapshot_identifier                           = lookup(var.auroradb_skip_final_snapshot, terraform.workspace)
  source_region                                 = var.region
  storage_encrypted                             = true
  storage_type                                  = lookup(var.aurora_storage_type, terraform.workspace)
  vpc_security_group_ids                        = [data.aws_security_group.auroradb.id]
  restore_to_point_in_time                      = {}
  s3_import                                     = {}
  scaling_configuration                         = {}
  serverlessv2_scaling_configuration            = {}

############ Instance
  ca_cert_identifier                            = "rds-ca-rsa2048-g1"
  db_subnet_group_name                          = "${var.source_market}-${lower(terraform.workspace)}-mim-auroradb-sg"
  instances_identifier                          = "${var.source_market}-${lower(terraform.workspace)}-mim-auroradb-instance"
  auroradb_instance_count                       = var.env_type == "PROD" ? 2 : 1
  instance_class                                = lookup(var.auroradb_instance_class, terraform.workspace)
  monitoring_role_arn                           = "arn:aws:iam::${var.aws_account_id}:role/${var.source_market}_${lower(terraform.workspace)}_mim_auroradb_monitoring_role"
  performance_insights_enabled                  = lookup(var.performance_ins_enabled, terraform.workspace)
  performance_insights_kms_key_id               = null
  performance_insights_retention_period         = lookup(var.insights_retention_period, terraform.workspace)
  publicly_accessible                           = false
  
  tags											= merge(var.tags,
														{ Account = var.aws_account_id },
														{ "Patch Group" = lookup(var.patchgroup, var.env_type) }
														) 
		
}



#resource "null_resource" "run_db_script" {
#  depends_on = [module.aws_rds]

#  provisioner "local-exec" {
#    command = <<EOT
      # Assume the IAM role for DB access
#      CREDS=$(aws sts assume-role \
#        --role-arn arn:aws:iam::${var.aws_account_id}:role/RoleForTerraform \
#        --role-session-name db-script-session)
#      export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r .Credentials.AccessKeyId)
#      export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r .Credentials.SecretAccessKey)
#      export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r .Credentials.SessionToken)

  # Wait for RDS to be available
#  sleep 60
  # Run the SQL script using psql
#  PGPASSWORD="${local.db_password}" psql "host=${module.aws_rds.rds_endpoint} port=5432 user=${local.db_username} dbname=database1 sslmode=require" -f "${path.module}/db_script.sql"
#    EOT
#  }
#}
