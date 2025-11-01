"""
Request Monitoring Service

Tracks the flow of content generation requests through the system pipeline.
Provides real-time visibility into request status, confidence scores, and performance metrics.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.user import User

logger = logging.getLogger(__name__)


# In-memory cache for real-time updates (can be replaced with Redis in production)
_request_events_cache: Dict[str, List[Dict[str, Any]]] = {}
_max_cache_size = 1000  # Maximum number of requests to keep in memory


class RequestMonitoringService:
    """
    Service for monitoring content generation request flow.

    Tracks requests through pipeline stages:
    1. Request Received (Frontend → Backend)
    2. NLU Topic Extraction
    3. Interest Matching
    4. RAG Content Retrieval
    5. Script Generation
    6. TTS Audio Generation
    7. Video Generation
    8. Completion
    """

    # Pipeline stages
    STAGE_REQUEST_RECEIVED = "request_received"
    STAGE_NLU = "nlu_extraction"
    STAGE_INTEREST_MATCH = "interest_matching"
    STAGE_RAG = "rag_retrieval"
    STAGE_SCRIPT = "script_generation"
    STAGE_TTS = "tts_generation"
    STAGE_VIDEO = "video_generation"
    STAGE_COMPLETED = "completed"
    STAGE_FAILED = "failed"

    def __init__(self):
        """Initialize monitoring service."""
        self.cache = _request_events_cache

    def track_event(
        self,
        request_id: str,
        student_id: str,
        stage: str,
        status: str = "in_progress",
        confidence_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a request pipeline event.

        Args:
            request_id: Unique request identifier
            student_id: Student user ID
            stage: Pipeline stage (use STAGE_* constants)
            status: Event status (in_progress, completed, failed)
            confidence_score: Model confidence score (0.0-1.0)
            metadata: Additional metadata (topic_id, interest, etc.)
            error: Error message if status is failed

        Returns:
            Dict with event details
        """
        event = {
            "request_id": request_id,
            "student_id": student_id,
            "stage": stage,
            "status": status,
            "confidence_score": confidence_score,
            "metadata": metadata or {},
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to cache
        if request_id not in self.cache:
            self.cache[request_id] = []

        self.cache[request_id].append(event)

        # Cleanup old entries if cache is too large
        self._cleanup_cache()

        logger.info(
            f"[Monitor] Request {request_id[:8]}... | "
            f"Stage: {stage} | Status: {status} | "
            f"Confidence: {confidence_score if confidence_score else 'N/A'}"
        )

        return event

    def get_request_flow(self, request_id: str) -> Dict[str, Any]:
        """
        Get complete flow for a specific request.

        Args:
            request_id: Request identifier

        Returns:
            Dict with request flow details and all events
        """
        events = self.cache.get(request_id, [])

        if not events:
            return {
                "request_id": request_id,
                "found": False,
                "events": [],
                "current_stage": None,
                "status": "unknown"
            }

        # Determine current stage and overall status
        latest_event = events[-1]
        current_stage = latest_event["stage"]

        # Check if completed or failed
        if current_stage == self.STAGE_COMPLETED:
            status = "completed"
        elif current_stage == self.STAGE_FAILED or latest_event["status"] == "failed":
            status = "failed"
        else:
            status = "in_progress"

        # Calculate metrics
        first_event = events[0]
        start_time = datetime.fromisoformat(first_event["timestamp"])
        current_time = datetime.utcnow()
        elapsed_seconds = (current_time - start_time).total_seconds()

        return {
            "request_id": request_id,
            "found": True,
            "student_id": latest_event["student_id"],
            "current_stage": current_stage,
            "status": status,
            "events": events,
            "started_at": first_event["timestamp"],
            "elapsed_seconds": elapsed_seconds,
            "total_stages": len(events),
            "metadata": latest_event.get("metadata", {})
        }

    def get_all_active_requests(
        self,
        student_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all active (in-progress) requests.

        Args:
            student_id: Filter by student ID (optional)
            limit: Maximum number of requests to return

        Returns:
            List of active request flows
        """
        active_requests = []

        for request_id, events in self.cache.items():
            if not events:
                continue

            latest_event = events[-1]

            # Skip completed/failed requests older than 5 minutes
            if latest_event["stage"] in [self.STAGE_COMPLETED, self.STAGE_FAILED]:
                event_time = datetime.fromisoformat(latest_event["timestamp"])
                if (datetime.utcnow() - event_time).total_seconds() > 300:
                    continue

            # Filter by student_id if provided
            if student_id and latest_event["student_id"] != student_id:
                continue

            flow = self.get_request_flow(request_id)
            active_requests.append(flow)

        # Sort by most recent first
        active_requests.sort(
            key=lambda x: x["started_at"],
            reverse=True
        )

        return active_requests[:limit]

    def search_by_student(
        self,
        db: Session,
        student_email: Optional[str] = None,
        student_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search requests by student email or ID.

        Args:
            db: Database session
            student_email: Student email address
            student_id: Student user ID
            limit: Maximum results

        Returns:
            List of request flows for the student
        """
        # Get student ID from email if provided
        if student_email and not student_id:
            student = db.query(User).filter(
                User.email == student_email
            ).first()
            if student:
                student_id = student.user_id
            else:
                return []

        if not student_id:
            return []

        return self.get_all_active_requests(student_id=student_id, limit=limit)

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide metrics.

        Returns:
            Dict with system metrics
        """
        total_requests = len(self.cache)
        active_count = 0
        completed_count = 0
        failed_count = 0
        avg_confidence_scores = {}
        stage_counts = {}

        for request_id, events in self.cache.items():
            if not events:
                continue

            latest_event = events[-1]

            # Count by status
            if latest_event["stage"] == self.STAGE_COMPLETED:
                completed_count += 1
            elif latest_event["stage"] == self.STAGE_FAILED or latest_event["status"] == "failed":
                failed_count += 1
            else:
                active_count += 1

            # Count by stage
            for event in events:
                stage = event["stage"]
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

                # Collect confidence scores
                if event.get("confidence_score") is not None:
                    if stage not in avg_confidence_scores:
                        avg_confidence_scores[stage] = []
                    avg_confidence_scores[stage].append(event["confidence_score"])

        # Calculate average confidence scores
        avg_scores = {}
        for stage, scores in avg_confidence_scores.items():
            if scores:
                avg_scores[stage] = sum(scores) / len(scores)

        return {
            "total_requests": total_requests,
            "active_requests": active_count,
            "completed_requests": completed_count,
            "failed_requests": failed_count,
            "stage_counts": stage_counts,
            "avg_confidence_scores": avg_scores,
            "cache_size": len(self.cache),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _cleanup_cache(self):
        """
        Clean up old entries from cache.
        Removes completed/failed requests older than 1 hour.
        """
        if len(self.cache) <= _max_cache_size:
            return

        # Find old completed/failed requests
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        to_remove = []

        for request_id, events in self.cache.items():
            if not events:
                to_remove.append(request_id)
                continue

            latest_event = events[-1]
            if latest_event["stage"] in [self.STAGE_COMPLETED, self.STAGE_FAILED]:
                event_time = datetime.fromisoformat(latest_event["timestamp"])
                if event_time < cutoff_time:
                    to_remove.append(request_id)

        # Remove old entries
        for request_id in to_remove:
            del self.cache[request_id]

        logger.info(f"[Monitor] Cleaned up {len(to_remove)} old requests from cache")


# Global instance
_monitoring_service = None


def get_monitoring_service() -> RequestMonitoringService:
    """Get or create monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = RequestMonitoringService()
    return _monitoring_service
