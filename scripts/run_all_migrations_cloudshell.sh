#!/bin/bash
#
# Run All Database Migrations via Cloud Shell
#
# This script runs all three migrations:
# 1. Feature Flags (add_feature_flags.sql)
# 2. Request Tracking (add_request_tracking.sql)
# 3. Phase 2 Indexes (add_phase2_indexes.sql)
#
# IMPORTANT: Run this in Google Cloud Shell, not locally
# The database has a private IP and requires VPC access
#
# Usage:
#   1. Open Google Cloud Shell: https://console.cloud.google.com/?cloudshell=true
#   2. Upload this script and the migration files
#   3. Run: bash run_all_migrations_cloudshell.sh
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Vividly Database Migrations${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Configuration
PROJECT_ID="vividly-dev-rich"
DB_INSTANCE="dev-vividly-db"
DB_USER="vividly"
DB_NAME="vividly"

# Set project
echo -e "${YELLOW}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project "${PROJECT_ID}"

# Get database IP
echo -e "${YELLOW}Getting database IP address...${NC}"
DB_IP=$(gcloud sql instances describe "${DB_INSTANCE}" \
    --format="value(ipAddresses[0].ipAddress)")

if [ -z "$DB_IP" ]; then
    echo -e "${RED}✗ Failed to get database IP${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database IP: ${DB_IP}${NC}"

# Get database password from Secret Manager
echo -e "${YELLOW}Retrieving database password from Secret Manager...${NC}"
DB_URL=$(gcloud secrets versions access latest --secret="database-url-dev" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to retrieve database password${NC}"
    exit 1
fi

DB_PASSWORD=$(echo "$DB_URL" | sed -n 's#.*://[^:]*:\([^@]*\)@.*#\1#p')

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}✗ Failed to parse database password${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database password retrieved${NC}"

# Set password environment variable
export PGPASSWORD="$DB_PASSWORD"

# Install postgresql-client if not present
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Installing postgresql-client...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y postgresql-client
    echo -e "${GREEN}✓ postgresql-client installed${NC}"
fi

# Test connection
echo ""
echo -e "${YELLOW}Testing database connection...${NC}"
psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" -t || {
    echo -e "${RED}✗ Connection test failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Connection successful${NC}"

# Function to run a migration
run_migration() {
    local migration_file=$1
    local migration_name=$2

    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Migration: ${migration_name}${NC}"
    echo -e "${BLUE}================================================${NC}"

    if [ ! -f "$migration_file" ]; then
        echo -e "${RED}✗ Migration file not found: ${migration_file}${NC}"
        echo -e "${YELLOW}  Please upload this file to Cloud Shell${NC}"
        return 1
    fi

    echo -e "${YELLOW}Running migration...${NC}"
    psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${migration_name} completed successfully${NC}"
        return 0
    else
        echo -e "${RED}✗ ${migration_name} failed${NC}"
        return 1
    fi
}

# Run migrations in order
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Starting Migrations${NC}"
echo -e "${BLUE}================================================${NC}"

# Migration 1: Feature Flags
run_migration "add_feature_flags.sql" "Feature Flags"
MIGRATION1_STATUS=$?

# Migration 2: Request Tracking
run_migration "add_request_tracking.sql" "Request Tracking"
MIGRATION2_STATUS=$?

# Migration 3: Phase 2 Indexes
run_migration "add_phase2_indexes.sql" "Phase 2 Indexes"
MIGRATION3_STATUS=$?

# Verify migrations
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Verification${NC}"
echo -e "${BLUE}================================================${NC}"

echo -e "${YELLOW}Checking migration results...${NC}"

# Check feature flags
FF_COUNT=$(psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM feature_flags;" 2>/dev/null | xargs)
echo -e "Feature Flags: ${GREEN}${FF_COUNT}${NC} records"

# Check pipeline stages
STAGE_COUNT=$(psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pipeline_stage_definitions;" 2>/dev/null | xargs)
echo -e "Pipeline Stages: ${GREEN}${STAGE_COUNT}${NC} records"

# Check indexes
INDEX_COUNT=$(psql -h "$DB_IP" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';" 2>/dev/null | xargs)
echo -e "Custom Indexes: ${GREEN}${INDEX_COUNT}${NC} indexes"

# Summary
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Migration Summary${NC}"
echo -e "${BLUE}================================================${NC}"

if [ $MIGRATION1_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Feature Flags Migration${NC}"
else
    echo -e "${RED}✗ Feature Flags Migration${NC}"
fi

if [ $MIGRATION2_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Request Tracking Migration${NC}"
else
    echo -e "${RED}✗ Request Tracking Migration${NC}"
fi

if [ $MIGRATION3_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 2 Indexes Migration${NC}"
else
    echo -e "${RED}✗ Phase 2 Indexes Migration${NC}"
fi

echo ""

if [ $MIGRATION1_STATUS -eq 0 ] && [ $MIGRATION2_STATUS -eq 0 ] && [ $MIGRATION3_STATUS -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  All migrations completed successfully! 🎉${NC}"
    echo -e "${GREEN}================================================${NC}"
    exit 0
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}  Some migrations failed${NC}"
    echo -e "${RED}================================================${NC}"
    exit 1
fi
