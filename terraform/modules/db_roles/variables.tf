variable "env" {
  type        = string
  description = "Development Environment"
}

variable "sa_password" {
  type        = string
  description = "Password for Dev DB instance service account"
  sensitive   = true
}

variable "db_password" {
  type        = string
  description = "Admin Password for Postgres"
  sensitive   = true
}

variable "db_user" {
  description = "Postgres User Name to login as"
  type        = string
}

variable "db_host" {
  description = "Host Name/Address for Postgres"
  type        = string
}
