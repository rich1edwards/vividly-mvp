# Production Environment Configuration

project_id  = "vividly-prod"  # TODO: Replace with your actual GCP project ID
environment = "prod"
region      = "us-central1"

subnet_cidr = "10.30.0.0/24"

# High-tier resources for production
db_tier      = "db-custom-4-15360"  # 4 vCPU, 15 GB RAM
db_disk_size = 500

# TODO: Add notification channels after creating them in GCP
# These should include email, Slack, PagerDuty, etc.
# notification_channels = [
#   "projects/vividly-prod/notificationChannels/1234567890",
#   "projects/vividly-prod/notificationChannels/0987654321"
# ]

domain = "vividly.mnps.edu"  # TODO: Update with actual production domain
