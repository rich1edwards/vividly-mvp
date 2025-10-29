# Phase 2: Core Backend Services - Sprint Plan

**Phase Duration**: 3 weeks (November 4 - November 22, 2025)
**Sprint Model**: 1-week sprints (3 sprints total)
**Team Size**: 2 full-stack engineers
**Velocity Target**: 25-30 story points per sprint
**Definition of Done**: Code reviewed, tests passing (>80% coverage), API docs updated, deployed to dev

---

## Table of Contents

1. [Sprint Overview](#sprint-overview)
2. [Team Capacity & Velocity](#team-capacity--velocity)
3. [Sprint 1: Foundation APIs](#sprint-1-foundation-apis-week-1)
4. [Sprint 2: Management APIs](#sprint-2-management-apis-week-2)
5. [Sprint 3: Infrastructure APIs](#sprint-3-infrastructure-apis-week-3)
6. [Risk Management](#risk-management)
7. [Technical Dependencies](#technical-dependencies)
8. [Quality Gates](#quality-gates)
9. [Success Metrics](#success-metrics)

---

## Sprint Overview

### Phase 2 Objectives

Build all core backend API services and endpoints required for the MVP, ensuring:
- Secure authentication and authorization
- Complete user management (CRUD operations)
- Content discovery and metadata
- Caching and delivery infrastructure
- Notification system
- Comprehensive testing and documentation

### Sprint Breakdown

| Sprint | Focus | Key Deliverables | Story Points |
|--------|-------|------------------|--------------|
| Sprint 1 | Foundation APIs | Auth, Student Service, Teacher Service | 28 |
| Sprint 2 | Management APIs | Admin Service, Topics/Interests, Content Metadata | 30 |
| Sprint 3 | Infrastructure APIs | Cache Service, Content Delivery, Notifications | 26 |
| **Total** | | **All Backend APIs** | **84** |

### Dependencies Graph

```
Sprint 1: Foundation
├─ Authentication API (CRITICAL PATH) ─┐
├─ Student Service ────────────────────┼─> Sprint 2
├─ Teacher Service ────────────────────┤
└─ Database Models ────────────────────┘

Sprint 2: Management
├─ Admin Service (depends on Sprint 1) ─┐
├─ Topics & Interests API ──────────────┼─> Sprint 3
└─ Content Metadata API ────────────────┘

Sprint 3: Infrastructure
├─ Cache Service (depends on Sprint 2)
├─ Content Delivery Service
└─ Notification Service
```

---

## Team Capacity & Velocity

### Team Composition

**Engineer 1** (Backend Focus):
- Primary: Authentication, Admin, Cache
- Secondary: Database optimization, testing
- Capacity: 14 story points/sprint (7 points/day)

**Engineer 2** (Full-Stack):
- Primary: Student/Teacher services, Content APIs
- Secondary: API documentation, integration
- Capacity: 14 story points/sprint (7 points/day)

### Story Point Scale (Fibonacci)

| Points | Complexity | Time Estimate | Examples |
|--------|-----------|---------------|----------|
| 1 | Trivial | 1-2 hours | Simple CRUD endpoint, schema definition |
| 2 | Simple | 2-4 hours | Basic endpoint with validation |
| 3 | Moderate | 4-6 hours | Complex endpoint with business logic |
| 5 | Complex | 1 day | Service with multiple endpoints |
| 8 | Very Complex | 1.5-2 days | Complete feature with testing |
| 13 | Epic | 2-3 days | Major system component |

### Velocity Tracking

**Sprint 1 Target**: 28 points (slightly below capacity for ramp-up)
**Sprint 2 Target**: 30 points (full capacity)
**Sprint 3 Target**: 26 points (buffer for integration issues)

---

## Sprint 1: Foundation APIs (Week 1)

**Dates**: November 4-8, 2025
**Goal**: Implement authentication system and basic user services
**Story Points**: 28

### Sprint 1 Objectives

1. ✅ Complete authentication flow (register, login, logout, refresh)
2. ✅ Implement student profile and interest management
3. ✅ Implement teacher class and student management
4. ✅ Establish testing patterns and CI/CD
5. ✅ Create Postman collection for manual testing

### Sprint 1 Backlog

#### Epic 1.1: Authentication API (13 points) - CRITICAL PATH

**Owner**: Engineer 1
**Priority**: P0 (Must Have)
**Dependencies**: Auth middleware (already complete ✅)

##### Story 1.1.1: User Registration Endpoint (3 points)

**As a** new user
**I want to** register an account with email and password
**So that** I can access the Vividly platform

**Tasks**:
- [ ] Define registration schema (Pydantic)
  - Email validation (regex)
  - Password strength validation (8+ chars, mixed case, number)
  - Role selection (student, teacher)
  - Grade level (students only)
- [ ] Implement registration endpoint `POST /api/v1/auth/register`
  - Check for duplicate email
  - Hash password with bcrypt (cost factor 12)
  - Create user in database
  - Generate welcome email (queue for sending)
- [ ] Write unit tests
  - Valid registration
  - Duplicate email handling
  - Password validation edge cases
  - SQL injection attempts
- [ ] Write integration test for full flow
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Endpoint returns 201 with user object (excluding password)
- [x] Password is hashed in database
- [x] Duplicate email returns 409 Conflict
- [x] Invalid email returns 422 Validation Error
- [x] Weak password returns 422 with helpful message
- [x] Welcome email queued (not sent yet, just logged)
- [x] Test coverage >85%

**API Contract**:
```python
# Request
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "student@mnps.edu",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "grade_level": 10  // Required if role=student
}

# Response (201 Created)
{
  "user_id": "user_abc123",
  "email": "student@mnps.edu",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "grade_level": 10,
  "created_at": "2025-11-04T10:00:00Z"
}

# Error (409 Conflict)
{
  "error": {
    "code": "CONFLICT",
    "message": "An account with this email already exists",
    "field": "email"
  }
}
```

**Time Estimate**: 4-6 hours

---

##### Story 1.1.2: User Login Endpoint (2 points)

**As a** registered user
**I want to** log in with my email and password
**So that** I can access my account

**Tasks**:
- [ ] Implement login endpoint `POST /api/v1/auth/login`
  - Validate credentials
  - Check account status (active, suspended)
  - Generate JWT access token (24h expiration)
  - Generate JWT refresh token (30d expiration)
  - Track login attempt (rate limiting already in middleware)
  - Update last_login_at timestamp
- [ ] Write unit tests
  - Valid login
  - Invalid credentials
  - Account suspended
  - Rate limiting (>5 attempts)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns 200 with access_token and refresh_token
- [x] Invalid credentials return 401 Unauthorized
- [x] Suspended account returns 403 Forbidden
- [x] Rate limiting after 5 failed attempts (15 min lockout)
- [x] Last login timestamp updated
- [x] JWT contains user_id, role, email in payload
- [x] Test coverage >85%

**API Contract**:
```python
# Request
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "student@mnps.edu",
  "password": "SecurePass123!"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "user_abc123",
    "email": "student@mnps.edu",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "grade_level": 10
  }
}

# Error (401 Unauthorized)
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid email or password"
  }
}

# Error (429 Rate Limit)
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many login attempts. Please try again in 15 minutes.",
    "retry_after": 900
  }
}
```

**Time Estimate**: 2-4 hours

---

##### Story 1.1.3: Token Refresh Endpoint (2 points)

**As a** logged-in user
**I want to** refresh my access token
**So that** I can stay authenticated without re-logging in

**Tasks**:
- [ ] Implement refresh endpoint `POST /api/v1/auth/refresh`
  - Validate refresh token
  - Check if token is revoked (session table)
  - Generate new access token
  - Optionally rotate refresh token (security best practice)
- [ ] Write unit tests
  - Valid refresh
  - Expired refresh token
  - Revoked token
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns 200 with new access_token
- [x] Expired refresh token returns 401
- [x] Revoked token returns 401
- [x] Refresh token rotated on use (new refresh_token returned)
- [x] Old refresh token invalidated
- [x] Test coverage >85%

**API Contract**:
```python
# Request
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // New
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", // New (rotated)
  "token_type": "Bearer",
  "expires_in": 86400
}
```

**Time Estimate**: 2-4 hours

---

##### Story 1.1.4: Logout Endpoint (2 points)

**As a** logged-in user
**I want to** log out
**So that** my session is terminated securely

**Tasks**:
- [ ] Implement logout endpoint `POST /api/v1/auth/logout`
  - Revoke current access token (add to blacklist)
  - Revoke refresh token (mark in database)
  - Delete session record
- [ ] Write unit tests
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns 204 No Content
- [x] Token added to Redis blacklist (TTL = token expiration)
- [x] Refresh token revoked in database
- [x] Subsequent requests with token return 401
- [x] Test coverage >85%

**API Contract**:
```python
# Request
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Response (204 No Content)
```

**Time Estimate**: 2-4 hours

---

##### Story 1.1.5: Get Current User Endpoint (2 points)

**As a** logged-in user
**I want to** get my current profile information
**So that** I can display it in the UI

**Tasks**:
- [ ] Implement profile endpoint `GET /api/v1/auth/me`
  - Extract user from JWT (middleware already does this)
  - Return user profile with relevant fields
  - Include role-specific data (e.g., classes for teachers)
- [ ] Write unit tests
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns 200 with user profile
- [x] Requires valid JWT (401 if missing/invalid)
- [x] Returns role-specific fields
- [x] Excludes sensitive data (password_hash)
- [x] Test coverage >85%

**API Contract**:
```python
# Request
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Response (200 OK) - Student
{
  "user_id": "user_abc123",
  "email": "student@mnps.edu",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "grade_level": 10,
  "school_id": "school_hillsboro_hs",
  "interests": ["int_basketball", "int_music"],
  "created_at": "2025-11-01T10:00:00Z",
  "last_login_at": "2025-11-04T09:15:00Z"
}

# Response (200 OK) - Teacher
{
  "user_id": "user_xyz789",
  "email": "teacher@mnps.edu",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "teacher",
  "school_id": "school_hillsboro_hs",
  "classes": [
    {"class_id": "class_001", "name": "Physics 101"}
  ],
  "created_at": "2025-09-01T10:00:00Z",
  "last_login_at": "2025-11-04T08:30:00Z"
}
```

**Time Estimate**: 2-4 hours

---

##### Story 1.1.6: Password Reset Flow (2 points)

**As a** user who forgot my password
**I want to** reset it via email
**So that** I can regain access to my account

**Tasks**:
- [ ] Implement reset request `POST /api/v1/auth/reset-password`
  - Generate secure reset token (UUID)
  - Store token with expiration (1 hour)
  - Queue password reset email (log for now)
- [ ] Implement reset confirmation `POST /api/v1/auth/reset-password/confirm`
  - Validate reset token
  - Update password
  - Revoke all existing sessions
  - Send confirmation email
- [ ] Write unit tests
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Reset request always returns 200 (security: don't reveal if email exists)
- [x] Reset token expires after 1 hour
- [x] Confirmation with invalid token returns 400
- [x] Password updated successfully
- [x] All sessions revoked after reset
- [x] Test coverage >85%

**API Contract**:
```python
# Request Reset
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "email": "student@mnps.edu"
}

# Response (200 OK) - Always returns this, even if email doesn't exist
{
  "message": "If an account exists with this email, a password reset link has been sent."
}

# Confirm Reset
POST /api/v1/auth/reset-password/confirm
Content-Type: application/json

{
  "reset_token": "550e8400-e29b-41d4-a716-446655440000",
  "new_password": "NewSecurePass123!"
}

# Response (200 OK)
{
  "message": "Password reset successfully. Please log in with your new password."
}
```

**Time Estimate**: 2-4 hours

---

#### Epic 1.2: Student Service (8 points)

**Owner**: Engineer 2
**Priority**: P0 (Must Have)
**Dependencies**: Authentication API (Story 1.1)

##### Story 1.2.1: Student Profile Management (3 points)

**As a** student
**I want to** view and update my profile
**So that** I can keep my information current

**Tasks**:
- [ ] Define student profile schema (Pydantic)
- [ ] Implement `GET /api/v1/students/profile`
  - Fetch current student profile
  - Include interests, progress summary
- [ ] Implement `PUT /api/v1/students/profile`
  - Update editable fields (name, grade_level)
  - Validate changes
  - Update database
- [ ] Write unit tests (5 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET returns complete student profile
- [x] PUT updates allowed fields only
- [x] Cannot change email or role (security)
- [x] Returns 403 if non-student tries to access
- [x] Test coverage >85%

**API Contract**:
```python
# Get Profile
GET /api/v1/students/profile
Authorization: Bearer <student-token>

# Response (200 OK)
{
  "student_id": "user_abc123",
  "email": "student@mnps.edu",
  "first_name": "John",
  "last_name": "Doe",
  "grade_level": 10,
  "school_id": "school_hillsboro_hs",
  "school_name": "Hillsboro High School",
  "interests": [
    {"interest_id": "int_basketball", "name": "Basketball", "category": "sports"}
  ],
  "progress_summary": {
    "topics_completed": 5,
    "videos_watched": 12,
    "total_watch_time_minutes": 45,
    "streak_days": 3
  },
  "created_at": "2025-11-01T10:00:00Z"
}

# Update Profile
PUT /api/v1/students/profile
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "first_name": "Jonathan",
  "grade_level": 11
}

# Response (200 OK)
{
  "student_id": "user_abc123",
  "first_name": "Jonathan",  // Updated
  "last_name": "Doe",
  "grade_level": 11,  // Updated
  ...
}
```

**Time Estimate**: 4-6 hours

---

##### Story 1.2.2: Interest Selection & Management (3 points)

**As a** student
**I want to** select and update my interests
**So that** my content is personalized to my passions

**Tasks**:
- [ ] Implement `GET /api/v1/students/interests`
  - Fetch student's current interests
- [ ] Implement `PUT /api/v1/students/interests`
  - Validate interest IDs (must be in canonical list)
  - Enforce min 1, max 5 interests
  - Update student_interests table
- [ ] Write unit tests (6 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET returns current interests with details
- [x] PUT validates interest IDs exist
- [x] PUT enforces 1-5 interest limit
- [x] PUT prevents duplicate interests
- [x] Invalid interest ID returns 422
- [x] Test coverage >85%

**API Contract**:
```python
# Get Interests
GET /api/v1/students/interests
Authorization: Bearer <student-token>

# Response (200 OK)
{
  "student_id": "user_abc123",
  "interests": [
    {
      "interest_id": "int_basketball",
      "name": "Basketball",
      "category": "sports",
      "icon_url": "https://cdn.vividly.edu/icons/basketball.svg",
      "selected_at": "2025-11-01T10:30:00Z"
    },
    {
      "interest_id": "int_music",
      "name": "Music Production",
      "category": "arts",
      "icon_url": "https://cdn.vividly.edu/icons/music.svg",
      "selected_at": "2025-11-01T10:30:00Z"
    }
  ]
}

# Update Interests
PUT /api/v1/students/interests
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "interest_ids": ["int_basketball", "int_music", "int_coding"]
}

# Response (200 OK)
{
  "student_id": "user_abc123",
  "interests": [
    {"interest_id": "int_basketball", ...},
    {"interest_id": "int_music", ...},
    {"interest_id": "int_coding", ...}  // New
  ],
  "updated_at": "2025-11-04T14:20:00Z"
}

# Error (422 Validation Error)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "You must select between 1 and 5 interests",
    "details": {
      "field": "interest_ids",
      "constraint": "length",
      "min": 1,
      "max": 5,
      "actual": 6
    }
  }
}
```

**Time Estimate**: 4-6 hours

---

##### Story 1.2.3: Student Progress Tracking (2 points)

**As a** student
**I want to** view my learning progress
**So that** I can see what I've accomplished

**Tasks**:
- [ ] Implement `GET /api/v1/students/progress`
  - Fetch progress summary (topics completed, videos watched)
  - Fetch recent activity (last 10 items)
  - Fetch topic completion matrix
- [ ] Implement query filters (by subject, date range)
- [ ] Write unit tests (4 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns comprehensive progress summary
- [x] Returns recent activity timeline
- [x] Supports filtering by subject and date
- [x] Calculates streak correctly
- [x] Test coverage >85%

**API Contract**:
```python
# Get Progress
GET /api/v1/students/progress?subject=physics&date_from=2025-11-01
Authorization: Bearer <student-token>

# Response (200 OK)
{
  "student_id": "user_abc123",
  "summary": {
    "topics_completed": 5,
    "videos_watched": 12,
    "total_watch_time_minutes": 45,
    "streak_days": 3,
    "last_active": "2025-11-04T09:15:00Z"
  },
  "recent_activity": [
    {
      "activity_id": "act_001",
      "type": "video_completed",
      "topic_id": "topic_phys_mech_newton_3",
      "topic_name": "Newton's Third Law",
      "interest": "basketball",
      "completed_at": "2025-11-04T09:15:00Z",
      "watch_duration_seconds": 180
    },
    ...
  ],
  "topic_matrix": {
    "Physics": {
      "Mechanics": {
        "completed": 3,
        "total": 10,
        "topics": [
          {
            "topic_id": "topic_phys_mech_newton_1",
            "name": "Newton's First Law",
            "status": "completed",
            "completed_at": "2025-11-02T10:00:00Z"
          },
          {
            "topic_id": "topic_phys_mech_newton_2",
            "name": "Newton's Second Law",
            "status": "in_progress",
            "progress_percentage": 60
          },
          ...
        ]
      }
    }
  }
}
```

**Time Estimate**: 2-4 hours

---

#### Epic 1.3: Teacher Service (7 points)

**Owner**: Engineer 2 (parallel with Engineer 1 on Auth)
**Priority**: P0 (Must Have)
**Dependencies**: Authentication API

##### Story 1.3.1: Teacher Profile & Class List (2 points)

**As a** teacher
**I want to** view my profile and classes
**So that** I can manage my classes

**Tasks**:
- [ ] Implement `GET /api/v1/teachers/profile`
  - Fetch teacher profile
  - Include school information
- [ ] Implement `GET /api/v1/teachers/classes`
  - Fetch all classes for teacher
  - Include student counts
  - Support pagination
- [ ] Write unit tests (4 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET profile returns teacher data
- [x] GET classes returns paginated list
- [x] Includes student counts per class
- [x] Returns 403 if non-teacher tries to access
- [x] Test coverage >85%

**API Contract**:
```python
# Get Profile
GET /api/v1/teachers/profile
Authorization: Bearer <teacher-token>

# Response (200 OK)
{
  "teacher_id": "user_xyz789",
  "email": "teacher@mnps.edu",
  "first_name": "Jane",
  "last_name": "Smith",
  "school_id": "school_hillsboro_hs",
  "school_name": "Hillsboro High School",
  "subjects": ["Physics", "Chemistry"],
  "total_students": 87,
  "total_classes": 3,
  "created_at": "2025-09-01T10:00:00Z"
}

# Get Classes
GET /api/v1/teachers/classes?limit=20&cursor=abc123
Authorization: Bearer <teacher-token>

# Response (200 OK)
{
  "classes": [
    {
      "class_id": "class_001",
      "name": "Physics 101 - Period 1",
      "subject": "Physics",
      "grade_level": 10,
      "student_count": 28,
      "active_students_7d": 24,
      "created_at": "2025-09-01T10:00:00Z"
    },
    ...
  ],
  "pagination": {
    "next_cursor": "xyz789",
    "has_more": true,
    "total_count": 3
  }
}
```

**Time Estimate**: 2-4 hours

---

##### Story 1.3.2: Class Management (3 points)

**As a** teacher
**I want to** create and manage classes
**So that** I can organize my students

**Tasks**:
- [ ] Implement `POST /api/v1/teachers/classes`
  - Create new class
  - Generate unique class code (for student join)
- [ ] Implement `PUT /api/v1/teachers/classes/{id}`
  - Update class details
- [ ] Implement `DELETE /api/v1/teachers/classes/{id}`
  - Soft delete (archive) class
  - Prevent if students have progress
- [ ] Implement `GET /api/v1/teachers/classes/{id}`
  - Get class details with student list
- [ ] Write unit tests (6 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] POST creates class with unique code
- [x] PUT updates allowed fields only
- [x] DELETE archives (not hard delete)
- [x] GET returns class with students
- [x] Prevents deletion if students have progress
- [x] Test coverage >85%

**API Contract**:
```python
# Create Class
POST /api/v1/teachers/classes
Authorization: Bearer <teacher-token>
Content-Type: application/json

{
  "name": "Physics 101 - Period 1",
  "subject": "Physics",
  "grade_level": 10,
  "description": "Introduction to Mechanics"
}

# Response (201 Created)
{
  "class_id": "class_001",
  "name": "Physics 101 - Period 1",
  "subject": "Physics",
  "grade_level": 10,
  "description": "Introduction to Mechanics",
  "class_code": "PHYS-ABC-123",  // For student join
  "teacher_id": "user_xyz789",
  "student_count": 0,
  "created_at": "2025-11-04T10:00:00Z"
}

# Get Class Details
GET /api/v1/teachers/classes/class_001
Authorization: Bearer <teacher-token>

# Response (200 OK)
{
  "class_id": "class_001",
  "name": "Physics 101 - Period 1",
  "subject": "Physics",
  "grade_level": 10,
  "student_count": 28,
  "students": [
    {
      "student_id": "user_abc123",
      "name": "John Doe",
      "email": "john.doe@mnps.edu",
      "last_active": "2025-11-04T09:15:00Z",
      "videos_watched": 12,
      "topics_completed": 5
    },
    ...
  ],
  "created_at": "2025-09-01T10:00:00Z"
}

# Update Class
PUT /api/v1/teachers/classes/class_001
Authorization: Bearer <teacher-token>
Content-Type: application/json

{
  "name": "Physics 101 - Period 2",
  "description": "Updated description"
}

# Delete (Archive) Class
DELETE /api/v1/teachers/classes/class_001
Authorization: Bearer <teacher-token>

# Response (204 No Content)
```

**Time Estimate**: 4-6 hours

---

##### Story 1.3.3: Student Account Request (2 points)

**As a** teacher
**I want to** request new student accounts
**So that** I can add students to my class

**Tasks**:
- [ ] Implement `POST /api/v1/teachers/student-requests`
  - Create account request
  - Route to appropriate approver (school admin)
  - Queue notification email to admin
- [ ] Implement `GET /api/v1/teachers/student-requests`
  - List teacher's pending requests
- [ ] Write unit tests (4 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] POST creates request with pending status
- [x] Request routed to school admin
- [x] Email notification queued (logged)
- [x] GET returns paginated request list
- [x] Test coverage >85%

**API Contract**:
```python
# Create Request
POST /api/v1/teachers/student-requests
Authorization: Bearer <teacher-token>
Content-Type: application/json

{
  "student_first_name": "Michael",
  "student_last_name": "Johnson",
  "student_email": "michael.johnson@mnps.edu",
  "grade_level": 10,
  "class_id": "class_001",
  "notes": "Transfer student from East High"
}

# Response (201 Created)
{
  "request_id": "req_001",
  "student_first_name": "Michael",
  "student_last_name": "Johnson",
  "student_email": "michael.johnson@mnps.edu",
  "grade_level": 10,
  "class_id": "class_001",
  "status": "pending",
  "requested_by": "user_xyz789",
  "requested_at": "2025-11-04T10:00:00Z",
  "approver_id": "user_admin123",  // School admin
  "approver_name": "Principal Jane Smith"
}

# Get Requests
GET /api/v1/teachers/student-requests?status=pending
Authorization: Bearer <teacher-token>

# Response (200 OK)
{
  "requests": [
    {
      "request_id": "req_001",
      "student_name": "Michael Johnson",
      "status": "pending",
      "requested_at": "2025-11-04T10:00:00Z"
    },
    ...
  ],
  "pagination": {...}
}
```

**Time Estimate**: 2-4 hours

---

### Sprint 1 Daily Breakdown

#### Monday (Nov 4) - Sprint Planning & Setup

**Morning** (9am-12pm):
- Sprint planning meeting (1 hour)
- Environment setup verification
- Database migration check ⚠️ (run migrations if not done)
- Create feature branches: `feature/auth-api`, `feature/student-service`

**Afternoon** (1pm-5pm):
- **Engineer 1**: Start Story 1.1.1 (Registration) - 50% complete
- **Engineer 2**: Start Story 1.2.1 (Student Profile GET) - 70% complete

**Standup Topics**:
- Confirm database migrations completed
- Verify auth middleware working
- Identify any blockers

**Daily Goal**: 6 story points started

---

#### Tuesday (Nov 5) - Core Authentication

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 1.1.1 (Registration) ✅
  - Start Story 1.1.2 (Login) - 80% complete
- **Engineer 2**:
  - Complete Story 1.2.1 (Student Profile GET) ✅
  - Start Story 1.2.1 (Student Profile PUT) - 60% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 1.1.2 (Login) ✅
  - Start Story 1.1.3 (Token Refresh) - 100% complete ✅
- **Engineer 2**:
  - Complete Story 1.2.1 (Student Profile PUT) ✅
  - Start Story 1.2.2 (Interest Selection) - 40% complete

**Standup Topics**:
- Registration endpoint working?
- Any issues with JWT generation?
- Database connection pool stable?

**Daily Goal**: 9 story points completed (cumulative: 15)

---

#### Wednesday (Nov 6) - Student & Teacher Services

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 1.1.4 (Logout) ✅
  - Complete Story 1.1.5 (Get Current User) ✅
  - Start Story 1.1.6 (Password Reset) - 50% complete
- **Engineer 2**:
  - Complete Story 1.2.2 (Interest Selection) ✅
  - Start Story 1.2.3 (Progress Tracking) - 60% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 1.1.6 (Password Reset) ✅
  - Start integration tests for Auth API
- **Engineer 2**:
  - Complete Story 1.2.3 (Progress Tracking) ✅
  - Start Story 1.3.1 (Teacher Profile) - 80% complete

**Standup Topics**:
- Password reset flow working?
- Student interests saving correctly?
- Any performance issues with progress queries?

**Daily Goal**: 8 story points completed (cumulative: 23)

---

#### Thursday (Nov 7) - Teacher Services & Testing

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Auth API integration tests ✅
  - Code review for Student Service
  - Start API documentation updates
- **Engineer 2**:
  - Complete Story 1.3.1 (Teacher Profile) ✅
  - Complete Story 1.3.2 (Class Management) - 70% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Postman collection for Auth API
  - Help with Teacher Service testing
- **Engineer 2**:
  - Complete Story 1.3.2 (Class Management) ✅
  - Start Story 1.3.3 (Student Request) - 100% complete ✅

**Standup Topics**:
- All auth tests passing?
- Class creation working?
- Any issues with RBAC enforcement?

**Daily Goal**: 7 story points completed (cumulative: 30)

---

#### Friday (Nov 8) - Sprint Review & Deployment

**Morning** (9am-12pm):
- **Both Engineers**:
  - Complete all remaining unit tests
  - Integration testing for all endpoints
  - Fix any failing tests
  - Code review session

**Afternoon** (1pm-3pm):
- Deploy to dev environment
- Smoke testing
- Update Postman collection
- Complete API documentation

**Afternoon** (3pm-5pm):
- Sprint Review (1 hour)
  - Demo all completed endpoints
  - Show Postman collection
  - Review test coverage report
- Sprint Retrospective (1 hour)
  - What went well?
  - What could be improved?
  - Action items for Sprint 2

**Sprint 1 Deliverables**:
- ✅ Complete Authentication API (13 points)
- ✅ Complete Student Service (8 points)
- ✅ Complete Teacher Service (7 points)
- ✅ Postman collection with examples
- ✅ API documentation updated
- ✅ Test coverage >80%
- ✅ All endpoints deployed to dev

**Standup Topics**:
- All tests passing?
- Ready for deployment?
- Any production concerns?

**Daily Goal**: Finalize sprint (28 points total completed)

---

### Sprint 1 Success Criteria

**Must Have** (Definition of Done):
- [ ] All 28 story points completed
- [ ] All endpoints functional and tested
- [ ] Test coverage >80% (pytest-cov report)
- [ ] Code reviewed and merged
- [ ] API documentation complete
- [ ] Postman collection created
- [ ] Deployed to dev environment
- [ ] Smoke tests passing
- [ ] No critical bugs

**Nice to Have**:
- Performance benchmarks (response times)
- Load testing initial results
- Additional edge case tests

---

## Sprint 2: Management APIs (Week 2)

**Dates**: November 11-15, 2025
**Goal**: Implement admin, content management, and discovery APIs
**Story Points**: 30

### Sprint 2 Objectives

1. ✅ Complete admin user management and KPI dashboard
2. ✅ Implement bulk upload functionality
3. ✅ Build topics and interests discovery APIs
4. ✅ Create content metadata system
5. ✅ Establish comprehensive integration testing

### Sprint 2 Backlog

#### Epic 2.1: Admin Service (13 points)

**Owner**: Engineer 1
**Priority**: P0 (Must Have)
**Dependencies**: Sprint 1 (User services complete)

##### Story 2.1.1: Bulk User Upload (5 points)

**As a** district admin
**I want to** upload multiple students via CSV
**So that** I can quickly onboard an entire school

**Tasks**:
- [ ] Define CSV schema and validation rules
- [ ] Implement `POST /api/v1/admin/users/bulk-upload`
  - Accept CSV file upload
  - Validate CSV structure (headers, row format)
  - Parse and validate each row
  - Check for duplicate emails
  - Create users in batch (transaction)
  - Generate welcome emails (queue)
  - Return detailed results (success/failures)
- [ ] Implement error handling
  - Partial success (some rows fail)
  - Complete failure (rollback)
  - Validation error reporting
- [ ] Implement upload status tracking
- [ ] Write unit tests (8 test cases)
- [ ] Write integration test (large CSV)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Accepts CSV with up to 1000 students
- [x] Processes in <30 seconds
- [x] Transaction-safe (all or nothing option)
- [x] Returns detailed success/failure report
- [x] Queues welcome emails efficiently
- [x] Handles duplicate emails gracefully
- [x] Test coverage >85%

**CSV Format**:
```csv
first_name,last_name,email,role,grade_level,school_id
John,Doe,john.doe@mnps.edu,student,10,school_hillsboro_hs
Jane,Smith,jane.smith@mnps.edu,student,11,school_hillsboro_hs
```

**API Contract**:
```python
# Request
POST /api/v1/admin/users/bulk-upload
Authorization: Bearer <admin-token>
Content-Type: multipart/form-data

file: students.csv
transaction_mode: "partial"  // "partial" or "atomic"

# Response (200 OK)
{
  "upload_id": "upload_001",
  "total_rows": 1000,
  "successful": 987,
  "failed": 13,
  "duration_seconds": 24.5,
  "results": {
    "created_users": ["user_001", "user_002", ...],
    "failed_rows": [
      {
        "row_number": 45,
        "email": "duplicate@mnps.edu",
        "error": "Email already exists",
        "error_code": "DUPLICATE_EMAIL"
      },
      {
        "row_number": 123,
        "email": "invalid-email",
        "error": "Invalid email format",
        "error_code": "INVALID_EMAIL"
      }
    ]
  }
}

# Get Upload Status
GET /api/v1/admin/users/bulk-upload/upload_001/status
Authorization: Bearer <admin-token>

# Response (200 OK)
{
  "upload_id": "upload_001",
  "status": "completed",
  "progress_percentage": 100,
  "created_at": "2025-11-11T10:00:00Z",
  "completed_at": "2025-11-11T10:00:24Z",
  ...
}
```

**Time Estimate**: 1 day

---

##### Story 2.1.2: User Management CRUD (5 points)

**As an** admin
**I want to** manage user accounts
**So that** I can create, update, and deactivate users

**Tasks**:
- [ ] Implement `GET /api/v1/admin/users`
  - Paginated user list
  - Filter by role, school, status
  - Search by name/email
- [ ] Implement `POST /api/v1/admin/users`
  - Create single user manually
- [ ] Implement `PUT /api/v1/admin/users/{id}`
  - Update user profile
  - Change role (with validation)
- [ ] Implement `DELETE /api/v1/admin/users/{id}`
  - Soft delete (deactivate)
  - Revoke all sessions
- [ ] Write unit tests (10 test cases)
- [ ] Write integration tests (3 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET supports filtering and pagination
- [x] POST creates user with validation
- [x] PUT allows admins to change roles
- [x] DELETE soft-deletes (is_active=false)
- [x] All sessions revoked on deletion
- [x] Cannot delete own account
- [x] Test coverage >85%

**API Contract**:
```python
# List Users
GET /api/v1/admin/users?role=student&school_id=school_hillsboro_hs&search=john&limit=20
Authorization: Bearer <admin-token>

# Response (200 OK)
{
  "users": [
    {
      "user_id": "user_abc123",
      "email": "john.doe@mnps.edu",
      "first_name": "John",
      "last_name": "Doe",
      "role": "student",
      "grade_level": 10,
      "school_id": "school_hillsboro_hs",
      "is_active": true,
      "created_at": "2025-11-01T10:00:00Z",
      "last_login_at": "2025-11-11T09:15:00Z"
    },
    ...
  ],
  "pagination": {
    "next_cursor": "cursor_xyz",
    "has_more": true,
    "total_count": 1543
  }
}

# Create User
POST /api/v1/admin/users
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "email": "newstudent@mnps.edu",
  "first_name": "Alice",
  "last_name": "Brown",
  "role": "student",
  "grade_level": 9,
  "school_id": "school_hillsboro_hs",
  "send_invitation": true
}

# Response (201 Created)
{
  "user_id": "user_new001",
  "email": "newstudent@mnps.edu",
  ...
  "invitation_sent": true
}

# Update User
PUT /api/v1/admin/users/user_abc123
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "role": "teacher",  // Promote to teacher
  "subjects": ["Physics"]
}

# Response (200 OK)
{
  "user_id": "user_abc123",
  "role": "teacher",  // Updated
  ...
}

# Delete User
DELETE /api/v1/admin/users/user_abc123
Authorization: Bearer <admin-token>

# Response (204 No Content)
```

**Time Estimate**: 1 day

---

##### Story 2.1.3: Account Request Approval (3 points)

**As an** admin
**I want to** approve or deny account requests
**So that** I can control user access

**Tasks**:
- [ ] Implement `GET /api/v1/admin/pending-requests`
  - List all pending account requests
  - Filter by school, teacher, date
- [ ] Implement `PUT /api/v1/admin/requests/{id}/approve`
  - Create user account
  - Add to requested class
  - Send welcome email
  - Notify requesting teacher
- [ ] Implement `PUT /api/v1/admin/requests/{id}/deny`
  - Mark request as denied
  - Add denial reason
  - Notify requesting teacher
- [ ] Write unit tests (6 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET returns paginated request list
- [x] Approve creates account immediately
- [x] Deny records reason
- [x] Notifications sent to teacher
- [x] Cannot approve duplicate requests
- [x] Test coverage >85%

**API Contract**:
```python
# List Pending Requests
GET /api/v1/admin/pending-requests?school_id=school_hillsboro_hs&limit=20
Authorization: Bearer <admin-token>

# Response (200 OK)
{
  "requests": [
    {
      "request_id": "req_001",
      "student_first_name": "Michael",
      "student_last_name": "Johnson",
      "student_email": "michael.johnson@mnps.edu",
      "grade_level": 10,
      "class_id": "class_001",
      "class_name": "Physics 101",
      "requested_by_id": "user_teacher123",
      "requested_by_name": "Jane Smith",
      "requested_at": "2025-11-10T14:30:00Z",
      "notes": "Transfer student from East High"
    },
    ...
  ],
  "pagination": {...}
}

# Approve Request
PUT /api/v1/admin/requests/req_001/approve
Authorization: Bearer <admin-token>

# Response (200 OK)
{
  "request_id": "req_001",
  "status": "approved",
  "user_created": {
    "user_id": "user_new002",
    "email": "michael.johnson@mnps.edu",
    "class_id": "class_001"
  },
  "approved_at": "2025-11-11T10:00:00Z",
  "approved_by": "user_admin123",
  "invitation_sent": true
}

# Deny Request
PUT /api/v1/admin/requests/req_001/deny
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "reason": "Student is not enrolled in MNPS district"
}

# Response (200 OK)
{
  "request_id": "req_001",
  "status": "denied",
  "denied_at": "2025-11-11T10:05:00Z",
  "denied_by": "user_admin123",
  "denial_reason": "Student is not enrolled in MNPS district",
  "teacher_notified": true
}
```

**Time Estimate**: 4-6 hours

---

#### Epic 2.2: Topics & Interests API (8 points)

**Owner**: Engineer 2
**Priority**: P0 (Must Have)
**Dependencies**: Database schema with topics/interests

##### Story 2.2.1: Topics Discovery API (5 points)

**As a** student or teacher
**I want to** browse and search available topics
**So that** I can find content to learn or assign

**Tasks**:
- [ ] Implement `GET /api/v1/topics`
  - List all topics with pagination
  - Filter by subject, grade level, category
  - Sort by name, difficulty, popularity
- [ ] Implement `GET /api/v1/topics/search`
  - Full-text search across topic names/descriptions
  - Use PostgreSQL full-text search (tsvector)
  - Rank results by relevance
- [ ] Implement `GET /api/v1/topics/{id}`
  - Get single topic details
  - Include prerequisites
  - Include related topics
  - Include standards alignment
- [ ] Implement `GET /api/v1/topics/{id}/prerequisites`
  - Get prerequisite topics
  - Check student completion status
- [ ] Write unit tests (8 test cases)
- [ ] Write integration tests (3 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET returns paginated topic list
- [x] Filtering works for all parameters
- [x] Search returns relevant results
- [x] GET by ID includes all relationships
- [x] Prerequisites ordered correctly
- [x] Test coverage >85%

**API Contract**:
```python
# List Topics
GET /api/v1/topics?subject=physics&grade_level=10&category=mechanics&limit=20
Authorization: Bearer <token>

# Response (200 OK)
{
  "topics": [
    {
      "topic_id": "topic_phys_mech_newton_3",
      "name": "Newton's Third Law",
      "subject": "Physics",
      "category": "Mechanics",
      "grade_levels": [9, 10],
      "difficulty": "intermediate",
      "description": "For every action, there is an equal and opposite reaction.",
      "estimated_duration_min": 15,
      "prerequisites": ["topic_phys_mech_newton_1", "topic_phys_mech_newton_2"],
      "standards": ["HS-PS2-1"],
      "content_available": true,  // At least one cached video exists
      "popularity_score": 0.85
    },
    ...
  ],
  "pagination": {
    "next_cursor": "cursor_abc",
    "has_more": true,
    "total_count": 142
  }
}

# Search Topics
GET /api/v1/topics/search?q=newton+laws&limit=10
Authorization: Bearer <token>

# Response (200 OK)
{
  "query": "newton laws",
  "results": [
    {
      "topic_id": "topic_phys_mech_newton_1",
      "name": "Newton's First Law",
      "relevance_score": 0.95,
      "highlights": ["Newton's First Law", "law of inertia"],
      ...
    },
    ...
  ],
  "total_results": 3
}

# Get Topic Details
GET /api/v1/topics/topic_phys_mech_newton_3
Authorization: Bearer <token>

# Response (200 OK)
{
  "topic_id": "topic_phys_mech_newton_3",
  "name": "Newton's Third Law",
  "subject": "Physics",
  "category": "Mechanics",
  "grade_levels": [9, 10],
  "difficulty": "intermediate",
  "description": "For every action, there is an equal and opposite reaction. When one object exerts a force on another, the second object exerts an equal force in the opposite direction.",
  "learning_objectives": [
    "Understand action-reaction pairs",
    "Apply Newton's Third Law to real-world scenarios",
    "Calculate forces in action-reaction pairs"
  ],
  "prerequisites": [
    {
      "topic_id": "topic_phys_mech_newton_1",
      "name": "Newton's First Law",
      "completed": true,  // For logged-in student
      "completed_at": "2025-11-05T10:00:00Z"
    },
    {
      "topic_id": "topic_phys_mech_newton_2",
      "name": "Newton's Second Law",
      "completed": false
    }
  ],
  "related_topics": [
    {"topic_id": "topic_phys_mech_momentum", "name": "Momentum"},
    {"topic_id": "topic_phys_mech_collisions", "name": "Collisions"}
  ],
  "standards": [
    {
      "standard_id": "HS-PS2-1",
      "description": "Analyze data to support the claim that Newton's second law of motion describes the mathematical relationship among...",
      "source": "NGSS"
    }
  ],
  "estimated_duration_min": 15,
  "content_available": true,
  "available_interests": ["basketball", "football", "music", "gaming"],
  "popularity_score": 0.85,
  "created_at": "2025-09-01T10:00:00Z"
}
```

**Time Estimate**: 1 day

---

##### Story 2.2.2: Interests API (3 points)

**As a** student
**I want to** browse all available interests
**So that** I can select ones that match my passions

**Tasks**:
- [ ] Implement `GET /api/v1/interests`
  - List all canonical interests
  - Group by category
  - Include icons/images
- [ ] Implement `GET /api/v1/interests/categories`
  - List all interest categories
  - Include interest counts
- [ ] Write unit tests (4 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Returns all 60 canonical interests
- [x] Grouped by category
- [x] Includes icon URLs
- [x] Categories endpoint works
- [x] Test coverage >85%

**API Contract**:
```python
# List Interests
GET /api/v1/interests
Authorization: Bearer <token>

# Response (200 OK)
{
  "interests": [
    {
      "interest_id": "int_basketball",
      "name": "Basketball",
      "category": "sports",
      "icon_url": "https://cdn.vividly.edu/icons/basketball.svg",
      "description": "Playing, watching, or coaching basketball",
      "popularity": 0.72,  // % of students with this interest
      "content_count": 45  // Videos using this interest
    },
    ...
  ],
  "total_count": 60,
  "categories": ["sports", "arts", "technology", "science", "entertainment"]
}

# List Categories
GET /api/v1/interests/categories
Authorization: Bearer <token>

# Response (200 OK)
{
  "categories": [
    {
      "category_id": "sports",
      "name": "Sports & Athletics",
      "description": "Physical activities, team sports, individual sports",
      "icon_url": "https://cdn.vividly.edu/icons/sports.svg",
      "interest_count": 15,
      "interests": [
        {"interest_id": "int_basketball", "name": "Basketball"},
        {"interest_id": "int_football", "name": "Football"},
        ...
      ]
    },
    ...
  ]
}
```

**Time Estimate**: 4-6 hours

---

#### Epic 2.3: Content Metadata API (9 points)

**Owner**: Engineer 2 (parallel with Topics API)
**Priority**: P1 (High)
**Dependencies**: Sprint 1, Topics API

##### Story 2.3.1: Content Metadata Endpoints (5 points)

**As a** user
**I want to** check if content exists and get metadata
**So that** I know what's available before requesting generation

**Tasks**:
- [ ] Implement `GET /api/v1/content/{cache_key}`
  - Get content metadata by cache key
  - Include URLs (script, audio, video)
  - Include generation status
- [ ] Implement `POST /api/v1/content/check`
  - Check if content exists for (topic_id, interest)
  - Return cache key if exists
  - Return null if needs generation
- [ ] Implement `GET /api/v1/content/recent`
  - List recently generated content
  - Filter by student, topic, interest
- [ ] Write unit tests (6 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] GET by cache_key returns full metadata
- [x] POST check performs cache lookup
- [x] Recent content paginated
- [x] Status tracking accurate
- [x] Test coverage >85%

**API Contract**:
```python
# Get Content Metadata
GET /api/v1/content/abc123def456
Authorization: Bearer <token>

# Response (200 OK) - Completed
{
  "cache_key": "abc123def456",
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "interest": "basketball",
  "status": "completed",
  "title": "Newton's Third Law: The Basketball Perspective",
  "duration_seconds": 180,
  "script_url": "https://storage.googleapis.com/.../script.json",
  "audio_url": "https://cdn.vividly.edu/.../audio.mp3",
  "video_url": "https://cdn.vividly.edu/.../video.mp4",
  "captions_url": "https://cdn.vividly.edu/.../captions.vtt",
  "thumbnail_url": "https://cdn.vividly.edu/.../thumbnail.jpg",
  "quality_levels": ["1080p", "720p", "480p"],
  "generated_at": "2025-11-11T10:00:00Z",
  "views": 12,
  "avg_completion_rate": 0.73
}

# Response (200 OK) - Generating
{
  "cache_key": "abc123def456",
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "interest": "basketball",
  "status": "generating",
  "progress_percentage": 45,
  "current_stage": "video_generation",
  "stages": {
    "nlu": {"status": "completed", "completed_at": "..."},
    "script": {"status": "completed", "completed_at": "..."},
    "audio": {"status": "completed", "completed_at": "..."},
    "video": {"status": "in_progress", "progress": 45}
  },
  "estimated_completion_seconds": 120,
  "audio_url": "https://cdn.vividly.edu/.../audio.mp3",  // Fast Path available
  "script_url": "https://storage.googleapis.com/.../script.json",
  "created_at": "2025-11-11T10:00:00Z"
}

# Check Content Exists
POST /api/v1/content/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic_id": "topic_phys_mech_newton_3",
  "interest": "basketball"
}

# Response (200 OK) - Cache Hit
{
  "cache_hit": true,
  "cache_key": "abc123def456",
  "status": "completed",
  "video_url": "https://cdn.vividly.edu/.../video.mp4",
  "metadata": {...}
}

# Response (200 OK) - Cache Miss
{
  "cache_hit": false,
  "cache_key": null,
  "message": "Content needs to be generated"
}

# Get Recent Content
GET /api/v1/content/recent?limit=10&topic_id=topic_phys_mech_newton_3
Authorization: Bearer <token>

# Response (200 OK)
{
  "content": [
    {
      "cache_key": "abc123def456",
      "topic_name": "Newton's Third Law",
      "interest": "basketball",
      "thumbnail_url": "...",
      "duration_seconds": 180,
      "generated_at": "2025-11-11T10:00:00Z"
    },
    ...
  ],
  "pagination": {...}
}
```

**Time Estimate**: 1 day

---

##### Story 2.3.2: Content Feedback System (4 points)

**As a** student
**I want to** provide feedback on content
**So that** I can help improve quality and get better content

**Tasks**:
- [ ] Implement `POST /api/v1/content/{cache_key}/feedback`
  - Submit rating (1-5 stars)
  - Submit feedback type (helpful, confusing, inaccurate, etc.)
  - Submit optional comment
  - Track feedback for analytics
- [ ] Implement `GET /api/v1/content/{cache_key}/feedback/summary`
  - Get aggregated feedback stats
  - Average rating
  - Feedback distribution
- [ ] Implement special actions
  - "Make it Simpler" → Queue re-generation with simpler prompt
  - "Try Different Interest" → Allow selecting new interest
  - "Report Issue" → Flag for review
- [ ] Write unit tests (6 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] POST submits feedback successfully
- [x] Prevents duplicate feedback from same user
- [x] Special actions queue appropriate tasks
- [x] Summary calculates correctly
- [x] Test coverage >85%

**API Contract**:
```python
# Submit Feedback
POST /api/v1/content/abc123def456/feedback
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "rating": 4,
  "feedback_type": "helpful",
  "comment": "Great explanation! The basketball analogy made it click.",
  "action": null  // Or "simpler", "different_interest", "report_issue"
}

# Response (201 Created)
{
  "feedback_id": "feedback_001",
  "cache_key": "abc123def456",
  "student_id": "user_abc123",
  "rating": 4,
  "feedback_type": "helpful",
  "submitted_at": "2025-11-11T10:30:00Z",
  "thank_you_message": "Thanks for your feedback! It helps us improve."
}

# Submit Special Action
POST /api/v1/content/abc123def456/feedback
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "action": "simpler",
  "comment": "Too complex for my level"
}

# Response (201 Created)
{
  "feedback_id": "feedback_002",
  "action_taken": "simpler_version_queued",
  "new_cache_key": "xyz789abc123",  // New simpler version
  "status": "generating",
  "estimated_wait_seconds": 180,
  "message": "We're creating a simpler version for you!"
}

# Get Feedback Summary
GET /api/v1/content/abc123def456/feedback/summary
Authorization: Bearer <token>

# Response (200 OK)
{
  "cache_key": "abc123def456",
  "total_feedback": 45,
  "average_rating": 4.2,
  "rating_distribution": {
    "5": 20,
    "4": 15,
    "3": 7,
    "2": 2,
    "1": 1
  },
  "feedback_types": {
    "helpful": 32,
    "confusing": 5,
    "inaccurate": 2,
    "boring": 1,
    "too_fast": 3,
    "too_slow": 2
  },
  "top_comments": [
    {
      "comment": "Great explanation!",
      "rating": 5,
      "helpful_count": 8
    },
    ...
  ]
}
```

**Time Estimate**: 6-8 hours

---

### Sprint 2 Daily Breakdown

#### Monday (Nov 11) - Sprint Planning & Admin Setup

**Morning** (9am-12pm):
- Sprint planning meeting (1 hour)
- Sprint 1 retrospective action items review
- Create feature branches: `feature/admin-service`, `feature/topics-api`

**Afternoon** (1pm-5pm):
- **Engineer 1**: Start Story 2.1.1 (Bulk Upload) - 40% complete
- **Engineer 2**: Start Story 2.2.1 (Topics Discovery) - 50% complete

**Standup Topics**:
- Sprint 1 deployment stable?
- Any tech debt from Sprint 1?
- CSV upload approach decided?

**Daily Goal**: 7 story points started

---

#### Tuesday (Nov 12) - Core Admin & Topics

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 2.1.1 (Bulk Upload) - 80% complete
- **Engineer 2**:
  - Complete Story 2.2.1 (Topics Discovery GET) ✅
  - Start Story 2.2.1 (Topics Search) - 60% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 2.1.1 (Bulk Upload) ✅
  - Start Story 2.1.2 (User Management) - 50% complete
- **Engineer 2**:
  - Complete Story 2.2.1 (Topics Search) ✅
  - Complete Story 2.2.1 (Topics by ID) ✅

**Standup Topics**:
- Bulk upload performance?
- Topics search relevance?
- Database query optimization needed?

**Daily Goal**: 8 story points completed (cumulative: 15)

---

#### Wednesday (Nov 13) - User Management & Content Metadata

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 2.1.2 (User Management CRUD) ✅
  - Start Story 2.1.3 (Account Approval) - 60% complete
- **Engineer 2**:
  - Complete Story 2.2.2 (Interests API) ✅
  - Start Story 2.3.1 (Content Metadata) - 40% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 2.1.3 (Account Approval) ✅
  - Start integration tests for Admin Service
- **Engineer 2**:
  - Complete Story 2.3.1 (Content Metadata) ✅
  - Start Story 2.3.2 (Feedback System) - 50% complete

**Standup Topics**:
- Account approval flow working?
- Content metadata cache strategy?
- Any performance concerns?

**Daily Goal**: 10 story points completed (cumulative: 25)

---

#### Thursday (Nov 14) - Feedback System & Testing

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Admin Service integration tests ✅
  - Code review for Topics/Content APIs
- **Engineer 2**:
  - Complete Story 2.3.2 (Feedback System) ✅
  - Start integration tests for all APIs

**Afternoon** (1pm-5pm):
- **Both Engineers**:
  - Complete all integration tests
  - Update Postman collection
  - API documentation review
  - Performance testing initial run

**Standup Topics**:
- All tests passing?
- Postman collection comprehensive?
- Performance benchmarks met?

**Daily Goal**: 5 story points completed (cumulative: 30)

---

#### Friday (Nov 15) - Sprint Review & Deployment

**Morning** (9am-12pm):
- **Both Engineers**:
  - Final code review
  - Fix any failing tests
  - Deploy to dev environment
  - Smoke testing

**Afternoon** (1pm-3pm):
- End-to-end testing
- Update all documentation
- Prepare demo

**Afternoon** (3pm-5pm):
- Sprint Review (1 hour)
  - Demo bulk upload
  - Demo topics discovery
  - Demo content metadata
  - Show feedback system
- Sprint Retrospective (1 hour)
  - Velocity review (hit 30 points?)
  - Technical challenges
  - Process improvements

**Sprint 2 Deliverables**:
- ✅ Complete Admin Service (13 points)
- ✅ Complete Topics & Interests API (8 points)
- ✅ Complete Content Metadata API (9 points)
- ✅ Updated Postman collection
- ✅ Comprehensive API documentation
- ✅ Test coverage >80%

**Daily Goal**: Finalize sprint (30 points total)

---

### Sprint 2 Success Criteria

**Must Have**:
- [ ] All 30 story points completed
- [ ] Bulk upload handles 1000 users <30s
- [ ] Topics search returns relevant results
- [ ] Content metadata accurate
- [ ] Feedback system functional
- [ ] Test coverage >80%
- [ ] All APIs deployed to dev

**Nice to Have**:
- Performance benchmarks documented
- Cache optimization implemented
- Additional admin reports

---

## Sprint 3: Infrastructure APIs (Week 3)

**Dates**: November 18-22, 2025
**Goal**: Implement caching, content delivery, and notification infrastructure
**Story Points**: 26

### Sprint 3 Objectives

1. ✅ Build intelligent caching system
2. ✅ Implement secure content delivery
3. ✅ Create notification service
4. ✅ Complete Phase 2 integration testing
5. ✅ Prepare for Phase 3 (AI Pipeline)

### Sprint 3 Backlog

#### Epic 3.1: Cache Service (10 points)

**Owner**: Engineer 1
**Priority**: P0 (Critical)
**Dependencies**: Content Metadata API (Sprint 2)

##### Story 3.1.1: Cache Key Generation & Lookup (5 points)

**As a** system
**I want to** efficiently check if content exists in cache
**So that** I can avoid expensive regeneration

**Tasks**:
- [ ] Implement cache key algorithm
  - SHA256 hash of (topic_id | interest | style)
  - Deterministic and consistent
- [ ] Implement `POST /internal/v1/cache/check`
  - Check Redis hot cache (TTL 1 hour)
  - Check GCS cold cache (metadata file)
  - Return cache hit/miss status
  - Track cache statistics
- [ ] Implement cache warming strategy
  - Pre-populate popular topic+interest combinations
  - Background job for cache warming
- [ ] Write unit tests (8 test cases)
- [ ] Write integration tests (3 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Cache key generation is deterministic
- [x] Check returns result in <100ms (p95)
- [x] Redis hot cache working
- [x] GCS cold cache fallback working
- [x] Statistics tracking accurate
- [x] Test coverage >85%

**Cache Architecture**:
```
Check Cache Flow:
1. Generate cache_key = SHA256(topic_id|interest|style)
2. Check Redis (hot cache)
   - If hit: Return metadata (fast path)
3. If miss: Check GCS
   - Look for bucket/cache_key/metadata.json
   - If exists: Warm Redis + return metadata
4. If GCS miss: Return cache miss status

Cache Key Example:
topic_id = "topic_phys_mech_newton_3"
interest = "basketball"
style = "default"
cache_key = SHA256("topic_phys_mech_newton_3|basketball|default")
          = "a3f8d9e2..."
```

**API Contract**:
```python
# Check Cache (Internal API)
POST /internal/v1/cache/check
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "topic_id": "topic_phys_mech_newton_3",
  "interest": "basketball",
  "style": "default"
}

# Response (200 OK) - Cache Hit
{
  "cache_hit": true,
  "cache_key": "a3f8d9e2...",
  "cache_source": "redis",  // "redis" or "gcs"
  "metadata": {
    "status": "completed",
    "video_url": "https://cdn.vividly.edu/.../video.mp4",
    "audio_url": "https://cdn.vividly.edu/.../audio.mp3",
    "script_url": "https://storage.googleapis.com/.../script.json",
    "duration_seconds": 180,
    "generated_at": "2025-11-10T10:00:00Z",
    "views": 12
  }
}

# Response (200 OK) - Cache Miss
{
  "cache_hit": false,
  "cache_key": "a3f8d9e2...",  // Generated for future use
  "message": "Content needs to be generated"
}

# Get Cache Statistics
GET /internal/v1/cache/stats
Authorization: Bearer <service-token>

# Response (200 OK)
{
  "total_requests": 1543,
  "cache_hits": 287,
  "cache_misses": 1256,
  "cache_hit_rate": 0.186,  // 18.6%
  "redis_hits": 245,
  "gcs_hits": 42,
  "avg_lookup_time_ms": 42,
  "cache_size_gb": 1.2,
  "top_cached_topics": [
    {"topic_id": "topic_phys_mech_newton_3", "hits": 45},
    ...
  ]
}
```

**Time Estimate**: 1 day

---

##### Story 3.1.2: Cache Storage & Invalidation (5 points)

**As a** system
**I want to** store generated content in cache
**So that** future requests can be served instantly

**Tasks**:
- [ ] Implement `POST /internal/v1/cache/store`
  - Store metadata in Redis (with TTL)
  - Store metadata in GCS (permanent)
  - Update statistics
- [ ] Implement cache invalidation
  - Manual invalidation endpoint
  - Automatic TTL expiration
  - LRU eviction for Redis
- [ ] Implement cache warming
  - Background job to pre-generate popular content
  - Priority queue for warming
- [ ] Write unit tests (7 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Store operation completes in <200ms
- [x] Redis and GCS stay in sync
- [x] TTL respected (1 hour for hot cache)
- [x] LRU eviction working
- [x] Cache warming effective
- [x] Test coverage >85%

**API Contract**:
```python
# Store in Cache (Internal API)
POST /internal/v1/cache/store
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "cache_key": "a3f8d9e2...",
  "metadata": {
    "topic_id": "topic_phys_mech_newton_3",
    "interest": "basketball",
    "status": "completed",
    "video_url": "https://cdn.vividly.edu/.../video.mp4",
    "audio_url": "https://cdn.vividly.edu/.../audio.mp3",
    "script_url": "https://storage.googleapis.com/.../script.json",
    "duration_seconds": 180,
    "generated_at": "2025-11-18T10:00:00Z"
  }
}

# Response (201 Created)
{
  "cache_key": "a3f8d9e2...",
  "stored_in_redis": true,
  "stored_in_gcs": true,
  "redis_ttl_seconds": 3600,
  "gcs_url": "gs://vividly-mvp-cache/a3f8d9e2.../metadata.json"
}

# Invalidate Cache (Admin API)
DELETE /api/v1/admin/cache/invalidate
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "cache_key": "a3f8d9e2...",
  "reason": "Content update required"
}

# Response (204 No Content)

# Warm Cache (Internal API)
POST /internal/v1/cache/warm
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "topic_ids": ["topic_phys_mech_newton_1", "topic_phys_mech_newton_2"],
  "interests": ["basketball", "football", "soccer"],
  "priority": "high"  // "low", "medium", "high"
}

# Response (202 Accepted)
{
  "job_id": "warming_job_001",
  "total_combinations": 6,
  "estimated_duration_minutes": 18,
  "status": "queued"
}
```

**Time Estimate**: 1 day

---

#### Epic 3.2: Content Delivery Service (8 points)

**Owner**: Engineer 2
**Priority**: P0 (Critical)
**Dependencies**: Cache Service, CDN setup (Phase 1 ✅)

##### Story 3.2.1: Signed URL Generation (5 points)

**As a** system
**I want to** generate secure, time-limited URLs
**So that** content is delivered securely via CDN

**Tasks**:
- [ ] Implement `GET /api/v1/content/{cache_key}/url`
  - Generate signed GCS URL (15-minute TTL)
  - Support different quality levels
  - Support different asset types (video, audio, script)
  - Track content access
- [ ] Implement URL refresh mechanism
  - Auto-refresh before expiration
  - Handle expiration gracefully in frontend
- [ ] Implement CDN cache warming
  - Warm CDN cache on popular content
  - Prefetch for predicted requests
- [ ] Write unit tests (6 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Generates valid signed URLs
- [x] URLs expire after 15 minutes
- [x] Quality selection working
- [x] CDN cache hit rate improving
- [x] Access tracking functional
- [x] Test coverage >85%

**API Contract**:
```python
# Get Content URL
GET /api/v1/content/abc123def456/url?type=video&quality=1080p
Authorization: Bearer <token>

# Response (200 OK)
{
  "cache_key": "abc123def456",
  "asset_type": "video",
  "quality": "1080p",
  "url": "https://cdn.vividly.edu/videos/abc123def456/1080p.mp4?signature=xyz&expires=1234567890",
  "expires_at": "2025-11-18T10:15:00Z",  // 15 minutes from now
  "expires_in_seconds": 900,
  "cdn_cache_status": "HIT",  // "HIT", "MISS", "BYPASS"
  "file_size_bytes": 25600000,
  "duration_seconds": 180
}

# Get Multiple URLs (Batch)
POST /api/v1/content/urls/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "requests": [
    {
      "cache_key": "abc123def456",
      "type": "video",
      "quality": "720p"
    },
    {
      "cache_key": "abc123def456",
      "type": "audio"
    },
    {
      "cache_key": "abc123def456",
      "type": "script"
    }
  ]
}

# Response (200 OK)
{
  "urls": [
    {
      "cache_key": "abc123def456",
      "type": "video",
      "quality": "720p",
      "url": "https://cdn.vividly.edu/...",
      "expires_at": "..."
    },
    {
      "cache_key": "abc123def456",
      "type": "audio",
      "url": "https://cdn.vividly.edu/...",
      "expires_at": "..."
    },
    {
      "cache_key": "abc123def456",
      "type": "script",
      "url": "https://storage.googleapis.com/...",
      "expires_at": "..."
    }
  ]
}
```

**Time Estimate**: 1 day

---

##### Story 3.2.2: Content Access Tracking (3 points)

**As a** system
**I want to** track content views and analytics
**So that** we can measure engagement and improve recommendations

**Tasks**:
- [ ] Implement view tracking
  - Log content access events
  - Track watch duration
  - Track completion rate
- [ ] Implement analytics aggregation
  - Hourly view counts
  - Popular content ranking
  - Student engagement metrics
- [ ] Write unit tests (5 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] View events logged correctly
- [x] Watch duration tracked
- [x] Completion rate calculated
- [x] Analytics aggregation working
- [x] Test coverage >85%

**API Contract**:
```python
# Track View Event (Frontend calls on video start)
POST /api/v1/content/abc123def456/view
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "quality": "1080p",
  "device_type": "desktop",
  "browser": "Chrome"
}

# Response (204 No Content)

# Track Progress (Frontend calls periodically)
POST /api/v1/content/abc123def456/progress
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "current_time_seconds": 120,
  "duration_seconds": 180,
  "playback_speed": 1.0,
  "paused": false
}

# Response (204 No Content)

# Mark Complete (Frontend calls on completion)
POST /api/v1/content/abc123def456/complete
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "watch_duration_seconds": 178,
  "completion_percentage": 98.9,
  "skipped_segments": []
}

# Response (200 OK)
{
  "achievement_unlocked": "First Video Complete",
  "progress_updated": true,
  "streak_days": 4
}
```

**Time Estimate**: 4-6 hours

---

#### Epic 3.3: Notification Service (8 points)

**Owner**: Engineer 1 (parallel with Cache Service)
**Priority**: P1 (High)
**Dependencies**: Email templates (Phase 1 ✅)

##### Story 3.3.1: Email Notification System (5 points)

**As a** system
**I want to** send transactional emails
**So that** users are notified of important events

**Tasks**:
- [ ] Implement SendGrid integration
  - Configure API key
  - Set up sender domain
  - Implement retry logic
- [ ] Implement `POST /internal/v1/notifications/send`
  - Queue email for sending
  - Template rendering
  - Personalization
  - Delivery tracking
- [ ] Implement email templates
  - Welcome emails (student, teacher, admin)
  - Password reset
  - Content ready notification
  - Account request notifications
- [ ] Implement notification queue
  - Redis queue for async sending
  - Rate limiting (avoid spam)
  - Batch sending optimization
- [ ] Write unit tests (7 test cases)
- [ ] Write integration tests (2 flows)
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Emails send successfully
- [x] Templates render correctly
- [x] Delivery tracking working
- [x] Queue handles high volume
- [x] Rate limiting prevents spam
- [x] Test coverage >85%

**API Contract**:
```python
# Send Email (Internal API)
POST /internal/v1/notifications/send
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "type": "email",
  "recipient": {
    "email": "student@mnps.edu",
    "name": "John Doe"
  },
  "template": "content_ready",
  "data": {
    "topic_name": "Newton's Third Law",
    "interest": "basketball",
    "video_url": "https://vividly.edu/content/abc123",
    "thumbnail_url": "https://cdn.vividly.edu/thumbnails/abc123.jpg"
  },
  "priority": "normal"  // "low", "normal", "high"
}

# Response (202 Accepted)
{
  "notification_id": "notif_001",
  "status": "queued",
  "estimated_send_time": "2025-11-18T10:00:30Z"
}

# Get Notification Status
GET /internal/v1/notifications/notif_001/status
Authorization: Bearer <service-token>

# Response (200 OK)
{
  "notification_id": "notif_001",
  "status": "delivered",  // "queued", "sending", "delivered", "failed", "bounced"
  "sent_at": "2025-11-18T10:00:32Z",
  "delivered_at": "2025-11-18T10:00:34Z",
  "opened_at": "2025-11-18T10:05:12Z",  // If tracking enabled
  "clicked_at": "2025-11-18T10:05:45Z"
}

# Batch Send (for bulk operations)
POST /internal/v1/notifications/send/batch
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "notifications": [
    {
      "recipient": {"email": "user1@mnps.edu", "name": "User 1"},
      "template": "welcome_student",
      "data": {...}
    },
    {
      "recipient": {"email": "user2@mnps.edu", "name": "User 2"},
      "template": "welcome_student",
      "data": {...}
    },
    ...
  ]
}

# Response (202 Accepted)
{
  "batch_id": "batch_001",
  "total_notifications": 100,
  "status": "queued",
  "estimated_completion_time": "2025-11-18T10:05:00Z"
}
```

**Implementation Details**:

```python
# backend/app/services/notification_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Environment, FileSystemLoader
import redis

class NotificationService:
    def __init__(self, sendgrid_api_key: str, redis_client):
        self.client = SendGridAPIClient(sendgrid_api_key)
        self.redis = redis_client
        self.template_env = Environment(
            loader=FileSystemLoader("app/email_templates")
        )

    async def send_email(
        self,
        recipient_email: str,
        recipient_name: str,
        template_name: str,
        template_data: dict,
        priority: str = "normal"
    ):
        """Send email notification."""

        # Render template
        template = self.template_env.get_template(f"{template_name}.html")
        html_content = template.render(**template_data)

        # Create message
        message = Mail(
            from_email="noreply@vividly.edu",
            to_emails=recipient_email,
            subject=self._get_subject(template_name),
            html_content=html_content
        )

        # Add to queue for async sending
        notification_id = self._queue_email(message, priority)

        return notification_id

    def _queue_email(self, message, priority):
        """Add email to Redis queue for async processing."""
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"

        queue_name = f"email_queue:{priority}"

        self.redis.lpush(queue_name, json.dumps({
            "notification_id": notification_id,
            "message": message.get(),
            "queued_at": datetime.utcnow().isoformat()
        }))

        return notification_id

    async def process_queue(self):
        """Background worker to process email queue."""
        while True:
            # Process high priority first
            for priority in ["high", "normal", "low"]:
                queue_name = f"email_queue:{priority}"

                # Get batch of emails
                emails = self.redis.rpop(queue_name, count=10)

                if emails:
                    await self._send_batch(emails)

            await asyncio.sleep(1)

    async def _send_batch(self, emails):
        """Send batch of emails with rate limiting."""
        for email_data in emails:
            try:
                response = self.client.send(email_data["message"])
                self._update_status(
                    email_data["notification_id"],
                    "delivered"
                )
            except Exception as e:
                logger.error(f"Email send failed: {e}")
                self._update_status(
                    email_data["notification_id"],
                    "failed"
                )

            # Rate limiting: 100 emails/second max
            await asyncio.sleep(0.01)
```

**Time Estimate**: 1 day

---

##### Story 3.3.2: Real-Time Notifications (3 points)

**As a** student
**I want to** be notified in real-time when content is ready
**So that** I don't have to keep refreshing

**Tasks**:
- [ ] Implement polling endpoint
  - `GET /api/v1/notifications/poll`
  - Return unread notifications
  - Mark as read
- [ ] Implement notification types
  - Content ready (Fast Path, Full Path)
  - Account approved
  - Teacher messages
- [ ] Write unit tests (5 test cases)
- [ ] Write integration test
- [ ] Update API docs

**Acceptance Criteria**:
- [x] Polling works efficiently
- [x] Notifications marked as read
- [x] All notification types supported
- [x] Test coverage >85%

**API Contract**:
```python
# Poll for Notifications
GET /api/v1/notifications/poll?since=2025-11-18T10:00:00Z
Authorization: Bearer <token>

# Response (200 OK)
{
  "notifications": [
    {
      "notification_id": "notif_123",
      "type": "content_ready",
      "title": "Your video is ready!",
      "message": "Newton's Third Law (Basketball) is ready to watch",
      "data": {
        "cache_key": "abc123def456",
        "topic_name": "Newton's Third Law",
        "video_url": "https://vividly.edu/content/abc123"
      },
      "created_at": "2025-11-18T10:03:00Z",
      "read": false
    },
    ...
  ],
  "unread_count": 3,
  "has_more": false
}

# Mark as Read
PUT /api/v1/notifications/notif_123/read
Authorization: Bearer <token>

# Response (204 No Content)

# Mark All as Read
PUT /api/v1/notifications/read-all
Authorization: Bearer <token>

# Response (204 No Content)
```

**Time Estimate**: 4-6 hours

---

### Sprint 3 Daily Breakdown

#### Monday (Nov 18) - Sprint Planning & Cache Setup

**Morning** (9am-12pm):
- Sprint planning (1 hour)
- Sprint 2 retrospective action items
- Create feature branches: `feature/cache-service`, `feature/content-delivery`

**Afternoon** (1pm-5pm):
- **Engineer 1**: Start Story 3.1.1 (Cache Key & Lookup) - 60% complete
- **Engineer 2**: Start Story 3.2.1 (Signed URLs) - 50% complete

**Daily Goal**: 7 story points started

---

#### Tuesday (Nov 19) - Core Infrastructure

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 3.1.1 (Cache Key & Lookup) ✅
  - Start Story 3.1.2 (Cache Storage) - 40% complete
- **Engineer 2**:
  - Complete Story 3.2.1 (Signed URLs) ✅
  - Start Story 3.2.2 (Access Tracking) - 70% complete

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 3.1.2 (Cache Storage) ✅
  - Start Story 3.3.1 (Email Notifications) - 30% complete
- **Engineer 2**:
  - Complete Story 3.2.2 (Access Tracking) ✅
  - Start Story 3.3.2 (Real-Time Notifications) - 50% complete

**Daily Goal**: 13 story points completed (cumulative: 20)

---

#### Wednesday (Nov 20) - Notifications & Testing

**Morning** (9am-12pm):
- **Engineer 1**:
  - Complete Story 3.3.1 (Email Notifications) - 80% complete
- **Engineer 2**:
  - Complete Story 3.3.2 (Real-Time Notifications) ✅
  - Start integration tests

**Afternoon** (1pm-5pm):
- **Engineer 1**:
  - Complete Story 3.3.1 (Email Notifications) ✅
  - Start integration tests for Cache Service
- **Engineer 2**:
  - Complete Content Delivery integration tests ✅
  - Update Postman collection

**Daily Goal**: 8 story points completed (cumulative: 28)

---

#### Thursday (Nov 21) - Phase 2 Integration Testing

**Morning** (9am-12pm):
- **Both Engineers**:
  - Complete all unit tests
  - Complete all integration tests
  - End-to-end testing (full user flows)

**Afternoon** (1pm-5pm):
- **Both Engineers**:
  - Performance testing
  - Load testing (100 concurrent users)
  - Fix any issues
  - Update all documentation

**Daily Goal**: Complete all testing

---

#### Friday (Nov 22) - Phase 2 Completion & Demo

**Morning** (9am-12pm):
- **Both Engineers**:
  - Final code review
  - Deploy all services to dev
  - Smoke testing
  - Prepare comprehensive demo

**Afternoon** (1pm-3pm):
- **Phase 2 Demo** (1.5 hours)
  - Demo all 3 sprints
  - Show complete API functionality
  - Performance metrics
  - Test coverage report

**Afternoon** (3pm-5pm):
- **Phase 2 Retrospective** (1 hour)
  - Review 3-sprint velocity
  - Technical learnings
  - Process improvements
- **Phase 3 Planning** (1 hour)
  - Review Phase 3 scope
  - Identify dependencies
  - Create initial backlog

**Phase 2 Complete Deliverables**:
- ✅ All 28 API endpoints functional
- ✅ Test coverage >80%
- ✅ Complete Postman collection
- ✅ Comprehensive API documentation
- ✅ All services deployed to dev
- ✅ Performance benchmarks met
- ✅ Ready for Phase 3 (AI Pipeline)

**Daily Goal**: Complete Phase 2 (84 points total)

---

### Sprint 3 Success Criteria

**Must Have**:
- [ ] All 26 story points completed
- [ ] Cache service <100ms lookup time
- [ ] Signed URLs working with CDN
- [ ] Email notifications sending
- [ ] Real-time polling functional
- [ ] Test coverage >80%
- [ ] All services deployed

**Phase 2 Complete**:
- [ ] 84 story points completed across 3 sprints
- [ ] All backend APIs functional
- [ ] Comprehensive testing done
- [ ] Documentation complete
- [ ] Ready for Phase 3

---

## Risk Management

### Sprint-Level Risks

#### Risk 1: Velocity Deviation
**Risk**: Team velocity lower than planned (28-30 points/sprint)

**Mitigation**:
- Daily standup to identify blockers early
- Mid-sprint check-in (Wednesday)
- Buffer in Sprint 3 (26 points vs 30)
- Prioritize P0 stories first
- Defer nice-to-have features

**Contingency**: If falling behind, defer P1 stories to Phase 3

---

#### Risk 2: Integration Issues
**Risk**: Services don't integrate smoothly

**Mitigation**:
- Integration tests from day 1
- API contracts defined upfront
- Mock services for parallel development
- Daily smoke tests
- Postman collection for validation

**Contingency**: Extra integration day if needed (buffer in Sprint 3)

---

#### Risk 3: Database Performance
**Risk**: Slow queries impact API response times

**Mitigation**:
- Database indexes in Sprint 1
- Query optimization from start
- Monitor query performance
- Use EXPLAIN ANALYZE
- Connection pooling configured

**Contingency**: Mid-sprint optimization session if needed

---

#### Risk 4: Test Coverage Gaps
**Risk**: Tests don't catch critical bugs

**Mitigation**:
- TDD approach (write tests first)
- Code review checks coverage
- Integration tests for user flows
- Edge case testing
- pytest-cov monitoring

**Contingency**: Friday buffer for additional testing

---

### Technical Dependencies

#### External Services Needed

**Before Sprint 1**:
- [x] Database migrations executed (tonight)
- [x] Redis running in dev environment
- [x] Auth middleware verified

**Before Sprint 2**:
- [ ] Topics data seeded in database
- [ ] Interests data seeded
- [ ] Test schools/users created

**Before Sprint 3**:
- [ ] GCS buckets configured
- [ ] CDN enabled and tested
- [ ] SendGrid account setup (or use logging for MVP)
- [ ] Redis queues configured

---

## Quality Gates

### Code Review Checklist

Every PR must pass:
- [ ] Code follows style guide (Black, isort)
- [ ] All tests passing
- [ ] Coverage >80% for new code
- [ ] No security vulnerabilities (Bandit)
- [ ] API docs updated
- [ ] Postman collection updated
- [ ] No TODOs or FIXMEs
- [ ] Performance acceptable (<500ms APIs)
- [ ] Approved by 1 other engineer

---

### Definition of Done (Sprint-Level)

A sprint is complete when:
- [ ] All committed story points delivered
- [ ] All tests passing (unit + integration)
- [ ] Test coverage >80%
- [ ] Code reviewed and merged
- [ ] API documentation complete
- [ ] Postman collection updated
- [ ] Deployed to dev environment
- [ ] Smoke tests passing
- [ ] Demo prepared
- [ ] Sprint retrospective completed

---

### Definition of Done (Phase 2)

Phase 2 is complete when:
- [ ] All 84 story points delivered
- [ ] All 28+ API endpoints functional
- [ ] Test coverage >80% overall
- [ ] Complete Postman collection (all endpoints)
- [ ] Comprehensive API documentation
- [ ] All services deployed to dev
- [ ] End-to-end user flows working
- [ ] Performance benchmarks met (<500ms APIs)
- [ ] Load testing passed (100 concurrent users)
- [ ] Security audit clean (no critical issues)
- [ ] Phase 2 demo completed
- [ ] Phase 3 backlog prepared

---

## Success Metrics

### Sprint Velocity

| Sprint | Planned | Actual | Notes |
|--------|---------|--------|-------|
| Sprint 1 | 28 | TBD | Foundation APIs |
| Sprint 2 | 30 | TBD | Management APIs |
| Sprint 3 | 26 | TBD | Infrastructure APIs |
| **Total** | **84** | **TBD** | |

**Velocity Target**: 28 ± 3 points per sprint

---

### API Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time (p50) | <200ms | Cloud Monitoring |
| Response Time (p95) | <500ms | Cloud Monitoring |
| Response Time (p99) | <1000ms | Cloud Monitoring |
| Error Rate | <1% | Sentry + Logs |
| Throughput | >100 req/s | Load testing |

---

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage (Backend) | >80% | pytest-cov |
| Test Coverage (Unit) | >85% | pytest-cov |
| Test Coverage (Integration) | >70% | pytest-cov |
| Code Review Time | <4 hours | GitHub metrics |
| Bug Escape Rate | <5% | Issue tracking |
| Security Vulnerabilities | 0 critical | Bandit, Snyk |

---

### Completion Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Story Points Completed | 84 | 0 / 84 (0%) |
| API Endpoints Delivered | 28+ | 0 / 28 (0%) |
| Integration Tests | 20+ | 0 / 20 (0%) |
| API Documentation | 100% | 0% |
| Postman Collection | 100% | 0% |

---

## Daily Standup Template

### Format (15 minutes max)

Each engineer answers:
1. **Yesterday**: What did you complete?
2. **Today**: What will you work on?
3. **Blockers**: Any impediments?

### Example

**Engineer 1** (Monday, Sprint 1):
- **Yesterday**: Sprint planning, setup feature branch
- **Today**: Complete Story 1.1.1 (Registration endpoint)
- **Blockers**: None

**Engineer 2** (Monday, Sprint 1):
- **Yesterday**: Sprint planning, reviewed auth middleware
- **Today**: Complete Student Profile GET endpoint
- **Blockers**: Need clarification on interest selection limits

**Action Items**:
- [ ] Clarify interest limits (1-5) - Product Owner
- [ ] Review database indexes - Engineer 1

---

## Sprint Retrospective Template

### Format (1 hour)

1. **What went well?** (15 min)
   - Celebrate wins
   - Note good practices to continue

2. **What could be improved?** (20 min)
   - Identify pain points
   - Discuss process issues
   - Technical challenges

3. **Action items** (20 min)
   - Concrete improvements for next sprint
   - Assign owners
   - Set deadlines

4. **Velocity review** (5 min)
   - Did we hit our target?
   - Adjust estimates if needed

### Example (Sprint 1 Retrospective)

**What went well**:
- ✅ Authentication API completed ahead of schedule
- ✅ Good test coverage from the start
- ✅ Daily standups kept team aligned
- ✅ Code reviews caught issues early

**What could be improved**:
- ⚠️ Integration testing took longer than expected
- ⚠️ Some API contracts changed mid-sprint
- ⚠️ Postman collection not updated daily

**Action items**:
- [ ] Start integration tests earlier (Day 2 vs Day 4)
- [ ] Lock API contracts before implementation
- [ ] Update Postman collection daily (end of day)
- [ ] Add more unit test examples to docs

**Velocity**:
- Planned: 28 points
- Actual: 28 points ✅
- Next sprint: Keep 30 points target

---

## Tools & Resources

### Development Tools

| Tool | Purpose | URL |
|------|---------|-----|
| GitHub | Code repository | (to be created) |
| Postman | API testing | (workspace to be created) |
| FastAPI Docs | Auto-generated API docs | http://localhost:8080/docs |
| Adminer | Database UI | http://localhost:8082 |
| Redis Commander | Redis UI | http://localhost:8083 |
| pytest-cov | Test coverage | Run: `pytest --cov=app` |

### Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| API Specification | `/API_SPECIFICATION.md` | API contracts |
| Database Schema | `/DATABASE_SCHEMA.md` | DB structure |
| Development Setup | `/DEVELOPMENT_SETUP.md` | Local dev guide |
| Testing Strategy | `/TESTING_STRATEGY.md` | Test approach |
| Phase 2 Sprint Plan | `/PHASE_2_SPRINT_PLAN.md` | This document |

### Communication

- **Daily Standup**: 9:00 AM (15 min)
- **Sprint Review**: Friday 3:00 PM (1 hour)
- **Sprint Retro**: Friday 4:00 PM (1 hour)
- **Sprint Planning**: Monday 9:00 AM (1 hour)
- **Code Review**: As needed (async)
- **Pair Programming**: As needed (ad hoc)

---

## Appendix

### A. Story Point Estimation Reference

**1 Point** (1-2 hours):
- Simple schema definition
- Basic CRUD endpoint (no logic)
- Simple validation rule
- Update existing endpoint

**2 Points** (2-4 hours):
- Standard API endpoint with validation
- Database query with joins
- Unit tests for one feature
- API documentation update

**3 Points** (4-6 hours):
- Complex endpoint with business logic
- Multiple database operations
- Integration test for flow
- Error handling and edge cases

**5 Points** (1 day):
- Complete service with multiple endpoints
- Complex business logic
- Comprehensive testing
- Full API documentation

**8 Points** (1.5-2 days):
- Major feature with integrations
- External service integration
- Performance optimization
- Complete test suite

**13 Points** (2-3 days):
- Epic-level feature
- Multiple services involved
- Extensive testing
- Documentation and examples

---

### B. API Testing Checklist

For each endpoint, test:
- [ ] Happy path (200/201 response)
- [ ] Invalid input (422 Validation Error)
- [ ] Unauthorized (401 if auth required)
- [ ] Forbidden (403 if RBAC enforced)
- [ ] Not found (404 for resources)
- [ ] Rate limiting (429 if applicable)
- [ ] Server error handling (500)
- [ ] Edge cases (empty, null, extreme values)
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] Performance (<500ms for p95)

---

### C. Git Workflow

**Branch Naming**:
- `feature/auth-api` - New features
- `bugfix/login-error` - Bug fixes
- `hotfix/security-patch` - Urgent fixes

**Commit Messages**:
```
feat(auth): Add user registration endpoint

- Implement POST /api/v1/auth/register
- Add email and password validation
- Hash passwords with bcrypt
- Add unit tests (coverage: 87%)

Closes #42
```

**PR Template**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] Postman collection updated

## Checklist
- [ ] Code follows style guide
- [ ] Tests passing
- [ ] Coverage >80%
- [ ] API docs updated
- [ ] No security issues

## Screenshots (if applicable)

## Related Issues
Closes #42
```

---

## Conclusion

This comprehensive sprint plan provides a detailed roadmap for Phase 2: Core Backend Services. With 3 one-week sprints and clear daily breakdowns, the team can systematically build all API endpoints needed for the MVP.

**Key Success Factors**:
- Clear story definitions with acceptance criteria
- Realistic velocity targets (28-30 points/sprint)
- Built-in buffers and contingencies
- Quality gates at every level
- Comprehensive testing strategy
- Daily tracking and adjustment

**Next Steps**:
1. ✅ Run database migrations tonight
2. ✅ Seed test data (Sprint 2 prep)
3. ⏳ Start Sprint 1 on November 4, 2025

With this plan, Phase 2 will deliver all backend services in 3 weeks, setting the foundation for Phase 3 (AI Content Pipeline).

---

**Document Control**:
- **Author**: Technical Lead
- **Date**: October 28, 2025
- **Version**: 1.0
- **Status**: Ready to Execute
- **Next Update**: After Sprint 1 completion
