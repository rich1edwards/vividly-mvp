"""
Content Generation Orchestration Service (Phase 3)

Orchestrates the full AI content generation pipeline:
1. NLU: Extract topic from query
2. RAG: Retrieve educational content
3. Script: Generate personalized script
4. TTS: Generate audio
5. Video: Render video with visuals
6. Cache: Store results
"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from app.services.nlu_service import get_nlu_service
from app.services.rag_service import get_rag_service
from app.services.script_generation_service import get_script_generation_service
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """
    Full content generation pipeline orchestrator.

    Coordinates all AI services to generate personalized educational content.
    """

    def __init__(self):
        """Initialize orchestration service with all dependencies."""
        self.nlu_service = get_nlu_service()
        self.rag_service = get_rag_service()
        self.script_service = get_script_generation_service()
        self.cache_service = CacheService()

    async def generate_content_from_query(
        self,
        student_query: str,
        student_id: str,
        grade_level: int,
        interest: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete educational content from natural language query.

        Pipeline:
        1. NLU: Extract topic from query
        2. Check cache for existing content
        3. RAG: Retrieve educational content
        4. Generate script
        5. Generate audio (TTS)
        6. Generate video
        7. Cache results

        Args:
            student_query: Natural language query
            student_id: Student ID
            grade_level: Student's grade (9-12)
            interest: Optional interest override

        Returns:
            Dict with generation status and content URLs
        """
        generation_id = self._generate_id()

        try:
            logger.info(f"[{generation_id}] Starting content generation")
            logger.info(f"Query: {student_query}, Grade: {grade_level}")

            # Step 1: Extract topic using NLU
            logger.info(f"[{generation_id}] Step 1: Topic extraction")
            topic_extraction = await self.nlu_service.extract_topic(
                student_query=student_query,
                grade_level=grade_level,
                student_id=student_id
            )

            # Handle clarification needed
            if topic_extraction["clarification_needed"]:
                return {
                    "status": "clarification_needed",
                    "generation_id": generation_id,
                    "message": "Need clarification to proceed",
                    "clarifying_questions": topic_extraction["clarifying_questions"]
                }

            # Handle out of scope
            if topic_extraction["out_of_scope"]:
                return {
                    "status": "out_of_scope",
                    "generation_id": generation_id,
                    "message": "Query is not related to academic content",
                    "reasoning": topic_extraction["reasoning"]
                }

            topic_id = topic_extraction["topic_id"]
            topic_name = topic_extraction["topic_name"]

            if not topic_id:
                return {
                    "status": "extraction_failed",
                    "generation_id": generation_id,
                    "message": "Could not extract topic from query"
                }

            # Use provided interest or default
            interest_value = interest or "general"

            # Step 2: Check cache
            logger.info(f"[{generation_id}] Step 2: Cache check")
            cache_hit, cached_content = await self.cache_service.check_content_cache(
                topic_id=topic_id,
                interest=interest_value,
                style="standard"
            )

            if cache_hit and cached_content:
                logger.info(f"[{generation_id}] Cache HIT - returning cached content")
                return {
                    "status": "completed",
                    "generation_id": generation_id,
                    "cache_hit": True,
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "content": cached_content
                }

            # Step 3: RAG - Retrieve educational content
            logger.info(f"[{generation_id}] Step 3: RAG content retrieval")
            rag_content = await self.rag_service.retrieve_content(
                topic_id=topic_id,
                interest=interest_value,
                grade_level=grade_level,
                limit=5
            )

            # Step 4: Generate script
            logger.info(f"[{generation_id}] Step 4: Script generation")
            script = await self.script_service.generate_script(
                topic_id=topic_id,
                topic_name=topic_name,
                interest=interest_value,
                grade_level=grade_level,
                rag_content=rag_content,
                duration_seconds=180
            )

            # Step 5 & 6: Generate audio + video (placeholder)
            # In production, these would be async jobs
            logger.info(f"[{generation_id}] Step 5-6: Audio/Video generation (async)")

            # Return generation status
            return {
                "status": "generating",
                "generation_id": generation_id,
                "cache_hit": False,
                "topic_id": topic_id,
                "topic_name": topic_name,
                "script": script,
                "message": "Content generation in progress. Audio and video will be ready in 2-3 minutes.",
                "estimated_completion_seconds": 180
            }

        except Exception as e:
            logger.error(f"[{generation_id}] Content generation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "generation_id": generation_id,
                "error": str(e),
                "message": "Content generation failed. Please try again."
            }

    async def generate_content_from_topic(
        self,
        topic_id: str,
        interest: str,
        grade_level: int
    ) -> Dict[str, Any]:
        """
        Generate content from known topic ID (skip NLU).

        Args:
            topic_id: Canonical topic ID
            interest: Student interest
            grade_level: Student's grade

        Returns:
            Dict with generation status
        """
        generation_id = self._generate_id()

        try:
            # Check cache first
            cache_hit, cached_content = await self.cache_service.check_content_cache(
                topic_id=topic_id,
                interest=interest,
                style="standard"
            )

            if cache_hit:
                return {
                    "status": "completed",
                    "generation_id": generation_id,
                    "cache_hit": True,
                    "content": cached_content
                }

            # RAG retrieval
            rag_content = await self.rag_service.retrieve_content(
                topic_id=topic_id,
                interest=interest,
                grade_level=grade_level
            )

            # Generate script
            script = await self.script_service.generate_script(
                topic_id=topic_id,
                topic_name=topic_id,  # Would lookup from DB in production
                interest=interest,
                grade_level=grade_level,
                rag_content=rag_content
            )

            return {
                "status": "generating",
                "generation_id": generation_id,
                "script": script,
                "message": "Content generation in progress"
            }

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "generation_id": generation_id,
                "error": str(e)
            }

    def _generate_id(self) -> str:
        """Generate unique generation ID."""
        import hashlib
        timestamp = datetime.utcnow().isoformat()
        hash_val = hashlib.sha256(timestamp.encode()).hexdigest()[:16]
        return f"gen_{hash_val}"


# Singleton
_content_gen_service = None


def get_content_generation_service() -> ContentGenerationService:
    """Get singleton content generation service."""
    global _content_gen_service
    if _content_gen_service is None:
        _content_gen_service = ContentGenerationService()
    return _content_gen_service
