locals {
  env = terraform.workspace
  global_tags = {
    env     = terraform.workspace
    project = "segment-hunter"
  }
}

module "iam" {
  source     = "./modules/iam"
  project_id = var.project_id
  env        = local.env
}

module "secretmanager" {
  source        = "./modules/secretmanager"
  env           = local.env
  project_id    = var.project_id
  client_id     = var.client_id
  client_secret = var.client_secret
  refresh_token = var.refresh_token
  access_token  = var.access_token
  sa_password   = var.sa_password
}

module "object_storage" {
  source = "./modules/objectstorage"
  env    = local.env
  tags   = local.global_tags
}

module "cloud_dbs" {
  source                = "./modules/db"
  env                   = local.env
  disk_size             = var.disk_size
  tier                  = var.tier
  db_root_user_password = var.db_root_user_password
  whitelisted_ip        = var.whitelisted_ip
  tags                  = local.global_tags
}

module "cloud_db_roles" {
  source = "./modules/db_roles"
  env    = local.env

  db_host     = module.cloud_dbs.db_hosts
  db_user     = var.db_user
  db_password = var.db_password
  sa_password = var.sa_password

  providers = {
    postgresql = postgresql.dev
  }
}

module "pubsub" {
  source                    = "./modules/pubsub"
  project_id                = var.project_id
  publisher_service_account = module.iam.service_account_email
  env                       = local.env
}