# Staging Environment Configuration

project_id  = "vividly-staging"  # TODO: Replace with your actual GCP project ID
environment = "staging"
region      = "us-central1"

subnet_cidr = "10.20.0.0/24"

# Mid-tier resources for staging
db_tier      = "db-custom-2-7680"  # 2 vCPU, 7.5 GB RAM
db_disk_size = 100

# Redis configuration (Phase 1.4 - Real-Time Notifications)
redis_memory_size       = 2
redis_reserved_ip_range = "10.20.1.0/29"
redis_subnet_cidr       = "10.20.0.0/24"
redis_tier              = "BASIC"  # Consider STANDARD_HA for prod-like testing
redis_memory_size_gb    = 2
redis_max_clients       = 20000

# VPC Serverless Connector (for Cloud Run -> Redis)
serverless_connector_cidr            = "10.20.1.0/28"
serverless_connector_min_throughput  = 200
serverless_connector_max_throughput  = 500
serverless_connector_machine_type    = "e2-small"
serverless_connector_min_instances   = 2
serverless_connector_max_instances   = 5

# Cloud Run configuration
cloud_run_max_instances = 10
cloud_run_cpu           = "2"
cloud_run_memory        = "2Gi"
cloud_run_service_account = "staging-cloud-run-sa@vividly-staging.iam.gserviceaccount.com"

# CORS configuration
cors_origins = [
  "https://staging.vividly.mnps.edu",
  "http://localhost:5173"  # For local testing
]

# Monitoring
# TODO: Add notification channels after creating them in GCP
# notification_channels = [
#   "projects/vividly-staging/notificationChannels/1234567890"
# ]
alert_notification_channels = []

# Domain configuration
domain     = "staging.vividly.mnps.edu"  # TODO: Update with actual staging domain
cdn_domain = "staging.vividly.mnps.edu"
