provider "google" {
  project = var.project_id
  region  = var.region
}

provider "postgresql" {
  alias     = "dev"
  host      = module.cloud_dbs.db_hosts
  port      = 5432
  database  = "postgres"
  username  = "postgres"
  password  = var.db_root_user_password
  sslmode   = "require"
  superuser = false
}