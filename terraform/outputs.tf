output "bucket_name" {
  value = module.object_storage.bucket_name
}

output "db_host" {
  value = module.cloud_dbs.db_hosts
}

output "db_service_account_name" {
  value = module.cloud_db_roles.db_service_account_name
}

output "pubsub_topic_path" {
  value = module.pubsub.topic_name
}

output "pubsub_topic_sub" {
  value = module.pubsub.sub_name
}