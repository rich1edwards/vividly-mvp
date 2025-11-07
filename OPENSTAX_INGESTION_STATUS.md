# OpenStax OER Content Ingestion - Session Handoff
**Date**: 2025-11-03
**Session Duration**: ~2 hours
**Status**: 60% Complete - Ready for PDF Processing
**Methodology**: Andrew Ng's Systematic Approach

---

## Executive Summary

Successfully pivoted from CNXML-based to PDF-based OpenStax ingestion after discovering **archive.cnx.org is completely offline**. Downloaded 4 textbooks (980 MB) covering 3 science + 1 math subjects for grades 9-12. PyMuPDF installed and ready. Next step: Build PDF text extractor.

---

## Critical Architectural Decision

### Problem Discovered:
The entire **archive.cnx.org domain is unreachable**:
- HTTPS port 443: Connection timeout
- HTTP port 80: Connection timeout
- legacy.cnx.org: Connection timeout
- API endpoints: Connection timeout

**Impact**: Original CNXML-based pipeline (scripts 02-05) cannot run.

### Solution Implemented:
**Pivoted to PDF-based ingestion** using OpenStax CloudFront CDN:
- ✅ PDFs are accessible and reliable
- ✅ Official distribution format from OpenStax
- ✅ CloudFront infrastructure is production-grade
- ✅ Reversible if archive.cnx.org comes back online

---

## What's Completed (60%)

### 1. ✅ PDF URL Discovery
Found 4 of 6 textbooks (67% MVP coverage):

**Science (Grades 9-12)**:
- ✅ **Physics 2e**: 273 MB - `College_Physics_2e-WEB.pdf`
- ✅ **Chemistry 2e**: 209 MB - `Chemistry2e-WEB.pdf`
- ✅ **Biology 2e**: 385 MB - `Biology2e-WEB.pdf`

**Math (Grades 9-12)**:
- ✅ **Precalculus 2e**: 113 MB - `Precalculus_2e-WEB.pdf`
- ❌ **Algebra & Trigonometry**: URL not found (yet)
- ❌ **College Algebra**: URL not found (yet)

**Total Downloaded**: 980 MB (4 books)

### 2. ✅ Download Script Created
**File**: `/backend/scripts/oer_ingestion/01_download_openstax_pdf.sh`

**Features**:
- Bash 3.x compatible (no associative arrays needed)
- Simple pipe-delimited format: `"book_id|url"`
- Idempotent (skips already-downloaded files)
- Progress tracking with file sizes
- Executable and tested

**Usage**:
```bash
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend/scripts/oer_ingestion
./01_download_openstax_pdf.sh
```

### 3. ✅ PDFs Downloaded Successfully
**Location**: `/backend/scripts/oer_ingestion/data/raw_pdf/`

```
physics_2e.pdf      (273 MB) ✅
chemistry_2e.pdf    (209 MB) ✅
biology_2e.pdf      (385 MB) ✅
precalculus_2e.pdf  (113 MB) ✅
```

**Download Duration**: ~1 minute total (fast CloudFront speeds)

### 4. ✅ PyMuPDF Installed
**Package**: `pymupdf`
**Version**: 1.26.5
**Status**: Installed and ready

**Verification**:
```python
python3 -c "import pymupdf; print('PyMuPDF ready')"
```

### 5. ✅ Pipeline Architecture Analyzed
Studied existing chunking infrastructure:
- **Input Expected**: JSON with `title`, `subject`, `chapters[]`
- **Chapter Structure**: `content_blocks[]` with `type` and `text`
- **Chunker Ready**: `utils/chunker.py` works with any structured content

---

## What Remains (40%)

### Next Steps (In Order):

#### 1. **Build PDF Text Extractor** (~1.5 hours)
**File to Create**: `/backend/scripts/oer_ingestion/02_process_pdf.py`

**Requirements**:
- Extract text from PDF using PyMuPDF
- Detect chapter boundaries (look for "Chapter N" headers)
- Structure as JSON compatible with existing chunker
- Handle figures/images (extract captions)
- Preserve page numbers for reference

**Expected JSON Output**:
```json
{
  "title": "College Physics 2e",
  "subject": "physics",
  "chapters": [
    {
      "title": "Chapter 1: Introduction",
      "number": 1,
      "content_blocks": [
        {
          "type": "paragraph",
          "text": "Physics is the study of...",
          "page_number": 15
        }
      ]
    }
  ]
}
```

**Implementation Hints**:
```python
import pymupdf  # formerly known as fitz
import json
import re

def extract_pdf_text(pdf_path):
    doc = pymupdf.open(pdf_path)
    chapters = []

    for page in doc:
        text = page.get_text()
        # Detect chapter headers with regex
        # Group paragraphs into content_blocks
        # ...

    return {
        "title": "...",
        "subject": "...",
        "chapters": chapters
    }
```

#### 2. **Test with One Book** (~30 minutes)
Run PDF processor on `chemistry_2e.pdf` (smallest science book):
```bash
cd /backend/scripts/oer_ingestion
python3 02_process_pdf.py
```

**Validation**:
- Check JSON structure matches expected format
- Verify chapter detection worked
- Spot-check text extraction quality
- Ensure no encoding issues

#### 3. **Run Full Ingestion Pipeline** (~1 hour)
Execute remaining pipeline stages for all 4 books:

```bash
# Stage 2: Process PDFs → JSON
python3 02_process_pdf.py

# Stage 3: Chunk content → 500-word chunks
python3 03_chunk_content.py

# Stage 4: Generate embeddings → 768-dim vectors
python3 04_generate_embeddings.py

# Stage 5: Create vector index → Vertex AI Matching Engine
python3 05_create_vector_index.py
```

**Expected Output**:
- `data/processed/*.json` (4 files, ~10-20 MB each)
- `data/chunks/*-chunks.json` (4 files, ~5-10 MB each)
- Embeddings uploaded to GCS
- Vector index created in Vertex AI

---

## Database Status

### Tables Ready:
```sql
content_chunks      (0 records) ✅
content_sources     (0 records) ✅
vector_indexes      (0 records) ✅
```

**Verified**: All tables exist and are empty, ready for data ingestion.

---

## Key Files Modified/Created

### New Files:
1. `/backend/scripts/oer_ingestion/01_download_openstax_pdf.sh` (73 lines)
   - PDF download script
   - Bash 3.x compatible

### Files to Create (Next Session):
1. `/backend/scripts/oer_ingestion/02_process_pdf.py` (~150-200 lines)
   - PDF text extraction
   - Chapter detection
   - JSON formatting

### Existing Files (Unchanged):
1. `/backend/scripts/oer_ingestion/03_chunk_content.py` ✅ Ready
2. `/backend/scripts/oer_ingestion/04_generate_embeddings.py` ✅ Ready
3. `/backend/scripts/oer_ingestion/05_create_vector_index.py` ✅ Ready
4. `/backend/scripts/oer_ingestion/utils/chunker.py` ✅ Ready

---

## Technical Decisions & Rationale

### 1. **PDF vs CNXML**
**Decision**: Use PDFs from CloudFront
**Reason**: archive.cnx.org is completely offline
**Trade-off**: Less structured data, but more reliable source
**Mitigation**: Smart regex-based chapter detection

### 2. **4 Books vs 6 Books**
**Decision**: Start with 4 accessible books
**Reason**: 67% coverage is sufficient for MVP
**MVP Philosophy**: Ship something working, iterate later
**Future**: Add Algebra & Trig + College Algebra when URLs found

### 3. **Bash 3.x Compatibility**
**Decision**: Use pipe-delimited arrays instead of associative arrays
**Reason**: macOS still ships with Bash 3.x by default
**Implementation**: `"key|value"` format with parameter expansion
**Result**: Works on all systems without requiring Bash 4+

---

## Performance Metrics

### Session Stats:
- **Duration**: ~2 hours
- **Downloads**: 980 MB in ~1 minute
- **Scripts Created**: 1 (73 lines)
- **Dependencies Installed**: 1 (PyMuPDF)
- **Bugs Fixed**: 2 (Bash array syntax issues)

### Resource Usage:
- **Disk Space**: 980 MB (PDFs)
- **Network**: ~980 MB download
- **CPU**: Minimal (downloads only)

---

## Next Session Quick Start

### Commands to Run:

```bash
# 1. Verify PDFs downloaded
ls -lh /Users/richedwards/AI-Dev-Projects/Vividly/backend/scripts/oer_ingestion/data/raw_pdf/

# Expected output:
# physics_2e.pdf      (273 MB)
# chemistry_2e.pdf    (209 MB)
# biology_2e.pdf      (385 MB)
# precalculus_2e.pdf  (113 MB)

# 2. Verify PyMuPDF installed
python3 -c "import pymupdf; print('PyMuPDF ready')"

# 3. Navigate to oer_ingestion directory
cd /Users/richedwards/AI-Dev-Projects/Vividly/backend/scripts/oer_ingestion

# 4. Create 02_process_pdf.py (the main work)
# Use PyMuPDF to extract text and structure as JSON

# 5. Test with one book
python3 02_process_pdf.py

# 6. Run full pipeline
python3 03_chunk_content.py
python3 04_generate_embeddings.py
python3 05_create_vector_index.py
```

---

## Code Snippet for PDF Processor

```python
#!/usr/bin/env python3
"""
Process OpenStax PDFs

Extracts text from PDF files and structures as JSON for chunking.
"""

import pymupdf  # PyMuPDF
import json
import re
from pathlib import Path

# Book metadata mapping
BOOKS = {
    "physics_2e": {"subject": "physics", "title": "College Physics 2e"},
    "chemistry_2e": {"subject": "chemistry", "title": "Chemistry 2e"},
    "biology_2e": {"subject": "biology", "title": "Biology 2e"},
    "precalculus_2e": {"subject": "mathematics", "title": "Precalculus 2e"},
}

def extract_chapters(pdf_path):
    """Extract chapters from PDF."""
    doc = pymupdf.open(pdf_path)
    chapters = []
    current_chapter = None

    for page_num, page in enumerate(doc):
        text = page.get_text()

        # Detect chapter headers (regex pattern)
        chapter_match = re.search(r'^Chapter\s+(\d+)[:\s]+(.+)$', text, re.MULTILINE)

        if chapter_match:
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = {
                "title": f"Chapter {chapter_match.group(1)}: {chapter_match.group(2)}",
                "number": int(chapter_match.group(1)),
                "content_blocks": []
            }

        # Add paragraph blocks
        if current_chapter:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                if len(para.strip()) > 50:  # Filter noise
                    current_chapter["content_blocks"].append({
                        "type": "paragraph",
                        "text": para.strip(),
                        "page_number": page_num + 1
                    })

    if current_chapter:
        chapters.append(current_chapter)

    return chapters

def main():
    script_dir = Path(__file__).parent
    raw_dir = script_dir / "data" / "raw_pdf"
    processed_dir = script_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    for book_id, metadata in BOOKS.items():
        pdf_file = raw_dir / f"{book_id}.pdf"
        if not pdf_file.exists():
            print(f"Skipping {book_id}: PDF not found")
            continue

        print(f"Processing: {book_id}")
        chapters = extract_chapters(pdf_file)

        book_data = {
            "title": metadata["title"],
            "subject": metadata["subject"],
            "chapters": chapters
        }

        output_file = processed_dir / f"{book_id}.json"
        with open(output_file, "w") as f:
            json.dump(book_data, f, indent=2)

        print(f"  ✓ Saved: {output_file}")
        print(f"  Chapters: {len(chapters)}")

if __name__ == "__main__":
    main()
```

---

## Blockers & Risks

### Current Blockers:
**None** - All prerequisites completed ✅

### Potential Risks:

1. **PDF Text Extraction Quality**
   - **Risk**: OCR issues, formatting problems
   - **Mitigation**: Test with one book first, validate output
   - **Severity**: MEDIUM

2. **Chapter Detection**
   - **Risk**: Inconsistent chapter header formats across books
   - **Mitigation**: Use flexible regex patterns, manual verification
   - **Severity**: LOW-MEDIUM

3. **Token Context Limits**
   - **Risk**: Large books may exceed embedding limits
   - **Mitigation**: Existing chunking handles this (500 words/chunk)
   - **Severity**: LOW (already solved)

---

## Success Criteria

### MVP Success (Minimum):
- ✅ 4 books downloaded
- ⏳ PDF text extraction working for 1 book
- ⏳ Chunking pipeline produces embeddings
- ⏳ Vector index created in Vertex AI

### Full Success (Ideal):
- ⏳ All 4 books processed end-to-end
- ⏳ Chunks loaded into PostgreSQL
- ⏳ Vector search functional
- ⏳ RAG service can retrieve relevant content

---

## Estimated Time to Complete

**Remaining Work**: ~3-4 hours

| Task | Est. Time | Complexity |
|------|-----------|------------|
| Build PDF processor | 1.5 hours | Medium |
| Test with one book | 0.5 hours | Low |
| Run full pipeline (4 books) | 1 hour | Low |
| Database ingestion | 0.5 hours | Low |
| End-to-end validation | 0.5 hours | Low |

**Total**: 3-4 hours to fully working RAG system with 4 textbooks

---

## Andrew Ng Principles Applied

1. ✅ **Measure Everything**: Tracked file sizes, download times, script execution
2. ✅ **Fix One Thing at a Time**: Systematic URL discovery, script debugging
3. ✅ **Document Thoroughly**: This handoff document
4. ✅ **Build It Right**: Chose reliable PDFs over broken CNXML source
5. ✅ **Think About the Future**: Designed for easy addition of 2 missing books

---

## Questions for Next Session

1. Should we invest time finding Algebra & Trig URLs, or proceed with 4 books?
2. Do we need any specific filtering for grade level appropriateness?
3. Should figures/diagrams be processed, or text-only for MVP?
4. What's the acceptable chunking quality threshold before moving forward?

---

**Status**: ✅ **READY FOR NEXT SESSION**
**Next Step**: Build `/backend/scripts/oer_ingestion/02_process_pdf.py`
**Estimated Next Session**: 3-4 hours to completion

---

**Report Generated**: 2025-11-03
**Session**: OpenStax Ingestion Setup
**Methodology**: Andrew Ng's Systematic Approach
