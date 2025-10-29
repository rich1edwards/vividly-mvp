# OER Content Ingestion Pipeline

This directory contains scripts for ingesting OpenStax OER content into Vividly's vector database.

## Overview

The pipeline consists of 5 stages:
1. **Download** - Fetch OpenStax textbooks in CNXML format
2. **Process** - Parse XML and extract structured content
3. **Chunk** - Split content into 500-word chunks with overlap
4. **Embed** - Generate 768-dim embeddings using Vertex AI
5. **Index** - Upload to Vertex AI Vector Search

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT=vividly-dev-rich
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Ensure Vertex AI API is enabled
gcloud services enable aiplatform.googleapis.com --project=vividly-dev-rich
```

## Quick Start

```bash
# Run full pipeline
python run_pipeline.py

# Or run stages individually
./01_download_openstax.sh
python 02_process_content.py
python 03_chunk_content.py
python 04_generate_embeddings.py
python 05_create_vector_index.py
```

## Directory Structure

```
oer_ingestion/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── run_pipeline.py              # Master script (runs all stages)
│
├── 01_download_openstax.sh      # Download OpenStax books
├── 02_process_content.py        # Parse CNXML, extract text
├── 03_chunk_content.py          # Create 500-word chunks
├── 04_generate_embeddings.py    # Vertex AI embeddings
├── 05_create_vector_index.py    # Vector database setup
│
├── data/                        # Data directory (gitignored)
│   ├── raw/                     # Downloaded CNXML files
│   ├── processed/               # Parsed JSON
│   ├── chunks/                  # Chunked content
│   ├── embeddings/              # Embedded chunks
│   └── index/                   # Vector index data
│
└── utils/                       # Utility modules
    ├── xml_parser.py            # CNXML parsing
    ├── chunker.py               # Text chunking
    └── vertex_ai_client.py      # Vertex AI wrapper
```

## OpenStax Books

The pipeline downloads these textbooks:

| Subject | Book | URL |
|---------|------|-----|
| Physics | College Physics 2e | https://openstax.org/details/books/college-physics-2e |
| Chemistry | Chemistry 2e | https://openstax.org/details/books/chemistry-2e |
| Biology | Biology 2e | https://openstax.org/details/books/biology-2e |
| Computer Science | (Curated sources) | Various OER |

## Stage Details

### Stage 1: Download

```bash
./01_download_openstax.sh
```

Downloads OpenStax books in CNXML format and associated images.

**Output**: `data/raw/physics-2e.xml`, `data/raw/physics-2e-images.zip`, etc.

### Stage 2: Process

```bash
python 02_process_content.py
```

Parses CNXML, extracts:
- Chapters and sections
- Text content (paragraphs, examples)
- Figures and captions
- Learning objectives
- Metadata

**Output**: `data/processed/physics-2e.json`

**Example output structure**:
```json
{
  "title": "College Physics 2e",
  "author": "OpenStax",
  "license": "CC BY 4.0",
  "chapters": [
    {
      "id": "chapter-04",
      "title": "Dynamics: Force and Newton's Laws",
      "sections": [
        {
          "id": "section-04-03",
          "title": "Newton's Third Law",
          "content_blocks": [...]
        }
      ]
    }
  ]
}
```

### Stage 3: Chunk

```bash
python 03_chunk_content.py
```

Splits content into 500-word chunks with 50-word overlap.

**Parameters**:
- Target chunk size: 500 words
- Minimum: 300 words
- Maximum: 800 words
- Overlap: 50 words

**Output**: `data/chunks/physics-2e-chunks.json`

**Example chunk**:
```json
{
  "chunk_id": "physics-2e-04-03-001",
  "text": "Newton's third law of motion states...",
  "word_count": 487,
  "metadata": {
    "source_title": "College Physics 2e",
    "chapter_id": "chapter-04",
    "section_title": "Newton's Third Law",
    "subject": "physics"
  }
}
```

### Stage 4: Generate Embeddings

```bash
python 04_generate_embeddings.py
```

Generates 768-dimensional embeddings using Vertex AI `text-embedding-gecko@003`.

**Cost**: ~$0.64 for 50,000 chunks (one-time)

**Output**: `data/embeddings/physics-2e-embeddings.json`

**Example**:
```json
{
  "chunk_id": "physics-2e-04-03-001",
  "text": "Newton's third law...",
  "embedding": [0.123, 0.456, ..., 0.789],  // 768 dimensions
  "metadata": {...}
}
```

### Stage 5: Create Vector Index

```bash
python 05_create_vector_index.py
```

Creates Vertex AI Vector Search index and uploads embeddings.

**Index configuration**:
- Dimensions: 768
- Distance measure: Dot product (cosine similarity)
- Approximate neighbors: 10
- Algorithm: Tree-AH

**Deployment**:
- Machine type: e2-standard-2
- Min replicas: 1
- Max replicas: 3 (auto-scaling)

## Data Volume

| Metric | Value |
|--------|-------|
| Source pages | ~4,800 |
| Total chunks | ~50,000 |
| Avg chunk size | ~480 words |
| Storage (chunks) | ~32 MB |
| Storage (embeddings) | ~150 MB |
| Vector index size | ~150 MB |

## Performance

| Stage | Time | Notes |
|-------|------|-------|
| Download | ~5 min | Network-dependent |
| Process | ~10 min | CPU-bound |
| Chunk | ~5 min | Fast |
| Embed | ~30 min | API rate-limited |
| Index | ~20 min | GCP provisioning |
| **Total** | **~70 min** | First run only |

## Incremental Updates

When OpenStax releases updates:

```bash
# Download new version only
./01_download_openstax.sh --book physics-2e

# Process differential
python 02_process_content.py --differential

# Update embeddings (only changed chunks)
python 04_generate_embeddings.py --differential

# Update index
python 05_create_vector_index.py --update
```

## Troubleshooting

### Download fails
- Check internet connection
- Verify OpenStax URLs haven't changed
- Try manual download from openstax.org

### XML parsing errors
- Check CNXML format hasn't changed
- Validate XML: `xmllint --noout data/raw/physics-2e.xml`
- Review error logs in `logs/process_content.log`

### Embedding API errors
- Verify Vertex AI API enabled
- Check GCP quotas: `gcloud services list --enabled`
- Increase quota if needed: [GCP Console](https://console.cloud.google.com/iam-admin/quotas)

### Vector index creation fails
- Ensure sufficient GCP permissions
- Check VPC network configuration
- Verify service account has `aiplatform.user` role

## Cost Estimation

| Resource | Cost | Frequency |
|----------|------|-----------|
| Embedding generation | $0.64 | One-time (or quarterly updates) |
| Vector Search index | ~$50/month | Ongoing (e2-standard-2 x1) |
| Storage (GCS) | ~$0.01/month | Ongoing (150 MB) |
| **Total setup** | **$0.64** | One-time |
| **Total monthly** | **~$50** | Ongoing |

## Next Steps

After ingestion:

1. **Test retrieval**: `python test_retrieval.py`
2. **Map topics**: `python map_topics_to_content.py`
3. **Verify quality**: `python qa_embeddings.py`
4. **Deploy to production**: Run pipeline in prod environment

## Reference

See full implementation details in:
- `/OER_CONTENT_STRATEGY.md` - Complete strategy
- `/VECTOR_DB_SCHEMA.md` - Database schema
- `/AI_GENERATION_SPECIFICATIONS.md` - RAG pipeline

## Support

Issues? Contact: dev@vividly.edu
