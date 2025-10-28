# Vividly API Specification

**Version:** 1.0.0
**Base URL:** `https://api.vividly.education`
**Protocol:** HTTPS only
**Authentication:** Bearer JWT
**Content-Type:** `application/json`

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Authentication Endpoints](#authentication-endpoints)
7. [Student Endpoints](#student-endpoints)
8. [Teacher Endpoints](#teacher-endpoints)
9. [Admin Endpoints](#admin-endpoints)
10. [Internal Service Endpoints](#internal-service-endpoints)
11. [Webhook Endpoints](#webhook-endpoints)

---

## Overview

The Vividly API follows RESTful principles with JSON request/response bodies. All endpoints require authentication except for the login endpoint.

### API Versioning

- Version is specified in the URL path: `/api/v1/`
- Breaking changes will increment the major version
- Backward-compatible changes maintain the current version

### Base Endpoints by Service

```
Authentication:  /api/v1/auth/*
Students:        /api/v1/students/*
Teachers:        /api/v1/teachers/*
Admins:          /api/v1/admin/*
Internal:        /internal/v1/*  (not exposed publicly)
```

---

## Authentication

### JWT Token Structure

All authenticated requests must include a Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### JWT Payload

```json
{
  "iss": "vividly-mvp",
  "sub": "user_12345",
  "user_id": "user_12345",
  "role": "student",
  "org_id": "org_mnps",
  "school_id": "school_hillsboro_hs",
  "email": "student@mnps.edu",
  "exp": 1730156400,
  "iat": 1730070000
}
```

### Role-Based Access

| Role | Code | Access |
|------|------|--------|
| Student | `student` | Own profile, content requests, progress |
| Teacher | `teacher` | Own classes, student progress, account requests |
| School Admin | `school_admin` | School-level management, teacher accounts |
| District Admin | `district_admin` | District-level management, all accounts |
| Vividly Admin | `vividly_admin` | Full system access |
| Vividly Ops | `vividly_ops` | Read-only system access |

---

## Common Patterns

### Pagination

List endpoints support pagination using cursor-based pagination:

**Request:**
```
GET /api/v1/teachers/students?limit=20&cursor=eyJpZCI6MTIzfQ
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true,
    "total_count": 150
  }
}
```

### Timestamps

- All timestamps are in ISO 8601 format with UTC timezone
- Example: `2025-10-27T14:30:00Z`

### IDs

- All resource IDs are prefixed strings: `user_abc123`, `topic_phys_001`
- UUIDs used internally, exposed as prefixed strings externally

---

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The topic_id field is required",
    "details": {
      "field": "topic_id",
      "reason": "missing_field"
    },
    "request_id": "req_7f8d9e1a2b3c"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request or invalid parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource already exists or state conflict |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Temporary service outage |

---

## Rate Limiting

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1730070600
```

### Limits by Role

| Role | Requests per Minute | Burst |
|------|---------------------|-------|
| Student | 60 | 10 |
| Teacher | 120 | 20 |
| Admin | 300 | 50 |
| Vividly Staff | 1000 | 100 |

---

## Authentication Endpoints

### POST /api/v1/auth/login

Authenticate user and receive JWT token.

**Request:**
```json
{
  "email": "student@mnps.edu",
  "password": "SecureP@ssw0rd"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "user_12345",
    "email": "student@mnps.edu",
    "role": "student",
    "first_name": "Jane",
    "last_name": "Doe",
    "school_id": "school_hillsboro_hs"
  }
}
```

**Errors:**
- `401 UNAUTHORIZED`: Invalid credentials
- `429 RATE_LIMIT_EXCEEDED`: Too many login attempts

---

### POST /api/v1/auth/logout

Invalidate current JWT token (future: token blacklist).

**Request:** Empty body

**Response:** `204 No Content`

---

### POST /api/v1/auth/refresh

Refresh an expiring JWT token (future feature).

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400
}
```

---

## Student Endpoints

### POST /api/v1/students/content/request

Request personalized content for a topic.

**Authorization:** `student`

**Request:**
```json
{
  "query": "Can you explain Newton's third law?",
  "interest_id": "int_basketball",
  "style": "conversational"
}
```

**Response:** `202 Accepted` (Async processing)
```json
{
  "request_id": "req_7f8d9e1a",
  "status": "processing",
  "estimated_time_seconds": 8,
  "message": "We're generating your personalized lesson. You'll see the script and audio shortly!"
}
```

**Polling Endpoint:** `GET /api/v1/students/content/status/{request_id}`

---

### POST /api/v1/students/content/clarify

Respond to clarification question from NLU.

**Authorization:** `student`

**Request:**
```json
{
  "request_id": "req_7f8d9e1a",
  "selected_option": "option_2",
  "options": [
    {
      "id": "option_1",
      "topic_id": "topic_phys_newton_1",
      "title": "Newton's First Law (Inertia)"
    },
    {
      "id": "option_2",
      "topic_id": "topic_phys_newton_3",
      "title": "Newton's Third Law (Action-Reaction)"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "request_id": "req_7f8d9e1a",
  "topic_id": "topic_phys_newton_3",
  "status": "processing"
}
```

---

### GET /api/v1/students/content/status/{request_id}

Check status of content generation request.

**Authorization:** `student`

**Response (Processing):** `200 OK`
```json
{
  "request_id": "req_7f8d9e1a",
  "status": "processing",
  "stage": "generating_audio",
  "progress_percent": 60,
  "estimated_completion": "2025-10-27T14:32:00Z"
}
```

**Response (Fast Path Ready):** `200 OK`
```json
{
  "request_id": "req_7f8d9e1a",
  "status": "fast_path_ready",
  "content": {
    "type": "vivid_now",
    "topic_id": "topic_phys_newton_3",
    "topic_title": "Newton's Third Law of Motion",
    "script": {
      "url": "https://storage.googleapis.com/.../script.json",
      "text_preview": "Imagine you're playing basketball..."
    },
    "audio": {
      "url": "https://storage.googleapis.com/.../audio.mp3",
      "duration_seconds": 180
    },
    "video_status": "generating"
  }
}
```

**Response (Full Experience Ready):** `200 OK`
```json
{
  "request_id": "req_7f8d9e1a",
  "status": "completed",
  "content": {
    "type": "vivid_learning",
    "topic_id": "topic_phys_newton_3",
    "topic_title": "Newton's Third Law of Motion",
    "video": {
      "url": "https://storage.googleapis.com/.../video.mp4",
      "duration_seconds": 180,
      "thumbnail_url": "https://storage.googleapis.com/.../thumb.jpg"
    },
    "script": {
      "url": "https://storage.googleapis.com/.../script.json"
    }
  }
}
```

**Errors:**
- `404 NOT_FOUND`: Request ID not found or expired

---

### POST /api/v1/students/feedback

Submit feedback on generated content.

**Authorization:** `student`

**Request:**
```json
{
  "content_id": "content_abc123",
  "feedback_type": "mark_complete",
  "rating": 5,
  "comment": "This helped me understand the concept!"
}
```

**Feedback Types:**
- `mark_complete`: Student understood the content
- `make_simpler`: Content too complex
- `try_different_interest`: Interest didn't resonate
- `report_issue`: Content error or inappropriate

**Response:** `201 Created`
```json
{
  "feedback_id": "feedback_xyz789",
  "status": "recorded",
  "next_action": null
}
```

**Response (Re-generation Triggered):** `201 Created`
```json
{
  "feedback_id": "feedback_xyz789",
  "status": "recorded",
  "next_action": {
    "type": "regenerate",
    "request_id": "req_8g9h0f2b",
    "message": "We're creating a simpler version for you!"
  }
}
```

---

### GET /api/v1/students/profile

Get student profile and preferences.

**Authorization:** `student`

**Response:** `200 OK`
```json
{
  "id": "user_12345",
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@mnps.edu",
  "grade_level": 10,
  "school": {
    "id": "school_hillsboro_hs",
    "name": "Hillsboro High School"
  },
  "interests": [
    {
      "id": "int_basketball",
      "name": "Basketball",
      "rank": 1
    },
    {
      "id": "int_music_production",
      "name": "Music Production",
      "rank": 2
    },
    {
      "id": "int_video_games",
      "name": "Video Games",
      "rank": 3
    }
  ],
  "preferred_style": "conversational",
  "statistics": {
    "total_videos_watched": 12,
    "topics_completed": 8,
    "streak_days": 3
  }
}
```

---

### PUT /api/v1/students/profile/interests

Update student interest rankings.

**Authorization:** `student`

**Request:**
```json
{
  "interests": [
    {
      "id": "int_basketball",
      "rank": 1
    },
    {
      "id": "int_music_production",
      "rank": 2
    },
    {
      "id": "int_robotics",
      "rank": 3
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "message": "Interests updated successfully",
  "interests": [...]
}
```

**Errors:**
- `422 VALIDATION_ERROR`: Invalid interest IDs or duplicate ranks

---

### GET /api/v1/students/progress

Get student learning progress.

**Authorization:** `student`

**Query Parameters:**
- `subject` (optional): Filter by subject (e.g., `physics`, `math`)

**Response:** `200 OK`
```json
{
  "overall_progress": {
    "total_topics": 120,
    "completed_topics": 8,
    "in_progress_topics": 3,
    "completion_percentage": 6.7
  },
  "by_subject": [
    {
      "subject": "Physics",
      "subject_id": "subj_physics",
      "total_topics": 60,
      "completed": 5,
      "in_progress": 2
    },
    {
      "subject": "Mathematics",
      "subject_id": "subj_math",
      "total_topics": 60,
      "completed": 3,
      "in_progress": 1
    }
  ],
  "recent_topics": [
    {
      "topic_id": "topic_phys_newton_3",
      "title": "Newton's Third Law",
      "status": "completed",
      "completed_at": "2025-10-26T10:15:00Z",
      "content_url": "https://storage.googleapis.com/.../video.mp4"
    }
  ]
}
```

---

### GET /api/v1/students/history

Get student's content viewing history.

**Authorization:** `student`

**Query Parameters:**
- `limit` (default: 20, max: 100)
- `cursor` (pagination cursor)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "history_h1i2j3",
      "topic_id": "topic_phys_newton_3",
      "topic_title": "Newton's Third Law",
      "interest_used": "Basketball",
      "content_type": "vivid_learning",
      "watched_at": "2025-10-26T10:15:00Z",
      "completed": true,
      "rating": 5
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true
  }
}
```

---

## Teacher Endpoints

### GET /api/v1/teachers/classes

Get list of teacher's classes.

**Authorization:** `teacher`

**Response:** `200 OK`
```json
{
  "classes": [
    {
      "id": "class_abc123",
      "name": "Physics - Period 3",
      "grade_level": 10,
      "subject": "Physics",
      "student_count": 24,
      "created_at": "2025-08-15T09:00:00Z"
    },
    {
      "id": "class_def456",
      "name": "Physics - Period 5",
      "grade_level": 11,
      "subject": "Physics",
      "student_count": 22,
      "created_at": "2025-08-15T09:00:00Z"
    }
  ]
}
```

---

### POST /api/v1/teachers/classes

Create a new class.

**Authorization:** `teacher`

**Request:**
```json
{
  "name": "Physics - Period 3",
  "grade_level": 10,
  "subject": "Physics",
  "school_year": "2025-2026"
}
```

**Response:** `201 Created`
```json
{
  "id": "class_abc123",
  "name": "Physics - Period 3",
  "grade_level": 10,
  "subject": "Physics",
  "student_count": 0,
  "invite_code": "JOIN-ABC123"
}
```

---

### GET /api/v1/teachers/classes/{class_id}/students

Get students in a class with engagement metrics.

**Authorization:** `teacher` (must own class)

**Response:** `200 OK`
```json
{
  "class": {
    "id": "class_abc123",
    "name": "Physics - Period 3"
  },
  "students": [
    {
      "id": "user_12345",
      "name": "Jane Doe",
      "email": "jane.doe@mnps.edu",
      "last_active": "2025-10-27T14:30:00Z",
      "engagement": {
        "total_videos_watched": 12,
        "topics_completed": 8,
        "last_7_days_activity": 5,
        "engagement_score": 85
      }
    }
  ]
}
```

---

### GET /api/v1/teachers/students/{student_id}/progress

Get detailed progress for a specific student.

**Authorization:** `teacher` (must have student in their class)

**Response:** `200 OK`
```json
{
  "student": {
    "id": "user_12345",
    "name": "Jane Doe"
  },
  "progress": {
    "overall_completion": 6.7,
    "topics_completed": 8,
    "topics_in_progress": 3,
    "total_time_minutes": 240,
    "average_rating": 4.6
  },
  "recent_activity": [
    {
      "topic_id": "topic_phys_newton_3",
      "topic_title": "Newton's Third Law",
      "completed_at": "2025-10-26T10:15:00Z",
      "rating": 5,
      "feedback": "mark_complete"
    }
  ],
  "struggling_topics": [
    {
      "topic_id": "topic_math_quadratic",
      "topic_title": "Quadratic Equations",
      "attempts": 3,
      "completed": false,
      "feedback_given": ["make_simpler", "try_different_interest"]
    }
  ]
}
```

---

### POST /api/v1/teachers/student-requests

Request creation of a new student account.

**Authorization:** `teacher`

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@mnps.edu",
  "grade_level": 10,
  "student_id": "123456",
  "class_id": "class_abc123",
  "justification": "New transfer student joining mid-semester"
}
```

**Response:** `201 Created`
```json
{
  "request_id": "sreq_xyz789",
  "status": "pending_approval",
  "submitted_at": "2025-10-27T14:35:00Z",
  "approver": "school_admin",
  "estimated_response_time": "1-2 business days"
}
```

---

### GET /api/v1/teachers/student-requests

Get list of student account requests made by teacher.

**Authorization:** `teacher`

**Query Parameters:**
- `status` (optional): `pending`, `approved`, `denied`

**Response:** `200 OK`
```json
{
  "requests": [
    {
      "id": "sreq_xyz789",
      "student_name": "John Smith",
      "email": "john.smith@mnps.edu",
      "status": "pending_approval",
      "submitted_at": "2025-10-27T14:35:00Z",
      "reviewed_by": null,
      "reviewed_at": null
    }
  ]
}
```

---

## Admin Endpoints

### POST /api/v1/admin/users/bulk-upload

Bulk upload students via CSV.

**Authorization:** `district_admin` or `school_admin`

**Request:** `multipart/form-data`
```
POST /api/v1/admin/users/bulk-upload
Content-Type: multipart/form-data

file: [CSV file]
school_id: school_hillsboro_hs
auto_activate: true
```

**CSV Format:**
```csv
student_id,first_name,last_name,email,grade_level
123456,Jane,Doe,jane.doe@mnps.edu,10
123457,John,Smith,john.smith@mnps.edu,11
```

**Response:** `202 Accepted`
```json
{
  "job_id": "upload_job_abc123",
  "status": "processing",
  "total_rows": 150,
  "message": "Upload is being processed. Check status endpoint for progress."
}
```

**Status Check:** `GET /api/v1/admin/jobs/{job_id}`

---

### GET /api/v1/admin/jobs/{job_id}

Check status of bulk upload job.

**Authorization:** `district_admin` or `school_admin`

**Response:** `200 OK`
```json
{
  "job_id": "upload_job_abc123",
  "status": "completed",
  "total_rows": 150,
  "successful": 148,
  "failed": 2,
  "errors": [
    {
      "row": 42,
      "email": "invalid@email",
      "error": "Invalid email format"
    },
    {
      "row": 89,
      "email": "duplicate@mnps.edu",
      "error": "Student already exists"
    }
  ],
  "completed_at": "2025-10-27T14:40:00Z"
}
```

---

### GET /api/v1/admin/kpis

Get KPI dashboard data.

**Authorization:** `district_admin`, `school_admin`, `teacher`

**Query Parameters:**
- `scope`: `district`, `school`, `class`
- `scope_id`: ID of the scope (school_id or class_id)
- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)

**Response:** `200 OK`
```json
{
  "period": {
    "from": "2025-09-01T00:00:00Z",
    "to": "2025-10-27T23:59:59Z"
  },
  "scope": {
    "type": "school",
    "id": "school_hillsboro_hs",
    "name": "Hillsboro High School"
  },
  "kpis": {
    "teacher_adoption_rate": {
      "value": 52.5,
      "target": 50.0,
      "status": "on_track",
      "total_teachers": 40,
      "active_teachers": 21
    },
    "student_activation_rate": {
      "value": 34.2,
      "target": 30.0,
      "status": "exceeding",
      "total_students": 480,
      "active_students": 164
    },
    "student_engagement": {
      "avg_videos_per_student": 3.4,
      "target": 3.0,
      "status": "on_track",
      "total_videos_watched": 557
    },
    "cache_hit_rate": {
      "value": 18.5,
      "target": 15.0,
      "status": "exceeding",
      "total_requests": 557,
      "cache_hits": 103
    }
  },
  "trends": {
    "weekly_active_students": [
      {"week": "2025-10-06", "count": 145},
      {"week": "2025-10-13", "count": 158},
      {"week": "2025-10-20", "count": 164}
    ]
  }
}
```

---

### GET /api/v1/admin/pending-requests

Get pending student account requests.

**Authorization:** `school_admin`, `district_admin`

**Query Parameters:**
- `school_id` (optional for district admin)

**Response:** `200 OK`
```json
{
  "requests": [
    {
      "id": "sreq_xyz789",
      "teacher": {
        "id": "user_teach_001",
        "name": "Ms. Johnson"
      },
      "student": {
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@mnps.edu",
        "grade_level": 10
      },
      "justification": "New transfer student",
      "submitted_at": "2025-10-27T14:35:00Z"
    }
  ]
}
```

---

### PUT /api/v1/admin/requests/{request_id}/approve

Approve or deny a student account request.

**Authorization:** `school_admin`, `district_admin`

**Request:**
```json
{
  "action": "approve",
  "notes": "Verified enrollment with registrar"
}
```

**Actions:** `approve`, `deny`

**Response:** `200 OK`
```json
{
  "request_id": "sreq_xyz789",
  "status": "approved",
  "student_account": {
    "id": "user_newstudent",
    "email": "john.smith@mnps.edu",
    "temporary_password": "TempP@ss123",
    "activation_link": "https://app.vividly.education/activate/abc123"
  },
  "processed_at": "2025-10-27T15:00:00Z"
}
```

---

## Internal Service Endpoints

These endpoints are for inter-service communication and are not exposed publicly.

### POST /internal/v1/nlu/extract-topic

Extract topic from free-text query.

**Request:**
```json
{
  "query": "Can you explain Newton's third law?",
  "context": {
    "grade_level": 10,
    "subject_preference": "physics"
  }
}
```

**Response:** `200 OK`
```json
{
  "topic_id": "topic_phys_newton_3",
  "confidence": 0.95,
  "needs_clarification": false
}
```

**Response (Needs Clarification):** `200 OK`
```json
{
  "needs_clarification": true,
  "clarification_question": "Which of Newton's laws would you like to learn about?",
  "options": [
    {
      "id": "option_1",
      "topic_id": "topic_phys_newton_1",
      "title": "First Law (Inertia)"
    },
    {
      "id": "option_2",
      "topic_id": "topic_phys_newton_3",
      "title": "Third Law (Action-Reaction)"
    }
  ]
}
```

---

### GET /internal/v1/cache/check

Check if content exists in cache.

**Query Parameters:**
- `topic_id`: The topic identifier
- `interest_id`: The interest identifier
- `style`: Content style

**Response (Cache Hit):** `200 OK`
```json
{
  "cache_hit": true,
  "content": {
    "script_url": "https://storage.googleapis.com/.../script.json",
    "audio_url": "https://storage.googleapis.com/.../audio.mp3",
    "video_url": "https://storage.googleapis.com/.../video.mp4",
    "cached_at": "2025-10-20T08:00:00Z"
  }
}
```

**Response (Cache Miss):** `200 OK`
```json
{
  "cache_hit": false
}
```

---

### POST /internal/v1/jobs/generate-script

Trigger script generation job (publishes to Pub/Sub).

**Request:**
```json
{
  "request_id": "req_7f8d9e1a",
  "topic_id": "topic_phys_newton_3",
  "interest_id": "int_basketball",
  "style": "conversational",
  "user_id": "user_12345"
}
```

**Response:** `202 Accepted`
```json
{
  "job_id": "job_script_abc123",
  "status": "queued",
  "estimated_time_seconds": 8
}
```

---

## Webhook Endpoints

### POST /api/v1/webhooks/nano-banana

Receive completion notification from Nano Banana video API.

**Authentication:** HMAC signature verification

**Request (from Nano Banana):**
```json
{
  "event": "video.completed",
  "video_id": "nb_video_xyz789",
  "status": "success",
  "video_url": "https://nano-banana.com/videos/xyz789.mp4",
  "metadata": {
    "vividly_job_id": "job_video_abc123"
  },
  "timestamp": "2025-10-27T14:45:00Z"
}
```

**Response:** `200 OK`
```json
{
  "received": true
}
```

---

## Appendix: Request ID Lifecycle

1. Student submits query → API generates `request_id`
2. Request ID tracked through entire pipeline:
   - NLU processing
   - Cache check
   - Script generation
   - Audio generation
   - Video generation
3. Student polls `/content/status/{request_id}` for updates
4. Request ID expires after 24 hours if not completed

---

## Appendix: Idempotency

All POST/PUT endpoints support idempotency keys to prevent duplicate operations:

**Header:**
```
Idempotency-Key: unique_key_12345
```

The server stores the response for 24 hours and returns the same response for duplicate requests with the same key.

---

**Document Control**
- **Owner**: API Team
- **Last Review**: 2025-10-27
- **Next Review**: After MVP Launch
