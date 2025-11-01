#!/usr/bin/env python3
"""
Generate Embeddings

Generates 768-dim embeddings using Vertex AI text-embedding-gecko@003.
"""

import os
import json
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.vertex_ai_client import VertexAIEmbeddings


def generate_embeddings_for_book(
    chunks_file: Path,
    output_dir: Path,
    embeddings_client: VertexAIEmbeddings,
    batch_size: int = 5,
) -> dict:
    """
    Generate embeddings for a single book's chunks.

    Args:
        chunks_file: Path to chunks JSON file
        output_dir: Directory for embedding output
        embeddings_client: VertexAIEmbeddings instance
        batch_size: Batch size for API calls

    Returns:
        Generation statistics
    """
    book_id = chunks_file.stem.replace("-chunks", "")
    print(f"Generating embeddings: {book_id}")
    print("=" * 60)

    # Load chunks
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"  Total chunks: {len(chunks)}")

    # Generate embeddings
    start_time = datetime.now()
    embedded_chunks = embeddings_client.generate_embeddings(
        chunks, batch_size=batch_size
    )
    duration = (datetime.now() - start_time).total_seconds()

    print(f"  Duration: {duration:.1f} seconds")
    print(f"  Rate: {len(embedded_chunks) / duration:.1f} chunks/sec")

    # Save embeddings
    output_file = output_dir / f"{book_id}-embeddings.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(embedded_chunks, f, indent=2, ensure_ascii=False)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved to: {output_file} ({file_size_mb:.2f} MB)")
    print("")

    return {
        "book_id": book_id,
        "chunks": len(chunks),
        "embedded": len(embedded_chunks),
        "duration_seconds": duration,
        "rate": len(embedded_chunks) / duration,
        "output_file": str(output_file),
        "size_mb": file_size_mb,
    }


def main():
    """Main embedding generation function."""
    # Get project ID from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("✗ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("")
        print("Set it with:")
        print("  export GOOGLE_CLOUD_PROJECT=vividly-dev-rich")
        sys.exit(1)

    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    chunks_dir = data_dir / "chunks"
    embeddings_dir = data_dir / "embeddings"

    # Create output directory
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("OpenStax Content Embedding Generation")
    print("=" * 60)
    print("")
    print(f"Project: {project_id}")
    print(f"Model: text-embedding-gecko@003")
    print(f"Region: us-central1")
    print("")

    # Find all chunked books
    chunks_files = list(chunks_dir.glob("*-chunks.json"))

    if not chunks_files:
        print("✗ Error: No chunked books found in:", chunks_dir)
        print("Run 03_chunk_content.py first")
        sys.exit(1)

    print(f"Found {len(chunks_files)} book(s) to embed")
    print("")

    # Initialize embeddings client
    embeddings_client = VertexAIEmbeddings(
        project_id=project_id, location="us-central1"
    )

    # Process all books
    results = []
    start_time = datetime.now()

    for chunks_file in chunks_files:
        try:
            result = generate_embeddings_for_book(
                chunks_file, embeddings_dir, embeddings_client, batch_size=5
            )
            results.append(result)
        except Exception as e:
            print(f"✗ Error embedding {chunks_file.stem}: {e}")
            print("")
            import traceback

            traceback.print_exc()

    total_duration = (datetime.now() - start_time).total_seconds()

    # Summary
    print("=" * 60)
    print("Embedding Generation Summary")
    print("=" * 60)
    print("")

    if results:
        total_chunks = 0
        total_embedded = 0
        total_size = 0

        for result in results:
            print(f"✓ {result['book_id']}")
            print(f"    Chunks: {result['chunks']}")
            print(f"    Embedded: {result['embedded']}")
            print(f"    Duration: {result['duration_seconds']:.1f}s")
            print(f"    Rate: {result['rate']:.1f} chunks/sec")
            print(f"    Size: {result['size_mb']:.2f} MB")
            print("")

            total_chunks += result["chunks"]
            total_embedded += result["embedded"]
            total_size += result["size_mb"]

        print(f"Totals:")
        print(f"  Books: {len(results)}")
        print(f"  Total chunks: {total_chunks:,}")
        print(f"  Total embedded: {total_embedded:,}")
        print(f"  Total duration: {total_duration / 60:.1f} minutes")
        print(f"  Avg rate: {total_embedded / total_duration:.1f} chunks/sec")
        print(f"  Total size: {total_size:.2f} MB")
        print("")

        # Cost calculation
        # text-embedding-gecko@003: $0.000025 per 1,000 characters
        # Estimate 500 words/chunk × 5 chars/word = 2,500 chars/chunk
        avg_chars_per_chunk = 2500
        total_chars = total_embedded * avg_chars_per_chunk
        cost = (total_chars / 1000) * 0.000025
        print(f"Estimated cost: ${cost:.2f}")
        print("")

    print("Next step: python 05_create_vector_index.py")


if __name__ == "__main__":
    main()
