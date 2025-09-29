resource "google_pubsub_topic" "segment_explorer" {
  name    = "segment-explorer--${var.env}"
  project = var.project_id
}

resource "google_pubsub_topic_iam_member" "publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.segment_explorer.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.publisher_service_account}"
}

resource "google_pubsub_subscription" "segment_explorer_sub" {
  name                 = "segment-explorer-sub--${var.env}"
  topic                = google_pubsub_topic.segment_explorer.id
  filter = "attributes.env = \"dev\""
  labels               = var.tags
  ack_deadline_seconds = 40
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.segment_explorer_dlq.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "segment_explorer_dlq" {
  name = "segment-explorer-dlq--${var.env}"

  labels = {
    environment = var.env
    service     = "segment-explorer"
  }
}