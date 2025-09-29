variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region"
  default     = "EU"
}

variable "client_secret" {
  type        = string
  description = "Strava Client Secret"
  sensitive   = true
}

variable "client_id" {
  type        = string
  description = "Strava Client ID"
  sensitive   = true
}

variable "refresh_token" {
  type        = string
  description = "Strava User Refresh Token"
  sensitive   = true
}

variable "access_token" {
  type        = string
  description = "Strava User Access Token"
  sensitive   = true
}
variable "tier" {
  type        = string
  description = "Cloud SQL database instance tier"
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

variable "sa_password" {
  type        = string
  description = "Password for DB instance service account"
  sensitive   = true
}

variable "disk_size" {
  type        = string
  description = "Amount of DB Storage"
  default     = 10
}

variable "whitelisted_ip" {
  type        = string
  description = "IP Address to access DBs from"
}

variable "db_root_user_password" {
  type        = string
  description = "Password for new root user"
}