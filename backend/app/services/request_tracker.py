"""
Request Tracking Service

Tracks content generation requests end-to-end through the entire pipeline.
Provides correlation IDs, stage tracking, event logging, and metrics.

Usage:
    tracker = RequestTracker(db)

    # Start tracking a new request
    request_id = tracker.create_request(
        student_id=student.id,
        topic="Photosynthesis",
        learning_objective="Understand the process of photosynthesis"
    )

    # Update stage
    tracker.start_stage(request_id, "rag_retrieval")
    # ... do work ...
    tracker.complete_stage(request_id, "rag_retrieval", output_data={...})

    # Log events
    tracker.log_event(request_id, "api_call", "Called Gemini API", severity="info")

    # Mark as complete
    tracker.complete_request(request_id, video_url="https://cdn.../video.mp4")
"""

import uuid
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

logger = logging.getLogger(__name__)


# Pipeline stage definitions
PIPELINE_STAGES = [
    {"name": "validation", "order": 1, "display": "Request Validation"},
    {"name": "rag_retrieval", "order": 2, "display": "OER Content Retrieval"},
    {"name": "script_generation", "order": 3, "display": "AI Script Generation"},
    {"name": "video_generation", "order": 4, "display": "Video Generation"},
    {"name": "video_processing", "order": 5, "display": "Video Processing & Upload"},
    {"name": "notification", "order": 6, "display": "Student Notification"},
]


class RequestTracker:
    """
    Service for tracking content generation requests through the pipeline.
    """

    def __init__(self, db: Session):
        """
        Initialize request tracker.

        Args:
            db: Database session
        """
        self.db = db

    def create_request(
        self,
        student_id: str,
        topic: str,
        learning_objective: Optional[str] = None,
        grade_level: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str]:
        """
        Create a new content request and initialize tracking.

        Args:
            student_id: Student's user ID
            topic: Learning topic
            learning_objective: Specific learning objective
            grade_level: Grade level
            duration_minutes: Desired video duration
            organization_id: Organization ID
            metadata: Additional request metadata

        Returns:
            Tuple of (request_id, correlation_id)
        """
        from ..models.request_tracking import ContentRequest, RequestStage

        # Generate correlation ID
        correlation_id = self._generate_correlation_id()

        # Create request
        request = ContentRequest(
            correlation_id=correlation_id,
            student_id=student_id,
            topic=topic,
            learning_objective=learning_objective,
            grade_level=grade_level,
            duration_minutes=duration_minutes,
            organization_id=organization_id,
            status="pending",
            request_metadata=metadata or {},
        )

        self.db.add(request)
        self.db.flush()  # Get ID without committing

        # Initialize all pipeline stages
        for stage_def in PIPELINE_STAGES:
            stage = RequestStage(
                request_id=request.id,
                stage_name=stage_def["name"],
                stage_order=stage_def["order"],
                status="pending",
            )
            self.db.add(stage)

        self.db.commit()

        # Log creation event
        self.log_event(
            request_id=str(request.id),
            event_type="request_created",
            message=f"Content request created for topic: {topic}",
            severity="info",
            event_data={"student_id": student_id, "topic": topic},
        )

        logger.info(f"Created content request {request.id} with correlation_id {correlation_id}")

        return str(request.id), correlation_id

    def start_request(self, request_id: str) -> None:
        """
        Mark request as started.

        Args:
            request_id: Request ID
        """
        from ..models.request_tracking import ContentRequest

        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.started_at = datetime.utcnow()
        request.status = "validating"  # First stage
        self.db.commit()

        self.log_event(request_id, "request_started", "Request processing started", severity="info")

    def start_stage(
        self,
        request_id: str,
        stage_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark a pipeline stage as started.

        Args:
            request_id: Request ID
            stage_name: Name of stage (e.g., 'rag_retrieval')
            metadata: Stage-specific metadata
        """
        from ..models.request_tracking import RequestStage, ContentRequest

        stage = (
            self.db.query(RequestStage)
            .filter(and_(RequestStage.request_id == request_id, RequestStage.stage_name == stage_name))
            .first()
        )

        if not stage:
            raise ValueError(f"Stage {stage_name} not found for request {request_id}")

        stage.status = "in_progress"
        stage.started_at = datetime.utcnow()
        if metadata:
            stage.stage_metadata = metadata

        # Update request status
        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if request:
            # Map stage name to request status
            status_map = {
                "validation": "validating",
                "rag_retrieval": "retrieving",
                "script_generation": "generating_script",
                "video_generation": "generating_video",
                "video_processing": "processing_video",
                "notification": "notifying",
            }
            request.status = status_map.get(stage_name, request.status)
            request.current_stage = stage_name

        self.db.commit()

        self.log_event(
            request_id,
            "stage_started",
            f"Started stage: {stage_name}",
            stage_name=stage_name,
            severity="info",
        )

    def complete_stage(
        self,
        request_id: str,
        stage_name: str,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark a pipeline stage as completed.

        Args:
            request_id: Request ID
            stage_name: Name of stage
            output_data: Output data from stage
        """
        from ..models.request_tracking import RequestStage

        stage = (
            self.db.query(RequestStage)
            .filter(and_(RequestStage.request_id == request_id, RequestStage.stage_name == stage_name))
            .first()
        )

        if not stage:
            raise ValueError(f"Stage {stage_name} not found for request {request_id}")

        stage.status = "completed"
        stage.completed_at = datetime.utcnow()

        if stage.started_at:
            duration = (stage.completed_at - stage.started_at).total_seconds()
            stage.duration_seconds = duration

        if output_data:
            stage.output_data = output_data

        self.db.commit()

        self.log_event(
            request_id,
            "stage_completed",
            f"Completed stage: {stage_name} in {stage.duration_seconds:.2f}s",
            stage_name=stage_name,
            severity="info",
            event_data={"duration_seconds": stage.duration_seconds},
        )

    def fail_stage(
        self,
        request_id: str,
        stage_name: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        is_retryable: bool = True,
    ) -> None:
        """
        Mark a pipeline stage as failed.

        Args:
            request_id: Request ID
            stage_name: Name of stage
            error_message: Error message
            error_details: Detailed error information
            is_retryable: Whether stage can be retried
        """
        from ..models.request_tracking import RequestStage, ContentRequest

        stage = (
            self.db.query(RequestStage)
            .filter(and_(RequestStage.request_id == request_id, RequestStage.stage_name == stage_name))
            .first()
        )

        if not stage:
            raise ValueError(f"Stage {stage_name} not found for request {request_id}")

        stage.status = "failed"
        stage.error_message = error_message
        stage.error_details = error_details or {}
        stage.completed_at = datetime.utcnow()

        if stage.started_at:
            duration = (stage.completed_at - stage.started_at).total_seconds()
            stage.duration_seconds = duration

        # Update request status to failed
        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if request:
            request.status = "failed"
            request.failed_at = datetime.utcnow()
            request.error_message = error_message
            request.error_stage = stage_name
            request.error_details = error_details or {}

        self.db.commit()

        self.log_event(
            request_id,
            "stage_failed",
            f"Stage {stage_name} failed: {error_message}",
            stage_name=stage_name,
            severity="error",
            event_data={"error_message": error_message, "is_retryable": is_retryable},
        )

        logger.error(f"Stage {stage_name} failed for request {request_id}: {error_message}")

    def retry_stage(self, request_id: str, stage_name: str) -> bool:
        """
        Retry a failed stage.

        Args:
            request_id: Request ID
            stage_name: Name of stage

        Returns:
            True if retry initiated, False if max retries exceeded
        """
        from ..models.request_tracking import RequestStage

        stage = (
            self.db.query(RequestStage)
            .filter(and_(RequestStage.request_id == request_id, RequestStage.stage_name == stage_name))
            .first()
        )

        if not stage:
            raise ValueError(f"Stage {stage_name} not found for request {request_id}")

        if stage.retry_count >= stage.max_retries:
            self.log_event(
                request_id,
                "retry_limit_exceeded",
                f"Max retries ({stage.max_retries}) exceeded for stage {stage_name}",
                stage_name=stage_name,
                severity="error",
            )
            return False

        stage.retry_count += 1
        stage.status = "pending"
        stage.error_message = None
        stage.error_details = None

        self.db.commit()

        self.log_event(
            request_id,
            "stage_retry",
            f"Retrying stage {stage_name} (attempt {stage.retry_count + 1})",
            stage_name=stage_name,
            severity="warning",
        )

        return True

    def complete_request(
        self,
        request_id: str,
        video_url: str,
        script_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> None:
        """
        Mark request as successfully completed.

        Args:
            request_id: Request ID
            video_url: URL of generated video
            script_text: Generated script
            thumbnail_url: Video thumbnail URL
        """
        from ..models.request_tracking import ContentRequest

        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.video_url = video_url
        request.script_text = script_text
        request.thumbnail_url = thumbnail_url

        # Calculate total duration
        if request.started_at:
            duration = (request.completed_at - request.started_at).total_seconds()
            request.total_duration_seconds = int(duration)

        request.progress_percentage = 100

        self.db.commit()

        self.log_event(
            request_id,
            "request_completed",
            f"Request completed successfully in {request.total_duration_seconds}s",
            severity="info",
            event_data={
                "video_url": video_url,
                "duration_seconds": request.total_duration_seconds,
            },
        )

        logger.info(f"Request {request_id} completed successfully")

    def fail_request(
        self,
        request_id: str,
        error_message: str,
        error_stage: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark request as failed.

        Args:
            request_id: Request ID
            error_message: Error message
            error_stage: Stage where error occurred
            error_details: Detailed error information
        """
        from ..models.request_tracking import ContentRequest

        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.status = "failed"
        request.failed_at = datetime.utcnow()
        request.error_message = error_message
        request.error_stage = error_stage
        request.error_details = error_details or {}

        self.db.commit()

        self.log_event(
            request_id,
            "request_failed",
            f"Request failed at {error_stage}: {error_message}",
            severity="critical",
            event_data={"error_stage": error_stage, "error_details": error_details},
        )

        logger.error(f"Request {request_id} failed at {error_stage}: {error_message}")

    def log_event(
        self,
        request_id: str,
        event_type: str,
        message: str,
        stage_name: Optional[str] = None,
        severity: str = "info",
        event_data: Optional[Dict[str, Any]] = None,
        source_service: Optional[str] = None,
    ) -> None:
        """
        Log a request event.

        Args:
            request_id: Request ID
            event_type: Type of event
            message: Event message
            stage_name: Stage name if applicable
            severity: Severity level (info, warning, error, critical)
            event_data: Additional event data
            source_service: Service that generated event
        """
        from ..models.request_tracking import RequestEvent

        event = RequestEvent(
            request_id=request_id,
            event_type=event_type,
            event_message=message,
            stage_name=stage_name,
            severity=severity,
            event_data=event_data or {},
            source_service=source_service,
        )

        self.db.add(event)
        self.db.commit()

    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a request with all stages.

        Args:
            request_id: Request ID

        Returns:
            Request status dictionary or None
        """
        from ..models.request_tracking import ContentRequest, RequestStage

        request = self.db.query(ContentRequest).filter(ContentRequest.id == request_id).first()
        if not request:
            return None

        stages = (
            self.db.query(RequestStage)
            .filter(RequestStage.request_id == request_id)
            .order_by(RequestStage.stage_order)
            .all()
        )

        return {
            "request_id": str(request.id),
            "correlation_id": request.correlation_id,
            "status": request.status,
            "current_stage": request.current_stage,
            "progress_percentage": request.progress_percentage,
            "created_at": request.created_at.isoformat() if request.created_at else None,
            "started_at": request.started_at.isoformat() if request.started_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "total_duration_seconds": request.total_duration_seconds,
            "video_url": request.video_url,
            "error_message": request.error_message,
            "error_stage": request.error_stage,
            "stages": [
                {
                    "name": stage.stage_name,
                    "status": stage.status,
                    "duration_seconds": float(stage.duration_seconds) if stage.duration_seconds else None,
                    "error_message": stage.error_message,
                    "retry_count": stage.retry_count,
                }
                for stage in stages
            ],
        }

    def get_request_events(self, request_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event log for a request.

        Args:
            request_id: Request ID
            limit: Maximum number of events

        Returns:
            List of events
        """
        from ..models.request_tracking import RequestEvent

        events = (
            self.db.query(RequestEvent)
            .filter(RequestEvent.request_id == request_id)
            .order_by(desc(RequestEvent.created_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "event_type": event.event_type,
                "message": event.event_message,
                "stage_name": event.stage_name,
                "severity": event.severity,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "event_data": event.event_data,
            }
            for event in events
        ]

    @contextmanager
    def track_stage(self, request_id: str, stage_name: str):
        """
        Context manager for tracking a stage automatically.

        Usage:
            with tracker.track_stage(request_id, "rag_retrieval"):
                # Do work
                results = perform_rag_retrieval()
        """
        self.start_stage(request_id, stage_name)
        try:
            yield
            self.complete_stage(request_id, stage_name)
        except Exception as e:
            self.fail_stage(request_id, stage_name, str(e), {"exception_type": type(e).__name__})
            raise

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing."""
        # Format: vvd_<timestamp>_<uuid>
        timestamp = int(time.time() * 1000)
        short_uuid = str(uuid.uuid4())[:8]
        return f"vvd_{timestamp}_{short_uuid}"


# Middleware for adding correlation ID to requests
class CorrelationIDMiddleware:
    """
    Middleware to add correlation ID to all HTTP requests.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Check for existing correlation ID in headers
            headers = dict(scope.get("headers", []))
            correlation_id = headers.get(b"x-correlation-id")

            if not correlation_id:
                # Generate new correlation ID
                correlation_id = f"req_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
            else:
                correlation_id = correlation_id.decode("utf-8")

            # Add to scope for downstream use
            scope["correlation_id"] = correlation_id

        await self.app(scope, receive, send)
