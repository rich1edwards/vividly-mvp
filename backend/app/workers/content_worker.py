"""
Content Generation Worker for Cloud Run Jobs

Subscribes to Pub/Sub messages for async content generation.
Orchestrates the full AI pipeline and updates ContentRequest tracking.

Architecture:
- Listens to Pub/Sub subscription: content-worker-sub-{environment}
- Pulls messages in batches
- Processes content generation (NLU → RAG → Script → TTS → Video)
- Updates ContentRequest table with progress and results
- Acknowledges successful messages, nacks failures for retry
"""
import json
import logging
import os
import asyncio
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.api_core import retry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.services.content_generation_service import ContentGenerationService
from app.services.content_request_service import ContentRequestService
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContentWorker:
    """Worker that processes content generation requests from Pub/Sub."""

    def __init__(self):
        """Initialize worker with database, services, and Pub/Sub subscriber."""
        # Services
        self.content_service = ContentGenerationService()
        self.request_service = ContentRequestService()

        # Database connection
        engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=engine)

        # Pub/Sub configuration
        self.project_id = os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.subscription_name = f"content-worker-sub-{self.environment}"
        self.subscription_path = f"projects/{self.project_id}/subscriptions/{self.subscription_name}"

        # Initialize Pub/Sub subscriber
        self.subscriber = pubsub_v1.SubscriberClient()

        # Graceful shutdown flag
        self.shutdown_requested = False

        logger.info(f"Worker initialized: subscription={self.subscription_path}")

    async def process_message(
        self,
        message: pubsub_v1.types.PubsubMessage,
        db: Session
    ) -> bool:
        """
        Process a single Pub/Sub message.

        Args:
            message: Pub/Sub message containing content request
            db: Database session

        Returns:
            True if processing succeeded, False if failed

        Message format:
            {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "correlation_id": "req_abc123def456",
                "student_id": "student_123",
                "student_query": "Explain photosynthesis with basketball",
                "grade_level": 10,
                "interest": "basketball",
                "environment": "dev"
            }
        """
        request_id = None
        correlation_id = None

        try:
            # Parse message data
            message_data = json.loads(message.data.decode("utf-8"))
            request_id = message_data.get("request_id")
            correlation_id = message_data.get("correlation_id", "unknown")

            logger.info(
                f"Processing message: request_id={request_id}, "
                f"correlation_id={correlation_id}"
            )

            # Validate required fields
            required_fields = ["request_id", "student_id", "student_query", "grade_level"]
            missing_fields = [f for f in required_fields if not message_data.get(f)]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                # Don't retry messages with missing fields - send to DLQ
                return False

            # Update status: validating
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                status="validating",
                progress_percentage=5,
                current_stage="Validating request parameters"
            )

            # Extract request parameters
            student_id = message_data["student_id"]
            student_query = message_data["student_query"]
            grade_level = message_data["grade_level"]
            interest = message_data.get("interest")

            # Update status: generating
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                status="generating",
                progress_percentage=10,
                current_stage="Starting content generation pipeline"
            )

            # Generate content through the AI pipeline
            # This calls: NLU → RAG → Script Generation → TTS → Video Assembly
            result = await self.content_service.generate_content_from_query(
                student_query=student_query,
                student_id=student_id,
                grade_level=grade_level,
                interest=interest,
            )

            # Update progress during generation
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                progress_percentage=90,
                current_stage="Finalizing video and uploading to storage"
            )

            # Handle different result statuses
            if result.get("status") == "completed":
                # Extract URLs from result
                video_url = result.get("video_url")
                script_text = result.get("script_text", "")
                thumbnail_url = result.get("thumbnail_url")

                # Store results
                self.request_service.set_results(
                    db=db,
                    request_id=request_id,
                    video_url=video_url,
                    script_text=script_text,
                    thumbnail_url=thumbnail_url
                )

                # Mark as completed
                self.request_service.update_status(
                    db=db,
                    request_id=request_id,
                    status="completed",
                    progress_percentage=100,
                    current_stage="Complete"
                )

                logger.info(
                    f"Request completed successfully: request_id={request_id}, "
                    f"video_url={video_url}"
                )
                return True

            elif result.get("status") == "cached":
                # Cache hit - content already exists
                video_url = result.get("video_url")
                script_text = result.get("script_text", "")
                thumbnail_url = result.get("thumbnail_url")

                self.request_service.set_results(
                    db=db,
                    request_id=request_id,
                    video_url=video_url,
                    script_text=script_text,
                    thumbnail_url=thumbnail_url
                )

                self.request_service.update_status(
                    db=db,
                    request_id=request_id,
                    status="completed",
                    progress_percentage=100,
                    current_stage="Complete (cache hit)"
                )

                logger.info(
                    f"Request completed from cache: request_id={request_id}"
                )
                return True

            else:
                # Unexpected status
                error_msg = f"Unexpected generation status: {result.get('status')}"
                logger.error(f"Request {request_id}: {error_msg}")

                self.request_service.set_error(
                    db=db,
                    request_id=request_id,
                    error_message=error_msg,
                    error_stage="content_generation",
                    error_details={"result": result}
                )
                return False

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            # Don't retry malformed JSON - send to DLQ
            if request_id:
                self.request_service.set_error(
                    db=db,
                    request_id=request_id,
                    error_message=f"Invalid JSON: {str(e)}",
                    error_stage="message_parsing"
                )
            return False

        except Exception as e:
            logger.error(
                f"Request {request_id} failed: {str(e)}",
                exc_info=True
            )

            # Update request with error details
            if request_id:
                self.request_service.set_error(
                    db=db,
                    request_id=request_id,
                    error_message=str(e),
                    error_stage="content_generation",
                    error_details={
                        "exception_type": type(e).__name__,
                        "correlation_id": correlation_id
                    }
                )

            # Return False to trigger retry (Pub/Sub will retry up to max_delivery_attempts)
            return False

    def message_callback(self, message: pubsub_v1.types.PubsubMessage):
        """
        Callback for processing Pub/Sub messages.

        This runs in a thread pool managed by the Pub/Sub client.
        We create a new DB session for each message to ensure thread safety.

        Args:
            message: Pub/Sub message to process
        """
        db = None
        try:
            # Create DB session (thread-safe)
            db = self.SessionLocal()

            # Process message (run async code in sync callback)
            success = asyncio.run(self.process_message(message, db))

            if success:
                # Acknowledge message (removes from queue)
                message.ack()
                logger.info(f"Message acknowledged: {message.message_id}")
            else:
                # Nack message (will be retried per retry policy)
                message.nack()
                logger.warning(f"Message nacked for retry: {message.message_id}")

        except Exception as e:
            logger.error(f"Callback failed: {e}", exc_info=True)
            # Nack on any error to trigger retry
            message.nack()

        finally:
            if db:
                db.close()

    def run(self):
        """
        Run the worker to listen for Pub/Sub messages.

        This is a blocking call that runs until shutdown is requested.
        Uses streaming pull for efficient message processing.
        """
        logger.info(f"Starting worker: subscription={self.subscription_path}")

        # Configure flow control for message processing
        flow_control = pubsub_v1.types.FlowControl(
            max_messages=10,  # Process up to 10 messages concurrently
            max_bytes=10 * 1024 * 1024,  # 10 MB
        )

        # Set up streaming pull
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.message_callback,
            flow_control=flow_control,
        )

        logger.info("Worker is listening for messages...")

        # Keep worker running until shutdown
        try:
            # Block until shutdown or error
            streaming_pull_future.result()
        except TimeoutError:
            logger.info("Streaming pull timed out")
            streaming_pull_future.cancel()
            streaming_pull_future.result()  # Wait for cancellation to complete
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            streaming_pull_future.cancel()
            streaming_pull_future.result()
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            streaming_pull_future.cancel()
            raise
        finally:
            logger.info("Worker shutting down gracefully")

    def shutdown(self, signum=None, frame=None):
        """
        Graceful shutdown handler.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Shutdown signal received: {signum}")
        self.shutdown_requested = True


def main():
    """
    Main entry point for the Content Worker.

    This can be run as:
    1. Cloud Run Job (triggered by Pub/Sub)
    2. Long-running service (for local dev or Cloud Run Service)
    """
    logger.info("Content Worker starting...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'dev')}")
    logger.info(f"Project: {os.getenv('GCP_PROJECT_ID', 'vividly-dev-rich')}")

    # Create worker
    worker = ContentWorker()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, worker.shutdown)
    signal.signal(signal.SIGINT, worker.shutdown)

    try:
        # Run worker (blocking call)
        worker.run()
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
