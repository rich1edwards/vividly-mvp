"""
Pub/Sub Infrastructure for Async Content Generation

This file defines the Pub/Sub topics and subscriptions needed for async content generation:
- Topic: content-requests-{environment} - Receives content generation requests from API
- Subscription: content-worker-sub-{environment} - Worker reads messages from this subscription
- Dead Letter Topic: content-requests-dlq-{environment} - Failed messages for investigation
- IAM: Proper permissions for API to publish, Worker to subscribe

Architecture:
API → Pub/Sub Topic → Subscription → Content Worker → Database
                          ↓ (after max retries)
                       Dead Letter Queue
"""

# ============================================================================
# Pub/Sub Topic for Content Generation Requests
# ============================================================================

resource "google_pubsub_topic" "content_requests" {
  name = "content-requests-${var.environment}"

  # Message retention: 7 days (Pub/Sub default)
  message_retention_duration = "604800s" # 7 days

  labels = {
    environment = var.environment
    service     = "content-generation"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# ============================================================================
# Dead Letter Topic for Failed Messages
# ============================================================================

resource "google_pubsub_topic" "content_requests_dlq" {
  name = "content-requests-dlq-${var.environment}"

  # Dead letter queue for messages that fail processing after max retries
  message_retention_duration = "604800s" # 7 days

  labels = {
    environment = var.environment
    service     = "content-generation"
    type        = "dead-letter-queue"
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

# ============================================================================
# Pub/Sub Subscription for Content Worker
# ============================================================================

resource "google_pubsub_subscription" "content_worker" {
  name  = "content-worker-sub-${var.environment}"
  topic = google_pubsub_topic.content_requests.name

  # Acknowledgement deadline: 10 minutes (video generation takes time)
  # Worker must ack within this time or message will be redelivered
  ack_deadline_seconds = 600 # 10 minutes

  # Message retention: 7 days
  message_retention_duration = "604800s" # 7 days

  # Retry policy: exponential backoff with max 10 attempts
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s" # 10 minutes
  }

  # Dead letter policy: after 10 failed delivery attempts, send to DLQ
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.content_requests_dlq.id
    max_delivery_attempts = 10
  }

  # Enable exactly-once delivery (requires Worker to be idempotent)
  enable_exactly_once_delivery = true

  # Enable message ordering (preserve order for same student_id)
  enable_message_ordering = true

  # Filter: only process messages for this environment
  # This allows multiple environments to share the same project if needed
  filter = "attributes.environment = \"${var.environment}\""

  labels = {
    environment = var.environment
    service     = "content-generation"
    managed_by  = "terraform"
  }

  depends_on = [
    google_pubsub_topic.content_requests,
    google_pubsub_topic.content_requests_dlq,
  ]
}

# ============================================================================
# IAM: Grant Content Worker Permission to Subscribe
# ============================================================================

# Note: google_service_account.content_worker is defined in main.tf
# We only need to grant Pub/Sub-specific permissions here

# Grant worker permission to subscribe to Pub/Sub
resource "google_pubsub_subscription_iam_member" "content_worker_subscriber" {
  subscription = google_pubsub_subscription.content_worker.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.content_worker.email}"
}

# Grant worker permission to view subscription details
resource "google_pubsub_subscription_iam_member" "content_worker_viewer" {
  subscription = google_pubsub_subscription.content_worker.name
  role         = "roles/pubsub.viewer"
  member       = "serviceAccount:${google_service_account.content_worker.email}"
}

# ============================================================================
# IAM: Grant API Gateway Permission to Publish
# ============================================================================

# Note: google_service_account.api_gateway is defined in main.tf
# Grant API gateway permission to publish to topic
resource "google_pubsub_topic_iam_member" "api_publisher" {
  topic  = google_pubsub_topic.content_requests.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.api_gateway.email}"
}

# ============================================================================
# Monitoring: Pub/Sub Metrics
# ============================================================================

# TODO: Add alerting policies for:
# - High message backlog (> 100 undelivered messages for 5 minutes)
# - Old unacked messages (> 30 minutes)
# Requires: alert_notification_channels variable to be defined in variables.tf

# ============================================================================
# Outputs
# ============================================================================

output "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic for content requests"
  value       = google_pubsub_topic.content_requests.name
}

output "pubsub_subscription_name" {
  description = "Name of the Pub/Sub subscription for content worker"
  value       = google_pubsub_subscription.content_worker.name
}

output "pubsub_dlq_topic_name" {
  description = "Name of the dead letter queue topic"
  value       = google_pubsub_topic.content_requests_dlq.name
}
