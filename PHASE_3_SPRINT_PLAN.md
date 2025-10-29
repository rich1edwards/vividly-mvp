# Phase 3: AI Content Pipeline - Sprint Plan

**Phase Duration**: 3 weeks (November 25 - December 13, 2025)
**Sprint Model**: 1-week sprints (3 sprints total)
**Team Size**: 2 engineers (1 AI/ML specialist + 1 full-stack)
**Velocity Target**: 26-28 story points per sprint
**Definition of Done**: Code reviewed, tests passing (>75% coverage), AI quality validated, deployed to dev

---

## Table of Contents

1. [Phase Overview](#phase-overview)
2. [Sprint 1: NLU & Topic Extraction](#sprint-1-nlu--topic-extraction)
3. [Sprint 2: RAG & Script Generation](#sprint-2-rag--script-generation)
4. [Sprint 3: Audio & Video Pipeline](#sprint-3-audio--video-pipeline)
5. [AI Quality Standards](#ai-quality-standards)
6. [Testing Strategy](#testing-strategy)
7. [Success Metrics](#success-metrics)

---

## Phase Overview

### Phase 3 Objectives

Build the complete AI-powered content generation pipeline:
- Natural language understanding for topic extraction
- RAG-based educational content retrieval
- Personalized script generation with LearnLM
- Text-to-speech audio generation
- Video generation and rendering
- Complete pipeline orchestration

### Sprint Breakdown

| Sprint | Focus | Key Deliverables | Story Points |
|--------|-------|------------------|--------------|
| Sprint 1 | NLU & Topic Extraction | NLU Service, Topic Mapping, Clarification | 26 |
| Sprint 2 | RAG & Script Generation | Vector Search, Script Worker, LearnLM | 28 |
| Sprint 3 | Audio & Video Pipeline | TTS Worker, Video Worker, Orchestration | 27 |
| **Total** | | **Complete AI Pipeline** | **81** |

### Critical Path

```
Sprint 1: NLU Service (BLOCKS Sprint 2)
    ↓
Sprint 2: Script Worker (BLOCKS Sprint 3)
    ↓
Sprint 3: Audio/Video Workers (PARALLEL)
    ↓
Phase 3 Complete
```

---

## Sprint 1: NLU & Topic Extraction

**Dates**: November 25-29, 2025 (4 days - Thanksgiving week)
**Goal**: Build intelligent topic extraction from free-text input
**Story Points**: 26

### Sprint 1 Backlog

#### Epic 1.1: NLU Service Foundation (13 points)

**Owner**: AI/ML Engineer
**Priority**: P0 (Critical Path)
**Dependencies**: Phase 2 complete (Topics API), Vertex AI access

##### Story 1.1.1: Vertex AI Integration & Prompt Engineering (5 points)

**As a** system
**I want to** extract structured topic data from student queries
**So that** I can map requests to canonical topics

**Tasks**:
- [ ] Set up Vertex AI Gemini client
  - Configure project and credentials
  - Set up API quotas and limits
  - Implement retry logic with exponential backoff
- [ ] Design base prompt template
  - System role definition
  - Topic list injection (JSON format)
  - Output format specification
  - Few-shot examples
- [ ] Implement prompt templating system
  - Jinja2 templates for flexibility
  - Context injection (grade level, history)
  - Dynamic topic filtering
- [ ] Test with sample queries (50 examples)
  - Physics, Chemistry, Biology queries
  - Varying complexity levels
  - Edge cases (ambiguous, off-topic)
- [ ] Measure accuracy baseline (target: >85%)
- [ ] Write unit tests (8 test cases)
- [ ] Document prompt engineering decisions

**Acceptance Criteria**:
- [x] Vertex AI client functional
- [x] Prompts return structured JSON
- [x] Accuracy >85% on test set
- [x] Response time <3 seconds (p95)
- [x] Graceful error handling
- [x] Test coverage >80%

**Prompt Template**:
```python
NLU_SYSTEM_PROMPT = """You are an educational AI assistant specializing in high school STEM subjects.

Your task is to analyze student queries and map them to standardized educational topics.

Available Topics (JSON):
{topics_json}

Student Information:
- Grade Level: {grade_level}
- Subject Context: {subject_context}
- Previous Topics: {recent_topics}

Instructions:
1. Identify the primary academic concept
2. Map to ONE of the available topic_ids
3. If ambiguous, provide clarifying questions
4. If off-topic, politely redirect
5. Consider grade-appropriateness

Output Format (JSON):
{{
  "confidence": 0.95,
  "topic_id": "topic_phys_mech_newton_3" | null,
  "topic_name": "Newton's Third Law" | null,
  "clarification_needed": false | true,
  "clarifying_questions": [],
  "out_of_scope": false | true,
  "reasoning": "Brief explanation"
}}

Few-Shot Examples:

Input: "Explain Newton's Third Law using basketball"
Output: {{
  "confidence": 0.98,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": false,
  "reasoning": "Clear reference to Newton's Third Law in physics"
}}

Input: "Tell me about gravity"
Output: {{
  "confidence": 0.65,
  "topic_id": null,
  "topic_name": null,
  "clarification_needed": true,
  "clarifying_questions": [
    "Are you interested in Newton's Law of Universal Gravitation?",
    "Or gravitational acceleration on Earth (g = 9.8 m/s²)?",
    "Or Einstein's General Relativity?"
  ],
  "out_of_scope": false,
  "reasoning": "Multiple valid interpretations of 'gravity'"
}}

Input: "What's the best pizza place?"
Output: {{
  "confidence": 0.99,
  "topic_id": null,
  "topic_name": null,
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": true,
  "reasoning": "Query not related to STEM education"
}}

Now analyze this student query:
Query: "{student_query}"
"""
```

**Implementation**:
```python
# backend/app/services/nlu_service.py
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
import json
from typing import Dict, Optional

class NLUService:
    def __init__(self):
        aiplatform.init(
            project="vividly-dev-rich",
            location="us-central1"
        )
        self.model = GenerativeModel("gemini-1.5-pro")

    async def extract_topic(
        self,
        student_query: str,
        grade_level: int,
        recent_topics: list = [],
        subject_context: Optional[str] = None
    ) -> Dict:
        """Extract topic from student query using Gemini."""

        # Get available topics for student's grade
        topics = await self._get_grade_appropriate_topics(grade_level)

        # Build prompt
        prompt = self._build_prompt(
            student_query=student_query,
            topics=topics,
            grade_level=grade_level,
            recent_topics=recent_topics,
            subject_context=subject_context
        )

        # Call Gemini with retry
        try:
            response = await self._call_gemini_with_retry(prompt)
            result = self._parse_response(response)

            # Validate result
            if result.get("topic_id"):
                validated = await self._validate_topic(
                    result["topic_id"],
                    grade_level
                )
                if not validated:
                    result["topic_id"] = None
                    result["clarification_needed"] = True

            return result

        except Exception as e:
            logger.error(f"NLU extraction failed: {e}")
            return self._fallback_response(student_query)

    async def _call_gemini_with_retry(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> str:
        """Call Gemini API with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,  # Low temperature for consistency
                        "top_p": 0.8,
                        "top_k": 40,
                        "max_output_tokens": 512,
                    }
                )
                return response.text

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

    def _parse_response(self, response_text: str) -> Dict:
        """Parse Gemini JSON response."""
        # Extract JSON from response (may have markdown formatting)
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in response")

        json_str = response_text[json_start:json_end]
        return json.loads(json_str)
```

**Time Estimate**: 1 day

---

##### Story 1.1.2: NLU API Endpoint (3 points)

**As a** Student Service
**I want to** call NLU service to extract topics
**So that** I can process content requests

**Tasks**:
- [ ] Implement Cloud Function HTTP endpoint
  - `POST /nlu/extract-topic`
  - Authentication (service-to-service)
  - Request validation
- [ ] Integrate NLU service
- [ ] Add response caching (Redis)
- [ ] Implement rate limiting
- [ ] Write integration tests
- [ ] Update API documentation

**API Contract**:
```python
# Request
POST /nlu/extract-topic
Authorization: Bearer <service-token>
Content-Type: application/json

{
  "query": "Explain Newton's Third Law using basketball",
  "student_id": "user_abc123",
  "grade_level": 10,
  "subject_context": "Physics",
  "recent_topics": [
    {"topic_id": "topic_phys_mech_newton_1", "completed_at": "2025-11-20T10:00:00Z"},
    {"topic_id": "topic_phys_mech_newton_2", "completed_at": "2025-11-22T14:30:00Z"}
  ]
}

# Response (200 OK) - Clear Match
{
  "confidence": 0.98,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "subject": "Physics",
  "category": "Mechanics",
  "grade_level": 10,
  "clarification_needed": false,
  "out_of_scope": false,
  "reasoning": "Student explicitly asks about Newton's Third Law",
  "processing_time_ms": 1240
}

# Response (200 OK) - Needs Clarification
{
  "confidence": 0.65,
  "topic_id": null,
  "topic_name": null,
  "clarification_needed": true,
  "clarifying_questions": [
    {
      "question": "Are you interested in Newton's Law of Universal Gravitation?",
      "topic_id": "topic_phys_grav_universal",
      "topic_name": "Universal Gravitation"
    },
    {
      "question": "Or gravitational acceleration on Earth (g = 9.8 m/s²)?",
      "topic_id": "topic_phys_mech_acceleration",
      "topic_name": "Acceleration & Gravity"
    },
    {
      "question": "Or Einstein's General Relativity?",
      "topic_id": "topic_phys_modern_relativity",
      "topic_name": "General Relativity"
    }
  ],
  "out_of_scope": false,
  "reasoning": "Query 'gravity' has multiple valid interpretations"
}

# Response (200 OK) - Out of Scope
{
  "confidence": 0.99,
  "topic_id": null,
  "topic_name": null,
  "clarification_needed": false,
  "out_of_scope": true,
  "message": "I'm designed to help with STEM subjects like Physics, Chemistry, Biology, and Mathematics. Could you ask about one of these subjects?",
  "suggested_topics": [
    {"topic_id": "topic_phys_mech_newton_3", "name": "Newton's Third Law"},
    {"topic_id": "topic_chem_atoms_structure", "name": "Atomic Structure"},
    {"topic_id": "topic_bio_cells_structure", "name": "Cell Structure"}
  ],
  "reasoning": "Query not related to educational content"
}
```

**Time Estimate**: 4-6 hours

---

##### Story 1.1.3: Topic Mapping & Validation (3 points)

**As a** NLU Service
**I want to** validate extracted topics
**So that** results are accurate and grade-appropriate

**Tasks**:
- [ ] Implement fuzzy topic matching
  - Handle typos and variations
  - Synonym mapping ("gravity" → "gravitation")
- [ ] Grade-level filtering
  - Filter topics by grade appropriateness
  - Suggest prerequisite topics if too advanced
- [ ] Implement topic validation
  - Verify topic_id exists in database
  - Check prerequisites
- [ ] Add confidence scoring
  - Combine NLU confidence + fuzzy match score
  - Threshold for auto-acceptance (>0.85)
- [ ] Write unit tests (10 cases)

**Implementation**:
```python
from fuzzywuzzy import fuzz
from typing import List, Dict

class TopicValidator:
    def __init__(self, db):
        self.db = db
        self.synonym_map = {
            "gravity": ["gravitation", "gravitational force"],
            "speed": ["velocity", "rate of motion"],
            "atoms": ["atomic structure", "atomic theory"],
        }

    async def validate_and_match(
        self,
        topic_id: Optional[str],
        topic_name: str,
        grade_level: int
    ) -> Dict:
        """Validate topic and find best match if needed."""

        # If we have topic_id, validate it
        if topic_id:
            valid = await self._validate_topic_id(topic_id, grade_level)
            if valid:
                return {"valid": True, "topic_id": topic_id}

        # Fuzzy match by name
        all_topics = await self._get_grade_topics(grade_level)
        best_match = self._fuzzy_match(topic_name, all_topics)

        if best_match["score"] > 85:
            return {
                "valid": True,
                "topic_id": best_match["topic_id"],
                "match_score": best_match["score"],
                "matched_by": "fuzzy"
            }

        # Check synonyms
        synonym_match = await self._check_synonyms(topic_name, all_topics)
        if synonym_match:
            return {
                "valid": True,
                "topic_id": synonym_match["topic_id"],
                "matched_by": "synonym"
            }

        return {"valid": False, "reason": "No matching topic found"}

    def _fuzzy_match(
        self,
        query: str,
        topics: List[Dict]
    ) -> Dict:
        """Find best fuzzy match."""
        best_score = 0
        best_match = None

        for topic in topics:
            score = fuzz.ratio(
                query.lower(),
                topic["name"].lower()
            )
            if score > best_score:
                best_score = score
                best_match = topic

        return {
            "topic_id": best_match["id"] if best_match else None,
            "score": best_score
        }
```

**Time Estimate**: 4-6 hours

---

##### Story 1.1.4: Clarification Dialogue System (2 points)

**As a** student
**I want to** receive clarifying questions
**So that** I can specify exactly what I want to learn

**Tasks**:
- [ ] Design clarification question format
- [ ] Implement multi-turn dialogue tracking
- [ ] Store conversation context (Redis)
- [ ] Generate relevant clarifying questions
- [ ] Write integration test for full flow
- [ ] Update API documentation

**Clarification Flow**:
```
Student: "Teach me about energy"
    ↓
NLU: Ambiguous - needs clarification
    ↓
System: Shows 3 options:
  1. Kinetic Energy
  2. Potential Energy
  3. Conservation of Energy
    ↓
Student: Selects #2
    ↓
NLU: Returns topic_phys_energy_potential
    ↓
System: Initiates content generation
```

**Time Estimate**: 2-4 hours

---

#### Epic 1.2: Content Request Integration (8 points)

**Owner**: Full-Stack Engineer
**Priority**: P0
**Dependencies**: Sprint 1.1, Phase 2 (Student Service)

##### Story 1.2.1: Student Content Request Endpoint Enhancement (5 points)

**As a** student
**I want to** request content with natural language
**So that** I don't need to browse topics manually

**Tasks**:
- [ ] Update `POST /api/v1/students/content/request`
  - Call NLU service
  - Handle clarification dialogue
  - Initiate content generation
  - Return immediate response
- [ ] Implement request tracking
  - Create content_request record
  - Store correlation_id for pipeline tracking
  - Update request status through pipeline
- [ ] Handle clarification flow
  - Store conversation context
  - Multiple API calls for dialogue
- [ ] Add analytics tracking
- [ ] Write comprehensive tests
- [ ] Update API documentation

**Updated API Contract**:
```python
# Request
POST /api/v1/students/content/request
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "query": "Explain Newton's Third Law using basketball",
  "conversation_id": null  // null for new, or existing ID for clarification response
}

# Response (200 OK) - Clarification Needed
{
  "status": "clarification_needed",
  "conversation_id": "conv_abc123",
  "message": "I found multiple topics related to your query. Which would you like to learn about?",
  "options": [
    {
      "option_id": "opt_1",
      "topic_id": "topic_phys_grav_universal",
      "topic_name": "Universal Gravitation",
      "description": "Newton's law of gravitational attraction between objects",
      "grade_level": 10,
      "difficulty": "intermediate"
    },
    {
      "option_id": "opt_2",
      "topic_id": "topic_phys_mech_acceleration",
      "topic_name": "Gravitational Acceleration",
      "description": "How gravity accelerates objects on Earth (g = 9.8 m/s²)",
      "grade_level": 9,
      "difficulty": "beginner"
    }
  ],
  "expires_at": "2025-11-25T10:05:00Z"  // 5 minute TTL
}

# Request (Clarification Response)
POST /api/v1/students/content/request
Authorization: Bearer <student-token>
Content-Type: application/json

{
  "query": null,  // Not needed for clarification response
  "conversation_id": "conv_abc123",
  "option_id": "opt_1"
}

# Response (202 Accepted) - Generation Started
{
  "status": "generation_started",
  "cache_key": "def456ghi789",
  "topic_id": "topic_phys_grav_universal",
  "topic_name": "Universal Gravitation",
  "interest": "basketball",
  "request_id": "req_001",
  "correlation_id": "corr_xyz789",
  "estimated_fast_path_seconds": 10,
  "estimated_full_path_seconds": 180,
  "check_status_url": "/api/v1/content/def456ghi789",
  "created_at": "2025-11-25T10:00:00Z"
}

# Response (200 OK) - Cache Hit
{
  "status": "cache_hit",
  "cache_key": "def456ghi789",
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "interest": "basketball",
  "video_url": "https://cdn.vividly.edu/.../video.mp4",
  "audio_url": "https://cdn.vividly.edu/.../audio.mp3",
  "script_url": "https://storage.googleapis.com/.../script.json",
  "duration_seconds": 180,
  "generated_at": "2025-11-20T10:00:00Z",
  "views": 45
}
```

**Time Estimate**: 1 day

---

##### Story 1.2.2: Pipeline Initialization (3 points)

**As a** system
**I want to** initialize the content generation pipeline
**So that** all workers are triggered correctly

**Tasks**:
- [ ] Implement pipeline orchestrator
  - Create content_request record
  - Initialize request_stages
  - Publish to Pub/Sub topic
- [ ] Add correlation_id tracking
  - Generate unique correlation ID
  - Pass through entire pipeline
  - Enable end-to-end tracing
- [ ] Implement status tracking
  - Update content_request status
  - Track pipeline progress
  - Estimate completion time
- [ ] Write integration tests
- [ ] Update monitoring dashboards

**Pipeline Initialization**:
```python
from google.cloud import pubsub_v1
import uuid
from datetime import datetime

class PipelineOrchestrator:
    def __init__(self, db, pubsub_client):
        self.db = db
        self.publisher = pubsub_client

    async def initiate_generation(
        self,
        topic_id: str,
        student_id: str,
        interest: str,
        cache_key: str
    ) -> Dict:
        """Initiate content generation pipeline."""

        # Generate correlation ID for tracing
        correlation_id = f"corr_{uuid.uuid4().hex[:12]}"

        # Create content request record
        request = await self.db.execute("""
            INSERT INTO content_requests (
                student_id, topic_id, interest, cache_key,
                correlation_id, status, current_stage, progress_percentage
            ) VALUES ($1, $2, $3, $4, $5, 'nlu_complete', 'script_generation', 0)
            RETURNING id
        """, student_id, topic_id, interest, cache_key, correlation_id)

        request_id = request['id']

        # Initialize pipeline stages
        await self._initialize_stages(request_id)

        # Publish to script generation topic
        message_data = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "topic_id": topic_id,
            "student_id": student_id,
            "interest": interest,
            "cache_key": cache_key,
            "grade_level": await self._get_grade_level(student_id),
            "timestamp": datetime.utcnow().isoformat()
        }

        future = self.publisher.publish(
            "projects/vividly-dev-rich/topics/generate-script-dev",
            json.dumps(message_data).encode("utf-8"),
            correlation_id=correlation_id,
            priority="normal"
        )

        message_id = future.result()

        logger.info(f"Pipeline initiated: {correlation_id} (message: {message_id})")

        return {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "cache_key": cache_key,
            "message_id": message_id
        }
```

**Time Estimate**: 4-6 hours

---

#### Epic 1.3: Testing & Quality (5 points)

**Owner**: Both Engineers
**Priority**: P0

##### Story 1.3.1: NLU Quality Testing (3 points)

**Tasks**:
- [ ] Create test dataset (200 queries)
  - 50 clear queries → direct match
  - 50 ambiguous queries → clarification
  - 50 off-topic queries → rejection
  - 50 edge cases → various
- [ ] Implement automated testing
- [ ] Measure accuracy metrics
  - Precision, Recall, F1 score
  - Confidence calibration
- [ ] Create quality dashboard
- [ ] Document results

**Target Metrics**:
- Precision: >90%
- Recall: >85%
- F1 Score: >87%
- Avg confidence (correct): >0.85
- Avg confidence (incorrect): <0.60

**Time Estimate**: 4-6 hours

---

##### Story 1.3.2: Integration Testing (2 points)

**Tasks**:
- [ ] End-to-end flow tests
  - Student query → NLU → Cache check → Pipeline init
- [ ] Error scenario testing
  - Vertex AI timeout
  - Invalid responses
  - Database failures
- [ ] Performance testing
  - Concurrent requests
  - Response time benchmarks
- [ ] Write test documentation

**Time Estimate**: 2-4 hours

---

### Sprint 1 Success Criteria

**Must Have**:
- [ ] NLU service extracts topics with >85% accuracy
- [ ] Clarification dialogue working
- [ ] Content request endpoint enhanced
- [ ] Pipeline initialization functional
- [ ] Test coverage >75%
- [ ] Response time <5s (p95)

---

## Sprint 2: RAG & Script Generation

**Dates**: December 2-6, 2025
**Goal**: Build RAG system and personalized script generation
**Story Points**: 28

### Sprint 2 Backlog

#### Epic 2.1: RAG System (10 points)

**Owner**: AI/ML Engineer
**Priority**: P0
**Dependencies**: OER content ingested, Vector Search index built

##### Story 2.1.1: Vector Search Integration (5 points)

**As a** Script Generator
**I want to** retrieve relevant OER content
**So that** scripts are educationally accurate

**Tasks**:
- [ ] Set up Vertex AI Vector Search client
- [ ] Implement query embedding generation
- [ ] Implement Top-K retrieval (K=10)
- [ ] Add relevance filtering (score >0.7)
- [ ] Implement reranking
- [ ] Measure retrieval quality
- [ ] Write comprehensive tests

**Acceptance Criteria**:
- [x] Retrieves top 10 relevant chunks
- [x] Precision@10 >80%
- [x] Retrieval time <2s (p95)
- [x] Handles empty results gracefully
- [x] Test coverage >80%

**Implementation**:
```python
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

class RAGRetriever:
    def __init__(self):
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            "text-embedding-gecko@003"
        )
        self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name="projects/.../indexEndpoints/..."
        )

    async def retrieve_context(
        self,
        topic_id: str,
        grade_level: int,
        top_k: int = 10
    ) -> List[Dict]:
        """Retrieve relevant OER content for topic."""

        # Get topic metadata
        topic = await self._get_topic(topic_id)

        # Build search query
        query = self._build_query(topic, grade_level)

        # Generate query embedding
        query_embedding = await self._embed_query(query)

        # Search vector index
        results = await self.index_endpoint.find_neighbors(
            deployed_index_id="oer_embeddings_deployed",
            queries=[query_embedding],
            num_neighbors=top_k
        )

        # Filter by relevance score
        filtered = [
            r for r in results[0]
            if r.distance < 0.3  # Cosine distance < 0.3 = similarity > 0.7
        ]

        # Fetch full content
        context_chunks = await self._fetch_content(filtered)

        # Rerank by relevance
        reranked = self._rerank(context_chunks, query)

        return reranked[:10]

    async def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        embeddings = self.embedding_model.get_embeddings([query])
        return embeddings[0].values

    def _rerank(
        self,
        chunks: List[Dict],
        query: str
    ) -> List[Dict]:
        """Rerank chunks by relevance to query."""
        # Simple BM25-based reranking
        from rank_bm25 import BM25Okapi

        corpus = [chunk["text"] for chunk in chunks]
        bm25 = BM25Okapi([text.split() for text in corpus])

        scores = bm25.get_scores(query.split())

        # Sort by score
        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [chunk for chunk, score in ranked]
```

**Time Estimate**: 1 day

---

##### Story 2.1.2: Context Assembly & Optimization (5 points)

**Tasks**:
- [ ] Implement context window management
  - Fit within LearnLM token limits
  - Prioritize most relevant chunks
- [ ] Add metadata enrichment
  - Topic hierarchies
  - Prerequisites
  - Standards alignment
- [ ] Implement context caching
  - Cache assembled context by topic
  - Redis caching for hot topics
- [ ] Measure context quality
- [ ] Write tests

**Time Estimate**: 1 day

---

#### Epic 2.2: Script Generation Worker (13 points)

**Owner**: AI/ML Engineer
**Priority**: P0 (Critical Path)

##### Story 2.2.1: LearnLM Prompt Engineering (5 points)

**Tasks**:
- [ ] Design base script generation prompt
- [ ] Add interest personalization
- [ ] Few-shot examples (10 examples)
- [ ] Output format (JSON storyboard)
- [ ] Test with 20 topics
- [ ] Iterate based on quality
- [ ] Document prompt decisions

**Script Generation Prompt**:
```python
SCRIPT_PROMPT = """You are an expert educational content creator for Vividly, specializing in personalized STEM learning.

Task: Create a 2-3 minute personalized video lesson script.

Topic: {topic_name}
Subject: {subject}
Grade Level: {grade_level}
Student Interest: {interest}

Educational Content (from OER):
{rag_context}

Requirements:
1. PRIMARY: Explain {topic_name} using {interest} as the main analogy/example
2. Keep language appropriate for grade {grade_level}
3. Use engaging, conversational tone (like talking to a friend)
4. Break into 6-8 scenes (20-30 seconds each)
5. Include visual descriptions for each scene
6. Ensure educational accuracy using the OER content above
7. Include a brief recap at the end
8. Make the connection between {interest} and {topic_name} crystal clear

Output Format (JSON):
{{
  "title": "Newton's Third Law: The Basketball Perspective",
  "duration_estimate": 150,
  "scenes": [
    {{
      "scene_number": 1,
      "duration": 25,
      "narration": "Imagine you're on the basketball court, about to take that perfect shot...",
      "visual_description": "Basketball player in shooting stance, ball in hands, focused expression",
      "educational_content": "Introduction to action-reaction pairs in everyday motion",
      "key_concept": "forces come in pairs"
    }},
    {{
      "scene_number": 2,
      "duration": 30,
      "narration": "When you push the ball forward with your hands, something amazing happens...",
      "visual_description": "Close-up of hands pushing basketball, with force arrows showing direction",
      "educational_content": "Newton's Third Law: For every action, there is an equal and opposite reaction",
      "key_concept": "action-reaction pairs are equal and opposite"
    }},
    ...
  ],
  "key_takeaways": [
    "Action-reaction pairs are equal in magnitude and opposite in direction",
    "Forces always come in pairs - you can't have one without the other",
    "In basketball, every push creates an equal push back"
  ],
  "prerequisites": ["Newton's First Law", "Newton's Second Law"],
  "next_topics": ["Momentum", "Collisions"]
}}

Few-Shot Examples:

Example 1:
Topic: Newton's Third Law
Interest: Basketball
Grade: 10

Output: {{
  "title": "Newton's Third Law: The Basketball Perspective",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "Picture yourself on the court, ready to make that game-winning shot. But have you ever wondered about the physics happening in that moment?",
      "visual_description": "Basketball court, player in shooting stance",
      "educational_content": "Introduction to forces in motion",
      "key_concept": "forces govern all motion"
    }},
    ...
  ]
}}

Example 2:
Topic: Photosynthesis
Interest: Cooking
Grade: 9

Output: {{
  "title": "Photosynthesis: Nature's Kitchen",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "Think of plants as master chefs with the ultimate solar-powered kitchen...",
      "visual_description": "Plant leaf with sunlight, shown as a kitchen scene",
      "educational_content": "Plants convert light energy into chemical energy",
      "key_concept": "energy transformation"
    }},
    ...
  ]
}}

Now create a script:
Topic: {topic_name}
Interest: {interest}
Grade Level: {grade_level}
"""
```

**Time Estimate**: 1 day

---

##### Story 2.2.2: Script Worker Cloud Function (5 points)

**Tasks**:
- [ ] Implement Cloud Function
- [ ] Pub/Sub trigger
- [ ] RAG integration
- [ ] LearnLM integration
- [ ] Script validation
- [ ] GCS storage
- [ ] Publish to next topics
- [ ] Write tests

**Worker Implementation**:
```python
import functions_framework
import json
import base64
from google.cloud import pubsub_v1, storage
from .rag_retriever import RAGRetriever
from .script_generator import ScriptGenerator

@functions_framework.cloud_event
def generate_script(cloud_event):
    """Generate personalized script using RAG + LearnLM."""

    # Parse Pub/Sub message
    data = base64.b64decode(cloud_event.data["message"]["data"])
    request = json.loads(data)

    request_id = request["request_id"]
    correlation_id = request["correlation_id"]
    topic_id = request["topic_id"]
    interest = request["interest"]
    grade_level = request["grade_level"]
    cache_key = request["cache_key"]

    logger.info(f"[{correlation_id}] Starting script generation for {topic_id}")

    try:
        # Update status
        await update_request_status(
            request_id,
            "script_generation",
            "in_progress",
            10
        )

        # 1. RAG Retrieval
        logger.info(f"[{correlation_id}] Retrieving OER content...")
        retriever = RAGRetriever()
        context = await retriever.retrieve_context(
            topic_id=topic_id,
            grade_level=grade_level
        )

        await update_request_status(request_id, "script_generation", "in_progress", 30)

        # 2. Generate script with LearnLM
        logger.info(f"[{correlation_id}] Generating script with LearnLM...")
        generator = ScriptGenerator()
        script = await generator.generate(
            topic_id=topic_id,
            interest=interest,
            grade_level=grade_level,
            context=context
        )

        await update_request_status(request_id, "script_generation", "in_progress", 70)

        # 3. Validate script
        logger.info(f"[{correlation_id}] Validating script...")
        validation = validate_script(script)
        if not validation["valid"]:
            raise ValueError(f"Invalid script: {validation['errors']}")

        # 4. Save to GCS
        logger.info(f"[{correlation_id}] Saving script to GCS...")
        script_url = await save_script_to_gcs(cache_key, script)

        await update_request_status(request_id, "script_generation", "completed", 100)

        # 5. Trigger audio generation (parallel with video)
        logger.info(f"[{correlation_id}] Triggering audio generation...")
        await publish_to_pubsub("generate-audio-dev", {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "cache_key": cache_key,
            "script_url": script_url,
            "script": script
        })

        # 6. Trigger video generation (parallel)
        logger.info(f"[{correlation_id}] Triggering video generation...")
        await publish_to_pubsub("generate-video-dev", {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "cache_key": cache_key,
            "script_url": script_url,
            "script": script
        })

        # 7. Update database
        await update_content_metadata(cache_key, {
            "status": "script_complete",
            "script_url": script_url,
            "script_generated_at": datetime.utcnow().isoformat()
        })

        logger.info(f"[{correlation_id}] Script generation complete")

        return {"status": "success", "cache_key": cache_key}

    except Exception as e:
        logger.error(f"[{correlation_id}] Script generation failed: {e}")

        await update_request_status(
            request_id,
            "script_generation",
            "failed",
            error=str(e)
        )

        # Publish to DLQ
        await publish_to_pubsub("generate-script-dev-dlq", request)

        raise
```

**Time Estimate**: 1 day

---

##### Story 2.2.3: Script Validation & Quality (3 points)

**Tasks**:
- [ ] Implement validation rules
  - JSON schema validation
  - Content length checks
  - Educational accuracy checks
- [ ] Add quality scoring
  - Engagement score
  - Clarity score
  - Interest integration score
- [ ] Implement AI safety guardrails
  - Profanity filter
  - Bias detection
  - Inappropriate content filter
- [ ] Write tests

**Validation Rules**:
```python
import jsonschema
from typing import Dict, List

SCRIPT_SCHEMA = {
    "type": "object",
    "required": ["title", "duration_estimate", "scenes", "key_takeaways"],
    "properties": {
        "title": {"type": "string", "minLength": 10, "maxLength": 100},
        "duration_estimate": {"type": "integer", "minimum": 90, "maximum": 240},
        "scenes": {
            "type": "array",
            "minItems": 6,
            "maxItems": 8,
            "items": {
                "type": "object",
                "required": ["scene_number", "duration", "narration", "visual_description"],
                "properties": {
                    "scene_number": {"type": "integer"},
                    "duration": {"type": "integer", "minimum": 15, "maximum": 45},
                    "narration": {"type": "string", "minLength": 50, "maxLength": 250},
                    "visual_description": {"type": "string", "minLength": 20, "maxLength": 200}
                }
            }
        },
        "key_takeaways": {
            "type": "array",
            "minItems": 2,
            "maxItems": 5
        }
    }
}

def validate_script(script: Dict) -> Dict:
    """Validate generated script."""
    errors = []

    # Schema validation
    try:
        jsonschema.validate(script, SCRIPT_SCHEMA)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation failed: {e.message}")

    # Content validation
    total_duration = sum(scene["duration"] for scene in script["scenes"])
    if abs(total_duration - script["duration_estimate"]) > 30:
        errors.append("Duration mismatch between scenes and estimate")

    # Check for profanity
    profanity_check = check_profanity(script)
    if profanity_check["contains_profanity"]:
        errors.append(f"Profanity detected: {profanity_check['words']}")

    # Check educational content
    if not has_educational_content(script):
        errors.append("Insufficient educational content")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
```

**Time Estimate**: 4-6 hours

---

#### Epic 2.3: Testing & Quality (5 points)

##### Story 2.3.1: Script Quality Testing (3 points)

**Tasks**:
- [ ] Generate 50 test scripts
  - 10 topics × 5 interests
- [ ] Manual quality review
- [ ] Automated quality checks
- [ ] Calculate quality metrics
- [ ] Document findings

**Target Metrics**:
- Educational Accuracy: >95%
- Interest Integration: >85%
- Engagement Score: >4/5
- Clarity Score: >4/5

**Time Estimate**: 4-6 hours

---

##### Story 2.3.2: Integration Testing (2 points)

**Tasks**:
- [ ] End-to-end pipeline test
  - NLU → Cache → Script Generation
- [ ] Performance testing
  - Script generation time <45s (p95)
- [ ] Error scenario testing
- [ ] Write documentation

**Time Estimate**: 2-4 hours

---

### Sprint 2 Success Criteria

**Must Have**:
- [ ] RAG retrieves relevant content (precision >80%)
- [ ] Scripts are educationally accurate (>95%)
- [ ] Scripts integrate student interests (>85%)
- [ ] Script generation <45s (p95)
- [ ] Test coverage >75%

---

## Sprint 3: Audio & Video Pipeline

**Dates**: December 9-13, 2025
**Goal**: Complete audio and video generation, full pipeline operational
**Story Points**: 27

### Sprint 3 Backlog

#### Epic 3.1: Audio Worker (8 points)

**Owner**: Full-Stack Engineer
**Priority**: P0

##### Story 3.1.1: Cloud TTS Integration (5 points)

**Tasks**:
- [ ] Set up Cloud Text-to-Speech client
- [ ] Select appropriate voice
  - Neural2 voices for quality
  - Age-appropriate (teenage/young adult)
  - Professional and clear
- [ ] Implement audio generation
  - Parse script narration
  - Generate audio for each scene
  - Concatenate scenes
- [ ] Add audio effects
  - Background music (optional)
  - Fade in/out
  - Normalization
- [ ] Save to GCS
- [ ] Write tests

**Voice Selection**:
- `en-US-Neural2-J` - Young adult male (recommended)
- `en-US-Neural2-F` - Young adult female
- Speaking rate: 1.0 (normal)
- Pitch: 0.0 (neutral)

**Implementation**:
```python
from google.cloud import texttospeech_v1 as tts
from pydub import AudioSegment
import io

class AudioGenerator:
    def __init__(self):
        self.client = tts.TextToSpeechClient()

    async def generate_audio(
        self,
        script: Dict,
        cache_key: str
    ) -> str:
        """Generate audio from script."""

        # Combine all narrations
        full_narration = self._build_narration(script)

        # Configure voice
        voice = tts.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-J",
            ssml_gender=tts.SsmlVoiceGender.MALE
        )

        # Configure audio
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0,
            sample_rate_hertz=24000,
            effects_profile_id=["headphone-class-device"]
        )

        # Generate audio
        input_text = tts.SynthesisInput(text=full_narration)

        response = self.client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )

        # Save to GCS
        audio_url = await self._save_audio(cache_key, response.audio_content)

        return audio_url

    def _build_narration(self, script: Dict) -> str:
        """Build full narration with pauses."""
        parts = []

        for scene in script["scenes"]:
            narration = scene["narration"]
            # Add SSML pause between scenes
            parts.append(f"{narration}<break time='1s'/>")

        return " ".join(parts)
```

**Time Estimate**: 1 day

---

##### Story 3.1.2: Audio Worker Cloud Function (3 points)

**Tasks**:
- [ ] Implement Cloud Function
- [ ] Pub/Sub trigger
- [ ] Audio generation
- [ ] GCS storage
- [ ] Update database
- [ ] Notify frontend (Fast Path)
- [ ] Write tests

**Worker Implementation**:
```python
@functions_framework.cloud_event
def generate_audio(cloud_event):
    """Generate audio narration using Cloud TTS."""

    data = base64.b64decode(cloud_event.data["message"]["data"])
    request = json.loads(data)

    request_id = request["request_id"]
    correlation_id = request["correlation_id"]
    cache_key = request["cache_key"]
    script = request["script"]

    logger.info(f"[{correlation_id}] Starting audio generation")

    try:
        await update_request_status(request_id, "audio_generation", "in_progress", 10)

        # Generate audio
        generator = AudioGenerator()
        audio_url = await generator.generate_audio(script, cache_key)

        await update_request_status(request_id, "audio_generation", "completed", 100)

        # Update database
        await update_content_metadata(cache_key, {
            "status": "audio_complete",
            "audio_url": audio_url,
            "audio_generated_at": datetime.utcnow().isoformat()
        })

        # Notify student (Fast Path complete)
        await publish_to_pubsub("content-ready-dev", {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "cache_key": cache_key,
            "status": "fast_path_ready",
            "audio_url": audio_url,
            "script_url": request["script_url"]
        })

        logger.info(f"[{correlation_id}] Audio generation complete")

        return {"status": "success", "audio_url": audio_url}

    except Exception as e:
        logger.error(f"[{correlation_id}] Audio generation failed: {e}")
        await update_request_status(request_id, "audio_generation", "failed", error=str(e))
        await publish_to_pubsub("generate-audio-dev-dlq", request)
        raise
```

**Time Estimate**: 4-6 hours

---

#### Epic 3.2: Video Worker (10 points)

**Owner**: AI/ML Engineer + Full-Stack Engineer (pair)
**Priority**: P0 (Critical Path)

##### Story 3.2.1: Nano Banana Integration (5 points)

**Tasks**:
- [ ] Set up Nano Banana API client
- [ ] Implement video generation request
- [ ] Poll for completion
- [ ] Handle timeouts
- [ ] Implement circuit breaker
- [ ] Download completed video
- [ ] Write tests

**Circuit Breaker Integration**:
```python
from app.services.circuit_breaker import nano_banana_breaker
import httpx

class VideoGenerator:
    def __init__(self):
        self.api_key = get_secret("nano-banana-api-key")
        self.api_url = "https://api.nanobanana.com/v1"

    async def generate_video(
        self,
        script: Dict,
        audio_url: str,
        cache_key: str
    ) -> str:
        """Generate video using Nano Banana API."""

        # Prepare payload
        payload = {
            "storyboard": self._format_storyboard(script),
            "audio_url": audio_url,
            "quality": "1080p",
            "style": "educational",
            "duration": script["duration_estimate"]
        }

        # Call API with circuit breaker
        video_job_id = await nano_banana_breaker.call(
            self._create_video_job,
            payload
        )

        # Poll for completion (max 10 minutes)
        video_url = await self._poll_completion(
            video_job_id,
            timeout=600
        )

        # Download and save to GCS
        final_url = await self._download_and_store(video_url, cache_key)

        return final_url

    async def _create_video_job(self, payload: Dict) -> str:
        """Create video generation job."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/videos",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["job_id"]

    async def _poll_completion(
        self,
        job_id: str,
        timeout: int = 600
    ) -> str:
        """Poll for video completion."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = await self._check_status(job_id)

            if status["status"] == "completed":
                return status["video_url"]
            elif status["status"] == "failed":
                raise Exception(f"Video generation failed: {status['error']}")

            # Wait before next poll (exponential backoff)
            wait_time = min(30, 5 * (1.5 ** (time.time() - start_time) // 30))
            await asyncio.sleep(wait_time)

        raise TimeoutError(f"Video generation timed out after {timeout}s")
```

**Time Estimate**: 1 day

---

##### Story 3.2.2: Video Worker Cloud Function (5 points)

**Tasks**:
- [ ] Implement Cloud Function
- [ ] Pub/Sub trigger
- [ ] Video generation
- [ ] GCS storage
- [ ] CDN cache warming
- [ ] Update database
- [ ] Notify frontend (Full Path)
- [ ] Write tests

**Time Estimate**: 1 day

---

#### Epic 3.3: Pipeline Completion & Monitoring (9 points)

##### Story 3.3.1: Content Ready Notification (3 points)

**Tasks**:
- [ ] Implement notification worker
- [ ] Handle Fast Path notification
- [ ] Handle Full Path notification
- [ ] Update frontend via polling/SSE
- [ ] Send email notification (optional)
- [ ] Write tests

**Time Estimate**: 4-6 hours

---

##### Story 3.3.2: End-to-End Testing (3 points)

**Tasks**:
- [ ] Complete pipeline test
  - Student query → Video ready
- [ ] Measure end-to-end timing
  - Fast Path: <10s target
  - Full Path: <3min target
- [ ] Test all error scenarios
- [ ] Load testing (10 concurrent)
- [ ] Write documentation

**Time Estimate**: 4-6 hours

---

##### Story 3.3.3: Monitoring & Observability (3 points)

**Tasks**:
- [ ] Add comprehensive logging
  - Correlation ID in all logs
  - Structured logging (JSON)
- [ ] Add metrics
  - Pipeline stage durations
  - Success/failure rates
  - Queue depths
- [ ] Create monitoring dashboard
  - Real-time pipeline status
  - Error rates by stage
  - Performance charts
- [ ] Set up alerts
  - Pipeline failures
  - Slow generations
  - API errors

**Time Estimate**: 4-6 hours

---

### Sprint 3 Success Criteria

**Must Have**:
- [ ] Audio generation working (<15s)
- [ ] Video generation working (<3min)
- [ ] Fast Path delivers in <10s (p95)
- [ ] Full Path delivers in <3min (p95)
- [ ] Pipeline success rate >95%
- [ ] End-to-end monitoring operational

---

## AI Quality Standards

### Script Quality Rubric

| Dimension | Weight | Criteria | Target Score |
|-----------|--------|----------|--------------|
| Educational Accuracy | 30% | Factually correct, aligned with OER content | >4.5/5 |
| Interest Integration | 25% | Natural use of student interest as analogy | >4/5 |
| Engagement | 20% | Conversational tone, relatable examples | >4/5 |
| Clarity | 15% | Clear explanations, appropriate language | >4/5 |
| Structure | 10% | Logical flow, good pacing | >4/5 |

**Overall Target**: >4.2/5 (84%)

### Human Review Process

**Week 1 (Sprint 1)**:
- Review 100% of generated scripts
- Build quality baseline
- Refine prompts

**Week 2 (Sprint 2)**:
- Review 50% of scripts
- Focus on edge cases
- Validate improvements

**Week 3 (Sprint 3)**:
- Review 25% of scripts
- Spot check only
- Production confidence

---

## Testing Strategy

### Unit Testing

**NLU Service**:
- Topic extraction accuracy
- Confidence calibration
- Error handling
- Edge cases

**RAG Retriever**:
- Retrieval precision/recall
- Relevance filtering
- Context assembly
- Performance

**Script Generator**:
- Prompt templating
- Output validation
- Quality scoring
- Error recovery

**Workers**:
- Message parsing
- API integration
- Error handling
- Retry logic

**Target Coverage**: >75% for AI/ML code, >80% for infrastructure

### Integration Testing

**End-to-End Flows**:
1. Student query → NLU → Cache miss → Pipeline init
2. Pipeline init → Script gen → Audio gen → Video gen
3. Fast Path delivery (<10s)
4. Full Path delivery (<3min)
5. Cache hit (instant delivery)

**Error Scenarios**:
- Vertex AI timeout
- Nano Banana failure
- GCS storage error
- Database connection loss
- Pub/Sub message loss

### Quality Testing

**AI Quality**:
- 200-query NLU test set
- 50-script quality review
- Human evaluation (5 reviewers)
- A/B testing framework

**Performance**:
- Load testing (100 concurrent requests)
- Latency benchmarks (p50, p95, p99)
- Resource utilization
- Cost per generation

---

## Success Metrics

### Phase 3 Completion Criteria

**Functional**:
- [ ] NLU accuracy >85%
- [ ] RAG precision >80%
- [ ] Script quality >4/5
- [ ] Audio quality acceptable
- [ ] Video generation >95% success rate

**Performance**:
- [ ] NLU response <5s (p95)
- [ ] Script generation <45s (p95)
- [ ] Audio generation <15s (p95)
- [ ] Video generation <3min (p95)
- [ ] Fast Path <10s (p95)
- [ ] Full Path <3min (p95)

**Quality**:
- [ ] Educational accuracy >95%
- [ ] Interest integration >85%
- [ ] Test coverage >75%
- [ ] Pipeline success rate >95%

**Operational**:
- [ ] All workers deployed
- [ ] Monitoring operational
- [ ] Alerting configured
- [ ] Documentation complete

---

## Conclusion

Phase 3 delivers the complete AI content generation pipeline, the most critical and complex component of the Vividly MVP. With careful prompt engineering, quality validation, and robust error handling, we'll create a system that generates educationally accurate, engaging, and personalized content at scale.

**Next Steps After Phase 3**:
- Phase 4: Frontend Application (parallel with Phase 3)
- Phase 5: Integration & Testing
- Phase 6: Pilot Deployment

---

**Document Control**:
- **Author**: Technical Lead
- **Date**: October 28, 2025
- **Version**: 1.0
- **Status**: Ready to Execute (after Phase 2)
- **Dependencies**: Phase 2 complete, OER content ingested
