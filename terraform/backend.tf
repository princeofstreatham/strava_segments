terraform {
  backend "gcs" {
    bucket = "yakob_tf_state_bucket"
    prefix = "terraform/state"
  }
}