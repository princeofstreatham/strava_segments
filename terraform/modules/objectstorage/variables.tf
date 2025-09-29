variable "env" {
  type        = string
  description = "Development environment to deploy DB in"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags/labels to apply to all resources in this module"
}