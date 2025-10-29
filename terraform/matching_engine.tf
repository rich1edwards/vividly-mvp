# ============================================================================
# Vertex AI Matching Engine for RAG Vector Search
# ============================================================================

# Vertex AI Index for content embeddings
resource "google_vertex_ai_index" "content_index" {
  display_name = "${var.environment}-vividly-content-index"
  description  = "Vector index for OER educational content (RAG)"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.oer_content.name}/index-data/"

    config {
      dimensions              = 768  # text-embedding-gecko@003
      approximate_neighbors_count = 150
      distance_measure_type = "DOT_PRODUCT_DISTANCE"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }

  index_update_method = "BATCH_UPDATE"

  depends_on = [
    google_project_service.required_apis,
    google_storage_bucket.oer_content
  ]
}

# Vertex AI Index Endpoint for serving queries
resource "google_vertex_ai_index_endpoint" "content_endpoint" {
  display_name = "${var.environment}-vividly-content-endpoint"
  description  = "Index endpoint for content retrieval"
  region       = var.region

  public_endpoint_enabled = false  # Private VPC access only
  network                 = google_compute_network.vpc.id

  depends_on = [
    google_project_service.required_apis,
    google_vertex_ai_index.content_index
  ]
}

# Deploy index to endpoint
# Note: This deployment happens via gcloud CLI or API after index creation
# Terraform doesn't directly support index deployment yet

# GCS bucket structure for index data
resource "google_storage_bucket_object" "index_metadata" {
  name    = "index-data/.metadata"
  bucket  = google_storage_bucket.oer_content.name
  content = "Vertex AI Matching Engine index data directory"

  depends_on = [google_storage_bucket.oer_content]
}

# Service account for index updates
resource "google_service_account" "index_updater" {
  account_id   = "${var.environment}-index-updater"
  display_name = "Index Updater Service Account"
  description  = "Service account for updating Vertex AI index"
}

resource "google_project_iam_member" "index_updater_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.index_updater.email}"
}

resource "google_project_iam_member" "index_updater_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.index_updater.email}"
}

# Store index configuration in Secret Manager
resource "google_secret_manager_secret" "matching_engine_config" {
  secret_id = "matching-engine-config-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "matching_engine_config" {
  secret = google_secret_manager_secret.matching_engine_config.id
  secret_data = jsonencode({
    index_id          = google_vertex_ai_index.content_index.id
    endpoint_id       = google_vertex_ai_index_endpoint.content_endpoint.id
    deployed_index_id = "${var.environment}-content-index-deployed"
    dimensions        = 768
    model             = "text-embedding-gecko@003"
  })
}
