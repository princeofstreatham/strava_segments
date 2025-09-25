output "db_hosts" {
  value = { for k, v in google_sql_database_instance.db_instances : k => v.public_ip_address }
}