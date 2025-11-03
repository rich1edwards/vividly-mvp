"""
Content Generation Orchestration Service (Phase 3)

Orchestrates the full AI content generation pipeline:
1. NLU: Extract topic from query
2. RAG: Retrieve educational content
3. Script: Generate personalized script
4. TTS: Generate audio
5. Video: Render video with visuals (Phase 1A: conditional based on modality)
6. Cache: Store results
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime

from app.services.nlu_service import get_nlu_service
from app.services.rag_service import get_rag_service
from app.services.script_generation_service import get_script_generation_service
from app.services.cache_service import CacheService
from app.services.tts_service import get_tts_service
from app.services.video_service import get_video_service

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
        self.tts_service = get_tts_service()
        self.video_service = get_video_service()

    async def generate_content_from_query(
        self,
        student_query: str,
        student_id: str,
        grade_level: int,
        interest: Optional[str] = None,
        # Phase 1A: Dual Modality Support
        requested_modalities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete educational content from natural language query.

        Pipeline:
        1. NLU: Extract topic from query
        2. Check cache for existing content
        3. RAG: Retrieve educational content
        4. Generate script
        5. Generate audio (TTS)
        6. Generate video (Phase 1A: conditional based on requested_modalities)
        7. Cache results

        Args:
            student_query: Natural language query
            student_id: Student ID
            grade_level: Student's grade (9-12)
            interest: Optional interest override
            requested_modalities: List of requested output formats (defaults to ["video"])

        Returns:
            Dict with generation status and content URLs
        """
        # Phase 1A: Default to video for backward compatibility
        if requested_modalities is None:
            requested_modalities = ["video"]
        generation_id = self._generate_id()

        try:
            logger.info(f"[{generation_id}] Starting content generation")
            logger.info(f"Query: {student_query}, Grade: {grade_level}")

            # Step 1: Extract topic using NLU
            logger.info(f"[{generation_id}] Step 1: Topic extraction")
            topic_extraction = await self.nlu_service.extract_topic(
                student_query=student_query,
                grade_level=grade_level,
                student_id=student_id,
            )

            # Handle clarification needed
            if topic_extraction["clarification_needed"]:
                return {
                    "status": "clarification_needed",
                    "generation_id": generation_id,
                    "message": "Need clarification to proceed",
                    "clarifying_questions": topic_extraction["clarifying_questions"],
                }

            # Handle out of scope
            if topic_extraction["out_of_scope"]:
                return {
                    "status": "out_of_scope",
                    "generation_id": generation_id,
                    "message": "Query is not related to academic content",
                    "reasoning": topic_extraction["reasoning"],
                }

            topic_id = topic_extraction["topic_id"]
            topic_name = topic_extraction["topic_name"]

            if not topic_id:
                return {
                    "status": "extraction_failed",
                    "generation_id": generation_id,
                    "message": "Could not extract topic from query",
                }

            # Use provided interest or default
            interest_value = interest or "general"

            # Step 2: Check cache
            logger.info(f"[{generation_id}] Step 2: Cache check")
            cache_hit, cached_content = await self.cache_service.check_content_cache(
                topic_id=topic_id, interest=interest_value, style="standard"
            )

            if cache_hit and cached_content:
                logger.info(f"[{generation_id}] Cache HIT - returning cached content")
                return {
                    "status": "completed",
                    "generation_id": generation_id,
                    "cache_hit": True,
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "content": cached_content,
                }

            # Step 3: RAG - Retrieve educational content
            logger.info(f"[{generation_id}] Step 3: RAG content retrieval")
            rag_content = await self.rag_service.retrieve_content(
                topic_id=topic_id,
                interest=interest_value,
                grade_level=grade_level,
                limit=5,
            )

            # Step 4: Generate script
            logger.info(f"[{generation_id}] Step 4: Script generation")
            script = await self.script_service.generate_script(
                topic_id=topic_id,
                topic_name=topic_name,
                interest=interest_value,
                grade_level=grade_level,
                rag_content=rag_content,
                duration_seconds=180,
            )

            # Step 5: Generate audio (TTS)
            logger.info(f"[{generation_id}] Step 5: Audio generation")
            audio = await self.tts_service.generate_audio(
                script=script, voice_type="female_professional", output_format="mp3"
            )

            # Step 6: Generate video (Phase 1A: CONDITIONAL based on requested_modalities)
            # This is where 12x cost savings occurs for text-only requests
            video = None
            if "video" in requested_modalities:
                logger.info(f"[{generation_id}] Step 6: Video generation (requested)")
                video = await self.video_service.generate_video(
                    script=script,
                    audio_url=audio["audio_url"],
                    interest=interest_value,
                    subject=self._infer_subject(topic_id),
                )
            else:
                logger.info(
                    f"[{generation_id}] Step 6: Video generation SKIPPED "
                    f"(not in requested_modalities={requested_modalities}) "
                    f"- COST SAVINGS: $0.183 saved per request"
                )

            # Step 7: Cache the complete content
            logger.info(f"[{generation_id}] Step 7: Caching content")
            content = {"script": script, "audio": audio}
            if video:
                content["video"] = video

            await self.cache_service.cache_content(
                topic_id=topic_id,
                interest=interest_value,
                style="standard",
                content=content,
            )

            # Return complete content
            return {
                "status": "completed",
                "generation_id": generation_id,
                "cache_hit": False,
                "topic_id": topic_id,
                "topic_name": topic_name,
                "content": content,
                "requested_modalities": requested_modalities,  # For tracking
                "message": "Content generation complete!",
            }

        except Exception as e:
            logger.error(
                f"[{generation_id}] Content generation failed: {e}", exc_info=True
            )
            return {
                "status": "failed",
                "generation_id": generation_id,
                "error": str(e),
                "message": "Content generation failed. Please try again.",
            }

    async def generate_content_from_topic(
        self, topic_id: str, interest: str, grade_level: int
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
                topic_id=topic_id, interest=interest, style="standard"
            )

            if cache_hit:
                return {
                    "status": "completed",
                    "generation_id": generation_id,
                    "cache_hit": True,
                    "content": cached_content,
                }

            # RAG retrieval
            rag_content = await self.rag_service.retrieve_content(
                topic_id=topic_id, interest=interest, grade_level=grade_level
            )

            # Generate script
            script = await self.script_service.generate_script(
                topic_id=topic_id,
                topic_name=topic_id,  # Would lookup from DB in production
                interest=interest,
                grade_level=grade_level,
                rag_content=rag_content,
            )

            return {
                "status": "generating",
                "generation_id": generation_id,
                "script": script,
                "message": "Content generation in progress",
            }

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return {"status": "failed", "generation_id": generation_id, "error": str(e)}

    def _generate_id(self) -> str:
        """Generate unique generation ID."""
        import hashlib

        timestamp = datetime.utcnow().isoformat()
        hash_val = hashlib.sha256(timestamp.encode()).hexdigest()[:16]
        return f"gen_{hash_val}"

    def _infer_subject(self, topic_id: str) -> str:
        """Infer subject area from topic ID."""
        topic_id_lower = topic_id.lower()

        if "phys" in topic_id_lower:
            return "physics"
        elif (
            "math" in topic_id_lower
            or "calc" in topic_id_lower
            or "algebra" in topic_id_lower
        ):
            return "math"
        elif "chem" in topic_id_lower:
            return "chemistry"
        elif "bio" in topic_id_lower:
            return "biology"
        elif "hist" in topic_id_lower:
            return "history"
        elif "lit" in topic_id_lower or "eng" in topic_id_lower:
            return "literature"
        else:
            return "default"


# Singleton
_content_gen_service = None


def get_content_generation_service() -> ContentGenerationService:
    """Get singleton content generation service."""
    global _content_gen_service
    if _content_gen_service is None:
        _content_gen_service = ContentGenerationService()
    return _content_gen_service
