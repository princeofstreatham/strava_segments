resource "google_sql_database_instance" "db_instances" {
  for_each         = var.dbs
  name             = "${each.key}-instance"
  database_version = "POSTGRES_17"
  region           = "europe-west2"

  settings {
    tier              = each.value.tier
    disk_size         = each.value.disk_size
    disk_type         = "PD_HDD"
    activation_policy = "ALWAYS"

    ip_configuration {
      ipv4_enabled = each.value.public

      dynamic "authorized_networks" {
        for_each = each.value.public ? [1] : []
        content {
          name  = "office"
          value = var.whitelisted_ip
        }
      }
    }
  }
}
