# RAG Pipeline Architecture

## Overview
This document describes the data flow for the educational content pipeline, from OpenStax ingestion through personalized video generation.

## Data Flow Pipeline

### 1. Source Content Ingestion
- **Sources**: OpenStax.org and other OER (Open Educational Resources)
- **Storage**: GCS bucket `vividly-dev-rich-dev-oer-content`
- **Structure**: Organized by subject → chapter → section hierarchy
- **Status**: Not yet implemented

### 2. Content Processing & Chunking
- **Purpose**: Break raw educational content into semantic chunks
- **Chunk Size**: Paragraph-level for conceptual understanding
- **Preservation**: Maintain context (headings, diagrams, examples)
- **Metadata**: Subject, grade level, standards alignment
- **Storage**: Database as Topics with hierarchical structure (app/models/topic.py)

### 3. Vector Embedding Generation
- **Method**: Convert chunks to vector embeddings using Google's embedding models
- **Purpose**: Enable semantic similarity search
- **Storage**: Vertex AI Vector Search or similar vector database
- **Status**: Infrastructure ready, implementation pending

### 4. Student Query → RAG Retrieval Flow

```
Student Query: "Explain Newton's Third Law"
    ↓
NLU Service (app/services/nlu_service.py)
  - Extract topic intent
  - Identify key concepts
  - Determine grade level context
    ↓
RAG Service (app/services/rag_service.py)
  - Convert query to embedding
  - Semantic search in vector DB
  - Retrieve top-k relevant chunks (3-5 pieces)
  - Include metadata: source, grade level, difficulty
    ↓
Retrieved Context:
  - OpenStax Physics Chapter 4.3
  - Newton's laws explanation
  - Real-world examples
  - Diagrams/visuals metadata
```

### 5. Interest Selection & Content Generation

**IMPORTANT DESIGN DECISIONS:**

#### Interest Selection Strategy
When combining RAG content with student personalization, we pass **ALL** of the student's interests to the LLM along with the RAG content. The LLM determines which **SINGLE** interest best aligns with the specific topic to create the most meaningful example.

#### Content Caching by Interest
Generated content is cached by the combination of:
- `topic_id`: The educational topic/concept
- `grade_level`: Student's grade level
- `selected_interest`: The specific interest used in the example

This enables **content reuse across students**: If another student requests the same topic at the same grade level and has the same interest in their profile, we serve the cached content instead of regenerating.

**Example:**
- Student A (Grade 10, interests: ["basketball", "music"]) requests "Newton's Third Law"
- LLM selects "basketball" as best fit
- Content generated with basketball examples, cached as: `topic_phys_mech_newton_3 + grade_10 + basketball`
- Student B (Grade 10, interests: ["basketball", "gaming"]) requests same topic
- System finds cached content with matching topic + grade + interest ("basketball")
- Serves existing content immediately, no regeneration needed

**Flow:**
```
RAG Content + ALL Student Interests (["basketball", "music", "cooking", "gaming"])
    ↓
Content Cache Check
  - Query: topic_id + grade_level + ANY(student_interests)
  - If match found: Return cached content ✓
  - If no match: Proceed to generation ↓
    ↓
Script Generation (Gemini 1.5 Pro)
  - LLM analyzes the topic and student interests
  - Selects THE SINGLE BEST interest for this specific concept
  - Example: For Newton's Third Law, selects "basketball"
    (forces during dribbling/shooting)
  - Generates personalized explanation using selected interest
  - Grade-appropriate language
  - 2-3 minute script
  - Returns: {script, selected_interest}
    ↓
Text-to-Speech (Google Cloud TTS)
  - Natural voice narration
  - Proper pacing and emphasis
    ↓
Video Rendering (app/services/video_service.py)
  - Combine audio + visuals
  - Add relevant diagrams from OER content
  - Generate captions
    ↓
Storage & Caching
  - Store in GCS: vividly-dev-rich-dev-generated-content
  - Cache metadata in ContentMetadata table:
    - topic_id
    - grade_level
    - selected_interest (the one used in examples)
    - video_url, audio_url, script_text
  - Enable future reuse for students with matching criteria
```

**Implementation Note:**
The script generation service should receive:
- `rag_content`: Retrieved educational content chunks
- `student_interests`: List[str] of ALL student interests
- `grade_level`: Student's grade level
- `topic_id`: Canonical topic identifier

The LLM prompt should instruct it to:
1. Analyze the topic/concept being taught
2. Review all available student interests
3. **Select EXACTLY ONE interest** that creates the most natural, meaningful connection
4. Generate examples using ONLY the selected interest
5. **Return the selected interest** along with the generated script

The content caching service should:
1. Before generation: Query for existing content matching `topic_id + grade_level + ANY(student_interests)`
2. After generation: Store content with `topic_id + grade_level + selected_interest` as composite cache key
3. Track cache hit rate for optimization insights

### 6. Key Database Tables

**Topics** (app/models/topic.py)
- Hierarchical curriculum structure
- Maps to OpenStax chapters/sections
- Stores topic_id, name, subject, grade_level

**ContentMetadata** (app/models/content_metadata.py)
- Generated content cache
- **Composite cache key**: topic_id + grade_level + interest_id
- Links to GCS storage (video_url, audio_url, script_content)
- Tracks views, completions
- **Schema Requirements**:
  - `topic_id`: FK to topics table
  - `grade_level`: Integer (9-12) - **NEEDS TO BE ADDED**
  - `interest_id`: FK to interests table (the single interest used in examples)
  - `video_url`, `audio_url`, `script_content`: Generated content URLs
  - `generation_metadata`: JSON field for additional context
  - `view_count`, `completion_count`: Usage metrics

**StudentProgress** (app/models/progress.py)
- Tracks what students have watched
- Completion percentage
- Watch time analytics

**Database Schema Changes Needed**:
1. Add `grade_level` column to `content_metadata` table
2. Create composite index on `(topic_id, grade_level, interest_id)` for fast cache lookups
3. Ensure `interest_id` properly references the single selected interest

## Missing Infrastructure Components

### 1. OpenStax Ingestion Pipeline
- Web scraper for openstax.org
- Parser for textbook structure (XML/HTML)
- Metadata extractor (subject, grade, standards)

### 2. Chunking Service
- Semantic text chunking algorithm
- Preserve context (headings, equations, diagrams)
- Generate chunk embeddings

### 3. Vector Database Setup
- Vertex AI Vector Search or Pinecone
- Index management
- Embedding model integration

### 4. RAG Service Enhancement (app/services/rag_service.py)
- Currently has stub/mock implementation
- Needs vector search integration
- Needs re-ranking logic
- Hybrid search (semantic + keyword)

## Architecture Diagram

```
OpenStax Content → Ingestion → Chunking → Embedding → Vector DB
                                                           ↓
Student Query → NLU → Query Embedding → Vector Search → Top-K Chunks
                                                           ↓
                            RAG Context + ALL Student Interests
                                                           ↓
                            Gemini (Interest Selection + Script Generation)
                                                           ↓
                            TTS → Video → Cache → Student
```

## Implementation Questions

### 1. Chunking Strategy
- Fixed token windows vs semantic boundaries?
- How to handle equations, diagrams, tables?

### 2. Vector DB Choice
- Vertex AI Vector Search (GCP native)?
- Pinecone (managed)?
- PostgreSQL pgvector (self-hosted)?

### 3. Embedding Model
- Google's textembedding-gecko?
- OpenAI ada-002?
- Domain-specific fine-tuned model?

### 4. Ingestion Frequency
- One-time batch import?
- Incremental updates?
- How to version content?

### 5. Metadata Preservation
- Standards alignment (Common Core, NGSS)?
- Prerequisites/dependencies?
- Difficulty ratings?

## Related Files
- Content Generation Service: `app/services/content_generation_service.py`
- Script Generation Service: `app/services/script_generation_service.py`
- RAG Service: `app/services/rag_service.py`
- NLU Service: `app/services/nlu_service.py`
- Topic Model: `app/models/topic.py`
- Content Metadata Model: `app/models/content_metadata.py`

## Last Updated
2025-11-01
