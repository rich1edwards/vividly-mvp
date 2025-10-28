# Backend configuration for Development environment
# Usage: terraform init -backend-config=backend-dev.hcl

bucket = "vividly-dev-terraform-state"  # TODO: Create this bucket manually before running terraform
prefix = "terraform/state"
