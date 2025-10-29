output "vpc_id" {
  description = "VPC Network ID"
  value       = google_compute_network.vpc.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = google_compute_subnetwork.subnet.id
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "redis_instance_name" {
  description = "Redis instance name"
  value       = google_redis_instance.cache.name
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "redis_url_secret_name" {
  description = "Secret Manager secret name for Redis URL"
  value       = google_secret_manager_secret.redis_url.secret_id
}

output "generated_content_bucket" {
  description = "Generated content storage bucket name"
  value       = google_storage_bucket.generated_content.name
}

output "oer_content_bucket" {
  description = "OER content storage bucket name"
  value       = google_storage_bucket.oer_content.name
}

output "temp_files_bucket" {
  description = "Temporary files storage bucket name"
  value       = google_storage_bucket.temp_files.name
}

output "content_requests_topic" {
  description = "Pub/Sub topic for content requests"
  value       = google_pubsub_topic.content_requests.id
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.vividly.repository_id}"
}

output "api_gateway_service_account" {
  description = "API Gateway service account email"
  value       = google_service_account.api_gateway.email
}

output "admin_service_account" {
  description = "Admin service account email"
  value       = google_service_account.admin_service.email
}

output "content_worker_service_account" {
  description = "Content Worker service account email"
  value       = google_service_account.content_worker.email
}

output "cicd_service_account" {
  description = "CI/CD service account email"
  value       = google_service_account.cicd.email
}

output "database_url_secret_name" {
  description = "Secret Manager secret name for database URL"
  value       = google_secret_manager_secret.database_url.secret_id
}

# Cloud Run Outputs
output "backend_api_url" {
  description = "Backend API Cloud Run service URL"
  value       = google_cloud_run_v2_service.backend_api.uri
}

output "backend_api_name" {
  description = "Backend API Cloud Run service name"
  value       = google_cloud_run_v2_service.backend_api.name
}

output "cloud_run_service_account" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run_sa.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Vividly images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.vividly_images.repository_id}"
}

output "content_worker_job_name" {
  description = "Content Worker Cloud Run Job name"
  value       = google_cloud_run_v2_job.content_worker.name
}

output "vpc_connector_name" {
  description = "VPC Access Connector name"
  value       = google_vpc_access_connector.cloud_run_connector.name
}
