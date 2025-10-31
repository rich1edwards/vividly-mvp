terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    # Backend configuration is provided via backend config file
    # terraform init -backend-config=backend-<env>.hcl
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "aiplatform.googleapis.com",
    "storage-api.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudprofiler.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.environment}-vividly-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.environment}-vividly-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.environment}-vividly-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.db_disk_size
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "prod" ? true : false
      start_time                     = "03:00"
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 30 : 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }

    database_flags {
      name  = "shared_buffers"
      value = "262144" # 1GB in 4KB pages
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # 4 AM
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
    }
  }

  deletion_protection = var.environment == "prod" ? true : false

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private VPC Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.environment}-vividly-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.required_apis]
}

# Database and User
resource "google_sql_database" "vividly" {
  name     = "vividly"
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "google_sql_user" "vividly" {
  name     = "vividly"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Store DB connection string in Secret Manager
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${google_sql_user.vividly.name}:${google_sql_user.vividly.password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.vividly.name}"
}

# ============================================================================
# Cloud Memorystore (Redis)
# ============================================================================

resource "google_redis_instance" "cache" {
  name               = "${var.environment}-vividly-cache"
  tier               = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.redis_memory_size
  region             = var.region
  redis_version      = "REDIS_7_0"
  display_name       = "${var.environment} Vividly Redis Cache"
  reserved_ip_range  = var.redis_reserved_ip_range
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  authorized_network = google_compute_network.vpc.id

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
    timeout          = "300"
  }

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 4
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }

  location_id             = "${var.region}-a"
  alternative_location_id = var.environment == "prod" ? "${var.region}-b" : null

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Store Redis connection info in Secret Manager
resource "google_secret_manager_secret" "redis_url" {
  secret_id = "redis-url-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "redis_url" {
  secret      = google_secret_manager_secret.redis_url.id
  secret_data = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
}

# Cloud Storage Buckets
resource "google_storage_bucket" "generated_content" {
  name          = "${var.project_id}-${var.environment}-generated-content"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod" ? true : false
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

resource "google_storage_bucket" "oer_content" {
  name          = "${var.project_id}-${var.environment}-oer-content"
  location      = var.region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "temp_files" {
  name          = "${var.project_id}-${var.environment}-temp-files"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

# ============================================================================
# Cloud CDN for Video Delivery
# ============================================================================

# Reserve global IP for CDN
resource "google_compute_global_address" "cdn_ip" {
  name = "${var.environment}-vividly-cdn-ip"
}

# Backend bucket for CDN
resource "google_compute_backend_bucket" "video_cdn" {
  name        = "${var.environment}-vividly-video-cdn"
  bucket_name = google_storage_bucket.generated_content.name
  enable_cdn  = true

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600
    default_ttl       = 86400    # 24 hours
    max_ttl           = 2592000  # 30 days
    negative_caching  = true
    serve_while_stale = 86400

    cache_key_policy {
      include_host           = true
      include_protocol       = true
      include_query_string   = false
    }

    negative_caching_policy {
      code = 404
      ttl  = 300
    }

    negative_caching_policy {
      code = 410
      ttl  = 300
    }
  }

  compression_mode = "AUTOMATIC"
}

# URL map for CDN
resource "google_compute_url_map" "cdn_url_map" {
  name            = "${var.environment}-vividly-cdn-url-map"
  default_service = google_compute_backend_bucket.video_cdn.id
}

# HTTPS certificate (managed)
resource "google_compute_managed_ssl_certificate" "cdn_cert" {
  name = "${var.environment}-vividly-cdn-cert"

  managed {
    domains = var.cdn_domain != "" ? [var.cdn_domain] : ["${var.environment}-cdn.vividly.edu"]
  }
}

# HTTPS proxy
resource "google_compute_target_https_proxy" "cdn_https_proxy" {
  name             = "${var.environment}-vividly-cdn-https-proxy"
  url_map          = google_compute_url_map.cdn_url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.cdn_cert.id]
}

# Forwarding rule (global)
resource "google_compute_global_forwarding_rule" "cdn_forwarding_rule" {
  name                  = "${var.environment}-vividly-cdn-forwarding-rule"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range            = "443"
  target                = google_compute_target_https_proxy.cdn_https_proxy.id
  ip_address            = google_compute_global_address.cdn_ip.id
}

# HTTP to HTTPS redirect
resource "google_compute_url_map" "cdn_http_redirect" {
  name = "${var.environment}-vividly-cdn-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "cdn_http_proxy" {
  name    = "${var.environment}-vividly-cdn-http-proxy"
  url_map = google_compute_url_map.cdn_http_redirect.id
}

resource "google_compute_global_forwarding_rule" "cdn_http_forwarding_rule" {
  name                  = "${var.environment}-vividly-cdn-http-forwarding-rule"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range            = "80"
  target                = google_compute_target_http_proxy.cdn_http_proxy.id
  ip_address            = google_compute_global_address.cdn_ip.id
}

# Pub/Sub Topics and Subscriptions
resource "google_pubsub_topic" "content_requests" {
  name = "content-requests-${var.environment}"

  message_retention_duration = "604800s" # 7 days
}

resource "google_pubsub_subscription" "content_requests_dlq" {
  name  = "content-requests-${var.environment}-dlq"
  topic = google_pubsub_topic.content_requests.name

  ack_deadline_seconds = 600

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.content_requests_dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_topic" "content_requests_dlq" {
  name = "content-requests-${var.environment}-dlq"

  message_retention_duration = "604800s" # 7 days
}

# Note: Artifact Registry for Docker Images moved to cloud_run.tf

# Service Accounts
resource "google_service_account" "api_gateway" {
  account_id   = "${var.environment}-api-gateway"
  display_name = "API Gateway Service Account (${var.environment})"
}

resource "google_service_account" "admin_service" {
  account_id   = "${var.environment}-admin-service"
  display_name = "Admin Service Account (${var.environment})"
}

resource "google_service_account" "content_worker" {
  account_id   = "${var.environment}-content-worker"
  display_name = "Content Worker Service Account (${var.environment})"
}

resource "google_service_account" "cicd" {
  account_id   = "${var.environment}-cicd"
  display_name = "CI/CD Service Account (${var.environment})"
}

# IAM Bindings for Service Accounts
# API Gateway permissions
resource "google_project_iam_member" "api_gateway_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

resource "google_project_iam_member" "api_gateway_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

resource "google_project_iam_member" "api_gateway_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

resource "google_project_iam_member" "api_gateway_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api_gateway.email}"
}

# Content Worker permissions
resource "google_project_iam_member" "content_worker_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

resource "google_project_iam_member" "content_worker_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

resource "google_project_iam_member" "content_worker_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

resource "google_project_iam_member" "content_worker_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.content_worker.email}"
}

# CI/CD permissions
resource "google_project_iam_member" "cicd_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_functions_admin" {
  project = var.project_id
  role    = "roles/cloudfunctions.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_artifact_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

# Vertex AI Vector Search Index (created separately via console/script)
# This requires embedding deployment which is done post-terraform

# Cloud Monitoring Alert Policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${var.environment} - High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.label.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "${var.environment} - High Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 2s"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 2000 # milliseconds

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "database_cpu" {
  display_name = "${var.environment} - High Database CPU"
  combiner     = "OR"

  conditions {
    display_name = "DB CPU > 80%"

    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND metric.type = \"cloudsql.googleapis.com/database/cpu/utilization\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }
}
