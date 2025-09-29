resource "google_storage_bucket" "segment_hunter_bucket" {
  name          = "segment_hunter__${var.env}"
  location      = "EU"
  force_destroy = true
  labels        = var.tags

  public_access_prevention = "enforced"
}