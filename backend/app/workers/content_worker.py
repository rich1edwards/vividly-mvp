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
import time
import threading
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.api_core import retry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from http.server import HTTPServer, BaseHTTPRequestHandler

from app.services.content_generation_service import ContentGenerationService
from app.services.content_request_service import ContentRequestService
from app.core.config import settings
from app.workers.metrics import get_metrics

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for health check endpoints.

    Provides:
    - GET /health - Liveness check (is worker running?)
    - GET /health/ready - Readiness check (can worker process messages?)
    """

    # Reference to worker instance (set externally)
    worker_instance = None

    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == "/health":
            # Liveness probe: is the worker process alive?
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "content-worker",
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/health/ready":
            # Readiness probe: can the worker process messages?
            try:
                # Check if worker is initialized and not shutting down
                if (
                    self.worker_instance
                    and not self.worker_instance.shutdown_requested
                    and self.worker_instance.subscriber
                ):
                    # Try to verify database connectivity
                    db = self.worker_instance.SessionLocal()
                    try:
                        db.execute("SELECT 1")
                        db.close()

                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        response = {
                            "status": "ready",
                            "service": "content-worker",
                            "database": "connected",
                            "pubsub": "initialized",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        self.wfile.write(json.dumps(response).encode())
                    except Exception as e:
                        # Database connection failed
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        response = {
                            "status": "not_ready",
                            "service": "content-worker",
                            "database": "disconnected",
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        self.wfile.write(json.dumps(response).encode())
                        db.close()
                else:
                    # Worker not initialized or shutting down
                    self.send_response(503)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    response = {
                        "status": "not_ready",
                        "service": "content-worker",
                        "reason": "worker_not_initialized_or_shutting_down",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                logger.error(f"Readiness check failed: {e}")
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "status": "error",
                    "service": "content-worker",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode())
        else:
            # Unknown path
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP logging (use our logger instead)."""
        pass


class ContentWorker:
    """Worker that processes content generation requests from Pub/Sub."""

    def __init__(self):
        """Initialize worker with database, services, and Pub/Sub subscriber."""
        # Validate required environment variables FIRST (fail-fast)
        self._validate_environment_variables()

        # Services
        self.content_service = ContentGenerationService()
        self.request_service = ContentRequestService()

        # Database connection with connection pooling
        # Pool configuration prevents connection exhaustion under concurrent load
        engine = create_engine(
            settings.DATABASE_URL,
            # Connection pool settings
            pool_size=5,  # Maintain 5 persistent connections
            max_overflow=10,  # Allow up to 10 additional connections under load
            pool_timeout=30,  # Wait up to 30 seconds for connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
            pool_pre_ping=True,  # Verify connection health before using
            # Additional settings for production reliability
            echo=False,  # Disable SQL echo (use logging instead)
            pool_use_lifo=True,  # LIFO ordering reduces connection count
        )
        self.SessionLocal = sessionmaker(bind=engine)

        logger.info(
            f"Database connection pool initialized: "
            f"pool_size=5, max_overflow=10, total_capacity=15"
        )

        # Pub/Sub configuration
        self.project_id = os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
        self.environment = os.getenv("ENVIRONMENT", "dev")

        # Use explicit subscription name if provided, otherwise construct from environment
        self.subscription_name = os.getenv(
            "PUBSUB_SUBSCRIPTION", f"content-worker-sub-{self.environment}"
        )
        self.subscription_path = (
            f"projects/{self.project_id}/subscriptions/{self.subscription_name}"
        )

        # Topic configuration (for publishing responses if needed)
        self.topic_name = os.getenv("PUBSUB_TOPIC", "content-generation-requests")

        # Initialize Pub/Sub subscriber
        self.subscriber = pubsub_v1.SubscriberClient()

        # Graceful shutdown flag
        self.shutdown_requested = False

        # Health check HTTP server
        self.health_check_port = int(os.getenv("HEALTH_CHECK_PORT", "8080"))
        self.health_server = None
        self.health_thread = None

        # Set worker instance reference for health check handler
        HealthCheckHandler.worker_instance = self

        # Initialize metrics
        self.metrics = get_metrics(self.project_id, self.environment)

        logger.info(
            f"Worker initialized: "
            f"subscription={self.subscription_path}, "
            f"topic={self.topic_name}, "
            f"health_port={self.health_check_port}"
        )

    def _validate_environment_variables(self):
        """
        Validate all required environment variables are present.

        Fails fast on missing/invalid configuration to prevent runtime errors.

        Raises:
            EnvironmentError: If any required variables are missing or invalid
        """
        required_vars = {
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT"),
            "GCS_BUCKET_GENERATED": os.getenv("GCS_GENERATED_CONTENT_BUCKET"),
            "GCS_BUCKET_OER": os.getenv("GCS_OER_CONTENT_BUCKET"),
            "GCS_BUCKET_TEMP": os.getenv("GCS_TEMP_FILES_BUCKET"),
        }

        # Check for missing variables
        missing_vars = [k for k, v in required_vars.items() if not v]
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Worker cannot start without proper configuration."
            )
            logger.error(error_msg)
            raise EnvironmentError(error_msg)

        # Validate DATABASE_URL format
        database_url = required_vars["DATABASE_URL"]
        if not database_url.startswith(("postgresql://", "sqlite://")):
            error_msg = f"Invalid DATABASE_URL format: {database_url[:20]}... (must start with postgresql:// or sqlite://)"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)

        # Validate ENVIRONMENT value
        environment = required_vars["ENVIRONMENT"]
        if environment not in ["dev", "staging", "prod"]:
            error_msg = f"Invalid ENVIRONMENT value: {environment} (must be dev, staging, or prod)"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)

        logger.info(
            f"Environment variables validated: "
            f"project={required_vars['GCP_PROJECT_ID']}, "
            f"env={required_vars['ENVIRONMENT']}"
        )

    async def process_message(
        self, message: pubsub_v1.types.PubsubMessage, db: Session
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
                "environment": "dev",
                "requested_modalities": ["video"],  # Phase 1A: Dual Modality
                "preferred_modality": "video"       # Phase 1A: Dual Modality
            }
        """
        request_id = None
        correlation_id = None
        start_time = time.time()  # Track processing duration

        try:
            # Parse message data
            message_data = json.loads(message.data.decode("utf-8"))
            request_id = message_data.get("request_id")
            correlation_id = message_data.get("correlation_id", "unknown")

            # POISON PILL DETECTION: Check delivery attempts
            # If a message has been delivered multiple times, it's likely a poisoned message
            # The DLQ configuration (max_delivery_attempts=5) will automatically move it to DLQ
            # But we log this explicitly for monitoring and alerting
            delivery_attempt = getattr(message, "delivery_attempt", None)
            if delivery_attempt and delivery_attempt > 3:
                logger.warning(
                    f"Message on delivery attempt {delivery_attempt}: "
                    f"request_id={request_id}, correlation_id={correlation_id}. "
                    f"If failures continue, DLQ will capture at attempt 5."
                )

            logger.info(
                f"Processing message: request_id={request_id}, "
                f"correlation_id={correlation_id}, "
                f"delivery_attempt={delivery_attempt or 1}"
            )

            # Validate required fields
            required_fields = [
                "request_id",
                "student_id",
                "student_query",
                "grade_level",
            ]
            missing_fields = [f for f in required_fields if not message_data.get(f)]
            if missing_fields:
                logger.error(
                    f"Missing required fields: {missing_fields}, "
                    f"request_id={request_id}, "
                    f"delivery_attempt={delivery_attempt or 1}. "
                    f"Message will be rejected to trigger DLQ routing."
                )
                # Don't retry messages with missing fields - send to DLQ
                return False

            # CRITICAL FIX: Validate UUID format before database operations
            # This prevents infinite retry loops from invalid request IDs
            try:
                uuid.UUID(str(request_id))
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(
                    f"Invalid request_id format: '{request_id}' is not a valid UUID "
                    f"(type: {type(request_id).__name__}). "
                    f"Message will be rejected to prevent retry loop. "
                    f"Error: {e}"
                )
                # DON'T RETRY - invalid UUID will always fail
                # Return False to trigger DLQ routing
                return False

            # IDEMPOTENCY CHECK: Check if request is already completed or failed
            # This prevents duplicate processing if Pub/Sub delivers message twice
            existing_request = self.request_service.get_request_by_id(
                db=db, request_id=request_id
            )
            if existing_request:
                if existing_request.status == "completed":
                    logger.info(
                        f"Request already completed (idempotency check): "
                        f"request_id={request_id}, skipping duplicate processing"
                    )
                    # Return True to acknowledge - don't reprocess completed requests
                    return True
                elif existing_request.status == "failed":
                    logger.info(
                        f"Request already failed (idempotency check): "
                        f"request_id={request_id}, skipping duplicate processing"
                    )
                    # Return True to acknowledge - don't retry failed requests via duplicate message
                    # (They will retry via Pub/Sub retry policy if needed)
                    return True
                # If status is pending/validating/generating, continue processing
                logger.info(
                    f"Request exists with status '{existing_request.status}', continuing processing"
                )
            else:
                logger.warning(
                    f"Request not found in database: request_id={request_id}, "
                    f"this may indicate API didn't create request before publishing to Pub/Sub"
                )

            # Update status: validating
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                status="validating",
                progress_percentage=5,
                current_stage="Validating request parameters",
            )

            # Extract request parameters
            student_id = message_data["student_id"]
            student_query = message_data["student_query"]
            grade_level = message_data["grade_level"]
            interest = message_data.get("interest")

            # Phase 1A: Dual Modality Support
            requested_modalities = message_data.get("requested_modalities", ["video"])
            preferred_modality = message_data.get("preferred_modality", "video")

            # Update status: generating
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                status="generating",
                progress_percentage=10,
                current_stage="Starting content generation pipeline",
            )

            # Generate content through the AI pipeline
            # This calls: NLU → RAG → Script Generation → TTS → Video Assembly
            # Phase 1A: Conditionally skip video if requested_modalities doesn't include it
            result = await self.content_service.generate_content_from_query(
                student_query=student_query,
                student_id=student_id,
                grade_level=grade_level,
                interest=interest,
                # Phase 1A: Dual Modality Support
                requested_modalities=requested_modalities,
            )

            # Update progress during generation
            self.request_service.update_status(
                db=db,
                request_id=request_id,
                status="generating",
                progress_percentage=90,
                current_stage="Finalizing video and uploading to storage",
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
                    thumbnail_url=thumbnail_url,
                )

                # Mark as completed
                self.request_service.update_status(
                    db=db,
                    request_id=request_id,
                    status="completed",
                    progress_percentage=100,
                    current_stage="Complete",
                )

                logger.info(
                    f"Request completed successfully: request_id={request_id}, "
                    f"video_url={video_url}"
                )

                # Record success metrics
                duration = time.time() - start_time
                self.metrics.record_message_processed(
                    success=True,
                    duration_seconds=duration,
                    retry_count=0,
                    request_id=request_id,
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
                    thumbnail_url=thumbnail_url,
                )

                self.request_service.update_status(
                    db=db,
                    request_id=request_id,
                    status="completed",
                    progress_percentage=100,
                    current_stage="Complete (cache hit)",
                )

                logger.info(f"Request completed from cache: request_id={request_id}")

                # Record cache hit metrics (treated as success, but faster)
                duration = time.time() - start_time
                self.metrics.record_message_processed(
                    success=True,
                    duration_seconds=duration,
                    retry_count=0,
                    request_id=request_id,
                )

                return True

            elif result.get("status") == "clarification_needed":
                # Valid response requiring user interaction
                # This is NOT an error - it's a workflow state where system needs user input
                clarifying_questions = result.get("clarifying_questions", [])
                reasoning = result.get("reasoning", "")

                logger.info(
                    f"Request requires clarification: request_id={request_id}, "
                    f"questions={len(clarifying_questions)}"
                )

                # Store clarification in database
                self.request_service.set_clarification_needed(
                    db=db,
                    request_id=request_id,
                    clarifying_questions=clarifying_questions,
                    reasoning=reasoning,
                )

                # Record as success (message processed correctly, just needs user input)
                duration = time.time() - start_time
                self.metrics.record_message_processed(
                    success=True,  # Not a failure - valid workflow state
                    duration_seconds=duration,
                    retry_count=0,
                    request_id=request_id,
                )

                return True  # Acknowledge message

            else:
                # Unexpected status
                error_msg = f"Unexpected generation status: {result.get('status')}"
                logger.error(f"Request {request_id}: {error_msg}")

                self.request_service.set_error(
                    db=db,
                    request_id=request_id,
                    error_message=error_msg,
                    error_stage="content_generation",
                    error_details={"result": result},
                )

                # Record failure metrics
                duration = time.time() - start_time
                self.metrics.record_message_processed(
                    success=False,
                    duration_seconds=duration,
                    retry_count=0,
                    request_id=request_id,
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
                    error_stage="message_parsing",
                )
            return False

        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}", exc_info=True)

            # Update request with error details
            if request_id:
                self.request_service.set_error(
                    db=db,
                    request_id=request_id,
                    error_message=str(e),
                    error_stage="content_generation",
                    error_details={
                        "exception_type": type(e).__name__,
                        "correlation_id": correlation_id,
                    },
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
        request_id = None

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
                # Extract request_id for retry tracking
                try:
                    message_data = json.loads(message.data.decode("utf-8"))
                    request_id = message_data.get("request_id")
                except Exception:
                    pass

                # Increment retry count in database before nack
                if request_id:
                    self.request_service.increment_retry_count(
                        db=db, request_id=request_id
                    )

                # Nack message (will be retried per retry policy)
                message.nack()
                logger.warning(
                    f"Message nacked for retry: message_id={message.message_id}, "
                    f"request_id={request_id}"
                )

        except Exception as e:
            logger.error(f"Callback failed: {e}", exc_info=True)

            # Extract request_id for retry tracking
            try:
                message_data = json.loads(message.data.decode("utf-8"))
                request_id = message_data.get("request_id")
                if request_id and db:
                    self.request_service.increment_retry_count(
                        db=db, request_id=request_id
                    )
            except Exception:
                pass

            # Nack on any error to trigger retry
            message.nack()

        finally:
            if db:
                db.close()

    def start_health_check_server(self):
        """Start HTTP health check server in background thread."""
        try:
            self.health_server = HTTPServer(
                ("0.0.0.0", self.health_check_port), HealthCheckHandler
            )
            self.health_thread = threading.Thread(
                target=self.health_server.serve_forever,
                daemon=True,
                name="health-check-server",
            )
            self.health_thread.start()
            logger.info(f"Health check server started on port {self.health_check_port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            # Don't fail worker startup if health check fails
            # Worker can still process messages

    def stop_health_check_server(self):
        """Stop HTTP health check server."""
        if self.health_server:
            logger.info("Stopping health check server...")
            self.health_server.shutdown()
            if self.health_thread:
                self.health_thread.join(timeout=5)
            logger.info("Health check server stopped")

    def run(self):
        """
        Run the worker to process available Pub/Sub messages (Cloud Run Job mode).

        This is designed for Cloud Run Jobs: pulls messages in batches, processes them,
        and exits when queue is empty or max runtime is reached.

        For long-running service mode, see run_service() method instead.
        """
        logger.info(
            f"Starting worker (Cloud Run Job mode): subscription={self.subscription_path}"
        )

        # Start health check server in background
        self.start_health_check_server()

        # Job execution parameters
        max_runtime_seconds = int(
            os.getenv("WORKER_MAX_RUNTIME", "300")
        )  # 5 minutes default
        pull_timeout_seconds = 30  # Timeout for each pull request
        max_messages_per_pull = 10  # Process up to 10 messages per batch
        empty_queue_timeout = 60  # Exit if queue empty for 60 seconds

        start_time = time.time()
        total_messages_processed = 0
        total_messages_failed = 0
        last_message_time = start_time

        logger.info(
            f"Worker configuration: max_runtime={max_runtime_seconds}s, "
            f"pull_timeout={pull_timeout_seconds}s, "
            f"batch_size={max_messages_per_pull}, "
            f"empty_queue_timeout={empty_queue_timeout}s"
        )

        try:
            # Process messages until timeout or queue empty
            while True:
                # Check if we've exceeded max runtime
                elapsed = time.time() - start_time
                if elapsed >= max_runtime_seconds:
                    logger.info(
                        f"Max runtime reached ({elapsed:.1f}s >= {max_runtime_seconds}s), "
                        f"exiting gracefully"
                    )
                    break

                # Check if queue has been empty too long
                time_since_last_message = time.time() - last_message_time
                if time_since_last_message >= empty_queue_timeout:
                    logger.info(
                        f"No messages for {time_since_last_message:.1f}s "
                        f"(>= {empty_queue_timeout}s), queue appears empty, exiting"
                    )
                    break

                # Pull batch of messages
                logger.info(f"Pulling up to {max_messages_per_pull} messages...")
                try:
                    pull_response = self.subscriber.pull(
                        request={
                            "subscription": self.subscription_path,
                            "max_messages": max_messages_per_pull,
                        },
                        timeout=pull_timeout_seconds,
                    )
                except Exception as e:
                    logger.warning(f"Pull request failed: {e}, retrying...")
                    time.sleep(5)  # Brief pause before retry
                    continue

                # Check if any messages were received
                received_messages = pull_response.received_messages
                if not received_messages:
                    logger.info("No messages available in current pull")
                    # Don't exit immediately - wait for empty_queue_timeout
                    time.sleep(10)  # Brief pause before next pull
                    continue

                logger.info(
                    f"Received {len(received_messages)} messages, processing..."
                )
                last_message_time = time.time()  # Reset empty queue timer

                # Process each message
                for received_message in received_messages:
                    try:
                        db = self.SessionLocal()
                        try:
                            # Process message (same logic as streaming callback)
                            success = asyncio.run(
                                self.process_message(received_message.message, db)
                            )

                            if success:
                                # Acknowledge message (removes from queue)
                                self.subscriber.acknowledge(
                                    request={
                                        "subscription": self.subscription_path,
                                        "ack_ids": [received_message.ack_id],
                                    }
                                )
                                total_messages_processed += 1
                                logger.info(
                                    f"Message processed successfully "
                                    f"(total: {total_messages_processed})"
                                )
                            else:
                                # Nack message for retry (or DLQ if max retries exceeded)
                                self.subscriber.modify_ack_deadline(
                                    request={
                                        "subscription": self.subscription_path,
                                        "ack_ids": [received_message.ack_id],
                                        "ack_deadline_seconds": 0,  # Immediate nack
                                    }
                                )
                                total_messages_failed += 1
                                logger.warning(
                                    f"Message processing failed "
                                    f"(total failed: {total_messages_failed})"
                                )
                        finally:
                            db.close()

                    except Exception as e:
                        logger.error(
                            f"Error processing message {received_message.ack_id}: {e}",
                            exc_info=True,
                        )
                        # Nack on error to trigger retry
                        try:
                            self.subscriber.modify_ack_deadline(
                                request={
                                    "subscription": self.subscription_path,
                                    "ack_ids": [received_message.ack_id],
                                    "ack_deadline_seconds": 0,
                                }
                            )
                            total_messages_failed += 1
                        except Exception as nack_error:
                            logger.error(f"Failed to nack message: {nack_error}")

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            raise
        finally:
            # Log final statistics
            total_time = time.time() - start_time
            logger.info(
                f"Worker completed: "
                f"runtime={total_time:.1f}s, "
                f"processed={total_messages_processed}, "
                f"failed={total_messages_failed}, "
                f"success_rate={100 * total_messages_processed / max(1, total_messages_processed + total_messages_failed):.1f}%"
            )
            self.stop_health_check_server()

    def shutdown(self, signum=None, frame=None):
        """
        Graceful shutdown handler.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Shutdown signal received: {signum}")
        self.shutdown_requested = True
        self.stop_health_check_server()


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
