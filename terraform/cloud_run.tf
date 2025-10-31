# ============================================================================
# Cloud Run Services
# ============================================================================

# Artifact Registry repository for Docker images
# Note: This resource was renamed from vividly_images to vividly
# Use: terraform import google_artifact_registry_repository.vividly projects/vividly-dev-rich/locations/us-central1/repositories/vividly
resource "google_artifact_registry_repository" "vividly" {
  location      = var.region
  repository_id = "vividly"
  description   = "Vividly Docker images"
  format        = "DOCKER"

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"

    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"

    condition {
      tag_state  = "UNTAGGED"
      older_than = "2592000s" # 30 days
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Service account for Cloud Run services
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.environment}-cloud-run-sa"
  display_name = "Cloud Run Service Account (${var.environment})"
  description  = "Service account for Vividly Cloud Run services"
}

# Grant Cloud Run SA access to Cloud SQL
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run SA access to Secret Manager
resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run SA access to Cloud Storage
resource "google_project_iam_member" "cloud_run_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run SA access to Vertex AI
resource "google_project_iam_member" "cloud_run_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run SA access to Logging
resource "google_project_iam_member" "cloud_run_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Run SA access to Monitoring
resource "google_project_iam_member" "cloud_run_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# VPC Connector for Cloud Run to access VPC resources (Cloud SQL, Redis)
resource "google_vpc_access_connector" "cloud_run_connector" {
  name          = "${var.environment}-cloud-run-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.vpc_connector_cidr

  min_instances = var.environment == "prod" ? 2 : 1
  max_instances = var.environment == "prod" ? 10 : 3
  machine_type  = "e2-micro"

  depends_on = [google_project_service.required_apis]
}

# Cloud Run Service - Backend API
resource "google_cloud_run_v2_service" "backend_api" {
  name     = "${var.environment}-vividly-api"
  location = var.region

  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run_sa.email

    # VPC access for Cloud SQL and Redis
    vpc_access {
      connector = google_vpc_access_connector.cloud_run_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    # Scaling configuration
    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = var.cloud_run_max_instances
    }

    # Timeout and concurrency
    timeout         = "300s"
    max_instance_request_concurrency = 80

    containers {
      # Image will be updated via CI/CD
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.vividly.repository_id}/backend-api:latest"

      # Resource limits
      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      # Port
      ports {
        name           = "http1"
        container_port = 8080
      }

      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "DEBUG"
        value = var.environment == "dev" ? "true" : "false"
      }

      env {
        name  = "CORS_ORIGINS"
        value = join(",", var.cors_origins)
      }

      # Database connection via Cloud SQL Proxy
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      # Redis connection
      env {
        name = "REDIS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.redis_url.secret_id
            version = "latest"
          }
        }
      }

      # JWT Secret
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }

      # Storage buckets
      env {
        name  = "GCS_GENERATED_CONTENT_BUCKET"
        value = google_storage_bucket.generated_content.name
      }

      env {
        name  = "GCS_OER_CONTENT_BUCKET"
        value = google_storage_bucket.oer_content.name
      }

      env {
        name  = "GCS_TEMP_FILES_BUCKET"
        value = google_storage_bucket.temp_files.name
      }

      # Vertex AI configuration
      env {
        name  = "VERTEX_LOCATION"
        value = "us-central1"
      }

      env {
        name  = "GEMINI_MODEL"
        value = "gemini-1.5-pro"
      }

      # Startup probe
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 10
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 30
        timeout_seconds       = 3
        period_seconds        = 30
        failure_threshold     = 3
      }
    }

    # Cloud SQL connections
    # Note: This requires the instance connection name
    # Format: project:region:instance
    # Uncomment and configure when deploying
    # cloud_sql_instances = [
    #   google_sql_database_instance.postgres.connection_name
    # ]
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.cloud_run_connector,
    google_service_account.cloud_run_sa
  ]
}

# Allow public access to Cloud Run service
resource "google_cloud_run_v2_service_iam_member" "backend_api_public" {
  name     = google_cloud_run_v2_service.backend_api.name
  location = google_cloud_run_v2_service.backend_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Service - Content Worker (for async TTS/Video jobs)
resource "google_cloud_run_v2_job" "content_worker" {
  name     = "${var.environment}-vividly-content-worker"
  location = var.region

  template {
    template {
      service_account = google_service_account.cloud_run_sa.email

      # VPC access
      vpc_access {
        connector = google_vpc_access_connector.cloud_run_connector.id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      # Timeout
      timeout = "1800s" # 30 minutes for video rendering

      # Parallelism
      max_retries = 3
      parallelism = 1

      containers {
        # Image will be updated via CI/CD
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.vividly.repository_id}/content-worker:latest"

        # Resource limits (higher for video processing)
        resources {
          limits = {
            cpu    = "4"
            memory = "8Gi"
          }
        }

        # Environment variables (same as backend API)
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name = "DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "GCS_GENERATED_CONTENT_BUCKET"
          value = google_storage_bucket.generated_content.name
        }
      }
    }
  }

  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.cloud_run_connector,
    google_service_account.cloud_run_sa
  ]
}
