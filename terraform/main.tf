module "iam" {
  source     = "./iam"
  project_id = var.project_id
}

module "secretmanager" {
  source        = "./secretmanager"
  project_id    = var.project_id
  client_id     = var.client_id
  client_secret = var.client_secret
  refresh_token = var.refresh_token
  access_token  = var.access_token
}

module "object_storage" {
  source = "./objectstorage"
}

module "cloud_dbs" {
  source = "./db"
  whitelisted_ip = var.whitelisted_ip
}

module "cloud_db_roles" {
  source = "./db_roles"

  db_host         = module.cloud_dbs.db_hosts["dev"]
  db_user         = var.db_user
  db_password     = var.db_password
  dev_sa_password = var.dev_sa_password

  providers = {
    postgresql = postgresql.dev
  }
}

