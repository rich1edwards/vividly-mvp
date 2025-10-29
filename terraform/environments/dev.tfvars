# Development Environment Configuration

project_id  = "vividly-dev-rich"
environment = "dev"
region      = "us-central1"

subnet_cidr = "10.10.0.0/24"

# Minimal resources for development
db_tier      = "db-custom-1-3840"  # 1 vCPU, 3.75 GB RAM
db_disk_size = 50

# Redis configuration
redis_memory_size       = 1
redis_reserved_ip_range = "10.10.1.0/29"

# TODO: Add notification channels after creating them in GCP
# notification_channels = [
#   "projects/vividly-dev/notificationChannels/1234567890"
# ]

domain = ""  # No custom domain for dev
