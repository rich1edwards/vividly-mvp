# Staging Environment Configuration

project_id  = "vividly-staging"  # TODO: Replace with your actual GCP project ID
environment = "staging"
region      = "us-central1"

subnet_cidr = "10.20.0.0/24"

# Mid-tier resources for staging
db_tier      = "db-custom-2-7680"  # 2 vCPU, 7.5 GB RAM
db_disk_size = 100

# TODO: Add notification channels after creating them in GCP
# notification_channels = [
#   "projects/vividly-staging/notificationChannels/1234567890"
# ]

domain = "staging.vividly.mnps.edu"  # TODO: Update with actual staging domain
