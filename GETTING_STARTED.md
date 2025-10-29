# Getting Started with Vividly Development Environment

This guide will walk you through setting up everything you need to deploy the Vividly development environment to Google Cloud Platform.

## Git Repository Setup ✅

Your Git repository has been initialized with:
- Initial commit with all documentation and infrastructure code
- `main` branch (default)
- `develop` branch for development work

## Next Steps: Google Cloud Platform Setup

### Step 1: Create a Google Cloud Account

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Sign up** with your email address
   - You can use any Google account (personal or business)
   - New users get **$300 in free credits** valid for 90 days
   - This is more than enough to run the dev environment for several months

3. **Set up billing**:
   - After signing up, you'll be prompted to set up a billing account
   - You'll need to provide a credit card, but you won't be charged during the free trial
   - After the trial, you'll only pay for what you use

### Step 2: Install Required Tools

**GitHub CLI** (for GitHub repository setup):
```bash
brew install gh
```

**Google Cloud SDK** (for GCP management):
```bash
brew install google-cloud-sdk
```

**Terraform** (for infrastructure deployment):
```bash
brew install terraform
```

### Step 3: Create GitHub Repository

Once you have GitHub CLI installed:

```bash
# Authenticate with GitHub
gh auth login

# Create the repository (choose public or private)
gh repo create vividly-mvp --description "Vividly MVP - AI-powered personalized STEM learning platform" --public

# Add the remote
git remote add origin https://github.com/YOUR_USERNAME/vividly-mvp.git

# Push both branches
git push -u origin main
git push -u origin develop
```

**Alternative**: If you prefer to create the repo manually:
1. Go to https://github.com/new
2. Name: `vividly-mvp`
3. Don't initialize with README, .gitignore, or license (we already have these)
4. Click "Create repository"
5. Follow the instructions to add remote and push

### Step 4: Get Your GCP Project Information

I'll need the following information from you:

#### Required Information:

1. **GCP Billing Account ID**
   - After setting up billing, go to: https://console.cloud.google.com/billing
   - You'll see your billing account listed
   - Copy the **Billing Account ID** (format: `01ABCD-123456-ABCDEF`)

2. **Preferred Project ID** (optional)
   - If you have a preference, suggest a project ID
   - Format: `vividly-dev-yourname` or just `vividly-dev`
   - Must be unique across all of Google Cloud
   - If you don't specify, I'll generate one

3. **GitHub Repository Information**
   - Your GitHub username
   - Repository name (e.g., `vividly-mvp`)
   - Format: `username/repo-name`

4. **Nano Banana API Key** (optional for now)
   - Only needed if you want to generate actual videos
   - Sign up at: https://nanobanana.ai
   - You can skip this for initial testing and add it later

#### Optional Information:

5. **Preferred GCP Region** (default: `us-central1`)
   - Recommended regions for US:
     - `us-central1` (Iowa) - Default, good balance
     - `us-east1` (South Carolina) - East coast
     - `us-west1` (Oregon) - West coast

## What I'll Do With This Information

Once you provide the above, I will:

1. **Create GCP Project** using your billing account
2. **Enable all required APIs** (~35 services including Vertex AI, Cloud Run, etc.)
3. **Set up infrastructure** with Terraform:
   - Cloud SQL PostgreSQL database (minimal tier: 1 vCPU, 3.75GB RAM)
   - Cloud Storage buckets for content
   - Pub/Sub topics for async processing
   - Service accounts with proper permissions
   - Networking (VPC, subnets)
   - Artifact Registry for Docker images

4. **Configure GitHub Actions** for automatic deployment
5. **Set up Workload Identity Federation** (secure authentication without keys)
6. **Create secrets** in Secret Manager (JWT secret, database credentials)
7. **Deploy the application** to Cloud Run

## Estimated Monthly Cost for Development Environment

Based on light usage (testing/development):

| Service | Monthly Cost |
|---------|--------------|
| Cloud SQL (db-custom-1-3840) | ~$40 |
| Cloud Run (minimal usage) | ~$5-10 |
| Cloud Storage | ~$5 |
| Vertex AI (usage-based) | ~$10-20 |
| Pub/Sub, Networking, Other | ~$5-10 |
| **Total** | **~$65-85/month** |

**With $300 free credit**, you can run this for 3-4+ months completely free.

**Ways to minimize costs during development**:
- Database auto-scales down when not in use
- Cloud Run scales to zero when idle (you only pay when it's running)
- You can stop the Cloud SQL instance when not actively developing

## What to Provide Me

Please reply with:

```
1. GCP Billing Account ID: [your-billing-account-id]
2. Preferred GCP Project ID: [your-preferred-id or "auto-generate"]
3. GitHub Repository: [username/repo-name]
4. GCP Region: [us-central1 or other]
5. Nano Banana API Key: [your-key or "skip for now"]
```

## Security Notes

- All secrets will be stored in Google Secret Manager (never in code or GitHub)
- We'll use Workload Identity Federation (no service account keys)
- Database has private IP only (not exposed to internet)
- All connections use TLS 1.3 encryption
- Service accounts follow least-privilege access

## Questions?

Common questions:

**Q: Do I need to create the GCP project manually?**
A: No, I'll create it for you using the billing account ID.

**Q: Will I be charged immediately?**
A: No, you have $300 in free credits. After that, you only pay for what you use.

**Q: Can I delete everything later?**
A: Yes, you can delete the entire GCP project, which removes all resources.

**Q: What if I don't have a Nano Banana API key?**
A: You can skip it for now. The system will work without it (videos just won't generate).

**Q: Can I use a different cloud provider?**
A: The infrastructure is designed for GCP (Vertex AI, Cloud Run). Adapting to AWS/Azure would require significant changes.

## Next Steps

1. Complete the Google Cloud signup and billing setup
2. Install the required tools (gh, gcloud, terraform)
3. Create your GitHub repository
4. Provide me with the information listed above
5. I'll handle the rest of the deployment automatically!

Let me know when you're ready with the information, and I'll get your development environment deployed.
