#!/bin/bash
# Create secrets in Google Secret Manager

set -e  # Exit on error

echo "========================================="
echo "Google Secret Manager Setup"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    exit 1
fi

# Get project details
read -p "Enter GCP Project ID: " PROJECT_ID
read -p "Enter environment (dev/staging/prod): " ENV

# Set project
gcloud config set project "$PROJECT_ID"

echo ""
echo "This script will create the following secrets:"
echo "  - jwt-secret: Secret key for JWT token signing"
echo "  - nano-banana-key: API key for Nano Banana video service"
echo "  - database-url-${ENV}: Database connection string (created by Terraform)"
echo ""
echo "Note: database-url-${ENV} is created by Terraform during infrastructure deployment"
echo ""

# Generate JWT secret
echo ""
echo "========================================="
echo "JWT Secret"
echo "========================================="
echo ""
echo "A JWT secret is used to sign authentication tokens."
echo ""
read -p "Do you want to generate a random JWT secret? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    JWT_SECRET=$(openssl rand -base64 32)
    echo "Generated JWT secret (save this securely):"
    echo "$JWT_SECRET"
else
    read -sp "Enter JWT secret (will not be displayed): " JWT_SECRET
    echo
fi

# Create JWT secret
echo "Creating jwt-secret in Secret Manager..."
if gcloud secrets describe jwt-secret --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "✓ jwt-secret already exists"
    read -p "Update the secret? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret \
            --data-file=- \
            --project="$PROJECT_ID"
        echo "✓ jwt-secret updated"
    fi
else
    echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
        --data-file=- \
        --replication-policy=automatic \
        --project="$PROJECT_ID"
    echo "✓ jwt-secret created"
fi

# Nano Banana API Key
echo ""
echo "========================================="
echo "Nano Banana API Key"
echo "========================================="
echo ""
echo "You need an API key from Nano Banana (https://nanobanana.ai)"
echo "Sign up and get your API key from the dashboard."
echo ""
read -p "Do you have a Nano Banana API key? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Enter Nano Banana API key: " NANO_BANANA_KEY
    echo

    # Create Nano Banana secret
    echo "Creating nano-banana-key in Secret Manager..."
    if gcloud secrets describe nano-banana-key --project="$PROJECT_ID" &> /dev/null 2>&1; then
        echo "✓ nano-banana-key already exists"
        read -p "Update the secret? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -n "$NANO_BANANA_KEY" | gcloud secrets versions add nano-banana-key \
                --data-file=- \
                --project="$PROJECT_ID"
            echo "✓ nano-banana-key updated"
        fi
    else
        echo -n "$NANO_BANANA_KEY" | gcloud secrets create nano-banana-key \
            --data-file=- \
            --replication-policy=automatic \
            --project="$PROJECT_ID"
        echo "✓ nano-banana-key created"
    fi
else
    echo "⚠ Skipping Nano Banana API key creation."
    echo "  You can create it later with:"
    echo "  echo -n 'YOUR_API_KEY' | gcloud secrets create nano-banana-key \\"
    echo "    --data-file=- --project=$PROJECT_ID"
fi

# Grant service accounts access to secrets
echo ""
echo "========================================="
echo "Granting Secret Access"
echo "========================================="

# Service accounts that need access
SA_API_GATEWAY="${ENV}-api-gateway@${PROJECT_ID}.iam.gserviceaccount.com"
SA_ADMIN="${ENV}-admin-service@${PROJECT_ID}.iam.gserviceaccount.com"
SA_WORKER="${ENV}-content-worker@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant jwt-secret access
echo "Granting access to jwt-secret..."
for SA in "$SA_API_GATEWAY" "$SA_ADMIN"; do
    gcloud secrets add-iam-policy-binding jwt-secret \
        --member="serviceAccount:${SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet &> /dev/null || true
done
echo "✓ jwt-secret access granted"

# Grant nano-banana-key access
if gcloud secrets describe nano-banana-key --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "Granting access to nano-banana-key..."
    gcloud secrets add-iam-policy-binding nano-banana-key \
        --member="serviceAccount:${SA_WORKER}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet &> /dev/null || true
    echo "✓ nano-banana-key access granted"
fi

# Grant database-url access (if it exists from Terraform)
if gcloud secrets describe "database-url-${ENV}" --project="$PROJECT_ID" &> /dev/null 2>&1; then
    echo "Granting access to database-url-${ENV}..."
    for SA in "$SA_API_GATEWAY" "$SA_ADMIN" "$SA_WORKER"; do
        gcloud secrets add-iam-policy-binding "database-url-${ENV}" \
            --member="serviceAccount:${SA}" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID" \
            --quiet &> /dev/null || true
    done
    echo "✓ database-url-${ENV} access granted"
else
    echo "ℹ database-url-${ENV} doesn't exist yet (will be created by Terraform)"
fi

# List all secrets
echo ""
echo "========================================="
echo "Created Secrets"
echo "========================================="
gcloud secrets list --project="$PROJECT_ID"

echo ""
echo "✓ Secret Manager setup complete!"
echo ""
echo "Important Security Notes:"
echo "  - JWT secret has been created and stored in Secret Manager"
echo "  - NEVER commit secrets to git or expose them in logs"
echo "  - Service accounts have been granted access to secrets"
echo "  - Rotate secrets regularly (at least every 90 days)"
echo ""
echo "To view a secret value:"
echo "  gcloud secrets versions access latest --secret=jwt-secret --project=$PROJECT_ID"
