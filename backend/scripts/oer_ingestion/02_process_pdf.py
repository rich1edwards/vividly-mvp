#!/usr/bin/env python3
"""
Process OpenStax PDFs

Extracts text from PDF files and structures as JSON compatible with
the existing chunking pipeline.

Architecture: Designed to be robust and maintainable
- Chapter detection via multiple heuristics
- Content block extraction with type classification
- Page number tracking for reference
- Error handling and progress reporting
"""

import pymupdf  # PyMuPDF
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


# Book metadata mapping
BOOKS = {
    "physics_2e": {
        "subject": "physics",
        "title": "College Physics 2e",
        "grade_level": "9-12",
    },
    "chemistry_2e": {
        "subject": "chemistry",
        "title": "Chemistry 2e",
        "grade_level": "9-12",
    },
    "biology_2e": {
        "subject": "biology",
        "title": "Biology 2e",
        "grade_level": "9-12",
    },
    "precalculus_2e": {
        "subject": "mathematics",
        "title": "Precalculus 2e",
        "grade_level": "9-12",
    },
}


class PDFProcessor:
    """
    Extracts structured content from OpenStax PDFs.

    Design Philosophy (Andrew Ng):
    - Start simple, measure, iterate
    - Handle errors gracefully
    - Build for maintainability
    """

    def __init__(self, min_paragraph_length: int = 50):
        """
        Initialize PDF processor.

        Args:
            min_paragraph_length: Minimum characters for valid paragraph
        """
        self.min_paragraph_length = min_paragraph_length

        # Chapter detection patterns (multiple heuristics for robustness)
        # Must be strict to avoid false positives (addresses, page numbers, etc.)
        self.chapter_patterns = [
            r"^Chapter\s+(\d{1,2})\s*[:\-]\s*(.+)$",  # "Chapter 1: Introduction" or "Chapter 1 - Introduction"
            r"^CHAPTER\s+(\d{1,2})\s*[:\-]\s*(.+)$",  # "CHAPTER 1: INTRODUCTION"
            r"^(\d{1,2})\.\s+([A-Z][a-zA-Z\s]{10,})$",  # "1. Introduction to Physics" (at least 10 chars)
        ]

    def extract_text_from_pdf(self, pdf_path: Path) -> Dict:
        """
        Extract structured content from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Structured book data with chapters and content blocks
        """
        print(f"  Opening PDF: {pdf_path.name}")
        doc = pymupdf.open(str(pdf_path))

        print(f"  Total pages: {len(doc)}")

        chapters = []
        current_chapter = None
        page_texts = []

        # First pass: Extract all page texts
        for page_num, page in enumerate(doc):
            text = page.get_text()
            page_texts.append((page_num + 1, text))

        # Track seen chapters to avoid duplicates (TOC vs actual content)
        seen_chapters = set()

        # Second pass: Detect chapters and extract content
        for page_num, text in page_texts:
            # Try to detect chapter start
            chapter_info = self._detect_chapter(text)

            if chapter_info:
                chapter_num, chapter_title = chapter_info

                # Skip if we've already seen this chapter (avoid TOC duplicates)
                if chapter_num in seen_chapters:
                    continue

                seen_chapters.add(chapter_num)

                # Save previous chapter
                if current_chapter and current_chapter["content_blocks"]:
                    chapters.append(current_chapter)

                # Start new chapter
                current_chapter = {
                    "id": f"ch{chapter_num:02d}",  # e.g., "ch01", "ch02"
                    "title": f"Chapter {chapter_num}: {chapter_title}",
                    "number": chapter_num,
                    "content_blocks": [],
                }
                print(f"    Found: Chapter {chapter_num}")

            # Extract content blocks from this page
            if current_chapter:
                content_blocks = self._extract_content_blocks(text, page_num)
                current_chapter["content_blocks"].extend(content_blocks)

        # Save final chapter
        if current_chapter and current_chapter["content_blocks"]:
            chapters.append(current_chapter)

        doc.close()

        return chapters

    def _detect_chapter(self, text: str) -> Tuple[int, str] | None:
        """
        Detect chapter start using OpenStax-specific pattern.

        OpenStax PDFs have a specific structure:
        - Line 1: "INTRODUCTION"
        - Line 2: "CHAPTER X"
        - Line 3: Chapter title

        Args:
            text: Page text to analyze

        Returns:
            Tuple of (chapter_number, chapter_title) or None
        """
        lines = text.split("\n")

        # Look for the OpenStax pattern in first 20 lines
        for i in range(min(20, len(lines) - 2)):
            line1 = lines[i].strip()
            line2 = lines[i + 1].strip() if i + 1 < len(lines) else ""
            line3 = lines[i + 2].strip() if i + 2 < len(lines) else ""

            # Pattern 1: INTRODUCTION + CHAPTER X + Title
            if line1 == "INTRODUCTION":
                chapter_match = re.match(
                    r"^CHAPTER\s+(\d{1,2})\s*$", line2, re.IGNORECASE
                )
                if chapter_match and line3 and len(line3) > 3:
                    chapter_num = int(chapter_match.group(1))
                    return (chapter_num, line3)

            # Pattern 2: Just CHAPTER X followed by title (for chapters without intro)
            chapter_match = re.match(r"^CHAPTER\s+(\d{1,2})\s*$", line1, re.IGNORECASE)
            if chapter_match and line2 and len(line2) > 3:
                # Make sure line2 isn't a section number
                if not re.match(r"^\d+\.\d+", line2):
                    chapter_num = int(chapter_match.group(1))
                    return (chapter_num, line2)

        return None

    def _extract_content_blocks(self, text: str, page_num: int) -> List[Dict]:
        """
        Extract content blocks from page text.

        Args:
            text: Page text
            page_num: Page number for reference

        Returns:
            List of content blocks with type and text
        """
        blocks = []

        # Split into paragraphs (double newline or large indent change)
        paragraphs = re.split(r"\n\s*\n", text)

        for para in paragraphs:
            para = para.strip()

            # Skip if too short
            if len(para) < self.min_paragraph_length:
                continue

            # Detect content type and extract metadata
            block_type, extra_fields = self._classify_block(para)

            # Create content block
            block = {
                "type": block_type,
                "text": para,
                "page_number": page_num,
            }
            # Add any extra fields (title, caption, etc.)
            block.update(extra_fields)

            blocks.append(block)

        return blocks

    def _classify_block(self, text: str) -> tuple[str, dict]:
        """
        Classify content block type and extract metadata.

        Args:
            text: Block text

        Returns:
            Tuple of (block_type, extra_fields)
        """
        text_lower = text.lower()

        # Learning objectives
        if any(
            keyword in text_lower
            for keyword in [
                "learning objective",
                "by the end of this",
                "you will be able to",
            ]
        ):
            return ("learning_objective", {})

        # Examples
        if text.startswith("Example") or "EXAMPLE" in text[:20]:
            # Extract example title if present
            lines = text.split("\n", 1)
            title = lines[0] if lines else "Example"
            return ("example", {"title": title})

        # Figures (captions)
        if text.startswith("Figure") or text.startswith("Fig."):
            return ("figure", {"caption": text})

        # Default: paragraph
        return ("paragraph", {})


def process_book(
    book_id: str, raw_dir: Path, output_dir: Path, processor: PDFProcessor
) -> Dict:
    """
    Process a single book PDF.

    Args:
        book_id: Book identifier
        raw_dir: Directory containing raw PDFs
        output_dir: Directory for processed JSON output
        processor: PDFProcessor instance

    Returns:
        Processing statistics
    """
    print(f"Processing: {book_id}")
    print("=" * 60)

    if book_id not in BOOKS:
        print(f"  ✗ Error: Unknown book_id: {book_id}")
        return {"error": "Unknown book_id"}

    book_config = BOOKS[book_id]
    pdf_file = raw_dir / f"{book_id}.pdf"

    if not pdf_file.exists():
        print(f"  ✗ Error: PDF not found: {pdf_file}")
        return {"error": "PDF not found"}

    # Extract content
    try:
        chapters = processor.extract_text_from_pdf(pdf_file)
    except Exception as e:
        print(f"  ✗ Error processing PDF: {e}")
        return {"error": str(e)}

    # Count content
    total_chapters = len(chapters)
    total_blocks = sum(len(ch["content_blocks"]) for ch in chapters)

    print(f"  Title: {book_config['title']}")
    print(f"  Subject: {book_config['subject']}")
    print(f"  Chapters: {total_chapters}")
    print(f"  Content blocks: {total_blocks}")

    # Build book data structure
    book_data = {
        "title": book_config["title"],
        "subject": book_config["subject"],
        "grade_level": book_config["grade_level"],
        "chapters": chapters,
    }

    # Save to JSON
    output_file = output_dir / f"{book_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(book_data, f, indent=2, ensure_ascii=False)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved to: {output_file} ({file_size_mb:.2f} MB)")
    print("")

    return {
        "book_id": book_id,
        "title": book_data["title"],
        "chapters": total_chapters,
        "content_blocks": total_blocks,
        "output_file": str(output_file),
        "size_mb": file_size_mb,
    }


def main():
    """Main processing function."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    raw_dir = data_dir / "raw_pdf"
    processed_dir = data_dir / "processed"

    # Create output directory
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("OpenStax PDF Content Processing")
    print("=" * 60)
    print("")

    # Initialize processor
    processor = PDFProcessor()

    # Process all books
    results = []
    for book_id in BOOKS.keys():
        result = process_book(book_id, raw_dir, processed_dir, processor)
        results.append(result)

    # Summary
    print("=" * 60)
    print("Processing Complete")
    print("=" * 60)
    print("")

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    print(f"Processed books: {len(successful)}/{len(results)}")

    if successful:
        print("")
        print("Successful:")
        for result in successful:
            print(
                f"  ✓ {result['book_id']}: {result['chapters']} chapters, "
                f"{result['content_blocks']} blocks ({result['size_mb']:.2f} MB)"
            )

    if failed:
        print("")
        print("Failed:")
        for result in failed:
            print(
                f"  ✗ {result.get('book_id', 'unknown')}: {result.get('error', 'Unknown error')}"
            )

    print("")
    print("Next step: python 03_chunk_content.py")


if __name__ == "__main__":
    main()
