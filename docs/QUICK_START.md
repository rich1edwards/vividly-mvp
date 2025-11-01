# Quick Start Guide

This guide provides the essential commands and credentials you need to work with the Vividly development environment.

## Essential URLs

**Frontend:** https://dev-vividly-frontend-rm2v4spyrq-uc.a.run.app
**Backend API:** https://dev-vividly-api-758727113555.us-central1.run.app
**Login Page:** https://dev-vividly-frontend-rm2v4spyrq-uc.a.run.app/auth/login

## Demo Credentials

```
Email:    admin@vividly.demo
Password: VividlyAdmin2024!
Role:     SUPER_ADMIN
```

**After Login, Access:**
- Monitoring Dashboard: `/super-admin/monitoring`
- Main Dashboard: `/super-admin/dashboard`
- Organizations: `/super-admin/organizations`
- Settings: `/super-admin/settings`

## Database Access (The Correct Way)

### Quick Connect
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly"
```

### Run SQL Command
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT * FROM users LIMIT 5;"
```

### Run SQL File
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -f /path/to/script.sql
```

**For detailed database instructions:** See [database_access.md](./database_access.md)

## Common Database Operations

### List All Tables
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "\dt"
```

### View Table Structure
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "\d users"
```

### Query Users
```bash
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "SELECT user_id, email, role, status FROM users WHERE role = 'SUPER_ADMIN';"
```

## Create New Test User

```bash
# Step 1: Generate SQL with hashed password
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
source venv/bin/activate
python3 ../scripts/create_demo_superadmin_via_sql.py > /tmp/create_user.sql

# Step 2: Execute SQL
export PGPASSWORD="VividlyTest2025Simple"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -f /tmp/create_user.sql
```

## Important Enum Values

When creating users or updating data, use these exact enum values:

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

## Common Column Names (Don't Mix These Up!)

| ❌ WRONG           | ✅ CORRECT      | Notes                    |
|--------------------|-----------------|--------------------------|
| `hashed_password`  | `password_hash` | Column storing password  |
| `is_active`        | `status`        | User status (enum)       |
| `super_admin`      | `SUPER_ADMIN`   | Role enum value          |
| `active`           | `ACTIVE`        | Status enum value        |

## GCP Commands

### Get Database Password
```bash
gcloud secrets versions access latest \
  --secret="database-url-dev" \
  --project=vividly-dev-rich
```

### Check Cloud Run Services
```bash
# List all services
gcloud run services list \
  --project=vividly-dev-rich \
  --region=us-central1

# Get frontend URL
gcloud run services describe dev-vividly-frontend \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --format="value(status.url)"

# Get backend URL
gcloud run services describe dev-vividly-api \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --format="value(status.url)"
```

### Check Database Status
```bash
gcloud sql instances describe dev-vividly-db \
  --project=vividly-dev-rich
```

## Backend Development

### Run Tests
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend

# Activate virtual environment
source venv/bin/activate

# Run all tests
DATABASE_URL="sqlite:///:memory:" \
SECRET_KEY=test_secret_key_12345 \
ALGORITHM=HS256 \
DEBUG=True \
CORS_ORIGINS=http://localhost \
PYTHONPATH=/Users/richedwards/AI-Dev-Projects/Vividly/backend \
./venv_test/bin/python -m pytest
```

### Run Backend Locally
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Frontend Development

### Run Frontend Locally
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/frontend
npm install
npm run dev
```

### Build Frontend
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/frontend
npm run build
```

## Project Structure

```
Vividly/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Security, config
│   │   ├── models/         # SQLAlchemy models
│   │   └── services/       # Business logic
│   ├── migrations/         # Alembic migrations
│   └── tests/              # Test suite
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API clients
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   └── store/         # State management
├── terraform/              # Infrastructure as code
├── scripts/               # Utility scripts
└── docs/                  # Documentation
    ├── database_access.md # Detailed DB access guide
    ├── test_users.md      # Test user credentials
    └── QUICK_START.md     # This file
```

## Helpful Shell Aliases

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# Vividly Database
alias vividly-db="PGPASSWORD='VividlyTest2025Simple' /opt/homebrew/opt/postgresql@15/bin/psql -h 34.56.211.136 -U vividly -d vividly"

# Vividly Backend
alias vividly-backend="cd /Users/richedwards/AI-Dev-Projects/Vividly/backend && source venv/bin/activate"

# Vividly Frontend
alias vividly-frontend="cd /Users/richedwards/AI-Dev-Projects/Vividly/frontend"

# Vividly GCloud
alias vividly-gcloud="export CLOUDSDK_CONFIG='/Users/richedwards/.gcloud' && gcloud config set project vividly-dev-rich"
```

Usage:
```bash
# Connect to database
vividly-db -c "SELECT * FROM users LIMIT 5;"

# Go to backend and activate venv
vividly-backend

# Go to frontend
vividly-frontend
```

## Troubleshooting

### "psql: command not found"
```bash
brew install postgresql@15
```

### "password authentication failed"
Make sure you're using the correct password:
```bash
export PGPASSWORD="VividlyTest2025Simple"
```

### "column does not exist"
Check the actual schema:
```bash
vividly-db -c "\d users"
```

Common mistakes:
- Using `hashed_password` instead of `password_hash`
- Using `is_active` instead of `status`
- Not quoting enum values: `'SUPER_ADMIN'` not `SUPER_ADMIN`

### Frontend Not Loading
1. Check frontend service is running:
   ```bash
   gcloud run services describe dev-vividly-frontend \
     --region=us-central1 \
     --project=vividly-dev-rich
   ```

2. Check it's pointing to correct API URL in build config

### Can't Login
1. Verify user exists:
   ```bash
   vividly-db -c "SELECT * FROM users WHERE email = 'admin@vividly.demo';"
   ```

2. Check user status is `ACTIVE`:
   ```bash
   vividly-db -c "SELECT email, status FROM users WHERE email = 'admin@vividly.demo';"
   ```

## Additional Documentation

- **[Database Access Guide](./database_access.md)** - Comprehensive database connection methods
- **[Test Users](./test_users.md)** - All test user credentials and access information
- **[Architecture](../architecture.md)** - System architecture overview
- **[API Documentation](../backend/README.md)** - Backend API details
- **[Security Testing](../docs/SECURITY_TESTING.md)** - Security test suite

## Quick Development Workflow

### 1. Make Backend Changes
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
source venv/bin/activate
# Make changes
pytest  # Run tests
```

### 2. Make Frontend Changes
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/frontend
# Make changes
npm run build
```

### 3. Deploy Changes
```bash
# Backend (uses Cloud Build)
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
gcloud builds submit --tag us-central1-docker.pkg.dev/vividly-dev-rich/vividly/backend-api:latest

# Frontend (uses Cloud Build)
cd /Users/richedwards/AI-Dev-Projects/Vividly/frontend
gcloud builds submit --config=cloudbuild.yaml
```

---

**Last Updated:** 2025-10-31

**For Database Issues:** Always refer to [database_access.md](./database_access.md) - it has the correct connection method.
