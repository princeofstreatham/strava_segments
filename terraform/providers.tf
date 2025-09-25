terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    postgresql = {
      source  = "jbg/postgresql"
      version = "1.19.0"
    }
  }
  required_version = ">= 1.5.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "postgresql" {
  alias     = "dev"
  host      = module.cloud_dbs.db_hosts["dev"]
  port      = 5432
  database  = "postgres"
  username  = var.db_user
  password  = var.db_password
  sslmode   = "require"
  superuser = false
}