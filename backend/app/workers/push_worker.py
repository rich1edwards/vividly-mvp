"""
Content Generation Push Worker for Cloud Run Service

Receives Pub/Sub push messages via HTTP POST for real-time async content generation.
This is the push-based counterpart to content_worker.py (pull-based).

Architecture:
- Cloud Run Service listening on PORT (default 8080)
- Pub/Sub push subscription sends POST requests to /push endpoint
- Processes content generation (NLU → RAG → Script → TTS → Video)
- Updates ContentRequest table with progress and results
- Returns 200 OK to acknowledge, 4xx/5xx to trigger retry

Push Message Format (HTTP POST body):
{
    "message": {
        "data": "<base64-encoded-json>",
        "messageId": "...",
        "publishTime": "..."
    },
    "subscription": "projects/..."
}
"""
import json
import logging
import os
import base64
import asyncio
import time
import uuid
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.services.content_generation_service import ContentGenerationService
from app.services.content_request_service import ContentRequestService
from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationEventType,
)
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vividly Content Worker (Push)", version="1.0.0")

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Service instances
content_service = ContentGenerationService()
request_service = ContentRequestService()
notification_service = NotificationService()


@app.get("/")
async def root():
    """Root endpoint for basic health check"""
    return {"service": "vividly-content-worker-push", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy"}


@app.post("/push")
async def push_handler(request: Request):
    """
    Pub/Sub push endpoint.

    Receives messages from Pub/Sub push subscription and processes them.
    Returns 200 OK to acknowledge successful processing.
    Returns 4xx/5xx to trigger Pub/Sub retry.

    Args:
        request: FastAPI request containing Pub/Sub push message

    Returns:
        200 OK if processing succeeded
        500 Internal Server Error if processing failed (triggers retry)
    """
    try:
        # Parse Pub/Sub push message
        envelope = await request.json()

        if not envelope or "message" not in envelope:
            logger.error("Invalid push message: missing 'message' field")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid push message format"}
            )

        message = envelope["message"]
        message_id = message.get("messageId", "unknown")

        # Decode base64 message data
        if "data" not in message:
            logger.error(f"Message {message_id}: missing 'data' field")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Missing message data"}
            )

        message_data_raw = base64.b64decode(message["data"]).decode("utf-8")
        message_data = json.loads(message_data_raw)

        request_id = message_data.get("request_id")
        correlation_id = message_data.get("correlation_id", "unknown")

        logger.info(
            f"Processing push message: "
            f"message_id={message_id}, "
            f"request_id={request_id}, "
            f"correlation_id={correlation_id}"
        )

        # Process message with database session
        db = SessionLocal()
        try:
            success = await process_message(message_data, db)

            if success:
                logger.info(f"Message {message_id} processed successfully")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"status": "processed", "request_id": request_id}
                )
            else:
                logger.warning(f"Message {message_id} processing failed, will retry")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": "Processing failed", "request_id": request_id}
                )
        finally:
            db.close()

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in push message: {e}")
        # Return 400 - don't retry malformed JSON
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON"}
        )

    except Exception as e:
        logger.error(f"Push handler error: {e}", exc_info=True)
        # Return 500 - trigger retry
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


async def process_message(message_data: Dict[str, Any], db: Session) -> bool:
    """
    Process a single content generation request from Pub/Sub push message.

    This mirrors the logic from content_worker.py but for push-based delivery.

    Args:
        message_data: Decoded Pub/Sub message data
        db: Database session

    Returns:
        True if processing succeeded, False if failed (triggers retry)
    """
    request_id = None
    correlation_id = None
    start_time = time.time()

    try:
        # Parse message data
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
            logger.error(
                f"Missing required fields: {missing_fields}, "
                f"request_id={request_id}. "
                f"Message will be rejected."
            )
            # Don't retry messages with missing fields
            return False

        # CRITICAL: Validate UUID format before database operations
        try:
            uuid.UUID(str(request_id))
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(
                f"Invalid request_id format: '{request_id}' is not a valid UUID. "
                f"Message will be rejected. Error: {e}"
            )
            # DON'T RETRY - invalid UUID will always fail
            return False

        # IDEMPOTENCY CHECK: Check if request is already completed or failed
        existing_request = request_service.get_request_by_id(db=db, request_id=request_id)
        if existing_request:
            if existing_request.status == "completed":
                logger.info(
                    f"Request already completed (idempotency check): "
                    f"request_id={request_id}, skipping duplicate processing"
                )
                return True
            elif existing_request.status == "failed":
                logger.info(
                    f"Request already failed (idempotency check): "
                    f"request_id={request_id}, skipping duplicate processing"
                )
                return True
            logger.info(
                f"Request exists with status '{existing_request.status}', continuing processing"
            )
        else:
            logger.warning(
                f"Request not found in database: request_id={request_id}"
            )

        # Update status: validating
        request_service.update_status(
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

        # Phase 1A: Dual Modality Support
        requested_modalities = message_data.get("requested_modalities", ["video"])
        preferred_modality = message_data.get("preferred_modality", "video")

        logger.info(
            f"Processing content request: "
            f"request_id={request_id}, "
            f"correlation_id={correlation_id}, "
            f"query='{student_query[:50]}...'"
        )

        # Update status: generating_script (using correct database enum value)
        request_service.update_status(
            db=db,
            request_id=request_id,
            status="generating_script",
            progress_percentage=10,
            current_stage="Starting content generation pipeline"
        )

        # Phase 1.4: Publish "generation started" notification
        try:
            await notification_service.publish_notification(
                user_id=str(student_id),
                notification=NotificationPayload(
                    event_type=NotificationEventType.CONTENT_GENERATION_STARTED,
                    content_request_id=str(request_id),
                    title="Video generation started",
                    message=f"We're creating your video about: {student_query[:100]}...",
                    progress_percentage=10,
                    metadata={
                        "query": student_query,
                        "grade_level": grade_level,
                        "interest": interest,
                    }
                )
            )
        except Exception as e:
            logger.warning(f"Failed to publish start notification: {e}")

        # Generate content through the AI pipeline
        # This calls: NLU → RAG → Script Generation → TTS → Video Assembly
        result = await content_service.generate_content_from_query(
            student_query=student_query,
            student_id=student_id,
            grade_level=grade_level,
            interest=interest,
            requested_modalities=requested_modalities,
        )

        # Update progress during generation
        request_service.update_status(
            db=db,
            request_id=request_id,
            status="generating_video",
            progress_percentage=90,
            current_stage="Finalizing video and uploading to storage"
        )

        # Phase 1.4: Publish progress notification
        try:
            await notification_service.publish_notification(
                user_id=str(student_id),
                notification=NotificationPayload(
                    event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
                    content_request_id=str(request_id),
                    title="Video generation in progress",
                    message="Finalizing your video and uploading to storage...",
                    progress_percentage=90,
                    metadata={
                        "stage": "finalizing_video",
                        "query": student_query,
                    }
                )
            )
        except Exception as e:
            logger.warning(f"Failed to publish progress notification: {e}")

        # Handle different result statuses
        if result.get("status") == "completed":
            # Extract URLs from result
            video_url = result.get("video_url")
            script_text = result.get("script_text", "")
            thumbnail_url = result.get("thumbnail_url")

            # Store results
            request_service.set_results(
                db=db,
                request_id=request_id,
                video_url=video_url,
                script_text=script_text,
                thumbnail_url=thumbnail_url
            )

            # Mark as completed
            request_service.update_status(
                db=db,
                request_id=request_id,
                status="completed",
                progress_percentage=100,
                current_stage="Complete"
            )

            # Phase 1.4: Publish "generation completed" notification
            try:
                await notification_service.publish_notification(
                    user_id=str(student_id),
                    notification=NotificationPayload(
                        event_type=NotificationEventType.CONTENT_GENERATION_COMPLETED,
                        content_request_id=str(request_id),
                        title="Video ready!",
                        message=f"Your video about '{student_query[:50]}...' is ready to watch",
                        progress_percentage=100,
                        metadata={
                            "video_url": video_url,
                            "thumbnail_url": thumbnail_url,
                            "query": student_query,
                        }
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to publish completion notification: {e}")

            duration = time.time() - start_time
            logger.info(
                f"Request completed successfully: request_id={request_id}, "
                f"video_url={video_url}, duration={duration:.1f}s"
            )

            return True

        elif result.get("status") == "cached":
            # Cache hit - content already exists
            video_url = result.get("video_url")
            script_text = result.get("script_text", "")
            thumbnail_url = result.get("thumbnail_url")

            request_service.set_results(
                db=db,
                request_id=request_id,
                video_url=video_url,
                script_text=script_text,
                thumbnail_url=thumbnail_url
            )

            request_service.update_status(
                db=db,
                request_id=request_id,
                status="completed",
                progress_percentage=100,
                current_stage="Complete (cache hit)"
            )

            duration = time.time() - start_time
            logger.info(
                f"Request completed from cache: request_id={request_id}, duration={duration:.1f}s"
            )

            return True

        elif result.get("status") == "clarification_needed":
            # Valid response requiring user interaction
            clarifying_questions = result.get("clarifying_questions", [])
            reasoning = result.get("reasoning", "")

            logger.info(
                f"Request requires clarification: request_id={request_id}, "
                f"questions={len(clarifying_questions)}"
            )

            # Store clarification in database using "pending" status with metadata
            # (avoids enum constraint - "clarification_needed" not in database enum)
            import datetime
            request_service.update_status(
                db=db,
                request_id=request_id,
                status="pending",
                progress_percentage=0,
                current_stage="Awaiting user clarification"
            )

            # Store clarification questions in request_metadata
            existing_request = request_service.get_request_by_id(db=db, request_id=request_id)
            if existing_request:
                metadata = existing_request.request_metadata or {}
                metadata["clarification"] = {
                    "questions": clarifying_questions,
                    "reasoning": reasoning,
                    "requested_at": datetime.datetime.utcnow().isoformat()
                }
                # Update metadata directly
                from sqlalchemy import update
                from app.models.request_tracking import ContentRequest
                db.execute(
                    update(ContentRequest)
                    .where(ContentRequest.id == request_id)
                    .values(request_metadata=metadata)
                )
                db.commit()

            duration = time.time() - start_time
            logger.info(
                f"Request marked for clarification: request_id={request_id}, duration={duration:.1f}s"
            )

            return True  # Acknowledge message - not a failure

        else:
            # Unexpected status
            error_msg = f"Unexpected generation status: {result.get('status')}"
            logger.error(f"Request {request_id}: {error_msg}")

            request_service.set_error(
                db=db,
                request_id=request_id,
                error_message=error_msg,
                error_stage="content_generation",
                error_details={"result": result}
            )

            return False

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        # Don't retry malformed JSON
        if request_id:
            request_service.set_error(
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
            request_service.set_error(
                db=db,
                request_id=request_id,
                error_message=str(e),
                error_stage="content_generation",
                error_details={
                    "exception_type": type(e).__name__,
                    "correlation_id": correlation_id
                }
            )

            # Phase 1.4: Publish "generation failed" notification
            try:
                await notification_service.publish_notification(
                    user_id=str(student_id),
                    notification=NotificationPayload(
                        event_type=NotificationEventType.CONTENT_GENERATION_FAILED,
                        content_request_id=str(request_id),
                        title="Video generation failed",
                        message=f"We encountered an error while creating your video. Our team has been notified.",
                        progress_percentage=0,
                        metadata={
                            "error_message": str(e),
                            "error_type": type(e).__name__,
                            "query": student_query if 'student_query' in locals() else "Unknown",
                        }
                    )
                )
            except Exception as notify_error:
                logger.warning(f"Failed to publish failure notification: {notify_error}")

        # Return False to trigger retry (Pub/Sub will retry up to max_delivery_attempts)
        return False


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))

    logger.info(f"Starting push worker service on port {port}")

    uvicorn.run(
        "app.workers.push_worker:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
