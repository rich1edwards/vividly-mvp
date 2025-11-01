#!/usr/bin/env python3
"""
Process OpenStax Content

Parses CNXML files and extracts structured content to JSON.
"""

import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.xml_parser import CNXMLParser


# Book configurations
BOOKS = {
    "physics-2e": {"subject": "physics", "title": "College Physics 2e"},
    "chemistry-2e": {"subject": "chemistry", "title": "Chemistry 2e"},
    "biology-2e": {"subject": "biology", "title": "Biology 2e"},
}


def process_book(book_id: str, raw_dir: Path, output_dir: Path) -> dict:
    """
    Process a single book.

    Args:
        book_id: Book identifier (e.g., 'physics-2e')
        raw_dir: Directory containing raw CNXML files
        output_dir: Directory for processed JSON output

    Returns:
        Processing statistics
    """
    print(f"Processing: {book_id}")
    print("=" * 60)

    book_config = BOOKS[book_id]
    book_dir = raw_dir / book_id

    if not book_dir.exists():
        print(f"  ✗ Error: Directory not found: {book_dir}")
        return {"error": "Directory not found"}

    # Parse book
    parser = CNXMLParser()
    try:
        book_data = parser.parse_book(str(book_dir), book_config["subject"])
    except Exception as e:
        print(f"  ✗ Error parsing book: {e}")
        return {"error": str(e)}

    # Count content
    total_chapters = len(book_data["chapters"])
    total_blocks = sum(len(ch["content_blocks"]) for ch in book_data["chapters"])

    print(f"  Title: {book_data['title']}")
    print(f"  Subject: {book_data['subject']}")
    print(f"  Chapters: {total_chapters}")
    print(f"  Content blocks: {total_blocks}")

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
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create output directory
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("OpenStax Content Processing")
    print("=" * 60)
    print("")

    # Process all books
    results = []
    for book_id in BOOKS.keys():
        result = process_book(book_id, raw_dir, processed_dir)
        results.append(result)

    # Summary
    print("=" * 60)
    print("Processing Summary")
    print("=" * 60)
    print("")

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    if successful:
        print("Successfully processed:")
        total_chapters = 0
        total_blocks = 0
        total_size = 0

        for result in successful:
            print(f"  ✓ {result['book_id']}")
            print(f"      Chapters: {result['chapters']}")
            print(f"      Content blocks: {result['content_blocks']}")
            print(f"      Size: {result['size_mb']:.2f} MB")
            print("")

            total_chapters += result["chapters"]
            total_blocks += result["content_blocks"]
            total_size += result["size_mb"]

        print(f"Totals:")
        print(f"  Books: {len(successful)}")
        print(f"  Chapters: {total_chapters}")
        print(f"  Content blocks: {total_blocks}")
        print(f"  Total size: {total_size:.2f} MB")
        print("")

    if failed:
        print("Failed:")
        for result in failed:
            print(f"  ✗ {result.get('book_id', 'unknown')}: {result['error']}")
        print("")

    print("Next step: python 03_chunk_content.py")


if __name__ == "__main__":
    main()
