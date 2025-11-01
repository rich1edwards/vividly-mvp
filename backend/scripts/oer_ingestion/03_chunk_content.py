#!/usr/bin/env python3
"""
Chunk OpenStax Content

Splits processed content into 500-word chunks with overlap.
"""

import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.chunker import TextChunker


def chunk_book(book_file: Path, output_dir: Path, chunker: TextChunker) -> dict:
    """
    Chunk a single processed book.

    Args:
        book_file: Path to processed JSON file
        output_dir: Directory for chunked output
        chunker: TextChunker instance

    Returns:
        Chunking statistics
    """
    book_id = book_file.stem
    print(f"Chunking: {book_id}")
    print("=" * 60)

    # Load processed book
    with open(book_file, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    print(f"  Title: {book_data['title']}")
    print(f"  Chapters: {len(book_data['chapters'])}")

    # Chunk content
    chunks = chunker.chunk_book(book_data)

    # Get statistics
    stats = chunker.get_chunk_statistics(chunks)

    print(f"  Chunks created: {stats['total_chunks']}")
    print(f"  Avg word count: {stats['avg_word_count']:.1f}")
    print(f"  Avg token count: {stats['avg_token_count']:.1f}")
    print(f"  Word count range: {stats['min_word_count']} - {stats['max_word_count']}")

    # Save chunks to JSON
    output_file = output_dir / f"{book_id}-chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved to: {output_file} ({file_size_mb:.2f} MB)")
    print("")

    return {
        "book_id": book_id,
        "title": book_data["title"],
        "chunks": stats["total_chunks"],
        "avg_word_count": stats["avg_word_count"],
        "avg_token_count": stats["avg_token_count"],
        "total_words": stats["total_words"],
        "total_tokens": stats["total_tokens"],
        "output_file": str(output_file),
        "size_mb": file_size_mb,
    }


def main():
    """Main chunking function."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    processed_dir = data_dir / "processed"
    chunks_dir = data_dir / "chunks"

    # Create output directory
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Initialize chunker
    chunker = TextChunker(target_size=500, min_size=300, max_size=800, overlap=50)

    print("=" * 60)
    print("OpenStax Content Chunking")
    print("=" * 60)
    print("")
    print("Chunking parameters:")
    print(f"  Target size: {chunker.target_size} words")
    print(f"  Min size: {chunker.min_size} words")
    print(f"  Max size: {chunker.max_size} words")
    print(f"  Overlap: {chunker.overlap} words")
    print("")

    # Find all processed books
    book_files = list(processed_dir.glob("*.json"))

    if not book_files:
        print("✗ Error: No processed books found in:", processed_dir)
        print("Run 02_process_content.py first")
        sys.exit(1)

    # Process all books
    results = []
    for book_file in book_files:
        try:
            result = chunk_book(book_file, chunks_dir, chunker)
            results.append(result)
        except Exception as e:
            print(f"✗ Error chunking {book_file.stem}: {e}")
            print("")

    # Summary
    print("=" * 60)
    print("Chunking Summary")
    print("=" * 60)
    print("")

    if results:
        total_chunks = 0
        total_words = 0
        total_tokens = 0

        for result in results:
            print(f"✓ {result['book_id']}")
            print(f"    Chunks: {result['chunks']}")
            print(f"    Avg words/chunk: {result['avg_word_count']:.1f}")
            print(f"    Avg tokens/chunk: {result['avg_token_count']:.1f}")
            print(f"    Size: {result['size_mb']:.2f} MB")
            print("")

            total_chunks += result["chunks"]
            total_words += result["total_words"]
            total_tokens += result["total_tokens"]

        print(f"Totals:")
        print(f"  Books: {len(results)}")
        print(f"  Total chunks: {total_chunks:,}")
        print(f"  Total words: {total_words:,}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Avg words/chunk: {total_words / total_chunks:.1f}")
        print(f"  Avg tokens/chunk: {total_tokens / total_chunks:.1f}")
        print("")

        # Cost estimate
        # Vertex AI text-embedding-gecko@003: $0.00001 per 1K characters
        # Approximate: 1 token ≈ 4 characters
        total_chars = total_tokens * 4
        cost = (total_chars / 1000) * 0.00001
        print(f"Estimated embedding cost: ${cost:.2f}")
        print("")

    print("Next step: python 04_generate_embeddings.py")


if __name__ == "__main__":
    main()
