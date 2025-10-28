#!/bin/bash
# Set up Workload Identity Federation for GitHub Actions
# This allows GitHub Actions to authenticate to GCP without service account keys

set -e  # Exit on error

echo "========================================="
echo "Workload Identity Federation Setup"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    exit 1
fi

# Get configuration
read -p "Enter GCP Project ID: " PROJECT_ID
read -p "Enter GitHub repository (format: owner/repo): " GITHUB_REPO
read -p "Enter environment (dev/staging/prod): " ENV

# Extract owner and repo
IFS='/' read -r GITHUB_OWNER GITHUB_REPO_NAME <<< "$GITHUB_REPO"

# Set project
gcloud config set project "$PROJECT_ID"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

echo ""
echo "========================================="
echo "Configuration"
echo "========================================="
echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "GitHub Repository: $GITHUB_REPO"
echo "Environment: $ENV"
echo "========================================="

# Create Workload Identity Pool
POOL_NAME="github"
POOL_DISPLAY_NAME="GitHub Actions Pool"

echo ""
echo "Creating Workload Identity Pool..."
if gcloud iam workload-identity-pools describe "$POOL_NAME" \
    --location=global \
    --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "✓ Workload Identity Pool already exists"
else
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --project="$PROJECT_ID" \
        --location=global \
        --display-name="$POOL_DISPLAY_NAME"

    echo "✓ Workload Identity Pool created"
fi

# Create Workload Identity Provider
PROVIDER_NAME="github"
PROVIDER_DISPLAY_NAME="GitHub Provider"

echo ""
echo "Creating Workload Identity Provider..."
if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --location=global \
    --workload-identity-pool="$POOL_NAME" \
    --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "✓ Workload Identity Provider already exists"
else
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --project="$PROJECT_ID" \
        --location=global \
        --workload-identity-pool="$POOL_NAME" \
        --display-name="$PROVIDER_DISPLAY_NAME" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
        --issuer-uri="https://token.actions.githubusercontent.com"

    echo "✓ Workload Identity Provider created"
fi

# Get the full provider resource name
PROVIDER_RESOURCE_NAME="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"

# Bind service account to workload identity
SERVICE_ACCOUNT="${ENV}-cicd@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo "Binding service account to Workload Identity..."
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT" \
    --project="$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_REPO}"

echo "✓ Service account bound to Workload Identity"

# Grant necessary permissions to CI/CD service account
echo ""
echo "Granting permissions to CI/CD service account..."

ROLES=(
    "roles/run.admin"
    "roles/cloudfunctions.admin"
    "roles/storage.admin"
    "roles/artifactregistry.writer"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.editor"
)

for ROLE in "${ROLES[@]}"; do
    echo "  Granting $ROLE..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="$ROLE" \
        --condition=None \
        --quiet
done

echo "✓ Permissions granted"

echo ""
echo "========================================="
echo "✓ Workload Identity Setup Complete!"
echo "========================================="
echo ""
echo "Add these secrets to your GitHub repository:"
echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER:"
echo "  $PROVIDER_RESOURCE_NAME"
echo ""
echo "GCP_SERVICE_ACCOUNT (for $ENV):"
echo "  $SERVICE_ACCOUNT"
echo ""
echo "Commands to set GitHub secrets:"
echo ""
echo "gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER \\"
echo "  --body \"$PROVIDER_RESOURCE_NAME\" \\"
echo "  --repo \"$GITHUB_REPO\""
echo ""
echo "gh secret set GCP_${ENV^^}_SERVICE_ACCOUNT \\"
echo "  --body \"$SERVICE_ACCOUNT\" \\"
echo "  --repo \"$GITHUB_REPO\""
echo ""
echo "See setup-github-secrets.sh for a guided setup process."
