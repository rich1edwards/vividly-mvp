# Database Access Guide

This document provides the correct methods for accessing the Cloud SQL PostgreSQL database.

## Database Information

- **Instance Name:** `dev-vividly-db`
- **Project:** `vividly-dev-rich`
- **Region:** `us-central1`
- **Connection Name:** `vividly-dev-rich:us-central1:dev-vividly-db`
- **Database Name:** `vividly`
- **Database User:** `vividly`
- **Public IP:** `34.56.211.136`
- **PostgreSQL Version:** 15

## Credentials

Database credentials are stored in GCP Secret Manager:

```bash
# Get the full DATABASE_URL (includes password)
gcloud secrets versions access latest \
  --secret="database-url-dev" \
  --project=vividly-dev-rich

# Output format:
# postgresql://vividly:VividlyTest2025Simple@/vividly?host=/cloudsql/vividly-dev-rich:us-central1:dev-vividly-db
```

**Database Password:** `VividlyTest2025Simple`

## Method 1: Direct psql Connection (RECOMMENDED)

This is the simplest and most reliable method for running SQL commands.

### Prerequisites

Install PostgreSQL client (one-time setup):
```bash
brew install postgresql@15
```

### Connect and Execute SQL

```bash
# Set password as environment variable
export PGPASSWORD="VividlyTest2025Simple"

# Connect to database
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly"
```

### Run SQL from File

```bash
export PGPASSWORD="VividlyTest2025Simple"

/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -f /path/to/your/script.sql
```

### Run Single SQL Command

```bash
export PGPASSWORD="VividlyTest2025Simple"

/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT * FROM users LIMIT 5;"
```

### Useful Database Commands

```bash
# List all tables
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "\dt"

# Describe table structure
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "\d users"

# Get enum values
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'userrole'::regtype ORDER BY enumsortorder;"
```

## Method 2: Python Script with SQLAlchemy

For operations that need password hashing or complex logic:

```bash
# Navigate to backend directory
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Activate virtual environment
source venv/bin/activate

# Run Python script
python3 your_script.py
```

**Example Python Script:**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Direct connection using public IP
DATABASE_URL = "postgresql://vividly:VividlyTest2025Simple@34.56.211.136:5432/vividly"

def run_query():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT * FROM users LIMIT 5"))
        for row in result:
            print(row)
    finally:
        db.close()

if __name__ == "__main__":
    run_query()
```

## Method 3: gcloud sql connect (AVOID - Has Issues)

**DO NOT USE THIS METHOD** - It has authentication issues and PATH conflicts.

~~The `gcloud sql connect` command does not work reliably due to:~~
- ~~Password authentication failures~~
- ~~PATH conflicts when setting up psql~~
- ~~Complex multi-step setup~~

## Common SQL Operations

### Create a User with Hashed Password

```bash
# Step 1: Generate SQL with hashed password
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
source venv/bin/activate

python3 -c "
from app.core.security import get_password_hash
import uuid

user_id = str(uuid.uuid4())
email = 'test@example.com'
password = 'TestPassword123!'
password_hash = get_password_hash(password)

print(f'''
DELETE FROM users WHERE email = '{email}';

INSERT INTO users (
    user_id, email, password_hash, first_name, last_name,
    role, status, created_at, updated_at
) VALUES (
    '{user_id}',
    '{email}',
    '{password_hash}',
    'Test',
    'User',
    'STUDENT',
    'ACTIVE',
    NOW(),
    NOW()
);

SELECT user_id, email, role, status FROM users WHERE email = '{email}';
''')
" > /tmp/create_user.sql

# Step 2: Execute the SQL
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -f /tmp/create_user.sql
```

### Query Users

```bash
export PGPASSWORD="VividlyTest2025Simple"

# Get all super admins
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT user_id, email, role, status FROM users WHERE role = 'SUPER_ADMIN';"

# Search by email
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT * FROM users WHERE email LIKE '%@vividly.demo';"
```

### Update User

```bash
export PGPASSWORD="VividlyTest2025Simple"

/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "UPDATE users SET role = 'SUPER_ADMIN' WHERE email = 'admin@vividly.demo';"
```

### Delete User

```bash
export PGPASSWORD="VividlyTest2025Simple"

/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "DELETE FROM users WHERE email = 'test@example.com';"
```

## Database Schema Quick Reference

### Users Table

```sql
Table "public.users"
     Column      |            Type             |
-----------------+-----------------------------+
 user_id         | character varying(100)      | PRIMARY KEY
 email           | character varying(255)      | UNIQUE, NOT NULL
 password_hash   | text                        | NOT NULL
 first_name      | character varying(100)      | NOT NULL
 last_name       | character varying(100)      | NOT NULL
 role            | userrole                    | NOT NULL (enum)
 status          | userstatus                  | NOT NULL (enum)
 grade_level     | integer                     |
 school_id       | character varying(100)      |
 organization_id | character varying(100)      |
 teacher_data    | json                        |
 settings        | json                        |
 created_at      | timestamp without time zone | DEFAULT NOW()
 updated_at      | timestamp without time zone | DEFAULT NOW()
 last_login_at   | timestamp without time zone |
 archived        | boolean                     |
 archived_at     | timestamp without time zone |
```

### Enum Types

**UserRole:**
- `STUDENT`
- `TEACHER`
- `ADMIN`
- `SUPER_ADMIN`

**UserStatus:**
- `ACTIVE`
- `SUSPENDED`
- `PENDING`
- `ARCHIVED`

## Troubleshooting

### "psql: command not found"

Install PostgreSQL client:
```bash
brew install postgresql@15
```

The psql binary is located at:
```
/opt/homebrew/opt/postgresql@15/bin/psql
```

### "password authentication failed"

Make sure you're using the correct password:
```bash
export PGPASSWORD="VividlyTest2025Simple"
```

Verify the password from secrets:
```bash
gcloud secrets versions access latest \
  --secret="database-url-dev" \
  --project=vividly-dev-rich
```

### "connection refused"

Check if public IP is enabled:
```bash
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(settings.ipConfiguration.ipv4Enabled)"
```

Should return: `True`

Get the public IP:
```bash
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich \
  --format="value(ipAddresses[0].ipAddress)"
```

Should return: `34.56.211.136`

### "column does not exist"

Common mistakes:
- Using `hashed_password` instead of `password_hash`
- Using `is_active` instead of `status`
- Not using quotes around enum values: `'SUPER_ADMIN'` not `SUPER_ADMIN`

Always check the actual schema:
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "\d users"
```

## Security Best Practices

1. **Never commit passwords to git**
   - Always use environment variables or Secret Manager

2. **Use SSL in production**
   - The connection string should include `sslmode=require`

3. **Rotate credentials regularly**
   - Update secrets in GCP Secret Manager
   - Restart services to pick up new credentials

4. **Limit IP access**
   - Only allow necessary IPs in authorized networks
   - Use Cloud SQL Auth Proxy for application connections

5. **Use least privilege**
   - Application should not use postgres superuser
   - Create role-specific database users

## Application Connection

The deployed application uses Unix socket connections via Cloud SQL Auth Proxy:

```
postgresql://vividly:VividlyTest2025Simple@/vividly?host=/cloudsql/vividly-dev-rich:us-central1:dev-vividly-db
```

This only works inside Cloud Run. For local development, use the public IP method.

## Quick Reference Commands

```bash
# Save these to your shell profile for easy access

# Database connection helper
alias vividly-db="PGPASSWORD='VividlyTest2025Simple' /opt/homebrew/opt/postgresql@15/bin/psql -h 34.56.211.136 -U vividly -d vividly"

# Now you can just run:
vividly-db -c "SELECT * FROM users LIMIT 5;"
```

## Related Documentation

- [Test Users](./test_users.md) - Demo account credentials
- [Backend README](../backend/README.md) - API documentation
- [Database Schema](./database_schema.md) - Full schema documentation
- [Migration Guide](../backend/migrations/README.md) - Alembic migrations

---

**Last Updated:** 2025-10-31
**Maintained By:** Development Team

**IMPORTANT:** Always use Method 1 (Direct psql Connection) for reliability and simplicity.
