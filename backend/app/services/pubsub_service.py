"""
Pub/Sub Service for Async Content Generation

Handles publishing content generation requests to Pub/Sub for async processing.
This decouples the API from long-running video generation tasks.

Architecture:
- API creates ContentRequest → publishes to Pub/Sub → returns immediately
- Worker subscribes to topic → processes request → updates database
- Frontend polls status endpoint for progress updates
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from google.cloud import pubsub_v1
from google.api_core import retry

logger = logging.getLogger(__name__)


class PubSubService:
    """
    Service for publishing content generation requests to Pub/Sub.

    Ensures reliable async processing of long-running content generation tasks.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Pub/Sub service.

        Args:
            project_id: GCP project ID (defaults to env var)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.environment = os.getenv("ENVIRONMENT", "dev")

        # Topic name includes environment for isolation
        self.topic_name = f"content-requests-{self.environment}"
        self.topic_path = f"projects/{self.project_id}/topics/{self.topic_name}"

        # Initialize publisher client
        try:
            self.publisher = pubsub_v1.PublisherClient()
            logger.info(f"Pub/Sub publisher initialized: {self.topic_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub publisher: {e}")
            self.publisher = None

    async def publish_content_request(
        self,
        request_id: str,
        correlation_id: str,
        student_id: str,
        student_query: str,
        grade_level: int,
        interest: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish content generation request to Pub/Sub.

        Args:
            request_id: Unique request ID (UUID from ContentRequest)
            correlation_id: Correlation ID for distributed tracing
            student_id: Student user ID
            student_query: Natural language query
            grade_level: Student's grade level (9-12)
            interest: Optional interest override

        Returns:
            Dict with:
                - success: bool
                - message_id: str (Pub/Sub message ID)
                - topic: str

        Raises:
            Exception: If publishing fails after retries
        """
        if not self.publisher:
            raise Exception("Pub/Sub publisher not initialized")

        # Build message payload
        message_data = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "student_id": student_id,
            "student_query": student_query,
            "grade_level": grade_level,
            "interest": interest,
            "environment": self.environment,
        }

        try:
            # Encode message as JSON bytes
            message_bytes = json.dumps(message_data).encode("utf-8")

            # Publish with retry logic
            future = self.publisher.publish(
                self.topic_path,
                message_bytes,
                # Add message attributes for filtering/routing
                request_id=request_id,
                student_id=student_id,
                environment=self.environment,
            )

            # Wait for publish confirmation
            message_id = future.result(timeout=10.0)

            logger.info(
                f"Published content request to Pub/Sub: "
                f"request_id={request_id}, message_id={message_id}"
            )

            return {
                "success": True,
                "message_id": message_id,
                "topic": self.topic_path,
                "request_id": request_id,
            }

        except Exception as e:
            logger.error(
                f"Failed to publish content request: "
                f"request_id={request_id}, error={e}",
                exc_info=True
            )
            raise Exception(f"Failed to publish to Pub/Sub: {str(e)}")

    def create_topic_if_not_exists(self) -> bool:
        """
        Create Pub/Sub topic if it doesn't exist.

        This is useful for development/testing. In production, topics
        should be created via Terraform.

        Returns:
            True if topic exists or was created
        """
        if not self.publisher:
            return False

        try:
            # Check if topic exists
            try:
                self.publisher.get_topic(request={"topic": self.topic_path})
                logger.info(f"Topic already exists: {self.topic_path}")
                return True
            except Exception:
                # Topic doesn't exist, create it
                pass

            # Create topic
            topic = self.publisher.create_topic(request={"name": self.topic_path})
            logger.info(f"Created Pub/Sub topic: {topic.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """
        Check if Pub/Sub service is healthy.

        Returns:
            Dict with health status
        """
        try:
            if not self.publisher:
                return {
                    "healthy": False,
                    "error": "Publisher not initialized"
                }

            # Try to get topic (this verifies credentials and network)
            self.publisher.get_topic(request={"topic": self.topic_path})

            return {
                "healthy": True,
                "topic": self.topic_path,
                "project_id": self.project_id,
                "environment": self.environment,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "topic": self.topic_path,
            }


# Singleton instance
_pubsub_service_instance: Optional[PubSubService] = None


def get_pubsub_service() -> PubSubService:
    """
    Get singleton Pub/Sub service instance.

    Returns:
        PubSubService instance
    """
    global _pubsub_service_instance
    if _pubsub_service_instance is None:
        _pubsub_service_instance = PubSubService()
    return _pubsub_service_instance
