"""
Content Generation Worker for Cloud Run Jobs

Processes content generation requests from Pub/Sub messages.
Orchestrates the full AI pipeline and updates request tracking.
"""
import json
import logging
import os
import asyncio
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.content_generation_service import ContentGenerationService
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContentWorker:
    """Worker that processes content generation requests."""

    def __init__(self):
        """Initialize worker with database and services."""
        self.content_service = ContentGenerationService()

        # Database connection for tracking
        engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=engine)

    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single content generation request.

        Args:
            request_data: Request data from Pub/Sub message
                {
                    "request_id": "req_abc123",
                    "student_id": "student_123",
                    "student_query": "Explain Newton's Third Law with basketball",
                    "grade_level": 10,
                    "interest": "basketball",
                    "duration_seconds": 180
                }

        Returns:
            Result dictionary with status and content URLs
        """
        request_id = request_data.get("request_id", "unknown")

        try:
            logger.info(f"Processing request {request_id}")

            # Update status: processing
            await self._update_request_status(request_id, "processing")

            # Extract request parameters
            student_query = request_data.get("student_query")
            student_id = request_data.get("student_id")
            grade_level = request_data.get("grade_level")
            interest = request_data.get("interest")
            duration = request_data.get("duration_seconds", 180)

            # Validate required fields
            if not all([student_query, student_id, grade_level]):
                raise ValueError(
                    "Missing required fields: student_query, student_id, or grade_level"
                )

            # Generate content through the pipeline
            result = await self.content_service.generate_content_from_query(
                student_query=student_query,
                student_id=student_id,
                grade_level=grade_level,
                interest=interest,
            )

            # Handle different result statuses
            if result.get("status") == "clarification_needed":
                await self._update_request_status(
                    request_id,
                    "needs_clarification",
                    metadata={"questions": result.get("clarifying_questions")},
                )
                return result

            if result.get("status") == "out_of_scope":
                await self._update_request_status(
                    request_id, "rejected", metadata={"reason": "out_of_scope"}
                )
                return result

            if result.get("status") == "cache_hit":
                logger.info(f"Request {request_id}: Cache hit")
                await self._update_request_status(
                    request_id,
                    "completed",
                    metadata={"cache_hit": True, "cache_key": result.get("cache_key")},
                )
                return result

            # Success - content generated
            logger.info(f"Request {request_id}: Generation successful")
            await self._update_request_status(
                request_id,
                "completed",
                metadata={
                    "cache_key": result.get("cache_key"),
                    "topic_id": result.get("topic_id"),
                    "generation_time_seconds": result.get("generation_time_seconds"),
                },
            )

            return result

        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}", exc_info=True)

            # Update status: failed
            await self._update_request_status(
                request_id, "failed", metadata={"error": str(e)}
            )

            # Re-raise for Cloud Run retry logic
            raise

    async def _update_request_status(
        self, request_id: str, status: str, metadata: Dict[str, Any] = None
    ):
        """
        Update request status in database.

        Args:
            request_id: Request ID
            status: New status (processing, completed, failed, etc.)
            metadata: Additional metadata to store
        """
        try:
            db = self.SessionLocal()

            # Import here to avoid circular dependency
            from app.models.request_tracking import ContentRequest

            request = (
                db.query(ContentRequest)
                .filter(ContentRequest.request_id == request_id)
                .first()
            )

            if request:
                request.status = status
                request.updated_at = datetime.utcnow()

                if metadata:
                    # Merge with existing metadata
                    current_metadata = request.metadata or {}
                    current_metadata.update(metadata)
                    request.metadata = current_metadata

                if status == "completed":
                    request.completed_at = datetime.utcnow()

                db.commit()
                logger.info(f"Updated request {request_id} status to {status}")
            else:
                logger.warning(f"Request {request_id} not found in database")

        except Exception as e:
            logger.error(f"Failed to update request status: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()


# Cloud Run Job entry point
async def main():
    """Main entry point for Cloud Run Job."""
    logger.info("Content Worker starting...")

    # Get request data from environment variable (set by Cloud Run Jobs)
    request_json = os.getenv("CLOUD_RUN_TASK_REQUEST_DATA", "{}")

    try:
        request_data = json.loads(request_json)
        logger.info(f"Processing request: {request_data.get('request_id', 'unknown')}")

        worker = ContentWorker()
        result = await worker.process_request(request_data)

        logger.info(f"Request completed successfully: {result.get('status')}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request data: {e}")
        raise
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
