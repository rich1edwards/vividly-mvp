# Sprint 3 Phase 4: Monitoring Dashboard Deployment
# Following Andrew Ng's "Build it right" principle with Infrastructure as Code
# Deploys GCP Cloud Monitoring dashboards for Vividly platform metrics

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables for multi-environment deployment
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Dashboard JSON configuration file
locals {
  dashboard_config_path = "${path.module}/../dashboards/vividly-metrics-overview.json"
  dashboard_config      = jsondecode(file(local.dashboard_config_path))
}

# Main metrics overview dashboard
resource "google_monitoring_dashboard" "vividly_metrics_overview" {
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName  = "${title(var.environment)} - ${local.dashboard_config.displayName}"
    mosaicLayout = local.dashboard_config.mosaicLayout
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Outputs for verification and CI/CD
output "dashboard_id" {
  description = "The ID of the deployed dashboard"
  value       = google_monitoring_dashboard.vividly_metrics_overview.id
}

output "dashboard_name" {
  description = "The name of the deployed dashboard"
  value       = google_monitoring_dashboard.vividly_metrics_overview.dashboard_json
}

output "dashboard_url" {
  description = "Direct URL to view the dashboard in GCP Console"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${replace(google_monitoring_dashboard.vividly_metrics_overview.id, "projects/${var.project_id}/dashboards/", "")}?project=${var.project_id}"
}

output "verification_status" {
  description = "Dashboard deployment verification"
  value = {
    deployed      = true
    environment   = var.environment
    project       = var.project_id
    config_source = local.dashboard_config_path
  }
}
