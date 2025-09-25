output "bucket_name" {
  value = module.object_storage.bucket_name
}

output "db_host" {
  value = module.cloud_dbs.db_hosts
}