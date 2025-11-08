# Development Environment Configuration

project_id  = "vividly-dev-rich"
environment = "dev"
region      = "us-central1"

subnet_cidr = "10.10.0.0/24"

# Minimal resources for development
db_tier      = "db-custom-1-3840"  # 1 vCPU, 3.75 GB RAM
db_disk_size = 50

# Redis configuration (Phase 1.4 - Real-Time Notifications)
redis_memory_size       = 1
redis_reserved_ip_range = "10.10.1.0/29"
redis_subnet_cidr       = "10.10.0.0/24"
redis_tier              = "BASIC"
redis_memory_size_gb    = 1
redis_max_clients       = 10000

# VPC Serverless Connector (for Cloud Run -> Redis)
serverless_connector_cidr            = "10.10.1.0/28"
serverless_connector_min_throughput  = 200
serverless_connector_max_throughput  = 300
serverless_connector_machine_type    = "e2-micro"
serverless_connector_min_instances   = 2
serverless_connector_max_instances   = 3

# Cloud Run configuration
cloud_run_max_instances = 5
cloud_run_cpu           = "1"
cloud_run_memory        = "1Gi"
cloud_run_service_account = "dev-cloud-run-sa@vividly-dev-rich.iam.gserviceaccount.com"

# CORS configuration
cors_origins = ["http://localhost:5173", "http://localhost:3000"]

# Monitoring
# TODO: Add notification channels after creating them in GCP
# notification_channels = [
#   "projects/vividly-dev-rich/notificationChannels/1234567890"
# ]
alert_notification_channels = []

# Domain configuration
domain     = ""  # No custom domain for dev
cdn_domain = ""  # No CDN domain for dev
