#!/bin/bash
# Set up GitHub repository with branch protection and settings

set -e  # Exit on error

echo "========================================="
echo "GitHub Repository Setup"
echo "========================================="

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Not authenticated with GitHub. Running authentication..."
    gh auth login
fi

# Get repository information
echo ""
read -p "Enter GitHub organization/username: " GITHUB_ORG
read -p "Enter repository name (e.g., vividly-mvp): " REPO_NAME

REPO_FULL_NAME="${GITHUB_ORG}/${REPO_NAME}"

# Check if repository exists
if gh repo view "$REPO_FULL_NAME" &> /dev/null; then
    echo "✓ Repository $REPO_FULL_NAME exists"
else
    echo "Repository $REPO_FULL_NAME does not exist."
    read -p "Do you want to create it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter repository description: " REPO_DESC
        read -p "Make repository private? (y/n): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gh repo create "$REPO_FULL_NAME" --description "$REPO_DESC" --private
        else
            gh repo create "$REPO_FULL_NAME" --description "$REPO_DESC" --public
        fi

        echo "✓ Repository created"
    else
        echo "Aborted."
        exit 1
    fi
fi

# Add remote if not exists
if ! git remote get-url origin &> /dev/null; then
    echo "Adding remote origin..."
    git remote add origin "git@github.com:${REPO_FULL_NAME}.git"
    echo "✓ Remote origin added"
else
    echo "✓ Remote origin already exists"
fi

# Push branches
echo ""
echo "Pushing branches to GitHub..."
read -p "Push main and develop branches? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push -u origin main
    git push -u origin develop
    echo "✓ Branches pushed"
fi

# Set up branch protection for main
echo ""
echo "Setting up branch protection for 'main'..."
gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/${REPO_FULL_NAME}/branches/main/protection" \
    -f required_status_checks='{"strict":true,"contexts":[]}' \
    -f enforce_admins=false \
    -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
    -f restrictions=null \
    -f allow_force_pushes=false \
    -f allow_deletions=false \
    -f block_creations=false \
    -f required_conversation_resolution=true \
    -f required_linear_history=false \
    2>/dev/null && echo "✓ Branch protection set for 'main'" || echo "⚠ Could not set branch protection (may require admin access)"

# Set up branch protection for develop
echo "Setting up branch protection for 'develop'..."
gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/${REPO_FULL_NAME}/branches/develop/protection" \
    -f required_status_checks='{"strict":true,"contexts":[]}' \
    -f enforce_admins=false \
    -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
    -f restrictions=null \
    -f allow_force_pushes=false \
    -f allow_deletions=false \
    -f block_creations=false \
    -f required_conversation_resolution=true \
    -f required_linear_history=false \
    2>/dev/null && echo "✓ Branch protection set for 'develop'" || echo "⚠ Could not set branch protection (may require admin access)"

# Create production environment (for manual approval)
echo ""
echo "Setting up GitHub Environments..."
gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "/repos/${REPO_FULL_NAME}/environments/production" \
    -f wait_timer=0 \
    -f reviewers='[]' \
    2>/dev/null && echo "✓ Production environment created" || echo "⚠ Could not create environment (may require admin access)"

# Add labels for issues/PRs
echo ""
echo "Creating labels..."
gh label create "bug" --description "Something isn't working" --color "d73a4a" --force 2>/dev/null
gh label create "enhancement" --description "New feature or request" --color "a2eeef" --force 2>/dev/null
gh label create "documentation" --description "Improvements or additions to documentation" --color "0075ca" --force 2>/dev/null
gh label create "infrastructure" --description "Infrastructure and deployment changes" --color "fbca04" --force 2>/dev/null
gh label create "security" --description "Security-related changes" --color "d93f0b" --force 2>/dev/null
gh label create "ai-safety" --description "AI safety and content moderation" --color "c5def5" --force 2>/dev/null
echo "✓ Labels created"

echo ""
echo "========================================="
echo "✓ GitHub Repository Setup Complete!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Configure GitHub Actions secrets:"
echo "   gh secret set GCP_DEV_PROJECT_ID"
echo "   gh secret set GCP_STAGING_PROJECT_ID"
echo "   gh secret set GCP_PROD_PROJECT_ID"
echo "   gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER"
echo "   gh secret set GCP_SERVICE_ACCOUNT"
echo ""
echo "2. See DEPLOYMENT.md for complete CI/CD setup"
echo ""
echo "Repository URL: https://github.com/${REPO_FULL_NAME}"
