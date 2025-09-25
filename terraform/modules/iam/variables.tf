variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "iam_roles" {
  type = list(string)
  default = [
    "roles/secretmanager.admin",
    "roles/storage.admin",
    "roles/cloudsql.admin"
  ]
}