resource "google_bigquery_dataset" "segment_dataset" {
    dataset_id = var.dataset_id
    location = "EU"
    delete_contents_on_destroy = true
    
    labels = var.tags
}