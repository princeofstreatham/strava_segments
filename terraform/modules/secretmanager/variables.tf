variable "project_id" {
  type        = string
  description = "GCP Project ID"
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

variable "dev_sa_password" {
  type        = string
  description = "Password for Dev DB instance service account"
  sensitive   = true
}
