variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "env" {
  type        = string
  description = "Development environment to deploy DB in"
}

variable "iam_roles" {
  type = list(string)
  default = [
    "roles/secretmanager.admin",
    "roles/storage.admin",
    "roles/cloudsql.admin",
    "roles/pubsub.admin",
    "roles/cloudfunctions.admin",
    "roles/cloudbuild.builds.builder",
    "roles/run.sourceDeveloper",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/iam.serviceAccountUser" 
  ]
}