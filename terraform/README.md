# Vividly Terraform Infrastructure

This directory contains Terraform configurations for deploying Vividly infrastructure to Google Cloud Platform (GCP).

## Prerequisites

1. **Install Terraform** (>= 1.6.0)
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```

2. **Install Google Cloud SDK**
   ```bash
   brew install google-cloud-sdk  # macOS
   # or download from https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate with GCP**
   ```bash
   gcloud auth application-default login
   ```

## Initial Setup

### 1. Create GCP Projects

Create separate GCP projects for each environment:

```bash
# Development
gcloud projects create vividly-dev --name="Vividly Development"

# Staging
gcloud projects create vividly-staging --name="Vividly Staging"

# Production
gcloud projects create vividly-prod --name="Vividly Production"
```

### 2. Enable Billing

Link each project to a billing account via the GCP Console:
https://console.cloud.google.com/billing/

### 3. Create Terraform State Buckets

Create GCS buckets to store Terraform state (do this manually for each environment):

```bash
# Development
gcloud storage buckets create gs://vividly-dev-terraform-state \
  --project=vividly-dev \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://vividly-dev-terraform-state \
  --versioning

# Staging
gcloud storage buckets create gs://vividly-staging-terraform-state \
  --project=vividly-staging \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://vividly-staging-terraform-state \
  --versioning

# Production
gcloud storage buckets create gs://vividly-prod-terraform-state \
  --project=vividly-prod \
  --location=us-central1 \
  --uniform-bucket-level-access

gcloud storage buckets update gs://vividly-prod-terraform-state \
  --versioning
```

### 4. Update Environment Configuration

Edit the `.tfvars` files in `environments/` to match your actual GCP project IDs and settings:

- `environments/dev.tfvars`
- `environments/staging.tfvars`
- `environments/prod.tfvars`

## Deploying Infrastructure

### Development Environment

```bash
# Initialize Terraform with dev backend
terraform init -backend-config=backend-dev.hcl

# Review the plan
terraform plan -var-file=environments/dev.tfvars

# Apply the configuration
terraform apply -var-file=environments/dev.tfvars
```

### Staging Environment

```bash
# Re-initialize for staging backend
terraform init -reconfigure -backend-config=backend-staging.hcl

# Review the plan
terraform plan -var-file=environments/staging.tfvars

# Apply the configuration
terraform apply -var-file=environments/staging.tfvars
```

### Production Environment

```bash
# Re-initialize for production backend
terraform init -reconfigure -backend-config=backend-prod.hcl

# Review the plan
terraform plan -var-file=environments/prod.tfvars

# Apply the configuration (requires approval)
terraform apply -var-file=environments/prod.tfvars
```

## What Gets Created

The Terraform configuration creates:

### Networking
- VPC Network
- Private subnet with IP range
- VPC Peering for Cloud SQL private connectivity

### Database
- Cloud SQL PostgreSQL 15 instance
  - Development: 1 vCPU, 3.75 GB RAM
  - Staging: 2 vCPU, 7.5 GB RAM
  - Production: 4 vCPU, 15 GB RAM (REGIONAL for HA)
- Database `vividly` with user
- Automated backups (7-30 days retention)
- Point-in-time recovery (production only)

### Storage
- **Generated Content Bucket**: Stores AI-generated videos and scripts
- **OER Content Bucket**: Stores OpenStax educational resources
- **Temp Files Bucket**: Temporary storage with 7-day auto-deletion

### Pub/Sub
- Content request topic
- Dead letter queue for failed messages

### Artifact Registry
- Docker image repository for all services

### Service Accounts
- `api-gateway`: API Gateway service
- `admin-service`: Admin dashboard service
- `content-worker`: AI content generation worker
- `cicd`: GitHub Actions deployment

### IAM Permissions
- Least-privilege access for each service account
- Cloud SQL, Storage, Pub/Sub, Vertex AI, Secret Manager access

### Monitoring
- Alert policies for:
  - High error rate (>5%)
  - High latency (P95 > 2s)
  - Database CPU (>80%)

### Secrets
- Database connection URL stored in Secret Manager

## Post-Deployment Steps

After Terraform completes, you need to manually:

### 1. Create Additional Secrets

```bash
# Set your environment
export ENV=dev  # or staging, prod
export PROJECT_ID=vividly-${ENV}

# JWT Secret
echo -n "your-random-jwt-secret-here" | gcloud secrets create jwt-secret \
  --project=$PROJECT_ID \
  --data-file=-

# Nano Banana API Key
echo -n "your-nano-banana-api-key" | gcloud secrets create nano-banana-key \
  --project=$PROJECT_ID \
  --data-file=-
```

### 2. Create Vertex AI Vector Search Index

The Vector Search index must be created separately (not supported by Terraform):

```bash
# See VECTOR_DB_SCHEMA.md for detailed instructions
gcloud ai indexes create \
  --display-name=oer-content-index-${ENV} \
  --metadata-file=index-config.json \
  --project=$PROJECT_ID \
  --region=us-central1
```

### 3. Set Up Monitoring Notification Channels

Create notification channels in Cloud Monitoring:

```bash
# Email notifications
gcloud alpha monitoring channels create \
  --display-name="Engineering Team" \
  --type=email \
  --channel-labels=email_address=engineering@example.com \
  --project=$PROJECT_ID

# Note the channel ID and add to environments/*.tfvars
# Then re-run terraform apply
```

### 4. Configure GitHub Actions Secrets

In your GitHub repository settings, add these secrets:

**For Development:**
- `GCP_DEV_PROJECT_ID`: Your dev project ID
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: Workload Identity provider
- `GCP_SERVICE_ACCOUNT`: CI/CD service account email
- `DEV_API_URL`: Will be set after first deployment

**For Staging:**
- `GCP_STAGING_PROJECT_ID`
- `GCP_STAGING_SERVICE_ACCOUNT`
- `STAGING_API_URL`
- `STAGING_FRONTEND_URL`

**For Production:**
- `GCP_PROD_PROJECT_ID`
- `GCP_PROD_SERVICE_ACCOUNT`
- `PROD_API_URL`

### 5. Set Up Workload Identity Federation

Configure GitHub Actions to authenticate to GCP without service account keys:

```bash
# See: https://github.com/google-github-actions/auth#setup

gcloud iam workload-identity-pools create github \
  --project=$PROJECT_ID \
  --location=global \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github \
  --project=$PROJECT_ID \
  --location=global \
  --workload-identity-pool=github \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Bind service account
gcloud iam service-accounts add-iam-policy-binding \
  ${ENV}-cicd@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=$PROJECT_ID \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/YOUR_ORG/YOUR_REPO"
```

## Terraform Outputs

After applying, Terraform outputs important values:

```bash
# View all outputs
terraform output

# Get specific values
terraform output database_connection_name
terraform output artifact_registry_url
terraform output cicd_service_account
```

## Destroying Infrastructure

**⚠️ WARNING: This will delete all resources including databases!**

```bash
# Development
terraform destroy -var-file=environments/dev.tfvars

# Staging
terraform destroy -var-file=environments/staging.tfvars

# Production (has deletion protection - disable first in main.tf)
terraform destroy -var-file=environments/prod.tfvars
```

## Common Commands

```bash
# Format Terraform files
terraform fmt -recursive

# Validate configuration
terraform validate

# Show current state
terraform show

# List all resources
terraform state list

# Import existing resource
terraform import google_storage_bucket.example gs://bucket-name

# Refresh state to match real infrastructure
terraform refresh -var-file=environments/dev.tfvars
```

## Troubleshooting

### "Error 403: Forbidden"
Ensure your user account has the necessary permissions:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/owner"
```

### "API not enabled"
Enable required APIs manually:
```bash
gcloud services enable compute.googleapis.com \
  --project=$PROJECT_ID
```

### State Lock Issues
If Terraform state is locked:
```bash
terraform force-unlock LOCK_ID
```

### Backend Configuration Changes
When switching environments:
```bash
terraform init -reconfigure -backend-config=backend-<env>.hcl
```

## Security Best Practices

1. **Never commit `.tfvars` files with sensitive data** - Use environment variables or Secret Manager
2. **Enable state file encryption** - GCS buckets have encryption by default
3. **Use workload identity** instead of service account keys
4. **Review plans before applying** - Always run `terraform plan` first
5. **Limit access to production** - Use separate GCP organizations/folders

## Directory Structure

```
terraform/
├── main.tf                    # Main infrastructure definition
├── variables.tf               # Variable declarations
├── outputs.tf                 # Output definitions
├── backend-dev.hcl           # Dev backend config
├── backend-staging.hcl       # Staging backend config
├── backend-prod.hcl          # Prod backend config
├── README.md                 # This file
└── environments/
    ├── dev.tfvars            # Dev environment values
    ├── staging.tfvars        # Staging environment values
    └── prod.tfvars           # Prod environment values
```

## Cost Estimates

**Development:** ~$150/month
- Cloud SQL: $50
- Cloud Run: $20
- Storage: $10
- Pub/Sub: $5
- Other: $65

**Staging:** ~$300/month
- Cloud SQL: $120
- Cloud Run: $50
- Storage: $20
- Pub/Sub: $10
- Other: $100

**Production:** ~$800/month (without heavy usage)
- Cloud SQL: $400 (HA configuration)
- Cloud Run: $150
- Storage: $50
- Pub/Sub: $20
- Vertex AI: $100 (usage-based)
- Other: $80

*Actual costs will vary based on usage, especially Vertex AI and Nano Banana API calls.*

## Additional Resources

- [Terraform GCP Provider Documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
