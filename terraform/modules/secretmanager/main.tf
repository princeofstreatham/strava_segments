module "secret-manager" {
  source     = "GoogleCloudPlatform/secret-manager/google"
  version    = "~> 0.8"
  project_id = var.project_id
  secrets = [
    {
      name        = "strava-client-secret--${var.env}"
      secret_data = var.client_secret
    },
    {
      name        = "strava-client-id--${var.env}"
      secret_data = var.client_id
    },
    {
      name        = "strava-refresh-token--${var.env}"
      secret_data = var.refresh_token
    },
    {
      name        = "strava-access-token--${var.env}"
      secret_data = var.access_token
    },
    {
      name        = "postgres-service-account-pwd--${var.env}"
      secret_data = var.sa_password
    }
  ]
}