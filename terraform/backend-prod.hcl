# Backend configuration for Production environment
# Usage: terraform init -backend-config=backend-prod.hcl

bucket = "vividly-prod-terraform-state"  # TODO: Create this bucket manually before running terraform
prefix = "terraform/state"
