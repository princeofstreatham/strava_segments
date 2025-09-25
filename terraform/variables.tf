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

variable "dbs" {
  type = map(object({
    tier      = string
    disk_size = number
    public    = bool
  }))
  description = "Map or args to pass to Google Cloud SQL provider"
  default = {
    dev  = { tier = "db-f1-micro", disk_size = 10, disk_type = "PD_HDD", public = true }
    prod = { tier = "db-g1-small", disk_size = 5, disk_type = "PD_SSD", public = true }
  }
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

variable "dev_sa_password" {
  type        = string
  description = "Password for Dev DB instance service account"
  sensitive   = true
}

variable "whitelisted_ip" {
  type        = string
  description = "IP Address to access DBs from"
}