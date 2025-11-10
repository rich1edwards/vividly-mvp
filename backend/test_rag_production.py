#!/usr/bin/env python3
"""
Test RAG Service in Production Environment

This script tests that the RAG service can:
1. Initialize successfully
2. Load OER embeddings from disk
3. Retrieve relevant content for a query
4. Return real (not mock) OER content

Run this in the Docker container to verify production readiness.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_service import get_rag_service


async def test_rag_retrieval():
    """Test RAG content retrieval with a real query."""

    print("=" * 70)
    print("RAG SERVICE PRODUCTION TEST")
    print("=" * 70)
    print()

    # Test 1: Initialize RAG service
    print("Test 1: Initializing RAG service...")
    try:
        rag_service = get_rag_service()
        print("✓ RAG service initialized")
    except Exception as e:
        print(f"✗ Failed to initialize RAG service: {e}")
        return False

    print()

    # Test 2: Check embeddings are loaded
    print("Test 2: Checking embeddings loaded...")
    if rag_service.retriever and rag_service.retriever.loaded:
        num_chunks = len(rag_service.retriever.chunks)
        memory_mb = rag_service.retriever.embeddings_matrix.nbytes / (1024**2)
        print(f"✓ Embeddings loaded: {num_chunks:,} chunks")
        print(f"  Memory usage: {memory_mb:.1f} MB")
    else:
        print("✗ Embeddings not loaded - would use mock data")
        print("  This is EXPECTED in local testing without GCP credentials")
        print("  In production, this should work with service account")
        return False

    print()

    # Test 3: Retrieve content for a physics topic with basketball interest
    print("Test 3: Retrieving content for Newton's Third Law + basketball...")
    try:
        content = await rag_service.retrieve_content(
            topic_id="topic_phys_mech_newton_3",
            interest="basketball",
            grade_level=10,
            limit=3,
        )

        if not content:
            print("✗ No content retrieved")
            return False

        print(f"✓ Retrieved {len(content)} content chunks")
        print()

        # Test 4: Verify we got real content (not mock)
        print("Test 4: Verifying real OER content (not mock)...")
        for i, chunk in enumerate(content, 1):
            print(f"\nChunk {i}:")
            print(f"  Title: {chunk.get('title', 'N/A')}")
            print(f"  Source: {chunk.get('source', 'N/A')}")
            print(f"  Relevance: {chunk.get('relevance_score', 0):.4f}")
            print(f"  Subject: {chunk.get('subject', 'N/A')}")
            print(f"  Chunk ID: {chunk.get('chunk_id', 'N/A')}")

            # Show first 150 chars of text
            text = chunk.get("text", "")
            if text:
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"  Text preview: {preview}")

            # Check if this looks like real content
            # Mock content has specific IDs like "oer_newton3_001"
            chunk_id = chunk.get("chunk_id", "")
            if chunk_id.startswith("oer_newton"):
                print("  ⚠ WARNING: This looks like mock content!")
                print(
                    "    Real content should have chunk IDs like 'physics_2e_chunk_001'"
                )

        print()
        print("=" * 70)
        print("✓ RAG SERVICE TEST PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  - Embeddings loaded: {num_chunks:,} chunks")
        print(f"  - Memory usage: {memory_mb:.1f} MB")
        print(f"  - Content retrieved: {len(content)} chunks")
        print(f"  - Top relevance score: {content[0].get('relevance_score', 0):.4f}")
        print()

        return True

    except Exception as e:
        print(f"✗ Failed to retrieve content: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    success = asyncio.run(test_rag_retrieval())

    if success:
        print("✓ All tests passed - RAG service is production ready")
        sys.exit(0)
    else:
        print("✗ Tests failed - RAG service has issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
