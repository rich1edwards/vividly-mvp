# Redis / Cloud Memorystore Configuration for Phase 1.4 Notifications
#
# This file provisions the Redis infrastructure required for the Server-Sent Events (SSE)
# notification system. Redis Pub/Sub enables distributed real-time notifications across
# multiple Cloud Run instances.
#
# Architecture:
# - Redis instance for Pub/Sub messaging and connection state
# - VPC network for secure Redis connectivity
# - VPC Serverless Connector for Cloud Run → Redis communication
# - Firewall rules for secure access
# - Secret Manager integration for connection credentials

# -----------------------------------------------------------------------------
# VPC Network for Redis
# -----------------------------------------------------------------------------
resource "google_compute_network" "redis_network" {
  name                    = "${var.environment}-vividly-redis-network"
  auto_create_subnetworks = false
  project                 = var.project_id

  description = "VPC network for Redis/Memorystore connectivity - Phase 1.4 Notifications"
}

# Subnet for Redis instance
resource "google_compute_subnetwork" "redis_subnet" {
  name          = "${var.environment}-vividly-redis-subnet"
  ip_cidr_range = var.redis_subnet_cidr  # e.g., "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.redis_network.id
  project       = var.project_id

  description = "Subnet for Redis instance"

  # Enable VPC Flow Logs for security monitoring
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# Subnet for VPC Serverless Connector (Cloud Run → Redis)
resource "google_compute_subnetwork" "serverless_connector_subnet" {
  name          = "${var.environment}-vividly-serverless-connector-subnet"
  ip_cidr_range = var.serverless_connector_cidr  # e.g., "10.10.1.0/28" (16 IPs)
  region        = var.region
  network       = google_compute_network.redis_network.id
  project       = var.project_id

  description = "Subnet for VPC Serverless Connector to enable Cloud Run access to Redis"
}

# -----------------------------------------------------------------------------
# Firewall Rules
# -----------------------------------------------------------------------------

# Allow Redis traffic from serverless connector subnet
resource "google_compute_firewall" "allow_redis_from_serverless" {
  name    = "${var.environment}-vividly-allow-redis-from-serverless"
  network = google_compute_network.redis_network.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["6379"]  # Redis default port
  }

  source_ranges = [var.serverless_connector_cidr]
  target_tags   = ["redis-instance"]

  description = "Allow Redis traffic from VPC Serverless Connector subnet"
}

# Allow internal health checks
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${var.environment}-vividly-allow-health-checks"
  network = google_compute_network.redis_network.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }

  # Google Cloud health check IP ranges
  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16"
  ]

  target_tags = ["redis-instance"]

  description = "Allow Google Cloud health checks to Redis instance"
}

# -----------------------------------------------------------------------------
# Cloud Memorystore (Redis) Instance
# -----------------------------------------------------------------------------

resource "google_redis_instance" "notifications_redis" {
  name               = "${var.environment}-vividly-notifications-redis"
  tier               = var.redis_tier  # "BASIC" for dev, "STANDARD_HA" for prod
  memory_size_gb     = var.redis_memory_size_gb  # 1 GB for dev, 5 GB for prod
  region             = var.region
  project            = var.project_id

  # Redis version (6.x for modern features, 7.x for latest)
  redis_version      = "REDIS_7_0"

  # Network configuration
  authorized_network = google_compute_network.redis_network.id
  connect_mode       = "DIRECT_PEERING"

  # Display name for GCP Console
  display_name       = "${var.environment} Vividly Notifications Redis"

  # Configuration for performance and reliability
  redis_configs = {
    # Pub/Sub optimizations
    "maxmemory-policy"      = "volatile-lru"  # Evict expired keys first
    "notify-keyspace-events" = "Ex"           # Enable expiration notifications

    # Connection limits (adjust based on expected load)
    "maxclients"            = var.redis_max_clients  # 10000 for dev, 50000 for prod

    # Timeout for idle connections (5 minutes)
    "timeout"               = "300"
  }

  # Maintenance window (Sunday 2 AM UTC = Saturday 6 PM PST)
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }

  # Labels for organization and cost tracking
  labels = {
    environment = var.environment
    component   = "notifications"
    phase       = "1-4"
    managed-by  = "terraform"
    cost-center = "infrastructure"
  }

  # Lifecycle management
  lifecycle {
    prevent_destroy = false  # Set to true for production after initial deployment

    # Ignore changes to labels that might be added via GCP Console
    ignore_changes = [
      labels["updated-by"],
      labels["last-modified"]
    ]
  }

  # Dependencies
  depends_on = [
    google_compute_network.redis_network,
    google_compute_subnetwork.redis_subnet,
    google_project_service.required_apis
  ]
}

# -----------------------------------------------------------------------------
# VPC Serverless Connector (Cloud Run → Redis)
# -----------------------------------------------------------------------------

resource "google_vpc_access_connector" "serverless_to_redis" {
  name          = "${var.environment}-vividly-serverless-redis-connector"
  region        = var.region
  project       = var.project_id

  # Use dedicated subnet
  subnet {
    name       = google_compute_subnetwork.serverless_connector_subnet.name
    project_id = var.project_id
  }

  # Throughput configuration
  # min_throughput: 200 Mbps (dev), 300 Mbps (prod)
  # max_throughput: 300 Mbps (dev), 1000 Mbps (prod)
  min_throughput = var.serverless_connector_min_throughput
  max_throughput = var.serverless_connector_max_throughput

  # Machine type for connector instances
  # e2-micro: 2 vCPU, 1 GB RAM (dev)
  # e2-standard-4: 4 vCPU, 16 GB RAM (prod)
  machine_type = var.serverless_connector_machine_type

  # Min/max instances for autoscaling
  min_instances = var.serverless_connector_min_instances
  max_instances = var.serverless_connector_max_instances

  depends_on = [
    google_compute_subnetwork.serverless_connector_subnet,
    google_project_service.required_apis
  ]
}

# -----------------------------------------------------------------------------
# Secret Manager for Redis Credentials
# -----------------------------------------------------------------------------

# Store Redis host
resource "google_secret_manager_secret" "redis_host" {
  secret_id = "${var.environment}-redis-host"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    component   = "notifications"
    phase       = "1-4"
  }
}

resource "google_secret_manager_secret_version" "redis_host_version" {
  secret      = google_secret_manager_secret.redis_host.id
  secret_data = google_redis_instance.notifications_redis.host

  depends_on = [google_redis_instance.notifications_redis]
}

# Store Redis port
resource "google_secret_manager_secret" "redis_port" {
  secret_id = "${var.environment}-redis-port"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    component   = "notifications"
    phase       = "1-4"
  }
}

resource "google_secret_manager_secret_version" "redis_port_version" {
  secret      = google_secret_manager_secret.redis_port.id
  secret_data = tostring(google_redis_instance.notifications_redis.port)

  depends_on = [google_redis_instance.notifications_redis]
}

# -----------------------------------------------------------------------------
# IAM Permissions for Cloud Run Services
# -----------------------------------------------------------------------------

# Grant Cloud Run services access to Redis connection secrets
resource "google_secret_manager_secret_iam_member" "redis_host_accessor" {
  secret_id = google_secret_manager_secret.redis_host.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_service_account}"
  project   = var.project_id
}

resource "google_secret_manager_secret_iam_member" "redis_port_accessor" {
  secret_id = google_secret_manager_secret.redis_port.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.cloud_run_service_account}"
  project   = var.project_id
}

# -----------------------------------------------------------------------------
# Monitoring & Alerting
# -----------------------------------------------------------------------------

# Monitoring alert for high memory usage (>80%)
resource "google_monitoring_alert_policy" "redis_high_memory" {
  display_name = "${var.environment} - Redis High Memory Usage"
  project      = var.project_id

  combiner = "OR"

  conditions {
    display_name = "Redis memory usage > 80%"

    condition_threshold {
      filter          = "resource.type = \"redis_instance\" AND resource.labels.instance_id = \"${google_redis_instance.notifications_redis.id}\" AND metric.type = \"redis.googleapis.com/stats/memory/usage_ratio\""
      duration        = "300s"  # 5 minutes
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8  # 80%

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.alert_notification_channels

  alert_strategy {
    auto_close = "604800s"  # 7 days
  }

  documentation {
    content   = "Redis instance ${google_redis_instance.notifications_redis.name} is using more than 80% of allocated memory. Consider scaling up the instance or optimizing notification retention policies."
    mime_type = "text/markdown"
  }
}

# Monitoring alert for high connection count (>90% of max)
resource "google_monitoring_alert_policy" "redis_high_connections" {
  display_name = "${var.environment} - Redis High Connection Count"
  project      = var.project_id

  combiner = "OR"

  conditions {
    display_name = "Redis connections > 90% of max"

    condition_threshold {
      filter          = "resource.type = \"redis_instance\" AND resource.labels.instance_id = \"${google_redis_instance.notifications_redis.id}\" AND metric.type = \"redis.googleapis.com/clients/connected\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.redis_max_clients * 0.9

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.alert_notification_channels

  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "Redis instance ${google_redis_instance.notifications_redis.name} has more than 90% of maximum connections in use. This may indicate a connection leak or the need to scale Cloud Run instances."
    mime_type = "text/markdown"
  }
}

# Monitoring dashboard for Redis metrics
resource "google_monitoring_dashboard" "redis_dashboard" {
  dashboard_json = jsonencode({
    displayName = "${var.environment} - Redis Notifications Dashboard"

    gridLayout = {
      widgets = [
        {
          title = "Memory Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.notifications_redis.id}\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
              plotType = "LINE"
            }]
          }
        },
        {
          title = "Connected Clients"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.notifications_redis.id}\" AND metric.type=\"redis.googleapis.com/clients/connected\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
              plotType = "LINE"
            }]
          }
        },
        {
          title = "Commands Processed (Pub/Sub)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.notifications_redis.id}\" AND metric.type=\"redis.googleapis.com/commands/total_commands\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
              plotType = "LINE"
            }]
          }
        },
        {
          title = "Network Traffic"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"redis_instance\" AND resource.labels.instance_id=\"${google_redis_instance.notifications_redis.id}\" AND metric.type=\"redis.googleapis.com/stats/network_traffic\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
                plotType = "LINE"
              }
            ]
          }
        }
      ]
    }
  })

  project = var.project_id
}

# -----------------------------------------------------------------------------
# Outputs (exported to outputs.tf)
# -----------------------------------------------------------------------------

# These outputs will be referenced in outputs.tf
