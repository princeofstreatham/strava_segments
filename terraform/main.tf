module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
}

module "secretmanager" {
  source          = "./modules/secretmanager"
  project_id      = var.project_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  refresh_token   = var.refresh_token
  access_token    = var.access_token
  dev_sa_password = var.dev_sa_password
}

module "object_storage" {
  source = "./modules/objectstorage"
}

module "cloud_dbs" {
  source         = "./modules/db"
  whitelisted_ip = var.whitelisted_ip
}

module "cloud_db_roles" {
  source = "./modules/db_roles"

  db_host         = module.cloud_dbs.db_hosts["dev"]
  db_user         = var.db_user
  db_password     = var.db_password
  dev_sa_password = var.dev_sa_password

  providers = {
    postgresql = postgresql.dev
  }
}

