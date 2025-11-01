#!/usr/bin/env python3
"""
Create Vector Search Index

Creates Vertex AI Vector Search index and uploads embeddings.
"""

import os
import json
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.vertex_ai_client import VertexVectorSearch


def load_all_embeddings(embeddings_dir: Path) -> tuple[list, dict]:
    """
    Load all embeddings from directory.

    Args:
        embeddings_dir: Directory containing embedding files

    Returns:
        Tuple of (all_embeddings, statistics)
    """
    all_embeddings = []
    stats = {"books": 0, "chunks": 0, "subjects": set()}

    # Load all embedding files
    for embeddings_file in embeddings_dir.glob("*-embeddings.json"):
        print(f"Loading: {embeddings_file.name}")

        with open(embeddings_file, "r", encoding="utf-8") as f:
            embeddings = json.load(f)

        all_embeddings.extend(embeddings)
        stats["books"] += 1
        stats["chunks"] += len(embeddings)

        # Collect subjects
        for emb in embeddings:
            stats["subjects"].add(emb["metadata"]["subject"])

    return all_embeddings, stats


def main():
    """Main vector index creation function."""
    # Get configuration from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    gcs_bucket = os.getenv("OER_CONTENT_BUCKET", f"{project_id}-oer-content")

    if not project_id:
        print("✗ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("")
        print("Set it with:")
        print("  export GOOGLE_CLOUD_PROJECT=vividly-dev-rich")
        sys.exit(1)

    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    embeddings_dir = data_dir / "embeddings"

    print("=" * 60)
    print("Vertex AI Vector Search Index Creation")
    print("=" * 60)
    print("")
    print(f"Project: {project_id}")
    print(f"Region: us-central1")
    print(f"GCS Bucket: {gcs_bucket}")
    print("")

    # Check for embeddings
    if not embeddings_dir.exists():
        print("✗ Error: Embeddings directory not found:", embeddings_dir)
        print("Run 04_generate_embeddings.py first")
        sys.exit(1)

    # Load all embeddings
    print("Loading embeddings...")
    all_embeddings, stats = load_all_embeddings(embeddings_dir)

    print(f"✓ Loaded embeddings:")
    print(f"    Books: {stats['books']}")
    print(f"    Total chunks: {stats['chunks']:,}")
    print(f"    Subjects: {', '.join(sorted(stats['subjects']))}")
    print("")

    if not all_embeddings:
        print("✗ Error: No embeddings found")
        sys.exit(1)

    # Verify embedding dimensions
    sample_dim = len(all_embeddings[0]["embedding"])
    print(f"Embedding dimensions: {sample_dim}")
    print("")

    # Initialize vector search client
    vector_search = VertexVectorSearch(
        project_id=project_id,
        location="us-central1",
        index_display_name="vividly-oer-index",
    )

    # Create index
    print("Creating vector search index...")
    print("⚠️  This operation takes 10-20 minutes")
    print("")

    try:
        index = vector_search.create_index(
            embeddings=all_embeddings,
            dimensions=sample_dim,
            distance_measure="DOT_PRODUCT_DISTANCE",  # For cosine similarity
        )

        print(f"✓ Index created: {index.resource_name}")
        print("")

        # Save index info
        index_info = {
            "index_name": index.resource_name,
            "display_name": index.display_name,
            "created_at": datetime.now().isoformat(),
            "dimensions": sample_dim,
            "data_points": len(all_embeddings),
            "books": stats["books"],
            "subjects": list(stats["subjects"]),
        }

        index_info_file = data_dir / "index" / "index_info.json"
        index_info_file.parent.mkdir(parents=True, exist_ok=True)

        with open(index_info_file, "w", encoding="utf-8") as f:
            json.dump(index_info, f, indent=2)

        print(f"✓ Index info saved: {index_info_file}")
        print("")

        # Upload embeddings to index
        print("Uploading embeddings to index...")
        print("⚠️  This operation takes 5-10 minutes")
        print("")

        vector_search.upload_embeddings(
            index=index, embeddings=all_embeddings, gcs_bucket=gcs_bucket
        )

        print("")
        print("=" * 60)
        print("✓ Vector Search Index Creation Complete")
        print("=" * 60)
        print("")
        print("Index details:")
        print(f"  Name: {index.display_name}")
        print(f"  Resource: {index.resource_name}")
        print(f"  Data points: {len(all_embeddings):,}")
        print(f"  Dimensions: {sample_dim}")
        print("")
        print("Next steps:")
        print("  1. Deploy index to endpoint (for queries)")
        print("  2. Test retrieval with sample queries")
        print("  3. Integrate with content generation pipeline")
        print("")

        # Optional: Deploy index to endpoint
        deploy = input("Deploy index to endpoint now? (y/N): ").strip().lower()
        if deploy == "y":
            print("")
            print("Deploying index to endpoint...")
            print("⚠️  This operation takes 20-30 minutes")
            print("")

            endpoint = vector_search.deploy_index(
                index=index,
                endpoint_display_name="vividly-oer-endpoint",
                machine_type="e2-standard-2",
                min_replica_count=1,
                max_replica_count=3,
            )

            # Update index info with endpoint
            index_info["endpoint_name"] = endpoint.resource_name
            index_info["endpoint_display_name"] = endpoint.display_name

            with open(index_info_file, "w", encoding="utf-8") as f:
                json.dump(index_info, f, indent=2)

            print("")
            print("✓ Index deployed successfully")
            print(f"  Endpoint: {endpoint.resource_name}")
            print("")

    except Exception as e:
        print(f"✗ Error creating index: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
