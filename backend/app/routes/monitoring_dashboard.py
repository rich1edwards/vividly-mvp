"""
Monitoring Dashboard API Routes

Real-time monitoring dashboard for tracking content generation requests.

Endpoints:
- GET /api/v1/monitoring/dashboard - Dashboard overview
- GET /api/v1/monitoring/requests - List active requests
- GET /api/v1/monitoring/requests/{id} - Get request details
- GET /api/v1/monitoring/requests/{id}/events - Get request event log
- GET /api/v1/monitoring/metrics - Get aggregated metrics
- GET /api/v1/monitoring/stream - Server-Sent Events for real-time updates
- GET /api/v1/monitoring/circuit-breakers - Get circuit breaker stats
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_

from ..middleware.auth import get_current_active_user, require_admin, require_teacher
from ..services.request_tracker import RequestTracker
from ..services.circuit_breaker import get_all_circuit_breaker_stats
from ..models.request_tracking import (
    ContentRequest,
    RequestStage,
    RequestEvent,
    RequestMetrics,
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring Dashboard"])


# Response Models


class DashboardOverviewResponse(BaseModel):
    """Overview statistics for dashboard."""

    active_requests: int
    completed_today: int
    failed_today: int
    avg_duration_seconds: Optional[float]
    success_rate_today: Optional[float]
    requests_per_hour: float
    circuit_breaker_status: dict


class RequestSummary(BaseModel):
    """Summary of a content request."""

    id: str
    correlation_id: str
    student_id: str
    student_name: Optional[str]
    topic: str
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    created_at: str
    elapsed_seconds: int
    error_message: Optional[str]


class RequestDetail(BaseModel):
    """Detailed request information."""

    id: str
    correlation_id: str
    student_id: str
    topic: str
    learning_objective: Optional[str]
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    total_duration_seconds: Optional[int]
    video_url: Optional[str]
    error_message: Optional[str]
    error_stage: Optional[str]
    retry_count: int
    stages: List[dict]


class MetricsBucket(BaseModel):
    """Metrics for a time bucket."""

    time_bucket: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    in_progress: int
    avg_duration: Optional[float]
    p95_duration: Optional[float]


# Dependencies


def get_db() -> Session:
    """Get database session (placeholder)."""
    # Implement based on your DB setup
    raise NotImplementedError("Database dependency not configured")


# Routes


@router.get("/dashboard", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user=Depends(require_teacher),  # Teachers and admins can view
    db: Session = Depends(get_db),
):
    """
    Get dashboard overview with key metrics.

    Includes:
    - Active request count
    - Completed/failed today
    - Success rate
    - Average duration
    - Circuit breaker status
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Active requests
    active_count = (
        db.query(func.count(ContentRequest.id))
        .filter(
            ContentRequest.status.in_(
                [
                    "pending",
                    "validating",
                    "retrieving",
                    "generating_script",
                    "generating_video",
                    "processing_video",
                    "notifying",
                ]
            )
        )
        .scalar()
    )

    # Completed today
    completed_today = (
        db.query(func.count(ContentRequest.id))
        .filter(
            and_(
                ContentRequest.status == "completed",
                ContentRequest.completed_at >= today_start,
            )
        )
        .scalar()
    )

    # Failed today
    failed_today = (
        db.query(func.count(ContentRequest.id))
        .filter(
            and_(
                ContentRequest.status == "failed",
                ContentRequest.failed_at >= today_start,
            )
        )
        .scalar()
    )

    # Average duration for completed requests today
    avg_duration = (
        db.query(func.avg(ContentRequest.total_duration_seconds))
        .filter(
            and_(
                ContentRequest.status == "completed",
                ContentRequest.completed_at >= today_start,
            )
        )
        .scalar()
    )

    # Success rate
    total_finished_today = completed_today + failed_today
    success_rate = (
        (completed_today / total_finished_today * 100)
        if total_finished_today > 0
        else None
    )

    # Requests per hour (last 24 hours)
    day_ago = now - timedelta(hours=24)
    requests_last_24h = (
        db.query(func.count(ContentRequest.id))
        .filter(ContentRequest.created_at >= day_ago)
        .scalar()
    )
    requests_per_hour = requests_last_24h / 24.0

    # Circuit breaker status
    circuit_breaker_status = get_all_circuit_breaker_stats()

    return DashboardOverviewResponse(
        active_requests=active_count or 0,
        completed_today=completed_today or 0,
        failed_today=failed_today or 0,
        avg_duration_seconds=float(avg_duration) if avg_duration else None,
        success_rate_today=success_rate,
        requests_per_hour=requests_per_hour,
        circuit_breaker_status=circuit_breaker_status,
    )


@router.get("/requests", response_model=List[RequestSummary])
async def list_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user=Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    List content requests with optional filtering.

    Teachers see their organization's requests.
    Admins see all requests (or filtered by org).
    """
    query = db.query(ContentRequest)

    # Filter by organization if teacher
    if hasattr(current_user, "role") and current_user.role == "teacher":
        query = query.filter(
            ContentRequest.organization_id == current_user.organization_id
        )

    # Filter by status
    if status:
        if status == "active":
            query = query.filter(
                ContentRequest.status.in_(
                    [
                        "pending",
                        "validating",
                        "retrieving",
                        "generating_script",
                        "generating_video",
                        "processing_video",
                        "notifying",
                    ]
                )
            )
        else:
            query = query.filter(ContentRequest.status == status)

    # Order by created_at descending
    query = query.order_by(desc(ContentRequest.created_at))

    # Pagination
    requests = query.offset(offset).limit(limit).all()

    # Convert to response
    results = []
    for req in requests:
        elapsed = (
            (datetime.utcnow() - req.created_at).total_seconds()
            if req.created_at
            else 0
        )
        results.append(
            RequestSummary(
                id=str(req.id),
                correlation_id=req.correlation_id,
                student_id=str(req.student_id),
                student_name=req.student.name if req.student else None,
                topic=req.topic,
                status=req.status,
                current_stage=req.current_stage,
                progress_percentage=req.progress_percentage,
                created_at=req.created_at.isoformat() if req.created_at else None,
                elapsed_seconds=int(elapsed),
                error_message=req.error_message,
            )
        )

    return results


@router.get("/requests/{request_id}", response_model=RequestDetail)
async def get_request_detail(
    request_id: str,
    current_user=Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific request.

    Includes all stages and their status.
    """
    tracker = RequestTracker(db)
    status = tracker.get_request_status(request_id)

    if not status:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Request not found")

    request = db.query(ContentRequest).filter(ContentRequest.id == request_id).first()

    return RequestDetail(
        id=status["request_id"],
        correlation_id=status["correlation_id"],
        student_id=str(request.student_id),
        topic=request.topic,
        learning_objective=request.learning_objective,
        status=status["status"],
        current_stage=status["current_stage"],
        progress_percentage=status["progress_percentage"],
        created_at=status["created_at"],
        started_at=status["started_at"],
        completed_at=status["completed_at"],
        total_duration_seconds=status["total_duration_seconds"],
        video_url=status["video_url"],
        error_message=status["error_message"],
        error_stage=status["error_stage"],
        retry_count=request.retry_count,
        stages=status["stages"],
    )


@router.get("/requests/{request_id}/events")
async def get_request_events(
    request_id: str,
    limit: int = Query(100, le=500),
    current_user=Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Get event log for a request.

    Returns detailed timeline of events for debugging.
    """
    tracker = RequestTracker(db)
    events = tracker.get_request_events(request_id, limit=limit)

    return {"request_id": request_id, "events": events}


@router.get("/metrics", response_model=List[MetricsBucket])
async def get_metrics(
    hours: int = Query(24, le=168),  # Max 1 week
    current_user=Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Get aggregated metrics for dashboard charts.

    Returns hourly buckets with request counts, success/failure rates, etc.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Query aggregated metrics
    results = (
        db.query(
            func.date_trunc("hour", ContentRequest.created_at).label("hour"),
            func.count(ContentRequest.id).label("total"),
            func.count(ContentRequest.id)
            .filter(ContentRequest.status == "completed")
            .label("successful"),
            func.count(ContentRequest.id)
            .filter(ContentRequest.status == "failed")
            .label("failed"),
            func.count(ContentRequest.id)
            .filter(
                ContentRequest.status.in_(
                    [
                        "pending",
                        "validating",
                        "retrieving",
                        "generating_script",
                        "generating_video",
                        "processing_video",
                        "notifying",
                    ]
                )
            )
            .label("in_progress"),
            func.avg(ContentRequest.total_duration_seconds)
            .filter(ContentRequest.status == "completed")
            .label("avg_duration"),
        )
        .filter(ContentRequest.created_at >= cutoff)
        .group_by(func.date_trunc("hour", ContentRequest.created_at))
        .order_by(desc("hour"))
        .all()
    )

    return [
        MetricsBucket(
            time_bucket=row.hour.isoformat() if row.hour else None,
            total_requests=row.total or 0,
            successful_requests=row.successful or 0,
            failed_requests=row.failed or 0,
            in_progress=row.in_progress or 0,
            avg_duration=float(row.avg_duration) if row.avg_duration else None,
            p95_duration=None,  # Could calculate with percentile_cont
        )
        for row in results
    ]


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    current_user=Depends(require_admin),
):
    """
    Get current status of all circuit breakers.

    Admin only. Shows state, failure counts, etc.
    """
    stats = get_all_circuit_breaker_stats()
    return {"circuit_breakers": stats}


@router.get("/stream")
async def stream_updates(
    request: Request,
    current_user=Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events stream for real-time dashboard updates.

    Sends updates every 2 seconds with current request status.
    """

    async def event_generator():
        """Generate SSE events."""
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Get current active requests
                active_requests = (
                    db.query(ContentRequest)
                    .filter(
                        ContentRequest.status.in_(
                            [
                                "pending",
                                "validating",
                                "retrieving",
                                "generating_script",
                                "generating_video",
                                "processing_video",
                                "notifying",
                            ]
                        )
                    )
                    .order_by(desc(ContentRequest.created_at))
                    .limit(20)
                    .all()
                )

                # Format as SSE event
                data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_count": len(active_requests),
                    "requests": [
                        {
                            "id": str(req.id),
                            "correlation_id": req.correlation_id,
                            "status": req.status,
                            "current_stage": req.current_stage,
                            "progress_percentage": req.progress_percentage,
                            "topic": req.topic,
                        }
                        for req in active_requests
                    ],
                }

                yield f"data: {json.dumps(data)}\n\n"

                # Wait 2 seconds before next update
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
