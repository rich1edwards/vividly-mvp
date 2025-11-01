"""
Vertex AI Client Utilities

Wrappers for Vertex AI embedding generation and vector search.
"""

import os
import time
from typing import List, Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Modern import pattern (google-cloud-aiplatform >= 1.60.0)
import vertexai
from google.cloud import aiplatform
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
from vertexai.language_models import TextEmbeddingModel
from tqdm import tqdm


class VertexAIEmbeddings:
    """
    Generate embeddings using Vertex AI text-embedding-gecko@003.

    Features:
    - Batch processing
    - Rate limiting
    - Retry logic
    - Progress tracking
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-embedding-gecko@003",
    ):
        """
        Initialize embeddings client.

        Args:
            project_id: GCP project ID
            location: GCP region
            model_name: Embedding model name
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Initialize Vertex AI (modern pattern requires vertexai.init())
        vertexai.init(project=project_id, location=location)
        aiplatform.init(project=project_id, location=location)

        # Load model
        self.model = TextEmbeddingModel.from_pretrained(model_name)

        # Rate limiting (100 requests per minute)
        self.max_requests_per_minute = 100
        self.request_times = []

    def generate_embeddings(
        self, chunks: List[Dict], batch_size: int = 5
    ) -> List[Dict]:
        """
        Generate embeddings for all chunks.

        Args:
            chunks: List of text chunks
            batch_size: Number of chunks to process at once

        Returns:
            Chunks with embeddings added
        """
        print(f"Generating embeddings for {len(chunks)} chunks...")
        print(f"Model: {self.model_name}")
        print(f"Batch size: {batch_size}")
        print("")

        embedded_chunks = []

        # Process in batches with progress bar
        for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
            batch = chunks[i : i + batch_size]

            # Rate limiting
            self._rate_limit()

            # Generate embeddings for batch
            try:
                batch_embeddings = self._generate_batch(batch)
                embedded_chunks.extend(batch_embeddings)
            except Exception as e:
                print(f"\nError processing batch {i // batch_size}: {e}")
                # Retry with exponential backoff
                time.sleep(2)
                try:
                    batch_embeddings = self._generate_batch(batch)
                    embedded_chunks.extend(batch_embeddings)
                except Exception as retry_error:
                    print(f"Retry failed: {retry_error}")
                    # Add chunks without embeddings (will be filtered later)
                    for chunk in batch:
                        chunk["embedding"] = None
                        chunk["embedding_error"] = str(retry_error)
                        embedded_chunks.append(chunk)

        # Filter out failed embeddings
        successful = [c for c in embedded_chunks if c.get("embedding") is not None]
        failed = len(embedded_chunks) - len(successful)

        print(f"\nEmbedding generation complete:")
        print(f"  ✓ Successful: {len(successful)}")
        if failed > 0:
            print(f"  ✗ Failed: {failed}")

        return successful

    def _generate_batch(self, batch: List[Dict]) -> List[Dict]:
        """Generate embeddings for a single batch."""
        texts = [chunk["text"] for chunk in batch]

        # Call Vertex AI API
        embeddings = self.model.get_embeddings(texts)

        # Add embeddings to chunks
        for chunk, embedding_result in zip(batch, embeddings):
            chunk["embedding"] = embedding_result.values
            chunk["embedding_dim"] = len(embedding_result.values)

        return batch

    def _rate_limit(self):
        """Implement rate limiting to stay under API quota."""
        now = time.time()

        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]

        # If at limit, wait
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                # Clear old times
                self.request_times = []

        # Record this request
        self.request_times.append(time.time())

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for this model."""
        # text-embedding-gecko@003 produces 768-dimensional embeddings
        return 768


class VertexVectorSearch:
    """
    Manage Vertex AI Vector Search indexes.

    Features:
    - Index creation
    - Index deployment
    - Bulk upload
    - Similarity search
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        index_display_name: str = "vividly-oer-index",
    ):
        """
        Initialize vector search client.

        Args:
            project_id: GCP project ID
            location: GCP region
            index_display_name: Display name for index
        """
        self.project_id = project_id
        self.location = location
        self.index_display_name = index_display_name

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

    def create_index(
        self,
        embeddings: List[Dict],
        dimensions: int = 768,
        distance_measure: str = "DOT_PRODUCT_DISTANCE",
    ) -> MatchingEngineIndex:
        """
        Create vector search index.

        Args:
            embeddings: List of chunks with embeddings
            dimensions: Embedding dimensions
            distance_measure: Distance metric (DOT_PRODUCT_DISTANCE for cosine)

        Returns:
            Created index
        """
        print(f"Creating vector search index: {self.index_display_name}")
        print(f"  Dimensions: {dimensions}")
        print(f"  Distance measure: {distance_measure}")
        print(f"  Data points: {len(embeddings)}")
        print("")

        # Create index
        index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
            display_name=self.index_display_name,
            dimensions=dimensions,
            approximate_neighbors_count=10,
            distance_measure_type=distance_measure,
            leaf_node_embedding_count=500,
            leaf_nodes_to_search_percent=7,
            description=f"OpenStax OER content embeddings for Vividly MVP",
        )

        print(f"✓ Index created: {index.resource_name}")
        return index

    def deploy_index(
        self,
        index: MatchingEngineIndex,
        endpoint_display_name: str = "vividly-oer-endpoint",
        machine_type: str = "e2-standard-2",
        min_replica_count: int = 1,
        max_replica_count: int = 3,
    ) -> MatchingEngineIndexEndpoint:
        """
        Deploy index to endpoint.

        Args:
            index: Vector search index
            endpoint_display_name: Endpoint display name
            machine_type: Machine type for deployment
            min_replica_count: Minimum replicas
            max_replica_count: Maximum replicas (for auto-scaling)

        Returns:
            Deployed endpoint
        """
        print(f"Deploying index to endpoint: {endpoint_display_name}")
        print(f"  Machine type: {machine_type}")
        print(f"  Replicas: {min_replica_count}-{max_replica_count}")
        print("")

        # Create endpoint
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=endpoint_display_name,
            description="Vector search endpoint for OER content",
            public_endpoint_enabled=False,  # Private VPC endpoint
        )

        print(f"✓ Endpoint created: {endpoint.resource_name}")

        # Deploy index to endpoint
        print("Deploying index to endpoint (this may take 10-20 minutes)...")
        endpoint.deploy_index(
            index=index,
            deployed_index_id="deployed_oer_index",
            display_name="OER Index Deployment",
            machine_type=machine_type,
            min_replica_count=min_replica_count,
            max_replica_count=max_replica_count,
        )

        print("✓ Index deployed successfully")
        return endpoint

    def upload_embeddings(
        self, index: MatchingEngineIndex, embeddings: List[Dict], gcs_bucket: str
    ):
        """
        Upload embeddings to GCS and update index.

        Args:
            index: Vector search index
            embeddings: List of chunks with embeddings
            gcs_bucket: GCS bucket for staging embeddings
        """
        import json
        from google.cloud import storage

        print(f"Uploading {len(embeddings)} embeddings to index...")

        # Format embeddings for Vertex AI
        formatted_data = []
        for chunk in embeddings:
            formatted_data.append(
                {
                    "id": chunk["chunk_id"],
                    "embedding": chunk["embedding"],
                    "restricts": [],
                    "crowding_tag": chunk["metadata"]["subject"],
                }
            )

        # Upload to GCS
        client = storage.Client(project=self.project_id)
        bucket = client.bucket(gcs_bucket)

        # Create JSONL file
        jsonl_content = "\n".join([json.dumps(item) for item in formatted_data])
        blob_name = f"oer_embeddings/embeddings_{int(time.time())}.jsonl"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(jsonl_content)

        gcs_uri = f"gs://{gcs_bucket}/{blob_name}"
        print(f"✓ Uploaded embeddings to: {gcs_uri}")

        # Update index with new embeddings
        print("Updating index with embeddings...")
        index.update_embeddings(contents_delta_uri=gcs_uri)

        print("✓ Index updated successfully")

    def search(
        self,
        endpoint: MatchingEngineIndexEndpoint,
        query_embedding: List[float],
        num_neighbors: int = 5,
    ) -> List[Dict]:
        """
        Search for similar embeddings.

        Args:
            endpoint: Deployed index endpoint
            query_embedding: Query embedding vector
            num_neighbors: Number of neighbors to return

        Returns:
            List of matching chunks with distances
        """
        response = endpoint.find_neighbors(
            deployed_index_id="deployed_oer_index",
            queries=[query_embedding],
            num_neighbors=num_neighbors,
        )

        results = []
        for match in response[0]:
            results.append({"chunk_id": match.id, "distance": match.distance})

        return results


def main():
    """Test embeddings generation."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python vertex_ai_client.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]

    # Test embeddings
    embeddings_client = VertexAIEmbeddings(project_id)

    sample_chunks = [
        {
            "chunk_id": "test-001",
            "text": "Newton's laws of motion describe the relationship between forces and motion.",
            "metadata": {"subject": "physics"},
        },
        {
            "chunk_id": "test-002",
            "text": "The periodic table organizes chemical elements by atomic number.",
            "metadata": {"subject": "chemistry"},
        },
    ]

    embedded = embeddings_client.generate_embeddings(sample_chunks, batch_size=2)

    for chunk in embedded:
        print(f"Chunk: {chunk['chunk_id']}")
        print(f"  Embedding dimension: {chunk['embedding_dim']}")
        print(f"  Sample values: {chunk['embedding'][:5]}")
        print("")


if __name__ == "__main__":
    main()
