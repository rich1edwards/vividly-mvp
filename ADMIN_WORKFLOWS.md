# Admin Workflows

## Table of Contents
1. [Overview](#overview)
2. [Organization Management](#organization-management)
   - [Onboard New Organization](#onboard-new-organization)
   - [Update Organization Settings](#update-organization-settings)
   - [Suspend/Archive Organization](#suspendarchive-organization)
3. [User Management](#user-management)
   - [Create Admin User](#create-admin-user)
   - [Reset User Password](#reset-user-password)
   - [Handle Locked Account](#handle-locked-account)
   - [Bulk User Import](#bulk-user-import)
4. [Subscription Management](#subscription-management)
   - [Upgrade Subscription Tier](#upgrade-subscription-tier)
   - [Adjust Quotas](#adjust-quotas)
   - [Handle Quota Exceeded](#handle-quota-exceeded)
5. [Content Management](#content-management)
   - [Review Flagged Content](#review-flagged-content)
   - [Delete Inappropriate Content](#delete-inappropriate-content)
   - [Clear Cache for Topic](#clear-cache-for-topic)
6. [Troubleshooting](#troubleshooting)
   - [Investigate User Cannot Log In](#investigate-user-cannot-log-in)
   - [Debug Video Generation Failure](#debug-video-generation-failure)
   - [Handle High Error Rate](#handle-high-error-rate)
7. [Monitoring and Alerts](#monitoring-and-alerts)
   - [Review Daily Metrics](#review-daily-metrics)
   - [Respond to Performance Alert](#respond-to-performance-alert)
   - [Investigate Security Incident](#investigate-security-incident)
8. [Maintenance](#maintenance)
   - [Schedule Maintenance Window](#schedule-maintenance-window)
   - [Database Backup and Restore](#database-backup-and-restore)
   - [Update Platform Configuration](#update-platform-configuration)

---

## Overview

This document provides step-by-step administrative workflows for Vividly platform operators. These procedures are designed for:
- **Vividly Internal Admins**: Platform operators managing the system
- **Support Team**: Handling customer support requests
- **SRE/DevOps**: Managing infrastructure and deployments

**Access Requirements**:
- Admin user account with `role = 'admin'`
- Access to Google Cloud Console
- Access to internal admin panel: `/internal/admin`
- For some procedures: SSH/console access to GCP resources

**Tools Used**:
- Vividly Admin Portal (`/internal/admin`)
- Google Cloud Console
- Terraform (for infrastructure changes)
- `gcloud` CLI
- PostgreSQL admin tools (for direct DB access if needed)

---

## Organization Management

### Onboard New Organization

**When**: New school or district signs contract

**Prerequisites**:
- Signed contract with subscription details
- Organization contact information
- Billing details

**Procedure**:

```
STEP 1: Gather Organization Information
├─> Collect from sales team:
│   - Organization name
│   - Type: school | district
│   - Address (street, city, state, zip)
│   - Subscription tier: basic | standard | premium
│   - Contract period (start and end dates)
│   - Quotas:
│     * max_students (default: 500)
│     * max_teachers (default: 50)
│     * max_admins (default: 5)
│   - Primary admin contact:
│     * Name
│     * Email
│     * Phone

STEP 2: Create Organization in Database
├─> Navigate to: /internal/admin/organizations/create
├─> Fill organization form:
│   ┌──────────────────────────────────────────────────┐
│   │ Create New Organization                          │
│   │                                                  │
│   │ Organization Name:                               │
│   │ [Lincoln High School_________________]           │
│   │                                                  │
│   │ Type:                                            │
│   │ ● School  ○ District                             │
│   │                                                  │
│   │ Address:                                         │
│   │ Street: [123 Main St_________________]           │
│   │ City:   [Springfield_________________]           │
│   │ State:  [IL__________________________]           │
│   │ Zip:    [62701_______________________]           │
│   │                                                  │
│   │ Subscription:                                    │
│   │ Tier: [▼ Standard____________________]           │
│   │ Start: [2024-01-01___________________]           │
│   │ End:   [2025-06-30___________________]           │
│   │                                                  │
│   │ Quotas:                                          │
│   │ Max Students: [500____]                          │
│   │ Max Teachers: [50_____]                          │
│   │ Max Admins:   [5______]                          │
│   │                                                  │
│   │ [Cancel]                [Create Organization]    │
│   └──────────────────────────────────────────────────┘
│
├─> Click "Create Organization"
│   API: POST /api/v1/internal/organizations
│   Response: {"org_id": "org_lincoln_abc123", ...}
│
├─> Verify creation:
│   ✓ Organization appears in org list
│   ✓ Status: active
│   ✓ Quotas set correctly

STEP 3: Create Primary Admin User
├─> Navigate to: /internal/admin/users/create
├─> Fill admin user form:
│   ┌──────────────────────────────────────────────────┐
│   │ Create Admin User                                │
│   │                                                  │
│   │ Organization:                                    │
│   │ [▼ Lincoln High School (org_lincoln_abc123)]     │
│   │                                                  │
│   │ Email:                                           │
│   │ [admin@lincoln.edu_____________________]         │
│   │                                                  │
│   │ First Name:                                      │
│   │ [Sarah_________________________________]         │
│   │                                                  │
│   │ Last Name:                                       │
│   │ [Johnson_______________________________]         │
│   │                                                  │
│   │ Role:                                            │
│   │ ● Admin  ○ Teacher  ○ Student                    │
│   │                                                  │
│   │ [x] Send welcome email                           │
│   │ [x] Is primary admin                             │
│   │                                                  │
│   │ [Cancel]                [Create User]            │
│   └──────────────────────────────────────────────────┘
│
├─> Click "Create User"
│   - System generates temporary password
│   - System sends welcome email with setup link
│   - Setup link expires in 48 hours
│
├─> Copy temporary credentials (for backup):
│   Email: admin@lincoln.edu
│   Temp Password: [redacted - shown once]

STEP 4: Document Organization Setup
├─> Create entry in internal CRM/wiki:
│   - Organization ID: org_lincoln_abc123
│   - Primary admin: Sarah Johnson (admin@lincoln.edu)
│   - Created: 2024-01-01
│   - Contract end: 2025-06-30
│   - Quotas: 500 students / 50 teachers / 5 admins
│   - Support tier: Standard
│   - Notes: [Any special requirements]

STEP 5: Notify Sales Team
├─> Send email to sales contact:
│   Subject: "Organization Setup Complete: Lincoln High School"
│   Body:
│   """
│   The organization has been successfully set up in Vividly.
│
│   Organization ID: org_lincoln_abc123
│   Primary Admin: Sarah Johnson (admin@lincoln.edu)
│   Login URL: https://app.vividly.edu
│
│   The admin has been sent login credentials and setup instructions.
│   They can begin inviting teachers immediately.
│   """

STEP 6: Monitor Initial Setup
├─> Add to monitoring checklist:
│   Day 1: Check if admin completed account setup
│   Day 3: Check if any teachers created
│   Day 7: Check if any students invited
│   Day 14: Review initial usage metrics
│
└─> If no activity by Day 7:
    - Contact admin to offer onboarding assistance
    - Schedule training call if needed

COMPLETION TIME: 15-20 minutes
FOLLOW-UP REQUIRED: Yes (Day 7 check-in)
```

---

### Update Organization Settings

**When**: Organization requests changes to settings or quotas

**Procedure**:

```
STEP 1: Verify Authorization
├─> Confirm request came from:
│   - Primary admin for the organization
│   - Vividly sales/account manager
│   - Authorized support ticket
│
└─> If uncertain, contact organization admin to verify

STEP 2: Navigate to Organization Settings
├─> Go to: /internal/admin/organizations
├─> Search for organization by name or ID
├─> Click organization name to view details
├─> Click "Edit Settings"

STEP 3: Update Settings
Common changes:

A. Update Subscription End Date (Contract Renewal)
├─> Navigate to: Subscription tab
├─> Update "Contract End Date"
│   Old: 2025-06-30
│   New: 2026-06-30
├─> Click "Save"
├─> Verify: No service interruption

B. Increase Student Quota
├─> Navigate to: Quotas tab
├─> Current: max_students = 500
├─> Update: max_students = 750
├─> Reason: Organization expanded
├─> Click "Save"
├─> Verify: Admins can now invite up to 750 students

C. Change Subscription Tier
├─> Navigate to: Subscription tab
├─> Current: standard
├─> Update: premium
├─> This enables:
│   ✓ Priority support
│   ✓ Advanced analytics
│   ✓ Custom branding (if available)
├─> Click "Save"
├─> Verify: Premium features visible to org admins

D. Update Organization Contact Info
├─> Navigate to: Details tab
├─> Update:
│   - Address (if school moved)
│   - Primary admin (if changed)
│   - Phone number
├─> Click "Save"

STEP 4: Document Change
├─> Add note to organization record:
│   Date: 2024-06-15
│   Change: Increased max_students from 500 to 750
│   Requested by: Sarah Johnson (admin@lincoln.edu)
│   Ticket: SUP-1234
│
└─> Update internal CRM/wiki

STEP 5: Notify Organization
├─> Send confirmation email:
│   To: Primary admin email
│   Subject: "Organization Settings Updated"
│   Body:
│   """
│   Your organization settings have been updated:
│
│   Change: Student quota increased
│   New limit: 750 students (previously 500)
│
│   This change is effective immediately.
│   """

COMPLETION TIME: 5-10 minutes
```

---

### Suspend/Archive Organization

**When**: Contract expires, payment issues, or Terms of Service violation

**Procedure**:

```
STEP 1: Determine Suspension Type
├─> SOFT SUSPENSION (Temporary - Payment Issue)
│   - Block new content requests
│   - Allow viewing existing content
│   - Allow exports
│   - Duration: Until payment resolved (typically 7-30 days)
│
└─> HARD SUSPENSION (Permanent - Contract Ended)
    - Block all access (read and write)
    - Preserve data for 90 days
    - Allow data export for 30 days
    - After 90 days: Delete all data

STEP 2: Notify Organization (Before Suspension)
├─> Email primary admin (7 days before):
│   Subject: "Action Required: Vividly Account Expiring"
│   Body:
│   """
│   Your Vividly contract expires on 2025-06-30.
│
│   To avoid service interruption:
│   - Contact our sales team to renew: sales@vividly.edu
│   - Or export your data before expiration
│
│   After expiration:
│   - Access will be suspended
│   - Data preserved for 90 days
│   - Export available for 30 days
│   """
│
└─> Follow-up email (3 days before, 1 day before)

STEP 3: Execute Suspension
├─> Navigate to: /internal/admin/organizations/{org_id}
├─> Click "Suspend Organization"
├─> Select suspension type:
│   ○ Soft Suspension (temporary payment issue)
│   ● Hard Suspension (contract ended)
│
├─> Set data retention:
│   Data preservation: [90 days]
│   Export window: [30 days]
│
├─> Confirm suspension:
│   "This will immediately block access for all users in this organization."
│   [Cancel] [Confirm Suspension]
│
├─> API: PATCH /api/v1/internal/organizations/{org_id}
│   Body: {
│     "status": "suspended",
│     "suspension_type": "hard",
│     "suspended_at": "2025-06-30T00:00:00Z",
│     "data_retention_until": "2025-09-28",
│     "export_available_until": "2025-07-30"
│   }

STEP 4: Verify Suspension
├─> Test user login:
│   - Navigate to: https://app.vividly.edu/login
│   - Attempt login with org user
│   - Expected: "Your organization's subscription has expired."
│   - Display: Contact info for renewal
│
├─> Test API access:
│   - API requests return: 403 Forbidden
│   - Error message: "Organization suspended"
│
└─> Verify data access:
    - Database records still exist (not deleted)
    - Marked with status = 'suspended'

STEP 5: Notify Users
├─> System sends email to all org users:
│   Subject: "Vividly Access Suspended"
│   Body:
│   """
│   Your organization's Vividly subscription has ended.
│
│   Access has been suspended as of 2025-06-30.
│
│   Your data is preserved until: 2025-09-28
│   Export available until: 2025-07-30
│
│   To restore access or export data, contact:
│   [Primary Admin Email]
│   or sales@vividly.edu
│   """

STEP 6: Schedule Data Deletion
├─> Create scheduled job:
│   Job: delete_org_data
│   Org ID: org_lincoln_abc123
│   Execute at: 2025-09-28T00:00:00Z
│
├─> Job will:
│   1. Delete all organization data:
│      - Users
│      - Classes
│      - Content requests
│      - Learning history
│      - Generated content (videos)
│   2. Preserve audit log (anonymized)
│   3. Update org status to 'deleted'
│
└─> Send final notification (7 days before deletion):
    "Final reminder: Your data will be permanently deleted in 7 days."

STEP 7: Handle Reactivation (If Organization Renews)
├─> If org renews before deletion date:
│   1. Update contract end date
│   2. Set status back to 'active'
│   3. Re-enable user access
│   4. Cancel deletion job
│   5. Notify users: "Access restored"
│
└─> API: PATCH /api/v1/internal/organizations/{org_id}
    Body: {
      "status": "active",
      "contract_end": "2026-06-30",
      "suspension_type": null,
      "suspended_at": null
    }

COMPLETION TIME: 15-20 minutes
FOLLOW-UP: Monitor deletion job execution
```

---

## User Management

### Create Admin User

**When**: Organization needs additional administrators

**Procedure**:

```
STEP 1: Verify Request
├─> Confirm request from:
│   - Existing primary admin for the org
│   - Via support ticket with proper authorization
│
└─> Check org quota:
    Current admins: 2
    Max admins: 5
    ✓ Can create new admin (within quota)

STEP 2: Create Admin User
├─> Navigate to: /internal/admin/users/create
├─> Fill form:
│   Organization: Lincoln High School
│   Email: tom.anderson@lincoln.edu
│   First Name: Tom
│   Last Name: Anderson
│   Role: Admin
│   [x] Send welcome email
│   [ ] Is primary admin (only one primary per org)
│
├─> Click "Create User"
├─> API: POST /api/v1/internal/users
│   Response: {"user_id": "user_tom_xyz", ...}

STEP 3: Send Credentials
├─> System automatically sends welcome email
├─> Email includes:
│   - Temporary password (24-char random)
│   - Setup link (expires in 48 hours)
│   - Instructions for first login
│
├─> Backup: Copy temp credentials to secure note:
│   User: tom.anderson@lincoln.edu
│   Temp PW: [redacted]
│   Expires: 2024-01-17 12:00 UTC

STEP 4: Notify Primary Admin
├─> Send email to primary admin:
│   Subject: "New Admin User Created"
│   Body:
│   """
│   A new administrator has been added to your organization:
│
│   Name: Tom Anderson
│   Email: tom.anderson@lincoln.edu
│
│   They will receive setup instructions via email.
│   """

STEP 5: Document Creation
├─> Update org notes:
│   "Added admin user: Tom Anderson (tom.anderson@lincoln.edu) on 2024-01-15"
│
└─> If this is a replacement admin:
    "Replaced previous admin: [name] - [reason]"

COMPLETION TIME: 5 minutes
```

---

### Reset User Password

**When**: User forgot password or account locked

**Procedure**:

```
STEP 1: Verify Identity
├─> If user contacted support directly:
│   - Verify email address
│   - Ask security question (if configured)
│   - Or: Send verification email with code
│
└─> If admin requested reset for their users:
    - Verify admin is from same organization
    - Verify admin has permission to manage this user

STEP 2: Locate User
├─> Navigate to: /internal/admin/users
├─> Search by:
│   - Email: sarah.johnson@lincoln.edu
│   - Or Name: Sarah Johnson
│   - Or User ID: user_sarah_abc123
│
└─> Click on user to view details

STEP 3: Reset Password
├─> Click "Actions" → "Reset Password"
├─> Choose reset method:
│   ● Send reset email to user
│   ○ Generate temporary password and provide to admin
│
├─> For "Send reset email":
│   - Click "Send Password Reset Email"
│   - API: POST /api/v1/internal/users/{user_id}/reset-password
│   - User receives email with reset link (expires in 24 hours)
│   - User must set new password via link
│
├─> For "Generate temp password" (for students without email access):
│   - Click "Generate Temporary Password"
│   - System shows temp password: [display once]
│   - Copy and provide to organization admin
│   - Admin provides to student
│   - Student must change on first login

STEP 4: Unlock Account (If Locked)
├─> If account locked due to failed login attempts:
│   - User status shows: 🔒 Locked
│   - Click "Unlock Account"
│   - API: PATCH /api/v1/internal/users/{user_id}
│     Body: {"locked": false, "failed_login_attempts": 0}
│   - User can now log in with correct password
│
└─> If password was also reset:
    - Unlocking happens automatically upon password reset

STEP 5: Verify and Document
├─> Verify:
│   ✓ User status: Active (not locked)
│   ✓ Must change password: true (if temp password)
│   ✓ Reset email sent (check logs)
│
├─> Add note to user record:
│   "Password reset on 2024-01-15 by [admin_name]. Reason: User forgot password."
│
└─> If this is via support ticket:
    Update ticket: "Password reset completed. User should receive email shortly."

STEP 6: Follow-Up
├─> If user reports not receiving email:
│   - Check spam folder
│   - Verify email address is correct
│   - Resend reset email
│   - If still failing: Generate temp password instead
│
└─> If user cannot set new password:
    - Check password complexity requirements
    - Verify reset link not expired
    - Generate new reset link if needed

COMPLETION TIME: 3-5 minutes
```

---

### Handle Locked Account

**When**: User locked out after multiple failed login attempts

**Procedure**:

```
STEP 1: Understand Lock Reason
Accounts lock automatically after:
- 5 failed login attempts within 15 minutes
- Lockout duration: 15 minutes (auto-unlock)
- Or: Admin can manually unlock immediately

STEP 2: Locate Locked User
├─> Navigate to: /internal/admin/users
├─> Filter: Status = "Locked"
├─> Or search by email: user@lincoln.edu
├─> Click on user to view details

STEP 3: Review Lock Details
├─> View user security tab:
│   Status: 🔒 Locked
│   Locked at: 2024-01-15 10:23:45 UTC
│   Reason: Exceeded failed login attempts (5)
│   Failed attempts: 5
│   Last failed attempt: 10:23:43 UTC
│   Auto-unlock at: 10:38:45 UTC (15 min)
│
└─> Check for suspicious activity:
    - Multiple attempts from different IPs → Possible brute force
    - Same IP, short time → User forgot password
    - Pattern of attempts → Investigate further

STEP 4: Determine Action
├─> OPTION A: Wait for Auto-Unlock (15 minutes)
│   - If user can wait
│   - No suspicious activity detected
│   - User knows correct password
│   - Inform user: "Account will unlock at 10:38 AM"
│
├─> OPTION B: Manual Unlock (Immediate)
│   - User verified identity
│   - Urgent access needed
│   - No security concerns
│
└─> OPTION C: Unlock + Password Reset
    - User forgot password (likely cause of lock)
    - Combine unlock with password reset
    - More efficient than separate steps

STEP 5: Execute Unlock
For Option B (Manual Unlock):
├─> Click "Unlock Account"
├─> API: PATCH /api/v1/internal/users/{user_id}
│   Body: {
│     "locked": false,
│     "failed_login_attempts": 0,
│     "lockout_until": null
│   }
├─> User can log in immediately

For Option C (Unlock + Reset):
├─> Click "Unlock and Reset Password"
├─> This performs both actions:
│   1. Unlocks account
│   2. Sends password reset email
├─> User receives email with reset link
├─> User sets new password and logs in

STEP 6: Investigate if Suspicious
├─> If multiple locks in short period:
│   - Review login history (last 7 days)
│   - Check IP addresses
│   - Look for patterns
│
├─> If brute force suspected:
│   - Keep account locked
│   - Contact user directly (via phone if possible)
│   - Verify user identity before unlocking
│   - Force password reset
│   - Enable MFA (if available)
│   - Add note: "Potential brute force detected"
│
└─> If compromised:
    - Change password immediately
    - Invalidate all sessions
    - Notify organization admin
    - Review recent account activity for unauthorized access

STEP 7: Document and Notify
├─> Add note to user record:
│   "Account unlocked on 2024-01-15 by [admin_name].
│    Reason: User forgot password, 5 failed attempts.
│    Password reset sent."
│
├─> If via support ticket:
│   Update ticket: "Account unlocked. User can now log in."
│
└─> If security concern:
    Notify organization admin:
    "We detected suspicious login activity for [user].
     Account has been secured. Please contact the user."

STEP 8: Prevent Recurrence
├─> If user frequently locks account:
│   - Suggest password manager
│   - Provide password reset training
│   - Enable MFA (if available)
│
└─> If organization-wide issue:
    - Review authentication logs
    - Check for systemic problems
    - Consider adjusting lockout threshold

COMPLETION TIME: 5-10 minutes
ESCALATION: If suspected security breach, escalate to security team
```

---

### Bulk User Import

**When**: Organization needs to import many users at once (e.g., start of school year)

**Procedure**:

```
STEP 1: Prepare Import File
├─> Obtain user data from organization
├─> Format: CSV file
├─> Required columns:
│   email, first_name, last_name, role, grade_level (for students)
│
├─> Example CSV:
│   email,first_name,last_name,role,grade_level
│   teacher1@lincoln.edu,Jane,Doe,teacher,
│   teacher2@lincoln.edu,John,Smith,teacher,
│   student1@lincoln.edu,Mike,Johnson,student,11
│   student2@lincoln.edu,Sarah,Lee,student,11
│   ...
│
└─> Validation before import:
    - Valid email format
    - No duplicate emails
    - Role is valid: teacher | student | admin
    - Grade level for students only (9-12)
    - Within organization quotas

STEP 2: Review and Clean Data
├─> Common issues to fix:
│   - Invalid email formats (missing @, typos)
│   - Duplicate emails
│   - Mixed case (normalize to lowercase)
│   - Extra whitespace
│   - Missing required fields
│   - Invalid grades (0, 13, etc.)
│
├─> Use spreadsheet to clean:
│   - Remove duplicates
│   - Trim whitespace
│   - Validate email format
│   - Fill missing names with placeholders
│
└─> Create backup of original file

STEP 3: Perform Test Import (Dry Run)
├─> Navigate to: /internal/admin/users/bulk-import
├─> Select organization: Lincoln High School
├─> Upload CSV file
├─> Check: [x] Dry run (don't create users, just validate)
├─> Click "Import"
│
├─> System validates all rows:
│   ✓ Valid: 145 users
│   ⚠ Warnings: 3 users
│   ✗ Errors: 2 users
│
├─> Review errors:
│   Row 23: Invalid email format "student23@lincoln"
│   Row 45: Duplicate email "student10@lincoln.edu"
│
├─> Review warnings:
│   Row 12: Email domain doesn't match org (student12@gmail.com)
│   Row 34: Grade level missing for student
│   Row 67: Name has special characters (O'Brien - but valid)
│
└─> Fix errors in CSV, re-run dry run until clean

STEP 4: Execute Import
├─> Uncheck "Dry run"
├─> Choose import options:
│   [x] Send welcome emails to all users
│   [x] Skip users that already exist (don't overwrite)
│   [x] Create class assignments (if provided in CSV)
│
├─> Click "Import"
├─> API: POST /api/v1/internal/users/bulk-import
│   Content-Type: multipart/form-data
│
├─> System processes:
│   - Creating users... (1/145) ████░░░░░░ 5%
│   - Processing can take 1-2 minutes for large files
│   - Don't close browser during import

STEP 5: Review Import Results
├─> System displays results:
│   ┌────────────────────────────────────────────────────┐
│   │ Import Complete                                    │
│   │                                                    │
│   │ ✓ Successfully created: 143 users                  │
│   │ ⏭ Skipped (already exist): 2 users                 │
│   │ ✗ Failed: 0 users                                  │
│   │                                                    │
│   │ Breakdown by role:                                 │
│   │   Teachers: 12 created                             │
│   │   Students: 131 created                            │
│   │   Admins: 0 created                                │
│   │                                                    │
│   │ [Download Full Report] [View Created Users]        │
│   └────────────────────────────────────────────────────┘
│
├─> Download report:
│   File: import-report-2024-01-15.csv
│   Contains: Status for each row, user_id if created, errors if any

STEP 6: Verify Import
├─> Spot-check created users:
│   - Navigate to: /internal/admin/users
│   - Filter by: Organization = Lincoln, Created = Today
│   - Verify count: 143 users
│   - Check few random users:
│     ✓ Email correct
│     ✓ Role correct
│     ✓ Names correct
│     ✓ Grade level (for students)
│     ✓ Organization correct
│
├─> Check welcome emails sent:
│   - Review email send logs
│   - Verify no bounce backs
│   - If bounces: Fix email and resend
│
└─> Check organization quotas not exceeded:
    Current: 143 students (limit: 500) ✓
    Current: 12 teachers (limit: 50) ✓

STEP 7: Notify Organization Admin
├─> Send email to primary admin:
│   Subject: "User Import Complete"
│   Body:
│   """
│   Your bulk user import has been completed successfully.
│
│   Summary:
│   - 143 users created
│   - 12 teachers
│   - 131 students
│   - 2 users skipped (already existed)
│
│   All users have been sent welcome emails with login instructions.
│
│   Detailed report attached.
│   """
│
└─> Attach: import-report-2024-01-15.csv

STEP 8: Handle Issues
Common post-import issues:

Issue A: User didn't receive welcome email
├─> Check email deliverability:
│   - Email address correct?
│   - Not in spam folder?
│   - Email server accepting?
├─> Resend individual welcome email:
│   User → Actions → Resend Welcome Email

Issue B: User cannot log in
├─> Check user status: Active?
├─> Reset password
├─> Verify user knows to check email for credentials

Issue C: Wrong role assigned
├─> Edit user: Change role from student to teacher (or vice versa)
├─> Note: This doesn't affect already created classes

Issue D: User in wrong organization
├─> If imported to wrong org:
│   1. Delete from wrong org (or deactivate)
│   2. Create in correct org
│   3. Cannot transfer between orgs (security)

STEP 9: Document Import
├─> Add note to organization record:
│   "Bulk import completed on 2024-01-15:
│    - 143 users created (12 teachers, 131 students)
│    - Import file: lincoln-users-2024-01-15.csv
│    - Completed by: [admin_name]"
│
└─> Archive import file and report:
    Location: /imports/org_lincoln/2024-01-15/

COMPLETION TIME: 30-45 minutes (for 150 users)
BEST PRACTICES:
- Always do dry run first
- Import during off-hours (less server load)
- Keep backup of import file
- Test with small batch first if unsure
- Coordinate timing with organization (before school year starts)
```

---

## Subscription Management

### Upgrade Subscription Tier

**When**: Organization wants to upgrade from basic → standard or standard → premium

**Procedure**:

```
STEP 1: Verify Request and Payment
├─> Confirm with sales team:
│   - Upgrade authorized
│   - Payment processed
│   - New tier: premium
│   - Effective date: 2024-02-01
│
└─> Check contract:
    Current tier: standard
    New tier: premium
    Price difference: $X,XXX annually

STEP 2: Review Tier Differences
Premium tier includes:
├─> All standard features, plus:
│   ✓ Increased quotas:
│     * max_students: 500 → 1000
│     * max_teachers: 50 → 100
│   ✓ Priority support (24-hour response)
│   ✓ Advanced analytics dashboard
│   ✓ Custom branding (logo, colors)
│   ✓ API access (if applicable)
│   ✓ Dedicated account manager
│
└─> Features auto-enabled upon upgrade

STEP 3: Perform Upgrade
├─> Navigate to: /internal/admin/organizations/{org_id}
├─> Click: Subscription tab
├─> Click: "Upgrade Tier"
│
├─> Select new tier:
│   Current: Standard
│   New: ● Premium  ○ Enterprise (custom)
│
├─> Set effective date:
│   [2024-02-01] (can be immediate or future date)
│
├─> Review changes:
│   ┌────────────────────────────────────────────────────┐
│   │ Confirm Subscription Upgrade                       │
│   │                                                    │
│   │ Organization: Lincoln High School                  │
│   │ From: Standard → To: Premium                       │
│   │ Effective: 2024-02-01                              │
│   │                                                    │
│   │ Changes:                                           │
│   │ ✓ Max students: 500 → 1000                         │
│   │ ✓ Max teachers: 50 → 100                           │
│   │ ✓ Priority support enabled                         │
│   │ ✓ Advanced analytics enabled                       │
│   │ ✓ Custom branding enabled                          │
│   │                                                    │
│   │ [Cancel]              [Confirm Upgrade]            │
│   └────────────────────────────────────────────────────┘
│
├─> Click "Confirm Upgrade"
├─> API: PATCH /api/v1/internal/organizations/{org_id}
│   Body: {
│     "subscription_tier": "premium",
│     "tier_effective_date": "2024-02-01",
│     "max_students": 1000,
│     "max_teachers": 100
│   }

STEP 4: Enable Premium Features
System automatically:
├─> Updates organization settings
├─> Increases quotas
├─> Enables premium features in UI for org admins
├─> Grants access to advanced analytics
├─> Adds "Priority Support" badge to support tickets
│
└─> Manual steps (if needed):
    - Configure custom branding (separate workflow)
    - Assign dedicated account manager
    - Set up API keys (if requested)

STEP 5: Verify Upgrade
├─> Log in as org admin to verify:
│   - Navigate to admin dashboard
│   - Check: "Premium" badge visible
│   - Check: Advanced analytics accessible
│   - Check: Quotas updated (Settings → Quotas)
│
├─> Test a premium feature:
│   - Access advanced analytics
│   - Verify additional data/charts visible
│
└─> Check billing:
    - Pro-rated charge calculated correctly
    - Invoice generated for difference
    - Payment processed

STEP 6: Notify Organization
├─> Send email to primary admin:
│   Subject: "Subscription Upgraded to Premium"
│   Body:
│   """
│   Congratulations! Your Vividly subscription has been upgraded to Premium.
│
│   Effective: February 1, 2024
│
│   New features now available:
│   • Increased capacity: 1000 students, 100 teachers
│   • Priority support (24-hour response time)
│   • Advanced analytics dashboard
│   • Custom branding
│   • Dedicated account manager: [Name]
│
│   To get started with premium features:
│   1. Log in to your admin dashboard
│   2. Visit Settings → Premium Features
│   3. Configure custom branding (optional)
│
│   Questions? Contact your account manager: [email]
│   """
│
└─> CC: Sales rep, account manager

STEP 7: Document Upgrade
├─> Update organization notes:
│   "Upgraded from standard to premium on 2024-02-01.
│    Reason: Organization growth.
│    Sales rep: [name]
│    Invoice: INV-2024-0215"
│
├─> Update CRM/billing system:
│   - New MRR/ARR
│   - Contract value
│   - Renewal date

STEP 8: Follow-Up
├─> Day 7: Check premium feature usage
│   - Has org accessed advanced analytics?
│   - Have they configured custom branding?
│   - Any support questions?
│
├─> Day 30: Account manager check-in
│   - Is organization satisfied?
│   - Any training needed?
│   - Collecting feedback on premium features
│
└─> Add to renewal calendar:
    - Note: Premium tier renewal in [X] months
    - Prepare upgrade retention strategy

COMPLETION TIME: 15-20 minutes
FOLLOW-UP: Account manager check-in at 7 and 30 days
```

---

### Adjust Quotas

**When**: Organization needs more students/teachers without upgrading tier

**Procedure**:

```
STEP 1: Evaluate Request
├─> Request details:
│   Organization: Lincoln High School
│   Current tier: Standard (max 500 students)
│   Current usage: 487 students (97% full)
│   Request: Increase to 600 students
│   Reason: Enrollment growth mid-year
│
├─> Check if tier upgrade better option:
│   Standard max: 500 students
│   Premium max: 1000 students
│
│   If request > tier max:
│   → Suggest tier upgrade instead
│
│   If request < tier max:
│   → Allow à la carte quota increase
│
└─> Verify payment for additional quota:
    Additional 100 students @ $X per student = $X,XXX
    Payment authorized: Yes

STEP 2: Calculate Pricing
├─> À la carte pricing (example):
│   Base tier: $5,000/year for 500 students
│   Additional: $10/student/year
│   100 additional students: $1,000/year
│   Pro-rated for remainder of contract: $X
│
├─> Confirm with sales:
│   - Price approved
│   - Contract amended
│   - Payment terms
│
└─> Generate invoice or quote if needed

STEP 3: Update Quotas
├─> Navigate to: /internal/admin/organizations/{org_id}/quotas
├─> Current quotas:
│   max_students: 500
│   max_teachers: 50
│   max_admins: 5
│
├─> Update quotas:
│   max_students: 500 → 600
│   Reason: Enrollment growth
│   Effective: Immediate
│
├─> Click "Save Changes"
├─> API: PATCH /api/v1/internal/organizations/{org_id}
│   Body: {
│     "max_students": 600,
│     "quota_updated_at": "2024-03-15T10:00:00Z",
│     "quota_update_reason": "Enrollment growth mid-year"
│   }

STEP 4: Verify Update
├─> Refresh organization page
├─> Check quotas:
│   Current students: 487
│   Max students: 600
│   Utilization: 81% (green)
│
├─> Test: Can admin now invite more students?
│   - Log in as org admin
│   - Navigate to: Invite Students
│   - System should allow up to 600 total
│   - Try inviting 1 student → Should succeed
│
└─> Check billing:
    - New quota reflected in billing system
    - Invoice generated for additional amount

STEP 5: Notify Organization
├─> Send email to primary admin:
│   Subject: "Student Quota Increased"
│   Body:
│   """
│   Your student quota has been increased.
│
│   Previous limit: 500 students
│   New limit: 600 students
│   Current enrollment: 487 students
│
│   You can now invite up to 113 additional students.
│
│   This change is effective immediately.
│   """
│
└─> Include: Updated invoice/quote if applicable

STEP 6: Document Change
├─> Add note to organization record:
│   "Increased student quota from 500 to 600 on 2024-03-15.
│    Reason: Mid-year enrollment growth.
│    Additional cost: $1,000 (prorated to $650 for remainder of year).
│    Approved by: [sales rep name]"
│
└─> Update contract:
    - Amend contract with new quota
    - File amended agreement
    - Update contract value in CRM

COMPLETION TIME: 10 minutes
```

---

### Handle Quota Exceeded

**When**: Organization reaches quota limit and cannot add more users

**Procedure**:

```
STEP 1: Detect Quota Issue
Quota exceeded detected when:
├─> Admin attempts to invite students:
│   Current: 500 students
│   Max: 500
│   Error: "Student quota reached"
│
├─> Or proactive monitoring:
│   Alert: "org_lincoln approaching student quota (495/500)"
│
└─> Or admin contacts support:
    "I can't invite any more students"

STEP 2: Assess Situation
├─> Check current usage:
│   API: GET /api/v1/internal/organizations/{org_id}/usage
│
│   Response:
│   {
│     "students": {
│       "current": 500,
│       "max": 500,
│       "utilization": 100%
│     },
│     "teachers": {
│       "current": 42,
│       "max": 50,
│       "utilization": 84%
│     }
│   }
│
├─> Check for inactive users:
│   - Students not logged in for 30+ days
│   - Students with pending invitations (expired)
│   - Graduated students (if applicable)
│
└─> Options:
    A. Clean up inactive users (free capacity)
    B. Increase quota (requires payment)
    C. Upgrade tier (if near tier max)

STEP 3: Option A - Clean Up Inactive Users
├─> Navigate to: /internal/admin/organizations/{org_id}/users
├─> Filter: Status = "Inactive" OR Last Login > 30 days ago
│
├─> Review inactive users:
│   Found: 23 students inactive for 30+ days
│
│   - 8 never logged in (pending invitations)
│   - 15 no activity in 30+ days
│
├─> Decide which to deactivate:
│   - Students who never logged in → Safe to deactivate
│   - Students inactive 30+ days → Contact org admin first
│
├─> Contact org admin:
│   "We noticed you're at capacity (500/500 students).
│    We found 23 students with no recent activity.
│    Would you like to deactivate them to free up space?
│    List: [attached]"
│
├─> If admin approves:
│   - Bulk deactivate users
│   - This frees: 23 slots
│   - New capacity: 477/500
│   - Org can now invite 23 more students
│
└─> If admin declines:
    Proceed to Option B or C

STEP 4: Option B - Increase Quota
├─> Contact sales to authorize quota increase
├─> Follow "Adjust Quotas" workflow above
├─> Typical increase: 100-200 students at a time
├─> Communicate cost to org admin
├─> Wait for payment approval
├─> Execute quota increase once approved

STEP 5: Option C - Upgrade Tier
├─> If current tier: Standard (max 500)
├─> Suggest: Premium (max 1000)
├─> Benefits beyond quota:
│   - Priority support
│   - Advanced analytics
│   - Better value if need significant capacity
│
├─> Contact sales for upgrade quote
├─> Present options to org admin
├─> Follow "Upgrade Subscription Tier" workflow if approved

STEP 6: Temporary Workaround (If Urgent)
├─> If org needs immediate access (e.g., new students arriving):
│   And payment approval pending
│
├─> Temporary quota increase:
│   - Increase quota by small amount (e.g., 10-20)
│   - Set reminder to revert if payment not approved
│   - Document as "temporary increase, pending payment"
│   - Duration: 7 days
│
├─> API: PATCH /api/v1/internal/organizations/{org_id}
│   Body: {
│     "max_students": 520,
│     "quota_temporary": true,
│     "quota_revert_at": "2024-03-22T00:00:00Z"
│   }
│
└─> Notify org admin:
    "We've temporarily increased your quota to 520 students
     for 7 days while we process your quota increase request.
     Please approve the payment by [date] to make this permanent."

STEP 7: Prevent Future Issues
├─> Set up proactive alerts:
│   - Alert at 80% capacity
│   - Alert at 90% capacity
│   - Alert at 95% capacity
│
├─> Educate org admin:
│   - Monitor usage regularly
│   - Plan for growth in advance
│   - Clean up inactive users periodically
│
└─> Quarterly reviews:
    - Review all orgs at >80% capacity
    - Proactively reach out with options
    - Prevent emergency quota issues

COMPLETION TIME: Varies (15 min for cleanup, 30+ min for increase)
PRIORITY: High (blocks org from adding users)
```

---

## Content Management

### Review Flagged Content

**When**: Content is flagged as potentially inappropriate by AI safety filters or user reports

**Procedure**:

```
STEP 1: Identify Flagged Content
Flagged content sources:
├─> Automatic AI safety filter:
│   - During generation: Output filter triggered
│   - After generation: Post-generation review
│   - User input filter: Query contained flagged terms
│
├─> User report:
│   - Student/teacher flagged video as inappropriate
│   - Form submitted with reason
│
└─> Proactive monitoring:
    - Daily review of edge cases
    - Quarterly audit of all content

STEP 2: Access Flagged Content Queue
├─> Navigate to: /internal/admin/content/flagged
├─> View flagged content list:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Flagged Content Review Queue                    Priority: High│
│   │                                                              │
│   │ Content ID        Topic            Flag Reason      Status  │
│   │ ───────────────────────────────────────────────────────────  │
│   │ content_abc123    Newton's 3rd     User Report      🔴 New   │
│   │ content_xyz789    Cell Division    Safety Filter   🔴 New   │
│   │ content_def456    Algorithms       Safety Filter   🟡 Review│
│   │ ...                                                          │
│   └──────────────────────────────────────────────────────────────┘
│
└─> Sort by: Priority, Date, Flag Type

STEP 3: Review Individual Content
├─> Click on flagged content to open review panel
├─> Content details:
│   Content ID: content_abc123
│   Topic: Newton's Third Law
│   Student: John Doe (student_john)
│   Organization: Lincoln High School
│   Created: 2024-01-15 10:23:45
│
│   Flag details:
│   Flagged by: User report (sarah.lee@lincoln.edu)
│   Flag reason: "Contains inappropriate example"
│   Flag date: 2024-01-15 14:30:00
│   Priority: High (user report)
│
├─> View content:
│   [▶ Play Video] (opens video player in review mode)
│   [📝 View Transcript]
│   [🔍 View Generation Logs]
│
├─> Review components:
│   1. Student's original query
│   2. Generated script
│   3. Video output
│   4. Interest personalization used
│
└─> Assessment criteria:
    - Is content age-appropriate? (high school students)
    - Are examples suitable?
    - Does it align with educational standards?
    - Any safety concerns?
    - Any offensive language/imagery?

STEP 4: Make Decision
Decision options:

OPTION A: Approve (No Issue Found)
├─> Content is appropriate
├─> False positive from safety filter
├─> Or user report was incorrect
├─> Action:
│   - Mark as "Reviewed - Approved"
│   - Content remains accessible
│   - Update filter to reduce false positives

OPTION B: Approve with Warning
├─> Content is borderline but acceptable
├─> Add warning label for students/teachers
├─> Action:
│   - Mark as "Reviewed - Approved with Warning"
│   - Add disclaimer: "This content includes [mature themes/
│     complex topics]. Teacher guidance recommended."
│   - Notify organization admin

OPTION C: Remove Content
├─> Content is inappropriate
├─> Violates content policy
├─> Action:
│   - Mark as "Reviewed - Removed"
│   - Delete video file from storage
│   - Set content status to "deleted"
│   - Notify student and teacher
│   - Investigate why safety filter didn't catch during generation

OPTION D: Regenerate Content
├─> Content has minor issues that can be fixed
├─> Example: One inappropriate phrase in script
├─> Action:
│   - Trigger regeneration with stricter filters
│   - Remove original content
│   - Notify student when new version ready

STEP 5: Execute Decision
For Option C (Remove Content):
├─> Click "Remove Content"
├─> Confirm removal:
│   ┌────────────────────────────────────────────────────┐
│   │ Remove Inappropriate Content                       │
│   │                                                    │
│   │ This will:                                         │
│   │ • Delete video file from storage                   │
│   │ • Remove from student's history                    │
│   │ • Mark content as deleted in database              │
│   │ • Notify student and teacher                       │
│   │                                                    │
│   │ Removal reason (required):                         │
│   │ [Inappropriate example used (non-educational)]     │
│   │                                                    │
│   │ [Cancel]              [Confirm Removal]            │
│   └────────────────────────────────────────────────────┘
│
├─> Click "Confirm Removal"
├─> API: DELETE /api/v1/internal/content/{content_id}
│   Body: {
│     "reason": "Inappropriate example used",
│     "reviewer": "admin_jane",
│     "action": "remove"
│   }
│
└─> System executes:
    - Delete video from GCS bucket
    - Update content record: status = "deleted"
    - Update learning_history: mark as removed
    - Send notifications

STEP 6: Notify Stakeholders
├─> Notify student:
│   Subject: "Content Removed - Vividly"
│   Body:
│   """
│   A video you requested has been removed as it didn't meet
│   our content guidelines.
│
│   Topic: Newton's Third Law
│   Removed: 2024-01-15
│
│   You can request a new video on this topic at any time.
│   This doesn't affect your account standing.
│   """
│
├─> Notify teacher:
│   Subject: "Student Content Flagged and Removed"
│   Body:
│   """
│   Content from one of your students was flagged and removed:
│
│   Student: John Doe
│   Topic: Newton's Third Law
│   Reason: Inappropriate example used
│
│   The student has been notified. This is handled automatically
│   and requires no action from you.
│   """
│
└─> Notify organization admin (if serious violation):
    Include details and any patterns observed

STEP 7: Document Review
├─> Add detailed note to content record:
│   "Content flagged by user report on 2024-01-15.
│    Reviewed by admin_jane on 2024-01-15.
│    Decision: Removed - Inappropriate example.
│    Details: [specific issue found]
│    Notifications sent to student and teacher."
│
├─> Update content moderation log:
│   - Content ID
│   - Flag source (user report / auto filter)
│   - Reviewer
│   - Decision
│   - Reason
│   - Actions taken
│
└─> Aggregate statistics:
    - Total flagged: 23 this month
    - Approved: 15 (65%)
    - Removed: 8 (35%)
    - False positive rate: 65%

STEP 8: Improve Filters (If Needed)
├─> If false positive (approved content):
│   - Review why filter triggered
│   - Adjust filter sensitivity
│   - Update flagged terms list
│   - Test with similar content
│
├─> If filter missed inappropriate content:
│   - Analyze what slipped through
│   - Add to flagged terms/patterns
│   - Increase filter strictness
│   - Regenerate similar content for review
│
└─> Monitor impact:
    - False positive rate
    - Miss rate
    - User satisfaction
    - Educational quality

STEP 9: Escalate If Needed
Escalate to senior leadership if:
├─> Severe policy violation:
│   - Illegal content
│   - Hate speech
│   - Violence
│
├─> Systematic issue:
│   - Multiple flags from same org
│   - Pattern of inappropriate requests
│   - Filter consistently failing
│
└─> Legal concern:
    - FERPA/COPPA violation
    - Copyright issue
    - Privacy breach

COMPLETION TIME: 5-15 minutes per piece of content
PRIORITY: Review within 24 hours of flag (user reports within 2 hours)
FOLLOW-UP: Monthly review of flagged content trends
```

---

### Delete Inappropriate Content

*See "Review Flagged Content" above - deletion is Option C in that workflow*

---

### Clear Cache for Topic

**When**: Topic content updated in source (OpenStax) and cached content is outdated

**Procedure**:

```
STEP 1: Identify Need to Clear Cache
Reasons to clear cache:
├─> Source content updated:
│   - OpenStax textbook revised
│   - Topic information corrected
│   - New examples added to OER
│
├─> Systematic issue with topic:
│   - Generated videos consistently low quality
│   - Outdated information being used
│   - Safety filter issues
│
└─> Request from organization:
    - Teacher reports inaccurate content
    - Multiple students see same error

STEP 2: Locate Cached Content
├─> Navigate to: /internal/admin/content/cache
├─> Search by:
│   - Topic ID: topic_phys_mech_newton_3
│   - Or Topic Name: "Newton's Third Law"
│
├─> View cached content:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Cached Content: Newton's Third Law                           │
│   │                                                              │
│   │ Topic ID: topic_phys_mech_newton_3                           │
│   │ Total cached videos: 47                                      │
│   │ Oldest: 2024-01-01 (14 days ago)                             │
│   │ Newest: 2024-01-15 (today)                                   │
│   │ Cache hit rate: 18% (target: 15%)                            │
│   │                                                              │
│   │ Breakdown by interest:                                       │
│   │ • Basketball: 12 videos                                      │
│   │ • Video Games: 10 videos                                     │
│   │ • Music: 8 videos                                            │
│   │ • No interest (general): 17 videos                           │
│   │                                                              │
│   │ [Clear All Cache] [Clear by Interest] [Clear Old (30d+)]    │
│   └──────────────────────────────────────────────────────────────┘

STEP 3: Determine Clear Strategy
Options:

OPTION A: Clear All Cache for Topic
├─> Use when: Source content significantly updated
├─> Effect: All 47 videos deleted and regenerated on next request
├─> Impact: Temporary cache miss rate increase

OPTION B: Clear by Interest
├─> Use when: Issue specific to one personalization
├─> Example: Basketball examples have errors
├─> Effect: Only Basketball videos (12) deleted
├─> Impact: Minimal, other interests unaffected

OPTION C: Clear Old Cache
├─> Use when: Want to gradually refresh without disruption
├─> Clear: Videos older than 30 days
├─> Effect: Slowly rotate out old content
├─> Impact: Minimal immediate effect

OPTION D: Manual Selection
├─> Use when: Need to clear specific videos
├─> Example: One particular personalization has issue
├─> Effect: Surgical cache clearing
├─> Impact: Minimal

STEP 4: Execute Cache Clear
For Option A (Clear All):
├─> Click "Clear All Cache"
├─> Confirm action:
│   ┌────────────────────────────────────────────────────┐
│   │ Clear All Cached Content                           │
│   │                                                    │
│   │ Topic: Newton's Third Law                          │
│   │ Videos to delete: 47                               │
│   │                                                    │
│   │ This will:                                         │
│   │ • Delete 47 videos from storage                    │
│   │ • Remove cache records from database               │
│   │ • Preserve learning history (students can still    │
│   │   see they watched these topics)                   │
│   │ • Videos will be regenerated on next request       │
│   │                                                    │
│   │ Estimated storage freed: 3.2 GB                    │
│   │                                                    │
│   │ Reason (required):                                 │
│   │ [Source content updated (OpenStax revision)]       │
│   │                                                    │
│   │ [Cancel]              [Clear Cache]                │
│   └────────────────────────────────────────────────────┘
│
├─> Click "Clear Cache"
├─> API: DELETE /api/v1/internal/content/cache
│   Query params: topic_id=topic_phys_mech_newton_3
│   Body: {
│     "clear_all": true,
│     "reason": "Source content updated",
│     "cleared_by": "admin_jane"
│   }
│
└─> System executes:
    - Delete video files from GCS
    - Remove cache records
    - Update topic metadata: last_cache_clear = NOW()
    - Log cache clear event

STEP 5: Verify Cache Cleared
├─> Refresh cache page
├─> Verify:
│   ✓ Cached videos: 0 (was 47)
│   ✓ Topic status: Active
│   ✓ Students can still request content
│   ✓ Storage freed: 3.2 GB
│
└─> Check first new request:
    - Student requests Newton's 3rd Law
    - Cache miss (as expected)
    - Generation succeeds
    - New video created with updated content
    - Cache begins rebuilding

STEP 6: Monitor Regeneration
├─> Over next 7-30 days:
│   - Cache gradually rebuilds as students request content
│   - Monitor generation quality
│   - Verify updated information being used
│
├─> Check metrics:
│   - Cache hit rate temporarily drops (normal)
│   - Should return to ~15% within 30 days
│   - Generation time slightly higher (cache misses)
│
└─> Alert if issues:
    - Generation failures increase
    - Quality problems persist
    - Cache not rebuilding as expected

STEP 7: Document Cache Clear
├─> Add note to topic record:
│   "Cache cleared on 2024-01-15 by admin_jane.
│    Reason: Source content updated (OpenStax revision 2024-01).
│    47 videos deleted (3.2 GB freed).
│    Cache rebuilding normally."
│
├─> Update change log:
│   Topic: Newton's Third Law
│   Action: Cache clear
│   Date: 2024-01-15
│   By: admin_jane
│   Impact: 47 cached videos removed
│
└─> Notify if needed:
    - If org-wide cache clear: Notify affected orgs
    - If impacting production: Notify SRE team
    - Generally: No user notification needed (transparent)

STEP 8: Proactive Cache Management
Set up regular cache maintenance:
├─> Automated monthly clearing:
│   - Clear cache for content 60+ days old
│   - Keep cache fresh
│   - Gradually rotate content
│
├─> Monitor source updates:
│   - Subscribe to OpenStax update notifications
│   - When textbook updated: Clear affected topics
│   - Proactive vs reactive
│
└─> Quarterly audit:
    - Review cache hit rates by topic
    - Identify topics with low quality
    - Clear and regenerate proactively

COMPLETION TIME: 10-15 minutes
IMPACT: Low (transparent to users, temporary cache miss increase)
FREQUENCY: As needed (typically monthly for aging content, immediately for updates)
```

---

## Troubleshooting

### Investigate User Cannot Log In

**Procedure**: See "Handle Locked Account" above for locked accounts.

For other login issues:

```
STEP 1: Gather Information
From user or support ticket:
├─> Email address
├─> Error message (if any)
├─> Browser and device
├─> When did issue start?
├─> Can they log in from different device?

STEP 2: Verify Account Status
├─> Navigate to: /internal/admin/users
├─> Search: user@lincoln.edu
├─> Check account:
│   - Status: Active? Locked? Suspended?
│   - Organization: Active?
│   - Email verified: Yes?
│   - Last login: When?

STEP 3: Check Common Issues
Issue A: Wrong password
├─> Most common cause
├─> Failed login attempts visible in logs
├─> Solution: Reset password

Issue B: Account locked
├─> After 5 failed attempts
├─> Solution: Unlock account (see workflow above)

Issue C: Organization suspended
├─> Entire org blocked
├─> Solution: Reactivate org or contact billing

Issue D: Browser/cookie issue
├─> Old cached credentials
├─> Solution: Clear browser cache, try incognito mode

Issue E: Email typo
├─> User entering wrong email
├─> Solution: Verify correct email, provide to user

Issue F: Account doesn't exist
├─> User never completed registration
├─> Or: Invitation expired
├─> Solution: Resend invitation

STEP 4: Resolve and Verify
├─> Apply appropriate solution
├─> Test: Can user now log in?
├─> Document in support ticket
└─> Follow up if issue persists

COMPLETION TIME: 5-10 minutes
```

---

### Debug Video Generation Failure

**When**: Student reports video generation failed or stuck

**Procedure**:

```
STEP 1: Locate Failed Request
├─> Obtain from user:
│   - Request ID (if they have it)
│   - Or: Student email + approximate time
│   - Topic requested
│
├─> Navigate to: /internal/admin/content/requests
├─> Search:
│   - Request ID: req_abc123
│   - Or: student_id + date range
│
└─> Filter: Status = "failed" or "stuck"

STEP 2: View Request Details
├─> Click on request to view full details:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Content Request: req_abc123                                  │
│   │                                                              │
│   │ Status: ❌ Failed                                            │
│   │ Student: John Doe (john.doe@lincoln.edu)                     │
│   │ Topic: Newton's Third Law                                    │
│   │ Interest: Basketball                                         │
│   │ Query: "Why does the ball bounce back?"                      │
│   │                                                              │
│   │ Timeline:                                                    │
│   │ ✓ Requested: 2024-01-15 10:23:45                             │
│   │ ✓ Validating: 10:23:46 (1s)                                  │
│   │ ✓ RAG Context Retrieval: 10:23:48 (2s)                       │
│   │ ✓ Script Generation: 10:23:56 (8s)                           │
│   │ ❌ Audio Generation: Failed at 10:24:15 (19s)                │
│   │                                                              │
│   │ Error: TTS API timeout (504 Gateway Timeout)                 │
│   │ Error details: External TTS service did not respond          │
│   │                                                              │
│   │ [View Full Logs] [Retry Generation] [Cancel Request]        │
│   └──────────────────────────────────────────────────────────────┘

STEP 3: Analyze Error
Common failure reasons:

ERROR TYPE A: External API Timeout (TTS, Video Gen)
├─> Symptom: "504 Gateway Timeout" or "Service unavailable"
├─> Cause: Third-party service (Nano Banana, Google TTS) down
├─> Check: /internal/admin/system/integrations
│   - TTS service: ❌ Down (last success: 10:15, 3 attempts failed)
│   - Video Gen: ✓ Up
├─> Solution:
│   - Wait for service recovery (usually 5-30 min)
│   - Or: Retry manually once service back up
│   - Or: Switch to backup provider if available

ERROR TYPE B: Safety Filter Triggered
├─> Symptom: "Content policy violation"
├─> Cause: Generated script or user query flagged
├─> Check: View flagged content in logs
│   Query: "Why does the ball bounce back?" ✓ Safe
│   Generated script: [Contains flagged phrase: "explosive reaction"]
├─> Solution:
│   - Retry with stricter filter
│   - Or: Manually adjust generation parameters
│   - Or: Different personalization might avoid trigger

ERROR TYPE C: Rate Limit (External API)
├─> Symptom: "429 Too Many Requests"
├─> Cause: Exceeded quota for Vertex AI or other service
├─> Check: API usage dashboard in GCP Console
│   Vertex AI quota: 980/1000 requests today (98% used)
├─> Solution:
│   - Wait for quota reset (usually daily)
│   - Or: Request quota increase from GCP
│   - Or: Implement request queue to spread load

ERROR TYPE D: Invalid Context Retrieved
├─> Symptom: "Insufficient context for generation"
├─> Cause: RAG query returned no/poor results
├─> Check: View retrieved context in logs
│   Retrieved: 0 relevant chunks (should be 5-10)
├─> Solution:
│   - Check vector database connectivity
│   - Verify topic embedding exists
│   - Regenerate topic embeddings if needed
│   - May indicate vector DB issue

ERROR TYPE E: Timeout (Overall)
├─> Symptom: "Request timeout" after 30+ seconds
├─> Cause: One stage took too long (usually video generation)
├─> Check: Timeline shows which stage stuck
│   Video Generation: 10:24:00 - timeout at 10:24:45 (45s, limit 40s)
├─> Solution:
│   - Retry (may succeed on second attempt)
│   - Check video generation service health
│   - May need to increase timeout limit if persistent

ERROR TYPE F: Database Error
├─> Symptom: "Database connection failed" or "Transaction failed"
├─> Cause: Cloud SQL connectivity issue
├─> Check: Database health dashboard
│   Cloud SQL: ⚠ High CPU (95%)
├─> Solution:
│   - Wait for CPU to stabilize
│   - Check for long-running queries
│   - May need to scale up database instance

STEP 4: Apply Solution
For TTS API Timeout (Error Type A):
├─> Check service status:
│   Navigate to: /internal/admin/system/integrations
│   TTS Service: ✓ Back up (recovered at 10:30)
│
├─> Retry request:
│   Click "Retry Generation"
│   API: POST /api/v1/internal/content/requests/{request_id}/retry
│
│   System will:
│   - Resume from failed stage (Audio Generation)
│   - Reuse already generated script (don't regenerate)
│   - Attempt audio generation again
│   - Continue with video generation if successful
│
└─> Monitor retry:
    Status updates in real-time
    ✓ Audio Generation: Success (10:31, 8s)
    ✓ Video Generation: Success (10:32, 35s)
    ✓ Complete: content_xyz789 created

STEP 5: Verify Resolution
├─> Request status: ✓ Completed
├─> Content ID: content_xyz789
├─> Preview video: [▶ Play]
│   - Quality check: Good
│   - Audio sync: Good
│   - Content accurate: Yes
│
├─> Student view:
│   - Student can now access video
│   - No error message visible
│   - Video plays correctly
│
└─> Notify student:
    "Your requested video is now ready!"

STEP 6: Document Issue
├─> Add note to request:
│   "Generation failed at audio stage due to TTS API timeout.
│    Service recovered and request retried successfully at 10:31.
│    Final content: content_xyz789.
│    Total time: 8 minutes (including failure + retry)."
│
├─> Update incident log if systemic:
│   "TTS API outage from 10:15-10:30 on 2024-01-15.
│    Impact: 12 failed requests.
│    All retried successfully after service recovery."
│
└─> If recurring issue:
    - File bug report
    - Contact third-party provider
    - Consider SLA review

STEP 7: Proactive Monitoring
├─> Set up alerts for:
│   - High failure rate (>5% in 1 hour)
│   - Specific service unavailability
│   - Slow generation times (>15s average)
│
├─> Regular health checks:
│   - Every 5 minutes: Ping external services
│   - Every hour: Test end-to-end generation
│   - Daily: Review failure logs
│
└─> Automated retries:
    - System auto-retries failed requests after 5 minutes
    - Up to 3 attempts
    - Exponential backoff: 5min, 15min, 30min
    - Reduces manual intervention

COMPLETION TIME: 10-20 minutes (depending on issue)
PRIORITY: High (user-facing issue)
ESCALATION: If service down >30 min, escalate to on-call engineer
```

---

### Handle High Error Rate

**When**: System alert triggered for elevated error rate

**Procedure**:

```
STEP 1: Receive Alert
Alert example:
├─> Email/Slack notification:
│   Subject: "🚨 HIGH ERROR RATE ALERT"
│   Body:
│   """
│   Environment: Production
│   Error Rate: 12.5% (threshold: 5%)
│   Time window: Last 15 minutes
│   Affected requests: 47 of 376
│
│   Top errors:
│   1. 503 Service Unavailable (28 occurrences)
│   2. 504 Gateway Timeout (12 occurrences)
│   3. 500 Internal Server Error (7 occurrences)
│
│   Dashboard: https://monitoring.vividly.edu/errors
│   """
│
└─> Acknowledge alert to start investigation

STEP 2: Assess Impact
├─> Navigate to: /internal/admin/system/errors
├─> View error dashboard:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Error Rate Dashboard                                         │
│   │                                                              │
│   │ Current Error Rate: 12.5% 🔴 (Target: <1%, Alert: >5%)      │
│   │                                                              │
│   │ Timeline (Last 1 Hour):                                      │
│   │ 15% │                                     ●●●                │
│   │ 10% │                               ●●●                      │
│   │  5% │ ─────────────────────────────────── Alert Threshold   │
│   │  1% │ ─────────────────────────────────── Target            │
│   │  0% │ ●●●●●●●●●●●●●●●●●                                     │
│   │     10:00   10:15   10:30   10:45 ← Spike started           │
│   │                                                              │
│   │ Error Breakdown (Last 15 min):                               │
│   │ • 503 Service Unavailable: 28 (59%)                          │
│   │ • 504 Gateway Timeout: 12 (26%)                              │
│   │ • 500 Internal Server Error: 7 (15%)                         │
│   │                                                              │
│   │ Affected Endpoints:                                          │
│   │ • POST /api/v1/students/content/request: 35 errors           │
│   │ • GET /api/v1/students/content/{id}: 8 errors                │
│   │ • GET /api/v1/teacher/dashboard: 4 errors                    │
│   │                                                              │
│   │ Affected Organizations:                                      │
│   │ • All organizations (not isolated to one)                    │
│   │                                                              │
│   └──────────────────────────────────────────────────────────────┘

STEP 3: Identify Root Cause
Common causes:

CAUSE A: External Service Outage
├─> Check: /internal/admin/system/integrations
│   Vertex AI: ✓ Up
│   Nano Banana (Video Gen): ❌ Down (503 errors)
│   Google TTS: ✓ Up
│   Cloud SQL: ✓ Up
│
├─> Diagnosis: Nano Banana API experiencing outage
├─> Impact: All video generation requests failing
├─> Affected: 35 content requests in queue
│
└─> Verify: Check Nano Banana status page
    https://status.nanobanana.com
    Status: Major Outage - Investigating
    ETA: 30 minutes

CAUSE B: Database Performance
├─> Check: Cloud SQL metrics in GCP Console
│   CPU: 98% (very high)
│   Connections: 195/200 (near limit)
│   Queries: 5,000/sec (3x normal)
│
├─> Diagnosis: Database under heavy load
├─> Impact: All API endpoints slow/timing out
│
└─> Investigate:
    - Slow query log: Check for inefficient queries
    - Connection pool: Check for connection leaks
    - Traffic spike: Unusual activity?

CAUSE C: Memory/Resource Exhaustion
├─> Check: Cloud Run service metrics
│   API Gateway instances: 10/10 (max capacity)
│   Memory usage: 95% per instance
│   CPU: 85% per instance
│
├─> Diagnosis: Traffic spike overwhelming service
├─> Impact: Requests queued, timeouts occurring
│
└─> Scale:
    Increase max instances: 10 → 20
    Auto-scaling will spin up new instances

CAUSE D: Code Deployment Issue
├─> Check: Recent deployments
│   Last deploy: 10:35 (5 minutes ago)
│   Error spike: Started at 10:37
│   Correlation: Likely related
│
├─> Diagnosis: New deployment introduced bug
├─> Impact: Specific code path failing
│
└─> Rollback:
    Revert to previous stable version
    Investigate bug in dev environment

CAUSE E: DDoS or Abuse
├─> Check: Traffic patterns
│   Requests from single IP: 500/min (very high)
│   Normal: 5-10/min per IP
│
├─> Diagnosis: Possible DDoS or abuse
├─> Impact: Legitimate requests crowded out
│
└─> Mitigate:
    Rate limit aggressive IPs
    Enable Cloud Armor (WAF)
    Block abusive IPs

STEP 4: Apply Immediate Mitigation
For External Service Outage (Cause A):
├─> MITIGATION PLAN:
│   1. Acknowledge: Nano Banana API down
│   2. Queue: Hold content requests until service recovers
│   3. Communicate: Notify users of temporary delay
│   4. Fallback: No immediate fallback for video generation
│
├─> Execute:
│   - Enable maintenance mode for video generation:
│     POST /api/v1/internal/system/maintenance
│     Body: {"service": "video_generation", "enabled": true}
│
│   - This will:
│     * Accept content requests (don't reject)
│     * Queue them for processing when service recovers
│     * Show status: "Video generation delayed. Your request is queued."
│     * Prevents error messages to users
│
│   - Update status page:
│     https://status.vividly.edu
│     "Video generation temporarily delayed due to third-party service issue.
│      All requests will be processed once service recovers (ETA: 30 min)."
│
└─> Monitor:
    - Watch Nano Banana status page
    - Check queue length every 5 minutes
    - When service recovers: Disable maintenance mode
    - Process queued requests

STEP 5: Monitor Recovery
├─> Watch error rate dashboard:
│   15:00: Error rate: 12.5%
│   15:05: Error rate: 10.2% (decreasing)
│   15:10: Error rate: 4.8% (below alert threshold)
│   15:15: Error rate: 1.2% (normal)
│
├─> Verify service recovery:
│   Nano Banana: ✓ Back up at 15:12
│   Queue processing: 35 requests being processed
│   New requests: Succeeding normally
│
└─> All clear:
    15:20: Error rate: 0.5% (normal)
    Queued requests: All processed (0 remaining)
    Incident resolved

STEP 6: Communicate Status
During incident:
├─> Update status page (every 15 min):
│   15:00: "Investigating video generation delays"
│   15:15: "Issue identified. Third-party service recovering."
│   15:30: "Issue resolved. All systems operational."
│
├─> If prolonged (>1 hour):
│   - Email all organization admins
│   - Explain impact and ETA
│   - Provide workarounds if any
│
└─> After resolution:
    Post-incident summary on status page

STEP 7: Document Incident
├─> Create incident report:
│   Incident ID: INC-2024-0115-001
│   Title: "High Error Rate - Nano Banana API Outage"
│   Start: 2024-01-15 10:45 UTC
│   End: 2024-01-15 11:20 UTC
│   Duration: 35 minutes
│
│   Impact:
│   - 35 video generation requests delayed
│   - No data loss
│   - No user-facing errors (queued gracefully)
│
│   Root Cause:
│   - Third-party service (Nano Banana API) experienced outage
│   - Outside our control
│
│   Mitigation:
│   - Enabled maintenance mode to queue requests
│   - Processed all requests after service recovery
│
│   Follow-up:
│   - Contact Nano Banana for post-mortem
│   - Consider backup video generation provider
│   - Improve queue visibility for users
│
└─> Share with team:
    - Engineering: For technical review
    - Support: For customer context
    - Sales: For account management

STEP 8: Post-Incident Actions
├─> Short-term (this week):
│   - Review Nano Banana SLA
│   - Implement better queue visibility for students
│   - Add ETA estimation for queued requests
│
├─> Medium-term (this month):
│   - Evaluate backup video generation providers
│   - Implement circuit breaker pattern for external APIs
│   - Improve monitoring and alerting
│
└─> Long-term (this quarter):
    - Multi-provider strategy for critical services
    - Enhanced failover mechanisms
    - Chaos engineering tests

COMPLETION TIME: Duration varies (typically 15-60 minutes)
PRIORITY: P0 - Highest priority (system-wide impact)
ESCALATION: Immediately notify on-call engineer and engineering lead
```

---

## Monitoring and Alerts

### Review Daily Metrics

**When**: Daily routine (every morning)

**Procedure**:

```
DAILY MONITORING ROUTINE (15 minutes)

STEP 1: System Health Overview (5 min)
├─> Navigate to: /internal/admin/system/health
├─> Check key metrics (last 24 hours):
│   ┌──────────────────────────────────────────────────────────────┐
│   │ System Health - Last 24 Hours                                │
│   │                                                              │
│   │ Overall Status: ✓ All Systems Operational                    │
│   │                                                              │
│   │ API Response Time: 142ms avg (Target: <200ms) ✓             │
│   │ Error Rate: 0.4% (Target: <1%) ✓                             │
│   │ Uptime: 100% (Target: >99.9%) ✓                              │
│   │                                                              │
│   │ Content Generation:                                          │
│   │ • Requests: 1,247 (avg per day)                              │
│   │ • Success Rate: 98.2% ✓                                      │
│   │ • Avg Generation Time: 8.5s (Target: <10s) ✓                 │
│   │ • Cache Hit Rate: 16.3% (Target: 15%) ✓                      │
│   │                                                              │
│   │ External Services:                                           │
│   │ • Vertex AI: ✓ Up (100% uptime)                              │
│   │ • Nano Banana: ✓ Up (99.8% uptime, 3 min downtime)           │
│   │ • Google TTS: ✓ Up (100% uptime)                             │
│   │ • Cloud SQL: ✓ Up (100% uptime, CPU: 45%)                    │
│   │                                                              │
│   │ Quotas & Limits:                                             │
│   │ • Vertex AI API: 8,450/10,000 calls (84%) ⚠                  │
│   │ • Cloud Storage: 1.2TB/5TB (24%) ✓                           │
│   │ • Database Connections: 150/200 (75%) ✓                      │
│   │                                                              │
│   └──────────────────────────────────────────────────────────────┘
│
└─> Note any warnings:
    ⚠ Vertex AI quota at 84% - may need increase soon

STEP 2: User Activity Review (3 min)
├─> Check user metrics:
│   Daily Active Users: 2,340 (normal: 2,000-2,500)
│   New Registrations: 45 students
│   Login Success Rate: 96% (normal: 95-98%)
│   Failed Logins: 87 attempts (check for suspicious patterns)
│
├─> Review by organization:
│   Most active: Lincoln High (387 users active)
│   Least active: Jefferson Middle (2 users, new org)
│
└─> Flag unusual activity:
    None today - all normal patterns

STEP 3: Content Quality Review (3 min)
├─> Check content metrics:
│   Videos Generated: 1,247
│   Flagged Content: 3 (review queue)
│   Safety Filter Triggers: 15 (1.2%, normal)
│   User Reports: 1 (investigate)
│
├─> Review flagged content queue:
│   3 items pending review
│   Oldest: 6 hours ago (within SLA)
│   Action: Assign to content moderator
│
└─> Check generation quality:
    Success rate: 98.2%
    Failure reasons: 2% API timeouts (acceptable)

STEP 4: Support Ticket Summary (2 min)
├─> Open tickets: 12
│   - P0 (critical): 0 ✓
│   - P1 (high): 2 (login issues, within SLA)
│   - P2 (medium): 7 (general questions)
│   - P3 (low): 3 (feature requests)
│
├─> Tickets closed yesterday: 18
│   Average resolution time: 4.2 hours (SLA: <8 hours)
│
└─> Trends:
    Common issues: Password resets (5 tickets)
    Action: Consider better password reset UX

STEP 5: Alert Review (2 min)
├─> Alerts triggered (last 24 hours): 2
│
│   Alert 1: Database CPU >80%
│   Time: 02:15-02:45 (30 minutes)
│   Cause: Nightly backup process
│   Resolution: Self-resolved
│   Action: None (expected)
│
│   Alert 2: Nano Banana API timeout spike
│   Time: 14:20-14:25 (5 minutes)
│   Cause: Brief service hiccup
│   Resolution: Service recovered
│   Action: Monitor today
│
└─> No action needed on past alerts

STEP 6: Capacity Planning Check (quick)
├─> Projected growth:
│   Students: +450 this month (3% growth)
│   Content requests: +50/day average
│   Storage: +100GB/week
│
├─> Resource headroom:
│   Database: 45% CPU → comfortable
│   API instances: Avg 40% utilization → comfortable
│   Storage: 1.2TB/5TB → 2 years at current rate
│   Vertex AI quota: 84% → may need increase in 2 weeks
│
└─> Action items:
    ✓ All systems have sufficient capacity
    ⚠ Request Vertex AI quota increase proactively

STEP 7: Document Daily Summary
├─> Update daily log:
│   Date: 2024-01-16
│   Status: ✓ All systems healthy
│   DAU: 2,340
│   Content requests: 1,247
│   Incidents: 0
│   Alerts: 2 (minor, resolved)
│   Action items:
│   - Request Vertex AI quota increase
│   - Review password reset UX
│   - Monitor Nano Banana API today
│
└─> Share with team (if noteworthy):
    All green today - no issues

COMPLETION TIME: 15 minutes daily
FREQUENCY: Every morning (weekdays)
ESCALATION: If P0 incidents or critical metrics, escalate immediately
```

---

### Respond to Performance Alert

**When**: Automated alert triggered for performance degradation

*See "Handle High Error Rate" above for detailed incident response workflow.*

---

### Investigate Security Incident

**When**: Suspicious activity detected or security alert triggered

**Procedure**:

```
SECURITY INCIDENT RESPONSE

⚠️ CRITICAL: Follow security protocols. Do not notify suspect user(s) during investigation.

STEP 1: Incident Identification
Security alert types:
├─> Multiple failed login attempts (potential brute force)
├─> Unusual access patterns (off-hours, unusual locations)
├─> Data export in large volumes (potential data theft)
├─> Privilege escalation attempts (unauthorized admin access)
├─> SQL injection or XSS attempts
├─> Suspicious API usage patterns

Example alert:
│   Subject: "🔴 SECURITY ALERT: Suspicious Login Activity"
│   Body:
│   """
│   User: john.doe@lincoln.edu
│   Activity: 47 failed login attempts in 10 minutes
│   IPs: 15 different IP addresses (distributed)
│   Location: Various countries
│   Time: 2024-01-16 03:00-03:10 UTC
│   Pattern: Potential credential stuffing attack
│   Status: Account automatically locked
│   """

STEP 2: Immediate Containment
├─> Lock affected account:
│   API: PATCH /api/v1/internal/users/{user_id}
│   Body: {"locked": true, "lock_reason": "security_investigation"}
│
├─> Invalidate all sessions:
│   API: POST /api/v1/internal/users/{user_id}/revoke-sessions
│   - Logs user out of all devices
│   - Invalidates all JWT tokens
│
├─> Block suspicious IPs (if concentrated):
│   API: POST /api/v1/internal/security/block-ip
│   Body: {"ips": ["1.2.3.4", "5.6.7.8"], "duration": "24h"}
│
└─> Prevent data exfiltration:
    If ongoing: Suspend organization API access temporarily

STEP 3: Investigate Scope
├─> Review authentication logs:
│   Navigate to: /internal/admin/security/logs
│   Filter: user_id = {user_id}, last 30 days
│
│   Look for:
│   - Successful logins: When? From where?
│   - Failed attempts: How many? From where?
│   - Password changes: Recent changes?
│   - Account modifications: Any unauthorized changes?
│
├─> Check for data access:
│   Review API access logs:
│   - What data did user access?
│   - Any bulk downloads?
│   - Unusual queries?
│   - Accessed other students' data?
│
├─> Determine compromise extent:
│   Single user affected?
│   Or: Multiple users in same organization?
│   Or: Cross-organization breach?
│
└─> Identify attack vector:
    - Compromised credentials (password stolen)?
    - Phishing attack?
    - Brute force success?
    - Application vulnerability exploited?

STEP 4: Assess Impact
├─> Data accessed:
│   - Student PII (names, emails)?
│   - Learning history?
│   - Teacher information?
│   - Organization details?
│
├─> Regulatory implications:
│   - FERPA violation? (if student education records accessed)
│   - COPPA violation? (if under-13 data accessed, rare)
│   - State data breach notification laws?
│
├─> Affected parties:
│   - Individual user
│   - Organization (school/district)
│   - Other users (if lateral movement)
│
└─> Classification:
    - Minor: Single account, no data exfiltration
    - Moderate: Account compromised, some data accessed
    - Major: Multiple accounts, significant data accessed
    - Critical: Systemic breach, regulatory notification required

STEP 5: Remediation
├─> Reset user credentials:
│   - Force password reset
│   - Require MFA setup (if available)
│   - Notify user via alternate channel (phone call)
│
├─> Patch vulnerability (if found):
│   - Deploy hotfix if application vulnerability
│   - Update security rules
│   - Enhance input validation
│
├─> Enhance monitoring:
│   - Add alerts for similar patterns
│   - Increase logging verbosity temporarily
│   - Monitor affected organization closely
│
└─> Review and harden:
    - Rate limiting sufficient?
    - CAPTCHA on login needed?
    - IP allowlisting for orgs?
    - Stronger password policies?

STEP 6: Notification
Based on severity:

MINOR INCIDENT (single account, no data breach):
├─> Notify user:
│   "Your account was locked due to suspicious login attempts.
│    For your security, please reset your password.
│    [Password Reset Link]"
│
└─> Notify organization admin:
    "We detected and blocked suspicious activity on a user account
     in your organization. The user has been notified."

MODERATE INCIDENT (compromise + data access):
├─> Notify user:
│   Via phone call (not email - account may be compromised)
│   Explain situation, require password reset
│
├─> Notify organization admin:
│   Detailed explanation, impacted user, data accessed
│   Recommendations for org-wide security review
│
└─> Notify Vividly leadership:
    Internal escalation for awareness

MAJOR/CRITICAL INCIDENT (data breach):
├─> Notify user and organization (within 24 hours)
├─> Notify Vividly legal team (immediately)
├─> Prepare regulatory notifications (FERPA, state laws)
├─> Notify affected parties (students, parents, teachers)
├─> Public disclosure (if required by law)
└─> Offer credit monitoring or remediation (if applicable)

STEP 7: Document Incident
├─> Create incident report:
│   Incident ID: SEC-2024-0116-001
│   Classification: Moderate
│   Type: Credential stuffing attack
│   Affected user: john.doe@lincoln.edu
│   Attack source: Distributed IPs (botnet suspected)
│   Timeline: 2024-01-16 03:00-03:10 UTC
│   Containment: Account locked, sessions revoked
│   Data accessed: None (attack blocked before success)
│   Remediation: Password reset required, IPs blocked
│   Notification: User and org admin notified
│
├─> Root cause analysis:
│   User used weak password ("Password123")
│   Password likely in leaked database from other breach
│   Recommendation: Enforce stronger password policy
│
└─> Lessons learned:
    - Rate limiting worked (blocked attack)
    - Detection was fast (10 minutes)
    - Improvement: Implement CAPTCHA after 3 failed attempts
    - Improvement: Require MFA for all users

STEP 8: Follow-Up Actions
├─> Short-term (this week):
│   - Implement CAPTCHA on login
│   - Audit all user passwords for weakness
│   - Force reset for users with common passwords
│
├─> Medium-term (this month):
│   - Implement MFA (multi-factor authentication)
│   - Enhanced security training for users
│   - IP allowlisting for enterprise orgs
│
└─> Long-term (this quarter):
    - Security audit by third party
    - Penetration testing
    - SOC 2 compliance certification

COMPLETION TIME: Varies (1-24 hours depending on severity)
PRIORITY: P0 - Highest priority
ESCALATION: Immediately notify security lead and engineering lead
REGULATORY: Consult legal team for notification requirements
```

---

## Maintenance

### Schedule Maintenance Window

**When**: Need to perform system maintenance (database upgrades, major deploys)

**Procedure**:

```
MAINTENANCE WINDOW PLANNING

STEP 1: Determine Maintenance Need
Types of maintenance:
├─> Database upgrades (PostgreSQL version, schema changes)
├─> Infrastructure changes (GCP resource scaling, network)
├─> Major application deployments (new features, breaking changes)
├─> Security patches (critical CVEs)
├─> Data migrations or cleanup

Example: PostgreSQL upgrade from 15 to 16

STEP 2: Plan Maintenance Window
├─> Duration estimate:
│   - Database backup: 30 minutes
│   - PostgreSQL upgrade: 1 hour
│   - Testing and verification: 30 minutes
│   - Buffer for issues: 1 hour
│   - Total: 3 hours
│
├─> Schedule:
│   - Date: Sunday, January 28, 2024
│   - Time: 02:00-05:00 UTC (off-peak hours)
│   - Reason: Minimize user impact (weekend, early morning)
│
├─> Impact assessment:
│   - Platform unavailable: Yes (full downtime)
│   - Data loss risk: Low (backup taken first)
│   - Rollback plan: Yes (restore from backup)
│
└─> Approval:
    - Engineering lead: Approved
    - CTO: Approved
    - Customer success: Notified

STEP 3: Create Maintenance Plan
├─> Pre-maintenance checklist:
│   □ Full database backup
│   □ Test backup restore in staging
│   □ Update status page with maintenance notice
│   │ Notify all organization admins (7 days, 3 days, 1 day, 2 hours before)
│   □ Prepare rollback scripts
│   □ Test upgrade in staging environment
│   □ On-call engineer assigned
│
├─> Maintenance steps:
│   1. Enable maintenance mode (02:00)
│   2. Stop all background workers
│   3. Drain active connections
│   4. Take final backup (02:10)
│   5. Begin PostgreSQL upgrade (02:30)
│   6. Run database migrations (03:30)
│   7. Verify data integrity (04:00)
│   8. Start services (04:30)
│   9. Smoke test all endpoints (04:40)
│   10. Disable maintenance mode (04:50)
│   11. Monitor for issues (05:00-06:00)
│
└─> Rollback plan:
    If upgrade fails:
    1. Stop upgrade process
    2. Restore from backup (taken at 02:10)
    3. Verify data integrity
    4. Start services with old version
    5. Communicate delay to users

STEP 4: Communicate Maintenance
7 days before:
├─> Update status page:
│   Title: "Scheduled Maintenance - January 28"
│   Body:
│   """
│   Vividly will undergo scheduled maintenance on Sunday, January 28,
│   from 2:00 AM to 5:00 AM UTC.
│
│   During this time:
│   • Platform will be unavailable
│   • All active sessions will be logged out
│   • No data will be lost
│   • Videos in your history will remain accessible after maintenance
│
│   Purpose: Database upgrade for improved performance
│
│   We apologize for any inconvenience.
│   """
│
├─> Email all organization admins:
│   Subject: "Scheduled Maintenance - January 28"
│   Body: [Same as status page + contact info for questions]
│
└─> In-app banner (starting 3 days before):
    "Scheduled maintenance on Jan 28, 2-5 AM UTC. Plan accordingly."

STEP 5: Execute Maintenance
On maintenance day:
├─> 02:00 UTC: Enable maintenance mode
│   API: POST /api/v1/internal/system/maintenance
│   Body: {"enabled": true, "reason": "Database upgrade"}
│
│   Effect:
│   - All API requests return: 503 Service Unavailable
│   - Frontend shows: "Vividly is undergoing maintenance.
│                       We'll be back by 5:00 AM UTC."
│   - Background workers: Paused
│
├─> 02:10 UTC: Take final backup
│   gcloud sql backups create --instance=dev-vividly-db
│   Verify backup: ✓ Success (5.2 GB)
│
├─> 02:30 UTC: Begin database upgrade
│   gcloud sql instances patch dev-vividly-db \
│     --database-version=POSTGRES_16 \
│     --async
│
│   Monitor progress in GCP Console
│   Estimated time: 60 minutes
│
├─> 03:30 UTC: Upgrade complete
│   Verify: ✓ PostgreSQL 16 running
│   Run database migrations:
│   alembic upgrade head
│   Verify: ✓ All migrations applied
│
├─> 04:00 UTC: Verify data integrity
│   Run integrity checks:
│   - Table counts: ✓ Match pre-upgrade
│   - Foreign key constraints: ✓ Valid
│   - Sample queries: ✓ Return expected results
│
├─> 04:30 UTC: Start services
│   Deploy Cloud Run services with updated config
│   gcloud run deploy vividly-dev-api-gateway --image=...
│   Verify: ✓ Services running
│
├─> 04:40 UTC: Smoke tests
│   Test critical paths:
│   ✓ Login works
│   ✓ Content request succeeds
│   ✓ Video playback works
│   ✓ Admin dashboard loads
│
└─> 04:50 UTC: Disable maintenance mode
    API: POST /api/v1/internal/system/maintenance
    Body: {"enabled": false}

    Platform live: ✓ Users can access

STEP 6: Post-Maintenance Monitoring
├─> 05:00-06:00 UTC: Active monitoring
│   Watch dashboards:
│   - Error rate: Normal (<1%)
│   - Response time: Normal (<200ms)
│   - Database performance: Monitor for issues
│   - User logins: Successful
│
├─> Check for issues:
│   No errors reported
│   User activity resuming normally
│   Database queries performing well (faster than before)
│
└─> All clear: 06:00 UTC
    Maintenance successful

STEP 7: Communicate Completion
├─> Update status page:
│   "Maintenance Complete - All Systems Operational"
│   "Scheduled maintenance completed successfully at 4:50 AM UTC.
│    All systems are now operational. Thank you for your patience."
│
├─> Email organization admins:
│   Subject: "Maintenance Complete - Vividly Back Online"
│   Body:
│   """
│   Our scheduled maintenance has been completed successfully.
│
│   Vividly is now fully operational.
│
│   What changed:
│   • Database upgraded for improved performance
│   • Faster query response times
│   • Enhanced reliability
│
│   No action needed from you. All your data is intact.
│   """
│
└─> Remove in-app banner

STEP 8: Document Maintenance
├─> Create maintenance report:
│   Maintenance ID: MAINT-2024-0128-001
│   Type: Database upgrade
│   Scheduled: 2024-01-28 02:00-05:00 UTC
│   Actual: 2024-01-28 02:00-04:50 UTC (finished early!)
│   Downtime: 2h 50min (within SLA)
│
│   Tasks completed:
│   ✓ PostgreSQL upgrade 15 → 16
│   ✓ Database migrations applied
│   ✓ Data integrity verified
│
│   Issues encountered: None
│
│   Post-maintenance:
│   - Performance improved: Avg query time 142ms → 98ms
│   - No user-reported issues
│   - All systems stable
│
└─> Lessons learned:
    - Staging tests were accurate (good planning)
    - Finished ahead of schedule (conservative estimates)
    - Communication was clear (no confused users)
    - Recommendation: Similar process for future DB upgrades

STEP 9: Update Documentation
├─> Update runbook:
│   Add PostgreSQL 16 upgrade steps to runbook
│   Document any configuration changes
│
├─> Update infrastructure docs:
│   Current PostgreSQL version: 16
│   Last upgraded: 2024-01-28
│   Next upgrade: TBD (PostgreSQL 17 in ~1 year)
│
└─> Share knowledge:
    Post-mortem meeting with engineering team
    Discuss what went well, what to improve

COMPLETION TIME: Varies (2-8 hours typical)
FREQUENCY: Quarterly for minor maintenance, annually for major upgrades
COMMUNICATION: Critical - notify users with ample lead time
```

---

### Database Backup and Restore

**When**: Regular backups (automated) or emergency restore needed

**Procedure**:

```
DATABASE BACKUP

Automated Backups:
├─> Configured in Terraform (see terraform/main.tf):
│   backup_configuration {
│     enabled = true
│     point_in_time_recovery_enabled = true
│     start_time = "03:00"  # Daily at 3 AM UTC
│     transaction_log_retention_days = 7
│     retained_backups = 30  # Keep 30 days of backups (prod)
│   }
│
├─> Backup schedule:
│   - Automated daily backups: 03:00 UTC
│   - Transaction logs: Continuous (for point-in-time recovery)
│   - Retention: 30 days (production), 7 days (dev/staging)
│
└─> Verify backups:
    gcloud sql backups list --instance=dev-vividly-db
    Should show recent backups

Manual Backup (On-Demand):
├─> When needed:
│   - Before major changes (deployments, migrations)
│   - Before maintenance windows
│   - For testing restore procedures
│
├─> Create backup:
│   gcloud sql backups create \
│     --instance=dev-vividly-db \
│     --description="Pre-maintenance backup 2024-01-28"
│
└─> Verify:
    Backup ID: backup_id_abc123
    Status: SUCCESSFUL
    Size: 5.2 GB

DATABASE RESTORE

SCENARIO 1: Restore from Automated Backup
├─> When: Data corruption, accidental deletion, need to rollback
│
├─> List available backups:
│   gcloud sql backups list --instance=dev-vividly-db
│
│   Output:
│   ID: 1234567890
│   Date: 2024-01-28 03:00:00
│   Status: SUCCESSFUL
│   Size: 5.2 GB
│
├─> Restore from backup:
│   ⚠️ WARNING: This will replace all current data!
│
│   gcloud sql backups restore 1234567890 \
│     --backup-instance=dev-vividly-db \
│     --backup-id=1234567890
│
│   Confirm: yes
│
│   Estimated time: 30-60 minutes (depends on size)
│
├─> Monitor restore:
│   Watch GCP Console for progress
│   Instance will be unavailable during restore
│
└─> Verify restore:
    - Check table counts
    - Verify recent data (before backup time)
    - Run integrity checks
    - Test critical queries

SCENARIO 2: Point-in-Time Recovery
├─> When: Need to restore to specific time (not just backup time)
│   Example: Accidental deletion at 14:30, need to restore to 14:25
│
├─> Check if point-in-time recovery enabled:
│   Terraform: point_in_time_recovery_enabled = true ✓
│
├─> Restore to specific time:
│   gcloud sql backups restore \
│     --backup-instance=dev-vividly-db \
│     --point-in-time='2024-01-28T14:25:00Z'
│
│   This uses transaction logs to restore to exact time
│
└─> Verify:
    Data as of 14:25 should be present
    Changes after 14:25 will be lost (expected)

SCENARIO 3: Clone Database for Testing
├─> When: Need to test restore without affecting production
│   Or: Need to test changes on production data
│
├─> Create clone:
│   gcloud sql instances clone dev-vividly-db \
│     dev-vividly-db-clone
│
│   Creates identical copy of database
│   Can be used for testing
│
├─> Use clone:
│   - Connect applications to clone
│   - Test changes
│   - Verify fixes
│
└─> Delete clone when done:
    gcloud sql instances delete dev-vividly-db-clone
    Saves costs

BEST PRACTICES:
├─> Test restores regularly (quarterly)
│   - Verify backups are valid
│   - Practice restore procedure
│   - Measure restore time
│
├─> Document restore procedures
│   - Keep runbook updated
│   - Train team on restore process
│   - Have 24/7 on-call with restore access
│
└─> Monitor backup success:
    - Alert if backup fails
    - Alert if backup size anomalous (too large/small)
    - Review backup logs monthly

DISASTER RECOVERY:
If primary database completely lost:
├─> 1. Create new Cloud SQL instance
├─> 2. Restore from most recent backup
├─> 3. Update application connection strings
├─> 4. Verify data integrity
├─> 5. Resume operations
└─> RTO: 2 hours, RPO: 24 hours (daily backups)
```

---

### Update Platform Configuration

**When**: Need to change application settings, feature flags, or configuration

**Procedure**:

```
CONFIGURATION MANAGEMENT

Configuration is stored in:
├─> Environment variables (for secrets and instance-specific config)
├─> Secret Manager (for sensitive data like API keys)
├─> Database (for application settings and feature flags)
├─> Terraform (for infrastructure configuration)

COMMON CONFIGURATION TASKS:

TASK 1: Update API Rate Limits
├─> Current: 10 content requests per hour per student
├─> New: 15 content requests per hour (increased for testing period)
│
├─> Update via admin panel:
│   Navigate to: /internal/admin/system/config
│   Find: CONTENT_REQUEST_RATE_LIMIT
│   Change: 10 → 15
│   Effective: Immediate (no restart required)
│
└─> Or via API:
    API: PATCH /api/v1/internal/system/config
    Body: {
      "key": "CONTENT_REQUEST_RATE_LIMIT",
      "value": "15",
      "description": "Max content requests per hour per student",
      "updated_by": "admin_jane"
    }

TASK 2: Enable Feature Flag
├─> Feature: New analytics dashboard (beta)
├─> Enable for specific organization first (gradual rollout)
│
├─> Navigate to: /internal/admin/features
├─> Find: advanced_analytics_dashboard
├─> Enable for: Lincoln High School (org_lincoln)
│   [ ] All organizations
│   [x] Specific organizations
│       ☑ Lincoln High School
│       ☐ Jefferson Middle School
│   [ ] Disabled
│
├─> Click "Save"
│
└─> Verify:
    - Log in as Lincoln admin: Feature visible ✓
    - Log in as Jefferson admin: Feature not visible ✓

TASK 3: Update External API Key
├─> API: Nano Banana (video generation)
├─> Reason: Key rotation (security best practice)
│
├─> Obtain new API key from Nano Banana dashboard
│
├─> Update in Secret Manager:
│   gcloud secrets versions add nano-banana-api-key-dev \
│     --data-file=- <<< "new_api_key_here"
│
├─> Restart services to pick up new key:
│   gcloud run services update vividly-dev-content-worker \
│     --region=us-central1
│
│   Services automatically fetch latest secret version
│
└─> Verify:
    - Test content generation: Success ✓
    - Check logs: Using new key ✓

TASK 4: Adjust Cache TTL
├─> Current: 30 days for cached videos
├─> New: 60 days (to improve cache hit rate)
│
├─> Update config:
│   Key: CACHE_TTL_DAYS
│   Old: 30
│   New: 60
│
├─> This affects:
│   - New cached content (60-day TTL)
│   - Existing cached content (retains original TTL until regenerated)
│
└─> Monitor impact:
    - Cache hit rate should increase over time
    - Storage usage will increase slightly

TASK 5: Update Notification Channels (Monitoring Alerts)
├─> Add new Slack channel for alerts
│
├─> Create notification channel in GCP Monitoring:
│   - Type: Slack
│   - Webhook URL: [from Slack]
│   - Display name: "Vividly Alerts - Slack"
│
├─> Update Terraform config (terraform/main.tf):
│   notification_channels = [
│     "projects/vividly-dev/notificationChannels/1234567890",  # Existing email
│     "projects/vividly-dev/notificationChannels/0987654321"   # New Slack
│   ]
│
├─> Apply changes:
│   cd terraform
│   terraform plan -var-file=environments/dev.tfvars
│   terraform apply -var-file=environments/dev.tfvars
│
└─> Test:
    Trigger test alert to verify Slack notification works

TASK 6: Update Subscription Tier Features
├─> Premium tier adds new feature: Custom branding
│
├─> Update tier definition:
│   Navigate to: /internal/admin/subscription-tiers
│   Tier: Premium
│   Features: [Add] custom_branding
│
│   This makes feature available to all premium orgs
│
└─> Notify existing premium customers:
    "New feature available: Custom branding!"

CONFIGURATION BEST PRACTICES:
├─> Version control all config changes (Terraform in Git)
├─> Test changes in dev/staging before production
├─> Document what each config does
├─> Never commit secrets to Git (use Secret Manager)
├─> Audit config changes (who changed what when)
└─> Have rollback plan for all changes
```

---

## Appendix

### Admin Tools Reference

```
ADMIN PANEL SECTIONS:

/internal/admin/
├─> /dashboard - System overview
├─> /organizations - Manage organizations
│   ├─> /create - Create new org
│   ├─> /{org_id} - Org details
│   └─> /{org_id}/edit - Edit org settings
├─> /users - Manage users
│   ├─> /create - Create new user
│   ├─> /bulk-import - Bulk user import
│   └─> /{user_id} - User details
├─> /content - Content management
│   ├─> /flagged - Flagged content review queue
│   ├─> /cache - Cache management
│   └─> /requests - Content request logs
├─> /system - System administration
│   ├─> /health - System health dashboard
│   ├─> /errors - Error logs and metrics
│   ├─> /integrations - External service status
│   ├─> /config - Configuration settings
│   └─> /logs - System logs
├─> /security - Security tools
│   ├─> /logs - Security audit logs
│   ├─> /incidents - Security incidents
│   └─> /block-ip - IP blocking
└─> /features - Feature flag management
```

### Contact Escalation Matrix

```
ISSUE SEVERITY LEVELS:

P0 - Critical (Immediate Response)
├─> Definition: System down, data breach, security incident
├─> Response time: 15 minutes
├─> Escalation: On-call engineer → Engineering lead → CTO
├─> Examples:
│   - API completely unavailable
│   - Database corruption
│   - Active security breach
│   - Mass user lockout

P1 - High (1-Hour Response)
├─> Definition: Major feature broken, high error rate
├─> Response time: 1 hour
├─> Escalation: On-call engineer → Engineering lead
├─> Examples:
│   - Video generation not working
│   - Login issues affecting multiple orgs
│   - External service outage (no workaround)

P2 - Medium (4-Hour Response)
├─> Definition: Minor feature issue, individual user problems
├─> Response time: 4 hours (business hours)
├─> Escalation: Support team → Engineering (if needed)
├─> Examples:
│   - Single user cannot log in
│   - Slow performance for one feature
│   - UI bug affecting usability

P3 - Low (24-Hour Response)
├─> Definition: Enhancement requests, non-urgent issues
├─> Response time: 24 hours (business hours)
├─> Escalation: Support team handles
├─> Examples:
│   - Feature requests
│   - Documentation updates
│   - Cosmetic UI issues

CONTACT LIST:
├─> On-Call Engineer: [Pagerduty rotation]
├─> Engineering Lead: engineering-lead@vividly.edu
├─> Security Team: security@vividly.edu
├─> CTO: cto@vividly.edu
├─> Customer Success: support@vividly.edu
└─> Sales: sales@vividly.edu
```

---

**Document Version**: 1.0
**Last Updated**: 2024-01-16
**Maintained By**: Vividly Operations Team
**Review Frequency**: Quarterly
