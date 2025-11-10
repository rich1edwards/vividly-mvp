"""
Health Check and Monitoring Endpoints

Session 11 Part 19: Added comprehensive health checks for prompt system
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.prompt_templates import get_metrics, TemplateSource

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint

    Returns:
        Status and basic system information
    """
    return {"status": "healthy", "service": "vividly-api", "version": "1.0.0"}


@router.get("/health/database")
async def database_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Database connectivity health check

    Returns:
        Database connection status and metrics
    """
    try:
        # Simple query to test connectivity
        db.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection is active",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)[:200],
        }


@router.get("/health/prompt-system")
async def prompt_system_health() -> Dict[str, Any]:
    """
    Prompt template system health check and metrics

    Returns:
        Detailed metrics about prompt template loading:
        - Template source distribution (database vs file fallback)
        - Error rates
        - Total request count
    """
    metrics = get_metrics()

    # Calculate health indicators
    total_requests = metrics["total_requests"]
    database_success_rate = 0.0
    fallback_rate = 0.0
    error_rate = 0.0

    if total_requests > 0:
        database_success_rate = (metrics["database_success"] / total_requests) * 100
        fallback_rate = (metrics["file_fallback_usage"] / total_requests) * 100
        error_rate = (metrics["database_errors"] / total_requests) * 100

    # Determine overall status
    status = "healthy"
    warnings = []

    if error_rate > 50:
        status = "degraded"
        warnings.append("High database error rate - system operating on fallback")
    elif fallback_rate > 90 and total_requests > 10:
        status = "degraded"
        warnings.append(
            "Primarily using file-based fallback - database may not be migrated"
        )

    return {
        "status": status,
        "warnings": warnings,
        "metrics": {
            "total_requests": total_requests,
            "database_success": metrics["database_success"],
            "database_errors": metrics["database_errors"],
            "environment_usage": metrics["environment_usage"],
            "file_fallback_usage": metrics["file_fallback_usage"],
        },
        "rates": {
            "database_success_rate": round(database_success_rate, 2),
            "fallback_rate": round(fallback_rate, 2),
            "error_rate": round(error_rate, 2),
        },
        "interpretation": {
            "database_available": database_success_rate > 0,
            "fallback_working": fallback_rate > 0 or total_requests == 0,
            "primary_source": TemplateSource.DATABASE.value
            if database_success_rate > fallback_rate
            else TemplateSource.FILE_DEFAULT.value,
        },
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check combining all subsystems

    Returns:
        Complete system health status
    """
    # Get individual health checks
    db_health = await database_health(db)
    prompt_health = await prompt_system_health()

    # Aggregate status
    overall_status = "healthy"
    if db_health["status"] == "unhealthy" or prompt_health["status"] == "degraded":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": {"database": db_health, "prompt_system": prompt_health},
        "service": "vividly-api",
        "version": "1.0.0",
    }
