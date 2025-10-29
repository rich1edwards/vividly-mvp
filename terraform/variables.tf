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

variable "redis_memory_size" {
  description = "Redis instance memory size in GB"
  type        = number
  default     = 1
}

variable "redis_reserved_ip_range" {
  description = "Reserved IP range for Redis instance (e.g., 10.0.1.0/29)"
  type        = string
  default     = "10.0.1.0/29"
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

variable "cdn_domain" {
  description = "Custom domain for CDN (for SSL certificate)"
  type        = string
  default     = ""
}

variable "vpc_connector_cidr" {
  description = "CIDR range for VPC connector (must be /28)"
  type        = string
  default     = "10.8.0.0/28"
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "cloud_run_cpu" {
  description = "CPU allocation for Cloud Run (e.g., '1', '2', '4')"
  type        = string
  default     = "2"
}

variable "cloud_run_memory" {
  description = "Memory allocation for Cloud Run (e.g., '512Mi', '1Gi', '2Gi')"
  type        = string
  default     = "2Gi"
}

variable "cors_origins" {
  description = "Allowed CORS origins for the API"
  type        = list(string)
  default     = ["http://localhost:3000", "http://localhost:5173"]
}
