variable "auroradb_cluster_create" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "1"
		PROD    = "1"
  }
}

variable "create_db_subnet_group" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "1"
		PROD    = "1"
  }
}



variable "allow_major_version_upgrade" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "0"
		PROD    = "0"
  }
}

variable "auroradb_monitor_interval" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = 0
		PROD    = 5
  }
}

variable "auroradb_apply_immediately" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "0"
		PROD    = "0"
  }
}

variable "auroradb_backup_retention_period" {
  type = string
  #Replicating previous behaviour
  default = "7"
}

variable "auroradb_insights_mode" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "standard"
		PROD    = "standard"
  }
}

variable "auroradb_instance_class" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "db.r6g.large"
		PROD    = "db.t4g.medium"
  }
}


variable "create_db_cluster_parameter_group" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "1"
		PROD    = "1"
  }
}


variable "create_db_instance_parameter_group" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "1"
		PROD    = "1"
  }
}


variable "db_deletion_protection" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "0"
		PROD    = "1"
  }
}

variable "cloudwatch_log_exports" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = []
		PROD    = ["postgresql"]
  }
}


variable "auroradb_engine" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "aurora-postgresql"
		PROD    = "aurora-postgresql"
  }
}


variable "auroradb_engine_mode" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "provisioned"
		PROD    = "provisioned"
  }
}

variable "auroradb_engine_version" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "17.5"
		PROD    = "17.5"
  }
}

variable "performance_insights_enabled" {
  description = "Specifies whether Performance Insights is enabled or not"
  type        = map
  default = {
		POC     = "0"
		PROD    = "1"
  }
}

variable "performance_ins_enabled" {
  description = "Specifies whether Performance Insights is enabled or not"
  type        = map
  default = {
		POC     = "0"
		PROD    = "1"
  }
}

variable "insights_retention_period" {
  description = "Specifies whether Performance Insights is enabled or not"
  type        = map
  default = {
		POC     = null
		PROD    = 7
  }
}



variable "auroradb_backup_window" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = ""
		PROD    = "02:00-03:00"
  }
}

variable "performance_insights_period" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "7"
		PROD    = "7"
  }
}


variable "auroradb_maintenance_window" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = ""
		PROD    = "sat:23:30-sun:00:30"
  }
}

variable "auroradb_auto_minor_version_upgrade" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "1"
		PROD    = "1"
  }
}

variable "auroradb_skip_final_snapshot" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = null
		PROD    = null
  }
}

variable "aurora_storage_type" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = ""
		PROD    = ""
  }
}

variable "auroradb_serverless_enabled" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = "0"
		PROD    = "0"
  }
}

variable "auroradb_final_snapshot_identifier" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = null
		PROD    = null
  }
}

variable "auroradb_iops" {
  type = map(any)
  #Replicating previous behaviour
  default = {
		POC     = 2000
		PROD    = 2500
  }
}
