# Test User Credentials

This document contains login credentials for test users in the Vividly development environment.

## All Test Accounts

### Demo Super Admin Account

The super admin account has full system access and can view the request monitoring dashboard.

```
Email:    admin@vividly.demo
Password: VividlyAdmin2024!
Role:     SUPER_ADMIN
User ID:  d938ca4e-af3f-49a7-81b5-77c580c7e425
Status:   ACTIVE
```

### Demo Student Account

The student account can request content, view videos, and manage their profile.

```
Email:    student1@test.com
Password: password123
Role:     STUDENT
User ID:  35c3c63f-c6a5-4cfa-a7d0-660c502ca5cb
Status:   ACTIVE
```

### Demo Teacher Account

The teacher account can manage classes and students.

```
Email:    teacher1@test.com
Password: password123
Role:     TEACHER
User ID:  d41e02bb-fd09-47c6-8192-ba876f337148
Status:   ACTIVE
```

### Access URLs

**Frontend Application:**
- Production: https://dev-vividly-frontend-rm2v4spyrq-uc.a.run.app
- Login: https://dev-vividly-frontend-rm2v4spyrq-uc.a.run.app/auth/login

**Super Admin Dashboard:**
- Main Dashboard: `/super-admin/dashboard`
- Request Monitoring: `/super-admin/monitoring`
- Organizations: `/super-admin/organizations`
- System Settings: `/super-admin/settings`

**Student Dashboard:**
- Main Dashboard: `/student/dashboard`
- Request Content: `/student/content/request`
- My Videos: `/student/videos`
- Profile: `/student/profile`

**Teacher Dashboard:**
- Main Dashboard: `/teacher/dashboard`
- My Classes: `/teacher/classes`
- Students: `/teacher/students`

### Permissions

The super admin role has access to:
- ✅ View all content generation requests across all users
- ✅ Search requests by student email or ID
- ✅ Monitor real-time pipeline flow through 8 stages
- ✅ View confidence scores and detailed event logs
- ✅ Access system metrics and analytics
- ✅ Manage all organizations and users
- ✅ Configure system settings

## Request Monitoring Dashboard Features

The monitoring dashboard (`/super-admin/monitoring`) provides:

### Real-time Tracking
- Auto-refresh every 5 seconds (toggle on/off)
- Live status updates for all active requests
- Visual pipeline progress indicators

### Search & Filter
- Search by student email address
- Search by student user ID
- View all requests or filter by criteria

### Pipeline Stages Tracked
1. **Request Received** - Initial request logged
2. **NLU Extraction** - Natural language understanding processing
3. **Interest Matching** - Student interest profile matching
4. **RAG Retrieval** - Retrieval-augmented generation context gathering
5. **Script Generation** - AI script writing with confidence scores
6. **TTS Generation** - Text-to-speech audio generation
7. **Video Generation** - Final video assembly
8. **Completed/Failed** - Final status with full event history

### Metrics Displayed
- Total requests processed
- Active requests in progress
- Successfully completed requests
- Failed requests with error details
- Average processing time per stage
- Confidence scores for AI-generated content

## Database Schema

The user is stored in the `users` table with the following structure:

```sql
Table "public.users"
     Column      |            Type             |   Value
-----------------+-----------------------------+----------
 user_id         | character varying(100)      | d938ca4e-af3f-49a7-81b5-77c580c7e425
 email           | character varying(255)      | admin@vividly.demo
 password_hash   | text                        | [bcrypt hash]
 first_name      | character varying(100)      | Super
 last_name       | character varying(100)      | Admin
 role            | userrole (enum)             | SUPER_ADMIN
 status          | userstatus (enum)           | ACTIVE
 created_at      | timestamp without time zone | [timestamp]
 updated_at      | timestamp without time zone | [timestamp]
```

### Enum Values

**UserRole:**
- STUDENT
- TEACHER
- ADMIN
- SUPER_ADMIN

**UserStatus:**
- ACTIVE
- SUSPENDED
- PENDING
- ARCHIVED

## How to Create Additional Test Users

To create additional test users, use the following scripts:

### Method 1: Python Script (Recommended)

Located at: `/Users/richedwards/AI-Dev-Projects/Vividly/scripts/create_demo_superadmin_via_sql.py`

This script generates SQL statements with properly hashed passwords using the application's security module.

```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
source venv/bin/activate
python3 ../scripts/create_demo_superadmin_via_sql.py > /tmp/user.sql
```

### Method 2: Direct SQL Execution

Use this template to create users directly:

```bash
export PGPASSWORD="[DATABASE_PASSWORD]"
/opt/homebrew/opt/postgresql@15/bin/psql \
  -h "34.56.211.136" \
  -U "vividly" \
  -d "vividly" \
  -c "INSERT INTO users (...) VALUES (...);"
```

### Method 3: Via API (Future)

A user management API endpoint could be created for easier user provisioning.

## Security Notes

**IMPORTANT:**
- These are TEST credentials for the DEVELOPMENT environment only
- Never use these credentials in production
- The password should be changed for any long-term testing
- Database password is stored in GCP Secret Manager: `database-url-dev`
- JWT secrets are stored in GCP Secret Manager: `jwt-secret-dev`

## Troubleshooting

### Cannot Connect to Database

If you cannot connect to Cloud SQL:

1. **Check IP Allowlist:**
   ```bash
   gcloud sql instances describe dev-vividly-db \
     --project=vividly-dev-rich \
     --format="value(settings.ipConfiguration.authorizedNetworks)"
   ```

2. **Your IP is auto-allowlisted for 5 minutes when using `gcloud sql connect`**

3. **Verify database credentials:**
   ```bash
   gcloud secrets versions access latest \
     --secret="database-url-dev" \
     --project=vividly-dev-rich
   ```

### Login Fails

If login fails with these credentials:

1. **Verify user exists:**
   ```bash
   export PGPASSWORD="VividlyTest2025Simple"
   /opt/homebrew/opt/postgresql@15/bin/psql \
     -h "34.56.211.136" \
     -U "vividly" \
     -d "vividly" \
     -c "SELECT user_id, email, role, status FROM users WHERE email = 'admin@vividly.demo';"
   ```

2. **Check user status is ACTIVE**

3. **Verify frontend is pointing to correct API URL**

4. **Check browser console for errors**

### Monitoring Dashboard Not Loading

If the monitoring dashboard doesn't load:

1. **Verify you're logged in as SUPER_ADMIN role**

2. **Check API endpoint is accessible:**
   ```bash
   curl https://dev-vividly-api-758727113555.us-central1.run.app/health
   ```

3. **Check monitoring endpoints:**
   ```bash
   curl -H "Authorization: Bearer [YOUR_JWT_TOKEN]" \
     https://dev-vividly-api-758727113555.us-central1.run.app/api/v1/monitoring/metrics
   ```

## Related Documentation

- [Architecture Documentation](../architecture.md)
- [API Endpoints](../backend/README.md)
- [Frontend Routes](../frontend/src/App.tsx)
- [Database Schema](../docs/database_schema.md)
- [Security Architecture](../docs/security_architecture.md)

## Maintenance

This file should be updated whenever:
- Test users are added or modified
- URLs change (new deployments)
- Access permissions are updated
- New features are added to the monitoring dashboard

**Last Updated:** 2025-10-31
**Created By:** Claude Code (Automated Setup)
