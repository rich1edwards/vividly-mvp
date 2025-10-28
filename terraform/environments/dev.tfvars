# Development Environment Configuration

project_id  = "vividly-dev"  # TODO: Replace with your actual GCP project ID
environment = "dev"
region      = "us-central1"

subnet_cidr = "10.10.0.0/24"

# Minimal resources for development
db_tier      = "db-custom-1-3840"  # 1 vCPU, 3.75 GB RAM
db_disk_size = 50

# TODO: Add notification channels after creating them in GCP
# notification_channels = [
#   "projects/vividly-dev/notificationChannels/1234567890"
# ]

domain = ""  # No custom domain for dev
