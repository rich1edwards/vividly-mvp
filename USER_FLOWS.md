# User Flows

## Table of Contents
1. [Overview](#overview)
2. [Student Flows](#student-flows)
   - [Student Onboarding Flow](#student-onboarding-flow)
   - [Content Discovery and Request Flow](#content-discovery-and-request-flow)
   - [Video Playback and Learning Flow](#video-playback-and-learning-flow)
   - [Learning History Review Flow](#learning-history-review-flow)
3. [Teacher Flows](#teacher-flows)
   - [Teacher Onboarding Flow](#teacher-onboarding-flow)
   - [Class Setup and Management Flow](#class-setup-and-management-flow)
   - [Student Monitoring Flow](#student-monitoring-flow)
   - [Content Recommendation Flow](#content-recommendation-flow)
4. [Admin Flows](#admin-flows)
   - [Organization Setup Flow](#organization-setup-flow)
   - [User Management Flow](#user-management-flow)
   - [System Monitoring Flow](#system-monitoring-flow)
5. [Error Handling Flows](#error-handling-flows)
6. [Cross-Role Interactions](#cross-role-interactions)

---

## Overview

This document provides detailed user journey flowcharts for all three user roles in the Vividly platform:
- **Students**: High school students (grades 9-12) consuming personalized STEM content
- **Teachers**: Educators managing classes and monitoring student progress
- **Admins**: School/district administrators managing users and viewing analytics

Each flow includes:
- Step-by-step user actions
- System responses
- Decision points
- Error handling paths
- Integration touchpoints with features from FEATURE_SPECIFICATIONS.md

**Notation**:
- `[ ]` = User action/input
- `( )` = System process
- `{ }` = Decision point
- `< >` = External system/API
- `[!]` = Error state
- `-->` = Flow direction

---

## Student Flows

### Student Onboarding Flow

**Features**: F1 (Authentication), F2 (Interest Selection)

**Entry Point**: Student receives invitation link from teacher

```
┌─────────────────────────────────────────────────────────────────┐
│                   STUDENT ONBOARDING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

START: Student receives invitation email
│
├─> [1. Click invitation link]
│   URL: https://app.vividly.edu/invite?token=abc123
│
├─> (2. System validates invite token)
│   API: GET /api/v1/students/invite/{token}
│   {Valid token?}
│   ├─ NO --> [!] "Invalid or expired invitation" --> END
│   └─ YES --> Continue
│
├─> [3. Student views registration form]
│   Display:
│   - Pre-filled: Email, Grade, Organization
│   - Required: First Name, Last Name, Password
│   - Optional: Preferred Name
│
├─> [4. Student fills registration form]
│   Validation rules:
│   - Password: 8+ chars, uppercase, lowercase, number
│   - Names: 1-50 chars
│
├─> [5. Student submits form]
│   API: POST /api/v1/students/register
│   {Valid data?}
│   ├─ NO --> [!] Display validation errors --> Return to step 4
│   └─ YES --> Continue
│
├─> (6. System creates student account)
│   - Hash password (bcrypt, 12 rounds)
│   - Create user record
│   - Create student profile
│   - Mark invite as used
│   - Generate JWT token
│
├─> (7. System redirects to Interest Selection)
│   Auto-login with JWT
│
├─> [8. Student views Interest Selection page]
│   Display: "Welcome! Let's personalize your learning experience"
│   Show 60 canonical interests in 6 categories:
│   - Sports & Athletics (10 interests)
│   - Arts & Creativity (10 interests)
│   - Technology & Gaming (10 interests)
│   - Career & Professional (10 interests)
│   - Nature & Outdoors (10 interests)
│   - Social & Community (10 interests)
│
├─> [9. Student selects 1-5 interests]
│   UI: Card-based selection with icons
│   Validation: Min 1, Max 5 interests
│
├─> [10. Student clicks "Get Started"]
│   API: POST /api/v1/students/interests
│   {Valid selection?}
│   ├─ NO --> [!] "Please select 1-5 interests" --> Return to step 9
│   └─ YES --> Continue
│
├─> (11. System saves interest preferences)
│   - Store selected interests in student_interests table
│   - Set onboarding_completed = true
│   - Track event: student_onboarded
│
├─> (12. System redirects to Topic Browse)
│   URL: /dashboard/browse
│
└─> END: Student ready to explore content

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Student already has account
├─> [1. Navigate to login page]
├─> [2. Enter email + password]
├─> [3. Submit login form]
├─> (4. System validates credentials)
│   {Valid?}
│   ├─ NO --> [!] "Invalid credentials" --> Retry (max 5 attempts)
│   └─ YES --> (5. Generate JWT) --> (6. Redirect to dashboard)

A2. Student forgot password
├─> [1. Click "Forgot Password"]
├─> [2. Enter email]
├─> (3. System sends reset link to teacher)
├─> [4. Teacher resets password via admin portal]
└─> (5. Student receives new temporary password)

A3. Invite token expired
├─> [!] "Invitation expired"
├─> Display: "Please contact your teacher for a new invitation"
└─> END

TIME ESTIMATES:
- First-time registration: 2-3 minutes
- Interest selection: 1-2 minutes
- Total onboarding: 3-5 minutes
```

---

### Content Discovery and Request Flow

**Features**: F3 (Topic Browse), F4 (Request Content)

**Entry Point**: Student clicks "Browse Topics" from dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTENT DISCOVERY AND REQUEST FLOW                  │
└─────────────────────────────────────────────────────────────────┘

START: Student on dashboard
│
├─> [1. Click "Browse Topics" or search bar]
│   Display: Topic Browse page with 4 subjects
│
├─> [2. Student views topic hierarchy]
│   Layout:
│   ┌──────────────────────────────────────────────────┐
│   │ Search: [________________] 🔍                    │
│   │                                                  │
│   │ 📚 Physics (35 topics)                  [Expand]│
│   │ 🧪 Chemistry (35 topics)                [Expand]│
│   │ 🧬 Biology (35 topics)                  [Expand]│
│   │ 💻 Computer Science (35 topics)         [Expand]│
│   └──────────────────────────────────────────────────┘
│
├─> {Student chooses navigation method}
│   ├─ Option A: Browse by expanding subjects
│   ├─ Option B: Use search bar
│   └─ Option C: Filter by grade level
│
├─> [3a. Browse: Student expands subject]
│   Example: Click "Physics" accordion
│   Display:
│   📚 Physics
│     └─ 🔧 Mechanics
│         ├─ ⚡ Kinematics
│         │   ├─ Motion in One Dimension
│         │   ├─ Motion in Two Dimensions
│         │   └─ Projectile Motion
│         ├─ 💪 Forces
│         │   ├─ Newton's Laws
│         │   │   ├─ Newton's First Law ✨
│         │   │   ├─ Newton's Second Law ✨
│         │   │   └─ Newton's Third Law ✨
│         │   └─ Force Diagrams
│         └─ 🔄 Energy and Work
│
│   Note: ✨ indicates topic has available content
│
├─> [3b. Search: Student types query]
│   Example: "newton's third law"
│   API: GET /api/v1/topics/search?q=newton's+third+law
│   Display: Ranked results with relevance scores
│
├─> [3c. Filter: Student selects grade level]
│   Dropdown: Grade 9 | 10 | 11 | 12
│   System filters topics by grade_level_min/max
│
├─> [4. Student clicks on specific topic]
│   Example: "Newton's Third Law"
│   URL: /topics/topic_phys_mech_newton_3
│
├─> [5. System displays Topic Detail page]
│   API: GET /api/v1/topics/{topic_id}
│   Display:
│   ┌──────────────────────────────────────────────────┐
│   │ Newton's Third Law                               │
│   │ Subject: Physics | Category: Mechanics           │
│   │ Grade Level: 9-11                                │
│   │                                                  │
│   │ Description:                                     │
│   │ For every action, there is an equal and         │
│   │ opposite reaction...                             │
│   │                                                  │
│   │ Prerequisites: ✓ Newton's First Law              │
│   │               ✓ Newton's Second Law              │
│   │                                                  │
│   │ Related Topics:                                  │
│   │ → Force Diagrams                                 │
│   │ → Momentum                                       │
│   │                                                  │
│   │ [Get Personalized Video] 🎥                      │
│   └──────────────────────────────────────────────────┘
│
├─> [6. Student clicks "Get Personalized Video"]
│   Triggers content request modal
│
├─> [7. System displays content request modal]
│   ┌──────────────────────────────────────────────────┐
│   │ Request Personalized Content                     │
│   │                                                  │
│   │ Topic: Newton's Third Law                        │
│   │                                                  │
│   │ Choose an interest (optional):                   │
│   │ ○ Basketball 🏀                                  │
│   │ ○ Video Games 🎮  [Selected from profile]       │
│   │ ○ Music Production 🎵                            │
│   │ ○ None - General explanation                    │
│   │                                                  │
│   │ Ask a specific question (optional):              │
│   │ [_______________________________________]        │
│   │ Example: "Why do I get pushed back when I       │
│   │ shoot a basketball?"                             │
│   │                                                  │
│   │ Explanation style:                               │
│   │ ● Conversational  ○ Formal  ○ Simple            │
│   │                                                  │
│   │ [Cancel]              [Request Video] 🎬         │
│   └──────────────────────────────────────────────────┘
│
├─> [8. Student customizes request and submits]
│   Example selections:
│   - Interest: Basketball
│   - Query: "Why do I get pushed back when I shoot?"
│   - Style: Conversational
│
├─> (9. System validates request)
│   API: POST /api/v1/students/content/request
│   Request body:
│   {
│     "topic_id": "topic_phys_mech_newton_3",
│     "interest_id": "int_basketball",
│     "query": "Why do I get pushed back when I shoot?",
│     "style": "conversational"
│   }
│
│   Validation:
│   - Topic exists and is active
│   - Interest is in student's profile (if provided)
│   - Query length < 500 chars
│   - Rate limit: 10 requests per hour
│
│   {Valid?}
│   ├─ NO --> [!] Display error --> Return to step 7
│   └─ YES --> Continue
│
├─> (10. System creates content request)
│   - Generate request_id
│   - Set status = "processing"
│   - Estimate time: 6-10 seconds
│   - Publish to Pub/Sub: content-requests-dev
│   - Return 202 Accepted
│
├─> [11. System displays processing modal]
│   ┌──────────────────────────────────────────────────┐
│   │ Creating Your Personalized Video                 │
│   │                                                  │
│   │ ░░░░░░░░░░░░░░░░░░░░░░░░ 45%                    │
│   │                                                  │
│   │ Current stage:                                   │
│   │ ✓ Validating request                             │
│   │ ✓ Retrieving context from OpenStax              │
│   │ ⏳ Generating personalized script...             │
│   │ ⏸ Creating audio narration                       │
│   │ ⏸ Generating video animation                     │
│   │                                                  │
│   │ Estimated time remaining: 4 seconds              │
│   └──────────────────────────────────────────────────┘
│
│   WebSocket connection for real-time updates:
│   ws://api.vividly.edu/ws/content-requests/{request_id}
│
├─> (12. Background: Content Worker processes request)
│   See AI_GENERATION_SPECIFICATIONS.md for detailed pipeline
│   Stages:
│   1. Validating (5%)
│   2. Retrieving Context (15%) - RAG from Vertex AI
│   3. Generating Script (40%) - Gemini 1.5 Pro
│   4. Creating Audio (60%) - TTS
│   5. Generating Video (90%) - Nano Banana API
│   6. Finalizing (100%) - Upload to GCS, create record
│
├─> (13. System completes generation)
│   WebSocket message:
│   {
│     "request_id": "req_abc123",
│     "status": "completed",
│     "content_id": "content_xyz789"
│   }
│
├─> [14. System redirects to video player]
│   URL: /content/content_xyz789
│   Automatically begins playback
│
└─> END: Student watching video (Continue to Video Playback Flow)

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Content already cached
├─> (9. System checks cache)
│   Query: generated_content table
│   WHERE topic_id = ? AND interest_id = ?
│   AND created_at > NOW() - INTERVAL '30 days'
│   {Cache hit?}
│   ├─ YES --> (Skip generation) --> [14. Redirect to cached video]
│   └─ NO --> Continue with generation

A2. Generation fails
├─> (12. Content Worker encounters error)
│   Examples: API timeout, safety filter triggered, invalid context
│   WebSocket message: {"status": "failed", "error": "..."}
├─> [!] Display error modal
│   "We couldn't generate your video. Please try again."
│   [Retry] [Browse Other Topics]
├─> {Student action}
│   ├─ Retry --> Return to step 9
│   └─ Browse --> Return to step 2

A3. Rate limit exceeded
├─> (9. System checks rate limit)
│   {Exceeded?}
│   ├─ YES --> [!] "You've reached your hourly limit (10 videos).
│   │             Try again in X minutes."
│   └─> END

A4. Network disconnection during generation
├─> [!] WebSocket connection lost
├─> System continues generation in background
├─> [Display reconnection UI]
│   "Connection lost. Checking status..."
│   [Check Status] [Cancel Request]
├─> {Student action}
│   ├─ Check Status --> Poll API: GET /api/v1/students/content/requests/{id}
│   └─ Cancel --> API: DELETE /api/v1/students/content/requests/{id}

TIME ESTIMATES:
- Topic browsing: 30-60 seconds
- Content customization: 20-30 seconds
- Video generation: 6-10 seconds
- Total: 1-2 minutes
```

---

### Video Playback and Learning Flow

**Features**: F5 (Video Playback), F6 (Learning History)

**Entry Point**: Student arrives at video player (from content request or history)

```
┌─────────────────────────────────────────────────────────────────┐
│              VIDEO PLAYBACK AND LEARNING FLOW                    │
└─────────────────────────────────────────────────────────────────┘

START: Student on video player page
│
├─> [1. System loads video player]
│   URL: /content/{content_id}
│   API: GET /api/v1/students/content/{content_id}
│
│   Response includes:
│   - video_url (Cloud CDN)
│   - transcript
│   - topic_metadata
│   - related_topics
│
├─> [2. System displays video player interface]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │                                                              │
│   │                   [VIDEO PLAYER]                             │
│   │                    1920 x 1080                               │
│   │                                                              │
│   │  ⏯ ⏮ ⏭  0:00 ━━━━━━━━━━○━━━━━━━━━━ 2:45  🔊 ⚙ ⛶           │
│   │                                                              │
│   ├──────────────────────────────────────────────────────────────┤
│   │ Newton's Third Law - Basketball Edition 🏀                   │
│   │ Physics > Mechanics > Forces                                 │
│   │                                                              │
│   │ In this video, we explore Newton's Third Law through         │
│   │ basketball shooting mechanics...                             │
│   │                                                              │
│   │ [📝 View Transcript] [🔖 Save] [↗️ Share]                    │
│   │                                                              │
│   │ Related Topics:                                              │
│   │ → Newton's Second Law                                        │
│   │ → Momentum and Impulse                                       │
│   │ → Force Diagrams                                             │
│   │                                                              │
│   │ Continue Learning:                                           │
│   │ [Get Another Video on This Topic]                            │
│   │ [Explore Related Topics]                                     │
│   └──────────────────────────────────────────────────────────────┘
│
├─> (3. System begins playback)
│   Video autoplay: YES
│   Default quality: 1080p (auto-adjust based on bandwidth)
│   CDN: Cloud CDN with multi-region caching
│
├─> (4. System tracks viewing analytics)
│   Events tracked every 5 seconds:
│   - current_position (seconds)
│   - playback_rate (0.5x - 2x)
│   - quality_level
│   - pause/play events
│   - seek events
│
├─> [5. Student watches video]
│   During playback:
│   - Video controls: play, pause, seek, volume, quality, fullscreen
│   - Captions: Auto-generated, always available
│   - Playback speed: 0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x
│
├─> {Student interactions during playback}
│
│   ├─> [5a. Student pauses video]
│   │   Track event: video_paused
│   │   Position: timestamp in seconds
│   │
│   ├─> [5b. Student seeks to different position]
│   │   Track event: video_seeked
│   │   From: previous_timestamp
│   │   To: new_timestamp
│   │
│   ├─> [5c. Student adjusts playback speed]
│   │   Track event: playback_rate_changed
│   │   Rate: 0.5x - 2x
│   │
│   ├─> [5d. Student views transcript]
│   │   Display: Side panel with timestamped transcript
│   │   Feature: Click timestamp to jump to that point
│   │   ┌────────────────────────────────────┐
│   │   │ Transcript                         │
│   │   ├────────────────────────────────────┤
│   │   │ [0:00] Hey there! Ever wonder why  │
│   │   │        you feel a push when you... │
│   │   │                                    │
│   │   │ [0:15] This is Newton's Third Law  │
│   │   │        in action. When you push... │
│   │   │                                    │
│   │   │ [0:32] Let's break it down with... │
│   │   └────────────────────────────────────┘
│   │
│   ├─> [5e. Student saves video]
│   │   API: POST /api/v1/students/bookmarks
│   │   Body: {"content_id": "content_xyz789"}
│   │   Display: ✓ "Saved to your library"
│   │
│   └─> [5f. Student shares video]
│       Display: Share modal with options
│       - Copy link (generates student-specific share link)
│       - Share with classmates (if enabled by teacher)
│       Note: Share links expire after 7 days
│
├─> [6. Student completes video]
│   Completion threshold: Watched 90%+ of video
│
├─> (7. System records completion)
│   API: POST /api/v1/students/content/{content_id}/complete
│   Updates:
│   - learning_history.completion_status = "completed"
│   - learning_history.completed_at = NOW()
│   - Track event: video_completed
│   - Update KPIs:
│     * student_kpis.total_content_consumed += 1
│     * student_kpis.total_time_spent += video_duration
│     * topic_kpis.views_count += 1
│
├─> [8. System displays completion UI]
│   ┌──────────────────────────────────────────────────┐
│   │ 🎉 Great job! You completed this video           │
│   │                                                  │
│   │ You watched: Newton's Third Law                  │
│   │ Time spent: 2m 45s                               │
│   │                                                  │
│   │ Keep learning:                                   │
│   │ [Watch Another Video on This Topic]              │
│   │ [Explore Related Topics]                         │
│   │ [Back to Dashboard]                              │
│   └──────────────────────────────────────────────────┘
│
├─> {Student chooses next action}
│   ├─> Option A: Watch another video on same topic
│   │   Return to Content Request Flow (step 7)
│   │
│   ├─> Option B: Explore related topics
│   │   Return to Topic Browse (step 2)
│   │
│   └─> Option C: Back to dashboard
│       Continue to Dashboard/History Flow
│
└─> END: Video playback complete

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Video fails to load
├─> [!] "Video failed to load"
│   Possible causes:
│   - Network connectivity issues
│   - CDN unavailable
│   - Video file corrupted
├─> Display: [Retry] [Report Problem] [Back to Browse]
├─> {Student action}
│   ├─ Retry --> Reload video player
│   ├─ Report --> Send error report to admins
│   └─ Back --> Return to topic browse

A2. Buffering/slow connection
├─> (Auto-adjust quality)
│   1080p --> 720p --> 480p --> 360p
├─> Display: "Adjusting quality for your connection..."
├─> {Connection improves?}
│   └─ YES --> Gradually increase quality

A3. Student exits mid-playback
├─> (Save watch position)
│   learning_history.last_position = current_timestamp
├─> {Student returns later}
│   └─> [Display "Resume from X:XX" option]

A4. Video content flagged as inappropriate (rare)
├─> [!] "This video has been flagged for review"
├─> Display: [Report Issue] [Request Different Video]
├─> (Notify admins via monitoring alert)

ANALYTICS TRACKED:
- video_started (timestamp, content_id, student_id)
- video_progress (every 5s: position, rate, quality)
- video_paused (timestamp, position)
- video_seeked (from, to, direction)
- video_completed (timestamp, total_watch_time, completion_rate)
- transcript_viewed (timestamp, duration)
- video_saved (timestamp)
- video_shared (timestamp, share_method)

TIME ESTIMATES:
- Video duration: 2-4 minutes (average)
- Completion: 90%+ watched
```

---

### Learning History Review Flow

**Features**: F6 (Learning History)

**Entry Point**: Student clicks "My Learning" from dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                   LEARNING HISTORY REVIEW FLOW                   │
└─────────────────────────────────────────────────────────────────┘

START: Student on dashboard
│
├─> [1. Student clicks "My Learning" tab]
│   URL: /dashboard/history
│
├─> (2. System loads learning history)
│   API: GET /api/v1/students/me/history?limit=50&offset=0
│
│   Query filters:
│   - Show all content accessed by student
│   - Order by: accessed_at DESC
│   - Include: topic metadata, completion status, watch time
│
├─> [3. System displays learning history page]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ My Learning History                                          │
│   │                                                              │
│   │ Filters: [All] [In Progress] [Completed] [Saved]            │
│   │ Sort by: [Recent] [Completion] [Subject] [Watch Time]       │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Today                                                        │
│   │                                                              │
│   │ 📹 Newton's Third Law - Basketball Edition       ✓ Completed│
│   │    Physics > Mechanics                           2m 45s     │
│   │    Watched: 100% | Created: 2 hours ago                     │
│   │    [▶ Watch Again] [📝 Transcript] [↗️ Share]                │
│   │                                                              │
│   │ 📹 Photosynthesis - Gaming Edition              ⏸ In Progress│
│   │    Biology > Cell Processes                      1m 20s/3m  │
│   │    Watched: 45% | Created: 3 hours ago                      │
│   │    [▶ Resume] [↗️ Share]                                     │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Yesterday                                                    │
│   │                                                              │
│   │ 📹 Binary Search - Minecraft Edition            ✓ Completed│
│   │    Computer Science > Algorithms                 2m 30s     │
│   │    Watched: 100% | Created: 1 day ago                       │
│   │    [▶ Watch Again] [📝 Transcript]                           │
│   │                                                              │
│   │ 📹 Chemical Bonding - Cooking Edition           ✓ Completed│
│   │    Chemistry > Bonding                           3m 15s     │
│   │    Watched: 95% | Created: 1 day ago                        │
│   │    [▶ Watch Again] [📝 Transcript]                           │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ This Week                                                    │
│   │ ... (more videos)                                            │
│   │                                                              │
│   │ [Load More]                                                  │
│   └──────────────────────────────────────────────────────────────┘
│
├─> {Student chooses action}
│
│   ├─> [4a. Student filters history]
│   │   Options:
│   │   - All: Show all videos (default)
│   │   - In Progress: completion_status = 'in_progress'
│   │   - Completed: completion_status = 'completed'
│   │   - Saved: Show bookmarked videos only
│   │
│   │   API: GET /api/v1/students/me/history?status=completed
│   │   Re-render list with filtered results
│   │
│   ├─> [4b. Student sorts history]
│   │   Options:
│   │   - Recent: ORDER BY accessed_at DESC (default)
│   │   - Completion: ORDER BY completion_percentage DESC
│   │   - Subject: GROUP BY subject, ORDER BY accessed_at DESC
│   │   - Watch Time: ORDER BY watch_time_seconds DESC
│   │
│   │   Re-render list with new sort order
│   │
│   ├─> [4c. Student clicks "Watch Again"]
│   │   Navigate to video player with content_id
│   │   URL: /content/{content_id}
│   │   Continue to Video Playback Flow
│   │
│   ├─> [4d. Student clicks "Resume"]
│   │   Navigate to video player
│   │   Auto-seek to last_position
│   │   Continue playback from saved position
│   │
│   ├─> [4e. Student views transcript]
│   │   API: GET /api/v1/students/content/{content_id}/transcript
│   │   Display: Modal with full transcript
│   │   ┌────────────────────────────────────────────────────┐
│   │   │ Transcript: Newton's Third Law                     │
│   │   ├────────────────────────────────────────────────────┤
│   │   │ [0:00] Hey there! Ever wonder why you feel a push  │
│   │   │        when you shoot a basketball? That's         │
│   │   │        Newton's Third Law in action!               │
│   │   │                                                    │
│   │   │ [0:15] Newton's Third Law states that for every   │
│   │   │        action, there is an equal and opposite...   │
│   │   │                                                    │
│   │   │ ... (full transcript)                              │
│   │   │                                                    │
│   │   │ [Close] [Download] [Copy]                          │
│   │   └────────────────────────────────────────────────────┘
│   │
│   ├─> [4f. Student shares video]
│   │   Display: Share modal
│   │   API: POST /api/v1/students/content/{content_id}/share
│   │   Generate: time-limited share link (7 days)
│   │   Options:
│   │   - Copy link
│   │   - Share with classmates (if enabled)
│   │
│   └─> [4g. Student loads more history]
│       API: GET /api/v1/students/me/history?offset=50&limit=50
│       Append: Next 50 videos to list
│       Infinite scroll or "Load More" button
│
├─> [5. Student views learning statistics]
│   Display: Stats panel (top of page)
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Your Learning Stats                                          │
│   │                                                              │
│   │ 📊 This Week          📈 Total                               │
│   │ 12 videos watched    47 videos watched                       │
│   │ 35 minutes           2h 15m total time                       │
│   │ 4 topics explored    15 topics explored                      │
│   │                                                              │
│   │ Most Watched Subjects:                                       │
│   │ 🏆 Physics (15 videos)                                       │
│   │ 🥈 Computer Science (12 videos)                              │
│   │ 🥉 Biology (10 videos)                                       │
│   └──────────────────────────────────────────────────────────────┘
│
│   Data source: student_kpis table
│
└─> END: Student continues browsing history or returns to dashboard

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Empty history (new student)
├─> Display: Empty state message
│   ┌──────────────────────────────────────────────────┐
│   │ 🎬 No Learning History Yet                       │
│   │                                                  │
│   │ Start your learning journey by exploring         │
│   │ personalized STEM content!                       │
│   │                                                  │
│   │ [Browse Topics] [Get Started]                    │
│   └──────────────────────────────────────────────────┘

A2. Deleted video (content no longer available)
├─> Display: Grayed out entry
│   "This video is no longer available"
│   [Request New Video on This Topic]

A3. Shared video accessed by classmate
├─> Student clicks shared link
├─> System validates share token
│   {Valid and not expired?}
│   ├─ YES --> Create view-only access record
│   │         Track event: shared_content_viewed
│   │         Allow playback but don't track in viewing student's history
│   └─ NO --> [!] "This link has expired" --> [Request Your Own Video]

TIME ESTIMATES:
- Loading history: < 1 second
- Browsing/filtering: 30-60 seconds
- Resume playback: Immediate
```

---

## Teacher Flows

### Teacher Onboarding Flow

**Features**: F1 (Authentication), F7 (Teacher Dashboard)

**Entry Point**: Admin creates teacher account

```
┌─────────────────────────────────────────────────────────────────┐
│                   TEACHER ONBOARDING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

START: Admin creates teacher account
│
├─> (1. Admin creates teacher via Admin Portal)
│   API: POST /api/v1/admin/users
│   Body:
│   {
│     "email": "teacher@school.edu",
│     "role": "teacher",
│     "first_name": "Jane",
│     "last_name": "Doe",
│     "org_id": "org_school123"
│   }
│
├─> (2. System generates temporary credentials)
│   - Create user record with role = "teacher"
│   - Generate random temporary password
│   - Set must_change_password = true
│   - Generate JWT token for password reset
│
├─> (3. System sends welcome email)
│   To: teacher@school.edu
│   Subject: "Welcome to Vividly - Set Up Your Account"
│   Body:
│   """
│   Welcome to Vividly!
│
│   Your account has been created by [Admin Name] at [Organization].
│
│   Email: teacher@school.edu
│   Temporary Password: [redacted]
│
│   Please log in and change your password:
│   https://app.vividly.edu/reset-password?token=abc123
│
│   This link expires in 24 hours.
│   """
│
├─> [4. Teacher receives email and clicks link]
│   URL: /reset-password?token=abc123
│
├─> (5. System validates reset token)
│   API: GET /api/v1/auth/validate-token/{token}
│   {Valid token?}
│   ├─ NO --> [!] "Invalid or expired link" --> Contact admin
│   └─ YES --> Continue
│
├─> [6. Teacher views password setup page]
│   Display:
│   ┌──────────────────────────────────────────────────┐
│   │ Welcome to Vividly, Jane!                        │
│   │                                                  │
│   │ Please set your password to get started.         │
│   │                                                  │
│   │ Current Password (temporary):                    │
│   │ [_________________________________]              │
│   │                                                  │
│   │ New Password:                                    │
│   │ [_________________________________]              │
│   │ Must be 8+ characters with uppercase, lowercase,│
│   │ number, and special character                    │
│   │                                                  │
│   │ Confirm New Password:                            │
│   │ [_________________________________]              │
│   │                                                  │
│   │ [Set Password and Continue]                      │
│   └──────────────────────────────────────────────────┘
│
├─> [7. Teacher enters temporary password + new password]
│   Validation:
│   - Temporary password matches stored value
│   - New password meets complexity requirements
│   - New password != temporary password
│   - Confirm password matches new password
│
├─> [8. Teacher submits form]
│   API: POST /api/v1/auth/reset-password
│   Body:
│   {
│     "token": "abc123",
│     "temporary_password": "temp123",
│     "new_password": "SecurePass123!"
│   }
│
│   {Valid?}
│   ├─ NO --> [!] Display validation errors --> Return to step 7
│   └─ YES --> Continue
│
├─> (9. System updates password)
│   - Hash new password (bcrypt, 12 rounds)
│   - Update user record
│   - Set must_change_password = false
│   - Invalidate reset token
│   - Generate new JWT for session
│
├─> (10. System redirects to Teacher Dashboard)
│   Auto-login with JWT
│   URL: /teacher/dashboard
│
├─> [11. System displays Teacher Dashboard]
│   First-time setup wizard overlay:
│   ┌──────────────────────────────────────────────────┐
│   │ 👋 Welcome to Vividly!                           │
│   │                                                  │
│   │ Let's get you set up:                            │
│   │                                                  │
│   │ ✓ Account created                                │
│   │ ✓ Password set                                   │
│   │ ⏳ Create your first class                       │
│   │ ⏳ Invite students                                │
│   │                                                  │
│   │ [Get Started] [Skip for Now]                     │
│   └──────────────────────────────────────────────────┘
│
├─> {Teacher chooses action}
│   ├─> Option A: Get Started --> Continue to Class Setup Flow
│   └─> Option B: Skip --> Show empty dashboard state
│
└─> END: Teacher onboarded and on dashboard

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Teacher already has account (returning login)
├─> [1. Navigate to login page]
│   URL: /login
├─> [2. Enter email + password]
├─> [3. Submit login form]
│   API: POST /api/v1/auth/login
├─> (4. System validates credentials)
│   {Valid?}
│   ├─ NO --> [!] "Invalid credentials" --> Retry (max 5 attempts)
│   │         After 5 failed: Lockout for 15 minutes
│   └─ YES --> (5. Generate JWT) --> (6. Redirect to dashboard)

A2. Teacher forgot password
├─> [1. Click "Forgot Password" on login page]
├─> [2. Enter email]
├─> (3. System sends reset link to admin)
│   Note: Teachers cannot self-reset for security
├─> [4. Admin resets password via admin portal]
├─> (5. Teacher receives new temporary password)
└─> Return to main flow step 6

A3. Reset token expired (>24 hours)
├─> [!] "This link has expired"
├─> Display: "Please contact your administrator for a new password reset link"
├─> [Contact Admin] [Back to Login]

TIME ESTIMATES:
- Password setup: 1-2 minutes
- First-time dashboard tour: 2-3 minutes
- Total onboarding: 3-5 minutes
```

---

### Class Setup and Management Flow

**Features**: F7 (Teacher Dashboard), F1 (Student Invitations)

**Entry Point**: Teacher clicks "Create New Class" from dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│              CLASS SETUP AND MANAGEMENT FLOW                     │
└─────────────────────────────────────────────────────────────────┘

START: Teacher on dashboard
│
├─> [1. Teacher clicks "Create New Class"]
│   Button location: Top right of dashboard
│
├─> [2. System displays class creation modal]
│   ┌──────────────────────────────────────────────────┐
│   │ Create New Class                                 │
│   │                                                  │
│   │ Class Name:                                      │
│   │ [_________________________________]              │
│   │ Example: "Physics 101 - Period 3"               │
│   │                                                  │
│   │ Subject:                                         │
│   │ [▼ Select Subject ___________________]          │
│   │ Options: Physics, Chemistry, Biology,           │
│   │          Computer Science, General STEM         │
│   │                                                  │
│   │ Grade Level:                                     │
│   │ [▼ Select Grade ______________________]         │
│   │ Options: 9, 10, 11, 12, Mixed                   │
│   │                                                  │
│   │ Academic Year:                                   │
│   │ [▼ 2024-2025 ______________________]            │
│   │                                                  │
│   │ [Cancel]                [Create Class]           │
│   └──────────────────────────────────────────────────┘
│
├─> [3. Teacher fills class details]
│   Example:
│   - Name: "Physics 101 - Period 3"
│   - Subject: Physics
│   - Grade: 11
│   - Year: 2024-2025
│
├─> [4. Teacher submits form]
│   API: POST /api/v1/teacher/classes
│   Body:
│   {
│     "name": "Physics 101 - Period 3",
│     "subject": "physics",
│     "grade_level": 11,
│     "academic_year": "2024-2025"
│   }
│
│   Validation:
│   - Name: 1-100 chars
│   - Subject: Must be valid subject enum
│   - Grade: 9-12
│   - Academic year: Current or next year only
│
│   {Valid?}
│   ├─ NO --> [!] Display validation errors --> Return to step 3
│   └─ YES --> Continue
│
├─> (5. System creates class)
│   - Generate class_id
│   - Set status = "active"
│   - Associate with teacher_id
│   - Create class record in database
│   - Track event: class_created
│
├─> (6. System redirects to class detail page)
│   URL: /teacher/classes/{class_id}
│   Display: ✓ "Class created successfully!"
│
├─> [7. System displays class detail page]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Physics 101 - Period 3                      [Edit] [Archive] │
│   │ Grade 11 | Physics | 2024-2025              [+ Add Students] │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Students (0)                                                 │
│   │                                                              │
│   │ No students enrolled yet.                                    │
│   │                                                              │
│   │ [+ Invite Students] [Import from CSV]                       │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Class Statistics                                             │
│   │                                                              │
│   │ Total Students: 0                                            │
│   │ Active This Week: 0                                          │
│   │ Total Content Views: 0                                       │
│   │                                                              │
│   └──────────────────────────────────────────────────────────────┘
│
├─> [8. Teacher clicks "Invite Students"]
│   Triggers student invitation flow
│
├─> [9. System displays student invitation modal]
│   ┌──────────────────────────────────────────────────┐
│   │ Invite Students to Physics 101 - Period 3        │
│   │                                                  │
│   │ Add student emails (one per line):              │
│   │ [_____________________________________________]  │
│   │ [_____________________________________________]  │
│   │ [_____________________________________________]  │
│   │                                                  │
│   │ Or upload CSV:                                   │
│   │ [Choose File] No file selected                   │
│   │ Format: email, first_name, last_name, grade      │
│   │ [Download Template]                              │
│   │                                                  │
│   │ [Cancel]              [Send Invitations]         │
│   └──────────────────────────────────────────────────┘
│
├─> {Teacher chooses input method}
│
│   ├─> [10a. Manual entry: Teacher enters emails]
│   │   Example:
│   │   john.doe@student.school.edu
│   │   jane.smith@student.school.edu
│   │   mike.jones@student.school.edu
│   │
│   │   Real-time validation:
│   │   - Valid email format
│   │   - No duplicates
│   │   - Max 100 at a time
│   │
│   └─> [10b. CSV upload: Teacher uploads file]
│       File format:
│       email,first_name,last_name,grade
│       john.doe@student.school.edu,John,Doe,11
│       jane.smith@student.school.edu,Jane,Smith,11
│
│       Validation:
│       - CSV format correct
│       - All required fields present
│       - Valid email addresses
│       - Grades match class grade (or within 1 grade)
│
├─> [11. Teacher clicks "Send Invitations"]
│   API: POST /api/v1/teacher/classes/{class_id}/invite
│   Body:
│   {
│     "students": [
│       {
│         "email": "john.doe@student.school.edu",
│         "first_name": "John",
│         "last_name": "Doe",
│         "grade": 11
│       },
│       ...
│     ]
│   }
│
├─> (12. System processes invitations)
│   For each student:
│   1. Check if user already exists
│      {Exists?}
│      ├─ YES --> Add to class_students
│      └─ NO --> Create invitation record
│
│   2. Generate unique invite token (expires in 7 days)
│
│   3. Send invitation email
│      Subject: "You're invited to join Physics 101 on Vividly!"
│      Body:
│      """
│      Hi [First Name],
│
│      Your teacher [Teacher Name] has invited you to join their class
│      on Vividly, a personalized STEM learning platform.
│
│      Class: Physics 101 - Period 3
│      Teacher: Jane Doe
│      School: [Organization Name]
│
│      Click here to create your account:
│      https://app.vividly.edu/invite?token=[unique_token]
│
│      This invitation expires in 7 days.
│      """
│
│   4. Track event: student_invited
│
├─> [13. System displays confirmation]
│   ┌──────────────────────────────────────────────────┐
│   │ ✓ Invitations Sent!                              │
│   │                                                  │
│   │ Successfully invited 3 students:                 │
│   │ ✓ john.doe@student.school.edu                    │
│   │ ✓ jane.smith@student.school.edu                  │
│   │ ✓ mike.jones@student.school.edu                  │
│   │                                                  │
│   │ Students will receive email invitations with     │
│   │ instructions to create their accounts.           │
│   │                                                  │
│   │ [OK]                                             │
│   └──────────────────────────────────────────────────┘
│
├─> (14. System updates class detail page)
│   Refresh student list with new invitations
│   Display: Invitation status for each student
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Students (3)                     [+ Invite More] [Export CSV]│
│   │                                                              │
│   │ Name              Email                      Status          │
│   │ ───────────────────────────────────────────────────────────  │
│   │ John Doe          john.doe@...edu            ⏳ Pending      │
│   │                   Invited: 2 minutes ago     [Resend]       │
│   │                                                              │
│   │ Jane Smith        jane.smith@...edu          ⏳ Pending      │
│   │                   Invited: 2 minutes ago     [Resend]       │
│   │                                                              │
│   │ Mike Jones        mike.jones@...edu          ⏳ Pending      │
│   │                   Invited: 2 minutes ago     [Resend]       │
│   └──────────────────────────────────────────────────────────────┘
│
├─> (15. Students receive and accept invitations)
│   When student completes onboarding:
│   - Invitation status updates to "✓ Active"
│   - Student appears in teacher's class roster
│   - Teacher receives notification
│
└─> END: Class created and students invited

════════════════════════════════════════════════════════════════════
ONGOING CLASS MANAGEMENT:

M1. View all classes
├─> Teacher dashboard shows all classes
│   ┌──────────────────────────────────────────────────┐
│   │ My Classes                    [+ Create New]     │
│   │                                                  │
│   │ 📚 Physics 101 - Period 3                        │
│   │    Grade 11 | 25 students | 127 views           │
│   │    [View Details]                                │
│   │                                                  │
│   │ 📚 Physics 101 - Period 5                        │
│   │    Grade 11 | 22 students | 98 views            │
│   │    [View Details]                                │
│   └──────────────────────────────────────────────────┘

M2. Edit class details
├─> [Click "Edit" on class detail page]
├─> [Modify name, subject, grade, year]
├─> API: PATCH /api/v1/teacher/classes/{class_id}
└─> Display: ✓ "Class updated"

M3. Archive class
├─> [Click "Archive" on class detail page]
├─> [Confirm: "Are you sure?"]
├─> API: PATCH /api/v1/teacher/classes/{class_id}
│   Body: {"status": "archived"}
├─> Students retain access to history
└─> Class removed from active list

M4. Remove student from class
├─> [Click "Remove" next to student name]
├─> [Confirm: "Remove [Student] from class?"]
├─> API: DELETE /api/v1/teacher/classes/{class_id}/students/{student_id}
├─> Student loses access to class content
└─> Student's historical data preserved

M5. Resend invitation
├─> [Click "Resend" next to pending student]
├─> API: POST /api/v1/teacher/classes/{class_id}/invite/resend
│   Body: {"student_id": "..."}
├─> Generate new token, send new email
└─> Display: ✓ "Invitation resent"

M6. Export student roster
├─> [Click "Export CSV"]
├─> API: GET /api/v1/teacher/classes/{class_id}/students/export
├─> Download CSV:
│   name,email,status,join_date,total_views,last_active
│   John Doe,john@...,active,2024-01-15,45,2024-01-20
└─> File: physics-101-roster-2024-01-20.csv

TIME ESTIMATES:
- Create class: 30 seconds
- Invite students (manual): 2-3 minutes
- Invite students (CSV): 1 minute
- Total setup: 3-4 minutes
```

---

### Student Monitoring Flow

**Features**: F8 (Student Progress Monitoring)

**Entry Point**: Teacher clicks on a class to view student progress

```
┌─────────────────────────────────────────────────────────────────┐
│                   STUDENT MONITORING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

START: Teacher on class detail page
│
├─> [1. Teacher views class dashboard]
│   URL: /teacher/classes/{class_id}
│   API: GET /api/v1/teacher/classes/{class_id}/dashboard
│
├─> [2. System displays class-level statistics]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Physics 101 - Period 3                                       │
│   │ Grade 11 | 25 Students                                       │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Class Statistics - This Week                                 │
│   │                                                              │
│   │ 📊 Active Students      📈 Total Views      ⏱ Avg Watch Time│
│   │    18 / 25 (72%)           127 videos          35 min/student│
│   │                                                              │
│   │ 🎯 Completion Rate      📚 Topics Explored  🔥 Most Popular  │
│   │    85%                     12 topics          Newton's Laws │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Engagement Timeline (Last 7 Days)                            │
│   │                                                              │
│   │ Views                                                        │
│   │  30 │                               ●                        │
│   │  25 │                         ●                              │
│   │  20 │         ●         ●                                    │
│   │  15 │   ●                                                    │
│   │  10 │                                         ●              │
│   │   5 │                                               ●        │
│   │   0 └─────────────────────────────────────────────────       │
│   │     Mon   Tue   Wed   Thu   Fri   Sat   Sun                 │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Student Roster               Sort by: [Engagement ▼]        │
│   │                              Filter: [All Students ▼]       │
│   │                                                              │
│   │ [View detailed progress for each student below]              │
│   └──────────────────────────────────────────────────────────────┘
│
├─> [3. Teacher scrolls to student roster]
│   Display: Table with all students and key metrics
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Student Name  Status    Views  Watch Time  Last Active  [...]│
│   │ ───────────────────────────────────────────────────────────  │
│   │ John Doe      ● Active   12     42 min      2 hours ago     │
│   │ Jane Smith    ● Active   8      28 min      5 hours ago     │
│   │ Mike Jones    ● Active   15     51 min      1 hour ago      │
│   │ Sarah Lee     ⚠ At Risk  2      7 min       3 days ago      │
│   │ Tom Wilson    ● Active   10     35 min      1 day ago       │
│   │ ...                                                          │
│   └──────────────────────────────────────────────────────────────┘
│
│   Status indicators:
│   - ● Active: Accessed within last 7 days
│   - ⚠ At Risk: No activity in 7-14 days
│   - 🔴 Inactive: No activity in 14+ days
│   - ⏳ Pending: Invitation not accepted
│
├─> {Teacher chooses monitoring action}
│
│   ├─> [4a. Sort students]
│   │   Sort options:
│   │   - Engagement (default): Activity level DESC
│   │   - Name: Alphabetical
│   │   - Views: Total views DESC
│   │   - Watch Time: Total time DESC
│   │   - Last Active: Most recent first
│   │
│   │   Re-render table with new sort order
│   │
│   ├─> [4b. Filter students]
│   │   Filter options:
│   │   - All Students (default)
│   │   - Active (last 7 days)
│   │   - At Risk (7-14 days inactive)
│   │   - Inactive (14+ days)
│   │   - Pending Invitations
│   │
│   │   API: GET /api/v1/teacher/classes/{class_id}/students?status=at_risk
│   │   Re-render table with filtered results
│   │
│   ├─> [4c. View individual student details]
│   │   [Click on student name]
│   │   Navigate to student detail page
│   │   URL: /teacher/students/{student_id}
│   │   Continue to Student Detail View (below)
│   │
│   └─> [4d. Export class report]
│       [Click "Export Report"]
│       API: GET /api/v1/teacher/classes/{class_id}/report
│       Download PDF with:
│       - Class statistics
│       - Student roster with metrics
│       - Engagement chart
│       - Topic coverage breakdown
│
├─> [5. STUDENT DETAIL VIEW: Teacher clicks student name]
│   URL: /teacher/students/{student_id}
│   API: GET /api/v1/teacher/students/{student_id}/progress
│
├─> [6. System displays student progress page]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ ← Back to Class                                              │
│   │                                                              │
│   │ John Doe                                    [Send Message]   │
│   │ Grade 11 | john.doe@student.school.edu                       │
│   │ Member of: Physics 101 - Period 3                            │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Learning Summary - This Week                                 │
│   │                                                              │
│   │ 📊 Videos Watched    ⏱ Watch Time    🎯 Completion    📈 Trend│
│   │    12 videos            42 min           90%          ↑ Up  │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Interests:                                                   │
│   │ 🏀 Basketball | 🎮 Video Games | 🎵 Music Production         │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Recent Activity (Last 7 Days)                                │
│   │                                                              │
│   │ Date       Topic                        Views  Status        │
│   │ ─────────────────────────────────────────────────────────    │
│   │ Today      Newton's Third Law             2    ✓ Completed  │
│   │            Watch Time: 5m 30s                                │
│   │                                                              │
│   │ Today      Force Diagrams                 1    ⏸ 45% done   │
│   │            Watch Time: 2m 15s                                │
│   │                                                              │
│   │ Yesterday  Newton's Second Law            1    ✓ Completed  │
│   │            Watch Time: 4m 45s                                │
│   │                                                              │
│   │ 2 days ago Kinematics                     3    ✓ Completed  │
│   │            Watch Time: 12m 20s                               │
│   │                                                              │
│   │ [Load More Activity]                                         │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Topic Coverage                                               │
│   │                                                              │
│   │ Physics                                                      │
│   │ ├─ Mechanics (8 topics explored)                             │
│   │ │  ├─ ✓ Kinematics                      [Strong]            │
│   │ │  ├─ ✓ Forces                          [Proficient]        │
│   │ │  └─ ⏳ Energy and Work                [In Progress]        │
│   │ ├─ Electricity (0 topics)                [Not Started]      │
│   │ └─ Waves (0 topics)                      [Not Started]      │
│   │                                                              │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Recommendations for John:                                    │
│   │ ✨ Ready to explore: Energy and Work                         │
│   │ ✨ Suggested next: Conservation of Energy                    │
│   │ ⚠  Hasn't accessed in 2 days - consider follow-up           │
│   │                                                              │
│   └──────────────────────────────────────────────────────────────┘
│
├─> {Teacher interactions on student page}
│
│   ├─> [7a. View specific video]
│   │   [Click on video title in activity log]
│   │   API: GET /api/v1/teacher/content/{content_id}
│   │   Display: Video metadata, transcript, watch analytics
│   │   ┌────────────────────────────────────────────────────┐
│   │   │ Newton's Third Law - Basketball Edition            │
│   │   │                                                    │
│   │   │ Created: Today at 10:15 AM                         │
│   │   │ Duration: 2m 45s                                   │
│   │   │                                                    │
│   │   │ Student's watch pattern:                           │
│   │   │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%               │
│   │   │ Watched twice (5m 30s total)                       │
│   │   │                                                    │
│   │   │ [View Transcript] [Preview Video]                  │
│   │   └────────────────────────────────────────────────────┘
│   │
│   ├─> [7b. Filter by topic]
│   │   Dropdown: Show all / Physics / Chemistry / etc.
│   │   Filter activity log by subject area
│   │
│   ├─> [7c. Filter by date range]
│   │   Presets: Last 7 days / Last 30 days / This semester
│   │   Custom range picker
│   │
│   ├─> [7d. Export student report]
│   │   [Click "Export Report"]
│   │   API: GET /api/v1/teacher/students/{student_id}/report
│   │   Download PDF with full progress details
│   │
│   └─> [7e. Send message (future feature)]
│       Placeholder for messaging/notification system
│
└─> END: Teacher reviewed student progress

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. At-risk student alert
├─> Teacher dashboard shows notification banner
│   ┌────────────────────────────────────────────────────┐
│   │ ⚠ 3 students haven't accessed content in 7+ days   │
│   │ [View At-Risk Students]                            │
│   └────────────────────────────────────────────────────┘
├─> Click to view filtered list
└─> Consider follow-up with students

A2. Class-wide trends
├─> Teacher notices low engagement on specific topic
├─> View topic-level analytics
│   API: GET /api/v1/teacher/classes/{class_id}/topics/{topic_id}/analytics
├─> See which students struggling
└─> Plan targeted intervention

A3. Empty student activity
├─> Student has accepted invitation but no activity
├─> Display: "John hasn't watched any videos yet"
├─> Suggestion: "Recommend starting with [Topic]"

TIME ESTIMATES:
- Review class dashboard: 1-2 minutes
- Review individual student: 2-3 minutes
- Identify at-risk students: 30 seconds
```

---

### Content Recommendation Flow

**Features**: F9 (Content Recommendations)

**Entry Point**: Teacher wants to recommend specific content to student(s)

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONTENT RECOMMENDATION FLOW                      │
└─────────────────────────────────────────────────────────────────┘

START: Teacher viewing student progress or class dashboard
│
├─> [1. Teacher clicks "Recommend Content"]
│   Entry points:
│   - From student detail page: "Recommend to John"
│   - From class page: "Recommend to Class"
│   - From topic page: "Recommend This Topic"
│
├─> [2. System displays recommendation modal]
│   ┌──────────────────────────────────────────────────┐
│   │ Recommend Learning Content                       │
│   │                                                  │
│   │ Recommend to:                                    │
│   │ ● Specific Students                              │
│   │ ○ Entire Class                                   │
│   │ ○ At-Risk Students                               │
│   │                                                  │
│   │ {If "Specific Students" selected:}               │
│   │ Select students:                                 │
│   │ [x] John Doe                                     │
│   │ [ ] Jane Smith                                   │
│   │ [x] Mike Jones                                   │
│   │ ... (show all class students)                    │
│   │                                                  │
│   │ Select topic to recommend:                       │
│   │ [🔍 Search topics ___________________]          │
│   │                                                  │
│   │ Recent topics in this class:                     │
│   │ ○ Newton's Third Law                             │
│   │ ○ Force Diagrams                                 │
│   │ ○ Conservation of Energy                         │
│   │                                                  │
│   │ Optional message:                                │
│   │ [_______________________________________]        │
│   │ Example: "This will help with Friday's quiz!"   │
│   │                                                  │
│   │ [Cancel]              [Send Recommendation]      │
│   └──────────────────────────────────────────────────┘
│
├─> [3. Teacher selects recipients]
│   Options:
│   - Specific Students: Multi-select checkbox list
│   - Entire Class: All active students
│   - At-Risk Students: Auto-filter inactive students
│
├─> [4. Teacher selects topic]
│   Methods:
│   - Search: Type topic name, get filtered results
│   - Browse: Click through topic hierarchy
│   - Recent: Select from recently viewed topics
│
├─> [5. Teacher adds optional message]
│   Character limit: 500
│   Examples:
│   - "Great video to review before our test!"
│   - "This connects to what we discussed in class today"
│   - "Check this out for extra credit opportunity"
│
├─> [6. Teacher clicks "Send Recommendation"]
│   API: POST /api/v1/teacher/recommendations
│   Body:
│   {
│     "class_id": "class_abc123",
│     "student_ids": ["student_1", "student_2"],
│     "topic_id": "topic_phys_mech_newton_3",
│     "message": "Great video to review before our test!",
│     "recommended_by": "teacher_xyz"
│   }
│
│   Validation:
│   - At least 1 recipient selected
│   - Valid topic_id
│   - Message < 500 chars
│   - Teacher has access to class
│
│   {Valid?}
│   ├─ NO --> [!] Display validation errors --> Return to step 3
│   └─ YES --> Continue
│
├─> (7. System creates recommendations)
│   For each student:
│   1. Create recommendation record
│      - recommendation_id
│      - student_id
│      - topic_id
│      - recommended_by (teacher_id)
│      - message
│      - status = "pending"
│      - created_at = NOW()
│
│   2. Send in-app notification
│      Notification appears in student dashboard
│
│   3. Track event: content_recommended
│
├─> [8. System displays confirmation]
│   ┌──────────────────────────────────────────────────┐
│   │ ✓ Recommendation Sent!                           │
│   │                                                  │
│   │ Newton's Third Law has been recommended to:      │
│   │ • John Doe                                       │
│   │ • Mike Jones                                     │
│   │                                                  │
│   │ Students will see this in their dashboard.       │
│   │                                                  │
│   │ [OK]                                             │
│   └──────────────────────────────────────────────────┘
│
├─> (9. STUDENT VIEW: Student sees recommendation)
│   Student dashboard shows notification banner:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ 📬 New Recommendation from Ms. Doe                           │
│   │                                                              │
│   │ Topic: Newton's Third Law                                    │
│   │ Message: "Great video to review before our test!"            │
│   │                                                              │
│   │ [View Topic] [Dismiss]                                       │
│   └──────────────────────────────────────────────────────────────┘
│
├─> [10. Student clicks "View Topic"]
│   Navigate to topic detail page
│   URL: /topics/topic_phys_mech_newton_3
│   Auto-scroll to "Get Personalized Video" button
│   Highlight: "Recommended by your teacher"
│
├─> (11. System tracks engagement)
│   When student interacts:
│   - Clicks "View Topic": Update status = "viewed"
│   - Requests video: Update status = "engaged"
│   - Dismisses: Update status = "dismissed"
│   - No action after 7 days: Update status = "expired"
│
├─> (12. TEACHER VIEW: Teacher monitors recommendations)
│   Teacher dashboard shows recommendation panel:
│   ┌──────────────────────────────────────────────────┐
│   │ Recent Recommendations                           │
│   │                                                  │
│   │ Newton's Third Law (sent today)                  │
│   │ • John Doe: ✓ Viewed, requested video           │
│   │ • Mike Jones: ⏳ Not viewed yet                   │
│   │                                                  │
│   │ Force Diagrams (sent 2 days ago)                 │
│   │ • Jane Smith: ✓ Viewed, completed video         │
│   │ • Tom Wilson: ✗ Dismissed                        │
│   └──────────────────────────────────────────────────┘
│
└─> END: Recommendation delivered and tracked

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. Bulk recommendation to struggling students
├─> Teacher reviews class analytics
├─> Identifies topic with low engagement: "Force Diagrams"
├─> Filters students: "Show students who haven't viewed this topic"
├─> Sends targeted recommendation to 8 students
└─> Tracks: Do these students engage after recommendation?

A2. Recommendation expires
├─> Student doesn't interact within 7 days
├─> Status: "expired"
├─> Remove from student's active notifications
├─> Track metric: recommendation_expiration_rate

A3. Student already viewed topic
├─> System detects student already completed topic
├─> Display message: "You've already explored this topic!"
├─> Suggest: "Watch again or explore related topics"

A4. Teacher views recommendation analytics
├─> Navigate to class analytics page
├─> View recommendation metrics:
│   - Total recommendations sent
│   - View rate (% students who clicked)
│   - Engagement rate (% who requested video)
│   - Completion rate (% who finished video)
│   - Most effective topics
└─> Use data to improve future recommendations

TIME ESTIMATES:
- Create recommendation: 30-60 seconds
- Student views notification: Immediate
- Student engages with content: Varies (1-5 minutes)
```

---

## Admin Flows

### Organization Setup Flow

**Features**: F10 (Admin User Management)

**Entry Point**: New organization signs up for Vividly

```
┌─────────────────────────────────────────────────────────────────┐
│                   ORGANIZATION SETUP FLOW                        │
└─────────────────────────────────────────────────────────────────┘

START: Sales team onboards new school/district
│
├─> (1. Vividly sales creates organization)
│   Manual process via internal admin panel
│   API: POST /api/v1/internal/organizations
│   Body:
│   {
│     "name": "Lincoln High School",
│     "type": "school",  // or "district"
│     "address": {...},
│     "subscription_tier": "standard",
│     "max_students": 500,
│     "max_teachers": 50,
│     "contract_start": "2024-01-01",
│     "contract_end": "2025-06-30"
│   }
│
├─> (2. System creates organization)
│   - Generate org_id
│   - Set status = "active"
│   - Create organization record
│   - Initialize quotas and limits
│   - Track event: organization_created
│
├─> (3. Vividly sales creates first admin user)
│   API: POST /api/v1/internal/users
│   Body:
│   {
│     "email": "admin@lincoln.edu",
│     "role": "admin",
│     "first_name": "Sarah",
│     "last_name": "Johnson",
│     "org_id": "org_lincoln",
│     "is_primary_admin": true
│   }
│
├─> (4. System generates admin credentials)
│   - Create user record with role = "admin"
│   - Generate temporary password
│   - Set must_change_password = true
│   - Generate password reset token
│
├─> (5. System sends welcome email to admin)
│   To: admin@lincoln.edu
│   Subject: "Welcome to Vividly - Set Up Your Organization"
│   Body:
│   """
│   Welcome to Vividly!
│
│   Your organization (Lincoln High School) has been set up on Vividly.
│
│   You have been designated as the primary administrator. Your role is to:
│   - Create teacher accounts
│   - Manage users
│   - Monitor platform usage
│   - View analytics
│
│   Click here to set your password and log in:
│   https://app.vividly.edu/admin/setup?token=[unique_token]
│
│   This link expires in 48 hours.
│
│   Need help? Contact support@vividly.edu
│   """
│
├─> [6. Admin receives email and clicks link]
│   URL: /admin/setup?token=abc123
│
├─> (7. System validates setup token)
│   API: GET /api/v1/auth/validate-token/{token}
│   {Valid token?}
│   ├─ NO --> [!] "Invalid or expired link" --> Contact support
│   └─ YES --> Continue
│
├─> [8. Admin views password setup page]
│   Similar to teacher onboarding, but admin-branded
│   Display:
│   ┌──────────────────────────────────────────────────┐
│   │ Welcome to Vividly, Sarah!                       │
│   │                                                  │
│   │ Lincoln High School - Administrator              │
│   │                                                  │
│   │ Please set your password to get started.         │
│   │                                                  │
│   │ Temporary Password:                              │
│   │ [_________________________________]              │
│   │                                                  │
│   │ New Password:                                    │
│   │ [_________________________________]              │
│   │ Must be 12+ characters with uppercase, lowercase│
│   │ number, and special character                    │
│   │                                                  │
│   │ Confirm New Password:                            │
│   │ [_________________________________]              │
│   │                                                  │
│   │ [Set Password and Continue]                      │
│   └──────────────────────────────────────────────────┘
│
│   Note: Admin password requirements stricter (12 vs 8 chars)
│
├─> [9. Admin sets password and submits]
│   API: POST /api/v1/auth/reset-password
│   Validation: Same as teacher flow but 12+ char minimum
│
├─> (10. System redirects to Admin Portal)
│   Auto-login with JWT
│   URL: /admin/dashboard
│
├─> [11. System displays Admin Dashboard with setup wizard]
│   ┌──────────────────────────────────────────────────────────────┐
│   │ 👋 Welcome to Vividly, Sarah!                                │
│   │                                                              │
│   │ Let's set up Lincoln High School:                            │
│   │                                                              │
│   │ ✓ Organization created                                       │
│   │ ✓ Admin account set up                                       │
│   │ ⏳ Add teachers (Step 1 of 2)                                │
│   │ ⏳ Teachers invite students (Step 2 of 2)                    │
│   │                                                              │
│   │ [Start Setup] [Skip to Dashboard]                            │
│   └──────────────────────────────────────────────────────────────┘
│
├─> {Admin chooses action}
│   ├─> Option A: Start Setup --> Continue to User Management Flow
│   └─> Option B: Skip --> Show dashboard (can return later)
│
└─> END: Organization set up, admin ready to add teachers

════════════════════════════════════════════════════════════════════
ALTERNATE PATHS:

A1. District-level organization
├─> District admin sets up multiple schools
├─> Create school sub-organizations
├─> Assign school-level admins
└─> School admins manage their teachers/students

A2. SSO integration (future)
├─> Organization uses Google Workspace or Microsoft 365
├─> Configure SSO during setup
├─> Users log in with institutional credentials
└─> Auto-provision accounts via SAML/OAuth

TIME ESTIMATES:
- Vividly sales setup: 10-15 minutes
- Admin password setup: 2-3 minutes
- Initial teacher creation: 5-10 minutes
- Total organization setup: 20-30 minutes
```

---

### User Management Flow

**Features**: F10 (Admin User Management)

**Entry Point**: Admin wants to create/manage users

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER MANAGEMENT FLOW                        │
└─────────────────────────────────────────────────────────────────┘

START: Admin on dashboard
│
├─> [1. Admin clicks "Manage Users"]
│   Navigate to: /admin/users
│
├─> [2. System displays user management page]
│   API: GET /api/v1/admin/users?org_id={org_id}&limit=50
│
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ User Management - Lincoln High School                        │
│   │                                                              │
│   │ Tabs: [Teachers] [Students] [Admins]            [+ Add User] │
│   │                                                              │
│   │ Search: [________________] 🔍  Filter: [All ▼] Sort: [Name ▼]│
│   │                                                              │
│   │ Teachers (12 / 50 max)                                       │
│   │ ───────────────────────────────────────────────────────────  │
│   │                                                              │
│   │ Name           Email                Status      Actions      │
│   │ ──────────────────────────────────────────────────────────   │
│   │ Jane Doe       jane@lincoln.edu     ● Active    [Edit] [⋮]  │
│   │ John Smith     john@lincoln.edu     ● Active    [Edit] [⋮]  │
│   │ Mike Johnson   mike@lincoln.edu     ⏸ Inactive  [Edit] [⋮]  │
│   │ ...                                                          │
│   │                                                              │
│   │ [Load More]                                                  │
│   └──────────────────────────────────────────────────────────────┘
│
├─> {Admin chooses user management action}
│
│   ├─> [ACTION A: Create New Teacher]
│   │
│   │   ├─> [A1. Click "+ Add User"]
│   │   ├─> [A2. System displays user creation modal]
│   │   │   ┌──────────────────────────────────────────────────┐
│   │   │   │ Create New User                                  │
│   │   │   │                                                  │
│   │   │   │ User Type:                                       │
│   │   │   │ ● Teacher  ○ Admin                               │
│   │   │   │                                                  │
│   │   │   │ First Name:                                      │
│   │   │   │ [_________________________________]              │
│   │   │   │                                                  │
│   │   │   │ Last Name:                                       │
│   │   │   │ [_________________________________]              │
│   │   │   │                                                  │
│   │   │   │ Email:                                           │
│   │   │   │ [_________________________________]              │
│   │   │   │ Must end with @lincoln.edu                       │
│   │   │   │                                                  │
│   │   │   │ [Cancel]                [Create User]            │
│   │   │   └──────────────────────────────────────────────────┘
│   │   │
│   │   ├─> [A3. Admin fills form and submits]
│   │   │   API: POST /api/v1/admin/users
│   │   │   Body:
│   │   │   {
│   │   │     "email": "sarah.williams@lincoln.edu",
│   │   │     "role": "teacher",
│   │   │     "first_name": "Sarah",
│   │   │     "last_name": "Williams",
│   │   │     "org_id": "org_lincoln"
│   │   │   }
│   │   │
│   │   │   Validation:
│   │   │   - Email format valid
│   │   │   - Email domain matches org (optional enforcement)
│   │   │   - Email not already in use
│   │   │   - Within teacher quota (12/50)
│   │   │   - Names 1-50 chars
│   │   │
│   │   │   {Valid?}
│   │   │   ├─ NO --> [!] Display errors --> Return to A2
│   │   │   └─ YES --> Continue
│   │   │
│   │   ├─> (A4. System creates teacher account)
│   │   │   Same process as teacher onboarding:
│   │   │   - Create user record
│   │   │   - Generate temporary password
│   │   │   - Send welcome email with setup link
│   │   │   - Track event: user_created
│   │   │
│   │   ├─> [A5. System displays confirmation]
│   │   │   ┌────────────────────────────────────────────────────┐
│   │   │   │ ✓ Teacher Account Created                          │
│   │   │   │                                                    │
│   │   │   │ Email: sarah.williams@lincoln.edu                  │
│   │   │   │ Temporary Password: [Show] [Copy]                  │
│   │   │   │                                                    │
│   │   │   │ A welcome email has been sent to Sarah with        │
│   │   │   │ instructions to set up their account.              │
│   │   │   │                                                    │
│   │   │   │ [OK]                                               │
│   │   │   └────────────────────────────────────────────────────┘
│   │   │
│   │   └─> (A6. Refresh user list with new teacher)
│   │
│   ├─> [ACTION B: Edit Existing User]
│   │
│   │   ├─> [B1. Click "Edit" next to user]
│   │   ├─> [B2. System displays edit modal]
│   │   │   ┌──────────────────────────────────────────────────┐
│   │   │   │ Edit User: Jane Doe                              │
│   │   │   │                                                  │
│   │   │   │ First Name:                                      │
│   │   │   │ [Jane_____________________________]              │
│   │   │   │                                                  │
│   │   │   │ Last Name:                                       │
│   │   │   │ [Doe______________________________]              │
│   │   │   │                                                  │
│   │   │   │ Email:                                           │
│   │   │   │ [jane@lincoln.edu_________________]              │
│   │   │   │                                                  │
│   │   │   │ Status:                                          │
│   │   │   │ ● Active  ○ Inactive                             │
│   │   │   │                                                  │
│   │   │   │ [Cancel]                [Save Changes]           │
│   │   │   └──────────────────────────────────────────────────┘
│   │   │
│   │   ├─> [B3. Admin makes changes and saves]
│   │   │   API: PATCH /api/v1/admin/users/{user_id}
│   │   │   Body: Changed fields only
│   │   │
│   │   └─> Display: ✓ "User updated successfully"
│   │
│   ├─> [ACTION C: Reset User Password]
│   │
│   │   ├─> [C1. Click "⋮" menu next to user]
│   │   ├─> [C2. Select "Reset Password"]
│   │   ├─> [C3. System displays confirmation]
│   │   │   "Reset password for Jane Doe?"
│   │   │   [Cancel] [Yes, Reset Password]
│   │   │
│   │   ├─> (C4. System generates new temp password)
│   │   │   API: POST /api/v1/admin/users/{user_id}/reset-password
│   │   │   - Generate new temporary password
│   │   │   - Set must_change_password = true
│   │   │   - Send email with reset link
│   │   │   - Track event: password_reset_by_admin
│   │   │
│   │   └─> Display: ✓ "Password reset email sent to jane@lincoln.edu"
│   │
│   ├─> [ACTION D: Deactivate User]
│   │
│   │   ├─> [D1. Click "⋮" menu next to user]
│   │   ├─> [D2. Select "Deactivate"]
│   │   ├─> [D3. System displays confirmation]
│   │   │   ┌────────────────────────────────────────────────────┐
│   │   │   │ Deactivate Jane Doe?                               │
│   │   │   │                                                    │
│   │   │   │ This will:                                         │
│   │   │   │ • Revoke access to Vividly                         │
│   │   │   │ • Preserve all historical data                     │
│   │   │   │ • Can be reactivated later                         │
│   │   │   │                                                    │
│   │   │   │ If this is a teacher, their classes will remain    │
│   │   │   │ active but students won't be able to contact them. │
│   │   │   │                                                    │
│   │   │   │ [Cancel]              [Deactivate User]            │
│   │   │   └────────────────────────────────────────────────────┘
│   │   │
│   │   ├─> [D4. Admin confirms]
│   │   │   API: PATCH /api/v1/admin/users/{user_id}
│   │   │   Body: {"status": "inactive"}
│   │   │   - Revoke JWT tokens
│   │   │   - Update user status
│   │   │   - Track event: user_deactivated
│   │   │
│   │   └─> Display: ✓ "Jane Doe has been deactivated"
│   │
│   ├─> [ACTION E: Reactivate User]
│   │
│   │   ├─> [E1. Filter: "Show Inactive Users"]
│   │   ├─> [E2. Click "⋮" menu next to inactive user]
│   │   ├─> [E3. Select "Reactivate"]
│   │   ├─> [E4. System confirms and sends reactivation email]
│   │   │   API: PATCH /api/v1/admin/users/{user_id}
│   │   │   Body: {"status": "active"}
│   │   │
│   │   └─> Display: ✓ "User reactivated"
│   │
│   ├─> [ACTION F: Bulk Import Users (CSV)]
│   │
│   │   ├─> [F1. Click "Import Users" button]
│   │   ├─> [F2. System displays import modal]
│   │   │   ┌────────────────────────────────────────────────────┐
│   │   │   │ Bulk Import Users                                  │
│   │   │   │                                                    │
│   │   │   │ Upload CSV file:                                   │
│   │   │   │ [Choose File] No file selected                     │
│   │   │   │                                                    │
│   │   │   │ CSV Format:                                        │
│   │   │   │ email,first_name,last_name,role                    │
│   │   │   │ jane@lincoln.edu,Jane,Doe,teacher                  │
│   │   │   │ john@lincoln.edu,John,Smith,teacher                │
│   │   │   │                                                    │
│   │   │   │ [Download Template]                                │
│   │   │   │                                                    │
│   │   │   │ [Cancel]                [Upload and Import]        │
│   │   │   └────────────────────────────────────────────────────┘
│   │   │
│   │   ├─> [F3. Admin uploads CSV]
│   │   │   API: POST /api/v1/admin/users/bulk-import
│   │   │   Content-Type: multipart/form-data
│   │   │
│   │   │   Server-side processing:
│   │   │   - Parse CSV
│   │   │   - Validate all rows
│   │   │   - Check quotas
│   │   │   - Create users in batch
│   │   │   - Send welcome emails (queued)
│   │   │
│   │   └─> [F4. Display import results]
│   │       ┌────────────────────────────────────────────────────┐
│   │       │ Import Complete                                    │
│   │       │                                                    │
│   │       │ ✓ Successfully imported: 8 users                   │
│   │       │ ⚠ Skipped (already exists): 2 users                │
│   │       │ ✗ Failed: 1 user                                   │
│   │       │                                                    │
│   │       │ Failed: Row 5                                      │
│   │       │ Email: invalid@email (Invalid email format)        │
│   │       │                                                    │
│   │       │ [Download Full Report] [OK]                        │
│   │       └────────────────────────────────────────────────────┘
│   │
│   ├─> [ACTION G: View User Details]
│   │
│   │   ├─> [G1. Click on user name]
│   │   ├─> [G2. Navigate to user detail page]
│   │   │   URL: /admin/users/{user_id}
│   │   │
│   │   │   Display:
│   │   │   - Full user profile
│   │   │   - Account activity log
│   │   │   - Classes (if teacher)
│   │   │   - Learning history (if student)
│   │   │   - Login history
│   │   │
│   │   └─> Admin can perform actions: Edit, Reset Password, etc.
│   │
│   ├─> [ACTION H: Search and Filter Users]
│   │
│   │   ├─> [H1. Use search bar]
│   │   │   API: GET /api/v1/admin/users?q=jane&role=teacher
│   │   │   Real-time search as user types
│   │   │   Search fields: name, email
│   │   │
│   │   ├─> [H2. Apply filters]
│   │   │   Filters:
│   │   │   - Status: All / Active / Inactive
│   │   │   - Role: All / Teachers / Students / Admins
│   │   │   - Created: Last 7 days / 30 days / All time
│   │   │
│   │   └─> Results update in real-time
│   │
│   └─> [ACTION I: Export User List]
│
│       ├─> [I1. Click "Export" button]
│       ├─> [I2. Select export format: CSV / Excel / PDF]
│       ├─> API: GET /api/v1/admin/users/export?format=csv
│       └─> Download file: lincoln-users-2024-01-20.csv
│
└─> END: User management complete

════════════════════════════════════════════════════════════════════
STUDENT TAB DIFFERENCES:

When viewing "Students" tab:
- Cannot directly create students (must be invited by teachers)
- Can view all students across all classes
- Can reassign students to different teachers (transfer classes)
- Can reset student passwords
- Can deactivate/delete student accounts (with data retention)
- Can view detailed learning history

TIME ESTIMATES:
- Create single teacher: 1 minute
- Bulk import 20 teachers: 3-5 minutes
- Search/find user: 10-30 seconds
- Edit user: 30 seconds
- Reset password: 20 seconds
```

---

### System Monitoring Flow

**Features**: F11 (Admin Analytics Dashboard)

**Entry Point**: Admin wants to view platform usage and analytics

```
┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM MONITORING FLOW                         │
└─────────────────────────────────────────────────────────────────┘

START: Admin on dashboard
│
├─> [1. Admin clicks "Analytics" in navigation]
│   Navigate to: /admin/analytics
│
├─> [2. System loads analytics dashboard]
│   API: GET /api/v1/admin/analytics/overview
│   Query params:
│   - org_id: Current organization
│   - date_range: Last 30 days (default)
│   - include: users, content, engagement, system
│
├─> [3. System displays analytics dashboard]
│   Layout:
│   ┌──────────────────────────────────────────────────────────────┐
│   │ Analytics Dashboard - Lincoln High School                    │
│   │                                                              │
│   │ Date Range: [Last 30 Days ▼]  Export: [PDF] [CSV] [Excel]  │
│   │                                                              │
│   │ ═══════════════════════════════════════════════════════════  │
│   │                                                              │
│   │ KEY METRICS                                                  │
│   │                                                              │
│   │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│   │ │ 👥 Users    │ │ 🎬 Videos   │ │ ⏱ Watch Time│ │ 📊 Engmt││
│   │ │   12 / 50   │ │     847     │ │   425 hrs   │ │   78%   ││
│   │ │  Teachers   │ │  Generated  │ │   Total     │ │  Active ││
│   │ │             │ │             │ │             │ │         ││
│   │ │  215 / 500  │ │  ↑ 12% WoW  │ │  ↑ 8% WoW   │ │ ↓ 2% WoW││
│   │ │  Students   │ │             │ │             │ │         ││
│   │ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘│
│   │                                                              │
│   │ ═══════════════════════════════════════════════════════════  │
│   │                                                              │
│   │ ENGAGEMENT TRENDS (Last 30 Days)                             │
│   │                                                              │
│   │ Daily Active Users                                           │
│   │ 200 │                                       ●                │
│   │ 175 │                         ●       ●                      │
│   │ 150 │       ●           ●                                    │
│   │ 125 │ ●           ●                                   ●      │
│   │ 100 │                                               ●        │
│   │  75 │                                                        │
│   │   0 └─────────────────────────────────────────────────────   │
│   │     Jan 1      Jan 8     Jan 15    Jan 22    Jan 29         │
│   │                                                              │
│   │ Content Requests Per Day                                     │
│   │  50 │                                       ●                │
│   │  40 │                         ●                              │
│   │  30 │       ●           ●           ●                        │
│   │  20 │ ●                                           ●          │
│   │  10 │                                                   ●    │
│   │   0 └─────────────────────────────────────────────────────   │
│   │     Jan 1      Jan 8     Jan 15    Jan 22    Jan 29         │
│   │                                                              │
│   │ ═══════════════════════════════════════════════════════════  │
│   │                                                              │
│   │ CONTENT ANALYTICS                                            │
│   │                                                              │
│   │ Top 10 Most Viewed Topics:                                   │
│   │  1. Newton's Third Law                   78 views   ████████││
│   │  2. Photosynthesis                       65 views   ███████ ││
│   │  3. Binary Search                        58 views   ██████  ││
│   │  4. Chemical Bonding                     54 views   ██████  ││
│   │  5. Cell Division                        47 views   █████   ││
│   │  6. Newton's Second Law                  45 views   █████   ││
│   │  7. Sorting Algorithms                   42 views   █████   ││
│   │  8. Force Diagrams                       38 views   ████    ││
│   │  9. DNA Structure                        35 views   ████    ││
│   │ 10. Variables in Python                  32 views   ███     ││
│   │                                                              │
│   │ Subject Distribution:                                        │
│   │ ┌─────────────────────────────────────────────────────────┐ │
│   │ │ Physics          ██████████████ 35% (297 views)         │ │
│   │ │ Biology          ██████████ 25% (212 views)             │ │
│   │ │ Comp Sci         ████████ 22% (186 views)               │ │
│   │ │ Chemistry        ██████ 18% (152 views)                 │ │
│   │ └─────────────────────────────────────────────────────────┘ │
│   │                                                              │
│   │ Cache Hit Rate: 14.2% (Target: 15%)                          │
│   │ Avg Video Duration: 2m 48s                                   │
│   │ Avg Generation Time: 8.2s (Target: <10s)                     │
│   │                                                              │
│   │ ═══════════════════════════════════════════════════════════  │
│   │                                                              │
│   │ STUDENT ENGAGEMENT                                           │
│   │                                                              │
│   │ Engagement Distribution:                                     │
│   │ ● High Engagement (10+ views/week):      45 students (21%)  │
│   │ ● Medium Engagement (3-9 views/week):    102 students (47%) │
│   │ ● Low Engagement (1-2 views/week):       48 students (22%)  │
│   │ ⚠ At Risk (<1 view/week):                20 students (9%)   │
│   │                                                              │
│   │ Top 5 Most Active Students:                                  │
│   │  1. John Doe               47 views | 2h 15m watch time     │
│   │  2. Jane Smith             42 views | 2h 03m watch time     │
│   │  3. Mike Jones             38 views | 1h 52m watch time     │
│   │  4. Sarah Lee              35 views | 1h 45m watch time     │
│   │  5. Tom Wilson             32 views | 1h 38m watch time     │
│   │                                                              │
│   │ [View Full Student Report]                                   │
│   │                                                              │
│   │ ═══════════════════════════════════════════════════════════  │
│   │                                                              │
│   │ SYSTEM HEALTH                                                │
│   │                                                              │
│   │ ✓ All systems operational                                    │
│   │                                                              │
│   │ API Response Time:     125ms avg (Target: <200ms)           │
│   │ Video Generation:      8.2s avg (Target: <10s)              │
│   │ Error Rate:            0.3% (Target: <1%)                    │
│   │ Uptime (30 days):      99.98%                                │
│   │                                                              │
│   │ Recent Issues: None                                          │
│   │                                                              │
│   │ [View System Logs]                                           │
│   │                                                              │
│   └──────────────────────────────────────────────────────────────┘
│
├─> {Admin explores analytics}
│
│   ├─> [4a. Change date range]
│   │   Dropdown options:
│   │   - Last 7 days
│   │   - Last 30 days (default)
│   │   - Last 90 days
│   │   - This semester
│   │   - Custom range
│   │
│   │   API: GET /api/v1/admin/analytics/overview?date_range=last_7_days
│   │   Refresh all metrics and charts
│   │
│   ├─> [4b. Export analytics report]
│   │   Click "Export" button, choose format
│   │   API: GET /api/v1/admin/analytics/export?format=pdf
│   │   Download: lincoln-analytics-2024-01-20.pdf
│   │
│   │   Report includes:
│   │   - All dashboard metrics
│   │   - Detailed charts
│   │   - Student roster with engagement scores
│   │   - Teacher activity summary
│   │   - Executive summary
│   │
│   ├─> [4c. Drill down into specific metric]
│   │   Click on any metric card
│   │   Example: Click "847 Videos Generated"
│   │   Navigate to: /admin/analytics/content
│   │
│   │   Show detailed content analytics:
│   │   - Generation success/failure rates
│   │   - Most requested topics by day/week/month
│   │   - Peak usage times
│   │   - Average generation time by topic
│   │   - Cache hit rate by topic
│   │
│   ├─> [4d. View student engagement details]
│   │   Click "View Full Student Report"
│   │   Navigate to: /admin/analytics/students
│   │
│   │   Display:
│   │   - Full student list with engagement scores
│   │   - Sort/filter by engagement level
│   │   - Identify at-risk students
│   │   - Export student engagement report
│   │
│   ├─> [4e. View teacher activity]
│   │   Navigate to: /admin/analytics/teachers
│   │
│   │   Display:
│   │   - Teacher usage statistics
│   │   - Classes per teacher
│   │   - Recommendations sent
│   │   - Login frequency
│   │   - Identify inactive teachers
│   │
│   └─> [4f. View system logs]
│       Click "View System Logs"
│       Navigate to: /admin/system/logs
│
│       Display:
│       - Recent API errors
│       - Failed video generations
│       - Authentication failures
│       - System performance alerts
│       - Integration status (Vertex AI, Nano Banana)
│
└─> END: Admin reviewed analytics

════════════════════════════════════════════════════════════════════
AUTOMATED ALERTING:

Admin receives automatic email alerts for:

ALERT 1: Low Engagement
├─> Trigger: >10% of students inactive for 7+ days
├─> Email: "Student Engagement Alert - Lincoln High School"
├─> Action: Review at-risk students, notify teachers

ALERT 2: System Performance
├─> Trigger: Avg generation time > 15s for 1 hour
├─> Email: "System Performance Degraded"
├─> Action: Review system logs, contact support if needed

ALERT 3: High Error Rate
├─> Trigger: Error rate > 5% for 30 minutes
├─> Email: "System Health Alert - High Error Rate"
├─> Action: Check system status, review error logs

ALERT 4: Quota Warning
├─> Trigger: Student count > 90% of max (450/500)
├─> Email: "Approaching Student Quota"
├─> Action: Plan for expansion or archive inactive students

ALERT 5: Contract Expiration
├─> Trigger: 30 days before contract_end
├─> Email: "Contract Renewal Reminder"
├─> Action: Contact sales for renewal

TIME ESTIMATES:
- Review dashboard: 2-3 minutes
- Deep dive into specific metric: 5-10 minutes
- Export and review full report: 10-15 minutes
- Address at-risk students: Varies (10-30 minutes)
```

---

## Error Handling Flows

### Common Error Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOWS                          │
└─────────────────────────────────────────────────────────────────┘

ERROR 1: Authentication Failure
├─> Trigger: Invalid credentials, expired session, etc.
├─> Display: [!] "Session expired. Please log in again."
├─> Action: Redirect to login page with return_url
├─> User: Re-authenticates and returns to original page

ERROR 2: Authorization Failure (403 Forbidden)
├─> Trigger: User attempts to access resource without permission
├─> Example: Student tries to access /admin
├─> Display: [!] "You don't have permission to access this page."
├─> Action: Redirect to appropriate dashboard

ERROR 3: Rate Limit Exceeded
├─> Trigger: Student requests 11th video within 1 hour
├─> Display: [!] "You've reached your hourly limit (10 videos).
│             Try again in 23 minutes."
├─> Action: Show timer, suggest browsing existing content

ERROR 4: Validation Error
├─> Trigger: Invalid input (malformed email, short password, etc.)
├─> Display: Inline field-level error messages
├─> Example: "Password must be at least 8 characters"
├─> Action: User corrects input and resubmits

ERROR 5: Network Error
├─> Trigger: Connection lost, timeout, etc.
├─> Display: [!] "Network connection lost. Retrying..."
├─> Action: Auto-retry with exponential backoff (3 attempts)
├─> If failed: Show "Check your connection" with [Retry] button

ERROR 6: Server Error (500)
├─> Trigger: Unexpected server error
├─> Display: [!] "Something went wrong. We've been notified."
├─> Action: Log error to monitoring, show generic error page
├─> User: [Retry] [Go to Dashboard] [Contact Support]

ERROR 7: Video Generation Failure
├─> Trigger: AI service timeout, safety filter, etc.
├─> Display: [!] "We couldn't generate your video. Please try again."
├─> Reason shown (if safe): "Generation timeout" or "Try different query"
├─> Action: [Retry] [Try Different Topic] [Report Issue]

ERROR 8: Content Not Found (404)
├─> Trigger: Video deleted, invalid ID, etc.
├─> Display: [!] "This content is no longer available."
├─> Action: [Request New Video] [Browse Topics] [Back to Dashboard]

ERROR 9: Quota Exceeded (Organization Level)
├─> Trigger: Org reaches max students (500/500)
├─> Display (Admin): [!] "Student quota reached. Contact sales to upgrade."
├─> Display (Teacher): [!] "Cannot invite students. Contact your admin."
├─> Action: Prevent new invitations until quota increased

ERROR 10: Safety Filter Triggered
├─> Trigger: User input contains inappropriate content
├─> Display: [!] "Your request contains inappropriate content.
│               Please revise and try again."
├─> Action: Clear input, show guidelines, allow retry
├─> Log: Track safety_filter_triggered event for monitoring

ERROR RECOVERY STRATEGIES:

Strategy 1: Graceful Degradation
- Feature unavailable → Disable UI element, show explanation
- Example: "Video generation temporarily unavailable.
            Browse existing content."

Strategy 2: Offline Support
- Store critical data locally (learning history, preferences)
- Sync when connection restored
- Show "Offline Mode" indicator

Strategy 3: Retry with Backoff
- Auto-retry failed requests: 1s, 2s, 4s delays
- Max 3 attempts
- User-initiated retry always available

Strategy 4: User Feedback
- All errors include:
  - Clear explanation (what happened)
  - Impact (what can't be done)
  - Next steps (how to resolve)
  - Support link (if needed)

Strategy 5: Error Logging
- All errors logged to monitoring system
- Include: user_id, action, error_type, timestamp, context
- Aggregate: Error rate dashboards, alert on spikes
