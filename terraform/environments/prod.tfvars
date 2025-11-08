# Production Environment Configuration

project_id  = "vividly-prod"  # TODO: Replace with your actual GCP project ID
environment = "prod"
region      = "us-central1"

subnet_cidr = "10.30.0.0/24"

# High-tier resources for production
db_tier      = "db-custom-4-15360"  # 4 vCPU, 15 GB RAM
db_disk_size = 500

# Redis configuration (Phase 1.4 - Real-Time Notifications)
# Use STANDARD_HA for high availability in production
redis_memory_size       = 5
redis_reserved_ip_range = "10.30.1.0/29"
redis_subnet_cidr       = "10.30.0.0/24"
redis_tier              = "STANDARD_HA"  # High availability with automatic failover
redis_memory_size_gb    = 5
redis_max_clients       = 50000

# VPC Serverless Connector (for Cloud Run -> Redis)
serverless_connector_cidr            = "10.30.1.0/28"
serverless_connector_min_throughput  = 300
serverless_connector_max_throughput  = 1000
serverless_connector_machine_type    = "e2-standard-4"
serverless_connector_min_instances   = 3
serverless_connector_max_instances   = 10

# Cloud Run configuration
cloud_run_max_instances = 50
cloud_run_cpu           = "4"
cloud_run_memory        = "4Gi"
cloud_run_service_account = "prod-cloud-run-sa@vividly-prod.iam.gserviceaccount.com"

# CORS configuration
cors_origins = [
  "https://vividly.mnps.edu",
  "https://www.vividly.mnps.edu"
]

# Monitoring
# TODO: Add notification channels after creating them in GCP
# These should include email, Slack, PagerDuty, etc.
# notification_channels = [
#   "projects/vividly-prod/notificationChannels/1234567890",
#   "projects/vividly-prod/notificationChannels/0987654321"
# ]
alert_notification_channels = []

# Domain configuration
domain     = "vividly.mnps.edu"  # TODO: Update with actual production domain
cdn_domain = "vividly.mnps.edu"
