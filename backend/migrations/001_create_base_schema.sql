/*
Base Schema Migration - Vividly MVP
Created: October 28, 2025
Version: 001

This creates the foundational database schema for the Vividly MVP.
Designed to be flexible and evolvable as the software develops.

Tables Created (13):
1. organizations - School districts and organizations
2. schools - Individual schools within organizations
3. users - All users (students, teachers, admins)
4. classes - Teacher classes
5. class_student - Student enrollment in classes
6. interests - Canonical list of student interests
7. student_interest - Student-selected interests
8. topics - Educational topics/curriculum
9. student_progress - Student learning progress per topic
10. student_activity - Student activity log
11. content_metadata - Generated video content
12. sessions - JWT refresh token tracking
13. password_reset - Password reset tokens

Design Principles:
- Flexible: Can evolve without breaking changes
- Normalized: Proper relational design
- JSONB fields: For flexible metadata that may change
- Timestamps: All tables have created_at, updated_at
- Soft deletes: archived/deleted flags instead of hard deletes
- UUIDs: For distributed ID generation (future-proof)
*/

BEGIN;

-- ==============================================================================
-- 1. Organizations Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    organization_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'school_district', -- school_district, individual_school
    domain VARCHAR(255), -- Email domain for auto-enrollment (e.g., mnps.edu)
    settings JSONB DEFAULT '{}', -- Flexible settings
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

CREATE INDEX idx_organizations_domain ON organizations(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_organizations_archived ON organizations(archived) WHERE archived = FALSE;

COMMENT ON TABLE organizations IS 'School districts and organizations';
COMMENT ON COLUMN organizations.settings IS 'Flexible JSONB for org-specific settings';

-- ==============================================================================
-- 2. Schools Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS schools (
    school_id VARCHAR(100) PRIMARY KEY,
    organization_id VARCHAR(100) REFERENCES organizations(organization_id),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    phone VARCHAR(50),
    principal_name VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

CREATE INDEX idx_schools_organization ON schools(organization_id);
CREATE INDEX idx_schools_archived ON schools(archived) WHERE archived = FALSE;

COMMENT ON TABLE schools IS 'Individual schools within organizations';

-- ==============================================================================
-- 3. Users Table (Students, Teachers, Admins)
-- ==============================================================================

CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin', 'super_admin');
CREATE TYPE user_status AS ENUM ('active', 'suspended', 'pending', 'archived');

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    status user_status NOT NULL DEFAULT 'active',

    -- School/Organization
    organization_id VARCHAR(100) REFERENCES organizations(organization_id),
    school_id VARCHAR(100) REFERENCES schools(school_id),

    -- Student-specific fields
    grade_level INTEGER CHECK (grade_level >= 9 AND grade_level <= 12),

    -- Teacher-specific fields (stored in JSONB for flexibility)
    teacher_data JSONB DEFAULT '{}', -- subjects taught, etc.

    -- Profile
    profile_picture_url TEXT,
    bio TEXT,

    -- Tracking
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_school ON users(school_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role_school ON users(role, school_id);
CREATE INDEX idx_users_last_login ON users(last_login_at DESC);

COMMENT ON TABLE users IS 'All users: students, teachers, admins';
COMMENT ON COLUMN users.teacher_data IS 'JSONB for teacher-specific data (subjects, certifications, etc.)';

-- ==============================================================================
-- 4. Classes Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS classes (
    class_id VARCHAR(100) PRIMARY KEY,
    teacher_id VARCHAR(100) NOT NULL REFERENCES users(user_id),
    school_id VARCHAR(100) NOT NULL REFERENCES schools(school_id),

    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL, -- Physics, Chemistry, Biology, Math, etc.
    grade_level INTEGER NOT NULL CHECK (grade_level >= 9 AND grade_level <= 12),

    class_code VARCHAR(50) UNIQUE NOT NULL, -- For student join (e.g., PHYS-ABC-123)
    description TEXT,

    -- Schedule (flexible JSONB)
    schedule JSONB DEFAULT '{}', -- days, times, etc.

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

CREATE INDEX idx_classes_teacher ON classes(teacher_id, created_at DESC);
CREATE INDEX idx_classes_school ON classes(school_id);
CREATE UNIQUE INDEX idx_classes_code ON classes(class_code);
CREATE INDEX idx_classes_subject ON classes(subject);
CREATE INDEX idx_classes_archived ON classes(archived, teacher_id) WHERE archived = FALSE;

COMMENT ON TABLE classes IS 'Teacher classes';
COMMENT ON COLUMN classes.class_code IS 'Unique code for student enrollment (e.g., PHYS-ABC-123)';

-- ==============================================================================
-- 5. Class-Student Junction Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS class_student (
    class_id VARCHAR(100) NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    enrolled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active', -- active, dropped, completed

    PRIMARY KEY (class_id, student_id)
);

CREATE INDEX idx_class_student_class ON class_student(class_id);
CREATE INDEX idx_class_student_student ON class_student(student_id);
CREATE INDEX idx_class_student_status ON class_student(status);

COMMENT ON TABLE class_student IS 'Student enrollment in classes';

-- ==============================================================================
-- 6. Interests Table (Canonical List)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS interests (
    interest_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL, -- sports, arts, technology, science, etc.
    description TEXT,
    icon_url TEXT,
    display_order INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interests_category ON interests(category, name);
CREATE INDEX idx_interests_active ON interests(active) WHERE active = TRUE;

COMMENT ON TABLE interests IS 'Canonical list of student interests for content personalization';

-- Insert default interests
INSERT INTO interests (interest_id, name, category, description, display_order) VALUES
    ('int_basketball', 'Basketball', 'sports', 'Basketball and related sports', 1),
    ('int_football', 'Football', 'sports', 'American football', 2),
    ('int_soccer', 'Soccer', 'sports', 'Soccer/futbol', 3),
    ('int_music', 'Music Production', 'arts', 'Making and producing music', 10),
    ('int_art', 'Visual Art', 'arts', 'Drawing, painting, design', 11),
    ('int_dance', 'Dance', 'arts', 'Dance and choreography', 12),
    ('int_gaming', 'Video Games', 'technology', 'Gaming and esports', 20),
    ('int_coding', 'Coding', 'technology', 'Programming and software development', 21),
    ('int_robotics', 'Robotics', 'technology', 'Robotics and automation', 22),
    ('int_space', 'Space & Astronomy', 'science', 'Space exploration and astronomy', 30),
    ('int_biology', 'Biology & Nature', 'science', 'Living things and ecosystems', 31),
    ('int_cooking', 'Cooking', 'lifestyle', 'Culinary arts and cooking', 40),
    ('int_fashion', 'Fashion', 'lifestyle', 'Fashion and style', 41),
    ('int_fitness', 'Fitness', 'lifestyle', 'Exercise and health', 42)
ON CONFLICT (interest_id) DO NOTHING;

-- ==============================================================================
-- 7. Student-Interest Junction Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS student_interest (
    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    interest_id VARCHAR(100) NOT NULL REFERENCES interests(interest_id),

    selected_at TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (student_id, interest_id)
);

CREATE INDEX idx_student_interest_student ON student_interest(student_id);
CREATE INDEX idx_student_interest_interest ON student_interest(interest_id);

COMMENT ON TABLE student_interest IS 'Student-selected interests (1-5 per student)';

-- ==============================================================================
-- 8. Topics Table (Educational Curriculum)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS topics (
    topic_id VARCHAR(100) PRIMARY KEY,
    subject VARCHAR(100) NOT NULL, -- Physics, Chemistry, Biology, Math, etc.
    unit VARCHAR(255) NOT NULL, -- Mechanics, Thermodynamics, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,

    grade_level_min INTEGER DEFAULT 9,
    grade_level_max INTEGER DEFAULT 12,

    topic_order INTEGER DEFAULT 0, -- Order within unit

    -- Standards alignment (flexible JSONB)
    standards JSONB DEFAULT '{}', -- Common Core, NGSS, etc.

    prerequisites JSONB DEFAULT '[]', -- Array of prerequisite topic_ids

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_topics_subject ON topics(subject);
CREATE INDEX idx_topics_subject_unit ON topics(subject, unit, topic_order);
CREATE INDEX idx_topics_grade ON topics(grade_level_min, grade_level_max);
CREATE INDEX idx_topics_active ON topics(active) WHERE active = TRUE;

COMMENT ON TABLE topics IS 'Educational topics/curriculum';
COMMENT ON COLUMN topics.standards IS 'JSONB for standards alignment (Common Core, NGSS, etc.)';

-- Insert sample topics (Physics - Mechanics)
INSERT INTO topics (topic_id, subject, unit, name, description, topic_order) VALUES
    ('topic_phys_mech_newton_1', 'Physics', 'Mechanics', 'Newton''s First Law', 'Law of inertia', 1),
    ('topic_phys_mech_newton_2', 'Physics', 'Mechanics', 'Newton''s Second Law', 'F = ma', 2),
    ('topic_phys_mech_newton_3', 'Physics', 'Mechanics', 'Newton''s Third Law', 'Action-reaction pairs', 3),
    ('topic_phys_mech_momentum', 'Physics', 'Mechanics', 'Momentum & Impulse', 'Conservation of momentum', 4),
    ('topic_phys_mech_energy', 'Physics', 'Mechanics', 'Energy & Work', 'Kinetic and potential energy', 5)
ON CONFLICT (topic_id) DO NOTHING;

-- ==============================================================================
-- 9. Student Progress Table
-- ==============================================================================

CREATE TYPE progress_status AS ENUM ('not_started', 'in_progress', 'completed');

CREATE TABLE IF NOT EXISTS student_progress (
    progress_id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    topic_id VARCHAR(100) NOT NULL REFERENCES topics(topic_id),
    class_id VARCHAR(100) REFERENCES classes(class_id) ON DELETE SET NULL,

    status progress_status NOT NULL DEFAULT 'not_started',
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Video watching
    videos_watched INTEGER DEFAULT 0,
    total_watch_time_seconds INTEGER DEFAULT 0,

    -- Completion
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE (student_id, topic_id)
);

CREATE INDEX idx_student_progress_student ON student_progress(student_id, topic_id);
CREATE INDEX idx_student_progress_topic ON student_progress(topic_id);
CREATE INDEX idx_student_progress_status ON student_progress(student_id, status);
CREATE INDEX idx_student_progress_class ON student_progress(class_id, topic_id);
CREATE INDEX idx_student_progress_completed ON student_progress(student_id, completed_at DESC) WHERE completed_at IS NOT NULL;

COMMENT ON TABLE student_progress IS 'Student learning progress per topic';

-- ==============================================================================
-- 10. Student Activity Table (Event Log)
-- ==============================================================================

CREATE TYPE activity_type AS ENUM (
    'video_started',
    'video_completed',
    'video_paused',
    'topic_started',
    'topic_completed',
    'interest_updated',
    'login'
);

CREATE TABLE IF NOT EXISTS student_activity (
    activity_id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type activity_type NOT NULL,

    -- Context
    topic_id VARCHAR(100) REFERENCES topics(topic_id),
    content_id VARCHAR(100), -- References content_metadata
    class_id VARCHAR(100) REFERENCES classes(class_id),
    interest_id VARCHAR(100) REFERENCES interests(interest_id),

    -- Details
    duration_seconds INTEGER,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_student_activity_student ON student_activity(student_id, created_at DESC);
CREATE INDEX idx_student_activity_type ON student_activity(activity_type);
CREATE INDEX idx_student_activity_topic ON student_activity(topic_id);
CREATE INDEX idx_student_activity_recent ON student_activity(student_id, created_at DESC);

COMMENT ON TABLE student_activity IS 'Student activity event log';

-- ==============================================================================
-- 11. Content Metadata Table (Generated Videos)
-- ==============================================================================

CREATE TYPE content_status AS ENUM ('generating', 'ready', 'failed', 'archived');

CREATE TABLE IF NOT EXISTS content_metadata (
    content_id VARCHAR(100) PRIMARY KEY,
    request_id VARCHAR(100), -- References content_requests (from tracking migration)

    student_id VARCHAR(100) NOT NULL REFERENCES users(user_id),
    topic_id VARCHAR(100) NOT NULL REFERENCES topics(topic_id),
    interest_id VARCHAR(100) REFERENCES interests(interest_id),

    title VARCHAR(500) NOT NULL,
    description TEXT,

    -- Video
    video_url TEXT,
    thumbnail_url TEXT,
    duration_seconds INTEGER,

    -- Storage
    gcs_bucket VARCHAR(255),
    gcs_path VARCHAR(500),
    cdn_url TEXT,

    -- Status
    status content_status NOT NULL DEFAULT 'generating',

    -- Generation metadata
    script_content TEXT, -- Full script
    generation_metadata JSONB DEFAULT '{}', -- Model versions, prompts, etc.

    -- Stats
    view_count INTEGER DEFAULT 0,
    completion_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

CREATE INDEX idx_content_student ON content_metadata(student_id, created_at DESC);
CREATE INDEX idx_content_topic ON content_metadata(topic_id);
CREATE INDEX idx_content_status ON content_metadata(status);
CREATE INDEX idx_content_request ON content_metadata(request_id);
CREATE INDEX idx_content_archived ON content_metadata(archived) WHERE archived = FALSE;

COMMENT ON TABLE content_metadata IS 'Generated video content metadata';
COMMENT ON COLUMN content_metadata.generation_metadata IS 'JSONB for flexible generation details';

-- ==============================================================================
-- 12. Sessions Table (JWT Refresh Tokens)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    refresh_token_hash TEXT NOT NULL, -- Hashed refresh token

    -- Metadata
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,

    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP
);

CREATE INDEX idx_sessions_user ON sessions(user_id, revoked) WHERE revoked = FALSE;
CREATE INDEX idx_sessions_token ON sessions(refresh_token_hash, revoked) WHERE revoked = FALSE;
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE revoked = FALSE;

COMMENT ON TABLE sessions IS 'JWT refresh token tracking';

-- ==============================================================================
-- 13. Password Reset Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS password_reset (
    reset_id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    reset_token_hash TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL, -- Usually 1 hour

    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);

CREATE INDEX idx_password_reset_user ON password_reset(user_id, created_at DESC);
CREATE INDEX idx_password_reset_token ON password_reset(reset_token_hash, used, expires_at)
    WHERE used = FALSE;

COMMENT ON TABLE password_reset IS 'Password reset tokens';

-- ==============================================================================
-- 14. Student Request Table (Account Approval Workflow)
-- ==============================================================================

CREATE TYPE request_status AS ENUM ('pending', 'approved', 'rejected');

CREATE TABLE IF NOT EXISTS student_request (
    request_id VARCHAR(100) PRIMARY KEY,

    -- Request details
    student_first_name VARCHAR(100) NOT NULL,
    student_last_name VARCHAR(100) NOT NULL,
    student_email VARCHAR(255) NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level >= 9 AND grade_level <= 12),

    class_id VARCHAR(100) REFERENCES classes(class_id),

    -- Workflow
    requested_by VARCHAR(100) NOT NULL REFERENCES users(user_id), -- Teacher
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),

    approver_id VARCHAR(100) REFERENCES users(user_id), -- Admin

    status request_status NOT NULL DEFAULT 'pending',

    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,

    notes TEXT,

    -- Created user (after approval)
    created_user_id VARCHAR(100) REFERENCES users(user_id)
);

CREATE INDEX idx_student_request_teacher ON student_request(requested_by, requested_at DESC);
CREATE INDEX idx_student_request_approver ON student_request(approver_id, status, requested_at DESC);
CREATE INDEX idx_student_request_status ON student_request(status, requested_at DESC);

COMMENT ON TABLE student_request IS 'Student account approval workflow';

-- ==============================================================================
-- Update Triggers
-- ==============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topics_updated_at BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_progress_updated_at BEFORE UPDATE ON student_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_metadata_updated_at BEFORE UPDATE ON content_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- Sample Data for Development/Testing
-- ==============================================================================

-- Insert sample organization
INSERT INTO organizations (organization_id, name, type, domain) VALUES
    ('org_mnps', 'Metropolitan Nashville Public Schools', 'school_district', 'mnps.edu')
ON CONFLICT (organization_id) DO NOTHING;

-- Insert sample school
INSERT INTO schools (school_id, organization_id, name, city, state) VALUES
    ('school_hillsboro_hs', 'org_mnps', 'Hillsboro High School', 'Nashville', 'TN')
ON CONFLICT (school_id) DO NOTHING;

COMMIT;

-- ==============================================================================
-- Post-Migration Summary
-- ==============================================================================

-- Display table counts
SELECT
    'Base Schema Created' as status,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    (SELECT COUNT(*) FROM interests) as interests_count,
    (SELECT COUNT(*) FROM topics) as topics_count;
