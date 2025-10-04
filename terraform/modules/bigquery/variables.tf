variable "dataset_id" {
  type        = string
  description = "ID for bigquery datasets"
  default = "segments"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags/labels to apply to all resources in this module"
}