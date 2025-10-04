resource "google_storage_bucket" "segment_hunter_bucket" {
  name          = "segment_hunter__${var.env}"
  location      = "EU"
  force_destroy = true
  labels        = var.tags

  public_access_prevention = "enforced"
}

resource "google_storage_bucket" "source_bucket" {
  name     = "gcf-source__${var.env}"  # Every bucket name must be globally unique
  location = "EU"
  force_destroy = true
  labels        = var.tags

  public_access_prevention = "enforced"
}

data "archive_file" "segment_explorer_zip" {
  type        = "zip"
  output_path = "../tmp/segment_explorer_lambda.zip"
  source_file = "../src/segment_explorer_lambda.py"
}

resource "google_storage_bucket_object" "segment_explorer_src" {
  name   = "segment_explorer_lambda.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.segment_explorer_zip.output_path
}
