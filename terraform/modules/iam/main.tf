resource "google_service_account" "segment_hunter_service_account" {
  account_id   = "segment-hunter-servie-account"
  display_name = "Segment Hunter Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "service_account_roles" {
  for_each = toset(var.iam_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.segment_hunter_service_account.email}"
}

