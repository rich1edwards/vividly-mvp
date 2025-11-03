"""
Request Tracking Models

SQLAlchemy models for end-to-end request tracking.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    ForeignKey,
    TIMESTAMP,
    CheckConstraint,
    text,
    Numeric,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.core.database import Base

# Enums
REQUEST_STATUS_ENUM = ENUM(
    "pending",
    "validating",
    "retrieving",
    "generating_script",
    "generating_video",
    "processing_video",
    "notifying",
    "completed",
    "failed",
    "cancelled",
    name="request_status",
    create_type=False,  # Created in migration
)

STAGE_STATUS_ENUM = ENUM(
    "pending",
    "in_progress",
    "completed",
    "failed",
    "skipped",
    name="stage_status",
    create_type=False,
)


class ContentRequest(Base):
    """
    Tracks content generation requests end-to-end.
    """

    __tablename__ = "content_requests"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Correlation ID for distributed tracing
    correlation_id = Column(String(64), nullable=False, unique=True, index=True)

    # Request details
    student_id = Column(
        String(100),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic = Column(String(500), nullable=False)
    learning_objective = Column(Text)
    grade_level = Column(String(50))
    duration_minutes = Column(Integer)

    # Current state
    status = Column(REQUEST_STATUS_ENUM, default="pending", nullable=False, index=True)
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    failed_at = Column(TIMESTAMP)

    # Results
    video_url = Column(Text)
    script_text = Column(Text)
    thumbnail_url = Column(Text)

    # Error tracking
    error_message = Column(Text)
    error_stage = Column(String(100))
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)

    # Metadata
    request_metadata = Column(JSON)

    # Performance metrics
    total_duration_seconds = Column(Integer)

    # Organization context
    # NOTE: FK constraint removed - organizations table doesn't exist yet
    # Will restore FK when organizations table is created
    organization_id = Column(String(100), nullable=True, index=True)

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    stages = relationship(
        "RequestStage", back_populates="request", cascade="all, delete-orphan"
    )
    events = relationship(
        "RequestEvent", back_populates="request", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="valid_progress",
        ),
    )

    def __repr__(self):
        return (
            f"<ContentRequest(id={self.id}, status={self.status}, topic={self.topic})>"
        )

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "correlation_id": self.correlation_id,
            "student_id": str(self.student_id),
            "topic": self.topic,
            "learning_objective": self.learning_objective,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress_percentage": self.progress_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "total_duration_seconds": self.total_duration_seconds,
            "video_url": self.video_url,
            "error_message": self.error_message,
            "error_stage": self.error_stage,
        }


class RequestStage(Base):
    """
    Tracks individual stages of the content generation pipeline.
    """

    __tablename__ = "request_stages"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Stage identification
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)

    # Status
    status = Column(STAGE_STATUS_ENUM, default="pending", nullable=False)

    # Timestamps
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)

    # Duration
    duration_seconds = Column(Numeric(10, 3))

    # Results
    output_data = Column(JSON)

    # Errors
    error_message = Column(Text)
    error_details = Column(JSON)

    # Retries
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Metadata
    stage_meta_data = Column(JSON)

    # Relationships
    request = relationship("ContentRequest", back_populates="stages")

    def __repr__(self):
        return f"<RequestStage(request_id={self.request_id}, stage={self.stage_name}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "stage_name": self.stage_name,
            "stage_order": self.stage_order,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_seconds": float(self.duration_seconds)
            if self.duration_seconds
            else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


class RequestEvent(Base):
    """
    Detailed event log for request debugging and monitoring.
    """

    __tablename__ = "request_events"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_message = Column(Text, nullable=False)

    # Context
    stage_name = Column(String(100))
    severity = Column(String(20))  # info, warning, error, critical

    # Timestamp
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False, index=True)

    # Additional data
    event_data = Column(JSON)

    # Source
    source_service = Column(String(100))
    source_host = Column(String(255))

    # Relationships
    request = relationship("ContentRequest", back_populates="events")

    def __repr__(self):
        return f"<RequestEvent(request_id={self.request_id}, type={self.event_type}, severity={self.severity})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "event_message": self.event_message,
            "stage_name": self.stage_name,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "event_data": self.event_data,
            "source_service": self.source_service,
        }


class RequestMetrics(Base):
    """
    Aggregated metrics for dashboard and reporting.
    """

    __tablename__ = "request_metrics"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Time bucket (hourly)
    time_bucket = Column(TIMESTAMP, nullable=False, index=True)

    # Aggregation scope
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), index=True
    )

    # Metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    cancelled_requests = Column(Integer, default=0)

    # Average durations (seconds)
    avg_total_duration = Column(Numeric(10, 2))
    avg_validation_duration = Column(Numeric(10, 2))
    avg_rag_duration = Column(Numeric(10, 2))
    avg_script_duration = Column(Numeric(10, 2))
    avg_video_duration = Column(Numeric(10, 2))

    # Error breakdown
    validation_errors = Column(Integer, default=0)
    rag_errors = Column(Integer, default=0)
    script_errors = Column(Integer, default=0)
    video_errors = Column(Integer, default=0)
    upload_errors = Column(Integer, default=0)

    # Circuit breaker stats
    circuit_breaker_open_count = Column(Integer, default=0)

    # Metadata
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<RequestMetrics(time_bucket={self.time_bucket}, total={self.total_requests})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "time_bucket": self.time_bucket.isoformat() if self.time_bucket else None,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_total_duration": float(self.avg_total_duration)
            if self.avg_total_duration
            else None,
            "validation_errors": self.validation_errors,
            "rag_errors": self.rag_errors,
            "script_errors": self.script_errors,
            "video_errors": self.video_errors,
        }


class PipelineStageDefinition(Base):
    """
    Configuration for pipeline stages.
    """

    __tablename__ = "pipeline_stage_definitions"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    stage_name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    stage_order = Column(Integer, nullable=False)
    estimated_duration_seconds = Column(Integer)
    description = Column(Text)
    is_critical = Column(Integer, default=1)  # SQLite doesn't have real boolean

    def __repr__(self):
        return f"<PipelineStageDefinition(name={self.stage_name}, order={self.stage_order})>"
