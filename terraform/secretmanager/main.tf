module "secret-manager" {
  source     = "GoogleCloudPlatform/secret-manager/google"
  version    = "~> 0.8"
  project_id = var.project_id
  secrets = [
    {
      name        = "strava-client-secret"
      secret_data = var.client_secret
    },
    {
      name        = "strava-client-id"
      secret_data = var.client_id
    },
    {
      name        = "strava-refresh-token"
      secret_data = var.refresh_token
    },
    {
      name        = "strava-access-token"
      secret_data = var.access_token
    }
  ]
}