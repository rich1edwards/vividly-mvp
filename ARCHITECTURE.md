# Vividly System Architecture

**Version:** 1.0
**Last Updated:** October 27, 2025
**Status:** MVP Specification

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [High-Level Architecture](#high-level-architecture)
4. [Component Descriptions](#component-descriptions)
5. [Data Flow](#data-flow)
6. [Technology Stack](#technology-stack)
7. [Infrastructure Topology](#infrastructure-topology)
8. [Security Architecture](#security-architecture)
9. [Scalability Considerations](#scalability-considerations)

## Overview

Vividly is a serverless, event-driven platform built on Google Cloud Platform (GCP) designed to generate personalized STEM learning content using AI. The architecture prioritizes:

- **Cost efficiency** through intelligent caching and serverless compute
- **Compliance** with FERPA/COPPA requirements
- **Scalability** to support pilot growth
- **Performance** with fast path (Vivid Now) and full path (Vivid Learning) delivery

## Architecture Principles

### 1. Serverless First
- Cloud Run for stateless HTTP services
- Cloud Functions for event-driven workers
- Managed services (Cloud SQL, Pub/Sub, GCS) over self-managed infrastructure

### 2. Event-Driven Processing
- Asynchronous job processing via Pub/Sub
- Decoupled services communicating through message queues
- Cloud Tasks for reliable task scheduling

### 3. Cache-First Design
- Check cache before expensive AI generation
- Shared cache across all customers keyed by (topic_id, interest, style)
- GCS for persistent asset storage

### 4. Data Privacy by Design
- Minimal PII collection
- Separation of identifiable data (Cloud SQL) from generated content (GCS)
- Encryption at rest and in transit
- Audit logging for all data access

### 5. Fail-Safe Operation
- Graceful degradation when external APIs fail
- Fallback interests when preferred unavailable
- Dead letter queues for failed jobs
- Circuit breakers for external service calls

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Web App    │    │   Mobile     │    │    Admin     │              │
│  │   (React)    │    │  (Future)    │    │   Portal     │              │
│  │              │    │              │    │   (React)    │              │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘              │
│         │                                         │                      │
└─────────┼─────────────────────────────────────────┼──────────────────────┘
          │                                         │
          │                   HTTPS                 │
          │                                         │
┌─────────┼─────────────────────────────────────────┼──────────────────────┐
│         │              APPLICATION LAYER          │                      │
├─────────┼─────────────────────────────────────────┼──────────────────────┤
│         │                                         │                      │
│         ▼                                         ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │          Cloud Load Balancer (Global HTTPS LB)              │        │
│  └─────────────────────────────────────────────────────────────┘        │
│         │                                         │                      │
│         ▼                                         ▼                      │
│  ┌──────────────────┐                    ┌───────────────────┐          │
│  │   API Gateway    │                    │  Admin Service    │          │
│  │  (Cloud Run)     │◄───────────────────┤  (Cloud Run)      │          │
│  │                  │                    │                   │          │
│  │ - Authentication │                    │ - User Mgmt       │          │
│  │ - Rate Limiting  │                    │ - KPI Dashboard   │          │
│  │ - Request Router │                    │ - Bulk Upload     │          │
│  └────────┬─────────┘                    └───────────────────┘          │
│           │                                                              │
└───────────┼──────────────────────────────────────────────────────────────┘
            │
            ├─────────────────────────────────────────────────────┐
            │                                                     │
┌───────────▼───────────┐                           ┌─────────────▼────────┐
│   Student Service     │                           │   Teacher Service    │
│   (Cloud Run)         │                           │   (Cloud Run)        │
│                       │                           │                      │
│ - Content Request     │                           │ - Class Management   │
│ - Profile Management  │                           │ - Progress Tracking  │
│ - Feedback Handling   │                           │ - Account Requests   │
└───────────┬───────────┘                           └──────────────────────┘
            │
            │
┌───────────▼──────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐           │
│  │  NLU Service │      │    Cache     │      │   Content    │           │
│  │ (Cloud Func) │      │   Service    │      │   Delivery   │           │
│  │              │      │ (Cloud Run)  │      │ (Cloud Run)  │           │
│  │ - Topic ID   │      │              │      │              │           │
│  │ - Clarify    │      │ - Check GCS  │      │ - Serve URL  │           │
│  └──────────────┘      └──────────────┘      └──────────────┘           │
│                                                                           │
│                     Cloud Pub/Sub Topics                                 │
│  ┌────────────────────────────────────────────────────────────┐          │
│  │  generate-script  │  generate-audio  │  generate-video     │          │
│  └────────────────────────────────────────────────────────────┘          │
│           │                    │                    │                    │
│           ▼                    ▼                    ▼                    │
│  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐             │
│  │   Script     │     │    Audio     │    │    Video     │             │
│  │   Worker     │     │   Worker     │    │   Worker     │             │
│  │(Cloud Func)  │     │(Cloud Func)  │    │(Cloud Func)  │             │
│  │              │     │              │    │              │             │
│  │ - RAG Query  │     │ - TTS API    │    │ - Nano API   │             │
│  │ - LearnLM    │     │ - Save GCS   │    │ - Save GCS   │             │
│  └──────┬───────┘     └──────────────┘    └──────────────┘             │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │         Vertex AI (LearnLM, Vector Search)               │           │
│  └──────────────────────────────────────────────────────────┘           │
└───────────────────────────────────────────────────────────────────────────┘
            │
            │
┌───────────▼───────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐     │
│  │   Cloud SQL     │  │   Cloud Storage │  │  Vertex AI Vector    │     │
│  │  (PostgreSQL)   │  │      (GCS)      │  │       Search         │     │
│  │                 │  │                 │  │                      │     │
│  │ - Users         │  │ - Audio Files   │  │ - OER Embeddings     │     │
│  │ - Topics        │  │ - Video Files   │  │ - RAG Retrieval      │     │
│  │ - Interests     │  │ - Scripts       │  │                      │     │
│  │ - Progress      │  │                 │  │                      │     │
│  │ - Metadata      │  │                 │  │                      │     │
│  └─────────────────┘  └─────────────────┘  └──────────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY LAYER                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Cloud      │  │    Cloud     │  │    Cloud     │  │    Cloud     │  │
│  │  Monitoring  │  │   Logging    │  │    Trace     │  │    Error     │  │
│  │              │  │              │  │              │  │  Reporting   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Frontend Components

#### Web App (React)
- **Purpose**: Primary student and teacher interface
- **Technology**: React 18+, TypeScript, Tailwind CSS
- **Hosting**: Firebase Hosting or Cloud Storage + CDN
- **Key Features**:
  - Authentication UI
  - Content request interface
  - Video/audio player
  - Progress tracking visualization
  - Interest management

#### Admin Portal
- **Purpose**: District/School administrator interface
- **Technology**: React 18+, TypeScript, Material-UI
- **Key Features**:
  - User management
  - KPI dashboards
  - Bulk upload interface
  - Account approval workflows

### Backend Services (Cloud Run)

#### API Gateway Service
- **Responsibility**: Single entry point for all client requests
- **Functions**:
  - JWT authentication validation
  - Rate limiting (per user/IP)
  - Request routing to appropriate services
  - CORS handling
  - API versioning
- **Scaling**: Auto-scale 0-100 instances
- **Language**: Python (FastAPI)

#### Student Service
- **Responsibility**: Student-specific operations
- **Endpoints**:
  - POST /api/v1/students/request-content
  - GET /api/v1/students/profile
  - PUT /api/v1/students/interests
  - POST /api/v1/students/feedback
  - GET /api/v1/students/progress
- **Dependencies**: NLU Service, Cache Service, Cloud SQL
- **Language**: Python (FastAPI)

#### Teacher Service
- **Responsibility**: Teacher and class management
- **Endpoints**:
  - GET /api/v1/teachers/classes
  - POST /api/v1/teachers/classes
  - GET /api/v1/teachers/students/{id}/progress
  - POST /api/v1/teachers/student-requests
- **Dependencies**: Cloud SQL, Admin Service
- **Language**: Python (FastAPI)

#### Admin Service
- **Responsibility**: Administrative operations
- **Endpoints**:
  - POST /api/v1/admin/users/bulk-upload
  - GET /api/v1/admin/kpis
  - GET /api/v1/admin/pending-requests
  - PUT /api/v1/admin/requests/{id}/approve
- **Dependencies**: Cloud SQL
- **Language**: Python (FastAPI)

#### Cache Service
- **Responsibility**: Centralized cache management
- **Functions**:
  - Generate cache keys: `SHA256(topic_id|interest|style)`
  - Check GCS for existing content
  - Return metadata (URLs, timestamps)
  - Track cache hit/miss metrics
- **Language**: Python (FastAPI)

#### Content Delivery Service
- **Responsibility**: Secure content URL generation
- **Functions**:
  - Generate signed GCS URLs (15-minute TTL)
  - Track content views
  - Handle content availability notifications
- **Language**: Python (FastAPI)

### Worker Services (Cloud Functions)

#### NLU Service (Cloud Function Gen 2)
- **Trigger**: HTTP request from Student Service
- **Function**:
  - Parse free-text student input
  - Call Vertex AI LLM for topic extraction
  - Return topic_id or clarification questions
- **Timeout**: 30 seconds
- **Memory**: 512MB
- **Language**: Python

#### Script Worker (Cloud Function Gen 2)
- **Trigger**: Pub/Sub message on `generate-script` topic
- **Function**:
  1. Retrieve OER content via Vertex AI Vector Search (RAG)
  2. Call LearnLM via Vertex AI with prompt template
  3. Parse JSON storyboard response
  4. Save script to GCS
  5. Publish to `generate-audio` topic
  6. Publish to `generate-video` topic (parallel)
- **Timeout**: 120 seconds
- **Memory**: 1GB
- **Language**: Python

#### Audio Worker (Cloud Function Gen 2)
- **Trigger**: Pub/Sub message on `generate-audio` topic
- **Function**:
  1. Retrieve script from GCS
  2. Call Cloud Text-to-Speech API
  3. Save audio file to GCS
  4. Update database with audio URL
  5. Notify Student Service (via Pub/Sub)
- **Timeout**: 60 seconds
- **Memory**: 512MB
- **Language**: Python

#### Video Worker (Cloud Function Gen 2)
- **Trigger**: Pub/Sub message on `generate-video` topic
- **Function**:
  1. Retrieve script and audio URL from GCS
  2. Call Nano Banana API with storyboard
  3. Poll for video completion
  4. Download and save video to GCS
  5. Update database with video URL
  6. Notify Student Service (via Pub/Sub)
- **Timeout**: 600 seconds (10 minutes)
- **Memory**: 1GB
- **Language**: Python

### Data Stores

#### Cloud SQL (PostgreSQL 15)
- **Purpose**: Relational data storage
- **Configuration**:
  - Instance Type: db-g1-small (MVP), upgradeable
  - Storage: 20GB SSD (auto-increase enabled)
  - Backups: Daily automated backups (7-day retention)
  - High Availability: Single zone (MVP), multi-zone (production)
- **Schemas**: See DATABASE_SCHEMA.md

#### Cloud Storage (GCS)
- **Buckets**:
  - `vividly-mvp-scripts`: JSON storyboard files
  - `vividly-mvp-audio`: MP3 audio files
  - `vividly-mvp-videos`: MP4 video files
  - `vividly-mvp-uploads`: Temporary bulk upload files
- **Configuration**:
  - Location: us-central1
  - Storage Class: Standard
  - Lifecycle: Delete temporary uploads after 7 days
  - Versioning: Disabled (MVP)
  - Encryption: Google-managed keys

#### Vertex AI Vector Search
- **Purpose**: RAG retrieval for OER content
- **Configuration**:
  - Index Type: Tree-AH (Approximate Nearest Neighbor)
  - Dimensions: 768 (text-embedding-gecko@003)
  - Distance Metric: Cosine similarity
  - Shard Size: 1 (MVP)
- **Contents**: Embedded chunks of OpenStax textbooks

### Message Queue (Cloud Pub/Sub)

#### Topics
- `generate-script`: Trigger script generation
- `generate-audio`: Trigger audio generation
- `generate-video`: Trigger video generation
- `content-ready`: Notify frontend of completion
- `dlq-script`, `dlq-audio`, `dlq-video`: Dead letter queues

#### Subscriptions
- Each worker has a dedicated subscription
- Message retention: 7 days
- Acknowledgment deadline: 600 seconds
- Retry policy: Exponential backoff (min 10s, max 600s)

## Data Flow

### Sequence 1: Cache Hit (Full Experience)

```
Student → Web App → API Gateway → Student Service → Cache Service
                                                            │
                                                            ├─→ Check GCS
                                                            │
                                                            ├─→ Cache HIT
                                                            │
                                                            └─→ Return URLs
                                                                     │
Web App ←─────────────────────────────────────────────────────────┘
   │
   ├─→ Display Video Player
   └─→ Record View Event
```

### Sequence 2: Cache Miss (Fast Path → Full Experience)

```
Student → Web App → API Gateway → Student Service
                                        │
                                        ├─→ NLU Service
                                        │      └─→ Vertex AI LLM → topic_id
                                        │
                                        ├─→ Cache Service
                                        │      └─→ GCS Check → MISS
                                        │
                                        └─→ Pub/Sub: generate-script
                                                │
                                                ▼
                                         Script Worker
                                                │
                                                ├─→ Vertex AI Vector Search (RAG)
                                                ├─→ Vertex AI LearnLM
                                                ├─→ Save Script to GCS
                                                │
                                                ├─→ Pub/Sub: generate-audio
                                                │        │
                                                │        ▼
                                                │   Audio Worker
                                                │        │
                                                │        ├─→ Cloud TTS API
                                                │        ├─→ Save Audio to GCS
                                                │        └─→ Pub/Sub: content-ready (FAST PATH)
                                                │                   │
                                                │                   ▼
                                                │            Student Service
                                                │                   │
                                                │                   └─→ Web App
                                                │                          │
                                                │                          └─→ Display Script + Audio
                                                │
                                                └─→ Pub/Sub: generate-video
                                                         │
                                                         ▼
                                                    Video Worker
                                                         │
                                                         ├─→ Nano Banana API
                                                         ├─→ Save Video to GCS
                                                         └─→ Pub/Sub: content-ready (FULL)
                                                                    │
                                                                    ▼
                                                             Student Service
                                                                    │
                                                                    └─→ Web App
                                                                           │
                                                                           └─→ Update to Video Player
```

## Technology Stack

### Frontend
- **Framework**: React 18.2+
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite
- **State Management**: React Context + React Query
- **Styling**: Tailwind CSS 3.3+
- **Video Player**: Video.js
- **HTTP Client**: Axios

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Migration Tool**: Alembic
- **Validation**: Pydantic 2.0+
- **Authentication**: PyJWT
- **Testing**: pytest, pytest-asyncio

### Infrastructure
- **Cloud Provider**: Google Cloud Platform
- **IaC**: Terraform 1.6+
- **CI/CD**: GitHub Actions
- **Container Registry**: Google Artifact Registry
- **Secrets**: Google Secret Manager

### AI/ML
- **LLM**: Vertex AI (Gemini/LearnLM)
- **Embeddings**: Vertex AI (text-embedding-gecko@003)
- **Vector DB**: Vertex AI Vector Search
- **TTS**: Google Cloud Text-to-Speech
- **Video Generation**: Nano Banana API (external)

### Monitoring
- **Logging**: Cloud Logging
- **Metrics**: Cloud Monitoring
- **Tracing**: Cloud Trace
- **Errors**: Cloud Error Reporting
- **Uptime**: Cloud Monitoring Uptime Checks

## Infrastructure Topology

### GCP Project Structure

```
vividly-mvp (Project ID: vividly-mvp-12345)
│
├── Compute
│   ├── Cloud Run Services (us-central1)
│   │   ├── api-gateway
│   │   ├── student-service
│   │   ├── teacher-service
│   │   ├── admin-service
│   │   ├── cache-service
│   │   └── content-delivery
│   │
│   └── Cloud Functions Gen 2 (us-central1)
│       ├── nlu-service
│       ├── script-worker
│       ├── audio-worker
│       └── video-worker
│
├── Storage
│   ├── Cloud SQL
│   │   └── vividly-mvp-db (PostgreSQL 15, us-central1)
│   │
│   └── Cloud Storage
│       ├── vividly-mvp-scripts
│       ├── vividly-mvp-audio
│       ├── vividly-mvp-videos
│       └── vividly-mvp-uploads
│
├── AI/ML
│   ├── Vertex AI Workbench
│   ├── Vector Search Index (oer-embeddings-index)
│   └── Model Endpoints (LearnLM, Embeddings)
│
├── Messaging
│   └── Pub/Sub
│       ├── Topics: generate-script, generate-audio, generate-video, content-ready
│       └── Subscriptions: (one per worker)
│
├── Networking
│   ├── VPC (default or custom)
│   ├── Cloud Load Balancer (HTTPS)
│   ├── Cloud Armor (DDoS protection)
│   └── Cloud CDN (static assets)
│
├── Security
│   ├── Secret Manager (API keys, DB credentials)
│   ├── IAM Policies
│   └── Service Accounts (one per service)
│
└── Operations
    ├── Cloud Monitoring (dashboards, alerts)
    ├── Cloud Logging (log sinks)
    ├── Cloud Trace
    └── Error Reporting
```

### Network Architecture

```
Internet
   │
   ▼
┌────────────────────────────────────────────┐
│       Cloud Load Balancer (HTTPS)          │
│       - SSL Termination                    │
│       - Cloud Armor (WAF)                  │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│            VPC Network                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Cloud Run Services (Private IPs)   │  │
│  │   - Ingress: Internal & Cloud LB     │  │
│  │   - Egress: Private Google Access    │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Cloud SQL (Private IP)             │  │
│  │   - VPC Peering                      │  │
│  │   - No public IP                     │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Cloud Functions (VPC Connector)    │  │
│  │   - Serverless VPC Access            │  │
│  └──────────────────────────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
                 │
                 │ (Private Google Access)
                 │
                 ▼
┌─────────────────────────────────────────────┐
│      Google APIs & Services                 │
│  - Vertex AI                                │
│  - Cloud Storage                            │
│  - Pub/Sub                                  │
│  - Secret Manager                           │
└─────────────────────────────────────────────┘
```

## Security Architecture

### Authentication Flow

```
1. User Login
   │
   ├─→ [SSO Future] Google/Clever OAuth
   │
   └─→ [MVP] Email/Password
        │
        └─→ API Gateway
             │
             ├─→ Validate Credentials (Cloud SQL)
             │
             ├─→ Generate JWT (HS256)
             │    - iss: vividly-mvp
             │    - sub: user_id
             │    - role: student|teacher|admin
             │    - exp: 24 hours
             │
             └─→ Return JWT to client
```

### Authorization (RBAC)

```
API Request with JWT
   │
   ▼
API Gateway Middleware
   │
   ├─→ Verify JWT signature
   ├─→ Check expiration
   ├─→ Extract role
   │
   └─→ Route to Service
        │
        ▼
   Service-Level RBAC Check
        │
        ├─→ Check user.role vs required_role
        ├─→ Check resource ownership (e.g., teacher can only view their students)
        │
        └─→ [PASS] Execute request
            [FAIL] Return 403 Forbidden
```

### Data Encryption

- **In Transit**: TLS 1.3 for all client-server communication
- **At Rest**:
  - Cloud SQL: Google-managed encryption
  - GCS: Google-managed encryption keys
  - Application-level: None (MVP), field-level for PII (future)

### Secrets Management

All sensitive values stored in Google Secret Manager:
- `db-password`: PostgreSQL password
- `jwt-secret`: JWT signing key
- `nano-banana-api-key`: Video generation API key
- `vertex-ai-service-account-key`: Vertex AI credentials

## Scalability Considerations

### Horizontal Scaling

#### Cloud Run Services
- **Auto-scaling**: 0 to 100 instances per service
- **Concurrency**: 80 requests per instance
- **Target Utilization**: 70% CPU

#### Cloud Functions
- **Max Instances**: 100 per function
- **Concurrency**: 1 (for simplicity)
- **Scaling Trigger**: Queue depth

### Vertical Scaling

#### Cloud SQL
- Upgradable from db-g1-small to db-custom-4-16384
- Read replicas for read-heavy workloads
- Connection pooling via PgBouncer (future)

#### Vector Search
- Shard size increase as dataset grows
- Index rebuilding strategy for large updates

### Caching Strategy

#### Application Cache
- Cache hit target: 15% (MVP) → 40% (production)
- Pre-warming strategy: Popular topics × Top interests
- TTL: Indefinite (content is immutable)

#### CDN
- Static assets served via Cloud CDN
- Cache headers for images, JS, CSS: max-age=31536000

### Cost Optimization

#### Resource Limits
- Cloud Run: Scale to zero when idle
- Cloud Functions: Conservative max instances
- Cloud SQL: Right-size instance type

#### Storage
- GCS Lifecycle: Archive videos not viewed in 90 days (future)
- Cloud SQL: Automated backups with 7-day retention

#### AI API Costs
- LearnLM: ~$0.001 per generation (1000 tokens)
- TTS: ~$0.006 per generation (200 characters)
- Nano Banana: ~$0.10 per video
- **Cache critical** for cost control

## Disaster Recovery

### Backup Strategy
- **Cloud SQL**: Daily automated backups, 7-day retention
- **GCS**: Not backed up (content is reproducible)
- **Vector Search**: Snapshot weekly

### Recovery Procedures
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 24 hours

### Failure Scenarios

#### Cloud SQL Failure
- Restore from latest backup
- Potential data loss: Last 24 hours

#### GCS Bucket Deletion
- Content regeneration from database records
- Priority: Most-viewed content first

#### Service Outage
- Automatic restart via Cloud Run health checks
- Manual intervention for persistent failures

## Future Architecture Enhancements

### Post-MVP Considerations

1. **Multi-Region Deployment**: Reduce latency for non-Nashville users
2. **Redis Cache Layer**: Reduce Cloud SQL load for hot data
3. **Event Sourcing**: Complete audit trail for compliance
4. **GraphQL API**: More efficient data fetching for frontend
5. **Microservices Decomposition**: Further split Student Service
6. **Kubernetes (GKE)**: For more complex orchestration needs
7. **Data Lake**: BigQuery for advanced analytics
8. **ML Pipeline**: Automated model retraining and A/B testing

---

**Document Control**
- **Owner**: Vividly Technical Team
- **Reviewers**: Architecture Review Board
- **Next Review**: Post-MVP Launch
