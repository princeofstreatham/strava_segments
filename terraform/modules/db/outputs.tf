output "db_hosts" {
  value = google_sql_database_instance.db_instance.public_ip_address
}
