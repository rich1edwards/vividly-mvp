"""
RAG Service for Educational Content Retrieval (Phase 3 Sprint 2, Updated Phase 4.3)

Retrieval-Augmented Generation service that:
1. Searches OER content using vector embeddings
2. Retrieves relevant educational materials via Vertex AI Matching Engine
3. Provides context for script generation
"""
import os
import logging
from typing import List, Dict, Optional, Any

from app.services.embeddings_service import get_embeddings_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Retrieval-Augmented Generation service for educational content.

    Uses vector search over OER (Open Educational Resources) to find
    relevant content for personalized script generation.
    """

    def __init__(self, project_id: str = None):
        """
        Initialize RAG service.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.embeddings_service = get_embeddings_service()

        # Try to initialize Vertex AI Vector Search (will fail gracefully in test)
        self.matching_engine_available = False
        self.index_endpoint = None

        try:
            from google.cloud import aiplatform

            aiplatform.init(project=self.project_id, location="us-central1")

            # Get index endpoint from environment
            index_endpoint_id = os.getenv("VERTEX_MATCHING_ENGINE_ENDPOINT")

            if index_endpoint_id:
                self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                    index_endpoint_id
                )
                self.matching_engine_available = True
                logger.info("Vertex AI Matching Engine initialized")
            else:
                logger.warning("VERTEX_MATCHING_ENGINE_ENDPOINT not configured")

            self.vertex_available = True
        except Exception as e:
            logger.warning(f"Vertex AI not available: {e}. Running in mock mode.")
            self.vertex_available = False

    async def retrieve_content(
        self, topic_id: str, interest: str, grade_level: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant OER content for topic and interest.

        Args:
            topic_id: Canonical topic ID
            interest: Student interest for personalization
            grade_level: Student's grade level
            limit: Max number of content pieces to retrieve

        Returns:
            List of content dicts with:
                - content_id: str
                - title: str
                - text: str (excerpt)
                - source: str (OER source)
                - relevance_score: float

        Example:
            >>> content = await rag.retrieve_content(
            ...     "topic_phys_mech_newton_3",
            ...     "basketball",
            ...     10,
            ...     limit=5
            ... )
        """
        # Use Matching Engine if available, otherwise mock
        if self.matching_engine_available and self.index_endpoint:
            return await self._retrieve_with_matching_engine(
                topic_id, interest, grade_level, limit
            )
        else:
            return self._mock_retrieve_content(topic_id, interest, grade_level, limit)

    async def _retrieve_with_matching_engine(
        self, topic_id: str, interest: str, grade_level: int, limit: int
    ) -> List[Dict]:
        """
        Retrieve content using Vertex AI Matching Engine.

        Process:
        1. Build search query from topic_id + interest
        2. Generate query embedding
        3. Search vector index
        4. Filter and rank results
        5. Return top matches
        """
        try:
            # Build search query
            query_text = f"{topic_id} {interest}"

            # Generate query embedding
            query_embedding = await self.embeddings_service.generate_query_embedding(
                query_text
            )

            # Search vector index
            # Note: Requires deployed index endpoint
            matches = self.index_endpoint.find_neighbors(
                deployed_index_id=os.getenv("VERTEX_DEPLOYED_INDEX_ID"),
                queries=[query_embedding],
                num_neighbors=limit * 2,  # Get extra for filtering
            )

            # Process results
            content_results = []

            for match in matches[0]:  # First query results
                chunk_id = match.id
                distance = match.distance

                # Fetch chunk metadata from database
                # In production, would query PostgreSQL here
                # For now, create mock result
                relevance_score = 1.0 - distance  # Convert distance to similarity

                content_results.append(
                    {
                        "content_id": chunk_id,
                        "title": f"Content for {topic_id}",
                        "text": "Educational content retrieved from vector database...",
                        "source": "OpenStax",
                        "relevance_score": relevance_score,
                    }
                )

            # Sort by relevance
            content_results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return content_results[:limit]

        except Exception as e:
            logger.error(f"Matching Engine retrieval failed: {e}", exc_info=True)
            # Fallback to mock
            return self._mock_retrieve_content(topic_id, interest, grade_level, limit)

    def _mock_retrieve_content(
        self, topic_id: str, interest: str, grade_level: int, limit: int
    ) -> List[Dict]:
        """
        Mock content retrieval for testing.

        Returns sample OER content relevant to topic.
        """
        # Sample OER content based on topic
        mock_content_db = {
            "topic_phys_mech_newton_3": [
                {
                    "content_id": "oer_newton3_001",
                    "title": "Newton's Third Law: Action and Reaction",
                    "text": "For every action, there is an equal and opposite reaction. This fundamental law explains how forces work in pairs. When you push against a wall, the wall pushes back with equal force.",
                    "source": "OpenStax Physics",
                    "relevance_score": 0.95,
                    "grade_level": [9, 10, 11, 12],
                    "keywords": ["action", "reaction", "force pairs", "Newton"],
                },
                {
                    "content_id": "oer_newton3_002",
                    "title": "Real-World Examples of Newton's Third Law",
                    "text": "Newton's Third Law appears everywhere in daily life. When you jump, you push down on the ground, and the ground pushes you up. When swimming, you push water backwards, and water pushes you forward.",
                    "source": "Khan Academy",
                    "relevance_score": 0.88,
                    "grade_level": [9, 10, 11, 12],
                    "keywords": ["examples", "applications", "sports"],
                },
                {
                    "content_id": "oer_newton3_003",
                    "title": "Force Pairs in Sports",
                    "text": "In basketball, when a player jumps to shoot, they push down on the court. The court pushes back with equal force, propelling the player upward. The harder the push, the higher the jump.",
                    "source": "Sports Physics",
                    "relevance_score": 0.92,
                    "grade_level": [10, 11, 12],
                    "keywords": ["basketball", "sports", "jumping", "force"],
                },
            ],
            "topic_phys_mech_newton_2": [
                {
                    "content_id": "oer_newton2_001",
                    "title": "Newton's Second Law: F = ma",
                    "text": "Newton's Second Law states that force equals mass times acceleration (F = ma). This means the acceleration of an object depends on both the net force acting on it and its mass.",
                    "source": "OpenStax Physics",
                    "relevance_score": 0.95,
                    "grade_level": [9, 10, 11, 12],
                    "keywords": ["F=ma", "force", "mass", "acceleration"],
                }
            ],
        }

        # Get content for topic
        content_list = mock_content_db.get(topic_id, [])

        # Filter by interest if basketball-related
        if interest == "basketball":
            # Boost relevance for basketball-related content
            for content in content_list:
                if "basketball" in content.get("keywords", []):
                    content["relevance_score"] = min(
                        1.0, content["relevance_score"] + 0.1
                    )

        # Sort by relevance and limit
        content_list = sorted(
            content_list, key=lambda x: x["relevance_score"], reverse=True
        )[:limit]

        return content_list

    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate text embeddings using Vertex AI.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector)
        """
        if not self.vertex_available:
            # Return mock embedding
            import hashlib

            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Generate deterministic pseudo-random embedding
            return [(hash_val >> i) % 100 / 100.0 for i in range(768)]

        # TODO: Use Vertex AI Text Embedding API
        # For now, return mock
        return [(0.1 * i) % 1.0 for i in range(768)]


# Singleton instance
_rag_service_instance = None


def get_rag_service() -> RAGService:
    """Get singleton RAG service instance."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance
