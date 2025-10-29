# Feature Specifications

**Version**: 1.0
**Last Updated**: 2025-10-28
**Status**: MVP Specification

This document provides detailed technical specifications for all features in the Vividly MVP.

## Table of Contents

1. [Student Features](#student-features)
2. [Teacher Features](#teacher-features)
3. [Administrative Features](#administrative-features)
4. [AI Content Generation Features](#ai-content-generation-features)
5. [System Features](#system-features)

---

## Student Features

### F1: Student Authentication & Onboarding

**Priority**: P0 (Critical)
**Epic**: Authentication
**User Story**: As a student, I want to create an account and set up my profile so I can access personalized learning content.

#### Acceptance Criteria
- Students can sign up with email and password
- Email validation required (valid email format)
- Password must meet security requirements (8+ chars, uppercase, lowercase, number)
- Students must select grade level (9-12)
- Profile creation includes name, grade level
- Account activation sends welcome email
- Students must accept Terms of Service
- Session persists across browser sessions

#### Technical Implementation

**API Endpoints**:
```
POST /api/v1/students/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/refresh
```

**Database Schema**:
```sql
users (
  id, email, password_hash, role='student',
  grade_level, created_at, last_login_at
)
```

**Frontend Components**:
- `StudentRegistrationForm.tsx`
- `LoginForm.tsx`
- `PasswordInput.tsx` (with strength indicator)
- `GradeLevelSelector.tsx`

**Security Requirements**:
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with 24-hour expiration
- Refresh tokens stored securely
- Rate limiting on auth endpoints (5 attempts/minute)

**Edge Cases**:
- Duplicate email registration → Show friendly error
- Password reset flow
- Account already exists → Redirect to login
- Network timeout during registration → Retry with exponential backoff

---

### F2: Interest Selection & Profile Customization

**Priority**: P0 (Critical)
**Epic**: Personalization
**User Story**: As a student, I want to select my interests so I can receive content that's relevant to me.

#### Acceptance Criteria
- Students can select from 60 canonical interests
- Minimum 1 interest, maximum 5 interests
- Interests organized by categories (Sports, Arts, Technology, etc.)
- Visual interest cards with icons/images
- "Other" option allows text input (stored but not used for generation initially)
- Students can update interests at any time from profile
- Interest changes reflect in new content requests

#### Technical Implementation

**API Endpoints**:
```
GET  /api/v1/interests                    # List all canonical interests
GET  /api/v1/students/{id}/interests      # Get student's interests
POST /api/v1/students/{id}/interests      # Update student interests
```

**Request/Response**:
```json
// POST /api/v1/students/{id}/interests
{
  "interest_ids": ["int_basketball", "int_music", "int_coding"]
}

// Response
{
  "student_id": "stu_123",
  "interests": [
    {"id": "int_basketball", "name": "Basketball", "category": "sports"},
    {"id": "int_music", "name": "Music Production", "category": "arts"},
    {"id": "int_coding", "name": "Coding", "category": "technology"}
  ],
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Frontend Components**:
- `InterestSelector.tsx` - Grid of interest cards
- `InterestCard.tsx` - Individual selectable card
- `InterestCategoryFilter.tsx` - Filter by category
- `InterestSearch.tsx` - Search interests

**Database Schema**:
```sql
student_interests (
  student_id, interest_id, selected_at
)
```

**Validation Rules**:
- At least 1 interest selected
- Maximum 5 interests
- All interest_ids must be valid canonical interests
- Cannot select duplicate interests

**UI/UX Considerations**:
- Show selected count (e.g., "3 of 5 selected")
- Disable selection when max reached
- Visual feedback on selection/deselection
- Responsive grid layout (4 cols desktop, 2 cols mobile)

---

### F3: Topic Browse & Search

**Priority**: P1 (High)
**Epic**: Content Discovery
**User Story**: As a student, I want to browse and search available topics so I can find subjects I'm interested in learning.

#### Acceptance Criteria
- Students can browse topics by subject (Physics, Mathematics)
- Hierarchical topic navigation (Subject → Unit → Topic)
- Search topics by keyword
- Filter by grade level appropriateness
- Display prerequisite topics
- Show topic metadata (difficulty, estimated time)
- Topics indicate if content is available or needs generation

#### Technical Implementation

**API Endpoints**:
```
GET /api/v1/topics                           # List all topics (with filters)
GET /api/v1/topics/search?q={query}          # Search topics
GET /api/v1/topics/{id}                      # Topic details
GET /api/v1/topics/{id}/prerequisites        # Get prerequisite topics
```

**Query Parameters**:
```
?subject=physics
?grade_level=10
?search=newton's laws
?category=mechanics
?difficulty=beginner|intermediate|advanced
```

**Response Example**:
```json
{
  "topics": [
    {
      "topic_id": "topic_phys_mech_newton_3",
      "name": "Newton's Third Law",
      "subject": "Physics",
      "category": "Mechanics",
      "grade_levels": [9, 10],
      "difficulty": "intermediate",
      "prerequisites": ["topic_phys_mech_newton_1", "topic_phys_mech_newton_2"],
      "standards": ["HS-PS2-1"],
      "estimated_duration_min": 15,
      "content_available": true
    }
  ],
  "total": 140,
  "page": 1,
  "page_size": 20
}
```

**Frontend Components**:
- `TopicBrowser.tsx` - Main browsing interface
- `TopicHierarchy.tsx` - Tree navigation
- `TopicCard.tsx` - Topic display card
- `TopicSearchBar.tsx` - Search with autocomplete
- `TopicFilters.tsx` - Subject/grade/difficulty filters
- `PrerequisiteGraph.tsx` - Visual prerequisite relationships

**Search Implementation**:
- Full-text search on topic names and descriptions
- Fuzzy matching for typos
- Search highlighting
- Recent searches stored in localStorage

**Caching Strategy**:
- Topic list cached client-side for 1 hour
- Invalidate on topic hierarchy updates
- Prefetch related topics

---

### F4: Request Personalized Content

**Priority**: P0 (Critical)
**Epic**: Content Generation
**User Story**: As a student, I want to request AI-generated content for a topic with my interests so I can learn in a way that's engaging to me.

#### Acceptance Criteria
- Student selects a topic to learn
- Student chooses which interest to apply (from their saved interests)
- Optional: Student can ask a specific question about the topic
- Optional: Student selects content style (conversational, formal, storytelling)
- System shows estimated generation time (5-10 seconds)
- Real-time progress indicator during generation
- If generation fails, show clear error message with retry option
- Success shows video player with generated content

#### Technical Implementation

**API Endpoints**:
```
POST   /api/v1/students/content/request      # Request new content
GET    /api/v1/students/content/status/{id}  # Check generation status
GET    /api/v1/students/content/{id}         # Get generated content
```

**Request Format**:
```json
{
  "topic_id": "topic_phys_mech_newton_3",
  "interest_id": "int_basketball",
  "style": "conversational",
  "query": "Why do I get pushed back when I shoot a basketball?"
}
```

**Response Format**:
```json
// POST response (202 Accepted)
{
  "request_id": "req_abc123",
  "status": "processing",
  "estimated_time_seconds": 8,
  "poll_url": "/api/v1/students/content/status/req_abc123"
}

// GET status response (while processing)
{
  "request_id": "req_abc123",
  "status": "processing",
  "stage": "generating_script",
  "progress_percent": 40
}

// GET status response (complete)
{
  "request_id": "req_abc123",
  "status": "completed",
  "content_id": "cnt_xyz789",
  "video_url": "https://storage.googleapis.com/.../video.mp4"
}
```

**Processing Stages**:
1. **Validating** (5%) - Validate input, check cache
2. **Retrieving Context** (15%) - RAG retrieval from OpenStax
3. **Generating Script** (40%) - Gemini script generation
4. **Creating Audio** (60%) - Text-to-Speech
5. **Generating Video** (90%) - Nano Banana video generation
6. **Finalizing** (100%) - Upload to storage, save to DB

**Frontend Components**:
- `ContentRequestForm.tsx` - Request form
- `InterestSelector.tsx` - Choose interest
- `StyleSelector.tsx` - Choose content style
- `GenerationProgress.tsx` - Real-time progress
- `VideoPlayer.tsx` - Playback interface

**Error Handling**:
```json
{
  "request_id": "req_abc123",
  "status": "failed",
  "error": {
    "code": "GENERATION_TIMEOUT",
    "message": "Video generation took too long. Please try again.",
    "retry_allowed": true
  }
}
```

**Caching Logic**:
- Check if identical content exists (topic + interest)
- If cache hit (< 30 days old), return immediately
- If cache miss, trigger generation
- Store generated content for future requests

**Real-time Updates**:
- Frontend polls status endpoint every 1 second
- WebSocket alternative for real-time updates (future enhancement)
- Show animated loader with current stage

---

### F5: Video Playback & Learning Experience

**Priority**: P0 (Critical)
**Epic**: Content Consumption
**User Story**: As a student, I want to watch personalized learning videos with good playback controls so I can learn effectively.

#### Acceptance Criteria
- Video plays smoothly without buffering
- Standard playback controls (play/pause, seek, volume)
- Playback speed adjustment (0.5x, 1x, 1.5x, 2x)
- Fullscreen mode
- Closed captions/subtitles available
- Video progress saved automatically
- Ability to replay video
- Related content suggestions after video ends
- Download option for offline viewing (future)

#### Technical Implementation

**Video Format**:
- Format: MP4 (H.264 video, AAC audio)
- Resolution: 1920x1080 (Full HD)
- Frame rate: 30fps
- Bitrate: 5 Mbps
- Storage: Google Cloud Storage with CDN

**API Endpoints**:
```
GET  /api/v1/students/content/{id}           # Get content metadata
POST /api/v1/students/content/{id}/progress  # Save progress
GET  /api/v1/students/content/{id}/related   # Get related content
```

**Progress Tracking**:
```json
// POST /api/v1/students/content/{id}/progress
{
  "current_time_seconds": 45,
  "total_duration_seconds": 120,
  "completed": false
}
```

**Frontend Components**:
- `VideoPlayer.tsx` - Custom video player (or use library like video.js)
- `PlaybackControls.tsx` - Custom controls
- `ProgressBar.tsx` - Seek bar with thumbnails
- `SpeedControl.tsx` - Playback speed selector
- `CaptionsPanel.tsx` - Closed captions overlay
- `RelatedContent.tsx` - Suggestions after completion

**Video Player Library Options**:
1. **Video.js** - Open source, highly customizable
2. **React Player** - Simple React wrapper
3. **Plyr** - Modern, accessible player

**Progress Save Logic**:
- Save progress every 5 seconds during playback
- Mark as "completed" when > 90% watched
- Resume from last position on return
- Track total watch time for analytics

**Accessibility**:
- Keyboard controls (space=play/pause, arrow keys=seek)
- Screen reader announcements
- High contrast mode support
- Closed captions always available

---

### F6: Learning History & Progress Tracking

**Priority**: P1 (High)
**Epic**: Student Analytics
**User Story**: As a student, I want to see my learning history and progress so I can track what I've learned.

#### Acceptance Criteria
- Dashboard shows recently watched videos
- Display total videos watched
- Show topics covered with completion status
- Time spent learning (daily, weekly, monthly)
- Learning streak tracking (consecutive days)
- Achievements/badges for milestones (future)
- Filter history by subject or date
- Ability to re-watch any previous video

#### Technical Implementation

**API Endpoints**:
```
GET /api/v1/students/{id}/history            # Learning history
GET /api/v1/students/{id}/stats              # Learning statistics
GET /api/v1/students/{id}/progress           # Topic progress
```

**Response Examples**:
```json
// GET /api/v1/students/{id}/stats
{
  "total_videos_watched": 23,
  "total_time_minutes": 345,
  "topics_covered": 15,
  "current_streak_days": 7,
  "longest_streak_days": 12,
  "last_activity": "2025-01-15T14:30:00Z",
  "this_week": {
    "videos": 5,
    "minutes": 75
  }
}

// GET /api/v1/students/{id}/history
{
  "history": [
    {
      "content_id": "cnt_123",
      "topic": "Newton's Third Law",
      "interest": "Basketball",
      "watched_at": "2025-01-15T10:00:00Z",
      "completed": true,
      "watch_time_seconds": 120,
      "total_duration_seconds": 120
    }
  ],
  "total": 23,
  "page": 1
}
```

**Frontend Components**:
- `StudentDashboard.tsx` - Main dashboard
- `LearningStats.tsx` - Statistics cards
- `ActivityHistory.tsx` - Timeline of activities
- `ProgressChart.tsx` - Visual progress over time
- `StreakCounter.tsx` - Streak display
- `TopicProgress.tsx` - Topic completion tracking

**Database Schema**:
```sql
student_progress (
  student_id, content_id, watched_at, completed,
  watch_time_seconds, last_position_seconds
)

learning_stats (
  student_id, date, videos_watched, time_minutes,
  topics_covered, updated_at
)
```

**Streak Calculation**:
- Streak counts consecutive days with ≥1 video watched
- Timezone-aware (use student's local time)
- Grace period: If missed 1 day, streak can be restored with 2 videos next day (future)

**Charts & Visualizations**:
- Line chart: Videos watched over time
- Pie chart: Subject distribution
- Heat map: Activity by day of week
- Progress bars: Topic completion percentage

---

## Teacher Features

### F7: Teacher Dashboard & Class Overview

**Priority**: P0 (Critical)
**Epic**: Teacher Tools
**User Story**: As a teacher, I want to see an overview of my classes and student engagement so I can monitor learning progress.

#### Acceptance Criteria
- Dashboard shows all assigned classes
- Each class displays total students and active students
- Class-level engagement metrics (videos watched, avg time)
- Ability to drill down into individual class details
- Quick access to top-engaged and at-risk students
- Weekly activity summary
- Export class data to CSV

#### Technical Implementation

**API Endpoints**:
```
GET /api/v1/teachers/{id}/classes            # List teacher's classes
GET /api/v1/teachers/classes/{id}            # Class details
GET /api/v1/teachers/classes/{id}/students   # Students in class
GET /api/v1/teachers/classes/{id}/stats      # Class statistics
```

**Response Example**:
```json
{
  "classes": [
    {
      "class_id": "cls_101",
      "name": "Physics 101 - Period 3",
      "grade_level": 10,
      "total_students": 28,
      "active_students_7d": 24,
      "total_videos_watched_7d": 156,
      "avg_time_per_student_minutes": 45,
      "last_activity": "2025-01-15T14:30:00Z"
    }
  ]
}
```

**Frontend Components**:
- `TeacherDashboard.tsx` - Main dashboard
- `ClassCard.tsx` - Class summary card
- `ClassDetailView.tsx` - Detailed class view
- `EngagementMetrics.tsx` - Metrics display
- `StudentList.tsx` - Searchable/sortable student list
- `ExportButton.tsx` - CSV export

**Key Metrics**:
- **Active Students**: Students with activity in last 7 days
- **Engagement Rate**: (Active students / Total students) × 100
- **Avg Videos/Student**: Total videos / Total students
- **Avg Time/Student**: Total minutes / Total students

**Alerts & Notifications**:
- Low engagement class (< 50% active students)
- Student hasn't logged in for 7+ days
- Spike in activity (celebrate success)

---

### F8: Student Progress Monitoring

**Priority**: P0 (Critical)
**Epic**: Teacher Tools
**User Story**: As a teacher, I want to see individual student progress so I can identify students who need help.

#### Acceptance Criteria
- View list of all students in a class
- Sort/filter by engagement, last activity, grade level
- Click student to see detailed progress
- Show topics covered, videos watched, time spent
- Identify topics where student is struggling (low completion)
- Compare student to class average
- Add private notes about student (visible only to teacher)
- Flag students for follow-up

#### Technical Implementation

**API Endpoints**:
```
GET /api/v1/teachers/students/{id}/progress        # Student progress
GET /api/v1/teachers/students/{id}/history         # Student history
POST /api/v1/teachers/students/{id}/notes          # Add teacher note
GET /api/v1/teachers/classes/{id}/comparison       # Class comparison data
```

**Student Progress Response**:
```json
{
  "student_id": "stu_123",
  "name": "Jane Doe",
  "grade_level": 10,
  "class_ids": ["cls_101", "cls_102"],
  "stats": {
    "total_videos_watched": 15,
    "total_time_minutes": 225,
    "topics_covered": 12,
    "current_streak_days": 3,
    "last_activity": "2025-01-15T10:00:00Z"
  },
  "class_comparison": {
    "videos_vs_avg": "+20%",
    "time_vs_avg": "+15%"
  },
  "topics": [
    {
      "topic_id": "topic_phys_mech_newton_3",
      "topic_name": "Newton's Third Law",
      "videos_watched": 2,
      "completed": true,
      "last_watched": "2025-01-14T15:00:00Z"
    }
  ],
  "teacher_notes": [
    {
      "note_id": "note_456",
      "text": "Showed great improvement in mechanics",
      "created_at": "2025-01-10T09:00:00Z",
      "created_by": "Teacher Name"
    }
  ],
  "flags": {
    "needs_attention": false,
    "at_risk": false
  }
}
```

**Frontend Components**:
- `StudentProgressView.tsx` - Detailed student view
- `ProgressComparison.tsx` - Compare to class average
- `TopicCompletionList.tsx` - List of topics with status
- `TeacherNotes.tsx` - Notes panel
- `StudentFlags.tsx` - Flag management

**Teacher Notes**:
- Private notes visible only to teachers in same school
- Support rich text formatting
- Searchable across all students
- Timestamp and author tracking

**At-Risk Identification**:
Student flagged as "at-risk" if:
- No activity in last 7 days
- < 30% engagement compared to class average
- Started but didn't complete > 50% of videos
- Teacher manually flagged

---

### F9: Content Recommendations

**Priority**: P2 (Medium)
**Epic**: Teacher Tools
**User Story**: As a teacher, I want to recommend specific content to students so I can guide their learning.

#### Acceptance Criteria
- Teachers can assign/recommend topics to individual students or whole class
- Students see recommendations in their dashboard
- Recommendations include optional due dates
- Teachers can add context/instructions with recommendations
- Track which students have completed recommended content
- Send notifications to students about new recommendations

#### Technical Implementation

**API Endpoints**:
```
POST /api/v1/teachers/recommendations              # Create recommendation
GET  /api/v1/teachers/recommendations/{id}         # Get recommendation details
PUT  /api/v1/teachers/recommendations/{id}         # Update recommendation
DELETE /api/v1/teachers/recommendations/{id}       # Delete recommendation
GET  /api/v1/students/{id}/recommendations         # Student's recommendations
```

**Recommendation Object**:
```json
{
  "recommendation_id": "rec_789",
  "topic_id": "topic_phys_mech_newton_3",
  "created_by_teacher_id": "tch_456",
  "recipients": {
    "type": "class",  // or "student"
    "class_id": "cls_101",
    // or "student_ids": ["stu_123", "stu_456"]
  },
  "instructions": "Watch this before Friday's lab",
  "due_date": "2025-01-18T23:59:59Z",
  "priority": "high",  // low, medium, high
  "created_at": "2025-01-15T10:00:00Z",
  "completion_stats": {
    "total_recipients": 28,
    "completed": 15,
    "in_progress": 8,
    "not_started": 5
  }
}
```

**Frontend Components**:
- `RecommendationForm.tsx` - Create recommendation
- `RecommendationsList.tsx` - Teacher's recommendations
- `StudentRecommendations.tsx` - Student view of recommendations
- `RecommendationCard.tsx` - Individual recommendation
- `CompletionTracker.tsx` - Track completion

**Notification System**:
- Email notification to students (optional)
- In-app notification badge
- Reminder 1 day before due date
- Summary email to teacher on due date

---

## Administrative Features

### F10: Organization & User Management

**Priority**: P0 (Critical)
**Epic**: Administration
**User Story**: As a school admin, I want to manage users and organizational structure so I can set up my school.

#### Acceptance Criteria
- School admins can create/edit/deactivate teacher accounts
- Teachers can create/edit student accounts
- Bulk user import via CSV
- Assign teachers to classes
- Assign students to classes (with class codes or manual assignment)
- Set school-wide settings (default interests, allowed topics, etc.)
- View organization hierarchy (district → schools → teachers → classes → students)

#### Technical Implementation

**API Endpoints**:
```
POST   /api/v1/admin/users                    # Create user
GET    /api/v1/admin/users                    # List users (with filters)
GET    /api/v1/admin/users/{id}               # Get user details
PUT    /api/v1/admin/users/{id}               # Update user
DELETE /api/v1/admin/users/{id}               # Deactivate user
POST   /api/v1/admin/users/bulk-import        # CSV import

POST   /api/v1/admin/classes                  # Create class
PUT    /api/v1/admin/classes/{id}/students    # Assign students to class
PUT    /api/v1/admin/classes/{id}/teachers    # Assign teachers to class
```

**CSV Import Format**:
```csv
email,role,first_name,last_name,grade_level,class_code
jane.doe@school.edu,student,Jane,Doe,10,PHY101-A
john.smith@school.edu,teacher,John,Smith,,
```

**Frontend Components**:
- `AdminDashboard.tsx` - Main admin panel
- `UserManagement.tsx` - User list/management
- `UserForm.tsx` - Create/edit user
- `BulkImport.tsx` - CSV upload interface
- `ClassManagement.tsx` - Class creation/assignment
- `OrganizationTree.tsx` - Visual org hierarchy

**User Roles & Permissions**:
- **District Admin**: Manage all schools in district
- **School Admin**: Manage users in their school
- **Teacher**: Manage students in their classes
- **Student**: Access learning content only

**Validation Rules**:
- Email must be unique within organization
- Students require grade_level
- Teachers must belong to at least one school
- Class codes must be unique within school

---

### F11: Analytics & Reporting

**Priority**: P1 (High)
**Epic**: Administration
**User Story**: As a school admin, I want to see system-wide analytics so I can measure program success.

#### Acceptance Criteria
- District/school-level dashboards
- Key metrics: total users, active users, videos watched, engagement rate
- Usage trends over time (daily, weekly, monthly)
- Most popular topics and interests
- Teacher adoption rate
- Student activation rate (% of students who watched ≥1 video)
- Export data to CSV/PDF for reports
- Compare metrics across schools (district admin only)

#### Technical Implementation

**API Endpoints**:
```
GET /api/v1/admin/analytics/overview           # System overview
GET /api/v1/admin/analytics/usage              # Usage trends
GET /api/v1/admin/analytics/topics             # Topic analytics
GET /api/v1/admin/analytics/export             # Export data
```

**Analytics Response**:
```json
{
  "period": "last_30_days",
  "overview": {
    "total_students": 500,
    "active_students": 350,
    "activation_rate_percent": 70,
    "total_teachers": 25,
    "active_teachers": 22,
    "teacher_adoption_rate_percent": 88,
    "total_videos_watched": 2450,
    "total_learning_hours": 612,
    "avg_videos_per_student": 7,
    "cache_hit_rate_percent": 18
  },
  "daily_usage": [
    {
      "date": "2025-01-15",
      "active_students": 180,
      "videos_watched": 95,
      "total_minutes": 1425
    }
  ],
  "top_topics": [
    {
      "topic_id": "topic_phys_mech_newton_3",
      "topic_name": "Newton's Third Law",
      "videos_generated": 45,
      "unique_students": 38
    }
  ],
  "top_interests": [
    {
      "interest_id": "int_basketball",
      "interest_name": "Basketball",
      "usage_count": 120
    }
  ]
}
```

**Frontend Components**:
- `AnalyticsDashboard.tsx` - Main analytics view
- `KPICards.tsx` - Key metric cards
- `UsageTrendChart.tsx` - Time series charts
- `TopicDistribution.tsx` - Topic popularity chart
- `InterestDistribution.tsx` - Interest usage chart
- `ExportReport.tsx` - Report generation

**Charts & Visualizations**:
- Line charts: Daily/weekly/monthly usage trends
- Bar charts: Top topics, top interests
- Pie charts: Subject distribution, grade level distribution
- Heat maps: Activity by day of week/hour

**Target KPIs** (from PRD):
- 50% teacher adoption by end of pilot
- 30% student activation by end of pilot
- 3 videos watched per activated student per week
- 15% cache hit rate
- < 10 second avg generation time

---

## AI Content Generation Features

### F12: AI Script Generation with RAG

**Priority**: P0 (Critical)
**Epic**: AI Pipeline
**User Story**: As the system, I want to generate accurate educational scripts using RAG so content is factually correct.

#### Acceptance Criteria
- Retrieve relevant context from OpenStax OER content (top 5 chunks)
- Generate script using Gemini 1.5 Pro with LearnLM prompting
- Script includes topic introduction, explanation with analogy, examples
- Script incorporates student's interest naturally
- Script length: 100-150 words (60-90 seconds of narration)
- Script structured as JSON with scenes
- Each scene has narration text and visual description
- Content is grade-level appropriate
- Safety checks for inappropriate content

#### Technical Implementation

**Processing Pipeline**:
```
1. Input Validation
   ↓
2. Canonical Interest Resolution
   ↓
3. RAG Retrieval (Vector Search)
   ↓
4. Script Generation (Gemini)
   ↓
5. Safety Filtering
   ↓
6. Output Validation
```

**Vector Search Query**:
```python
def retrieve_oer_context(topic_id: str, num_chunks: int = 5):
    # Get topic metadata
    topic = get_topic_metadata(topic_id)

    # Create embedding for query
    query_text = f"{topic.name} {topic.description} {topic.key_concepts}"
    query_embedding = create_embedding(query_text)

    # Search vector database
    results = vector_search(
        embedding=query_embedding,
        num_neighbors=num_chunks,
        filter={"subject": topic.subject}
    )

    return [r.text for r in results]
```

**Prompt Template**:
```
You are an expert educational content creator using LearnLM methodology.

Topic: {topic_name}
Student Interest: {interest_name}
Grade Level: {grade_level}
Style: {content_style}

Educational Context:
{oer_chunks}

Create a 60-90 second educational video script that:
1. Introduces the topic clearly
2. Explains the concept using an analogy to {interest_name}
3. Provides a concrete example
4. Uses grade-appropriate language for grade {grade_level}

Output as JSON:
{
  "scenes": [
    {
      "narration": "text to be spoken",
      "visual_description": "what to show on screen",
      "duration_seconds": 15
    }
  ]
}
```

**Output Validation**:
- Total duration between 60-90 seconds
- 3-6 scenes
- Each scene 10-30 seconds
- Narration is complete sentences
- Visual descriptions are specific
- No inappropriate content (checked by safety filter)

**Error Handling**:
- If Gemini API fails → Retry with exponential backoff (max 3 attempts)
- If output invalid JSON → Log error, retry with stricter prompt
- If safety check fails → Return generic error, log for review
- If generation timeout → Return error after 10 seconds

---

### F13: Text-to-Speech Audio Generation

**Priority**: P0 (Critical)
**Epic**: AI Pipeline
**User Story**: As the system, I want to convert scripts to natural-sounding speech so videos have engaging narration.

#### Acceptance Criteria
- Convert script narration to speech using Google Cloud TTS
- Use Neural2 voices for natural sound
- Voice selection based on content (default: en-US-Neural2-A)
- Audio format: MP3, 44.1kHz sample rate
- Clear pronunciation of technical terms
- Natural pacing and inflection
- SSML support for emphasis and pauses
- Audio files stored in Cloud Storage

#### Technical Implementation

**TTS API Call**:
```python
from google.cloud import texttospeech

def generate_audio(narration_text: str, voice_name: str = "en-US-Neural2-A"):
    client = texttospeech.TextToSpeechClient()

    # Enhance with SSML for better delivery
    ssml_text = add_ssml_markup(narration_text)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        sample_rate_hertz=44100,
        speaking_rate=1.0,
        pitch=0.0
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content
```

**SSML Enhancements**:
```xml
<speak>
  <p>
    <s>Newton's Third Law states that for every action, there is an equal and opposite reaction.</s>
    <break time="500ms"/>
    <s>Let's see how this applies to <emphasis level="moderate">basketball</emphasis>.</s>
  </p>
</speak>
```

**Audio Processing**:
1. Generate audio for each scene separately
2. Store audio files in Cloud Storage with unique names
3. Generate signed URLs (24-hour expiration) for Nano Banana API
4. Clean up temp audio files after video generation

**Voice Selection Strategy**:
- Default: `en-US-Neural2-A` (neutral, clear)
- Science topics: Slightly lower pitch for authority
- Math topics: Standard neutral voice
- Future: Let students choose voice preference

**Quality Assurance**:
- Verify audio file size > 0 bytes
- Check audio duration matches expected length
- Validate MP3 format
- Log TTS API response time

---

### F14: Video Generation with Nano Banana

**Priority**: P0 (Critical)
**Epic**: AI Pipeline
**User Story**: As the system, I want to generate animated educational videos so students have engaging visual content.

#### Acceptance Criteria
- Generate video using Nano Banana API
- Video includes animated scenes with narration
- Visual style: educational, animated, professional
- Resolution: 1920x1080 (Full HD)
- Frame rate: 30fps
- Video synced with audio narration
- Scenes transition smoothly
- Final video stored in Cloud Storage
- Generation completes within 60 seconds

#### Technical Implementation

**Nano Banana API Integration**:
```python
import requests

def generate_video(scenes: List[Scene], audio_url: str):
    payload = {
        "scenes": [
            {
                "visual_description": scene.visual_description,
                "duration_seconds": scene.duration_seconds,
                "transition": "fade"
            }
            for scene in scenes
        ],
        "audio_url": audio_url,
        "style": "educational_animated",
        "resolution": "1920x1080",
        "fps": 30,
        "output_format": "mp4"
    }

    headers = {
        "Authorization": f"Bearer {NANO_BANANA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Initiate generation
    response = requests.post(
        "https://api.nanobanana.ai/v1/generate",
        json=payload,
        headers=headers
    )

    job_id = response.json()["job_id"]

    # Poll for completion
    return poll_video_completion(job_id, max_wait_seconds=60)

def poll_video_completion(job_id: str, max_wait_seconds: int):
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        response = requests.get(
            f"https://api.nanobanana.ai/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {NANO_BANANA_API_KEY}"}
        )

        data = response.json()

        if data["status"] == "completed":
            return data["video_url"]
        elif data["status"] == "failed":
            raise VideoGenerationError(data["error"])

        time.sleep(2)  # Poll every 2 seconds

    raise TimeoutError("Video generation exceeded time limit")
```

**Scene Formatting**:
```json
{
  "scenes": [
    {
      "visual_description": "Animated basketball player jumping to shoot a ball, with arrows showing force directions",
      "duration_seconds": 15,
      "transition": "fade"
    },
    {
      "visual_description": "Split screen: player pushing down on ground (action), ground pushing up on player (reaction)",
      "duration_seconds": 20,
      "transition": "slide_left"
    }
  ],
  "audio_url": "https://storage.googleapis.com/bucket/audio.mp3",
  "style": "educational_animated",
  "resolution": "1920x1080"
}
```

**Video Post-Processing**:
1. Download video from Nano Banana
2. Upload to Cloud Storage bucket
3. Generate signed URL for playback
4. Save metadata to database
5. Clean up temporary files

**Error Handling**:
- Nano Banana API timeout → Retry once, then fail gracefully
- Invalid scene description → Log warning, use fallback description
- Video generation failed → Return error to user with retry option
- Rate limit exceeded → Queue request for later processing

**Rate Limiting**:
- Nano Banana API: 10 requests/minute
- Implement queue system with exponential backoff
- Cache identical requests to avoid regeneration

---

### F15: Content Caching & Reuse

**Priority**: P1 (High)
**Epic**: AI Pipeline
**User Story**: As the system, I want to cache generated content so I can serve it faster and reduce costs.

#### Acceptance Criteria
- Check cache before generating new content
- Cache key: (topic_id, interest_id, content_style)
- Cache TTL: 30 days
- Return cached content immediately if available
- Track cache hit rate
- Invalidate cache when content quality issues reported
- Admin can manually clear cache for specific content

#### Technical Implementation

**Cache Check Logic**:
```python
def request_content(topic_id, interest_id, style="conversational"):
    # Generate cache key
    cache_key = f"{topic_id}:{interest_id}:{style}"

    # Check if content exists in cache (< 30 days old)
    cached_content = db.query(
        GeneratedContent
    ).filter(
        GeneratedContent.topic_id == topic_id,
        GeneratedContent.interest_id == interest_id,
        GeneratedContent.style == style,
        GeneratedContent.created_at > datetime.now() - timedelta(days=30)
    ).first()

    if cached_content:
        # Cache hit - return immediately
        record_cache_hit(topic_id, interest_id)
        return {
            "status": "completed",
            "content_id": cached_content.id,
            "video_url": cached_content.video_url,
            "from_cache": True
        }

    # Cache miss - trigger generation
    record_cache_miss(topic_id, interest_id)
    return trigger_generation(topic_id, interest_id, style)
```

**Cache Metrics**:
```python
def calculate_cache_hit_rate(period_days=7):
    start_date = datetime.now() - timedelta(days=period_days)

    total_requests = db.query(func.count(ContentRequest.id)).filter(
        ContentRequest.created_at > start_date
    ).scalar()

    cache_hits = db.query(func.count(ContentRequest.id)).filter(
        ContentRequest.created_at > start_date,
        ContentRequest.cache_hit == True
    ).scalar()

    return (cache_hits / total_requests * 100) if total_requests > 0 else 0
```

**Cache Invalidation**:
- Automatic: After 30 days
- Manual: Admin can invalidate specific content
- Quality-based: User reports issue → flag for review → invalidate if confirmed
- Bulk: Admin can clear all cache for a topic

**Database Schema**:
```sql
generated_content (
  id, topic_id, interest_id, style,
  script_json, audio_url, video_url,
  generation_time_seconds,
  created_at, last_accessed_at,
  access_count, invalidated
)

content_requests (
  id, student_id, topic_id, interest_id,
  content_id, cache_hit, generation_time_ms,
  created_at
)
```

**Target**: 15% cache hit rate by end of pilot

---

## System Features

### F16: Safety & Content Moderation

**Priority**: P0 (Critical)
**Epic**: Safety
**User Story**: As the system, I want to filter inappropriate content so students are protected.

#### Acceptance Criteria
- Input validation: Block inappropriate queries
- Canonical interest enforcement (no custom interests for MVP)
- Output safety check on generated scripts
- PII detection and removal
- Profanity filtering
- Age-appropriate content verification
- Logging of all safety incidents
- Admin review queue for flagged content

#### Technical Implementation

**See AI_SAFETY_GUARDRAILS.md for complete specifications**

**Safety Layers**:
1. **Input Layer**: Validate and sanitize user input
2. **Generation Layer**: Use safe generation parameters
3. **Output Layer**: Filter generated content
4. **Monitoring Layer**: Track and alert on safety incidents

**Incident Logging**:
```python
def log_safety_incident(
    incident_type: str,
    severity: str,
    details: dict,
    student_id: str = None
):
    incident = SafetyIncident(
        incident_type=incident_type,  # "inappropriate_query", "unsafe_output", etc.
        severity=severity,  # "low", "medium", "high", "critical"
        details_json=json.dumps(details),
        student_id=student_id,
        timestamp=datetime.now(),
        resolved=False
    )
    db.add(incident)

    if severity in ["high", "critical"]:
        send_alert_to_admins(incident)
```

---

### F17: Error Handling & Reliability

**Priority**: P0 (Critical)
**Epic**: System Quality
**User Story**: As the system, I want to handle errors gracefully so users have a good experience even when things go wrong.

#### Acceptance Criteria
- All API errors return standardized error responses
- User-friendly error messages (no technical jargon)
- Automatic retry with exponential backoff for transient failures
- Fallback responses when AI services unavailable
- Dead letter queue for failed messages
- Health check endpoints for all services
- Graceful degradation when non-critical services down
- Comprehensive error logging for debugging

#### Technical Implementation

**Error Response Format**:
```json
{
  "error": {
    "code": "GENERATION_TIMEOUT",
    "message": "Video generation took longer than expected. Please try again.",
    "details": {
      "request_id": "req_123",
      "retry_after_seconds": 10
    },
    "retry_allowed": true,
    "support_link": "https://support.vividly.com/generation-timeout"
  }
}
```

**Error Codes**:
- `VALIDATION_ERROR`: Invalid input
- `AUTHENTICATION_ERROR`: Auth failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `RATE_LIMIT_ERROR`: Too many requests
- `GENERATION_TIMEOUT`: Content generation timeout
- `SERVICE_UNAVAILABLE`: External service down
- `INTERNAL_ERROR`: Unexpected server error

**Retry Strategy**:
```python
def exponential_backoff_retry(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

**Health Checks**:
```
GET /health
Response:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "vertex_ai": "healthy",
    "cloud_storage": "healthy",
    "nano_banana": "degraded"  // Still functional but slow
  },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

---

### F18: Performance & Scalability

**Priority**: P1 (High)
**Epic**: System Quality
**User Story**: As the system, I want to serve content quickly even under high load so students have a responsive experience.

#### Acceptance Criteria
- API response time < 200ms (p50), < 500ms (p95)
- Content generation < 10 seconds average
- Support 500 concurrent users
- Database queries optimized with proper indexes
- CDN for video delivery
- Horizontal scaling for Cloud Run services
- Connection pooling for database
- Redis cache for frequently accessed data (future)

#### Technical Implementation

**Performance Targets**:
- API Gateway: < 200ms p50, < 500ms p95
- Content Generation: < 10s average
- Video Playback Startup: < 2s
- Page Load Time: < 1.5s

**Database Optimization**:
```sql
-- Indexes for common queries
CREATE INDEX idx_content_requests_student ON content_requests(student_id, created_at);
CREATE INDEX idx_generated_content_cache ON generated_content(topic_id, interest_id, style, created_at);
CREATE INDEX idx_student_progress_lookup ON student_progress(student_id, content_id);
```

**Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

**Cloud Run Autoscaling**:
```yaml
min_instances: 1
max_instances: 20
cpu: 2
memory: 2Gi
concurrency: 100  # Requests per instance
```

**CDN Configuration**:
- Videos served from Cloud Storage with Cloud CDN
- Cache-Control headers: max-age=31536000 (1 year) for videos
- Signed URLs prevent unauthorized access

**Monitoring**:
- Track p50, p95, p99 latencies
- Alert if p95 > 1 second
- Dashboard showing real-time performance metrics

---

## Feature Dependencies

```
F1 (Auth) → F2 (Interests) → F4 (Content Request) → F5 (Playback)
                ↓
            F3 (Browse)

F7 (Teacher Dashboard) → F8 (Student Progress) → F9 (Recommendations)

F10 (User Management) → F7, F8, F9, F11

F12 (Script Gen) → F13 (TTS) → F14 (Video) → F15 (Cache)
                                              ↓
                                        F4, F5

F16 (Safety) → All content features
F17 (Error Handling) → All features
F18 (Performance) → All features
```

## Implementation Priority

### Phase 1: Core MVP (Weeks 1-4)
- F1: Authentication
- F2: Interest Selection
- F4: Content Request
- F12: Script Generation
- F13: TTS
- F14: Video Generation
- F5: Video Playback
- F16: Safety (basic)
- F17: Error Handling (basic)

### Phase 2: Teacher & Admin (Weeks 5-6)
- F10: User Management
- F7: Teacher Dashboard
- F8: Student Progress
- F3: Topic Browse

### Phase 3: Analytics & Optimization (Weeks 7-8)
- F6: Learning History
- F11: Analytics
- F15: Caching
- F18: Performance Optimization
- F9: Recommendations

---

**End of Feature Specifications**
