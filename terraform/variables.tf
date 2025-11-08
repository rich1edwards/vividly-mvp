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

# -----------------------------------------------------------------------------
# Phase 1.4: Redis/Memorystore Variables for Notification System
# -----------------------------------------------------------------------------

variable "redis_subnet_cidr" {
  description = "CIDR range for Redis subnet (e.g., '10.10.0.0/24')"
  type        = string
  default     = "10.10.0.0/24"
}

variable "serverless_connector_cidr" {
  description = "CIDR range for VPC Serverless Connector subnet (must be /28, e.g., '10.10.1.0/28')"
  type        = string
  default     = "10.10.1.0/28"

  validation {
    condition     = can(regex("/28$", var.serverless_connector_cidr))
    error_message = "Serverless connector CIDR must be a /28 subnet (16 IP addresses)."
  }
}

variable "redis_tier" {
  description = "Redis instance tier - BASIC (dev) or STANDARD_HA (prod for high availability)"
  type        = string
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be either BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size_gb" {
  description = "Redis instance memory size in GB (1-300 GB)"
  type        = number
  default     = 1

  validation {
    condition     = var.redis_memory_size_gb >= 1 && var.redis_memory_size_gb <= 300
    error_message = "Redis memory size must be between 1 and 300 GB."
  }
}

variable "redis_max_clients" {
  description = "Maximum number of concurrent Redis connections (10000 for dev, 50000 for prod)"
  type        = number
  default     = 10000

  validation {
    condition     = var.redis_max_clients >= 1000 && var.redis_max_clients <= 65000
    error_message = "Redis max clients must be between 1000 and 65000."
  }
}

variable "serverless_connector_min_throughput" {
  description = "Minimum throughput for VPC Serverless Connector in Mbps (200-1000)"
  type        = number
  default     = 200

  validation {
    condition     = var.serverless_connector_min_throughput >= 200 && var.serverless_connector_min_throughput <= 1000
    error_message = "Serverless connector min throughput must be between 200 and 1000 Mbps."
  }
}

variable "serverless_connector_max_throughput" {
  description = "Maximum throughput for VPC Serverless Connector in Mbps (200-1000)"
  type        = number
  default     = 300

  validation {
    condition     = var.serverless_connector_max_throughput >= 200 && var.serverless_connector_max_throughput <= 1000
    error_message = "Serverless connector max throughput must be between 200 and 1000 Mbps."
  }
}

variable "serverless_connector_machine_type" {
  description = "Machine type for VPC Serverless Connector (e2-micro for dev, e2-standard-4 for prod)"
  type        = string
  default     = "e2-micro"

  validation {
    condition     = contains(["e2-micro", "e2-small", "e2-medium", "e2-standard-4"], var.serverless_connector_machine_type)
    error_message = "Serverless connector machine type must be one of: e2-micro, e2-small, e2-medium, e2-standard-4."
  }
}

variable "serverless_connector_min_instances" {
  description = "Minimum number of VPC Serverless Connector instances (2-10)"
  type        = number
  default     = 2

  validation {
    condition     = var.serverless_connector_min_instances >= 2 && var.serverless_connector_min_instances <= 10
    error_message = "Serverless connector min instances must be between 2 and 10."
  }
}

variable "serverless_connector_max_instances" {
  description = "Maximum number of VPC Serverless Connector instances (3-10)"
  type        = number
  default     = 10

  validation {
    condition     = var.serverless_connector_max_instances >= 3 && var.serverless_connector_max_instances <= 10
    error_message = "Serverless connector max instances must be between 3 and 10."
  }
}

variable "cloud_run_service_account" {
  description = "Service account email for Cloud Run services (for IAM permissions)"
  type        = string
}

variable "alert_notification_channels" {
  description = "List of notification channel IDs for Cloud Monitoring alerts"
  type        = list(string)
  default     = []
}
