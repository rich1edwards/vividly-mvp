#!/usr/bin/env python3
"""
Test OER Content Retrieval

Simple MVP retrieval system that:
1. Loads all embeddings from JSON files
2. Generates query embedding using same model
3. Finds top-K similar chunks via cosine similarity
4. Returns relevant content

Architecture: File-based for MVP, can upgrade to Vertex AI Matching Engine later.
"""

import os
import json
import numpy as np
from pathlib import Path
import sys
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.vertex_ai_client import VertexAIEmbeddings


class SimpleVectorRetriever:
    """
    Simple vector retrieval system for MVP.

    Loads embeddings into memory and uses numpy for similarity search.
    Fast enough for 3,783 chunks, can upgrade to Vertex AI later.
    """

    def __init__(self, embeddings_dir: Path):
        """
        Initialize retriever.

        Args:
            embeddings_dir: Directory containing embedding JSON files
        """
        self.embeddings_dir = embeddings_dir
        self.chunks = []
        self.embeddings_matrix = None

    def load_embeddings(self):
        """Load all embeddings from JSON files into memory."""
        print("Loading embeddings from disk...")

        all_chunks = []

        for embeddings_file in self.embeddings_dir.glob("*-embeddings.json"):
            print(f"  Loading: {embeddings_file.name}")

            with open(embeddings_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)

        self.chunks = all_chunks

        # Convert to numpy matrix for fast similarity search
        embeddings_list = [chunk["embedding"] for chunk in self.chunks]
        self.embeddings_matrix = np.array(embeddings_list, dtype=np.float32)

        print(f"\n✓ Loaded {len(self.chunks):,} chunks")
        print(f"  Embedding dimensions: {self.embeddings_matrix.shape[1]}")
        print(f"  Memory usage: {self.embeddings_matrix.nbytes / (1024**2):.1f} MB")
        print("")

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Find top-K most similar chunks to query.

        Args:
            query_embedding: Query embedding vector (768-dim)
            top_k: Number of results to return

        Returns:
            List of top-K chunks with similarity scores
        """
        # Convert query to numpy array
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Normalize vectors (for cosine similarity)
        query_norm = query_vec / np.linalg.norm(query_vec)
        embeddings_norm = self.embeddings_matrix / np.linalg.norm(
            self.embeddings_matrix, axis=1, keepdims=True
        )

        # Compute cosine similarity (dot product of normalized vectors)
        similarities = np.dot(embeddings_norm, query_norm)

        # Get top-K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Build results
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["similarity_score"] = float(similarities[idx])
            results.append(chunk)

        return results


def test_retrieval_system(
    embeddings_dir: Path,
    project_id: str,
    test_queries: List[str]
):
    """
    Test the retrieval system with sample queries.

    Args:
        embeddings_dir: Directory containing embeddings
        project_id: GCP project ID for embedding generation
        test_queries: List of test queries
    """
    print("=" * 60)
    print("OER Content Retrieval Test")
    print("=" * 60)
    print("")

    # Initialize retriever
    retriever = SimpleVectorRetriever(embeddings_dir)
    retriever.load_embeddings()

    # Initialize embeddings client (for query embedding)
    embeddings_client = VertexAIEmbeddings(project_id=project_id)

    # Test each query
    for i, query in enumerate(test_queries, 1):
        print("-" * 60)
        print(f"Query {i}: \"{query}\"")
        print("-" * 60)
        print("")

        # Generate query embedding
        query_chunks = [{"chunk_id": "query", "text": query, "metadata": {}}]
        query_embedded = embeddings_client.generate_embeddings(query_chunks, batch_size=1)

        if not query_embedded:
            print("✗ Error: Failed to generate query embedding")
            continue

        query_embedding = query_embedded[0]["embedding"]

        # Search for similar chunks
        results = retriever.search(query_embedding, top_k=3)

        # Display results
        print(f"Top 3 results:")
        print("")

        for j, result in enumerate(results, 1):
            score = result["similarity_score"]
            text = result["text"]
            metadata = result["metadata"]

            # Truncate text for display
            text_preview = text[:200] + "..." if len(text) > 200 else text

            print(f"{j}. Similarity: {score:.4f}")
            print(f"   Subject: {metadata.get('subject', 'unknown')}")
            print(f"   Source: {metadata.get('source_title', 'unknown')}")
            print(f"   Text: {text_preview}")
            print("")

        print("")


def main():
    """Main test function."""
    # Get project ID from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("✗ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("")
        print("Set it with:")
        print("  export GOOGLE_CLOUD_PROJECT=vividly-dev-rich")
        sys.exit(1)

    script_dir = Path(__file__).parent
    embeddings_dir = script_dir / "data" / "embeddings"

    # Check for embeddings
    if not embeddings_dir.exists():
        print("✗ Error: Embeddings directory not found:", embeddings_dir)
        print("Run 04_generate_embeddings.py first")
        sys.exit(1)

    # Test queries covering different subjects
    test_queries = [
        "What is Newton's third law of motion?",
        "How does photosynthesis work in plants?",
        "What is the quadratic formula?",
    ]

    # Run tests
    test_retrieval_system(embeddings_dir, project_id, test_queries)

    print("=" * 60)
    print("✓ Retrieval Test Complete")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Integrate with content generation pipeline")
    print("  2. Add caching for faster repeated queries")
    print("  3. (Optional) Upgrade to Vertex AI Matching Engine for scale")
    print("")


if __name__ == "__main__":
    main()
