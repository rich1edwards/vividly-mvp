variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "subnet_cidr" {
  description = "CIDR range for VPC subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-7680" # 2 vCPU, 7.5 GB RAM
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 100
}

variable "notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

variable "domain" {
  description = "Custom domain for the application"
  type        = string
  default     = ""
}
