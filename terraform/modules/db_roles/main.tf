terraform {
  required_providers {
    postgresql = {
      source  = "jbg/postgresql"
      version = "1.19.0"
    }
  }
  required_version = ">= 1.5.0"
}


resource "postgresql_role" "dev_service_account" {
  name     = "service_account"
  login    = true
  password = var.dev_sa_password
}

resource "postgresql_grant" "readonly_tables_schema_usage_public" {
  database    = "postgres"
  role        = postgresql_role.dev_service_account.name
  schema      = "dev"
  object_type = "schema"
  privileges  = ["USAGE"]
}


resource "postgresql_grant" "dev_service_account_grant" {
  role        = postgresql_role.dev_service_account.name
  database    = "postgres"
  object_type = "table"
  schema      = "dev"
  objects     = ["bounding_boxes"]
  privileges  = ["SELECT", "INSERT", "UPDATE"]
  depends_on  = [postgresql_role.dev_service_account]
}

resource "postgresql_default_privileges" "dev_service_account_defaults" {
  role        = postgresql_role.dev_service_account.name
  owner       = "yakob"
  database    = "postgres"
  schema      = "dev"
  object_type = "table"
  privileges  = ["SELECT", "INSERT", "UPDATE"]

}
