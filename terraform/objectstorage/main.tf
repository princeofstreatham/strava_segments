resource "google_storage_bucket" "segment_hunter_bucket" {
  name          = "segment_hunter"
  location      = "EU"
  force_destroy = true

  public_access_prevention = "enforced"
}