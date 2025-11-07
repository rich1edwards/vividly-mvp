#!/usr/bin/env python3
"""
Run Phase 1A Dual Modality Migration via Python
Connects to Cloud SQL database and applies migration SQL.
"""
import os
import sys
import psycopg2
import subprocess

def get_database_url():
    """Get DATABASE_URL from Secret Manager."""
    try:
        result = subprocess.run(
            [
                "/opt/homebrew/share/google-cloud-sdk/bin/gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                "--secret=database-url-dev",
                "--project=vividly-dev-rich"
            ],
            env={"CLOUDSDK_CONFIG": os.path.expanduser("~/.gcloud")},
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get database URL: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

def run_migration(database_url, migration_file):
    """Run migration SQL file against database."""
    print("=" * 60)
    print("Phase 1A Dual Modality Migration")
    print("=" * 60)
    print(f"Migration file: {migration_file}")
    print()

    # Read migration file
    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"Migration SQL size: {len(migration_sql)} bytes")
    print()

    # Connect to database
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()

        print("Connected successfully!")
        print()
        print("Running migration...")
        print("(This may take 1-2 minutes for indexes)")
        print()

        # Execute migration
        cursor.execute(migration_sql)

        # Commit transaction
        conn.commit()

        print()
        print("=" * 60)
        print("MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print("Changes:")
        print("  - Added 4 columns to content_requests")
        print("  - Added 10 columns to content_metadata")
        print("  - Added 3 columns to users")
        print("  - Added 8 columns to request_metrics")
        print("  - Created 5 new indexes")
        print("  - Added 4 new pipeline stages")
        print("  - Created 2 analytics views")
        print("  - Created 1 trigger")
        print()
        print("Next: Restart Cloud Run services to pick up schema changes")
        print("=" * 60)

        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print()
        print("=" * 60)
        print("MIGRATION FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Attempting rollback...")
        try:
            conn.rollback()
            print("Rollback successful.")
        except:
            print("Rollback failed.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migration_file = "/Users/richedwards/AI-Dev-Projects/Vividly/backend/migrations/add_dual_modality_phase1.sql"

    print("Getting database URL from Secret Manager...")
    database_url = get_database_url()
    print("Database URL retrieved.")
    print()

    run_migration(database_url, migration_file)
