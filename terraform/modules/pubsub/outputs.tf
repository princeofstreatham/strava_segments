output "topic_name" {
  value = google_pubsub_topic.segment_explorer.name
}

output "sub_name" {
  value = google_pubsub_subscription.segment_explorer_sub.name
}