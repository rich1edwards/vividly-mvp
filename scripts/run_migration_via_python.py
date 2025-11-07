#!/usr/bin/env python3
"""
Execute prompt system migration via Python and Cloud SQL Connector.

This script uses the Cloud SQL Python Connector to connect directly
to the database and execute the migration SQL file.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from google.cloud.sql.connector import Connector
import psycopg2

# Configuration
PROJECT_ID = "vividly-dev-rich"
REGION = "us-central1"
INSTANCE_NAME = "dev-vividly-db"
DATABASE_NAME = "vividly"
CONNECTION_NAME = f"{PROJECT_ID}:{REGION}:{INSTANCE_NAME}"

# Migration file
MIGRATION_FILE = backend_dir / "migrations" / "enterprise_prompt_system_phase1.sql"

print("=" * 80)
print("Enterprise Prompt System Migration (Python)")
print("=" * 80)
print(f"Connection: {CONNECTION_NAME}")
print(f"Database: {DATABASE_NAME}")
print(f"Migration: {MIGRATION_FILE}")
print()

# Step 1: Verify migration file exists
print("[1/4] Verifying migration file...")
if not MIGRATION_FILE.exists():
    print(f"ERROR: Migration file not found: {MIGRATION_FILE}")
    sys.exit(1)

with open(MIGRATION_FILE, 'r') as f:
    migration_sql = f.read()

print(f"✓ Migration file loaded ({len(migration_sql)} characters)")
print()

# Step 2: Check if tables already exist
print("[2/4] Checking existing tables...")

def get_connection():
    """Create database connection using Cloud SQL Connector."""
    connector = Connector()

    def getconn():
        conn = connector.connect(
            CONNECTION_NAME,
            "pg8000",
            user="postgres",
            db=DATABASE_NAME,
            enable_iam_auth=False,
        )
        return conn

    return getconn()

try:
    conn = get_connection()
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('prompt_templates', 'prompt_executions', 'prompt_guardrails', 'ab_test_experiments')
    """)

    existing_tables = cursor.fetchone()[0]

    if existing_tables == 4:
        print("✓ All 4 tables already exist - migration already completed")
        print()
        print("Tables: prompt_templates, prompt_executions, prompt_guardrails, ab_test_experiments")
        cursor.close()
        conn.close()
        sys.exit(0)
    elif existing_tables > 0:
        print(f"WARNING: Found {existing_tables}/4 tables (partial migration)")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled")
            cursor.close()
            conn.close()
            sys.exit(1)

    print(f"✓ Migration needed ({existing_tables}/4 tables exist)")
    print()

    # Step 3: Execute migration
    print("[3/4] Executing migration...")
    print("Creating 4 tables with seed data...")
    print()

    # Execute the migration SQL
    cursor.execute(migration_sql)
    conn.commit()

    print("✓ Migration executed successfully")
    print()

    # Step 4: Verify migration
    print("[4/4] Verifying migration...")

    # Check tables created
    cursor.execute("""
        SELECT
            table_name,
            (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public'
        AND table_name IN ('prompt_templates', 'prompt_executions', 'prompt_guardrails', 'ab_test_experiments')
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print("Tables created:")
    for table_name, column_count in tables:
        print(f"  - {table_name} ({column_count} columns)")

    print()

    # Check seed data
    cursor.execute("SELECT COUNT(*) FROM prompt_templates")
    template_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prompt_guardrails")
    guardrail_count = cursor.fetchone()[0]

    print("Seed data inserted:")
    print(f"  - Prompt Templates: {template_count}")
    print(f"  - Guardrails: {guardrail_count}")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✓ MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Test integration: python backend/test_prompt_templates_integration.py")
    print("2. Deploy updated code with database integration")
    print()

except Exception as e:
    print(f"ERROR: Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
