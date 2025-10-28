# Vividly Database Schema

**Database:** PostgreSQL 15+
**Version:** 1.0
**Last Updated:** October 27, 2025

## Table of Contents

1. [Overview](#overview)
2. [Schema Design Principles](#schema-design-principles)
3. [Entity Relationship Diagram](#entity-relationship-diagram)
4. [Table Definitions](#table-definitions)
5. [Indexes](#indexes)
6. [Migration Strategy](#migration-strategy)
7. [Data Retention](#data-retention)
8. [Sample Queries](#sample-queries)

---

## Overview

The Vividly database manages:
- User accounts and authentication
- Organizational hierarchy (Districts, Schools, Classes)
- Topic hierarchy and canonical interests
- Content generation requests and tracking
- Student progress and engagement
- Administrative workflows

**Schema Name:** `public` (MVP), namespaced schemas (future)

---

## Schema Design Principles

### 1. Data Minimization
- Store only essential PII
- Separate identifiable data from content metadata
- Cascade deletes for user data cleanup

### 2. Referential Integrity
- Foreign keys with appropriate CASCADE/RESTRICT rules
- NOT NULL constraints on critical fields
- CHECK constraints for data validation

### 3. Audit Trail
- `created_at` and `updated_at` on all tables
- `deleted_at` for soft deletes (GDPR compliance)
- Separate `audit_logs` table for compliance

### 4. Performance
- Strategic indexing on query patterns
- Partitioning for large tables (future)
- Denormalization for read-heavy data (KPIs)

### 5. Extensibility
- JSONB columns for flexible metadata
- Enums for type safety with easy extension
- Versioned schemas for migrations

---

## Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  districts   │────1:N──│   schools    │────1:N──│    users     │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                                                    ┌─────┴─────┐
                                                    │           │
                         ┌──────────────┐      (students)  (teachers)
                         │   classes    │           │           │
                         └───────┬──────┘           │           │
                                 │                  │           │
                                 │                  │           │
                         ┌───────┴──────────────────┘           │
                         │  class_students (join)               │
                         └──────────────────────────────────────┘
                                                    │
┌──────────────┐                            ┌──────┴───────┐
│    topics    │────1:N─────────────────────│   content_   │
└──────────────┘                            │   requests   │
                                            └──────┬───────┘
┌──────────────┐                                   │
│  interests   │───────────────────────────────────┤
└──────────────┘                                   │
                                            ┌──────┴───────┐
                                            │   generated_ │
                                            │   content    │
                                            └──────┬───────┘
                                                   │
                                            ┌──────┴───────┐
                                            │   student_   │
                                            │   progress   │
                                            └──────────────┘

┌──────────────┐
│   feedback   │
└──────────────┘

┌──────────────┐
│  audit_logs  │
└──────────────┘
```

---

## Table Definitions

### organizations

Represents districts and schools in a hierarchical structure.

```sql
CREATE TYPE organization_type AS ENUM ('district', 'school');

CREATE TABLE organizations (
    id VARCHAR(50) PRIMARY KEY,  -- 'org_mnps', 'school_hillsboro_hs'
    name VARCHAR(255) NOT NULL,
    org_type organization_type NOT NULL,
    parent_id VARCHAR(50) REFERENCES organizations(id) ON DELETE RESTRICT,

    -- Contact Information
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    phone VARCHAR(20),

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CHECK (
        (org_type = 'district' AND parent_id IS NULL) OR
        (org_type = 'school' AND parent_id IS NOT NULL)
    )
);

CREATE INDEX idx_organizations_parent ON organizations(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_type ON organizations(org_type) WHERE deleted_at IS NULL;
```

**Sample Data:**
```sql
INSERT INTO organizations VALUES
('org_mnps', 'Metro Nashville Public Schools', 'district', NULL, ...),
('school_hillsboro_hs', 'Hillsboro High School', 'school', 'org_mnps', ...);
```

---

### users

All user accounts (students, teachers, admins, staff).

```sql
CREATE TYPE user_role AS ENUM (
    'student',
    'teacher',
    'school_admin',
    'district_admin',
    'vividly_admin',
    'vividly_ops',
    'vividly_curriculum'
);

CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,  -- 'user_abc123'

    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    email_verified BOOLEAN DEFAULT false,

    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    -- Role & Organization
    role user_role NOT NULL,
    org_id VARCHAR(50) NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,

    -- Student-specific (NULL for non-students)
    student_id VARCHAR(50),  -- School district student ID
    grade_level INTEGER,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Password Reset
    reset_token VARCHAR(255),
    reset_token_expires_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CHECK (
        (role = 'student' AND grade_level IS NOT NULL) OR
        (role != 'student' AND grade_level IS NULL)
    )
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_org_role ON users(org_id, role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_student_id ON users(student_id) WHERE student_id IS NOT NULL;
```

---

### classes

Teacher-managed class groups.

```sql
CREATE TABLE classes (
    id VARCHAR(50) PRIMARY KEY,  -- 'class_abc123'

    -- Basic Information
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade_level INTEGER,
    school_year VARCHAR(20),  -- '2025-2026'

    -- Ownership
    teacher_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    school_id VARCHAR(50) NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,

    -- Invite Code
    invite_code VARCHAR(20) UNIQUE,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CHECK (grade_level BETWEEN 9 AND 12)
);

CREATE INDEX idx_classes_teacher ON classes(teacher_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_classes_school ON classes(school_id) WHERE deleted_at IS NULL;
```

---

### class_students

Join table for many-to-many relationship between classes and students.

```sql
CREATE TABLE class_students (
    id SERIAL PRIMARY KEY,

    class_id VARCHAR(50) NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Enrollment
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dropped_at TIMESTAMP WITH TIME ZONE,

    -- Unique constraint
    UNIQUE(class_id, student_id)
);

CREATE INDEX idx_class_students_class ON class_students(class_id) WHERE dropped_at IS NULL;
CREATE INDEX idx_class_students_student ON class_students(student_id) WHERE dropped_at IS NULL;
```

---

### topics

Hierarchical STEM topic structure.

```sql
CREATE TABLE topics (
    id VARCHAR(100) PRIMARY KEY,  -- 'topic_phys_newton_3'

    -- Hierarchy
    parent_id VARCHAR(100) REFERENCES topics(id) ON DELETE RESTRICT,
    path VARCHAR(500),  -- Materialized path: 'physics.mechanics.newtons_laws.third_law'
    depth INTEGER NOT NULL DEFAULT 0,

    -- Content
    title VARCHAR(255) NOT NULL,
    description TEXT,

    -- Classification
    subject VARCHAR(50) NOT NULL,  -- 'physics', 'mathematics'
    grade_level_min INTEGER,
    grade_level_max INTEGER,

    -- Ordering
    display_order INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- difficulty_level, prerequisites, etc.

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topics_subject ON topics(subject) WHERE is_active = true;
CREATE INDEX idx_topics_parent ON topics(parent_id) WHERE is_active = true;
CREATE INDEX idx_topics_path ON topics USING GIN(to_tsvector('english', path));
```

**Sample Data:**
```sql
INSERT INTO topics VALUES
('topic_phys', NULL, 'physics', 0, 'Physics', 'High School Physics', 'physics', 9, 12, 1, true, '{}', NOW(), NOW()),
('topic_phys_mechanics', 'topic_phys', 'physics.mechanics', 1, 'Mechanics', 'Classical mechanics', 'physics', 9, 12, 1, true, '{}', NOW(), NOW()),
('topic_phys_newton_laws', 'topic_phys_mechanics', 'physics.mechanics.newtons_laws', 2, 'Newton''s Laws', 'Three laws of motion', 'physics', 9, 10, 1, true, '{}', NOW(), NOW()),
('topic_phys_newton_3', 'topic_phys_newton_laws', 'physics.mechanics.newtons_laws.third_law', 3, 'Newton''s Third Law', 'Action and reaction forces', 'physics', 9, 10, 3, true, '{"difficulty": "medium"}', NOW(), NOW());
```

---

### interests

Canonical interest categories for personalization.

```sql
CREATE TABLE interests (
    id VARCHAR(50) PRIMARY KEY,  -- 'int_basketball'

    -- Content
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),  -- 'sports', 'arts', 'technology', etc.

    -- Media
    icon_url VARCHAR(500),

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Ordering
    display_order INTEGER DEFAULT 0,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interests_category ON interests(category) WHERE is_active = true;
```

**Sample Data:**
```sql
INSERT INTO interests VALUES
('int_basketball', 'Basketball', 'Learn through basketball analogies', 'sports', NULL, true, 1, '{}', NOW(), NOW()),
('int_music_production', 'Music Production', 'Learn through music and audio', 'arts', NULL, true, 2, '{}', NOW(), NOW()),
('int_video_games', 'Video Games', 'Learn through gaming concepts', 'technology', NULL, true, 3, '{}', NOW(), NOW());
```

---

### student_interests

Student-ranked interest preferences.

```sql
CREATE TABLE student_interests (
    id SERIAL PRIMARY KEY,

    student_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest_id VARCHAR(50) NOT NULL REFERENCES interests(id) ON DELETE CASCADE,

    -- Ranking (1 = top preference)
    rank INTEGER NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(student_id, interest_id),
    UNIQUE(student_id, rank),
    CHECK (rank > 0 AND rank <= 10)
);

CREATE INDEX idx_student_interests_student ON student_interests(student_id);
```

---

### content_requests

Tracks student content requests through the pipeline.

```sql
CREATE TYPE request_status AS ENUM (
    'nlu_processing',
    'needs_clarification',
    'cache_check',
    'generating_script',
    'generating_audio',
    'generating_video',
    'fast_path_ready',
    'completed',
    'failed'
);

CREATE TABLE content_requests (
    id VARCHAR(50) PRIMARY KEY,  -- 'req_abc123'

    -- User
    student_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Input
    original_query TEXT NOT NULL,

    -- NLU Results
    topic_id VARCHAR(100) REFERENCES topics(id) ON DELETE SET NULL,
    interest_id VARCHAR(50) REFERENCES interests(id) ON DELETE SET NULL,
    style VARCHAR(50) DEFAULT 'conversational',

    -- Status
    status request_status NOT NULL DEFAULT 'nlu_processing',

    -- Cache
    cache_hit BOOLEAN DEFAULT false,

    -- Results
    generated_content_id VARCHAR(50) REFERENCES generated_content(id) ON DELETE SET NULL,

    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timing
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- clarification data, etc.

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_content_requests_student ON content_requests(student_id, created_at DESC);
CREATE INDEX idx_content_requests_status ON content_requests(status) WHERE status NOT IN ('completed', 'failed');
CREATE INDEX idx_content_requests_topic ON content_requests(topic_id) WHERE topic_id IS NOT NULL;
```

---

### generated_content

Storage metadata for AI-generated content.

```sql
CREATE TYPE content_type AS ENUM ('vivid_now', 'vivid_learning');

CREATE TABLE generated_content (
    id VARCHAR(50) PRIMARY KEY,  -- 'content_abc123'

    -- Content Key (for caching)
    topic_id VARCHAR(100) NOT NULL REFERENCES topics(id) ON DELETE RESTRICT,
    interest_id VARCHAR(50) NOT NULL REFERENCES interests(id) ON DELETE RESTRICT,
    style VARCHAR(50) NOT NULL DEFAULT 'conversational',
    cache_key VARCHAR(255) NOT NULL UNIQUE,  -- SHA256(topic_id|interest_id|style)

    -- Content Type
    content_type content_type NOT NULL,

    -- GCS URLs
    script_url VARCHAR(500),
    audio_url VARCHAR(500),
    video_url VARCHAR(500),
    thumbnail_url VARCHAR(500),

    -- Metrics
    duration_seconds INTEGER,
    file_size_bytes BIGINT,

    -- Generation Metadata
    generation_metadata JSONB DEFAULT '{}',  -- model versions, prompts, etc.

    -- Quality
    quality_score DECIMAL(3,2),  -- 0.00 to 1.00
    manual_review_status VARCHAR(50),  -- 'pending', 'approved', 'flagged'

    -- Usage Stats
    view_count INTEGER DEFAULT 0,
    completion_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_generated_content_cache_key ON generated_content(cache_key);
CREATE INDEX idx_generated_content_topic ON generated_content(topic_id);
CREATE INDEX idx_generated_content_popularity ON generated_content(view_count DESC);
```

---

### student_progress

Tracks student learning progress per topic.

```sql
CREATE TYPE progress_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'struggling'
);

CREATE TABLE student_progress (
    id SERIAL PRIMARY KEY,

    student_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id VARCHAR(100) NOT NULL REFERENCES topics(id) ON DELETE CASCADE,

    -- Progress
    status progress_status NOT NULL DEFAULT 'not_started',

    -- Engagement
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Content Used
    content_id VARCHAR(50) REFERENCES generated_content(id) ON DELETE SET NULL,

    -- Time Tracking
    total_time_seconds INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(student_id, topic_id)
);

CREATE INDEX idx_student_progress_student ON student_progress(student_id, status);
CREATE INDEX idx_student_progress_topic ON student_progress(topic_id);
CREATE INDEX idx_student_progress_recent ON student_progress(student_id, last_viewed_at DESC);
```

---

### feedback

User feedback on generated content.

```sql
CREATE TYPE feedback_type AS ENUM (
    'mark_complete',
    'make_simpler',
    'try_different_interest',
    'report_issue',
    'rating_only'
);

CREATE TABLE feedback (
    id VARCHAR(50) PRIMARY KEY,  -- 'feedback_abc123'

    -- References
    student_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id VARCHAR(50) NOT NULL REFERENCES generated_content(id) ON DELETE CASCADE,

    -- Feedback
    feedback_type feedback_type NOT NULL,
    rating INTEGER,  -- 1-5 stars
    comment TEXT,

    -- Action Taken
    triggered_regeneration BOOLEAN DEFAULT false,
    regeneration_request_id VARCHAR(50) REFERENCES content_requests(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5))
);

CREATE INDEX idx_feedback_content ON feedback(content_id, created_at DESC);
CREATE INDEX idx_feedback_student ON feedback(student_id, created_at DESC);
CREATE INDEX idx_feedback_type ON feedback(feedback_type) WHERE triggered_regeneration = true;
```

---

### student_account_requests

Teacher-submitted requests for new student accounts.

```sql
CREATE TYPE account_request_status AS ENUM (
    'pending',
    'approved',
    'denied'
);

CREATE TABLE student_account_requests (
    id VARCHAR(50) PRIMARY KEY,  -- 'sreq_abc123'

    -- Requester
    teacher_id VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Student Info
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    grade_level INTEGER NOT NULL,
    student_id VARCHAR(50),

    -- Assignment
    class_id VARCHAR(50) NOT NULL REFERENCES classes(id) ON DELETE CASCADE,

    -- Justification
    justification TEXT,

    -- Status
    status account_request_status NOT NULL DEFAULT 'pending',

    -- Review
    reviewed_by VARCHAR(50) REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Result (if approved)
    created_user_id VARCHAR(50) REFERENCES users(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_account_requests_status ON student_account_requests(status, created_at DESC);
CREATE INDEX idx_account_requests_teacher ON student_account_requests(teacher_id);
```

---

### bulk_upload_jobs

Tracks CSV bulk upload processing.

```sql
CREATE TYPE job_status AS ENUM (
    'queued',
    'processing',
    'completed',
    'failed'
);

CREATE TABLE bulk_upload_jobs (
    id VARCHAR(50) PRIMARY KEY,  -- 'upload_job_abc123'

    -- Uploader
    uploaded_by VARCHAR(50) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    school_id VARCHAR(50) NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- File
    file_path VARCHAR(500) NOT NULL,
    total_rows INTEGER,

    -- Status
    status job_status NOT NULL DEFAULT 'queued',

    -- Results
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    error_log JSONB DEFAULT '[]',  -- Array of {row, error}

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bulk_upload_jobs_uploader ON bulk_upload_jobs(uploaded_by, created_at DESC);
CREATE INDEX idx_bulk_upload_jobs_status ON bulk_upload_jobs(status);
```

---

### audit_logs

Compliance audit trail.

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- Actor
    user_id VARCHAR(50) REFERENCES users(id) ON DELETE SET NULL,
    user_role user_role,

    -- Action
    action VARCHAR(100) NOT NULL,  -- 'view_student_data', 'delete_user', etc.
    resource_type VARCHAR(50),     -- 'user', 'content', 'progress'
    resource_id VARCHAR(50),

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Details
    metadata JSONB DEFAULT '{}',

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- Partition by month for performance
-- ALTER TABLE audit_logs PARTITION BY RANGE (created_at);
```

---

## Indexes

### Composite Indexes for Common Queries

```sql
-- Dashboard queries
CREATE INDEX idx_student_progress_dashboard
ON student_progress(student_id, status, last_viewed_at DESC);

-- Teacher class view
CREATE INDEX idx_class_students_engagement
ON class_students(class_id, enrolled_at DESC)
WHERE dropped_at IS NULL;

-- KPI calculations
CREATE INDEX idx_users_activation
ON users(org_id, role, last_login_at DESC)
WHERE is_active = true AND deleted_at IS NULL;

-- Content popularity
CREATE INDEX idx_content_usage
ON generated_content(topic_id, view_count DESC, average_rating DESC);
```

### Full-Text Search Indexes

```sql
-- Topic search
CREATE INDEX idx_topics_search
ON topics USING GIN(to_tsvector('english', title || ' ' || description));

-- User search
CREATE INDEX idx_users_search
ON users USING GIN(to_tsvector('english', first_name || ' ' || last_name || ' ' || email));
```

---

## Migration Strategy

### Alembic Configuration

**Directory Structure:**
```
backend/
  migrations/
    versions/
      001_initial_schema.py
      002_add_feedback_table.py
      ...
    env.py
    script.py.mako
```

### Migration Template

```python
"""Add feedback table

Revision ID: 002
Revises: 001
Create Date: 2025-10-27 14:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum
    feedback_type = sa.Enum(
        'mark_complete',
        'make_simpler',
        'try_different_interest',
        'report_issue',
        'rating_only',
        name='feedback_type'
    )
    feedback_type.create(op.get_bind())

    # Create table
    op.create_table('feedback',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('student_id', sa.String(50), nullable=False),
        sa.Column('content_id', sa.String(50), nullable=False),
        sa.Column('feedback_type', feedback_type, nullable=False),
        sa.Column('rating', sa.Integer),
        sa.Column('comment', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)')
    )

    # Create indexes
    op.create_index('idx_feedback_content', 'feedback', ['content_id', 'created_at'])
    op.create_index('idx_feedback_student', 'feedback', ['student_id', 'created_at'])

def downgrade():
    op.drop_index('idx_feedback_student')
    op.drop_index('idx_feedback_content')
    op.drop_table('feedback')
    sa.Enum(name='feedback_type').drop(op.get_bind())
```

---

## Data Retention

### Retention Policies

| Table | Retention Period | Action |
|-------|------------------|--------|
| `users` | Until contract end + 30 days | Hard delete (CASCADE) |
| `content_requests` | 90 days | Archive to BigQuery, soft delete |
| `generated_content` | Indefinite (cached) | Never delete (shared resource) |
| `student_progress` | Until contract end + 30 days | Hard delete (CASCADE) |
| `feedback` | 2 years | Archive to BigQuery |
| `audit_logs` | 7 years | Partition by year, archive old partitions |

### Cleanup Jobs

```sql
-- Soft delete old content requests (run daily)
UPDATE content_requests
SET deleted_at = NOW()
WHERE created_at < NOW() - INTERVAL '90 days'
  AND status IN ('completed', 'failed')
  AND deleted_at IS NULL;

-- Delete expired password reset tokens (run hourly)
UPDATE users
SET reset_token = NULL, reset_token_expires_at = NULL
WHERE reset_token_expires_at < NOW();
```

---

## Sample Queries

### Student Dashboard: Recent Activity

```sql
SELECT
    sp.topic_id,
    t.title AS topic_title,
    t.subject,
    sp.status,
    sp.last_viewed_at,
    gc.video_url,
    gc.duration_seconds
FROM student_progress sp
JOIN topics t ON sp.topic_id = t.id
LEFT JOIN generated_content gc ON sp.content_id = gc.id
WHERE sp.student_id = 'user_12345'
  AND sp.last_viewed_at IS NOT NULL
ORDER BY sp.last_viewed_at DESC
LIMIT 10;
```

### Teacher Dashboard: Class Engagement

```sql
SELECT
    u.id,
    u.first_name,
    u.last_name,
    u.last_login_at,
    COUNT(DISTINCT sp.topic_id) AS topics_completed,
    COUNT(DISTINCT cr.id) AS total_requests,
    COALESCE(AVG(f.rating), 0) AS avg_rating,
    MAX(sp.last_viewed_at) AS last_activity
FROM class_students cs
JOIN users u ON cs.student_id = u.id
LEFT JOIN student_progress sp ON u.id = sp.student_id AND sp.status = 'completed'
LEFT JOIN content_requests cr ON u.id = cr.student_id
LEFT JOIN feedback f ON u.id = f.student_id
WHERE cs.class_id = 'class_abc123'
  AND cs.dropped_at IS NULL
GROUP BY u.id, u.first_name, u.last_name, u.last_login_at
ORDER BY last_activity DESC NULLS LAST;
```

### Admin KPI: Cache Hit Rate

```sql
SELECT
    DATE_TRUNC('day', created_at) AS date,
    COUNT(*) AS total_requests,
    SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) AS cache_hits,
    ROUND(
        100.0 * SUM(CASE WHEN cache_hit = true THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS cache_hit_rate_percent
FROM content_requests
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status IN ('fast_path_ready', 'completed')
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;
```

### Content Popularity Analysis

```sql
SELECT
    t.subject,
    t.title AS topic_title,
    i.name AS interest,
    gc.view_count,
    gc.completion_count,
    ROUND(100.0 * gc.completion_count / NULLIF(gc.view_count, 0), 2) AS completion_rate,
    gc.average_rating
FROM generated_content gc
JOIN topics t ON gc.topic_id = t.id
JOIN interests i ON gc.interest_id = i.id
WHERE gc.view_count >= 10
ORDER BY gc.view_count DESC
LIMIT 50;
```

### Struggling Students Report

```sql
SELECT
    u.id,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT sp.topic_id) FILTER (WHERE sp.status = 'struggling') AS struggling_topics,
    COUNT(DISTINCT f.id) FILTER (WHERE f.feedback_type = 'make_simpler') AS simplify_requests,
    ARRAY_AGG(DISTINCT t.title) FILTER (WHERE sp.status = 'struggling') AS topics
FROM users u
JOIN student_progress sp ON u.id = sp.student_id
LEFT JOIN feedback f ON u.id = f.student_id
LEFT JOIN topics t ON sp.topic_id = t.id
WHERE u.role = 'student'
  AND sp.status = 'struggling'
GROUP BY u.id, u.first_name, u.last_name
HAVING COUNT(DISTINCT sp.topic_id) FILTER (WHERE sp.status = 'struggling') >= 2
ORDER BY struggling_topics DESC;
```

---

## Database Functions

### Update Timestamp Trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ... (repeat for all tables with updated_at)
```

### Generate ID Function

```sql
CREATE OR REPLACE FUNCTION generate_id(prefix TEXT)
RETURNS TEXT AS $$
DECLARE
    random_string TEXT;
BEGIN
    random_string := encode(gen_random_bytes(8), 'hex');
    RETURN prefix || '_' || random_string;
END;
$$ LANGUAGE plpgsql;

-- Usage:
-- INSERT INTO users (id, ...) VALUES (generate_id('user'), ...);
```

---

**Document Control**
- **Owner**: Database Team
- **Last Migration**: 001_initial_schema
- **Next Review**: After MVP Launch
