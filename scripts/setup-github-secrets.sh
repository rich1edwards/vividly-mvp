#!/bin/bash
# Set up GitHub Actions secrets for Vividly CI/CD

set -e  # Exit on error

echo "========================================="
echo "GitHub Actions Secrets Setup"
echo "========================================="

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Not authenticated with GitHub."
    gh auth login
fi

echo ""
echo "This script will help you set up GitHub Actions secrets."
echo "You'll need the following information:"
echo "  - GCP Project IDs (dev, staging, prod)"
echo "  - GCP Service Account emails"
echo "  - Workload Identity Provider"
echo ""
read -p "Press Enter to continue..."

# Repository name
read -p "Enter repository (format: owner/repo): " REPO

# Development secrets
echo ""
echo "========================================="
echo "Development Environment Secrets"
echo "========================================="

read -p "GCP Dev Project ID: " GCP_DEV_PROJECT_ID
gh secret set GCP_DEV_PROJECT_ID --body "$GCP_DEV_PROJECT_ID" --repo "$REPO"
echo "✓ GCP_DEV_PROJECT_ID set"

read -p "Dev API URL (leave blank if not deployed yet): " DEV_API_URL
if [ ! -z "$DEV_API_URL" ]; then
    gh secret set DEV_API_URL --body "$DEV_API_URL" --repo "$REPO"
    echo "✓ DEV_API_URL set"
fi

# Staging secrets
echo ""
echo "========================================="
echo "Staging Environment Secrets"
echo "========================================="

read -p "GCP Staging Project ID: " GCP_STAGING_PROJECT_ID
gh secret set GCP_STAGING_PROJECT_ID --body "$GCP_STAGING_PROJECT_ID" --repo "$REPO"
echo "✓ GCP_STAGING_PROJECT_ID set"

read -p "Staging service account email: " GCP_STAGING_SERVICE_ACCOUNT
gh secret set GCP_STAGING_SERVICE_ACCOUNT --body "$GCP_STAGING_SERVICE_ACCOUNT" --repo "$REPO"
echo "✓ GCP_STAGING_SERVICE_ACCOUNT set"

read -p "Staging API URL (leave blank if not deployed yet): " STAGING_API_URL
if [ ! -z "$STAGING_API_URL" ]; then
    gh secret set STAGING_API_URL --body "$STAGING_API_URL" --repo "$REPO"
    echo "✓ STAGING_API_URL set"
fi

read -p "Staging Frontend URL (leave blank if not deployed yet): " STAGING_FRONTEND_URL
if [ ! -z "$STAGING_FRONTEND_URL" ]; then
    gh secret set STAGING_FRONTEND_URL --body "$STAGING_FRONTEND_URL" --repo "$REPO"
    echo "✓ STAGING_FRONTEND_URL set"
fi

# Production secrets
echo ""
echo "========================================="
echo "Production Environment Secrets"
echo "========================================="

read -p "GCP Production Project ID: " GCP_PROD_PROJECT_ID
gh secret set GCP_PROD_PROJECT_ID --body "$GCP_PROD_PROJECT_ID" --repo "$REPO"
echo "✓ GCP_PROD_PROJECT_ID set"

read -p "Production service account email: " GCP_PROD_SERVICE_ACCOUNT
gh secret set GCP_PROD_SERVICE_ACCOUNT --body "$GCP_PROD_SERVICE_ACCOUNT" --repo "$REPO"
echo "✓ GCP_PROD_SERVICE_ACCOUNT set"

read -p "Production API URL (leave blank if not deployed yet): " PROD_API_URL
if [ ! -z "$PROD_API_URL" ]; then
    gh secret set PROD_API_URL --body "$PROD_API_URL" --repo "$REPO"
    echo "✓ PROD_API_URL set"
fi

# Workload Identity (shared across environments)
echo ""
echo "========================================="
echo "Workload Identity Configuration"
echo "========================================="
echo ""
echo "To get your Workload Identity Provider, run:"
echo "  gcloud iam workload-identity-pools providers describe github \\"
echo "    --location=global \\"
echo "    --workload-identity-pool=github \\"
echo "    --format='value(name)'"
echo ""

read -p "Workload Identity Provider (full path): " GCP_WORKLOAD_IDENTITY_PROVIDER
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body "$GCP_WORKLOAD_IDENTITY_PROVIDER" --repo "$REPO"
echo "✓ GCP_WORKLOAD_IDENTITY_PROVIDER set"

read -p "Primary GCP Service Account email (for dev): " GCP_SERVICE_ACCOUNT
gh secret set GCP_SERVICE_ACCOUNT --body "$GCP_SERVICE_ACCOUNT" --repo "$REPO"
echo "✓ GCP_SERVICE_ACCOUNT set"

# List all secrets
echo ""
echo "========================================="
echo "Configured Secrets"
echo "========================================="
gh secret list --repo "$REPO"

echo ""
echo "✓ GitHub Actions secrets configured successfully!"
echo ""
echo "Note: You can update API URLs later by re-running this script"
echo "      or manually using: gh secret set SECRET_NAME --repo $REPO"
