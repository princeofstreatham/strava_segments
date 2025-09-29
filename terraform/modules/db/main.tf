resource "google_sql_database_instance" "db_instance" {
  name             = "${var.env}-instance"
  database_version = "POSTGRES_17"
  region           = "europe-west2"


  settings {
    tier              = var.tier
    disk_size         = var.disk_size
    disk_type         = "PD_HDD"
    activation_policy = "ALWAYS"
    user_labels       = var.tags

    ip_configuration {
      ipv4_enabled = true

      authorized_networks {
        name  = "office"
        value = var.whitelisted_ip
      }
    }
  }
}

resource "google_sql_user" "db_user" {
  name     = "yakob"
  instance = google_sql_database_instance.db_instance.name
  password = var.db_root_user_password
}

resource "google_sql_user" "postgres" {
  name     = "postgres"
  instance = google_sql_database_instance.db_instance.name
  password = var.db_root_user_password
}