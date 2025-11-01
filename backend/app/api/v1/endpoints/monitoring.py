"""
Request Monitoring API Endpoints

Provides real-time visibility into content generation pipeline for super admins.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.services.request_monitoring_service import get_monitoring_service

router = APIRouter()


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super admin role for monitoring endpoints."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can access monitoring data",
        )
    return current_user


@router.get("/requests", response_model=List[Dict[str, Any]])
def get_all_active_requests(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of requests"),
    current_user: User = Depends(require_super_admin),
):
    """
    Get all active content generation requests.

    Returns list of active requests with their current pipeline stage,
    status, and elapsed time.

    **Permissions:** Super Admin only
    """
    monitoring_service = get_monitoring_service()
    requests = monitoring_service.get_all_active_requests(
        student_id=student_id, limit=limit
    )
    return requests


@router.get("/requests/{request_id}", response_model=Dict[str, Any])
def get_request_flow(
    request_id: str, current_user: User = Depends(require_super_admin)
):
    """
    Get complete flow details for a specific request.

    Returns all pipeline events, confidence scores, and metadata
    for the specified request ID.

    **Permissions:** Super Admin only
    """
    monitoring_service = get_monitoring_service()
    flow = monitoring_service.get_request_flow(request_id)

    if not flow["found"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found in monitoring cache",
        )

    return flow


@router.get("/search", response_model=List[Dict[str, Any]])
def search_requests(
    student_email: Optional[str] = Query(None, description="Student email address"),
    student_id: Optional[str] = Query(None, description="Student user ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Search requests by student email or ID.

    Provide either student_email or student_id to find all requests
    for that student.

    **Permissions:** Super Admin only
    """
    if not student_email and not student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either student_email or student_id",
        )

    monitoring_service = get_monitoring_service()
    requests = monitoring_service.search_by_student(
        db=db, student_email=student_email, student_id=student_id, limit=limit
    )

    return requests


@router.get("/metrics", response_model=Dict[str, Any])
def get_system_metrics(current_user: User = Depends(require_super_admin)):
    """
    Get system-wide monitoring metrics.

    Returns aggregate statistics about all requests in the monitoring cache:
    - Total, active, completed, and failed request counts
    - Average confidence scores by pipeline stage
    - Stage distribution

    **Permissions:** Super Admin only
    """
    monitoring_service = get_monitoring_service()
    metrics = monitoring_service.get_system_metrics()
    return metrics


@router.get("/health", response_model=Dict[str, str])
def monitoring_health_check(current_user: User = Depends(require_super_admin)):
    """
    Health check for monitoring service.

    **Permissions:** Super Admin only
    """
    return {"status": "healthy", "service": "request_monitoring"}
