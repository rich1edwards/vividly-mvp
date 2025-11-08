# ============================================================================
# Frontend Static Hosting Infrastructure
# ============================================================================
#
# This module provisions:
# - Google Cloud Storage bucket for static assets (React build)
# - Cloud CDN for global content delivery
# - Load balancer with SSL termination
# - Managed SSL certificates for custom domains
# - URL rewrites for SPA routing
#
# Architecture:
#   Internet -> Load Balancer (HTTPS) -> Cloud CDN -> GCS Bucket (React build)
#
# ============================================================================

# ============================================================================
# GCS Bucket for Frontend Assets
# ============================================================================

resource "google_storage_bucket" "frontend" {
  name     = "${var.project_id}-frontend-${var.environment}"
  location = var.region

  # Enable uniform bucket-level access (recommended for public websites)
  uniform_bucket_level_access = true

  # Website configuration
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html" # SPA routing - serve index.html for 404s
  }

  # CORS configuration for API calls from frontend
  cors {
    origin          = var.environment == "prod" ? ["https://${var.domain}"] : ["http://localhost:5173", "https://${var.environment}.${var.domain}"]
    method          = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  # Lifecycle rules to clean up old deployments
  lifecycle_rule {
    condition {
      age                = 90 # Keep builds for 90 days
      num_newer_versions = 3  # Keep last 3 versions
    }
    action {
      type = "Delete"
    }
  }

  # Enable versioning for rollback capability
  versioning {
    enabled = true
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    component   = "frontend"
  }

  depends_on = [google_project_service.required_apis]
}

# Make bucket publicly readable for website hosting
resource "google_storage_bucket_iam_member" "frontend_public_read" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ============================================================================
# Backend Bucket for Load Balancer
# ============================================================================

resource "google_compute_backend_bucket" "frontend" {
  name        = "${var.environment}-vividly-frontend-backend"
  bucket_name = google_storage_bucket.frontend.name
  enable_cdn  = true

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    client_ttl        = 3600  # 1 hour
    default_ttl       = 3600  # 1 hour
    max_ttl           = 86400 # 24 hours
    negative_caching  = true
    serve_while_stale = 86400 # Serve stale content for 24 hours if origin is down

    # Cache key policy moved to newer provider versions
    # Note: cache_key_policy requires google provider >= 5.0
    # For now, CDN will use default cache key (includes host, protocol)

    # Negative caching for 404s
    negative_caching_policy {
      code = 404
      ttl  = 120 # Cache 404s for 2 minutes
    }
  }
}

# ============================================================================
# URL Map for Load Balancer Routing
# ============================================================================

resource "google_compute_url_map" "frontend" {
  name            = "${var.environment}-vividly-frontend-urlmap"
  default_service = google_compute_backend_bucket.frontend.id

  # Redirect all traffic to HTTPS
  host_rule {
    hosts        = var.domain != "" ? ["${var.domain}", "www.${var.domain}"] : ["*"]
    path_matcher = "allpaths"
  }

  path_matcher {
    name            = "allpaths"
    default_service = google_compute_backend_bucket.frontend.id

    # Serve index.html for all paths (SPA routing)
    path_rule {
      paths   = ["/*"]
      service = google_compute_backend_bucket.frontend.id
    }
  }
}

# ============================================================================
# SSL Certificate (Managed)
# ============================================================================

# Only create SSL certificate if custom domain is configured
resource "google_compute_managed_ssl_certificate" "frontend" {
  count = var.domain != "" ? 1 : 0

  name = "${var.environment}-vividly-frontend-cert"

  managed {
    domains = [
      var.domain,
      "www.${var.domain}"
    ]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# HTTPS Proxy
# ============================================================================

resource "google_compute_target_https_proxy" "frontend" {
  count = var.domain != "" ? 1 : 0

  name             = "${var.environment}-vividly-frontend-https-proxy"
  url_map          = google_compute_url_map.frontend.id
  ssl_certificates = [google_compute_managed_ssl_certificate.frontend[0].id]
}

# ============================================================================
# HTTP Proxy (for redirect to HTTPS)
# ============================================================================

resource "google_compute_url_map" "frontend_redirect" {
  count = var.domain != "" ? 1 : 0

  name = "${var.environment}-vividly-frontend-redirect-urlmap"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "frontend_redirect" {
  count = var.domain != "" ? 1 : 0

  name    = "${var.environment}-vividly-frontend-http-proxy"
  url_map = google_compute_url_map.frontend_redirect[0].id
}

# ============================================================================
# Global Forwarding Rules (External IPs)
# ============================================================================

# HTTPS forwarding rule
resource "google_compute_global_forwarding_rule" "frontend_https" {
  count = var.domain != "" ? 1 : 0

  name       = "${var.environment}-vividly-frontend-https-rule"
  target     = google_compute_target_https_proxy.frontend[0].id
  port_range = "443"
  ip_address = google_compute_global_address.frontend[0].address
}

# HTTP forwarding rule (redirect to HTTPS)
resource "google_compute_global_forwarding_rule" "frontend_http" {
  count = var.domain != "" ? 1 : 0

  name       = "${var.environment}-vividly-frontend-http-rule"
  target     = google_compute_target_http_proxy.frontend_redirect[0].id
  port_range = "80"
  ip_address = google_compute_global_address.frontend[0].address
}

# Reserve static external IP address
resource "google_compute_global_address" "frontend" {
  count = var.domain != "" ? 1 : 0

  name = "${var.environment}-vividly-frontend-ip"
}

# ============================================================================
# Cloud Armor Security Policy (Optional - for DDoS protection)
# ============================================================================

# Uncomment to enable Cloud Armor for production
# resource "google_compute_security_policy" "frontend" {
#   count = var.environment == "prod" ? 1 : 0
#
#   name = "${var.environment}-vividly-frontend-security-policy"
#
#   # Rate limiting rule
#   rule {
#     action   = "rate_based_ban"
#     priority = "1000"
#     match {
#       versioned_expr = "SRC_IPS_V1"
#       config {
#         src_ip_ranges = ["*"]
#       }
#     }
#     rate_limit_options {
#       conform_action = "allow"
#       exceed_action  = "deny(429)"
#       enforce_on_key = "IP"
#       ban_duration_sec = 600
#       rate_limit_threshold {
#         count        = 1000
#         interval_sec = 60
#       }
#     }
#   }
#
#   # Default rule - allow all
#   rule {
#     action   = "allow"
#     priority = "2147483647"
#     match {
#       versioned_expr = "SRC_IPS_V1"
#       config {
#         src_ip_ranges = ["*"]
#       }
#     }
#   }
# }

# ============================================================================
# Outputs
# ============================================================================

output "frontend_bucket_name" {
  description = "GCS bucket name for frontend assets"
  value       = google_storage_bucket.frontend.name
}

output "frontend_bucket_url" {
  description = "GCS bucket URL for frontend assets"
  value       = google_storage_bucket.frontend.url
}

output "frontend_external_ip" {
  description = "External IP address for frontend load balancer"
  value       = var.domain != "" ? google_compute_global_address.frontend[0].address : "N/A (no domain configured)"
}

output "frontend_url" {
  description = "Frontend URL (configure DNS A record to point here)"
  value       = var.domain != "" ? "https://${var.domain}" : "No custom domain configured - use GCS bucket URL for testing"
}

output "frontend_cdn_enabled" {
  description = "Whether Cloud CDN is enabled for frontend"
  value       = google_compute_backend_bucket.frontend.enable_cdn
}
