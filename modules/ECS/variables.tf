variable "service_name" {
  type = string
}

variable "cpu" {
  type = number
}

variable "memory" {
  type = number
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  type    = string
  default = null
}

variable "container_definitions" {
  type = string
}

variable "ecs_cluster_id" {
  type = string
}

variable "lb_target_group_arn" {
  type = string
}

variable "container_name" {
  type = string
}

variable "container_port" {
  type = number
}

variable "security_group_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "assign_public_ip" {
  type    = bool
  default = false
}

variable "enable_execute_command" {
  type    = bool
  default = false
}

variable "desired_count" {
  type = number
  default = 1
}

variable "create_time_out" {
  type = string
  default = "20m"
}

variable "delete_time_out" {
  type = string
  default = "20m"
}

variable "update_time_out" {
  type = string
  default = "20m"
}

variable "force_new_deployment" {
  type = bool
  description = "Provide true or false for force new deployment"
  default = false
}