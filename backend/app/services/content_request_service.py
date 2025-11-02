"""
Content Request Service

Manages ContentRequest records for async content generation tracking.
Provides CRUD operations and status queries for the request_tracking system.
"""
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.request_tracking import ContentRequest

logger = logging.getLogger(__name__)


class ContentRequestService:
    """
    Service for managing content generation requests.

    Handles the lifecycle of ContentRequest records:
    - Creating new requests
    - Updating status and progress
    - Querying request status
    - Storing results (URLs)
    """

    @staticmethod
    def create_request(
        db: Session,
        student_id: str,
        topic: str,
        learning_objective: Optional[str],
        grade_level: str,
        duration_minutes: Optional[int] = 3,
        correlation_id: Optional[str] = None,
    ) -> ContentRequest:
        """
        Create a new content generation request.

        Args:
            db: Database session
            student_id: Student user ID
            topic: Topic or query text
            learning_objective: Optional learning objective
            grade_level: Student's grade level
            duration_minutes: Target video duration in minutes
            correlation_id: Optional correlation ID for tracing

        Returns:
            Created ContentRequest record

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = f"req_{uuid.uuid4().hex[:16]}"

            # Create request
            request = ContentRequest(
                correlation_id=correlation_id,
                student_id=student_id,
                topic=topic,
                learning_objective=learning_objective,
                grade_level=grade_level,
                duration_minutes=duration_minutes,
                status="pending",
                progress_percentage=0,
                retry_count=0,
            )

            db.add(request)
            db.commit()
            db.refresh(request)

            logger.info(
                f"Created content request: "
                f"id={request.id}, correlation_id={correlation_id}, "
                f"student_id={student_id}"
            )

            return request

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create content request: {e}", exc_info=True)
            raise

    @staticmethod
    def get_request_by_id(
        db: Session,
        request_id: str
    ) -> Optional[ContentRequest]:
        """
        Get content request by ID.

        Args:
            db: Database session
            request_id: Request ID (UUID)

        Returns:
            ContentRequest or None if not found
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.id == request_id
            ).first()

            return request

        except SQLAlchemyError as e:
            logger.error(f"Failed to get request by ID: {e}")
            return None

    @staticmethod
    def get_request_by_correlation_id(
        db: Session,
        correlation_id: str
    ) -> Optional[ContentRequest]:
        """
        Get content request by correlation ID.

        Args:
            db: Database session
            correlation_id: Correlation ID

        Returns:
            ContentRequest or None if not found
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.correlation_id == correlation_id
            ).first()

            return request

        except SQLAlchemyError as e:
            logger.error(f"Failed to get request by correlation ID: {e}")
            return None

    @staticmethod
    def update_status(
        db: Session,
        request_id: str,
        status: str,
        progress_percentage: Optional[int] = None,
        current_stage: Optional[str] = None,
    ) -> bool:
        """
        Update request status and progress.

        Args:
            db: Database session
            request_id: Request ID (UUID)
            status: New status
            progress_percentage: Progress (0-100)
            current_stage: Current processing stage

        Returns:
            True if updated successfully
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.id == request_id
            ).first()

            if not request:
                logger.warning(f"Request not found: {request_id}")
                return False

            # Update fields
            request.status = status

            if progress_percentage is not None:
                request.progress_percentage = progress_percentage

            if current_stage:
                request.current_stage = current_stage

            # Update timestamps based on status
            if status == "validating" and not request.started_at:
                request.started_at = datetime.utcnow()
            elif status == "completed":
                request.completed_at = datetime.utcnow()
            elif status == "failed":
                request.failed_at = datetime.utcnow()

            db.commit()

            logger.info(
                f"Updated request status: "
                f"id={request_id}, status={status}, progress={progress_percentage}%"
            )

            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to update request status: {e}", exc_info=True)
            return False

    @staticmethod
    def set_error(
        db: Session,
        request_id: str,
        error_message: str,
        error_stage: Optional[str] = None,
        error_details: Optional[Dict] = None,
    ) -> bool:
        """
        Set error information for a request.

        Args:
            db: Database session
            request_id: Request ID (UUID)
            error_message: Error message
            error_stage: Stage where error occurred
            error_details: Additional error details (JSON)

        Returns:
            True if updated successfully
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.id == request_id
            ).first()

            if not request:
                return False

            request.status = "failed"
            request.error_message = error_message
            request.error_stage = error_stage
            request.error_details = error_details
            request.failed_at = datetime.utcnow()

            db.commit()

            logger.error(
                f"Request failed: "
                f"id={request_id}, stage={error_stage}, error={error_message}"
            )

            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to set error: {e}", exc_info=True)
            return False

    @staticmethod
    def set_results(
        db: Session,
        request_id: str,
        video_url: Optional[str] = None,
        script_text: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> bool:
        """
        Set result URLs for a completed request.

        Args:
            db: Database session
            request_id: Request ID (UUID)
            video_url: Video URL (GCS)
            script_text: Script text or URL
            thumbnail_url: Thumbnail URL

        Returns:
            True if updated successfully
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.id == request_id
            ).first()

            if not request:
                return False

            if video_url:
                request.video_url = video_url
            if script_text:
                request.script_text = script_text
            if thumbnail_url:
                request.thumbnail_url = thumbnail_url

            db.commit()

            logger.info(
                f"Set request results: id={request_id}, video_url={video_url}"
            )

            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to set results: {e}", exc_info=True)
            return False

    @staticmethod
    def get_request_status(
        db: Session,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get request status for API response.

        Args:
            db: Database session
            request_id: Request ID (UUID)

        Returns:
            Dict with status information or None if not found
        """
        try:
            request = db.query(ContentRequest).filter(
                ContentRequest.id == request_id
            ).first()

            if not request:
                return None

            # Build status response
            status_data = {
                "request_id": str(request.id),
                "correlation_id": request.correlation_id,
                "status": request.status,
                "progress_percentage": request.progress_percentage,
                "current_stage": request.current_stage,
                "created_at": request.created_at.isoformat() if request.created_at else None,
                "started_at": request.started_at.isoformat() if request.started_at else None,
                "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            }

            # Add results if completed
            if request.status == "completed":
                status_data.update({
                    "video_url": request.video_url,
                    "script_text": request.script_text,
                    "thumbnail_url": request.thumbnail_url,
                })

            # Add error info if failed
            if request.status == "failed":
                status_data.update({
                    "error_message": request.error_message,
                    "error_stage": request.error_stage,
                    "error_details": request.error_details,
                    "failed_at": request.failed_at.isoformat() if request.failed_at else None,
                })

            return status_data

        except SQLAlchemyError as e:
            logger.error(f"Failed to get request status: {e}")
            return None


# Convenience function
def get_content_request_service() -> ContentRequestService:
    """Get ContentRequestService instance."""
    return ContentRequestService()
