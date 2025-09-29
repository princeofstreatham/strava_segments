variable "env" {
  type        = string
  description = "Development environment to deploy DB in"
}

variable "tier" {
  type        = string
  description = "Cloud SQL database instance tier"
}

variable "disk_size" {
  type        = string
  description = "Amount of DB Storage"
}

variable "whitelisted_ip" {
  type        = string
  description = "IP Address to access DBs from"
}

variable "db_root_user_password" {
  type        = string
  description = "Password for new root user"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags/labels to apply to all resources in this module"
}