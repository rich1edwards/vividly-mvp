#!/bin/bash
# Set up a new GCP project for Vividly

set -e  # Exit on error

echo "========================================="
echo "Vividly GCP Project Setup"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Not authenticated with gcloud."
    gcloud auth login
fi

# Get environment
echo ""
echo "Select environment to set up:"
echo "1) Development"
echo "2) Staging"
echo "3) Production"
read -p "Enter choice (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENV="dev"
        ENV_NAME="Development"
        ;;
    2)
        ENV="staging"
        ENV_NAME="Staging"
        ;;
    3)
        ENV="prod"
        ENV_NAME="Production"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Get project details
read -p "Enter GCP Project ID (e.g., vividly-${ENV}): " PROJECT_ID
read -p "Enter billing account ID: " BILLING_ACCOUNT_ID
read -p "Enter region [us-central1]: " REGION
REGION=${REGION:-us-central1}

echo ""
echo "========================================="
echo "Configuration Summary"
echo "========================================="
echo "Environment: $ENV_NAME"
echo "Project ID: $PROJECT_ID"
echo "Billing Account: $BILLING_ACCOUNT_ID"
echo "Region: $REGION"
echo "========================================="
read -p "Proceed with setup? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create project
echo ""
echo "Creating GCP project..."
if gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    echo "✓ Project $PROJECT_ID already exists"
else
    gcloud projects create "$PROJECT_ID" \
        --name="Vividly $ENV_NAME" \
        --set-as-default
    echo "✓ Project created"
fi

# Link billing account
echo "Linking billing account..."
gcloud billing projects link "$PROJECT_ID" \
    --billing-account="$BILLING_ACCOUNT_ID"
echo "✓ Billing account linked"

# Set default project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo ""
echo "Enabling required APIs (this may take a few minutes)..."

REQUIRED_APIS=(
    "compute.googleapis.com"
    "run.googleapis.com"
    "cloudfunctions.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "sqladmin.googleapis.com"
    "aiplatform.googleapis.com"
    "storage-api.googleapis.com"
    "pubsub.googleapis.com"
    "secretmanager.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iam.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
    "cloudtrace.googleapis.com"
    "cloudprofiler.googleapis.com"
    "servicenetworking.googleapis.com"
)

for API in "${REQUIRED_APIS[@]}"; do
    echo "  Enabling $API..."
    gcloud services enable "$API" --project="$PROJECT_ID" --quiet
done

echo "✓ All APIs enabled"

# Create Terraform state bucket
echo ""
echo "Creating Terraform state bucket..."
STATE_BUCKET="${PROJECT_ID}-terraform-state"

if gcloud storage buckets describe "gs://${STATE_BUCKET}" &> /dev/null; then
    echo "✓ State bucket already exists"
else
    gcloud storage buckets create "gs://${STATE_BUCKET}" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --uniform-bucket-level-access

    gcloud storage buckets update "gs://${STATE_BUCKET}" \
        --versioning

    echo "✓ Terraform state bucket created: gs://${STATE_BUCKET}"
fi

# Create service accounts
echo ""
echo "Creating service accounts..."

# API Gateway service account
SA_API_GATEWAY="${ENV}-api-gateway@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SA_API_GATEWAY" &> /dev/null 2>&1; then
    echo "✓ API Gateway service account exists"
else
    gcloud iam service-accounts create "${ENV}-api-gateway" \
        --display-name="API Gateway Service Account (${ENV_NAME})" \
        --project="$PROJECT_ID"
    echo "✓ API Gateway service account created"
fi

# Admin service account
SA_ADMIN="${ENV}-admin-service@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SA_ADMIN" &> /dev/null 2>&1; then
    echo "✓ Admin service account exists"
else
    gcloud iam service-accounts create "${ENV}-admin-service" \
        --display-name="Admin Service Account (${ENV_NAME})" \
        --project="$PROJECT_ID"
    echo "✓ Admin service account created"
fi

# Content worker service account
SA_WORKER="${ENV}-content-worker@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SA_WORKER" &> /dev/null 2>&1; then
    echo "✓ Content Worker service account exists"
else
    gcloud iam service-accounts create "${ENV}-content-worker" \
        --display-name="Content Worker Service Account (${ENV_NAME})" \
        --project="$PROJECT_ID"
    echo "✓ Content Worker service account created"
fi

# CI/CD service account
SA_CICD="${ENV}-cicd@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe "$SA_CICD" &> /dev/null 2>&1; then
    echo "✓ CI/CD service account exists"
else
    gcloud iam service-accounts create "${ENV}-cicd" \
        --display-name="CI/CD Service Account (${ENV_NAME})" \
        --project="$PROJECT_ID"
    echo "✓ CI/CD service account created"
fi

# Create Artifact Registry repository
echo ""
echo "Creating Artifact Registry repository..."
if gcloud artifacts repositories describe vividly \
    --location="$REGION" \
    --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "✓ Artifact Registry repository exists"
else
    gcloud artifacts repositories create vividly \
        --repository-format=docker \
        --location="$REGION" \
        --description="Vividly Docker images" \
        --project="$PROJECT_ID"
    echo "✓ Artifact Registry repository created"
fi

# Create storage buckets
echo ""
echo "Creating Cloud Storage buckets..."

BUCKET_GENERATED_CONTENT="${PROJECT_ID}-generated-content"
if gcloud storage buckets describe "gs://${BUCKET_GENERATED_CONTENT}" &> /dev/null; then
    echo "✓ Generated content bucket exists"
else
    gcloud storage buckets create "gs://${BUCKET_GENERATED_CONTENT}" \
        --location="$REGION" \
        --uniform-bucket-level-access \
        --project="$PROJECT_ID"
    echo "✓ Generated content bucket created"
fi

BUCKET_OER="${PROJECT_ID}-oer-content"
if gcloud storage buckets describe "gs://${BUCKET_OER}" &> /dev/null; then
    echo "✓ OER content bucket exists"
else
    gcloud storage buckets create "gs://${BUCKET_OER}" \
        --location="$REGION" \
        --uniform-bucket-level-access \
        --project="$PROJECT_ID"
    echo "✓ OER content bucket created"
fi

BUCKET_TEMP="${PROJECT_ID}-temp-files"
if gcloud storage buckets describe "gs://${BUCKET_TEMP}" &> /dev/null; then
    echo "✓ Temp files bucket exists"
else
    gcloud storage buckets create "gs://${BUCKET_TEMP}" \
        --location="$REGION" \
        --uniform-bucket-level-access \
        --project="$PROJECT_ID"
    echo "✓ Temp files bucket created"
fi

# Create Pub/Sub topics
echo ""
echo "Creating Pub/Sub topics..."

TOPIC_CONTENT_REQUESTS="content-requests-${ENV}"
if gcloud pubsub topics describe "$TOPIC_CONTENT_REQUESTS" &> /dev/null 2>&1; then
    echo "✓ Content requests topic exists"
else
    gcloud pubsub topics create "$TOPIC_CONTENT_REQUESTS" \
        --project="$PROJECT_ID"
    echo "✓ Content requests topic created"
fi

TOPIC_CONTENT_REQUESTS_DLQ="content-requests-${ENV}-dlq"
if gcloud pubsub topics describe "$TOPIC_CONTENT_REQUESTS_DLQ" &> /dev/null 2>&1; then
    echo "✓ Content requests DLQ topic exists"
else
    gcloud pubsub topics create "$TOPIC_CONTENT_REQUESTS_DLQ" \
        --project="$PROJECT_ID"
    echo "✓ Content requests DLQ topic created"
fi

echo ""
echo "========================================="
echo "✓ GCP Project Setup Complete!"
echo "========================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "Service Accounts:"
echo "  - API Gateway: $SA_API_GATEWAY"
echo "  - Admin: $SA_ADMIN"
echo "  - Content Worker: $SA_WORKER"
echo "  - CI/CD: $SA_CICD"
echo ""
echo "Next Steps:"
echo "1. Set up Workload Identity Federation (run setup-workload-identity.sh)"
echo "2. Create secrets in Secret Manager (JWT secret, Nano Banana API key)"
echo "3. Deploy infrastructure with Terraform"
echo "4. Configure GitHub Actions secrets"
echo ""
echo "See DEPLOYMENT.md for detailed instructions."
