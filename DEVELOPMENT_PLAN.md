# Vividly - Comprehensive Development Plan

**Document Version**: 1.0
**Date**: October 28, 2025
**Status**: Active Development Roadmap
**Project**: Vividly MVP - AI-Powered Personalized STEM Learning Platform

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Current State Assessment](#current-state-assessment)
4. [Development Phases](#development-phases)
5. [Phase 1: Foundation & Infrastructure](#phase-1-foundation--infrastructure)
6. [Phase 2: Core Backend Services](#phase-2-core-backend-services)
7. [Phase 3: AI Content Pipeline](#phase-3-ai-content-pipeline)
8. [Phase 4: Frontend Application](#phase-4-frontend-application)
9. [Phase 5: Integration & Testing](#phase-5-integration--testing)
10. [Phase 6: Pilot Deployment](#phase-6-pilot-deployment)
11. [Phase 7: Production Hardening](#phase-7-production-hardening)
12. [Technical Dependencies](#technical-dependencies)
13. [Resource Requirements](#resource-requirements)
14. [Risk Assessment & Mitigation](#risk-assessment--mitigation)
15. [Success Metrics](#success-metrics)
16. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

### Project Overview

Vividly is an AI-powered educational platform that generates personalized STEM micro-lessons for high school students. The platform uses student interests to create engaging video content that explains academic concepts through relatable analogies, transforming traditional textbook learning into personalized, multimedia experiences.

### Business Model

- **Target Market**: B2B/B2G - School districts and educational institutions
- **Pilot Customer**: Metro Nashville Public Schools (MNPS)
- **Pilot Scale**: ~3,000 active students across multiple high schools
- **Revenue Model**: Per-student subscription (post-MVP)

### Technical Approach

- **Architecture**: Serverless, event-driven, microservices on GCP
- **AI Stack**: Vertex AI (Gemini/LearnLM), Vector Search RAG, Cloud TTS, Nano Banana
- **Frontend**: React 18 + TypeScript + shadcn/ui
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy
- **Infrastructure**: Fully automated with Terraform

### Current Status

- **Phase 1**: 100% Complete (Infrastructure & Foundation)
- **Phase 2**: 0% Complete (Backend Services - Ready to Start)
- **Overall Progress**: ~15% complete
- **Estimated Time to MVP**: 12-14 weeks

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT TIER                                 │
│  React Web App → Cloud Load Balancer → API Gateway              │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION TIER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Student    │  │   Teacher    │  │    Admin     │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     NLU      │  │    Cache     │  │   Content    │          │
│  │   Service    │  │   Service    │  │   Delivery   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  PROCESSING TIER                                 │
│  Cloud Pub/Sub Topics → Cloud Functions Workers                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Script     │  │    Audio     │  │    Video     │          │
│  │   Worker     │  │   Worker     │  │   Worker     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      DATA TIER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Cloud SQL  │  │     GCS      │  │  Vertex AI   │          │
│  │  PostgreSQL  │  │   Storage    │  │Vector Search │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Core User Flows

**Student Content Request Flow**:
1. Student enters free-text learning request (e.g., "Explain Newton's 3rd Law using basketball")
2. NLU Service extracts topic_id → "topic_phys_mech_newton_3"
3. Cache Service checks for existing content (topic_id + interest + style)
4. **Cache HIT**: Return video URL immediately
5. **Cache MISS**:
   - Return script + audio (Fast Path / "Vivid Now") in ~10 seconds
   - Generate video asynchronously (Full Path / "Vivid Learning") in ~2-3 minutes
   - Notify student when video is ready

**Teacher Monitoring Flow**:
1. Teacher views class dashboard
2. See student engagement metrics (last active, videos viewed, topics completed)
3. Drill down into individual student progress
4. Identify struggling students or gaps in topic completion

**Admin Management Flow**:
1. District admin uploads student roster (CSV)
2. System creates accounts, sends invitations
3. Admin monitors KPIs: adoption rate, engagement, cache hit rate
4. Manage teacher/school admin accounts

---

## Current State Assessment

### Phase 1: Foundation & Infrastructure ✅ (100% Complete)

**Completed Items**:

1. **Infrastructure as Code** ✅
   - Terraform configuration for all GCP resources
   - Multi-environment setup (dev, staging, prod)
   - VPC, Cloud SQL, GCS buckets, Pub/Sub, Cloud Run, Cloud Functions
   - Secret Manager for credentials
   - Cloud Memorystore (Redis) for caching
   - Cloud CDN for video delivery
   - GitHub Actions CI/CD pipelines

2. **Database Schema** ✅
   - PostgreSQL schema designed and documented
   - Users, organizations, schools, classes
   - Topics, interests, content metadata
   - Progress tracking, feedback, analytics
   - Feature flags system (with migrations ready)
   - Request tracking system (with migrations ready)

3. **Authentication & Security** ✅
   - JWT-based authentication middleware
   - bcrypt password hashing (cost factor 12)
   - RBAC decorators (require_admin, require_teacher, require_student)
   - Session management and revocation
   - Login attempt tracking and rate limiting

4. **Rate Limiting** ✅
   - Token bucket algorithm with Redis
   - Per-user and per-IP limits
   - Configurable limits per endpoint
   - Auth protection: 5 attempts/15min
   - Content requests: 10/hour

5. **Development Environment** ✅
   - Docker Compose with all services
   - Hot reload for backend and frontend
   - Database UI (Adminer)
   - Redis UI (Redis Commander)
   - Local development fully functional

6. **Error Tracking** ✅
   - Sentry integration for FastAPI
   - Environment-based sample rates
   - Request/response tracking
   - User context capture
   - Automatic breadcrumb tracking

7. **Circuit Breaker Pattern** ✅
   - Protection for external API calls
   - Three states: CLOSED, OPEN, HALF_OPEN
   - Pre-configured for Nano Banana, Vertex AI, Gemini
   - Automatic state transitions
   - Statistics tracking

8. **Frontend Design System** ✅
   - React 18 + TypeScript + Vite
   - Tailwind CSS + shadcn/ui components
   - Vividly color palette and typography
   - Path aliases configured (@/ imports)
   - Video player component (Plyr)
   - Comprehensive design documentation

9. **OER Content Pipeline** ✅
   - 5-stage ingestion: Download → Process → Chunk → Embed → Index
   - OpenStax support (Physics, Chemistry, Biology)
   - Vertex AI embeddings (768-dim)
   - Vector Search integration
   - Complete documentation and scripts

10. **Email Templates** ✅
    - Student invitation
    - Teacher/Admin welcome
    - Password reset
    - Content ready notifications
    - Responsive HTML design

11. **Monitoring & Observability** ✅
    - Cost monitoring scripts
    - Billing budgets with alerts
    - Cloud Monitoring dashboards
    - Feature flag system
    - Request tracking system

12. **Database Seed Data** ✅
    - Davidson County Metro Schools
    - 2 high schools (Hillsboro, Early College)
    - 3 admins, 7 teachers, 35 students
    - Sample topics, interests, classes
    - Test credentials for all roles

### What's Working Right Now

- ✅ Local development environment (`docker-compose up`)
- ✅ GCP infrastructure (Terraform deployed)
- ✅ Authentication & authorization system
- ✅ Rate limiting with Redis
- ✅ Error tracking with Sentry
- ✅ Video delivery via Cloud CDN
- ✅ Circuit breaker for API resilience
- ✅ Professional video player component
- ✅ Cost monitoring and alerts
- ✅ Feature flag system (migrations ready)
- ✅ Request tracking system (migrations ready)

### Immediate Blockers (To Be Resolved)

1. **Database Migrations** ⚠️
   - Status: SQL files created, not yet executed
   - Blocker: Need to run migrations via Cloud Shell (database has private IP only)
   - Impact: Feature flags and request tracking not operational
   - Resolution: Use Cloud Shell to run migrations tonight

2. **OER Content Ingestion** ⚠️
   - Status: Pipeline created, not yet executed
   - Blocker: Need to run ingestion for Physics, Chemistry, Biology
   - Impact: No RAG content available for script generation
   - Resolution: Run ingestion pipeline (~70 minutes) after migrations

### What Needs to Be Built (Phases 2-7)

- Backend API endpoints (all services)
- Frontend components (all user interfaces)
- AI workers (NLU, Script, Audio, Video)
- Integration testing
- Deployment automation
- Production hardening

---

## Development Phases

### Phase Overview

| Phase | Focus Area | Duration | Dependencies | Status |
|-------|-----------|----------|--------------|--------|
| Phase 1 | Foundation & Infrastructure | 4 weeks | None | ✅ Complete |
| Phase 2 | Core Backend Services | 3 weeks | Phase 1 | ⏳ Ready to Start |
| Phase 3 | AI Content Pipeline | 3 weeks | Phase 2 | 🔜 Pending |
| Phase 4 | Frontend Application | 3 weeks | Phase 2 | 🔜 Pending |
| Phase 5 | Integration & Testing | 2 weeks | Phase 3, 4 | 🔜 Pending |
| Phase 6 | Pilot Deployment | 1 week | Phase 5 | 🔜 Pending |
| Phase 7 | Production Hardening | 2 weeks | Phase 6 | 🔜 Pending |

**Total Estimated Duration**: 18 weeks (4.5 months) from current state

**Current Progress**: ~15% complete (Phase 1 done, 6 phases remaining)

---

## Phase 1: Foundation & Infrastructure

### Status: ✅ COMPLETE (100%)

### Accomplishments

**Infrastructure**:
- Complete GCP infrastructure via Terraform
- Multi-environment support (dev, staging, prod)
- Serverless compute (Cloud Run, Cloud Functions)
- Managed databases (Cloud SQL, Cloud Memorystore Redis)
- Object storage (GCS with CDN)
- Message queuing (Pub/Sub)
- AI services (Vertex AI, Vector Search)

**Development Tools**:
- Docker Compose for local development
- Hot reload for rapid iteration
- Database and Redis UI tools
- Comprehensive documentation

**Security & Reliability**:
- Authentication and authorization system
- Rate limiting and throttling
- Error tracking (Sentry)
- Circuit breaker for external APIs
- Cost monitoring and alerting

**Quality of Life**:
- Seed data for testing
- Email templates
- Design system
- Video player component

### Key Decisions Made

1. **GCP over AWS/Azure**: Better AI/ML services (Vertex AI), simpler serverless
2. **FastAPI over Django/Flask**: Modern async, automatic API docs, better performance
3. **React over Vue/Angular**: Larger ecosystem, better TypeScript support
4. **shadcn/ui over Material-UI**: More customizable, Tailwind-based, modern
5. **Plyr over Video.js**: Better accessibility, simpler API
6. **PostgreSQL over MySQL**: Better JSON support, full ACID compliance
7. **Redis over Memcached**: More features (pub/sub, sorted sets), persistence
8. **Pub/Sub over SQS**: Native GCP integration, better Cloud Functions triggers
9. **Terraform over Pulumi**: More mature, better GCP support, larger community

### Deliverables

- [x] Terraform infrastructure code
- [x] Database schema and migrations
- [x] Authentication middleware
- [x] Rate limiting middleware
- [x] Docker Compose development environment
- [x] Frontend design system
- [x] OER ingestion pipeline
- [x] Email templates
- [x] Seed data scripts
- [x] Monitoring and alerting setup

---

## Phase 2: Core Backend Services

### Status: ⏳ READY TO START (0% Complete)

### Duration: 3 weeks

### Objective

Build all core backend API services and endpoints required for the MVP, focusing on authentication, user management, and basic CRUD operations before adding AI complexity.

### Milestones

#### Milestone 2.1: Authentication & User Management (Week 1)

**Deliverables**:

1. **Authentication API** (3 days)
   - `POST /api/v1/auth/register` - User registration
   - `POST /api/v1/auth/login` - User login
   - `POST /api/v1/auth/logout` - User logout
   - `POST /api/v1/auth/refresh` - Token refresh
   - `POST /api/v1/auth/reset-password` - Password reset request
   - `POST /api/v1/auth/reset-password/confirm` - Password reset confirmation
   - `GET /api/v1/auth/me` - Get current user

2. **Student Service** (2 days)
   - `GET /api/v1/students/profile` - Get student profile
   - `PUT /api/v1/students/profile` - Update student profile
   - `GET /api/v1/students/interests` - Get student interests
   - `PUT /api/v1/students/interests` - Update student interests
   - `GET /api/v1/students/progress` - Get learning progress

3. **Teacher Service** (2 days)
   - `GET /api/v1/teachers/profile` - Get teacher profile
   - `GET /api/v1/teachers/classes` - List classes
   - `POST /api/v1/teachers/classes` - Create class
   - `GET /api/v1/teachers/classes/{id}` - Get class details
   - `GET /api/v1/teachers/classes/{id}/students` - List students in class
   - `POST /api/v1/teachers/student-requests` - Request new student account

**Acceptance Criteria**:
- All endpoints implement proper authentication
- RBAC correctly enforces permissions
- Rate limiting applies to all endpoints
- Comprehensive error handling
- Unit tests (>80% coverage)
- API documentation (FastAPI auto-docs)
- Postman collection for manual testing

**Technical Implementation**:

```python
# Example: Student Profile Endpoint
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.middleware.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import StudentProfile, StudentProfileUpdate

router = APIRouter(prefix="/api/v1/students", tags=["students"])

@router.get("/profile", response_model=StudentProfile)
async def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current student's profile."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    return StudentProfile.from_orm(current_user)

@router.put("/profile", response_model=StudentProfile)
async def update_student_profile(
    profile_update: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current student's profile."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    # Update user object
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return StudentProfile.from_orm(current_user)
```

#### Milestone 2.2: Admin & Content Management (Week 2)

**Deliverables**:

1. **Admin Service** (3 days)
   - `POST /api/v1/admin/users/bulk-upload` - Bulk student upload
   - `GET /api/v1/admin/users` - List all users (paginated)
   - `POST /api/v1/admin/users` - Create user manually
   - `PUT /api/v1/admin/users/{id}` - Update user
   - `DELETE /api/v1/admin/users/{id}` - Soft delete user
   - `GET /api/v1/admin/pending-requests` - Get pending account requests
   - `PUT /api/v1/admin/requests/{id}/approve` - Approve account request
   - `PUT /api/v1/admin/requests/{id}/deny` - Deny account request
   - `GET /api/v1/admin/kpis` - Get dashboard KPIs

2. **Topics & Interests API** (2 days)
   - `GET /api/v1/topics` - List all topics (with filters)
   - `GET /api/v1/topics/search` - Search topics by keyword
   - `GET /api/v1/topics/{id}` - Get topic details
   - `GET /api/v1/topics/{id}/prerequisites` - Get prerequisite topics
   - `GET /api/v1/interests` - List all canonical interests
   - `GET /api/v1/interests/categories` - List interest categories

3. **Content Metadata API** (2 days)
   - `GET /api/v1/content/{id}` - Get content metadata
   - `GET /api/v1/content/check` - Check if content exists for (topic, interest)
   - `POST /api/v1/content/{id}/feedback` - Submit content feedback
   - `GET /api/v1/content/recent` - Get recently generated content

**Acceptance Criteria**:
- Bulk upload handles CSV with validation
- Account request workflow complete
- Topic search returns relevant results
- KPI calculations are accurate
- All endpoints have comprehensive tests
- Admin endpoints properly restricted

**Bulk Upload CSV Format**:
```csv
first_name,last_name,email,grade_level,school_id
John,Doe,john.doe@mnps.edu,10,school_hillsboro_hs
Jane,Smith,jane.smith@mnps.edu,11,school_hillsboro_hs
```

#### Milestone 2.3: Cache & Delivery Services (Week 3)

**Deliverables**:

1. **Cache Service** (2 days)
   - Cache key generation: `SHA256(topic_id|interest|style)`
   - `POST /internal/v1/cache/check` - Check cache for content
   - `POST /internal/v1/cache/store` - Store content metadata
   - `GET /internal/v1/cache/stats` - Get cache hit/miss statistics
   - Redis integration for hot cache
   - GCS metadata lookup for cold cache

2. **Content Delivery Service** (2 days)
   - `GET /api/v1/content/{id}/url` - Get signed GCS URL
   - Generate signed URLs with 15-minute TTL
   - Track content views and analytics
   - Handle CDN cache invalidation
   - Support different quality levels (1080p, 720p, 480p)

3. **Notification Service** (3 days)
   - `POST /internal/v1/notifications/send` - Send notification
   - Email notifications via SendGrid or Cloud Email
   - Real-time notifications via WebSocket (future) or polling
   - Notification templates
   - Delivery tracking and retry logic
   - Queue integration for async sending

**Cache Service Logic**:

```python
from hashlib import sha256
import json
from google.cloud import storage

class CacheService:
    def __init__(self, redis_client, gcs_client):
        self.redis = redis_client
        self.gcs = gcs_client

    def generate_cache_key(self, topic_id: str, interest: str, style: str = "default") -> str:
        """Generate deterministic cache key."""
        key_string = f"{topic_id}|{interest}|{style}"
        return sha256(key_string.encode()).hexdigest()

    async def check_cache(self, topic_id: str, interest: str, style: str = "default"):
        """Check if content exists in cache."""
        cache_key = self.generate_cache_key(topic_id, interest, style)

        # Check hot cache (Redis)
        redis_data = await self.redis.get(f"content:{cache_key}")
        if redis_data:
            return json.loads(redis_data)

        # Check cold cache (GCS metadata)
        bucket = self.gcs.bucket("vividly-mvp-videos")
        blob = bucket.blob(f"{cache_key}/metadata.json")

        if blob.exists():
            metadata = json.loads(blob.download_as_text())
            # Warm Redis cache
            await self.redis.setex(
                f"content:{cache_key}",
                3600,  # 1 hour TTL
                json.dumps(metadata)
            )
            return metadata

        return None  # Cache miss
```

**Testing Requirements**:
- Unit tests for all services
- Integration tests for cache flow
- Load testing for cache service (1000 req/s)
- Signed URL expiration verification
- Email delivery testing (sandbox mode)

### Phase 2 Success Criteria

- [ ] All API endpoints implemented and documented
- [ ] Authentication works end-to-end
- [ ] User management (CRUD) functional
- [ ] Bulk upload processes 1000 students in <30 seconds
- [ ] Cache service returns results in <100ms
- [ ] Content delivery generates signed URLs successfully
- [ ] Email notifications send successfully
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Postman collection with examples
- [ ] API documentation complete

### Dependencies

**Requires**:
- Phase 1 complete ✅
- Database migrations executed ⚠️ (tonight)
- Seed data loaded ✅

**Blocks**:
- Phase 3 (AI Content Pipeline)
- Phase 4 (Frontend Application)

---

## Phase 3: AI Content Pipeline

### Status: 🔜 PENDING (0% Complete)

### Duration: 3 weeks

### Objective

Build the complete AI content generation pipeline from natural language input to finished video, including NLU, RAG retrieval, script generation, audio synthesis, and video rendering.

### Milestones

#### Milestone 3.1: NLU & Topic Extraction (Week 1)

**Deliverables**:

1. **NLU Service** (3 days)
   - Natural language understanding using Vertex AI Gemini
   - Free-text input → topic_id extraction
   - Clarification dialogue when ambiguous
   - Context awareness (user's grade level, prior topics)
   - Fallback handling for out-of-scope requests

2. **Topic Mapping System** (2 days)
   - Fuzzy matching for similar topics
   - Synonym handling ("gravity" vs "gravitational force")
   - Hierarchical topic navigation
   - Prerequisite checking
   - Topic recommendation based on history

3. **Integration** (2 days)
   - Connect to Student Service
   - Cache integration for repeated queries
   - Performance optimization (<5s response)
   - Error handling and fallbacks
   - Logging and monitoring

**NLU Prompt Template**:

```python
NLU_PROMPT = """You are an educational AI that maps student questions to standardized topics.

Available Topics (JSON):
{topics_json}

Student Input: "{student_input}"
Student Grade Level: {grade_level}
Student Context: {context}

Task:
1. Identify the primary academic topic
2. Map to one of the available topic_ids
3. If ambiguous, generate clarifying questions
4. If out of scope, politely redirect

Output (JSON):
{
  "confidence": 0.95,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": false,
  "reasoning": "Student is asking about action-reaction pairs in physics."
}
"""
```

**Example NLU Flow**:

```
Input: "Explain Newton's Third Law using basketball"
↓
NLU Service → Vertex AI Gemini
↓
Output: {
  "topic_id": "topic_phys_mech_newton_3",
  "confidence": 0.98,
  "clarification_needed": false
}
↓
Return to Student Service
```

**Example Clarification Flow**:

```
Input: "Explain gravity"
↓
NLU Service detects ambiguity
↓
Output: {
  "clarification_needed": true,
  "clarifying_questions": [
    "Are you interested in Newton's Law of Universal Gravitation?",
    "Or gravitational acceleration on Earth (g = 9.8 m/s²)?",
    "Or Einstein's General Relativity?"
  ]
}
↓
Student selects option 1
↓
NLU Service returns: {"topic_id": "topic_phys_grav_universal"}
```

#### Milestone 3.2: RAG & Script Generation (Week 2)

**Deliverables**:

1. **Vector Search Integration** (2 days)
   - Query embedding generation
   - Top-K retrieval (K=5-10)
   - Context ranking and filtering
   - Reranking for relevance
   - Vertex AI Vector Search optimization

2. **Script Generation Worker** (3 days)
   - Cloud Function triggered by Pub/Sub
   - RAG-based content retrieval
   - LearnLM prompt engineering
   - JSON storyboard generation
   - Interest-based personalization
   - Fallback interest selection
   - GCS storage of scripts

3. **Script Structure & Validation** (2 days)
   - Storyboard JSON schema
   - Scene structure validation
   - Character limit enforcement (200 chars/scene)
   - Educational content verification
   - AI safety guardrails
   - Profanity and bias filtering

**RAG Retrieval Flow**:

```python
async def retrieve_context(topic_id: str, grade_level: int) -> List[str]:
    """Retrieve relevant OER content chunks."""

    # Get topic metadata
    topic = await get_topic(topic_id)

    # Create query embedding
    query = f"{topic.name} {topic.description} grade {grade_level}"
    embedding = await vertex_ai_embed(query)

    # Search vector index
    results = await vertex_search.query(
        embedding=embedding,
        top_k=10,
        filters={"subject": topic.subject, "grade_level": grade_level}
    )

    # Extract text chunks
    context_chunks = [r.text for r in results if r.score > 0.7]

    return context_chunks
```

**LearnLM Script Prompt**:

```python
SCRIPT_PROMPT = """You are an expert educational content creator for Vividly.

Task: Create a 2-3 minute personalized video lesson script.

Topic: {topic_name}
Subject: {subject}
Grade Level: {grade_level}
Student Interest: {interest}

OER Content Context:
{rag_context}

Requirements:
1. Explain {topic_name} using {interest} as the primary analogy/example
2. Keep language appropriate for grade {grade_level}
3. Use engaging, conversational tone
4. Break into 6-8 scenes (20-30 seconds each)
5. Include visual descriptions for each scene
6. Ensure educational accuracy (use OER content)
7. Include a brief recap at the end

Output Format (JSON):
{
  "title": "Newton's Third Law: The Basketball Perspective",
  "duration_estimate": 150,
  "scenes": [
    {
      "scene_number": 1,
      "duration": 25,
      "narration": "Imagine you're on the court, about to take a shot...",
      "visual_description": "Basketball player in shooting stance",
      "educational_content": "Introduction to action-reaction pairs"
    },
    ...
  ],
  "key_takeaways": ["Action-reaction pairs are equal and opposite", ...],
  "prerequisites": ["Newton's First Law", "Newton's Second Law"]
}
"""
```

**Script Worker Architecture**:

```python
# Cloud Function: Script Worker
@functions_framework.cloud_event
def generate_script(cloud_event):
    """Generate personalized script using RAG + LearnLM."""

    # Parse Pub/Sub message
    data = base64.b64decode(cloud_event.data["message"]["data"])
    request = json.loads(data)

    topic_id = request["topic_id"]
    interest = request["interest"]
    grade_level = request["grade_level"]
    cache_key = request["cache_key"]

    try:
        # 1. RAG Retrieval
        context = await retrieve_context(topic_id, grade_level)

        # 2. Generate script with LearnLM
        script = await generate_with_learnlm(
            topic_id=topic_id,
            interest=interest,
            context=context,
            grade_level=grade_level
        )

        # 3. Validate script
        validate_script(script)

        # 4. Save to GCS
        save_script_to_gcs(cache_key, script)

        # 5. Trigger audio generation
        publish_to_pubsub("generate-audio", {
            "cache_key": cache_key,
            "script": script
        })

        # 6. Trigger video generation (parallel)
        publish_to_pubsub("generate-video", {
            "cache_key": cache_key,
            "script": script
        })

        # 7. Update database
        update_content_status(cache_key, "script_complete")

        return {"status": "success", "cache_key": cache_key}

    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        publish_to_dlq("dlq-script", request)
        raise
```

#### Milestone 3.3: Audio & Video Generation (Week 3)

**Deliverables**:

1. **Audio Worker** (2 days)
   - Cloud Function triggered by Pub/Sub
   - Cloud Text-to-Speech integration
   - Voice selection (appropriate for grade level)
   - Audio effects (background music, fade in/out)
   - MP3 encoding and compression
   - GCS storage with CDN optimization

2. **Video Worker** (3 days)
   - Cloud Function triggered by Pub/Sub
   - Nano Banana API integration
   - Storyboard → video rendering
   - Audio track synchronization
   - Quality levels (1080p, 720p, 480p)
   - Progress polling and timeout handling
   - GCS storage with CDN cache warming

3. **Pipeline Orchestration** (2 days)
   - Pub/Sub message flow
   - Error handling and retries
   - Dead letter queues
   - Progress tracking in database
   - Notification on completion
   - Cache warming for popular content

**Audio Worker**:

```python
@functions_framework.cloud_event
def generate_audio(cloud_event):
    """Generate audio narration using Cloud TTS."""

    data = base64.b64decode(cloud_event.data["message"]["data"])
    request = json.loads(data)

    cache_key = request["cache_key"]
    script = request["script"]

    try:
        # Combine all scene narrations
        full_narration = " ".join([scene["narration"] for scene in script["scenes"]])

        # Generate audio with Cloud TTS
        audio_content = await text_to_speech(
            text=full_narration,
            voice_name="en-US-Neural2-J",  # Young adult voice
            speaking_rate=1.0,
            pitch=0.0
        )

        # Save to GCS
        audio_url = save_audio_to_gcs(cache_key, audio_content)

        # Update database
        update_content_status(cache_key, "audio_complete", audio_url)

        # Notify student (Fast Path complete)
        publish_to_pubsub("content-ready", {
            "cache_key": cache_key,
            "status": "fast_path",
            "audio_url": audio_url,
            "script": script
        })

        return {"status": "success", "audio_url": audio_url}

    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        publish_to_dlq("dlq-audio", request)
        raise
```

**Video Worker** (with Circuit Breaker):

```python
@functions_framework.cloud_event
async def generate_video(cloud_event):
    """Generate video using Nano Banana API."""

    data = base64.b64decode(cloud_event.data["message"]["data"])
    request = json.loads(data)

    cache_key = request["cache_key"]
    script = request["script"]

    try:
        # Get audio URL from database
        audio_url = get_content_audio_url(cache_key)

        # Prepare Nano Banana payload
        payload = {
            "storyboard": script["scenes"],
            "audio_url": audio_url,
            "quality": "1080p",
            "style": "educational"
        }

        # Call Nano Banana with circuit breaker
        video_job_id = await nano_banana_breaker.call(
            nano_banana_api.create_video,
            payload
        )

        # Poll for completion (max 10 minutes)
        video_url = await poll_video_completion(video_job_id, timeout=600)

        # Download and save to GCS
        final_video_url = await download_and_store_video(video_url, cache_key)

        # Update database
        update_content_status(cache_key, "video_complete", final_video_url)

        # Warm CDN cache
        warm_cdn_cache(final_video_url)

        # Notify student (Full Path complete)
        publish_to_pubsub("content-ready", {
            "cache_key": cache_key,
            "status": "full_path",
            "video_url": final_video_url
        })

        return {"status": "success", "video_url": final_video_url}

    except CircuitBreakerOpenError:
        logger.warning("Circuit breaker open for Nano Banana")
        # Retry later
        publish_with_delay("generate-video", request, delay_seconds=300)

    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        publish_to_dlq("dlq-video", request)
        raise
```

### Phase 3 Success Criteria

- [ ] NLU correctly identifies topics (>90% accuracy)
- [ ] RAG retrieves relevant content (precision >80%)
- [ ] Scripts are educationally accurate
- [ ] Scripts incorporate student interests naturally
- [ ] Audio quality is clear and professional
- [ ] Videos render successfully (>95% success rate)
- [ ] Fast Path delivers in <10 seconds
- [ ] Full Path delivers in <3 minutes
- [ ] Circuit breaker prevents cascading failures
- [ ] Dead letter queues capture failed jobs
- [ ] Pipeline scales to 100 concurrent generations
- [ ] AI safety guardrails block inappropriate content

### Dependencies

**Requires**:
- Phase 2 complete (Backend Services)
- OER content ingested ⚠️ (run pipeline after migrations)
- Vertex AI Vector Search index built
- Nano Banana API key and quota

**Blocks**:
- Phase 5 (Integration & Testing)

---

## Phase 4: Frontend Application

### Status: 🔜 PENDING (0% Complete)

### Duration: 3 weeks

### Objective

Build all user-facing interfaces for students, teachers, and administrators using React, TypeScript, and shadcn/ui components.

### Milestones

#### Milestone 4.1: Student Interface (Week 1)

**Deliverables**:

1. **Authentication UI** (2 days)
   - Login page
   - Registration flow
   - Password reset flow
   - Email verification
   - Session management
   - Protected routes

2. **Student Dashboard** (3 days)
   - Recent activity feed
   - Progress overview
   - Quick content request
   - Recommended topics
   - Interest badges
   - Streak counter

3. **Content Request Interface** (2 days)
   - Free-text input with autocomplete
   - Topic clarification dialogue
   - Interest selection
   - Loading states (Fast Path / Full Path)
   - Error handling and retries

**Component Structure**:

```tsx
// StudentDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { ContentRequestInput } from '@/components/ContentRequestInput';
import { RecentActivity } from '@/components/RecentActivity';
import { RecommendedTopics } from '@/components/RecommendedTopics';

export function StudentDashboard() {
  const { data: profile } = useQuery(['student', 'profile'], fetchProfile);
  const { data: progress } = useQuery(['student', 'progress'], fetchProgress);

  return (
    <div className="container mx-auto py-8">
      <div className="grid gap-6 md:grid-cols-3">
        {/* Stats Cards */}
        <Card>
          <CardHeader>
            <CardTitle>Videos Watched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{progress?.videos_watched}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Topics Mastered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{progress?.topics_completed}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Learning Streak</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{progress?.streak_days} days</div>
          </CardContent>
        </Card>
      </div>

      {/* Content Request */}
      <div className="mt-8">
        <ContentRequestInput />
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <RecentActivity />
      </div>

      {/* Recommended Topics */}
      <div className="mt-8">
        <RecommendedTopics interests={profile?.interests} />
      </div>
    </div>
  );
}
```

**Content Request Flow**:

```tsx
// ContentRequestInput.tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

export function ContentRequestInput() {
  const [query, setQuery] = useState('');

  const requestMutation = useMutation({
    mutationFn: (input: string) =>
      fetch('/api/v1/students/content/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input })
      }).then(res => res.json()),
    onSuccess: (data) => {
      if (data.clarification_needed) {
        // Show clarification dialogue
        showClarificationDialog(data.clarifying_questions);
      } else {
        // Navigate to content viewer
        navigate(`/content/${data.cache_key}`);
      }
    }
  });

  return (
    <div className="flex gap-4">
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="What do you want to learn? (e.g., 'Explain Newton's 3rd Law using basketball')"
        className="flex-1"
        onKeyPress={(e) => e.key === 'Enter' && requestMutation.mutate(query)}
      />
      <Button
        onClick={() => requestMutation.mutate(query)}
        disabled={!query || requestMutation.isPending}
      >
        {requestMutation.isPending ? (
          <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</>
        ) : (
          'Learn'
        )}
      </Button>
    </div>
  );
}
```

4. **Video Viewing Interface** (2 days)
   - Video player integration (Plyr)
   - Script display (synchronized)
   - Playback controls
   - Quality selection
   - Closed captions
   - Progress tracking
   - Feedback buttons
   - Related content suggestions

**Video Viewer**:

```tsx
// ContentViewer.tsx
import { useQuery } from '@tanstack/react-query';
import { VideoPlayer } from '@/components/VideoPlayer';
import { ContentFeedback } from '@/components/ContentFeedback';
import { RelatedTopics } from '@/components/RelatedTopics';

export function ContentViewer({ cacheKey }: { cacheKey: string }) {
  const { data: content, isLoading } = useQuery(
    ['content', cacheKey],
    () => fetchContent(cacheKey),
    { refetchInterval: (data) => data?.status === 'generating' ? 5000 : false }
  );

  if (isLoading) {
    return <ContentLoadingSkeleton />;
  }

  if (content.status === 'generating') {
    return (
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-4">{content.title}</h1>

        {/* Fast Path: Show script + audio */}
        {content.audio_url && (
          <div className="mb-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm font-medium text-blue-900">
                🎧 Fast Path Available! Listen while the video generates.
              </p>
            </div>
            <AudioPlayer url={content.audio_url} />
            <ScriptDisplay script={content.script} />
          </div>
        )}

        {/* Video generation progress */}
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <h3 className="text-xl font-semibold mb-2">Creating Your Personalized Video</h3>
          <p className="text-gray-600">This usually takes 2-3 minutes...</p>
          <Progress value={content.progress_percentage} className="mt-4" />
        </div>
      </div>
    );
  }

  // Full Path: Show video
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4">{content.title}</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <VideoPlayer
            videoUrl={content.video_url}
            captionsUrl={content.captions_url}
            title={content.title}
            onProgress={(time) => saveProgress(cacheKey, time)}
            onComplete={() => markCompleted(cacheKey)}
          />
        </div>

        <div className="space-y-6">
          <ContentFeedback cacheKey={cacheKey} />
          <RelatedTopics topicId={content.topic_id} />
        </div>
      </div>
    </div>
  );
}
```

#### Milestone 4.2: Teacher Interface (Week 2)

**Deliverables**:

1. **Teacher Dashboard** (2 days)
   - Class overview
   - Student engagement metrics
   - Recent activity across classes
   - Alerts for struggling students
   - Quick actions (add student, create class)

2. **Class Management** (2 days)
   - Create/edit classes
   - Add/remove students
   - View class roster
   - Bulk operations
   - Class analytics

3. **Student Progress Monitoring** (3 days)
   - Individual student view
   - Topic completion matrix
   - Engagement timeline
   - Video watch time
   - Feedback history
   - Export progress reports (PDF/CSV)

**Teacher Dashboard**:

```tsx
// TeacherDashboard.tsx
export function TeacherDashboard() {
  const { data: classes } = useQuery(['teacher', 'classes'], fetchClasses);
  const { data: analytics } = useQuery(['teacher', 'analytics'], fetchAnalytics);

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Teacher Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-4 mb-8">
        <StatCard
          title="Total Students"
          value={analytics?.total_students}
          icon={Users}
        />
        <StatCard
          title="Active This Week"
          value={analytics?.active_this_week}
          trend={analytics?.active_trend}
          icon={TrendingUp}
        />
        <StatCard
          title="Videos Generated"
          value={analytics?.videos_generated}
          icon={Video}
        />
        <StatCard
          title="Avg. Completion Rate"
          value={`${analytics?.avg_completion_rate}%`}
          icon={CheckCircle}
        />
      </div>

      {/* Classes List */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {classes?.map((cls) => (
          <ClassCard key={cls.id} class={cls} />
        ))}
        <CreateClassCard />
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Recent Student Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityTimeline activities={analytics?.recent_activity} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

**Student Progress View**:

```tsx
// StudentProgressView.tsx
export function StudentProgressView({ studentId }: { studentId: string }) {
  const { data: student } = useQuery(['student', studentId], fetchStudent);
  const { data: progress } = useQuery(['student', studentId, 'progress'], fetchProgress);

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback>{student?.initials}</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-3xl font-bold">{student?.name}</h1>
            <p className="text-gray-600">{student?.grade_level}th Grade • {student?.email}</p>
          </div>
        </div>
        <Button onClick={() => exportProgressReport(studentId)}>
          <Download className="mr-2 h-4 w-4" />
          Export Report
        </Button>
      </div>

      {/* Progress Summary */}
      <div className="grid gap-6 md:grid-cols-3 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-2">
                {progress?.videos_watched}
              </div>
              <div className="text-sm text-gray-600">Videos Watched</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">
                {progress?.topics_completed}
              </div>
              <div className="text-sm text-gray-600">Topics Completed</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {progress?.avg_watch_time} min
              </div>
              <div className="text-sm text-gray-600">Avg. Watch Time</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Topic Completion Matrix */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Topic Mastery</CardTitle>
        </CardHeader>
        <CardContent>
          <TopicCompletionMatrix progress={progress?.topic_matrix} />
        </CardContent>
      </Card>

      {/* Activity Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Learning Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <ActivityCalendar activities={progress?.activity_history} />
        </CardContent>
      </Card>
    </div>
  );
}
```

#### Milestone 4.3: Admin Interface (Week 3)

**Deliverables**:

1. **Admin Dashboard** (2 days)
   - System-wide KPIs
   - User distribution charts
   - Content generation stats
   - Cache hit rate
   - Cost tracking
   - Alert notifications

2. **User Management** (2 days)
   - User list with search/filters
   - Create/edit/delete users
   - Bulk upload interface
   - Account request approval
   - Role management
   - Session management

3. **System Configuration** (3 days)
   - Feature flag management
   - Topic hierarchy editor
   - Canonical interest management
   - System settings
   - OER content management
   - Maintenance mode

**Admin Dashboard**:

```tsx
// AdminDashboard.tsx
export function AdminDashboard() {
  const { data: kpis } = useQuery(['admin', 'kpis'], fetchKPIs);
  const { data: alerts } = useQuery(['admin', 'alerts'], fetchAlerts);

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">System Dashboard</h1>

      {/* Alerts */}
      {alerts?.length > 0 && (
        <Alert className="mb-8" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>System Alerts</AlertTitle>
          <AlertDescription>
            {alerts.map(alert => <div key={alert.id}>{alert.message}</div>)}
          </AlertDescription>
        </Alert>
      )}

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <KPICard
          title="Total Users"
          value={kpis?.total_users}
          breakdown={{
            students: kpis?.total_students,
            teachers: kpis?.total_teachers,
            admins: kpis?.total_admins
          }}
        />
        <KPICard
          title="Active Users (7d)"
          value={kpis?.active_users_7d}
          trend={kpis?.active_users_trend}
        />
        <KPICard
          title="Cache Hit Rate"
          value={`${kpis?.cache_hit_rate}%`}
          target={15}
          status={kpis?.cache_hit_rate >= 15 ? 'success' : 'warning'}
        />
        <KPICard
          title="Monthly Cost"
          value={`$${kpis?.monthly_cost}`}
          budget={kpis?.monthly_budget}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Content Generation Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ContentGenerationChart data={kpis?.generation_trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Growth</CardTitle>
          </CardHeader>
          <CardContent>
            <UserGrowthChart data={kpis?.user_growth} />
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <Button onClick={() => navigate('/admin/users/bulk-upload')}>
              <Upload className="mr-2 h-4 w-4" />
              Bulk Upload Users
            </Button>
            <Button onClick={() => navigate('/admin/requests')}>
              <UserPlus className="mr-2 h-4 w-4" />
              Pending Requests ({kpis?.pending_requests})
            </Button>
            <Button onClick={() => navigate('/admin/feature-flags')}>
              <Flag className="mr-2 h-4 w-4" />
              Manage Feature Flags
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Phase 4 Success Criteria

- [ ] All user interfaces responsive (mobile, tablet, desktop)
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] Intuitive navigation and UX
- [ ] Fast page load times (<2s initial, <500ms subsequent)
- [ ] Real-time updates for content generation
- [ ] Error handling with user-friendly messages
- [ ] Consistent design across all pages
- [ ] Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- [ ] Comprehensive E2E tests with Playwright
- [ ] Storybook documentation for all components

### Dependencies

**Requires**:
- Phase 2 complete (Backend Services)
- Design system ready ✅
- Video player component ready ✅

**Blocks**:
- Phase 5 (Integration & Testing)

---

## Phase 5: Integration & Testing

### Status: 🔜 PENDING (0% Complete)

### Duration: 2 weeks

### Objective

Conduct comprehensive integration testing, end-to-end testing, and system validation to ensure all components work together seamlessly.

### Milestones

#### Milestone 5.1: Integration Testing (Week 1)

**Deliverables**:

1. **API Integration Tests** (3 days)
   - Auth flow tests
   - Content request flow
   - User management operations
   - Cache service integration
   - Pub/Sub message flow
   - Database transactions

2. **AI Pipeline Tests** (2 days)
   - NLU accuracy validation
   - RAG retrieval quality
   - Script generation validation
   - Audio/video generation
   - End-to-end pipeline timing

3. **Frontend-Backend Integration** (2 days)
   - API contract testing
   - Real-time update verification
   - Error handling scenarios
   - Loading state management
   - WebSocket/polling validation

**Test Structure**:

```python
# tests/integration/test_content_request_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_content_request_flow(
    client: AsyncClient,
    test_student_token: str,
    mock_vertex_ai,
    mock_nano_banana
):
    """Test complete content request flow from student input to video delivery."""

    # 1. Student requests content
    response = await client.post(
        "/api/v1/students/content/request",
        json={"query": "Explain Newton's 3rd Law using basketball"},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic_id"] == "topic_phys_mech_newton_3"
    assert data["cache_key"] is not None
    cache_key = data["cache_key"]

    # 2. Check cache (should be miss for new content)
    response = await client.get(f"/api/v1/content/{cache_key}")
    assert response.status_code == 200
    assert response.json()["status"] == "generating"

    # 3. Wait for Fast Path (script + audio)
    await wait_for_status(client, cache_key, "fast_path_ready", timeout=30)

    response = await client.get(f"/api/v1/content/{cache_key}")
    content = response.json()
    assert content["audio_url"] is not None
    assert content["script"] is not None

    # 4. Wait for Full Path (video)
    await wait_for_status(client, cache_key, "video_ready", timeout=300)

    response = await client.get(f"/api/v1/content/{cache_key}")
    content = response.json()
    assert content["video_url"] is not None

    # 5. Verify cache hit on second request
    response = await client.post(
        "/api/v1/students/content/request",
        json={"query": "Explain Newton's 3rd Law using basketball"},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )
    data = response.json()
    assert data["cache_key"] == cache_key  # Same cache key
    assert data["cache_hit"] is True
    assert data["video_url"] is not None  # Immediate video URL
```

#### Milestone 5.2: End-to-End Testing (Week 2)

**Deliverables**:

1. **Critical User Flows** (3 days)
   - Student registration → content request → video viewing → feedback
   - Teacher class creation → student monitoring → progress export
   - Admin bulk upload → account approval → KPI dashboard

2. **Performance Testing** (2 days)
   - Load testing (100 concurrent users)
   - Stress testing (find breaking point)
   - Spike testing (sudden traffic increase)
   - Endurance testing (24-hour sustained load)

3. **Security Testing** (2 days)
   - Authentication bypass attempts
   - RBAC validation
   - SQL injection prevention
   - XSS prevention
   - CSRF protection
   - Rate limiting validation
   - Secret exposure checks

**E2E Test with Playwright**:

```typescript
// tests/e2e/student-content-request.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Student Content Request Flow', () => {
  test('student can request, view, and complete a lesson', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'john.doe.11@student.hillsboro.edu');
    await page.fill('input[name="password"]', 'Student123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');

    // 2. Request content
    const query = "Explain Newton's Third Law using basketball";
    await page.fill('input[placeholder*="What do you want to learn"]', query);
    await page.click('button:has-text("Learn")');

    // 3. Should show generating state
    await expect(page.locator('text=Creating Your Personalized Video')).toBeVisible();

    // 4. Fast Path: Audio should appear within 10 seconds
    await expect(page.locator('text=Fast Path Available')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('audio')).toBeVisible();

    // 5. Can play audio
    await page.click('button[aria-label="Play"]');
    await page.waitForTimeout(3000); // Play for 3 seconds

    // 6. Full Path: Video should appear within 3 minutes
    await expect(page.locator('video')).toBeVisible({ timeout: 200000 });

    // 7. Can play video
    await page.click('video');
    await page.waitForTimeout(5000);

    // 8. Mark as complete
    await page.click('button:has-text("Mark as Complete")');

    // 9. Verify completion
    await page.goto('/dashboard');
    await expect(page.locator('text=Topics Mastered').locator('.. >> text=1')).toBeVisible();
  });
});
```

**Load Test with Locust**:

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class VividlyUser(HttpUser):
    wait_time = between(5, 15)

    def on_start(self):
        """Login before tasks."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "student@test.com",
            "password": "Test123!"
        })
        self.token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def view_dashboard(self):
        """View dashboard (common action)."""
        self.client.get("/api/v1/students/profile")
        self.client.get("/api/v1/students/progress")

    @task(1)
    def request_content(self):
        """Request new content (less frequent)."""
        self.client.post("/api/v1/students/content/request", json={
            "query": "Explain photosynthesis using cooking"
        })

    @task(2)
    def view_content(self):
        """View existing content."""
        self.client.get("/api/v1/content/recent")
```

### Phase 5 Success Criteria

- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Zero critical security vulnerabilities
- [ ] Load test: 100 concurrent users with <2s response time
- [ ] Stress test: System gracefully degrades under extreme load
- [ ] Cache hit rate >15% in testing
- [ ] Fast Path delivers in <10 seconds (95th percentile)
- [ ] Full Path delivers in <3 minutes (95th percentile)
- [ ] No memory leaks in 24-hour endurance test
- [ ] Test coverage >80% (backend) and >70% (frontend)

### Dependencies

**Requires**:
- Phase 3 complete (AI Pipeline)
- Phase 4 complete (Frontend)

**Blocks**:
- Phase 6 (Pilot Deployment)

---

## Phase 6: Pilot Deployment

### Status: 🔜 PENDING (0% Complete)

### Duration: 1 week

### Objective

Deploy the complete MVP to the development environment, conduct final validation, and prepare for the MNPS pilot launch.

### Milestones

#### Milestone 6.1: Dev Environment Deployment (Days 1-2)

**Deliverables**:

1. **Infrastructure Deployment** (1 day)
   - Run Terraform apply for dev environment
   - Verify all GCP resources created
   - Configure DNS and SSL certificates
   - Set up monitoring dashboards
   - Configure alerting

2. **Application Deployment** (1 day)
   - Build and push Docker images to Artifact Registry
   - Deploy Cloud Run services
   - Deploy Cloud Functions
   - Run database migrations
   - Seed initial data
   - Warm cache with popular content

**Deployment Checklist**:

```bash
# 1. Deploy infrastructure
cd terraform
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars

# 2. Build and push images
docker build -t gcr.io/vividly-dev-rich/api-gateway:latest -f Dockerfile.api-gateway .
docker push gcr.io/vividly-dev-rich/api-gateway:latest

# 3. Deploy Cloud Run services
gcloud run deploy api-gateway \
  --image gcr.io/vividly-dev-rich/api-gateway:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

# 4. Deploy Cloud Functions
gcloud functions deploy nlu-service \
  --gen2 \
  --runtime python311 \
  --trigger-http \
  --region us-central1

# 5. Run migrations
./scripts/connect_and_migrate.sh

# 6. Seed data
python backend/scripts/seed_database.py

# 7. Ingest OER content
python backend/scripts/oer_ingestion/run_pipeline.py

# 8. Verify deployment
curl https://api-dev.vividly.edu/health
curl https://api-dev.vividly.edu/api/v1/topics | jq
```

#### Milestone 6.2: Pilot Preparation (Days 3-5)

**Deliverables**:

1. **Content Pre-warming** (1 day)
   - Identify top 20 topics for Physics
   - Generate content for top 5 interests per topic
   - Warm CDN cache
   - Verify cache hit rate improvement

2. **MNPS Pilot Setup** (1 day)
   - Create Davidson County Metro Schools organization
   - Set up Hillsboro High School and Early College High School
   - Create admin accounts for school principals
   - Create teacher accounts for pilot teachers
   - Configure pilot-specific feature flags

3. **User Onboarding Materials** (1 day)
   - Student invitation email template
   - Teacher training guide
   - Admin quick start guide
   - Video tutorials
   - FAQ document
   - Support contact information

**Pre-warming Script**:

```python
# scripts/prewarm_cache.py
"""Pre-generate popular content combinations."""

import asyncio
from itertools import product

TOP_TOPICS = [
    "topic_phys_mech_newton_1",
    "topic_phys_mech_newton_2",
    "topic_phys_mech_newton_3",
    "topic_phys_energy_kinetic",
    "topic_phys_energy_potential",
    # ... 15 more
]

TOP_INTERESTS = [
    "int_basketball",
    "int_football",
    "int_soccer",
    "int_music",
    "int_gaming"
]

async def prewarm_content():
    """Generate content for all combinations."""
    combinations = list(product(TOP_TOPICS, TOP_INTERESTS))

    print(f"Pre-warming {len(combinations)} content pieces...")

    for topic_id, interest in combinations:
        try:
            # Trigger content generation
            response = await api_client.post("/internal/v1/content/generate", {
                "topic_id": topic_id,
                "interest": interest,
                "priority": "low"  # Background generation
            })
            print(f"✓ {topic_id} + {interest}")
        except Exception as e:
            print(f"✗ {topic_id} + {interest}: {e}")

    print("Pre-warming complete!")

if __name__ == "__main__":
    asyncio.run(prewarm_content())
```

#### Milestone 6.3: Pilot Launch (Days 6-7)

**Deliverables**:

1. **Smoke Testing** (1 day)
   - Test critical paths in production
   - Verify all integrations working
   - Check error rates and latency
   - Validate monitoring and alerts

2. **Pilot Go-Live** (1 day)
   - Send teacher invitations
   - Conduct teacher training session
   - Enable student registration
   - Monitor system health
   - Provide real-time support

**Smoke Test Suite**:

```bash
#!/bin/bash
# scripts/smoke_test.sh

API_BASE="https://api-dev.vividly.edu"

echo "🔍 Running smoke tests..."

# Health check
echo "✓ Health check"
curl -f $API_BASE/health || exit 1

# Auth flow
echo "✓ Authentication"
TOKEN=$(curl -s -X POST $API_BASE/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@vividly.edu","password":"Test123!"}' \
  | jq -r '.access_token')
[ -n "$TOKEN" ] || exit 1

# Topics API
echo "✓ Topics API"
curl -f -H "Authorization: Bearer $TOKEN" \
  $API_BASE/api/v1/topics?limit=10 || exit 1

# Content request
echo "✓ Content request"
CACHE_KEY=$(curl -s -X POST $API_BASE/api/v1/students/content/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain gravity"}' \
  | jq -r '.cache_key')
[ -n "$CACHE_KEY" ] || exit 1

echo "✅ All smoke tests passed!"
```

### Phase 6 Success Criteria

- [ ] All services deployed and healthy
- [ ] Database migrations completed
- [ ] OER content ingested
- [ ] Cache pre-warmed (>100 videos)
- [ ] MNPS pilot accounts created
- [ ] Smoke tests passing
- [ ] Monitoring dashboards operational
- [ ] Alerts configured and tested
- [ ] Teacher training completed
- [ ] Documentation accessible
- [ ] Support channel active

### Dependencies

**Requires**:
- Phase 5 complete (Integration & Testing)
- GCP billing account active
- Domain name configured
- SSL certificates provisioned
- MNPS stakeholder approval

**Blocks**:
- Phase 7 (Production Hardening)

---

## Phase 7: Production Hardening

### Status: 🔜 PENDING (0% Complete)

### Duration: 2 weeks

### Objective

Harden the system based on pilot feedback, optimize performance, enhance security, and prepare for production scale.

### Milestones

#### Milestone 7.1: Performance Optimization (Week 1)

**Deliverables**:

1. **API Performance** (2 days)
   - Identify slow endpoints
   - Add database indexes
   - Optimize N+1 queries
   - Implement connection pooling
   - Add Redis caching for hot data
   - Target: All APIs <500ms (p95)

2. **Frontend Performance** (2 days)
   - Code splitting and lazy loading
   - Image optimization
   - Asset compression
   - CDN configuration
   - Bundle size optimization
   - Target: Lighthouse score >90

3. **AI Pipeline Optimization** (3 days)
   - Prompt optimization (reduce tokens)
   - Batch processing where possible
   - Parallel execution optimization
   - Timeout tuning
   - Cost optimization
   - Target: 15% cost reduction

**Database Optimization**:

```sql
-- Add indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_active ON users(role, is_active);
CREATE INDEX idx_content_topic_interest ON generated_content(topic_id, interest);
CREATE INDEX idx_progress_student_topic ON student_progress(student_id, topic_id);
CREATE INDEX idx_sessions_user_expiry ON user_sessions(user_id, expires_at);

-- Optimize frequently accessed views
CREATE MATERIALIZED VIEW student_engagement_summary AS
SELECT
    student_id,
    COUNT(DISTINCT topic_id) as topics_completed,
    SUM(watch_duration_seconds) as total_watch_time,
    MAX(last_accessed_at) as last_active
FROM student_progress
GROUP BY student_id;

CREATE INDEX idx_engagement_summary_student ON student_engagement_summary(student_id);

-- Refresh materialized view every hour
REFRESH MATERIALIZED VIEW CONCURRENTLY student_engagement_summary;
```

#### Milestone 7.2: Security Hardening (Week 2)

**Deliverables**:

1. **Security Audit** (2 days)
   - Penetration testing
   - Dependency vulnerability scan
   - Secret rotation
   - Access review
   - Compliance verification (FERPA, COPPA)

2. **Reliability Improvements** (2 days)
   - Enhanced error handling
   - Graceful degradation
   - Circuit breaker tuning
   - Retry logic optimization
   - Dead letter queue monitoring

3. **Disaster Recovery** (3 days)
   - Backup verification
   - Recovery procedure testing
   - Failover testing
   - Data retention policies
   - Incident response playbook

**Security Checklist**:

```markdown
## Security Hardening Checklist

### Authentication & Authorization
- [x] JWT tokens have short expiration (24h)
- [x] Refresh tokens rotated on use
- [x] Passwords hashed with bcrypt (cost 12)
- [x] Rate limiting on auth endpoints
- [x] Session revocation on password change
- [x] RBAC enforced on all endpoints
- [ ] MFA support (future)

### API Security
- [x] All endpoints use HTTPS
- [x] CORS properly configured
- [x] Input validation with Pydantic
- [x] SQL injection prevention (ORM)
- [x] XSS prevention (React auto-escaping)
- [ ] CSRF tokens (future if using cookies)
- [x] Rate limiting per user and IP
- [x] Request size limits

### Data Security
- [x] Encryption in transit (TLS 1.3)
- [x] Encryption at rest (Google-managed keys)
- [ ] Field-level encryption for PII (future)
- [x] Secrets in Secret Manager
- [x] No secrets in code or logs
- [x] Database access restricted to VPC
- [x] GCS buckets not publicly accessible

### Infrastructure Security
- [x] Private Cloud SQL instance
- [x] VPC network isolation
- [x] Least privilege IAM
- [x] Service accounts per service
- [ ] Cloud Armor (WAF) enabled
- [x] DDoS protection
- [ ] Intrusion detection (future)

### Compliance
- [ ] FERPA compliance verified
- [ ] COPPA compliance verified
- [x] Data minimization practiced
- [x] Audit logging enabled
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Cookie consent (if applicable)
- [ ] Data retention policies
- [ ] Data deletion procedures
```

**Disaster Recovery Playbook**:

```markdown
## Incident Response Playbook

### 1. Database Failure
**Detection**: Cloud SQL health check fails
**Impact**: Complete service outage
**Recovery Time Objective (RTO)**: 4 hours
**Recovery Point Objective (RPO)**: 24 hours

**Procedure**:
1. Check Cloud SQL status in console
2. If instance is down, attempt restart
3. If restart fails, restore from latest backup
4. Verify data integrity
5. Update DNS if new instance IP
6. Run smoke tests
7. Monitor for 1 hour

**Restoration Commands**:
```bash
# Restore from backup
gcloud sql backups restore <backup-id> \
  --backup-instance=dev-vividly-db \
  --backup-instance-project=vividly-dev-rich

# Verify restoration
psql -h <new-ip> -U vividly -d vividly -c "SELECT COUNT(*) FROM users;"
```

### 2. GCS Bucket Deletion
**Detection**: 404 errors on video URLs
**Impact**: Partial service degradation (new content works, old content 404)
**RTO**: 48 hours (for most-viewed content)
**RPO**: Content is reproducible

**Procedure**:
1. Restore bucket from version backup (if enabled)
2. If not, regenerate content from database records
3. Prioritize by view count (most-viewed first)
4. Use content generation pipeline to regenerate
5. Monitor regeneration progress

### 3. API Service Outage
**Detection**: Health check failures, increased error rate
**Impact**: Service unavailable
**RTO**: 15 minutes
**RPO**: 0 (stateless services)

**Procedure**:
1. Check Cloud Run service health
2. Review recent deployments (rollback if needed)
3. Check logs for error patterns
4. Scale up instances if resource exhaustion
5. If persistent, deploy previous known-good version
6. Investigate root cause offline
```

### Phase 7 Success Criteria

- [ ] All APIs <500ms response time (p95)
- [ ] Frontend Lighthouse score >90
- [ ] AI pipeline cost reduced by 15%
- [ ] Zero critical security vulnerabilities
- [ ] Disaster recovery tested successfully
- [ ] Database backups verified
- [ ] Incident response playbook complete
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Production deployment checklist complete

### Dependencies

**Requires**:
- Phase 6 complete (Pilot Deployment)
- Pilot running for at least 1 week
- Initial feedback collected

**Blocks**:
- Production launch
- Scaling to additional schools

---

## Technical Dependencies

### External Services

| Service | Purpose | Provider | Status |
|---------|---------|----------|--------|
| Vertex AI (Gemini) | NLU, Script Generation | Google Cloud | ✅ Available |
| Vertex AI (LearnLM) | Educational Content | Google Cloud | ⚠️ Requires Access |
| Vertex AI Vector Search | RAG Retrieval | Google Cloud | ✅ Available |
| Cloud Text-to-Speech | Audio Generation | Google Cloud | ✅ Available |
| Nano Banana | Video Generation | Third-party | ⚠️ API Key Needed |
| SendGrid | Email Delivery | Twilio | ⚠️ Account Setup |
| Sentry | Error Tracking | Sentry.io | ⚠️ DSN Needed |

### GCP Services

| Service | Purpose | Terraform Status |
|---------|---------|------------------|
| Cloud Run | Backend Services | ✅ Configured |
| Cloud Functions | Workers | ✅ Configured |
| Cloud SQL | PostgreSQL Database | ✅ Configured |
| Cloud Storage | Video/Audio Storage | ✅ Configured |
| Cloud Memorystore | Redis Cache | ✅ Configured |
| Cloud Pub/Sub | Message Queue | ✅ Configured |
| Cloud Load Balancer | HTTPS Ingress | ✅ Configured |
| Cloud CDN | Video Delivery | ✅ Configured |
| Secret Manager | Credentials | ✅ Configured |
| Cloud Monitoring | Observability | ✅ Configured |

### API Keys & Credentials Needed

```bash
# Required before Phase 3
VERTEX_AI_PROJECT_ID=vividly-dev-rich
VERTEX_AI_LOCATION=us-central1

# Required before Phase 3
NANO_BANANA_API_KEY=<pending>
NANO_BANANA_API_URL=https://api.nanobanana.com

# Required before Phase 2 (notifications)
SENDGRID_API_KEY=<pending>
SENDGRID_FROM_EMAIL=noreply@vividly.edu

# Required before Phase 2 (error tracking)
SENTRY_DSN=<pending>

# Required before Phase 6 (custom domain)
DOMAIN_NAME=vividly.edu
SSL_CERTIFICATE=<auto-provisioned>
```

### Development Tools

| Tool | Purpose | Status |
|------|---------|--------|
| Docker | Local development | ✅ Installed |
| Docker Compose | Service orchestration | ✅ Configured |
| Terraform | Infrastructure | ✅ Configured |
| Poetry | Python dependencies | ⚠️ Needs setup |
| npm/pnpm | Node.js dependencies | ✅ Installed |
| pytest | Backend testing | ✅ Configured |
| Playwright | E2E testing | ⚠️ Needs setup |
| Locust | Load testing | ⚠️ Needs setup |

---

## Resource Requirements

### Team Composition

**Recommended Team** (for 12-week timeline):

| Role | Count | Responsibilities | Time Allocation |
|------|-------|------------------|-----------------|
| **Full-Stack Engineer** | 2 | Backend services, API development, frontend features | 100% (12 weeks) |
| **AI/ML Engineer** | 1 | NLU, RAG, script generation, prompt engineering | 100% (8 weeks, Phase 3) |
| **Frontend Engineer** | 1 | React components, UX, responsive design | 100% (8 weeks, Phase 4) |
| **DevOps Engineer** | 0.5 | CI/CD, monitoring, deployment | 50% (ongoing) |
| **QA Engineer** | 1 | Testing, quality assurance, automation | 75% (Phases 5-7) |
| **Product Manager** | 0.25 | Requirements, prioritization, stakeholder mgmt | 25% (ongoing) |
| **UI/UX Designer** | 0.25 | Design refinement, user research | 25% (Phases 4-5) |

**Minimum Viable Team** (for 18-week timeline):

| Role | Count | Time Allocation |
|------|-------|-----------------|
| **Full-Stack Engineer** | 1-2 | 100% |
| **Product Manager** | 0.25 | 25% |

### Infrastructure Costs (Projected)

**Development Environment** (Monthly):

| Resource | Quantity | Unit Cost | Total |
|----------|----------|-----------|-------|
| Cloud Run (API services) | 4 services | ~$5/service | $20 |
| Cloud Functions (workers) | 4 functions | ~$3/function | $12 |
| Cloud SQL (db-f1-micro) | 1 instance | $7 | $7 |
| Cloud Memorystore (1GB) | 1 instance | $35 | $35 |
| Cloud Storage (100 GB) | ~100 GB | $0.02/GB | $2 |
| Cloud Load Balancer | 1 | $18 | $18 |
| Cloud CDN | ~500 GB | $0.08/GB | $40 |
| Vertex AI (embeddings) | ~10K calls | $0.0001/call | $1 |
| Vertex AI (Gemini) | ~1K calls | $0.001/call | $1 |
| Cloud TTS | ~500 calls | $0.006/call | $3 |
| Pub/Sub | ~100K msgs | $0.0001/msg | $10 |
| **Total Dev** | | | **~$150/mo** |

**Pilot Environment** (Monthly, 3,000 students):

| Resource | Quantity | Unit Cost | Total |
|----------|----------|-----------|-------|
| Cloud Run (auto-scale) | 4 services | ~$50/service | $200 |
| Cloud Functions | 4 functions | ~$30/function | $120 |
| Cloud SQL (db-custom-2-8GB) | 1 instance | $110 | $110 |
| Cloud Memorystore (5GB) | 1 instance | $175 | $175 |
| Cloud Storage (2 TB) | 2000 GB | $0.02/GB | $40 |
| Cloud CDN (20 TB) | 20,000 GB | $0.04/GB | $800 |
| Vertex AI (embeddings) | ~50K calls | $0.0001/call | $5 |
| Vertex AI (Gemini - NLU) | ~30K calls | $0.001/call | $30 |
| Vertex AI (LearnLM - scripts) | ~3K calls | $0.01/call | $30 |
| Cloud TTS | ~3K calls | $0.006/call | $18 |
| Nano Banana (videos) | ~3K videos | $0.10/video | $300 |
| Pub/Sub | ~500K msgs | $0.0001/msg | $50 |
| **Total Pilot** | | | **~$1,900/mo** |

**Assumptions**:
- 3,000 active students
- 10% active weekly (300 students)
- 3 videos per student per month (900 videos/month)
- 15% cache hit rate (2,550 cache misses, 765 cache hits)
- 20 GB video per month consumption (CDN)
- 80% cost attributed to video generation (Nano Banana)

**Cost Optimization Strategies**:
1. Increase cache hit rate to 40% → Save $700/mo on Nano Banana
2. Pre-warm popular content → Reduce generation load
3. Lower video quality to 720p → Save 30% on storage/bandwidth
4. Batch audio generation → Reduce TTS costs by 20%
5. Optimize prompts → Reduce Gemini token usage by 30%

### Timeline by Phase

```mermaid
gantt
    title Vividly MVP Development Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    Foundation & Infrastructure           :done, p1, 2025-10-01, 4w
    section Phase 2
    Core Backend Services                 :active, p2, 2025-10-29, 3w
    section Phase 3
    AI Content Pipeline                   :p3, after p2, 3w
    section Phase 4
    Frontend Application                  :p4, after p2, 3w
    section Phase 5
    Integration & Testing                 :p5, after p3 p4, 2w
    section Phase 6
    Pilot Deployment                      :p6, after p5, 1w
    section Phase 7
    Production Hardening                  :p7, after p6, 2w
```

**Key Milestones**:

| Date | Milestone | Description |
|------|-----------|-------------|
| ✅ Oct 28, 2025 | Phase 1 Complete | Infrastructure ready |
| Nov 18, 2025 | Phase 2 Complete | Backend APIs functional |
| Dec 9, 2025 | Phase 3 Complete | AI pipeline operational |
| Dec 9, 2025 | Phase 4 Complete | Frontend complete |
| Dec 23, 2025 | Phase 5 Complete | Testing done |
| Dec 30, 2025 | Phase 6 Complete | Pilot deployed |
| Jan 13, 2026 | Phase 7 Complete | Production ready |
| Jan 20, 2026 | **MVP LAUNCH** | MNPS pilot goes live |

**Total Duration**: ~12 weeks from now (October 28, 2025 → January 20, 2026)

---

## Risk Assessment & Mitigation

### High-Priority Risks

#### 1. AI Model Performance Risk
**Risk**: LearnLM or Gemini does not generate educationally accurate or engaging content.

**Impact**: High (core product value)
**Likelihood**: Medium
**Mitigation**:
- Extensive prompt engineering and testing (Phase 3)
- Human review of initial scripts (Phase 6)
- Feedback loop for continuous improvement
- RAG ensures content grounded in OER textbooks
- Fallback to pre-written templates if quality is poor

#### 2. Video Generation Latency Risk
**Risk**: Nano Banana API takes >5 minutes per video, creating poor UX.

**Impact**: High (user experience)
**Likelihood**: Medium
**Mitigation**:
- Fast Path (script + audio) provides immediate value
- Set clear expectations (2-3 minutes for video)
- Pre-warm cache for popular topics
- Evaluate alternative video generation providers (Synthesia, Rephrase.ai)
- Circuit breaker prevents cascading failures

#### 3. Cost Overrun Risk
**Risk**: Video generation costs exceed budget, especially if cache hit rate is low.

**Impact**: High (financial sustainability)
**Likelihood**: Medium
**Mitigation**:
- Target 15% cache hit rate in MVP, 40% in production
- Pre-warm top 100 topic+interest combinations
- Implement cost monitoring and alerts
- Rate limit content generation per student (10/hour)
- Consider lower video quality (720p) to reduce costs

#### 4. FERPA/COPPA Compliance Risk
**Risk**: Inadvertent violations of student data privacy laws.

**Impact**: Critical (legal/regulatory)
**Likelihood**: Low (with proper implementation)
**Mitigation**:
- Legal review of Data Privacy Policy
- Data minimization (collect only necessary PII)
- Secure data handling (encryption, access controls)
- Audit logging of all data access
- School-based consent (COPPA exemption)
- Annual compliance review

#### 5. Scalability Risk
**Risk**: System cannot handle 3,000 concurrent students during peak usage.

**Impact**: High (service availability)
**Likelihood**: Low (with proper testing)
**Mitigation**:
- Load testing in Phase 5 (100+ concurrent users)
- Serverless auto-scaling (Cloud Run, Cloud Functions)
- Redis caching for hot data
- CDN for video delivery
- Circuit breakers for external APIs
- Graceful degradation under load

#### 6. Dependency Risk
**Risk**: Nano Banana or other third-party API becomes unavailable or changes pricing.

**Impact**: High (service continuity)
**Likelihood**: Medium
**Mitigation**:
- Circuit breaker prevents cascading failures
- Dead letter queues for retry
- Evaluate backup video providers
- Consider in-house video generation (Remotion, Manim) for future
- Contract with SLA guarantees

### Medium-Priority Risks

#### 7. Pilot Adoption Risk
**Risk**: Teachers or students do not engage with the platform.

**Impact**: Medium (pilot success)
**Likelihood**: Medium
**Mitigation**:
- Extensive teacher training before launch
- Simple, intuitive UX
- Quick wins (Fast Path in <10s)
- Regular feedback collection
- Dedicated support during pilot
- Gamification (badges, streaks) to drive engagement

#### 8. Content Quality Risk
**Risk**: Generated content is inaccurate or inappropriate.

**Impact**: High (trust, safety)
**Likelihood**: Low (with guardrails)
**Mitigation**:
- AI safety guardrails (Phase 3)
- RAG grounds content in OER textbooks
- Canonical interest list prevents inappropriate personalization
- Profanity and bias filtering
- Human review of initial content
- Student feedback mechanism ("Report Issue" button)

#### 9. Infrastructure Risk
**Risk**: GCP service outage or configuration issue causes downtime.

**Impact**: Medium (service availability)
**Likelihood**: Low (with GCP SLAs)
**Mitigation**:
- Multi-zone deployment (Phase 7)
- Automated backups (Cloud SQL)
- Infrastructure as Code (Terraform) for quick rebuild
- Disaster recovery playbook (Phase 7)
- Monitoring and alerting
- Status page for transparency

---

## Success Metrics

### MVP Success Criteria

#### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| System Uptime | >99.5% | Cloud Monitoring |
| API Response Time (p95) | <500ms | Cloud Monitoring |
| Fast Path Delivery | <10s (p95) | Custom tracking |
| Full Path Delivery | <3 min (p95) | Custom tracking |
| Cache Hit Rate | >15% | Redis stats |
| Error Rate | <1% | Sentry, Cloud Logging |
| Page Load Time | <2s initial, <500ms subsequent | Lighthouse |
| Test Coverage | >80% backend, >70% frontend | pytest, Jest |

#### Business Metrics (Pilot Phase)

| Metric | Target | Measurement | Aligned with PRD |
|--------|--------|-------------|------------------|
| Teacher Adoption Rate | 50% | Teachers using platform / Total teachers | ✅ PRD Target |
| Student Activation Rate | 30% | Students with ≥1 video / Total students | ✅ PRD Target |
| Student Engagement | 3 videos/student/month | Avg videos generated per active student | ✅ PRD Target |
| Cache Hit Rate | 15% | Cache hits / Total requests | ✅ PRD Target |
| Content Quality Score | >4.0/5.0 | Student feedback ratings | New metric |
| Support Ticket Rate | <10% | Students with support tickets / Total | New metric |

#### User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Video | <10 min | From registration to first video view |
| Content Completion Rate | >70% | Videos watched to end / Total started |
| Repeat Usage Rate | >40% | Students with 2+ videos in first week |
| NPS Score | >50 | Net Promoter Score survey |
| System Usability Scale (SUS) | >70 | SUS survey (teachers and students) |

### Key Performance Indicators (KPIs)

**Week 1 of Pilot**:
- 100% of pilot teachers trained
- 50% of students activated accounts
- 20% of students requested first video
- <5% error rate
- >95% uptime

**Week 4 of Pilot**:
- 40% teacher adoption
- 25% student activation
- 2 videos per active student
- 10% cache hit rate
- >99% uptime

**Week 8 of Pilot (End of MVP)**:
- 50% teacher adoption ✅
- 30% student activation ✅
- 3 videos per active student ✅
- 15% cache hit rate ✅
- >99.5% uptime

### Monitoring Dashboard

**Key Metrics to Display**:

```markdown
## Vividly Operations Dashboard

### System Health
- Uptime: 99.8%
- API Response Time (p95): 320ms
- Error Rate: 0.3%
- Active Alerts: 0

### Content Generation
- Fast Path Delivery (p95): 8.2s ✅
- Full Path Delivery (p95): 2m 45s ✅
- Cache Hit Rate: 18% ✅
- Videos Generated Today: 42
- Queue Depth: 3

### User Engagement
- Active Students (7d): 287 / 960 (30%) ✅
- Active Teachers (7d): 12 / 24 (50%) ✅
- Videos Watched Today: 68
- Avg. Completion Rate: 73% ✅

### Infrastructure
- Cloud Run Instances: 3 / 10
- Cloud Functions Executions: 1,240 today
- Cloud SQL Connections: 18 / 100
- Redis Memory Usage: 28%
- GCS Storage: 1.2 TB / 2 TB

### Costs
- MTD Spend: $1,347 / $1,900 budget
- Projected Monthly: $1,820
- Largest Cost: Nano Banana ($812)
- Cache Savings: $340 this month
```

---

## Timeline & Milestones

### Detailed Timeline (18 weeks total)

#### Weeks 1-4: Phase 1 - Foundation & Infrastructure ✅ COMPLETE
- Infrastructure as Code (Terraform)
- Database schema and migrations
- Authentication and security
- Development environment
- Design system and components
- Monitoring and observability

#### Weeks 5-7: Phase 2 - Core Backend Services ⏳ READY TO START
- **Week 5**: Authentication API, Student Service, Teacher Service
- **Week 6**: Admin Service, Topics/Interests API, Content Metadata API
- **Week 7**: Cache Service, Content Delivery Service, Notification Service

**Deliverables**:
- All REST API endpoints implemented
- Comprehensive API documentation
- Unit tests (>80% coverage)
- Postman collection

**Go/No-Go Criteria**:
- [ ] All endpoints returning expected responses
- [ ] Authentication flow working end-to-end
- [ ] Bulk upload processing 1000 users <30s
- [ ] All integration tests passing

#### Weeks 8-10: Phase 3 - AI Content Pipeline
- **Week 8**: NLU Service, Topic Extraction, Clarification Flow
- **Week 9**: RAG Integration, Script Generation Worker, LearnLM Prompts
- **Week 10**: Audio Worker, Video Worker, Pipeline Orchestration

**Deliverables**:
- NLU service with >90% accuracy
- Script generation with RAG
- Audio and video workers
- End-to-end pipeline functional

**Go/No-Go Criteria**:
- [ ] NLU correctly identifies topics >90% of time
- [ ] RAG retrieves relevant content (precision >80%)
- [ ] Scripts are educationally accurate
- [ ] Fast Path delivers in <10s
- [ ] Full Path delivers in <3 min
- [ ] Circuit breaker prevents failures

#### Weeks 8-10: Phase 4 - Frontend Application (Parallel with Phase 3)
- **Week 8**: Student Authentication UI, Dashboard, Content Request
- **Week 9**: Teacher Dashboard, Class Management, Student Monitoring
- **Week 10**: Admin Dashboard, User Management, System Configuration

**Deliverables**:
- Complete student interface
- Complete teacher interface
- Complete admin interface
- Responsive design (mobile, tablet, desktop)

**Go/No-Go Criteria**:
- [ ] All user flows functional
- [ ] Responsive on all device sizes
- [ ] WCAG 2.1 AA compliant
- [ ] Lighthouse score >90
- [ ] Cross-browser compatible

#### Weeks 11-12: Phase 5 - Integration & Testing
- **Week 11**: Integration Testing, API Contract Tests, Frontend-Backend Integration
- **Week 12**: E2E Testing, Performance Testing, Security Testing

**Deliverables**:
- All integration tests passing
- All E2E tests passing (Playwright)
- Load test results
- Security audit report

**Go/No-Go Criteria**:
- [ ] All tests passing
- [ ] Load test: 100 users with <2s response
- [ ] Zero critical vulnerabilities
- [ ] Cache hit rate >15%
- [ ] No memory leaks

#### Week 13: Phase 6 - Pilot Deployment
- **Days 1-2**: Deploy to dev environment, verify infrastructure
- **Days 3-5**: Pre-warm content, set up MNPS pilot, create onboarding materials
- **Days 6-7**: Smoke testing, pilot go-live

**Deliverables**:
- Complete deployment to dev
- MNPS pilot configured
- Teacher training completed
- System operational

**Go/No-Go Criteria**:
- [ ] All services deployed and healthy
- [ ] OER content ingested
- [ ] Cache pre-warmed (>100 videos)
- [ ] Smoke tests passing
- [ ] Teachers trained

#### Weeks 14-15: Phase 7 - Production Hardening
- **Week 14**: Performance optimization, API/frontend/AI pipeline tuning
- **Week 15**: Security hardening, disaster recovery, incident response playbook

**Deliverables**:
- Performance benchmarks met
- Security audit passed
- Disaster recovery tested
- Production deployment checklist

**Go/No-Go Criteria**:
- [ ] APIs <500ms (p95)
- [ ] Lighthouse >90
- [ ] Zero critical vulnerabilities
- [ ] Disaster recovery tested

#### Week 16+: Pilot Operation & Iteration
- Monitor pilot performance
- Collect user feedback
- Iterate based on learnings
- Prepare for production scale

---

## Appendix

### A. Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Product Requirements | `/PRD.md` | Business requirements, goals |
| Architecture | `/ARCHITECTURE.md` | System design, components |
| API Specification | `/API_SPECIFICATION.md` | REST API contracts |
| Database Schema | `/DATABASE_SCHEMA.md` | PostgreSQL tables |
| Feature Specifications | `/FEATURE_SPECIFICATIONS.md` | Detailed feature specs |
| User Flows | `/USER_FLOWS.md` | User journey maps |
| Testing Strategy | `/TESTING_STRATEGY.md` | Test plans, coverage |
| Security | `/SECURITY.md` | Security measures |
| Deployment | `/DEPLOYMENT.md` | Deployment procedures |
| MVP Status | `/MVP_COMPLETION_STATUS.md` | Current progress |

### B. Development Commands

```bash
# Local Development
docker-compose up                           # Start all services
docker-compose logs -f api-gateway          # View API logs
docker-compose down                         # Stop all services

# Database
psql -h localhost -U vividly -d vividly     # Connect to DB
alembic upgrade head                        # Run migrations
python backend/scripts/seed_database.py     # Seed test data

# Backend Testing
cd backend
pytest                                      # Run all tests
pytest tests/unit -v                        # Unit tests only
pytest --cov=app --cov-report=html          # Coverage report

# Frontend Development
cd frontend
npm run dev                                 # Start dev server
npm run build                               # Production build
npm run test                                # Run tests
npm run lint                                # Lint code

# Infrastructure
cd terraform
terraform init                              # Initialize Terraform
terraform plan -var-file=environments/dev.tfvars  # Plan changes
terraform apply -var-file=environments/dev.tfvars # Apply changes

# Deployment
./scripts/deploy.sh dev                     # Deploy to dev
./scripts/run_migrations_cloudshell.sh      # Run migrations
./scripts/smoke_test.sh                     # Smoke tests
```

### C. Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://vividly:password@localhost:5432/vividly
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
SENTRY_DSN=https://...@sentry.io/...
SENDGRID_API_KEY=SG.xxx
VERTEX_AI_PROJECT_ID=vividly-dev-rich
VERTEX_AI_LOCATION=us-central1
NANO_BANANA_API_KEY=nb_xxx

# Frontend (.env)
VITE_API_BASE_URL=http://localhost:8080
VITE_ENVIRONMENT=development
VITE_SENTRY_DSN=https://...@sentry.io/...
```

### D. Useful Links

- **GCP Console**: https://console.cloud.google.com/
- **Project**: vividly-dev-rich
- **GitHub Repo**: (to be created)
- **Figma Designs**: (if applicable)
- **Sentry**: (to be configured)
- **Status Page**: (to be created)
- **Documentation**: (this repository)

---

## Conclusion

This comprehensive development plan provides a detailed roadmap for building the Vividly MVP from its current state (Phase 1 complete) to a production-ready pilot deployment for Metro Nashville Public Schools.

**Key Highlights**:

- **Current Status**: 15% complete (Phase 1 done, infrastructure ready)
- **Timeline**: 12 weeks to MVP launch (October 28, 2025 → January 20, 2026)
- **Budget**: ~$150/mo dev, ~$1,900/mo pilot
- **Team**: 2 full-stack engineers minimum, 5-7 people ideal
- **Risk**: Manageable with proper mitigation strategies

**Immediate Next Steps**:

1. ✅ Complete database migrations (tonight via Cloud Shell)
2. ⏳ Run OER ingestion pipeline (after migrations)
3. ⏳ Begin Phase 2: Core Backend Services (Week 5, ready to start)

**Success Factors**:

- Strong technical foundation (Phase 1 complete)
- Clear requirements and architecture
- Comprehensive testing strategy
- Iterative development with feedback loops
- Focus on MVP scope (no feature creep)

With this plan, Vividly is well-positioned to deliver a high-quality MVP that validates the core value proposition and sets the stage for future growth.

---

**Document Control**:
- **Author**: Application Architect
- **Date**: October 28, 2025
- **Version**: 1.0
- **Status**: Active Development Plan
- **Next Review**: After Phase 2 completion (Week 7)
