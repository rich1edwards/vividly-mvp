# Vividly Vector Database Schema

**Platform:** Vertex AI Vector Search
**Version:** 1.0
**Last Updated:** October 27, 2025

## Table of Contents

1. [Overview](#overview)
2. [Vector Embedding Strategy](#vector-embedding-strategy)
3. [Index Configuration](#index-configuration)
4. [Document Schema](#document-schema)
5. [Ingestion Pipeline](#ingestion-pipeline)
6. [Query Patterns](#query-patterns)
7. [Performance Optimization](#performance-optimization)
8. [Maintenance](#maintenance)

---

## Overview

The vector database powers Vividly's Retrieval-Augmented Generation (RAG) system by storing semantic embeddings of Open Educational Resources (OER) content. This enables the AI to retrieve relevant educational material when generating personalized scripts.

### Purpose

- **Semantic Search**: Find relevant educational content beyond keyword matching
- **Context Enrichment**: Provide LearnLM with factual, curriculum-aligned information
- **Source Attribution**: Track which OER materials contributed to generated content

### Technology Stack

- **Vector Store**: Vertex AI Vector Search
- **Embedding Model**: text-embedding-gecko@003 (768 dimensions)
- **Distance Metric**: Cosine similarity
- **Source Data**: OpenStax textbooks (.docx format)

---

## Vector Embedding Strategy

### Chunking Strategy

OER content is split into semantic chunks optimized for retrieval:

| Chunk Type | Size | Use Case |
|------------|------|----------|
| **Concept Chunk** | 200-400 tokens | Single concepts (e.g., definition of Newton's 3rd Law) |
| **Example Chunk** | 300-600 tokens | Worked examples and problems |
| **Section Chunk** | 500-1000 tokens | Complete subsections with context |

### Chunking Rules

1. **Preserve Semantic Boundaries**
   - Don't split mid-sentence
   - Keep equations with surrounding explanation
   - Maintain figure references with captions

2. **Overlap Strategy**
   - 50-token overlap between consecutive chunks
   - Prevents context loss at boundaries

3. **Minimum Viable Content**
   - Each chunk must be self-explanatory
   - Include topic context in metadata

### Embedding Process

```python
from vertexai.language_models import TextEmbeddingModel

model = TextEmbeddingModel.from_pretrained("text-embedding-gecko@003")

def embed_text(text: str) -> list[float]:
    """Generate 768-dimensional embedding vector."""
    embeddings = model.get_embeddings([text])
    return embeddings[0].values
```

**Batch Size**: 250 texts per API call
**Cost**: ~$0.00001 per 1000 characters

---

## Index Configuration

### Vertex AI Vector Search Index

```python
# Index Configuration
INDEX_CONFIG = {
    "display_name": "vividly-oer-embeddings-index",
    "description": "OER content embeddings for RAG retrieval",
    "metadata": {
        "contentsDeltaUri": "gs://vividly-mvp-vector-db/embeddings",
        "config": {
            "dimensions": 768,
            "approximateNeighborsCount": 150,
            "distanceMeasureType": "COSINE_DISTANCE",
            "algorithmConfig": {
                "treeAhConfig": {
                    "leafNodeEmbeddingCount": 1000,
                    "leafNodesToSearchPercent": 7
                }
            }
        }
    }
}
```

### Index Parameters Explained

- **dimensions**: 768 (matches text-embedding-gecko@003)
- **approximateNeighborsCount**: 150 (maximum neighbors to return)
- **distanceMeasureType**: COSINE_DISTANCE (best for text similarity)
- **algorithmConfig**: Tree-AH (Approximate Hierarchical)
  - **leafNodeEmbeddingCount**: 1000 (vectors per leaf node)
  - **leafNodesToSearchPercent**: 7% (recall vs latency tradeoff)

### Index Endpoint

```python
ENDPOINT_CONFIG = {
    "display_name": "vividly-oer-endpoint",
    "description": "Query endpoint for OER embeddings",
    "public_endpoint_enabled": False,  # VPC-only access
    "deployed_index": {
        "id": "vividly_oer_deployed",
        "index": "projects/{project_id}/locations/us-central1/indexes/{index_id}",
        "dedicated_resources": {
            "machine_type": "e2-standard-2",
            "min_replica_count": 1,
            "max_replica_count": 3
        }
    }
}
```

---

## Document Schema

### Vector Record Structure

Each embedded chunk is stored with this structure:

```json
{
  "id": "chunk_openstax_phys_newton_003_0042",
  "embedding": [0.0234, -0.0456, 0.0789, ...],  // 768 floats
  "restricts": [
    {"namespace": "source", "allow_list": ["openstax"]},
    {"namespace": "subject", "allow_list": ["physics"]},
    {"namespace": "grade_level", "allow_list": ["9", "10", "11", "12"]}
  ],
  "crowding_tag": "openstax_phys_newton",
  "numeric_restricts": [
    {"namespace": "difficulty_level", "value_int": 3}
  ]
}
```

### Metadata Stored Separately (Cloud SQL)

Due to Vertex AI Vector Search size limits, full metadata is stored in PostgreSQL:

```sql
CREATE TABLE vector_metadata (
    chunk_id VARCHAR(100) PRIMARY KEY,

    -- Source Information
    source_id VARCHAR(100) NOT NULL,  -- 'openstax_physics_v1'
    source_type VARCHAR(50) NOT NULL,  -- 'textbook', 'article'

    -- Topic Mapping
    topic_id VARCHAR(100) NOT NULL REFERENCES topics(id),
    subject VARCHAR(50) NOT NULL,

    -- Content
    chunk_text TEXT NOT NULL,
    chunk_type VARCHAR(50),  -- 'concept', 'example', 'section'

    -- Context
    chapter_title VARCHAR(255),
    section_title VARCHAR(255),
    subsection_title VARCHAR(255),
    page_number INTEGER,

    -- Figures/Equations
    contains_figure BOOLEAN DEFAULT false,
    figure_captions TEXT[],
    contains_equation BOOLEAN DEFAULT false,
    equation_labels TEXT[],

    -- Quality
    token_count INTEGER,
    difficulty_level INTEGER,  -- 1-5

    -- GCS Reference
    original_document_url VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vector_metadata_topic ON vector_metadata(topic_id);
CREATE INDEX idx_vector_metadata_source ON vector_metadata(source_id);
CREATE INDEX idx_vector_metadata_subject ON vector_metadata(subject);
```

### Joining Vector Search with Metadata

```python
# 1. Query Vector Search
similar_chunks = index_endpoint.find_neighbors(
    deployed_index_id="vividly_oer_deployed",
    queries=[query_embedding],
    num_neighbors=10
)

chunk_ids = [neighbor.id for neighbor in similar_chunks[0]]

# 2. Fetch metadata from Cloud SQL
metadata_results = db.query(
    "SELECT * FROM vector_metadata WHERE chunk_id = ANY(%s)",
    (chunk_ids,)
)

# 3. Combine results
enriched_results = []
for neighbor in similar_chunks[0]:
    metadata = next(m for m in metadata_results if m.chunk_id == neighbor.id)
    enriched_results.append({
        "chunk_id": neighbor.id,
        "similarity_score": neighbor.distance,
        "text": metadata.chunk_text,
        "topic_id": metadata.topic_id,
        "chapter": metadata.chapter_title,
        "section": metadata.section_title
    })
```

---

## Ingestion Pipeline

### Step-by-Step Process

```
OpenStax .docx → Extract Text → Chunk → Clean → Embed → Upload
```

### 1. Document Extraction

```python
import docx

def extract_text_from_docx(file_path: str) -> dict:
    """Extract structured text from OpenStax .docx file."""
    doc = docx.Document(file_path)

    structure = {
        "title": doc.core_properties.title,
        "chapters": []
    }

    current_chapter = None
    current_section = None

    for para in doc.paragraphs:
        style = para.style.name

        if style == 'Heading 1':  # Chapter
            current_chapter = {
                "title": para.text,
                "sections": []
            }
            structure["chapters"].append(current_chapter)

        elif style == 'Heading 2':  # Section
            current_section = {
                "title": para.text,
                "content": []
            }
            current_chapter["sections"].append(current_section)

        elif style == 'Normal' and current_section:
            current_section["content"].append(para.text)

    return structure
```

### 2. Chunking

```python
import tiktoken

def chunk_section(section: dict, max_tokens: int = 400) -> list[dict]:
    """Split section into semantic chunks."""
    encoding = tiktoken.get_encoding("cl100k_base")

    chunks = []
    current_chunk = {
        "text": "",
        "token_count": 0
    }

    for paragraph in section["content"]:
        tokens = encoding.encode(paragraph)
        token_count = len(tokens)

        # If adding this paragraph exceeds limit, start new chunk
        if current_chunk["token_count"] + token_count > max_tokens:
            if current_chunk["text"]:
                chunks.append(current_chunk)

            # Start new chunk with overlap
            overlap_text = " ".join(current_chunk["text"].split()[-50:])
            current_chunk = {
                "text": overlap_text + " " + paragraph,
                "token_count": len(encoding.encode(overlap_text)) + token_count
            }
        else:
            current_chunk["text"] += " " + paragraph
            current_chunk["token_count"] += token_count

    # Add final chunk
    if current_chunk["text"]:
        chunks.append(current_chunk)

    return chunks
```

### 3. Embedding Generation

```python
from vertexai.language_models import TextEmbeddingModel

def generate_embeddings(chunks: list[dict]) -> list[dict]:
    """Generate embeddings for chunks in batches."""
    model = TextEmbeddingModel.from_pretrained("text-embedding-gecko@003")

    embedded_chunks = []
    batch_size = 250

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk["text"] for chunk in batch]

        # Generate embeddings
        embeddings = model.get_embeddings(texts)

        # Attach embeddings to chunks
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding.values
            embedded_chunks.append(chunk)

    return embedded_chunks
```

### 4. Upload to Vector Search

```python
import json

def upload_to_vector_search(embedded_chunks: list[dict], gcs_bucket: str):
    """Upload embeddings to GCS for Vector Search ingestion."""

    # Convert to newline-delimited JSON
    records = []
    for i, chunk in enumerate(embedded_chunks):
        record = {
            "id": chunk["chunk_id"],
            "embedding": chunk["embedding"],
            "restricts": [
                {"namespace": "source", "allow_list": [chunk["source"]]},
                {"namespace": "subject", "allow_list": [chunk["subject"]]},
                {"namespace": "grade_level", "allow_list": chunk["grade_levels"]}
            ],
            "crowding_tag": chunk["topic_id"]
        }
        records.append(json.dumps(record))

    # Upload to GCS
    blob_path = f"embeddings/batch_{timestamp}.json"
    upload_to_gcs(
        bucket=gcs_bucket,
        blob_path=blob_path,
        content="\n".join(records)
    )

    # Update Vector Search index
    update_index(blob_path)
```

### 5. Store Metadata

```python
def store_metadata(chunks: list[dict], db_connection):
    """Store chunk metadata in PostgreSQL."""

    insert_query = """
        INSERT INTO vector_metadata (
            chunk_id, source_id, topic_id, subject,
            chunk_text, chunk_type, chapter_title, section_title,
            token_count, difficulty_level, created_at
        ) VALUES %s
    """

    values = [
        (
            chunk["chunk_id"],
            chunk["source_id"],
            chunk["topic_id"],
            chunk["subject"],
            chunk["text"],
            chunk["type"],
            chunk["chapter_title"],
            chunk["section_title"],
            chunk["token_count"],
            chunk["difficulty_level"],
            "NOW()"
        )
        for chunk in chunks
    ]

    execute_batch(db_connection, insert_query, values)
```

---

## Query Patterns

### 1. Basic Similarity Search

```python
def retrieve_relevant_chunks(
    query: str,
    topic_id: str,
    k: int = 10
) -> list[dict]:
    """Retrieve top-k most relevant chunks for a topic."""

    # Generate query embedding
    query_embedding = embed_text(query)

    # Query Vector Search with topic filter
    response = index_endpoint.find_neighbors(
        deployed_index_id="vividly_oer_deployed",
        queries=[query_embedding],
        num_neighbors=k,
        filter=[{
            "namespace": "topic",
            "allow_list": [topic_id]
        }]
    )

    # Fetch metadata
    chunk_ids = [n.id for n in response[0]]
    metadata = fetch_metadata(chunk_ids)

    return metadata
```

### 2. Filtered Search by Grade Level

```python
def retrieve_grade_appropriate_content(
    query: str,
    topic_id: str,
    grade_level: int,
    k: int = 10
) -> list[dict]:
    """Retrieve content appropriate for student's grade level."""

    query_embedding = embed_text(query)

    response = index_endpoint.find_neighbors(
        deployed_index_id="vividly_oer_deployed",
        queries=[query_embedding],
        num_neighbors=k,
        filter=[
            {"namespace": "topic", "allow_list": [topic_id]},
            {"namespace": "grade_level", "allow_list": [str(grade_level)]}
        ]
    )

    return enrich_with_metadata(response[0])
```

### 3. Diversified Retrieval

```python
def retrieve_diverse_examples(
    query: str,
    topic_id: str,
    k: int = 15
) -> list[dict]:
    """Retrieve diverse examples (not just similar ones)."""

    query_embedding = embed_text(query)

    # Use crowding_tag to limit similar results
    response = index_endpoint.find_neighbors(
        deployed_index_id="vividly_oer_deployed",
        queries=[query_embedding],
        num_neighbors=k,
        per_crowding_attribute_num_neighbors=2  # Max 2 from same subtopic
    )

    return enrich_with_metadata(response[0])
```

### 4. Multi-Query Retrieval

```python
def retrieve_for_script_generation(
    topic_id: str,
    interest: str,
    grade_level: int
) -> dict:
    """Retrieve chunks optimized for script generation."""

    # Generate multiple query perspectives
    queries = [
        f"definition and explanation of {topic_id}",
        f"practical examples of {topic_id}",
        f"real-world applications of {topic_id} related to {interest}",
        f"common misconceptions about {topic_id}"
    ]

    all_chunks = []
    seen_ids = set()

    for query in queries:
        chunks = retrieve_relevant_chunks(query, topic_id, k=5)

        # Deduplicate
        for chunk in chunks:
            if chunk["chunk_id"] not in seen_ids:
                all_chunks.append(chunk)
                seen_ids.add(chunk["chunk_id"])

    return {
        "definitions": all_chunks[:3],
        "examples": all_chunks[3:6],
        "applications": all_chunks[6:9],
        "misconceptions": all_chunks[9:12]
    }
```

---

## Performance Optimization

### Index Update Strategy

**Incremental Updates**: Add new embeddings without full rebuild

```python
def incremental_index_update(new_chunks: list[dict]):
    """Add new embeddings to existing index."""

    # Upload new embeddings to GCS
    new_blob_path = f"embeddings/incremental_{timestamp}.json"
    upload_embeddings(new_chunks, new_blob_path)

    # Update index (non-blocking)
    index.update(
        metadata={
            "contentsDeltaUri": f"gs://vividly-mvp-vector-db/{new_blob_path}"
        }
    )
```

**Full Rebuild**: Required for major schema changes

```python
def full_index_rebuild():
    """Rebuild index from scratch (maintenance window)."""

    # 1. Create new index version
    new_index = create_index(
        display_name="vividly-oer-embeddings-index-v2"
    )

    # 2. Upload all embeddings
    upload_all_embeddings(new_index)

    # 3. Deploy new index
    deploy_index(new_index)

    # 4. Switch traffic
    switch_endpoint_index(old_index, new_index)

    # 5. Delete old index after verification
```

### Query Optimization

**Caching Frequent Queries**

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_retrieve(query_hash: str, topic_id: str) -> str:
    """Cache retrieval results for common queries."""
    results = retrieve_relevant_chunks(query_hash, topic_id)
    return json.dumps(results)

def retrieve_with_cache(query: str, topic_id: str):
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    return json.loads(cached_retrieve(query_hash, topic_id))
```

### Embedding Batch Processing

```python
async def batch_embed_async(texts: list[str]) -> list[list[float]]:
    """Process embeddings asynchronously for faster ingestion."""

    from concurrent.futures import ThreadPoolExecutor

    batch_size = 250
    batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(model.get_embeddings, batch)
            for batch in batches
        ]

        results = []
        for future in futures:
            embeddings = future.result()
            results.extend([emb.values for emb in embeddings])

    return results
```

---

## Maintenance

### Regular Tasks

#### Daily
- Monitor query latency (target: <100ms p95)
- Check index health via Cloud Monitoring
- Review failed embedding jobs

#### Weekly
- Analyze retrieval quality metrics
- Review chunk coverage per topic
- Update difficulty levels based on usage

#### Monthly
- Ingest new OER content
- Rebuild index if >20% new content
- Archive unused chunks

### Monitoring Queries

```sql
-- Check chunk coverage by topic
SELECT
    t.id AS topic_id,
    t.title,
    COUNT(vm.chunk_id) AS chunk_count,
    AVG(vm.token_count) AS avg_chunk_size
FROM topics t
LEFT JOIN vector_metadata vm ON t.id = vm.topic_id
GROUP BY t.id, t.title
HAVING COUNT(vm.chunk_id) < 5
ORDER BY chunk_count ASC;

-- Identify low-quality chunks (too short/long)
SELECT
    chunk_id,
    topic_id,
    token_count,
    chunk_type
FROM vector_metadata
WHERE token_count < 50 OR token_count > 1500
ORDER BY token_count DESC;
```

### Vector Search Metrics

```python
# Monitor via Cloud Monitoring
METRICS_TO_TRACK = [
    "aiplatform.googleapis.com/online_serving/index_latency",
    "aiplatform.googleapis.com/online_serving/queries_per_second",
    "aiplatform.googleapis.com/online_serving/error_count"
]

# Alert thresholds
LATENCY_THRESHOLD_MS = 200  # p95
ERROR_RATE_THRESHOLD = 0.01  # 1%
```

---

## Future Enhancements

### Post-MVP Considerations

1. **Hybrid Search**: Combine vector search with keyword search
2. **Reranking**: Use cross-encoder model to rerank top-k results
3. **Feedback Loop**: Update chunk quality scores based on usage
4. **Multi-Modal**: Add image embeddings for diagrams/figures
5. **Personalized Embeddings**: Fine-tune embeddings per student cohort

---

**Document Control**
- **Owner**: AI/ML Team
- **Current Index Version**: v1.0
- **Last Reindex**: 2025-10-15
- **Next Review**: After initial OER ingestion
