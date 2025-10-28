# Vividly Setup Scripts

This directory contains automation scripts for setting up Vividly's development infrastructure.

## Prerequisites

Before running these scripts, ensure you have:

1. **Git** - `git --version`
2. **GitHub CLI** - `gh --version` (install: `brew install gh`)
3. **Google Cloud SDK** - `gcloud --version` (install: https://cloud.google.com/sdk/docs/install)
4. **Terraform** - `terraform --version` (install: `brew install terraform`)

## Quick Start (Full Setup)

For a complete setup from scratch:

```bash
# 1. Initialize Git repository
./scripts/init-git-repo.sh

# 2. Set up GitHub repository (requires GitHub CLI)
./scripts/setup-github.sh

# 3. Set up GCP project for each environment
./scripts/setup-gcp-project.sh  # Run once for dev, staging, prod

# 4. Set up Workload Identity Federation
./scripts/setup-workload-identity.sh  # Run for each environment

# 5. Create secrets in Secret Manager
./scripts/create-gcp-secrets.sh  # Run for each environment

# 6. Configure GitHub Actions secrets
./scripts/setup-github-secrets.sh

# 7. Deploy infrastructure with Terraform (see terraform/README.md)
cd terraform
terraform init -backend-config=backend-dev.hcl
terraform apply -var-file=environments/dev.tfvars
```

## Script Reference

### Git & GitHub Scripts

#### `init-git-repo.sh`
**Purpose**: Initialize Git repository with proper branch structure

**What it does**:
- Initializes git repository
- Creates `main` and `develop` branches
- Creates initial commit
- Provides instructions for connecting to GitHub

**Usage**:
```bash
./scripts/init-git-repo.sh
```

**When to use**: First time setting up the repository, before pushing to GitHub.

---

#### `setup-github.sh`
**Purpose**: Create and configure GitHub repository

**What it does**:
- Creates GitHub repository (if it doesn't exist)
- Sets up branch protection rules for `main` and `develop`
- Creates production environment (for manual approval)
- Creates labels for issues/PRs
- Pushes initial code to GitHub

**Usage**:
```bash
./scripts/setup-github.sh
```

**Requirements**:
- GitHub CLI installed and authenticated (`gh auth login`)
- Git repository initialized locally

**When to use**: After initializing local git repo, before setting up CI/CD.

---

#### `setup-github-secrets.sh`
**Purpose**: Configure GitHub Actions secrets for CI/CD

**What it does**:
- Prompts for GCP project IDs and service account emails
- Sets all required secrets for dev/staging/prod environments
- Configures Workload Identity Provider
- Lists all configured secrets

**Usage**:
```bash
./scripts/setup-github-secrets.sh
```

**Required secrets**:
- `GCP_DEV_PROJECT_ID`
- `GCP_STAGING_PROJECT_ID`
- `GCP_PROD_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT` (dev)
- `GCP_STAGING_SERVICE_ACCOUNT`
- `GCP_PROD_SERVICE_ACCOUNT`
- `DEV_API_URL` (after first deployment)
- `STAGING_API_URL` (after first deployment)
- `PROD_API_URL` (after first deployment)

**When to use**: After setting up GCP projects and Workload Identity Federation.

---

### GCP Scripts

#### `setup-gcp-project.sh`
**Purpose**: Create and configure a GCP project for Vividly

**What it does**:
- Creates GCP project
- Links billing account
- Enables all required APIs (35+ services)
- Creates Terraform state bucket
- Creates service accounts (api-gateway, admin-service, content-worker, cicd)
- Creates Artifact Registry repository
- Creates Cloud Storage buckets (generated-content, oer-content, temp-files)
- Creates Pub/Sub topics (content-requests, DLQ)

**Usage**:
```bash
./scripts/setup-gcp-project.sh
```

**Prompts for**:
- Environment (dev/staging/prod)
- GCP Project ID
- Billing account ID
- Region (default: us-central1)

**When to use**: Once for each environment (dev, staging, prod).

**Estimated time**: 5-10 minutes

---

#### `setup-workload-identity.sh`
**Purpose**: Configure Workload Identity Federation for GitHub Actions

**What it does**:
- Creates Workload Identity Pool
- Creates Workload Identity Provider (OIDC with GitHub)
- Binds service account to workload identity
- Grants necessary permissions to CI/CD service account
- Outputs provider resource name for GitHub secrets

**Usage**:
```bash
./scripts/setup-workload-identity.sh
```

**Prompts for**:
- GCP Project ID
- GitHub repository (owner/repo)
- Environment (dev/staging/prod)

**When to use**: After creating GCP project, before setting up GitHub secrets.

**Security Note**: This eliminates the need for service account keys, improving security.

---

#### `create-gcp-secrets.sh`
**Purpose**: Create secrets in Google Secret Manager

**What it does**:
- Generates or accepts JWT secret
- Stores Nano Banana API key
- Grants service accounts access to secrets
- Lists all created secrets

**Secrets created**:
- `jwt-secret`: For JWT token signing
- `nano-banana-key`: Nano Banana API key
- (Note: `database-url-{env}` is created by Terraform)

**Usage**:
```bash
./scripts/create-gcp-secrets.sh
```

**Prompts for**:
- GCP Project ID
- Environment (dev/staging/prod)
- JWT secret (or generate random)
- Nano Banana API key

**When to use**: After GCP project setup, before deploying infrastructure.

**Security Warning**: Secrets are stored securely in Secret Manager. Never commit secrets to git!

---

## Typical Workflow

### Setting Up a New Environment

Here's the typical order for setting up a new environment (e.g., development):

1. **Initialize Git** (once)
   ```bash
   ./scripts/init-git-repo.sh
   ```

2. **Set up GitHub** (once)
   ```bash
   ./scripts/setup-github.sh
   ```

3. **Set up GCP project**
   ```bash
   ./scripts/setup-gcp-project.sh
   # Select: 1) Development
   # Enter project ID: vividly-dev
   # Enter billing account: 01ABCD-123456-ABCDEF
   ```

4. **Set up Workload Identity**
   ```bash
   ./scripts/setup-workload-identity.sh
   # Enter project ID: vividly-dev
   # Enter repo: your-org/vividly-mvp
   # Enter environment: dev
   ```

5. **Create secrets**
   ```bash
   ./scripts/create-gcp-secrets.sh
   # Enter project ID: vividly-dev
   # Enter environment: dev
   # Generate JWT secret: y
   # Enter Nano Banana key: [your-key]
   ```

6. **Configure GitHub secrets**
   ```bash
   ./scripts/setup-github-secrets.sh
   # Enter repository: your-org/vividly-mvp
   # Follow prompts for all secrets
   ```

7. **Deploy infrastructure with Terraform**
   ```bash
   cd terraform
   terraform init -backend-config=backend-dev.hcl
   terraform plan -var-file=environments/dev.tfvars
   terraform apply -var-file=environments/dev.tfvars
   ```

8. **Deploy application via GitHub Actions**
   ```bash
   git checkout develop
   git push origin develop
   # This triggers automatic deployment to dev
   ```

### Setting Up Additional Environments

For staging and production, repeat steps 3-7 for each environment:

```bash
# Staging
./scripts/setup-gcp-project.sh  # Choose staging
./scripts/setup-workload-identity.sh  # environment: staging
./scripts/create-gcp-secrets.sh  # environment: staging

# Production
./scripts/setup-gcp-project.sh  # Choose production
./scripts/setup-workload-identity.sh  # environment: prod
./scripts/create-gcp-secrets.sh  # environment: prod
```

Then update GitHub secrets to include staging and prod configurations.

## Troubleshooting

### "Command not found: gh"
Install GitHub CLI:
```bash
brew install gh
# or visit https://cli.github.com/
```

### "Command not found: gcloud"
Install Google Cloud SDK:
```bash
# macOS
brew install google-cloud-sdk

# Or download from:
# https://cloud.google.com/sdk/docs/install
```

### "Permission denied" when running scripts
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### "API not enabled"
The setup script should enable all required APIs, but if you encounter this error:
```bash
gcloud services enable [API_NAME] --project=[PROJECT_ID]
```

### "Insufficient permissions"
Ensure your Google Cloud user has the following roles:
- Project Creator (to create projects)
- Project IAM Admin (to grant permissions)
- Service Account Admin (to create service accounts)

Add permissions:
```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="user:your-email@example.com" \
  --role="roles/owner"
```

### "Billing account not found"
List billing accounts:
```bash
gcloud billing accounts list
```

### Workload Identity setup fails
Ensure you have enabled the required APIs:
```bash
gcloud services enable iamcredentials.googleapis.com \
  --project=[PROJECT_ID]
```

## Security Best Practices

1. **Never commit secrets**: The scripts store secrets in Secret Manager, not in code
2. **Use Workload Identity**: Avoids service account keys
3. **Rotate secrets regularly**: Update JWT secret every 90 days
4. **Limit permissions**: Use least-privilege access for service accounts
5. **Enable audit logs**: Monitor access to secrets in Cloud Audit Logs

## Script Dependencies

```
init-git-repo.sh
    ↓
setup-github.sh
    ↓
setup-gcp-project.sh → setup-workload-identity.sh → create-gcp-secrets.sh
                            ↓
                    setup-github-secrets.sh
                            ↓
                    Terraform deployment
```

## Cost Implications

Running these setup scripts creates resources that may incur costs:

- **Free**: Git, GitHub, service accounts, Pub/Sub topics (low volume)
- **Minimal cost**: Cloud Storage buckets (storage only), Artifact Registry
- **Actual costs**: Occur when you deploy infrastructure with Terraform

See `terraform/README.md` for cost estimates per environment.

## Additional Resources

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete deployment guide
- [terraform/README.md](../terraform/README.md) - Terraform infrastructure guide
- [DEVELOPMENT_SETUP.md](../DEVELOPMENT_SETUP.md) - Local development setup
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Google Cloud SDK Documentation](https://cloud.google.com/sdk/docs)

## Support

For issues with these scripts:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Ensure all prerequisites are installed
4. Check that you have necessary permissions in GCP and GitHub
