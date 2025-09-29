variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "publisher_service_account" {
  type        = string
  description = "Email Address of Service Account"
}

variable "env" {
  type        = string
  description = "Development environment"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags/labels to apply to all resources in this module"
}