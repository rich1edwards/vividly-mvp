#!/bin/bash
# Initialize Git repository and set up branches for Vividly

set -e  # Exit on error

echo "========================================="
echo "Vividly Git Repository Initialization"
echo "========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

# Check if we're already in a git repository
if [ -d .git ]; then
    echo "Warning: This directory is already a git repository."
    read -p "Do you want to continue? This may reset some settings. (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
else
    # Initialize git repository
    echo "Initializing git repository..."
    git init
    echo "✓ Git repository initialized"
fi

# Set main as the default branch
echo "Setting up main branch..."
git branch -M main
echo "✓ Main branch configured"

# Create develop branch
echo "Creating develop branch..."
git checkout -b develop 2>/dev/null || git checkout develop
echo "✓ Develop branch created"

# Return to main
git checkout main

# Add all files (respecting .gitignore)
echo "Staging files..."
git add .
echo "✓ Files staged"

# Create initial commit
echo "Creating initial commit..."
if git diff-index --quiet --cached HEAD 2>/dev/null; then
    echo "No changes to commit (repository may already have commits)"
else
    git commit -m "Initial commit: Vividly MVP setup

- Complete architecture and infrastructure documentation
- GitHub Actions CI/CD pipelines for dev/staging/prod
- Terraform infrastructure as code for GCP deployment
- Dockerfiles for all services
- Development environment setup guides

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
    echo "✓ Initial commit created"
fi

# Display git status
echo ""
echo "========================================="
echo "Git Repository Status"
echo "========================================="
git status

echo ""
echo "========================================="
echo "Branch Structure"
echo "========================================="
git branch -a

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Create repository (e.g., 'vividly-mvp')"
echo "   - Do NOT initialize with README, .gitignore, or license"
echo ""
echo "2. Connect to GitHub:"
echo "   git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git"
echo ""
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo "   git push -u origin develop"
echo ""
echo "4. Set up branch protection rules:"
echo "   - Protect 'main' branch (require PR reviews)"
echo "   - Protect 'develop' branch"
echo ""
echo "5. Configure GitHub Actions secrets (see DEPLOYMENT.md)"
echo ""
echo "✓ Git repository initialized successfully!"
