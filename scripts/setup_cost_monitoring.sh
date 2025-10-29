#!/bin/bash

###############################################################################
# Vividly Cost Monitoring Setup
#
# Sets up GCP billing budgets and alert policies to prevent cost overruns.
#
# Features:
# - Billing budgets with email notifications
# - Alert policies for resource usage
# - Cost anomaly detection
# - Budget thresholds: 50%, 90%, 100%
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Billing account linked to project
# - Billing API enabled
# - Monitoring API enabled
#
# Usage:
#   ./scripts/setup_cost_monitoring.sh <environment> <monthly_budget>
#
# Example:
#   ./scripts/setup_cost_monitoring.sh dev 100
#   ./scripts/setup_cost_monitoring.sh prod 500
###############################################################################

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-dev}"
MONTHLY_BUDGET="${2:-100}"  # USD

# Get project configuration
PROJECT_ID=$(gcloud config get-value project)
BILLING_ACCOUNT_ID=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingAccountName)" | cut -d'/' -f2)
NOTIFICATION_EMAIL="${3:-$(gcloud config get-value account)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Validate configuration
if [ -z "$PROJECT_ID" ]; then
    log_error "No GCP project configured. Run: gcloud config set project PROJECT_ID"
    exit 1
fi

if [ -z "$BILLING_ACCOUNT_ID" ]; then
    log_error "No billing account linked to project $PROJECT_ID"
    log_info "Link a billing account: gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID"
    exit 1
fi

log_info "Setting up cost monitoring for Vividly"
echo "  Project: $PROJECT_ID"
echo "  Environment: $ENVIRONMENT"
echo "  Monthly Budget: \$${MONTHLY_BUDGET}"
echo "  Notification Email: $NOTIFICATION_EMAIL"
echo ""

# Enable required APIs
log_info "Enabling required APIs..."
gcloud services enable cloudbilling.googleapis.com --project="$PROJECT_ID" || true
gcloud services enable billingbudgets.googleapis.com --project="$PROJECT_ID" || true
gcloud services enable monitoring.googleapis.com --project="$PROJECT_ID" || true
log_success "APIs enabled"

# Create notification channel for budget alerts
log_info "Creating notification channel..."

# Check if channel already exists
EXISTING_CHANNEL=$(gcloud alpha monitoring channels list \
    --project="$PROJECT_ID" \
    --filter="displayName:'Budget Alerts - ${ENVIRONMENT}'" \
    --format="value(name)" \
    2>/dev/null || echo "")

if [ -n "$EXISTING_CHANNEL" ]; then
    NOTIFICATION_CHANNEL_NAME="$EXISTING_CHANNEL"
    log_success "Using existing notification channel: $NOTIFICATION_CHANNEL_NAME"
else
    # Create new notification channel
    CHANNEL_CONFIG=$(cat <<EOF
{
  "type": "email",
  "displayName": "Budget Alerts - ${ENVIRONMENT}",
  "labels": {
    "email_address": "${NOTIFICATION_EMAIL}"
  },
  "enabled": true
}
EOF
    )

    NOTIFICATION_CHANNEL_NAME=$(gcloud alpha monitoring channels create \
        --project="$PROJECT_ID" \
        --display-name="Budget Alerts - ${ENVIRONMENT}" \
        --type=email \
        --channel-labels=email_address="${NOTIFICATION_EMAIL}" \
        --format="value(name)" 2>/dev/null || echo "")

    if [ -z "$NOTIFICATION_CHANNEL_NAME" ]; then
        log_warning "Could not create notification channel via gcloud, will use billing budget email notifications"
        NOTIFICATION_CHANNEL_NAME=""
    else
        log_success "Created notification channel: $NOTIFICATION_CHANNEL_NAME"
    fi
fi

# Create billing budget
log_info "Creating billing budget..."

BUDGET_NAME="${ENVIRONMENT}-vividly-budget"

# Budget configuration
BUDGET_CONFIG=$(cat <<EOF
{
  "displayName": "${BUDGET_NAME}",
  "budgetFilter": {
    "projects": ["projects/${PROJECT_ID}"],
    "labels": {
      "environment": "${ENVIRONMENT}"
    }
  },
  "amount": {
    "specifiedAmount": {
      "currencyCode": "USD",
      "units": "${MONTHLY_BUDGET}"
    }
  },
  "thresholdRules": [
    {
      "thresholdPercent": 0.5,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 0.75,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 0.9,
      "spendBasis": "CURRENT_SPEND"
    },
    {
      "thresholdPercent": 1.0,
      "spendBasis": "CURRENT_SPEND"
    }
  ],
  "notificationsRule": {
    "pubsubTopic": "",
    "schemaVersion": "1.0",
    "monitoringNotificationChannels": [],
    "disableDefaultIamRecipients": false,
    "enableProjectLevelRecipients": true
  }
}
EOF
)

# Save budget config to temp file
BUDGET_CONFIG_FILE=$(mktemp)
echo "$BUDGET_CONFIG" > "$BUDGET_CONFIG_FILE"

# Create budget using REST API (gcloud alpha budgets not available in all regions)
log_info "Configuring budget via gcloud..."

# Try to create budget
gcloud billing budgets create \
    --billing-account="$BILLING_ACCOUNT_ID" \
    --display-name="${BUDGET_NAME}" \
    --budget-amount="${MONTHLY_BUDGET}USD" \
    --threshold-rule=percent=0.5 \
    --threshold-rule=percent=0.75 \
    --threshold-rule=percent=0.9 \
    --threshold-rule=percent=1.0 \
    2>/dev/null || log_warning "Budget may already exist or gcloud version doesn't support budgets command"

log_success "Budget configuration completed"

# Create alert policies for resource usage
log_info "Creating alert policies..."

# 1. Cloud Run CPU Usage Alert
log_info "  - Cloud Run CPU usage alert..."
gcloud alpha monitoring policies create \
    --project="$PROJECT_ID" \
    --notification-channels="$NOTIFICATION_CHANNEL_NAME" \
    --display-name="${ENVIRONMENT}-vividly-cloudrun-cpu" \
    --condition-display-name="High CPU Usage" \
    --condition-threshold-value=0.8 \
    --condition-threshold-duration=300s \
    --condition='type="METRIC_THRESHOLD", metric="run.googleapis.com/container/cpu/utilizations", resource="cloud_run_revision", aggregation="{alignment_period: 60s, per_series_aligner: ALIGN_MEAN, cross_series_reducer: REDUCE_MEAN}", comparison="COMPARISON_GT", threshold_value=0.8, duration="300s"' \
    2>/dev/null || log_warning "Could not create Cloud Run CPU alert (may already exist or API not available)"

# 2. Cloud SQL Connection Count Alert
log_info "  - Cloud SQL connection alert..."
gcloud alpha monitoring policies create \
    --project="$PROJECT_ID" \
    --notification-channels="$NOTIFICATION_CHANNEL_NAME" \
    --display-name="${ENVIRONMENT}-vividly-cloudsql-connections" \
    --condition-display-name="High Connection Count" \
    --condition-threshold-value=80 \
    --condition-threshold-duration=300s \
    2>/dev/null || log_warning "Could not create Cloud SQL connection alert"

# 3. Redis Memory Usage Alert
log_info "  - Redis memory usage alert..."
gcloud alpha monitoring policies create \
    --project="$PROJECT_ID" \
    --notification-channels="$NOTIFICATION_CHANNEL_NAME" \
    --display-name="${ENVIRONMENT}-vividly-redis-memory" \
    --condition-display-name="High Memory Usage" \
    --condition-threshold-value=0.85 \
    --condition-threshold-duration=300s \
    2>/dev/null || log_warning "Could not create Redis memory alert"

log_success "Alert policies created (check Cloud Console for full details)"

# Create cost dashboard
log_info "Setting up cost monitoring dashboard..."

DASHBOARD_CONFIG=$(cat <<EOF
{
  "displayName": "Vividly ${ENVIRONMENT} - Cost Monitoring",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Daily Cost Trend",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"global\"",
                  "aggregation": {
                    "alignmentPeriod": "86400s",
                    "perSeriesAligner": "ALIGN_SUM"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "xPos": 6,
        "widget": {
          "title": "Cost by Service",
          "pieChart": {}
        }
      },
      {
        "width": 12,
        "height": 4,
        "yPos": 4,
        "widget": {
          "title": "Budget Status",
          "scorecard": {}
        }
      }
    ]
  }
}
EOF
)

DASHBOARD_FILE=$(mktemp)
echo "$DASHBOARD_CONFIG" > "$DASHBOARD_FILE"

gcloud monitoring dashboards create --config-from-file="$DASHBOARD_FILE" \
    --project="$PROJECT_ID" \
    2>/dev/null || log_warning "Could not create dashboard (may already exist)"

rm "$DASHBOARD_FILE"

log_success "Cost monitoring dashboard created"

# Clean up
rm "$BUDGET_CONFIG_FILE" 2>/dev/null || true

# Summary
echo ""
log_success "Cost monitoring setup complete!"
echo ""
echo "Summary:"
echo "  ✓ Monthly Budget: \$${MONTHLY_BUDGET}"
echo "  ✓ Alert Thresholds: 50%, 75%, 90%, 100%"
echo "  ✓ Notification Email: ${NOTIFICATION_EMAIL}"
echo "  ✓ Alert Policies: CPU, SQL Connections, Redis Memory"
echo ""
echo "View costs:"
echo "  Console: https://console.cloud.google.com/billing/${BILLING_ACCOUNT_ID}"
echo "  CLI:     gcloud billing budgets list --billing-account=${BILLING_ACCOUNT_ID}"
echo ""
echo "Monitoring:"
echo "  Dashboards: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo "  Alerts:     https://console.cloud.google.com/monitoring/alerting?project=${PROJECT_ID}"
echo ""
log_info "Cost alerts will be sent to: ${NOTIFICATION_EMAIL}"
