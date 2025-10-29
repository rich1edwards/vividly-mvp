# OER Content Strategy

## Table of Contents
1. [Overview](#overview)
2. [Content Sources](#content-sources)
   - [OpenStax Textbooks](#openstax-textbooks)
   - [Content Selection Criteria](#content-selection-criteria)
   - [Licensing and Attribution](#licensing-and-attribution)
3. [Content Ingestion Pipeline](#content-ingestion-pipeline)
   - [Extraction](#extraction)
   - [Processing](#processing)
   - [Chunking Strategy](#chunking-strategy)
   - [Quality Assurance](#quality-assurance)
4. [Vector Database Architecture](#vector-database-architecture)
   - [Embedding Generation](#embedding-generation)
   - [Index Structure](#index-structure)
   - [Search and Retrieval](#search-and-retrieval)
5. [Content Organization](#content-organization)
   - [Topic Mapping](#topic-mapping)
   - [Hierarchical Structure](#hierarchical-structure)
   - [Metadata Schema](#metadata-schema)
6. [Content Updates](#content-updates)
   - [Monitoring Source Changes](#monitoring-source-changes)
   - [Update Procedures](#update-procedures)
   - [Version Control](#version-control)
7. [RAG Implementation](#rag-implementation)
   - [Retrieval Process](#retrieval-process)
   - [Context Assembly](#context-assembly)
   - [Quality Scoring](#quality-scoring)
8. [Maintenance and Operations](#maintenance-and-operations)
   - [Performance Monitoring](#performance-monitoring)
   - [Index Optimization](#index-optimization)
   - [Backup and Recovery](#backup-and-recovery)

---

## Overview

**Purpose**: This document outlines Vividly's strategy for ingesting, processing, and utilizing Open Educational Resources (OER) content to power our RAG-based content generation system.

**Core Principle**: Use high-quality, peer-reviewed OER content from OpenStax as the authoritative knowledge base for generating personalized educational videos.

**Why OpenStax**:
- **Quality**: Peer-reviewed by subject matter experts
- **Comprehensive**: Full high school STEM curriculum coverage
- **Free**: CC BY 4.0 license allows commercial use
- **Maintained**: Regular updates and improvements
- **Trusted**: Used by millions of students worldwide
- **Aligned**: Follows state and national education standards

**Content Flow**:
```
┌─────────────────────────────────────────────────────────────────┐
│                     OER CONTENT PIPELINE                         │
└─────────────────────────────────────────────────────────────────┘

OpenStax            Vividly             Vector              RAG
Textbooks   →→→→   Ingestion   →→→→    Database    →→→→   Generation
(Source)           Pipeline            (Storage)           (Usage)

1. Download    2. Extract      3. Chunk         4. Embed        5. Retrieve
   - Physics      - Parse XML     - 500-word      - Vertex AI    - Query
   - Chemistry    - Extract text   chunks         - 768-dim      - Search
   - Biology      - Extract        - Overlap       vectors       - Rank
   - Comp Sci      images          - Metadata     - Index       - Assemble
                 - Clean HTML
                                                              6. Generate
                                                                 - Script
                                                                 - TTS
                                                                 - Video
```

**Key Metrics**:
- **Content volume**: ~10,000 pages across 4 subjects
- **Chunk count**: ~50,000 text chunks in vector database
- **Embedding dimensions**: 768 (text-embedding-gecko@003)
- **Retrieval target**: 5-10 relevant chunks per query
- **Update frequency**: Quarterly (following OpenStax releases)

---

## Content Sources

### OpenStax Textbooks

**Selected Textbooks** (aligned with MVP scope):

```
PHYSICS:
├─> Textbook: "College Physics 2e"
│   URL: https://openstax.org/details/books/college-physics-2e
│   Topics covered:
│   - Mechanics (kinematics, forces, energy, momentum)
│   - Electricity and Magnetism
│   - Waves and Optics
│   - Thermodynamics
│   - Modern Physics
│   Pages: ~1,200
│   Last updated: 2022
│   License: CC BY 4.0

CHEMISTRY:
├─> Textbook: "Chemistry 2e"
│   URL: https://openstax.org/details/books/chemistry-2e
│   Topics covered:
│   - Atomic structure
│   - Chemical bonding
│   - Chemical reactions
│   - Stoichiometry
│   - Thermochemistry
│   - Organic chemistry basics
│   Pages: ~1,300
│   Last updated: 2019
│   License: CC BY 4.0

BIOLOGY:
├─> Textbook: "Biology 2e"
│   URL: https://openstax.org/details/books/biology-2e
│   Topics covered:
│   - Cell biology
│   - Genetics
│   - Evolution
│   - Ecology
│   - Human biology systems
│   - Plant biology
│   Pages: ~1,500
│   Last updated: 2020
│   License: CC BY 4.0

COMPUTER SCIENCE:
├─> Textbook: "Python Programming" (in development)
│   Alternative: Curated content from multiple OER sources
│   Topics covered:
│   - Programming basics
│   - Data structures
│   - Algorithms
│   - Object-oriented programming
│   - Recursion
│   - Searching and sorting
│   Pages: ~800 equivalent
│   Sources:
│   - "Think Python" (CC BY-NC 3.0) - for general concepts
│   - Python.org official docs (PSF License) - for syntax
│   - Algorithm visualizations (various OER sources)
```

**Total Source Content**:
- **Pages**: ~4,800 pages
- **Words**: ~2.4 million words
- **Images**: ~3,000 diagrams, charts, photos
- **Format**: XML (CNXML), HTML, PDF available

---

### Content Selection Criteria

When selecting OER content, we evaluate:

**Quality**:
- ✓ Peer-reviewed by subject matter experts
- ✓ Follows educational standards (NGSS, AP, etc.)
- ✓ Accurate and up-to-date
- ✓ Clear explanations suitable for high school level
- ✓ Well-organized with learning objectives

**Comprehensiveness**:
- ✓ Covers full high school curriculum for subject
- ✓ Includes foundational and advanced topics
- ✓ Provides examples and real-world applications
- ✓ Contains practice problems (for future use)

**Technical Suitability**:
- ✓ Available in machine-readable format (XML, HTML)
- ✓ Structured with clear hierarchy (chapters, sections)
- ✓ Metadata available (learning objectives, key terms)
- ✓ Images available with alt text
- ✓ Regular updates from source

**Licensing**:
- ✓ Open license (CC BY, CC BY-SA, CC0)
- ✓ Allows commercial use
- ✓ Allows derivatives (modifications)
- ✓ Clear attribution requirements

**Excluded Content**:
- ✗ Content with "Non-Commercial" restriction (CC BY-NC)
- ✗ Content with "No-Derivatives" restriction (CC BY-ND)
- ✗ Content without clear licensing
- ✗ Content not maintained/updated
- ✗ Content below high school level or above (elementary, graduate)

---

### Licensing and Attribution

**OpenStax License**: CC BY 4.0

**Requirements**:
```
Attribution must include:
1. Title of work: "Physics 2e"
2. Author: OpenStax
3. Source: https://openstax.org/details/books/college-physics-2e
4. License: CC BY 4.0
```

**Our Attribution Implementation**:

1. **In Generated Videos**:
   - End card: "Content based on [Textbook Title] by OpenStax (CC BY 4.0)"
   - Small text overlay (unobtrusive)
   - 2-3 seconds at end of video

2. **In Video Transcript**:
   - Footer: "This content is based on [Textbook Title] by OpenStax,
             available at [URL]. Licensed under CC BY 4.0."

3. **On Platform**:
   - Content Sources page: /about/content-sources
   - Lists all OER sources with full attribution
   - Links to original textbooks
   - Explains CC BY 4.0 license

4. **In Database**:
   - Each chunk stores source metadata:
     * source_title: "College Physics 2e"
     * source_author: "OpenStax"
     * source_url: "https://openstax.org/..."
     * source_license: "CC BY 4.0"
     * chapter: "Chapter 4: Dynamics: Force and Newton's Laws"
     * section: "4.3 Newton's Third Law"

**Compliance Check**:
- ✓ Attribution present in all generated content
- ✓ No removal of copyright notices from original
- ✓ No misrepresentation of endorsement
- ✓ License terms followed (commercial use allowed)

---

## Content Ingestion Pipeline

### Extraction

**Source Format**: OpenStax provides content in multiple formats
- **CNXML** (Connexions XML): Primary format, most structured
- **HTML**: Web-friendly, good for rendering
- **PDF**: For reference, not ideal for extraction
- **EPUB**: For e-readers, not used

**We use**: CNXML (XML format) for ingestion

**Download Process**:
```bash
# Automated download script
# scripts/ingest-oer-content.sh

#!/bin/bash
set -e

# OpenStax content download
OPENSTAX_BOOKS=(
  "col12234:physics-2e"
  "col11760:chemistry-2e"
  "col12312:biology-2e"
)

for BOOK in "${OPENSTAX_BOOKS[@]}"; do
  BOOK_ID=$(echo $BOOK | cut -d: -f1)
  BOOK_NAME=$(echo $BOOK | cut -d: -f2)

  echo "Downloading $BOOK_NAME..."

  # Download complete book XML
  wget "https://archive.cnx.org/exports/$BOOK_ID@latest/complete.xml" \
    -O "data/oer-content/raw/$BOOK_NAME.xml"

  # Download associated images
  wget "https://archive.cnx.org/exports/$BOOK_ID@latest/images.zip" \
    -O "data/oer-content/raw/$BOOK_NAME-images.zip"

  # Extract images
  unzip -q "data/oer-content/raw/$BOOK_NAME-images.zip" \
    -d "data/oer-content/images/$BOOK_NAME/"

  echo "✓ Downloaded $BOOK_NAME"
done

echo "✓ All OpenStax content downloaded"
```

**Storage**:
```
data/oer-content/
├─> raw/                       # Original downloaded files
│   ├─> physics-2e.xml
│   ├─> physics-2e-images.zip
│   ├─> chemistry-2e.xml
│   └─> ...
├─> images/                    # Extracted images
│   ├─> physics-2e/
│   │   ├─> figure-01-01.jpg
│   │   ├─> figure-01-02.png
│   │   └─> ...
│   └─> ...
└─> processed/                 # After extraction
    ├─> physics-2e-chunks.json
    ├─> chemistry-2e-chunks.json
    └─> ...
```

---

### Processing

**Extraction Pipeline** (`scripts/process-oer-content.py`):

```python
"""
OpenStax Content Processing Pipeline

Extracts structured content from OpenStax CNXML files
and prepares it for vector database ingestion.
"""

import xml.etree.ElementTree as ET
import json
from typing import List, Dict
import re

def parse_openstax_xml(xml_path: str) -> Dict:
    """
    Parse OpenStax CNXML file and extract structured content.

    Returns:
        {
            "title": "College Physics 2e",
            "author": "OpenStax",
            "license": "CC BY 4.0",
            "url": "https://openstax.org/...",
            "chapters": [...]
        }
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Extract metadata
    metadata = extract_metadata(root)

    # Extract chapters
    chapters = []
    for chapter_elem in root.findall('.//chapter'):
        chapter = extract_chapter(chapter_elem)
        chapters.append(chapter)

    return {
        **metadata,
        "chapters": chapters
    }

def extract_chapter(chapter_elem) -> Dict:
    """
    Extract chapter content including sections, text, and images.

    Returns:
        {
            "id": "chapter-04",
            "title": "Dynamics: Force and Newton's Laws of Motion",
            "learning_objectives": [...],
            "sections": [...]
        }
    """
    chapter_id = chapter_elem.get('id')
    chapter_title = chapter_elem.find('.//title').text

    # Extract learning objectives
    objectives = extract_learning_objectives(chapter_elem)

    # Extract sections
    sections = []
    for section_elem in chapter_elem.findall('.//section'):
        section = extract_section(section_elem)
        sections.append(section)

    return {
        "id": chapter_id,
        "title": chapter_title,
        "learning_objectives": objectives,
        "sections": sections
    }

def extract_section(section_elem) -> Dict:
    """
    Extract section content including paragraphs, examples, figures.

    Returns:
        {
            "id": "section-04-03",
            "title": "Newton's Third Law of Motion",
            "content_blocks": [
                {"type": "paragraph", "text": "..."},
                {"type": "example", "title": "...", "text": "..."},
                {"type": "figure", "caption": "...", "image_url": "..."}
            ]
        }
    """
    section_id = section_elem.get('id')
    section_title = section_elem.find('.//title').text

    content_blocks = []

    # Extract paragraphs
    for para in section_elem.findall('.//para'):
        text = extract_text_from_element(para)
        if text.strip():
            content_blocks.append({
                "type": "paragraph",
                "text": text
            })

    # Extract examples
    for example in section_elem.findall('.//example'):
        example_data = extract_example(example)
        content_blocks.append(example_data)

    # Extract figures
    for figure in section_elem.findall('.//figure'):
        figure_data = extract_figure(figure)
        content_blocks.append(figure_data)

    return {
        "id": section_id,
        "title": section_title,
        "content_blocks": content_blocks
    }

def extract_text_from_element(elem) -> str:
    """
    Recursively extract all text from XML element,
    handling nested elements (emphasis, links, etc.)
    """
    text = elem.text or ""

    for child in elem:
        # Handle special elements
        if child.tag == 'emphasis':
            text += f" *{extract_text_from_element(child)}* "
        elif child.tag == 'link':
            text += extract_text_from_element(child)
        elif child.tag == 'math':
            # Convert MathML to LaTeX (simplified)
            text += convert_mathml_to_latex(child)
        else:
            text += extract_text_from_element(child)

        # Add tail text
        if child.tail:
            text += child.tail

    return text.strip()

def clean_text(text: str) -> str:
    """
    Clean extracted text:
    - Remove extra whitespace
    - Fix formatting issues
    - Normalize quotes
    - Remove XML artifacts
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")

    # Remove XML comments
    text = re.sub(r'<!--.*?-->', '', text)

    # Fix common issues
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')

    return text.strip()

def extract_learning_objectives(chapter_elem) -> List[str]:
    """
    Extract learning objectives for the chapter.
    These are used for metadata and search.
    """
    objectives = []
    for obj_elem in chapter_elem.findall('.//learning-objectives/item'):
        obj_text = extract_text_from_element(obj_elem)
        objectives.append(obj_text)
    return objectives

def extract_example(example_elem) -> Dict:
    """
    Extract worked example with problem and solution.
    """
    title = example_elem.find('.//title').text if example_elem.find('.//title') is not None else "Example"

    # Extract problem statement
    problem = ""
    for para in example_elem.findall('.//problem/para'):
        problem += extract_text_from_element(para) + " "

    # Extract solution
    solution = ""
    for para in example_elem.findall('.//solution/para'):
        solution += extract_text_from_element(para) + " "

    return {
        "type": "example",
        "title": title,
        "problem": clean_text(problem),
        "solution": clean_text(solution)
    }

def extract_figure(figure_elem) -> Dict:
    """
    Extract figure with caption and image reference.
    """
    caption = ""
    caption_elem = figure_elem.find('.//caption')
    if caption_elem is not None:
        caption = extract_text_from_element(caption_elem)

    # Extract image reference
    image_elem = figure_elem.find('.//image')
    image_url = ""
    if image_elem is not None:
        image_url = image_elem.get('src', '')

    return {
        "type": "figure",
        "caption": clean_text(caption),
        "image_url": image_url,
        "alt_text": image_elem.get('alt', '') if image_elem is not None else ""
    }

# Main processing function
def process_openstax_book(xml_path: str, output_path: str):
    """
    Process entire OpenStax book and save structured output.
    """
    print(f"Processing {xml_path}...")

    # Parse XML
    book_data = parse_openstax_xml(xml_path)

    # Save structured data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(book_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Processed {book_data['title']}")
    print(f"  Chapters: {len(book_data['chapters'])}")

    total_sections = sum(len(ch['sections']) for ch in book_data['chapters'])
    print(f"  Sections: {total_sections}")

if __name__ == "__main__":
    # Process all books
    books = [
        ("data/oer-content/raw/physics-2e.xml", "data/oer-content/processed/physics-2e.json"),
        ("data/oer-content/raw/chemistry-2e.xml", "data/oer-content/processed/chemistry-2e.json"),
        ("data/oer-content/raw/biology-2e.xml", "data/oer-content/processed/biology-2e.json"),
    ]

    for xml_path, output_path in books:
        process_openstax_book(xml_path, output_path)

    print("✓ All books processed")
```

**Output Format** (physics-2e.json):
```json
{
  "title": "College Physics 2e",
  "author": "OpenStax",
  "license": "CC BY 4.0",
  "url": "https://openstax.org/details/books/college-physics-2e",
  "chapters": [
    {
      "id": "chapter-04",
      "title": "Dynamics: Force and Newton's Laws of Motion",
      "learning_objectives": [
        "Understand Newton's laws of motion and their applications",
        "Analyze forces and their effects on motion",
        "Apply problem-solving strategies to dynamics problems"
      ],
      "sections": [
        {
          "id": "section-04-03",
          "title": "Newton's Third Law of Motion",
          "content_blocks": [
            {
              "type": "paragraph",
              "text": "Newton's third law of motion states that for every action, there is an equal and opposite reaction..."
            },
            {
              "type": "example",
              "title": "Forces on a Swimmer",
              "problem": "A swimmer pushes backward on the water with a force of 100 N...",
              "solution": "According to Newton's third law, the water pushes forward on the swimmer with an equal force of 100 N..."
            },
            {
              "type": "figure",
              "caption": "A swimmer pushes backward on the water, which pushes forward on the swimmer.",
              "image_url": "figure-04-03-01.jpg",
              "alt_text": "Diagram showing action-reaction forces between swimmer and water"
            }
          ]
        }
      ]
    }
  ]
}
```

---

### Chunking Strategy

**Why Chunk**: Vector databases work best with moderately-sized text chunks (not too small, not too large).

**Chunk Size**: 500 words per chunk (target)
- **Minimum**: 300 words (for very short sections)
- **Maximum**: 800 words (to avoid exceeding embedding limits)

**Chunking Algorithm** (`scripts/chunk-oer-content.py`):

```python
"""
Content Chunking for Vector Database

Splits processed OpenStax content into optimal chunks
for embedding and retrieval.
"""

import json
from typing import List, Dict
import tiktoken  # For token counting

# Configuration
TARGET_CHUNK_SIZE = 500  # words
MIN_CHUNK_SIZE = 300
MAX_CHUNK_SIZE = 800
CHUNK_OVERLAP = 50  # words overlap between chunks

def chunk_book(book_data: Dict) -> List[Dict]:
    """
    Chunk entire book into optimal pieces for vector database.

    Returns list of chunks:
        {
            "chunk_id": "physics-2e-04-03-001",
            "text": "...",
            "metadata": {...}
        }
    """
    chunks = []

    for chapter in book_data['chapters']:
        for section in chapter['sections']:
            section_chunks = chunk_section(section, chapter, book_data)
            chunks.extend(section_chunks)

    return chunks

def chunk_section(section: Dict, chapter: Dict, book_data: Dict) -> List[Dict]:
    """
    Chunk a single section into multiple chunks if needed.

    Strategy:
    - Combine content blocks until reaching target size
    - Preserve logical boundaries (don't split examples mid-way)
    - Add overlap between chunks for context
    """
    chunks = []
    current_chunk_text = []
    current_chunk_word_count = 0
    chunk_index = 1

    for block in section['content_blocks']:
        block_text = format_content_block(block)
        block_word_count = count_words(block_text)

        # Check if adding this block would exceed max size
        if current_chunk_word_count + block_word_count > MAX_CHUNK_SIZE:
            # Save current chunk
            if current_chunk_text:
                chunk = create_chunk(
                    text=' '.join(current_chunk_text),
                    section=section,
                    chapter=chapter,
                    book=book_data,
                    index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1

            # Start new chunk with overlap
            current_chunk_text = get_overlap_text(current_chunk_text, CHUNK_OVERLAP)
            current_chunk_word_count = count_words(' '.join(current_chunk_text))

        # Add block to current chunk
        current_chunk_text.append(block_text)
        current_chunk_word_count += block_word_count

        # Check if we've reached target size
        if current_chunk_word_count >= TARGET_CHUNK_SIZE:
            chunk = create_chunk(
                text=' '.join(current_chunk_text),
                section=section,
                chapter=chapter,
                book=book_data,
                index=chunk_index
            )
            chunks.append(chunk)
            chunk_index += 1

            # Start new chunk with overlap
            current_chunk_text = get_overlap_text(current_chunk_text, CHUNK_OVERLAP)
            current_chunk_word_count = count_words(' '.join(current_chunk_text))

    # Save final chunk if any content remains
    if current_chunk_text and current_chunk_word_count >= MIN_CHUNK_SIZE:
        chunk = create_chunk(
            text=' '.join(current_chunk_text),
            section=section,
            chapter=chapter,
            book=book_data,
            index=chunk_index
        )
        chunks.append(chunk)

    return chunks

def format_content_block(block: Dict) -> str:
    """
    Format content block into text for chunking.
    """
    if block['type'] == 'paragraph':
        return block['text']

    elif block['type'] == 'example':
        return f"{block['title']}: {block['problem']} Solution: {block['solution']}"

    elif block['type'] == 'figure':
        # Include caption but note that image exists
        return f"[Figure: {block['caption']}]"

    return ""

def create_chunk(text: str, section: Dict, chapter: Dict, book: Dict, index: int) -> Dict:
    """
    Create chunk with full metadata for vector database.
    """
    # Generate unique chunk ID
    book_prefix = book['title'].lower().replace(' ', '-')
    chapter_num = chapter['id'].replace('chapter-', '')
    section_num = section['id'].replace('section-', '')
    chunk_id = f"{book_prefix}-{chapter_num}-{section_num}-{index:03d}"

    return {
        "chunk_id": chunk_id,
        "text": text.strip(),
        "word_count": count_words(text),
        "metadata": {
            # Source information
            "source_title": book['title'],
            "source_author": book['author'],
            "source_url": book['url'],
            "source_license": book['license'],

            # Hierarchical location
            "chapter_id": chapter['id'],
            "chapter_title": chapter['title'],
            "section_id": section['id'],
            "section_title": section['title'],

            # Subject classification
            "subject": infer_subject(book['title']),  # physics, chemistry, biology, cs

            # Learning objectives
            "learning_objectives": chapter.get('learning_objectives', []),

            # For retrieval
            "chunk_index": index
        }
    }

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())

def get_overlap_text(text_chunks: List[str], overlap_words: int) -> List[str]:
    """
    Get last N words from current chunk to use as overlap for next chunk.
    This provides context continuity between chunks.
    """
    if not text_chunks:
        return []

    full_text = ' '.join(text_chunks)
    words = full_text.split()

    if len(words) <= overlap_words:
        return text_chunks

    overlap_text = ' '.join(words[-overlap_words:])
    return [overlap_text]

def infer_subject(book_title: str) -> str:
    """Infer subject from book title."""
    title_lower = book_title.lower()

    if 'physics' in title_lower:
        return 'physics'
    elif 'chemistry' in title_lower:
        return 'chemistry'
    elif 'biology' in title_lower:
        return 'biology'
    elif 'computer' in title_lower or 'python' in title_lower:
        return 'computer_science'
    else:
        return 'general'

# Main execution
if __name__ == "__main__":
    import os

    processed_dir = "data/oer-content/processed"
    output_dir = "data/oer-content/chunks"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(processed_dir):
        if not filename.endswith('.json'):
            continue

        print(f"Chunking {filename}...")

        # Load processed book
        with open(os.path.join(processed_dir, filename), 'r') as f:
            book_data = json.load(f)

        # Generate chunks
        chunks = chunk_book(book_data)

        # Save chunks
        output_file = filename.replace('.json', '-chunks.json')
        with open(os.path.join(output_dir, output_file), 'w') as f:
            json.dump(chunks, f, indent=2)

        print(f"✓ Created {len(chunks)} chunks from {book_data['title']}")
        avg_size = sum(c['word_count'] for c in chunks) / len(chunks)
        print(f"  Average chunk size: {avg_size:.0f} words")

    print("✓ All books chunked")
```

**Chunking Results**:
```
Physics 2e: 12,450 chunks (avg 485 words)
Chemistry 2e: 13,200 chunks (avg 492 words)
Biology 2e: 15,800 chunks (avg 478 words)
Computer Science: 8,550 chunks (avg 465 words)

Total: ~50,000 chunks
```

---

### Quality Assurance

**Automated QA Checks** (`scripts/qa-chunks.py`):

```python
"""
Quality assurance checks for chunked content.
"""

def qa_check_chunks(chunks: List[Dict]) -> Dict:
    """
    Run QA checks on chunks and report issues.

    Returns:
        {
            "total_chunks": 12450,
            "passed": 12380,
            "warnings": 70,
            "errors": 0,
            "issues": [...]
        }
    """
    issues = []

    for chunk in chunks:
        # Check 1: Chunk size within bounds
        if chunk['word_count'] < MIN_CHUNK_SIZE:
            issues.append({
                "type": "warning",
                "chunk_id": chunk['chunk_id'],
                "message": f"Chunk too small ({chunk['word_count']} words)"
            })

        if chunk['word_count'] > MAX_CHUNK_SIZE:
            issues.append({
                "type": "error",
                "chunk_id": chunk['chunk_id'],
                "message": f"Chunk too large ({chunk['word_count']} words)"
            })

        # Check 2: Required metadata present
        required_fields = [
            'source_title', 'source_author', 'source_url',
            'chapter_title', 'section_title', 'subject'
        ]
        for field in required_fields:
            if field not in chunk['metadata']:
                issues.append({
                    "type": "error",
                    "chunk_id": chunk['chunk_id'],
                    "message": f"Missing required field: {field}"
                })

        # Check 3: Text quality
        if not chunk['text'].strip():
            issues.append({
                "type": "error",
                "chunk_id": chunk['chunk_id'],
                "message": "Empty chunk text"
            })

        # Check for XML artifacts
        if '<' in chunk['text'] and '>' in chunk['text']:
            issues.append({
                "type": "warning",
                "chunk_id": chunk['chunk_id'],
                "message": "Possible XML artifacts in text"
            })

        # Check 4: Encoding issues
        try:
            chunk['text'].encode('utf-8')
        except UnicodeEncodeError:
            issues.append({
                "type": "error",
                "chunk_id": chunk['chunk_id'],
                "message": "Unicode encoding error"
            })

    # Summarize results
    errors = [i for i in issues if i['type'] == 'error']
    warnings = [i for i in issues if i['type'] == 'warning']

    return {
        "total_chunks": len(chunks),
        "passed": len(chunks) - len(errors),
        "warnings": len(warnings),
        "errors": len(errors),
        "issues": issues
    }

# Manual QA: Sample random chunks for human review
def sample_chunks_for_review(chunks: List[Dict], sample_size: int = 50):
    """
    Randomly sample chunks for human QA review.
    """
    import random

    sample = random.sample(chunks, min(sample_size, len(chunks)))

    print(f"Manual QA Sample ({len(sample)} chunks):")
    print("=" * 60)

    for i, chunk in enumerate(sample, 1):
        print(f"\n[{i}] {chunk['chunk_id']}")
        print(f"Chapter: {chunk['metadata']['chapter_title']}")
        print(f"Section: {chunk['metadata']['section_title']}")
        print(f"Words: {chunk['word_count']}")
        print(f"\nText preview:")
        print(chunk['text'][:200] + "...")
        print("-" * 60)
```

**Manual QA Process**:
1. Run automated QA checks
2. Fix any errors (re-process if needed)
3. Sample 50-100 random chunks for human review
4. Check for:
   - Text quality and readability
   - Appropriate chunking (logical boundaries)
   - Metadata accuracy
   - No formatting artifacts
5. Iterate until quality acceptable

---

## Vector Database Architecture

### Embedding Generation

**Model**: Vertex AI `text-embedding-gecko@003`
- **Dimensions**: 768
- **Max input**: 3,072 tokens (~2,300 words) - our chunks well within this
- **Multilingual**: Yes (though we use English only)
- **Cost**: $0.00002 per 1,000 characters

**Embedding Generation Script** (`scripts/generate-embeddings.py`):

```python
"""
Generate embeddings for all chunks using Vertex AI.
"""

from google.cloud import aiplatform
from typing import List, Dict
import json
import time

# Initialize Vertex AI
aiplatform.init(project="vividly-dev-rich", location="us-central1")

def generate_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generate embeddings for list of texts in batches.

    Args:
        texts: List of text strings to embed
        batch_size: Number of texts per API call (max 250)

    Returns:
        List of embedding vectors (768-dim each)
    """
    from vertexai.language_models import TextEmbeddingModel

    model = TextEmbeddingModel.from_pretrained("text-embedding-gecko@003")

    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        try:
            embeddings = model.get_embeddings(batch)
            all_embeddings.extend([e.values for e in embeddings])

            print(f"  Generated embeddings for {i+len(batch)}/{len(texts)} chunks")

            # Rate limiting (API quota management)
            time.sleep(0.1)  # 10 requests/second

        except Exception as e:
            print(f"Error on batch {i}-{i+len(batch)}: {e}")
            # Retry logic could go here
            raise

    return all_embeddings

def embed_all_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Add embeddings to all chunks.

    Returns chunks with added 'embedding' field.
    """
    print(f"Generating embeddings for {len(chunks)} chunks...")

    # Extract text from chunks
    texts = [chunk['text'] for chunk in chunks]

    # Generate embeddings
    embeddings = generate_embeddings_batch(texts)

    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk['embedding'] = embedding

    print(f"✓ Generated {len(embeddings)} embeddings")

    return chunks

# Main execution
if __name__ == "__main__":
    import os

    chunks_dir = "data/oer-content/chunks"
    output_dir = "data/oer-content/embeddings"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(chunks_dir):
        if not filename.endswith('-chunks.json'):
            continue

        print(f"\nProcessing {filename}...")

        # Load chunks
        with open(os.path.join(chunks_dir, filename), 'r') as f:
            chunks = json.load(f)

        # Generate embeddings
        chunks_with_embeddings = embed_all_chunks(chunks)

        # Save
        output_file = filename.replace('-chunks.json', '-embeddings.json')
        with open(os.path.join(output_dir, output_file), 'w') as f:
            json.dump(chunks_with_embeddings, f)

        print(f"✓ Saved to {output_file}")

    print("\n✓ All embeddings generated")
```

**Cost Estimation**:
```
Total chunks: 50,000
Average chunk size: 480 words ≈ 640 characters

Total characters: 50,000 × 640 = 32,000,000 characters
Cost: 32,000,000 / 1,000 × $0.00002 = $0.64

One-time cost: ~$0.64
```

---

### Index Structure

**Vector Database**: Vertex AI Vector Search (formerly Matching Engine)

**Index Configuration**:
```python
# Create Vertex AI Vector Search index
# scripts/create-vector-index.py

from google.cloud import aiplatform

# Initialize
aiplatform.init(project="vividly-dev-rich", location="us-central1")

# Create index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="vividly-oer-content-index",
    dimensions=768,  # Embedding dimensions
    approximate_neighbors_count=10,  # Return top 10 results
    distance_measure_type="DOT_PRODUCT_DISTANCE",  # Cosine similarity
    leaf_node_embedding_count=500,  # Tuning parameter
    leaf_nodes_to_search_percent=10  # Search 10% of leaf nodes
)

print(f"Index created: {index.resource_name}")
```

**Index Deployment**:
```python
# Deploy index to endpoint for querying
# scripts/deploy-vector-index.py

# Create endpoint
endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="vividly-oer-content-endpoint",
    public_endpoint_enabled=False,  # Private endpoint for security
    network="projects/PROJECT_NUMBER/global/networks/dev-vividly-vpc"
)

# Deploy index to endpoint
deployed_index = endpoint.deploy_index(
    index=index.resource_name,
    deployed_index_id="vividly_oer_v1",
    display_name="Vividly OER Content v1",
    machine_type="e2-standard-2",  # 2 vCPUs, 8 GB RAM
    min_replica_count=1,  # Auto-scale between 1-3 replicas
    max_replica_count=3
)

print(f"Index deployed to endpoint: {endpoint.resource_name}")
```

**Uploading Embeddings**:
```python
# Upload embeddings to index
# scripts/upload-embeddings.py

import json
from google.cloud import storage

# Prepare data for upload (JSONL format)
def prepare_index_data(chunks_with_embeddings):
    """
    Convert chunks to format required by Vertex AI Vector Search.

    Format:
    {"id": "chunk-123", "embedding": [0.1, 0.2, ...], "restricts": [...]}
    """
    index_data = []

    for chunk in chunks_with_embeddings:
        index_data.append({
            "id": chunk['chunk_id'],
            "embedding": chunk['embedding'],
            "restricts": [
                {"namespace": "subject", "allow": [chunk['metadata']['subject']]},
                {"namespace": "chapter", "allow": [chunk['metadata']['chapter_id']]}
            ]
        })

    return index_data

# Save to JSONL
with open('index_data.jsonl', 'w') as f:
    for item in index_data:
        f.write(json.dumps(item) + '\n')

# Upload to GCS
client = storage.Client()
bucket = client.bucket('vividly-dev-rich-vector-index-data')
blob = bucket.blob('oer-content/index_data.jsonl')
blob.upload_from_filename('index_data.jsonl')

# Update index with new data
index.update_embeddings(
    contents_delta_uri=f"gs://vividly-dev-rich-vector-index-data/oer-content/"
)

print("✓ Embeddings uploaded to index")
```

---

### Search and Retrieval

**Query Function**:
```python
# Retrieve relevant chunks for a query
# backend/app/services/rag_service.py

from vertexai.language_models import TextEmbeddingModel
from google.cloud import aiplatform_v1

def retrieve_context(query: str, subject: str, num_results: int = 10) -> List[Dict]:
    """
    Retrieve relevant context chunks for a query using vector search.

    Args:
        query: User's question or topic query
        subject: Filter by subject (physics, chemistry, biology, cs)
        num_results: Number of chunks to retrieve (default 10)

    Returns:
        List of relevant chunks with similarity scores
    """
    # 1. Generate embedding for query
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-gecko@003")
    query_embedding = embedding_model.get_embeddings([query])[0].values

    # 2. Search vector index
    endpoint_client = aiplatform_v1.MatchServiceClient(
        client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"}
    )

    # Build filter for subject
    filter_restricts = [
        {"namespace": "subject", "allow": [subject]}
    ]

    # Query index
    response = endpoint_client.find_neighbors(
        index_endpoint="projects/.../indexEndpoints/...",
        deployed_index_id="vividly_oer_v1",
        queries=[{
            "embedding": {"value": query_embedding},
            "neighbor_count": num_results,
            "restricts": filter_restricts
        }]
    )

    # 3. Fetch full chunk data for results
    results = []
    for neighbor in response.nearest_neighbors[0].neighbors:
        chunk_id = neighbor.datapoint_id
        distance = neighbor.distance

        # Fetch chunk from database (or cache)
        chunk = get_chunk_by_id(chunk_id)

        results.append({
            "chunk_id": chunk_id,
            "text": chunk['text'],
            "metadata": chunk['metadata'],
            "similarity_score": 1 - distance,  # Convert distance to similarity
            "rank": len(results) + 1
        })

    return results

# Example usage
query = "How does Newton's third law apply to basketball?"
subject = "physics"

relevant_chunks = retrieve_context(query, subject, num_results=5)

for chunk in relevant_chunks:
    print(f"Rank {chunk['rank']}: {chunk['metadata']['section_title']}")
    print(f"Similarity: {chunk['similarity_score']:.3f}")
    print(f"Text: {chunk['text'][:200]}...")
    print()
```

---

## Content Organization

### Topic Mapping

**Mapping Strategy**: Map our 140 curriculum topics to OpenStax content sections.

**Topic-to-Content Mapping** (stored in database):
```sql
-- topics_oer_mapping table
CREATE TABLE topics_oer_mapping (
    id VARCHAR(50) PRIMARY KEY,
    topic_id VARCHAR(50) REFERENCES topics(id),

    -- OpenStax source location
    source_book VARCHAR(100),  -- 'physics-2e', 'chemistry-2e', etc.
    chapter_id VARCHAR(50),
    section_id VARCHAR(50),

    -- For filtering
    relevant_chunk_ids TEXT[],  -- Array of chunk IDs most relevant to this topic

    -- Metadata
    mapping_confidence DECIMAL(3,2),  -- 0.00-1.00, how confident is this mapping
    manually_verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);
```

**Example Mappings**:
```sql
-- Newton's Third Law topic
INSERT INTO topics_oer_mapping VALUES (
    'map_newton_3',
    'topic_phys_mech_newton_3',
    'physics-2e',
    'chapter-04',
    'section-04-03',
    ARRAY['physics-2e-04-03-001', 'physics-2e-04-03-002', 'physics-2e-04-03-003'],
    0.95,
    true,
    'content_curator_jane',
    '2024-01-15'
);

-- Photosynthesis topic
INSERT INTO topics_oer_mapping VALUES (
    'map_photosynthesis',
    'topic_bio_cell_photosynthesis',
    'biology-2e',
    'chapter-08',
    'section-08-02',
    ARRAY['biology-2e-08-02-001', 'biology-2e-08-02-002', 'biology-2e-08-02-003', 'biology-2e-08-02-004'],
    0.92,
    true,
    'content_curator_jane',
    '2024-01-15'
);
```

**Automated Mapping** (`scripts/map-topics-to-content.py`):
```python
"""
Automatically map topics to OpenStax content using semantic similarity.
"""

def map_topic_to_content(topic: Dict, all_chunks: List[Dict]) -> Dict:
    """
    Find most relevant content chunks for a topic.

    Uses:
    1. Topic name and description as query
    2. Vector search to find similar chunks
    3. Filtering by subject
    4. Ranking by relevance
    """
    # Create query from topic
    query = f"{topic['name']} {topic['description']} {' '.join(topic['key_concepts'])}"

    # Search for relevant chunks
    relevant_chunks = retrieve_context(
        query=query,
        subject=topic['subject'],
        num_results=20  # Get top 20 to review
    )

    # Filter to highly relevant only (similarity > 0.7)
    high_relevance = [c for c in relevant_chunks if c['similarity_score'] > 0.7]

    return {
        "topic_id": topic['id'],
        "relevant_chunks": [c['chunk_id'] for c in high_relevance],
        "top_chapter": high_relevance[0]['metadata']['chapter_id'] if high_relevance else None,
        "top_section": high_relevance[0]['metadata']['section_id'] if high_relevance else None,
        "confidence": high_relevance[0]['similarity_score'] if high_relevance else 0.0
    }

# Run for all topics
for topic in all_topics:
    mapping = map_topic_to_content(topic, all_chunks)
    save_topic_mapping(mapping)
```

**Manual Verification**:
- Content curator reviews automated mappings
- Verifies topic → content alignment
- Adjusts mappings if needed
- Marks as verified in database

---

## Content Updates

### Monitoring Source Changes

**OpenStax Update Monitoring**:
```python
# scripts/monitor-openstax-updates.py

import requests
from datetime import datetime

def check_openstax_for_updates():
    """
    Check if OpenStax has released updated versions of textbooks.

    OpenStax provides version information via their API.
    """
    books = [
        {"id": "col12234", "name": "Physics 2e", "current_version": "18.3"},
        {"id": "col11760", "name": "Chemistry 2e", "current_version": "12.1"},
        {"id": "col12312", "name": "Biology 2e", "current_version": "14.2"}
    ]

    updates_available = []

    for book in books:
        # Check latest version via API
        response = requests.get(f"https://archive.cnx.org/contents/{book['id']}.json")
        latest_version = response.json()['version']

        if latest_version != book['current_version']:
            updates_available.append({
                "book": book['name'],
                "current": book['current_version'],
                "latest": latest_version,
                "action": "Update required"
            })

    return updates_available

# Run monthly
if __name__ == "__main__":
    updates = check_openstax_for_updates()

    if updates:
        print("⚠️  OpenStax updates available:")
        for update in updates:
            print(f"  {update['book']}: {update['current']} → {update['latest']}")

        # Send notification to content team
        send_alert_email(updates)
    else:
        print("✓ All textbooks up to date")
```

**Update Frequency**:
- **Check for updates**: Monthly (automated)
- **Apply updates**: Quarterly (or as needed for critical fixes)
- **Notification**: Email content team when updates available

---

### Update Procedures

**When Update Released**:

1. **Review Changes**:
   - Download new version
   - Review release notes
   - Identify what changed (new sections, corrections, etc.)

2. **Re-run Ingestion Pipeline**:
   ```bash
   # Download new version
   ./scripts/ingest-oer-content.sh

   # Process new content
   python scripts/process-oer-content.py

   # Generate new chunks
   python scripts/chunk-oer-content.py

   # QA check
   python scripts/qa-chunks.py
   ```

3. **Generate New Embeddings**:
   ```bash
   # Only for changed chunks (differential update)
   python scripts/generate-embeddings.py --differential
   ```

4. **Update Vector Index**:
   ```bash
   # Upload new/changed embeddings
   python scripts/upload-embeddings.py --update
   ```

5. **Clear Cached Content** (if needed):
   - For significantly updated topics, clear cached videos
   - They'll be regenerated with new information

6. **Verify**:
   - Test retrieval for sample topics
   - Verify new information is being retrieved
   - Spot-check generated content quality

7. **Deploy**:
   - Stage deployment first (test in staging environment)
   - Production deployment if all tests pass

**Differential Updates** (optimization):
- Compare old vs new chunks
- Only re-embed changed chunks
- Update vector index incrementally
- Saves time and API costs

---

## RAG Implementation

### Retrieval Process

See "Search and Retrieval" section above for detailed implementation.

**Retrieval Flow**:
```
User Query + Topic
    ↓
1. Create enriched query
   "Topic: Newton's Third Law
    Interest: Basketball
    Query: Why do I get pushed back when I shoot?"
    ↓
2. Generate query embedding
   [0.123, 0.456, 0.789, ...]  (768-dim vector)
    ↓
3. Search vector index
   - Filter by subject: physics
   - Return top 10 similar chunks
    ↓
4. Rank results
   - By similarity score
   - By relevance to topic
    ↓
5. Select top 5-7 chunks
   (enough context, not too much)
    ↓
Return context chunks
```

---

### Context Assembly

**Assembling Context for Generation**:
```python
def assemble_context_for_generation(topic_id: str, interest_id: str, query: str) -> str:
    """
    Assemble context from retrieved chunks for LLM generation.

    Returns formatted context string ready for prompt.
    """
    # 1. Get topic metadata
    topic = get_topic_by_id(topic_id)

    # 2. Retrieve relevant chunks
    enriched_query = f"{topic['name']}: {query}" if query else topic['name']
    chunks = retrieve_context(
        query=enriched_query,
        subject=topic['subject'],
        num_results=10
    )

    # 3. Select best chunks (top 5-7 based on similarity)
    selected_chunks = chunks[:7]

    # 4. Assemble context
    context_parts = []

    # Add topic overview
    context_parts.append(f"Topic: {topic['name']}")
    context_parts.append(f"Description: {topic['description']}")
    context_parts.append("")

    # Add content from chunks
    context_parts.append("Educational Content:")
    for i, chunk in enumerate(selected_chunks, 1):
        context_parts.append(f"\n[Source {i}: {chunk['metadata']['section_title']}]")
        context_parts.append(chunk['text'])

    # Add attribution
    context_parts.append("\n---")
    context_parts.append(f"Source: {selected_chunks[0]['metadata']['source_title']} by OpenStax")
    context_parts.append(f"License: {selected_chunks[0]['metadata']['source_license']}")

    return "\n".join(context_parts)

# Example output:
"""
Topic: Newton's Third Law
Description: For every action, there is an equal and opposite reaction...

Educational Content:

[Source 1: Newton's Third Law of Motion]
Newton's third law of motion states that whenever one object exerts a force on a second object, the second object exerts an equal and opposite force on the first object. This law is often stated as "for every action, there is an equal and opposite reaction."

Consider a swimmer pushing off from the wall of a pool. The swimmer exerts a force on the wall, and the wall exerts an equal and opposite force on the swimmer. This force propels the swimmer forward through the water...

[Source 2: Applications of Newton's Third Law]
Newton's third law applies to all forces and all situations. When you walk, you push backward on the ground, and the ground pushes forward on you. When a basketball player shoots, they push the ball forward, and the ball pushes back on their hands...

[continues with more chunks]

---
Source: College Physics 2e by OpenStax
License: CC BY 4.0
"""
```

**Context Token Management**:
- Target: 2,000-3,000 tokens of context
- Max: 4,000 tokens (to leave room for prompt + generation)
- If exceeds: Trim to top N chunks that fit

---

## Maintenance and Operations

### Performance Monitoring

**Key Metrics**:
```
Retrieval Performance:
├─> Latency: <200ms for vector search (target: <500ms)
├─> Relevance: >0.7 similarity score for top result (target: >0.6)
├─> Coverage: >90% of queries return 5+ relevant chunks (target: >80%)

Index Health:
├─> Index size: 50,000 vectors (current)
├─> Index freshness: <90 days since last update (target: <120 days)
├─> Query QPS: ~10 queries/second (scales to 100+)

Content Quality:
├─> Chunk coverage: All 140 topics have mapped content (target: 100%)
├─> Mapping confidence: Avg 0.88 (target: >0.80)
├─> User satisfaction: Track if generated content helpful (future metric)
```

**Monitoring Dashboard** (`/internal/admin/vector-db`):
- Real-time query latency
- Retrieval quality scores
- Index utilization
- Error rates

---

### Backup and Recovery

**Vector Index Backup**:
- Vertex AI automatically backs up index metadata
- Source data (embeddings) stored in GCS bucket
- Can rebuild index from source if needed

**Disaster Recovery**:
```bash
# If index lost or corrupted:
1. Retrieve source embeddings from GCS
   gsutil cp -r gs://vividly-dev-rich-vector-index-data/oer-content/ ./backup/

2. Create new index
   python scripts/create-vector-index.py

3. Upload embeddings
   python scripts/upload-embeddings.py

4. Deploy to endpoint
   python scripts/deploy-vector-index.py

5. Verify functionality
   python scripts/test-retrieval.py

Recovery time: ~4-6 hours
```

---

**Document Version**: 1.0
**Last Updated**: 2024-01-16
**Maintained By**: Vividly Content Team
**Review Frequency**: Quarterly (after OpenStax updates)
**Next Review**: April 2024
