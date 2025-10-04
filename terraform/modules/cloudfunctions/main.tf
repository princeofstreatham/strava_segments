# resource "google_cloudfunctions2_function" "segment_explorer_ndjson_converter" {
#   name        = "segment-explorer-ndjson"
#   location    = "eu-west2"
#   description = "A function to convert calls to Strava Segment Explorer Endpoint to NDJSON"

#   build_config {
#     runtime     = "python312"
#     entry_point = "helloPubSub" # Set the entry point
#     environment_variables = {
#       env = "build_test"
#     }
#     source {
#       storage_source {
#         bucket = google_storage_bucket.default.name
#         object = google_storage_bucket_object.default.name
#       }
#     }
#   }

#   service_config {
#     max_instance_count = 3
#     min_instance_count = 1
#     available_memory   = "256M"
#     timeout_seconds    = 60
#     environment_variables = {
#       SERVICE_CONFIG_TEST = "config_test"
#     }
#     ingress_settings               = "ALLOW_INTERNAL_ONLY"
#     all_traffic_on_latest_revision = true
#     service_account_email          = google_service_account.default.email
#   }

#   event_trigger {
#     trigger_region = "us-central1"
#     event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
#     pubsub_topic   = google_pubsub_topic.default.id
#     retry_policy   = "RETRY_POLICY_RETRY"
#   }
# }