#!/usr/bin/env python3
"""
Database Migration Runner for Cloud Build

This script runs SQL migrations in Cloud Build using the existing DATABASE_URL secret.
It uses psycopg2 to connect via Cloud SQL Unix socket (automatic in Cloud Build).

Usage:
    python run_migration.py <migration_file.sql>
"""

import sys
import os
import psycopg2
from urllib.parse import urlparse

def run_migration(migration_file: str):
    """
    Execute a SQL migration file against the database.

    Args:
        migration_file: Path to the .sql file to execute
    """
    # Get DATABASE_URL from environment (injected by Cloud Build via Secret Manager)
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse the DATABASE_URL
    parsed = urlparse(database_url)

    print(f"[Migration] Connecting to database...")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path[1:]}")
    print(f"  User: {parsed.username}")
    print(f"  Migration file: {migration_file}")
    print()

    # Check if migration file exists
    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    # Read the migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"[Migration] Loaded SQL file ({len(migration_sql)} bytes, {migration_sql.count(chr(10))} lines)")
    print()

    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )

        print("[Migration] Connected successfully")
        print()

        # Execute the migration
        with conn.cursor() as cursor:
            print("[Migration] Executing SQL migration...")
            cursor.execute(migration_sql)
            conn.commit()
            print("[Migration] ✓ Migration executed successfully")
            print()

            # Verify the tables were created
            print("[Verification] Checking migration results...")
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('prompt_templates', 'prompt_executions', 'prompt_guardrails', 'ab_test_experiments')
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()
            if tables:
                print("[Verification] Created tables:")
                for (table_name,) in tables:
                    print(f"  ✓ {table_name}")
            else:
                print("[Verification] Warning: Expected tables not found")
            print()

        conn.close()
        print("=" * 60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except psycopg2.Error as e:
        print(f"ERROR: Database error occurred:")
        print(f"  {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error:")
        print(f"  {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        sys.exit(1)

    migration_file = sys.argv[1]
    run_migration(migration_file)
