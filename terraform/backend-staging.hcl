# Backend configuration for Staging environment
# Usage: terraform init -backend-config=backend-staging.hcl

bucket = "vividly-staging-terraform-state"  # TODO: Create this bucket manually before running terraform
prefix = "terraform/state"
