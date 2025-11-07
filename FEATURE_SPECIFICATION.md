# Vividly Platform - Comprehensive Feature Specification
**Author**: Andrew Ng's Systematic Analysis
**Date**: 2025-11-03
**Version**: 1.0
**Focus**: Generalized Training Content Platform

---

## Executive Summary

This specification transforms Vividly from an education-specific platform into a **generalized, extensible training content generation system** applicable to K-12 education, corporate training, professional development, onboarding, compliance training, and lifelong learning. The core architectural principle is **content-agnostic RAG** with **pluggable knowledge sources**.

### Key Innovation: Knowledge Source Management System (KSMS)

The platform will support **any** training content through a unified Knowledge Source Management System that allows administrators to define, upload, and manage learning materials from multiple sources.

---

## Current Architecture Analysis

### Existing Components (What We Have)

#### Frontend Structure
```
frontend/src/
├── pages/
│   ├── student/         # Learner interface
│   ├── teacher/         # Instructor interface
│   ├── admin/           # Org Admin (partial)
│   └── super-admin/     # Platform Admin (partial)
├── components/
│   ├── ContentRequestForm.tsx      # Content generation UI
│   ├── ContentStatusTracker.tsx    # Real-time progress
│   ├── VideoPlayer.tsx             # Playback interface
│   └── MonitoringDashboard.tsx     # System health
└── types/
    ├── auth.ts          # User roles: Student, Teacher, Admin, Super_Admin
    ├── content.ts       # Content generation types
    └── teacher.ts       # Instructor-specific types
```

#### Backend Models
```
backend/app/models/
├── user.py                  # Authentication & RBAC
├── content_metadata.py      # Generated content tracking
├── request_tracking.py      # Async request pipeline
├── interest.py              # Personalization
├── class_model.py          # Groups/cohorts
└── progress.py             # Learning analytics
```

#### RAG Infrastructure
- **Embeddings**: 3,783 OpenStax education textbook embeddings (hardcoded)
- **Vector Store**: ChromaDB with cosine similarity search (threshold > 0.65)
- **Content Worker**: Async Pub/Sub-based generation pipeline
- **LLM**: Vertex AI (Gemini) for script generation

### Current Limitations (Critical Gaps)

1. **Hardcoded Knowledge Sources**
   - Only supports OpenStax embeddings
   - No admin interface to add new sources
   - Cannot support non-education domains

2. **Missing Content Source Management**
   - No URL ingestion system
   - No PDF upload capability
   - No multi-source RAG aggregation

3. **Incomplete Admin Tools**
   - Admin/Super-Admin dashboards are placeholder UI
   - No content library management
   - No source quality metrics

4. **Limited Personalization**
   - "Interests" are education-specific (basketball, etc.)
   - No learner personas for different training contexts
   - Fixed grade-level model

5. **No Multi-Tenancy Support**
   - Organizations cannot have isolated knowledge bases
   - No per-org content source configuration

---

## Proposed Feature Set

### Priority 1: Knowledge Source Management System (KSMS)

#### 1.1 Content Source Definition

**User Story**: As a Super Admin or Admin, I need to define new knowledge sources so learners can generate content from organization-specific materials.

**Features**:
- **URL Ingestion**
  - Add public web page URLs (documentation sites, knowledge bases)
  - Add PDF URLs for automatic download + processing
  - Support for authentication (Basic Auth, API keys for private docs)
  - Sitemap crawling for bulk URL ingestion

- **PDF Upload**
  - Direct PDF file upload (< 50 MB per file)
  - Bulk upload (up to 100 files at once)
  - Support for training manuals, policy documents, procedures

- **Text Content**
  - Direct markdown/plain text input
  - Useful for FAQs, company policies, standard procedures

**Data Model**:
```python
class ContentSource(Base):
    source_id: str (UUID)
    organization_id: str (nullable for platform-wide sources)
    name: str  # "Sales Training Manual 2025"
    description: str
    source_type: Enum['url', 'pdf', 'text', 'youtube', 'api']

    # Source-specific metadata
    url: str (nullable)
    file_path: str (nullable, GCS bucket path)
    api_config: JSON (nullable)

    # Processing status
    status: Enum['pending', 'processing', 'active', 'failed', 'deprecated']
    embedding_count: int  # Number of chunks indexed
    last_updated: datetime

    # Access control
    visibility: Enum['public', 'organization', 'class']
    allowed_roles: List[UserRole]

    # Quality metrics
    usage_count: int  # How many content generations used this source
    avg_relevance_score: float  # Average RAG similarity when retrieved

    created_by: str (user_id)
    created_at: datetime
```

#### 1.2 Processing Pipeline

**Architecture**:
```
Content Source Input
    ↓
Preprocessing Service
    ├── URL Fetcher (BeautifulSoup/Playwright)
    ├── PDF Parser (PyPDF2/pdfplumber)
    └── Text Normalizer
    ↓
Chunking Strategy
    ├── Semantic chunking (LangChain RecursiveCharacterTextSplitter)
    ├── Size: 500-1000 tokens per chunk
    └── Overlap: 100 tokens
    ↓
Embedding Generation (Vertex AI)
    ├── text-embedding-004 model
    └── Batch processing (100 chunks/request)
    ↓
Vector Store (ChromaDB)
    ├── Collection per organization
    ├── Metadata: {source_id, chunk_index, doc_title, page_num}
    └── Searchable by organization_id + query
```

**Implementation Approach**:
1. Create new Cloud Run Job: `content-source-processor`
2. Triggered by Pub/Sub on source creation
3. Store embeddings in organization-specific ChromaDB collections
4. Update `ContentSource.status` throughout processing

#### 1.3 Multi-Source RAG Retrieval

**Enhanced RAG Service**:
```python
class MultiSourceRAGService:
    async def retrieve_context(
        self,
        query: str,
        organization_id: str,
        learner_id: str,
        top_k: int = 10
    ) -> List[RetrievedChunk]:
        # 1. Determine applicable sources
        sources = await self.get_active_sources(
            organization_id,
            learner_id
        )

        # 2. Query each source's collection
        results = []
        for source in sources:
            chunks = await self.query_collection(
                collection_name=f"org_{organization_id}_source_{source.source_id}",
                query=query,
                top_k=top_k
            )
            results.extend(chunks)

        # 3. Re-rank by relevance
        ranked_results = self.rerank_by_similarity(results)

        # 4. Filter by threshold (> 0.65)
        filtered = [r for r in ranked_results if r.score > 0.65]

        # 5. Diversify sources (max 3 chunks per source)
        diversified = self.diversify_by_source(filtered)

        return diversified[:top_k]
```

### Priority 2: Admin Content Management UI

#### 2.1 Content Library Dashboard

**Route**: `/admin/content-library` (Admin), `/super-admin/content-library` (Super Admin)

**Features**:
- Table view of all content sources
  - Columns: Name, Type, Status, Embeddings, Usage, Last Updated
  - Filters: Type, Status, Visibility
  - Search by name/description

- Source actions:
  - Edit metadata (name, description, visibility)
  - Reprocess (re-run embedding generation)
  - Deprecate (mark as inactive without deleting)
  - Delete (with confirmation, cascades to embeddings)

- Bulk operations:
  - Select multiple sources → Bulk deprecate
  - Export source metadata as CSV

**UI Components**:
```tsx
// frontend/src/pages/admin/ContentLibraryPage.tsx
<ContentLibrary>
  <ContentLibraryFilters />
  <ContentLibraryTable
    data={sources}
    onEdit={handleEdit}
    onReprocess={handleReprocess}
    onDelete={handleDelete}
  />
  <AddContentSourceModal />
</ContentLibrary>
```

#### 2.2 Add Content Source Form

**Modal**: `AddContentSourceModal.tsx`

**Form Fields**:
```
Source Type: [URL | PDF Upload | Text | YouTube]
    ↓
Name: [Free text, required, 100 char max]
Description: [Textarea, optional, 500 char max]
    ↓
[IF URL]
  - URL: [Input, validates URL format]
  - Fetch Depth: [Dropdown: Single page | Follow links (1 level) | Crawl subdirectory]
  - Authentication: [Optional: Basic Auth username/password]

[IF PDF Upload]
  - File Upload: [Drag-and-drop, supports .pdf, max 50MB]
  - OR Bulk Upload: [Supports .zip of PDFs, max 500MB]

[IF Text]
  - Content: [Markdown editor, 50,000 char max]

[IF YouTube]
  - Video URL or Playlist URL
  - Extract: [Subtitles | Auto-generated captions | Transcript]
    ↓
Visibility: [Public | Organization-only | Specific classes]
    ↓
Allowed Roles: [Checkbox: All | Students | Teachers | Admins]
    ↓
[Submit Button] → Triggers processing pipeline
```

**Backend API**:
```python
# POST /api/v1/content-sources
@router.post("/content-sources")
async def create_content_source(
    source_data: ContentSourceCreate,
    current_user: User = Depends(get_current_user)
):
    # Validate permissions (Admin or Super_Admin)
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(403, "Insufficient permissions")

    # Create source record
    source = await db.create_content_source(source_data)

    # Publish to Pub/Sub for processing
    await pubsub.publish(
        topic="content-source-processing",
        message={"source_id": source.source_id}
    )

    return {"source_id": source.source_id, "status": "processing"}
```

### Priority 3: Role-Based Access Control (RBAC) Enhancements

#### 3.1 Permission Matrix

| Feature | Student | Teacher | Admin (Org) | Super Admin |
|---------|---------|---------|-------------|-------------|
| Generate content | ✓ | ✓ | ✓ | ✓ |
| View own videos | ✓ | ✓ | ✓ | ✓ |
| View class videos | - | ✓ | ✓ | ✓ |
| View all org videos | - | - | ✓ | ✓ |
| Add content sources | - | - | ✓ (org) | ✓ (all) |
| Edit content sources | - | - | ✓ (org) | ✓ (all) |
| Delete content sources | - | - | ✓ (org) | ✓ (all) |
| Manage users | - | ✓ (class) | ✓ (org) | ✓ (all) |
| View analytics | - | ✓ (class) | ✓ (org) | ✓ (all) |
| System settings | - | - | - | ✓ |
| Monitoring dashboard | - | - | - | ✓ |

#### 3.2 Organization-Scoped Data Isolation

**Principle**: Each organization has logically isolated data, enforced at the database query level.

**Implementation**:
```python
# Middleware for automatic org filtering
async def get_current_org_context(
    current_user: User = Depends(get_current_user)
) -> OrganizationContext:
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can access all orgs (via query param)
        return OrganizationContext(
            organization_id=request.query_params.get("org_id"),
            is_super_admin=True
        )
    else:
        # Other users are scoped to their org
        return OrganizationContext(
            organization_id=current_user.organization_id,
            is_super_admin=False
        )

# Applied to all queries
async def list_content_sources(
    ctx: OrganizationContext = Depends(get_current_org_context)
):
    query = select(ContentSource)
    if not ctx.is_super_admin:
        query = query.where(
            ContentSource.organization_id == ctx.organization_id
        )
    return await db.execute(query)
```

### Priority 4: Generalized Learning Personas

#### 4.1 Replace "Grade Level" with "Proficiency Level"

**Current**: `grade_level` (9-12, education-specific)
**Proposed**: `proficiency_level` (enum: beginner, intermediate, advanced, expert)

**Migration Strategy**:
- Keep `grade_level` for backward compatibility
- Add `proficiency_level` to User model
- Map grade_level → proficiency_level:
  - 9-10 → beginner
  - 11 → intermediate
  - 12 → advanced

#### 4.2 Contextual "Interests" → "Learning Preferences"

**Current**: Hardcoded interests (basketball, music, etc.)
**Proposed**: Organization-defined learning preferences

**Data Model**:
```python
class LearningPreference(Base):
    preference_id: str
    organization_id: str  # Each org defines their own
    name: str  # "Sales scenarios", "Technical deep-dives", "Case studies"
    category: str  # "Analogy style", "Format", "Pace"
    description: str
    is_active: bool
```

**Example Use Cases**:
- **Corporate Training**: "Real-world scenarios", "Step-by-step guides", "Video demos"
- **Healthcare**: "Clinical case studies", "Procedure walkthroughs", "Evidence-based"
- **Education**: "Sports analogies", "Pop culture references", "Historical context"

### Priority 5: Content Generation Enhancements

#### 5.1 Source Attribution in Generated Content

**Requirement**: Generated scripts must cite sources for compliance/auditability.

**Implementation**:
```python
# Enhanced prompt template
CONTENT_GENERATION_PROMPT = """
Generate a learning video script based on:
Query: {query}
Proficiency Level: {proficiency_level}

Retrieved Context:
{context_with_sources}

Requirements:
1. Explain concepts at {proficiency_level} level
2. Use analogies related to: {learning_preferences}
3. Cite sources using [Source: {source_name}] notation
4. Duration: 2-3 minutes when read aloud
"""

# Post-processing
def add_source_citations(script: str, sources: List[ContentSource]) -> str:
    # Append "Sources Used" section
    sources_section = "\n\n--- Sources ---\n"
    for source in sources:
        sources_section += f"- {source.name}: {source.url or 'Internal document'}\n"
    return script + sources_section
```

#### 5.2 Multi-Language Support

**Future Consideration**: Support content generation in multiple languages.

**Architecture**:
- Detect user's preferred language from profile
- Translate query → English for RAG retrieval (if needed)
- Generate script in target language
- Use multilingual embeddings (text-multilingual-embedding-002)

---

## Implementation Roadmap

### Phase 1: Content Source Management (Weeks 1-3)

**Week 1**: Backend Foundation
- [ ] Create `ContentSource` model
- [ ] Build PDF upload → GCS storage
- [ ] Implement URL fetching service
- [ ] Create `content-source-processor` Cloud Run Job

**Week 2**: Processing Pipeline
- [ ] Chunking strategy implementation
- [ ] Vertex AI embedding integration
- [ ] ChromaDB collection management per org
- [ ] Status tracking & error handling

**Week 3**: API & Testing
- [ ] REST APIs for CRUD operations
- [ ] Permission middleware
- [ ] Unit tests for processing pipeline
- [ ] Integration tests for multi-source RAG

### Phase 2: Admin UI (Weeks 4-5)

**Week 4**: Content Library Dashboard
- [ ] `/admin/content-library` page
- [ ] Content sources table with filtering
- [ ] Add source modal (URL & PDF)
- [ ] Real-time status updates via WebSocket

**Week 5**: Admin Features
- [ ] Edit source metadata
- [ ] Reprocess functionality
- [ ] Delete with confirmation
- [ ] Source analytics dashboard

### Phase 3: RBAC & Multi-Tenancy (Week 6)

- [ ] Organization context middleware
- [ ] Permission enforcement on all endpoints
- [ ] Org-scoped ChromaDB collections
- [ ] Super admin org-switching UI

### Phase 4: Generalization (Weeks 7-8)

**Week 7**: Proficiency Levels
- [ ] Add `proficiency_level` to User model
- [ ] Update content generation prompts
- [ ] Migration script for existing users

**Week 8**: Learning Preferences
- [ ] `LearningPreference` model
- [ ] Org-defined preference management
- [ ] Updated interest selection UI
- [ ] Re-train preference matching

### Phase 5: Enhancements (Weeks 9-10)

- [ ] Source citation in scripts
- [ ] YouTube transcript integration
- [ ] API-based source connectors (Google Drive, Confluence)
- [ ] Advanced RAG: Hybrid search (keyword + semantic)

---

## Database Schema Changes

### New Tables

```sql
-- Content Sources
CREATE TABLE content_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(organization_id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    source_type VARCHAR(20) NOT NULL, -- 'url', 'pdf', 'text', 'youtube', 'api'

    -- Source-specific data
    url TEXT,
    file_path TEXT,  -- GCS path
    api_config JSONB,

    -- Processing status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'active', 'failed', 'deprecated'
    embedding_count INTEGER DEFAULT 0,
    processing_error TEXT,
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Access control
    visibility VARCHAR(20) DEFAULT 'organization', -- 'public', 'organization', 'class'
    allowed_roles TEXT[], -- ['student', 'teacher', 'admin']

    -- Quality metrics
    usage_count INTEGER DEFAULT 0,
    avg_relevance_score DECIMAL(3,2),

    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_org_status (organization_id, status),
    INDEX idx_source_type (source_type),
    INDEX idx_visibility (visibility)
);

-- Learning Preferences (replaces hardcoded interests)
CREATE TABLE learning_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(organization_id),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- 'analogy_style', 'format', 'pace'
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(organization_id, name)
);

-- User Learning Preferences (many-to-many)
CREATE TABLE user_learning_preferences (
    user_id UUID REFERENCES users(user_id),
    preference_id UUID REFERENCES learning_preferences(preference_id),
    selected_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, preference_id)
);

-- Source Usage Tracking
CREATE TABLE content_source_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES content_sources(source_id),
    request_id UUID REFERENCES content_requests(request_id),
    relevance_score DECIMAL(3,2),
    chunks_used INTEGER,
    used_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_source_usage (source_id, used_at)
);
```

### Modified Tables

```sql
-- Add proficiency_level to users
ALTER TABLE users
ADD COLUMN proficiency_level VARCHAR(20) DEFAULT 'intermediate';
-- Values: 'beginner', 'intermediate', 'advanced', 'expert'

-- Add source citations to content_requests
ALTER TABLE content_requests
ADD COLUMN sources_used JSONB;
-- Stores: [{"source_id": "...", "source_name": "...", "chunks_used": 5}]
```

---

## API Specifications

### Content Source Management

```
POST   /api/v1/content-sources
GET    /api/v1/content-sources
GET    /api/v1/content-sources/{source_id}
PUT    /api/v1/content-sources/{source_id}
DELETE /api/v1/content-sources/{source_id}
POST   /api/v1/content-sources/{source_id}/reprocess
GET    /api/v1/content-sources/{source_id}/analytics
```

### Learning Preferences

```
POST   /api/v1/learning-preferences
GET    /api/v1/learning-preferences
PUT    /api/v1/learning-preferences/{preference_id}
DELETE /api/v1/learning-preferences/{preference_id}

GET    /api/v1/users/me/learning-preferences
POST   /api/v1/users/me/learning-preferences
```

### Enhanced Content Generation

```
POST   /api/v1/content/generate
{
  "query": "Explain Kubernetes deployments",
  "proficiency_level": "intermediate",
  "learning_preferences": ["technical_deep_dives", "real_world_examples"],
  "source_filters": {
    "source_ids": ["uuid1", "uuid2"],  // Optional: limit to specific sources
    "source_types": ["url", "pdf"]      // Optional: limit to certain types
  }
}

Response:
{
  "request_id": "uuid",
  "status": "processing",
  "estimated_completion_seconds": 180,
  "sources_queried": 5
}
```

---

## Security & Compliance Considerations

### 1. Data Privacy

**Challenge**: Organizations may upload confidential materials (HR policies, proprietary procedures).

**Solution**:
- Encryption at rest (GCS server-side encryption)
- Encryption in transit (HTTPS only)
- Org-scoped ChromaDB collections (logical isolation)
- Optional: Customer-managed encryption keys (CMEK) for enterprise

### 2. Content Licensing

**Challenge**: URLs/PDFs may be copyrighted material.

**Solution**:
- Terms of Service: Admins certify they have rights to use content
- Opt-in checkbox: "I confirm I have rights to use this content for training"
- Audit log: Track which admin added which source

### 3. Access Control Enforcement

**Critical**: Prevent cross-organization data leakage.

**Implementation**:
- Middleware-enforced org filtering on ALL queries
- Database-level row-level security (RLS) in PostgreSQL
- Automated security tests: Attempt cross-org access, expect 403

---

## Success Metrics

### Content Source Management
- **Adoption**: % of organizations that add custom sources (Target: 80% within 3 months)
- **Processing Success Rate**: % of sources successfully embedded (Target: > 95%)
- **Average Processing Time**: Time from upload → active (Target: < 5 minutes for PDFs, < 10 minutes for URLs)

### Content Quality
- **Source Diversity**: Average # of distinct sources per generated video (Target: > 3)
- **Relevance Scores**: Average RAG similarity score for retrieved chunks (Target: > 0.75)
- **Citation Accuracy**: % of scripts with valid source citations (Target: 100%)

### User Engagement
- **Content Generation Rate**: Videos generated per active user per week (Target: > 2)
- **Learner Satisfaction**: Post-video rating (Target: > 4.2 / 5.0)
- **Admin Engagement**: % of admins who actively manage sources (Target: > 60%)

---

## Risk Analysis & Mitigation

### Risk 1: Poor Quality Sources
**Risk**: Admins upload low-quality or irrelevant content → bad video scripts.

**Mitigation**:
- Quality scoring: Analyze embedding distribution (detect garbage text)
- Usage analytics: Flag sources with low avg relevance scores
- Admin feedback: "Report poor quality source" button

### Risk 2: Processing Scalability
**Risk**: Large PDF uploads (500-page manuals) overload processing pipeline.

**Mitigation**:
- Chunking limits: Max 10,000 chunks per source
- Rate limiting: Max 10 concurrent processing jobs per org
- Queue management: Pub/Sub with dead-letter queue for failed jobs

### Risk 3: RAG Retrieval Latency
**Risk**: Querying multiple org-specific ChromaDB collections is slow.

**Mitigation**:
- Index optimization: Pre-filter collections by metadata before vector search
- Caching: Cache frequently retrieved chunks (Redis)
- Async processing: Keep content generation async (already implemented)

---

## Future Vision (12-18 Months)

### 1. AI-Powered Content Curation
- Automatically suggest content sources based on learner queries
- "Your org is missing content about X. Suggested sources: [URL1, URL2]"

### 2. Collaborative Learning
- Learners can share generated videos with classmates
- Commenting and discussion threads on videos
- Upvote/downvote to improve content quality

### 3. Advanced Analytics
- Learner journey mapping: What content paths lead to mastery?
- Source ROI: Which sources generate the highest-rated content?
- Predictive analytics: Recommend content before learners ask

### 4. Integration Ecosystem
- LMS integrations (Canvas, Moodle, Blackboard)
- HR system integrations (Workday, BambooHR)
- Knowledge base connectors (Confluence, Notion, SharePoint)

### 5. Live Content Generation
- Real-time Q&A: Learners ask questions, get instant video responses
- Voice input: Speak your question, get a video
- AR/VR: Immersive 3D learning experiences

---

## Conclusion

This specification transforms Vividly into a **universal training content platform** by:

1. **Decoupling from education**: Proficiency levels, learning preferences
2. **Enabling customization**: Admins define their own knowledge sources
3. **Ensuring scalability**: Org-scoped data, multi-source RAG, robust RBAC
4. **Future-proofing**: Extensible architecture for integrations, advanced analytics

The **Knowledge Source Management System** is the cornerstone innovation, enabling:
- Corporate training (company wikis, product docs, procedures)
- Healthcare training (clinical guidelines, protocols, case studies)
- Software onboarding (API docs, codebase tutorials, architecture guides)
- Compliance training (regulations, policies, safety procedures)

By following this specification, Vividly becomes **the AI training platform for any organization**, not just schools.

---

**Next Steps**:
1. Review this spec with product/engineering teams
2. Prioritize features based on customer feedback
3. Begin Phase 1 implementation: Content Source Management
4. Iterate based on early adopter feedback (beta customers)
