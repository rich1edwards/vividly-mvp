"""
Content Access Tracking Service (Story 3.2.2)

Tracks content views, playback progress, and completion events for analytics.
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.content_metadata import ContentMetadata
from app.models.progress import StudentProgress, ProgressStatus

logger = logging.getLogger(__name__)


class ContentTrackingService:
    """Service for tracking content access and analytics."""

    def track_view(
        self,
        db: Session,
        cache_key: str,
        student_id: str,
        quality: str,
        device_type: str,
        browser: Optional[str] = None,
    ) -> bool:
        """
        Track content view event.

        Args:
            db: Database session
            cache_key: Content cache key
            student_id: Student user ID
            quality: Video quality (1080p, 720p, 480p)
            device_type: Device type (desktop, mobile, tablet)
            browser: Browser name (optional)

        Returns:
            bool: True if view was tracked successfully
        """
        try:
            # Get content metadata
            content = (
                db.query(ContentMetadata)
                .filter(ContentMetadata.cache_key == cache_key)
                .first()
            )

            if not content:
                logger.warning(f"Content not found for cache_key: {cache_key}")
                return False

            # Increment view count on content
            # TODO: Store detailed view records in ContentView table when it's created
            if content.views is None:
                content.views = 0
            content.views += 1

            db.commit()
            logger.info(f"Tracked view for content {cache_key} by student {student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to track view: {e}")
            db.rollback()
            return False

    def track_progress(
        self,
        db: Session,
        cache_key: str,
        student_id: str,
        current_time_seconds: int,
        duration_seconds: int,
        playback_speed: float = 1.0,
        paused: bool = False,
    ) -> bool:
        """
        Track content playback progress.

        Updates the student's progress record with current playback position.

        Args:
            db: Database session
            cache_key: Content cache key
            student_id: Student user ID
            current_time_seconds: Current playback position
            duration_seconds: Total content duration
            playback_speed: Playback speed (0.25-2.0)
            paused: Whether playback is currently paused

        Returns:
            bool: True if progress was tracked successfully
        """
        try:
            # Get content metadata
            content = (
                db.query(ContentMetadata)
                .filter(ContentMetadata.cache_key == cache_key)
                .first()
            )

            if not content:
                logger.warning(f"Content not found for cache_key: {cache_key}")
                return False

            # Get or create progress record
            progress = (
                db.query(StudentProgress)
                .filter(
                    StudentProgress.student_id == student_id,
                    StudentProgress.topic_id == content.topic_id,
                )
                .first()
            )

            if not progress:
                # Create new progress record
                # Store playback position in meta_data since model doesn't have dedicated field
                progress = StudentProgress(
                    student_id=student_id,
                    topic_id=content.topic_id,
                    status=ProgressStatus.IN_PROGRESS,
                    total_watch_time_seconds=current_time_seconds,
                    started_at=datetime.utcnow(),
                    meta_data={
                        "current_position_seconds": current_time_seconds,
                        "playback_speed": playback_speed,
                        "paused": paused
                    }
                )
                db.add(progress)
            else:
                # Update existing progress
                # Store current position in meta_data
                if progress.meta_data is None:
                    progress.meta_data = {}
                if isinstance(progress.meta_data, dict):
                    progress.meta_data["current_position_seconds"] = current_time_seconds
                    progress.meta_data["playback_speed"] = playback_speed
                    progress.meta_data["paused"] = paused

                # Update status if started
                if progress.status == ProgressStatus.NOT_STARTED:
                    progress.status = ProgressStatus.IN_PROGRESS
                    progress.started_at = datetime.utcnow()

            # Calculate progress percentage (model uses progress_percentage, not completion_percentage)
            progress_pct = int((current_time_seconds / duration_seconds) * 100)
            # Safely compare - handle None, Mock objects, or existing values
            try:
                current_pct = progress.progress_percentage
                # If it's None, unset, or less than new value, update it
                if current_pct is None or progress_pct > int(current_pct):
                    progress.progress_percentage = progress_pct
            except (TypeError, AttributeError):
                # If comparison fails (e.g., Mock object), just set it
                progress.progress_percentage = progress_pct

            db.commit()
            logger.debug(
                f"Tracked progress for {cache_key}: {current_time_seconds}/{duration_seconds}s"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to track progress: {e}")
            db.rollback()
            return False

    def track_completion(
        self,
        db: Session,
        cache_key: str,
        student_id: str,
        watch_duration_seconds: int,
        completion_percentage: float,
        skipped_segments: list,
    ) -> Dict:
        """
        Mark content as completed.

        Updates progress to COMPLETED status and checks for achievements.

        Args:
            db: Database session
            cache_key: Content cache key
            student_id: Student user ID
            watch_duration_seconds: Total watch duration
            completion_percentage: Percentage completed
            skipped_segments: List of skipped segments

        Returns:
            Dict with completion response:
                - achievement_unlocked: Optional achievement name
                - progress_updated: Whether progress was updated
                - streak_days: Current learning streak
        """
        try:
            # Get content metadata
            content = (
                db.query(ContentMetadata)
                .filter(ContentMetadata.cache_key == cache_key)
                .first()
            )

            if not content:
                logger.warning(f"Content not found for cache_key: {cache_key}")
                return {
                    "achievement_unlocked": None,
                    "progress_updated": False,
                    "streak_days": 0,
                }

            # Get or create progress record
            progress = (
                db.query(StudentProgress)
                .filter(
                    StudentProgress.student_id == student_id,
                    StudentProgress.topic_id == content.topic_id,
                )
                .first()
            )

            if not progress:
                progress = StudentProgress(
                    student_id=student_id,
                    topic_id=content.topic_id,
                    status=ProgressStatus.COMPLETED,
                    progress_percentage=int(completion_percentage),  # Model uses progress_percentage
                    total_watch_time_seconds=watch_duration_seconds,
                    completed_at=datetime.utcnow(),
                    started_at=datetime.utcnow(),
                    meta_data={
                        "skipped_segments": skipped_segments,
                        "completion_percentage": completion_percentage  # Store float value in meta_data
                    }
                )
                db.add(progress)
            else:
                # Update to completed
                progress.status = ProgressStatus.COMPLETED
                progress.progress_percentage = int(completion_percentage)  # Model uses progress_percentage
                progress.total_watch_time_seconds = watch_duration_seconds
                progress.completed_at = datetime.utcnow()
                # Store additional metadata
                if progress.meta_data is None:
                    progress.meta_data = {}
                if isinstance(progress.meta_data, dict):
                    progress.meta_data["skipped_segments"] = skipped_segments
                    progress.meta_data["completion_percentage"] = completion_percentage

            # Check for achievements
            achievement = self._check_achievements(db, student_id, progress)

            # Calculate streak
            streak_days = self._calculate_streak(db, student_id)

            db.commit()
            logger.info(
                f"Marked content {cache_key} as completed for student {student_id}"
            )

            return {
                "achievement_unlocked": achievement,
                "progress_updated": True,
                "streak_days": streak_days,
            }

        except Exception as e:
            logger.error(f"Failed to track completion: {e}")
            db.rollback()
            return {
                "achievement_unlocked": None,
                "progress_updated": False,
                "streak_days": 0,
            }

    def get_content_analytics(self, db: Session, cache_key: str) -> Optional[Dict]:
        """
        Get analytics for content.

        Args:
            db: Database session
            cache_key: Content cache key

        Returns:
            Dict with analytics data or None if content not found
        """
        try:
            # Get content metadata
            content = (
                db.query(ContentMetadata)
                .filter(ContentMetadata.cache_key == cache_key)
                .first()
            )

            if not content:
                return None

            # Get view statistics
            # TODO: Query ContentView table when it's created
            total_views = content.views or 0
            unique_viewers = 0  # TODO: Count unique viewers from ContentView table

            # Get average completion rate from progress
            # Model uses progress_percentage field, not completion_percentage
            progress_stats = (
                db.query(
                    func.avg(StudentProgress.progress_percentage).label(
                        "avg_completion"
                    ),
                    func.avg(StudentProgress.total_watch_time_seconds).label(
                        "avg_duration"
                    ),
                )
                .filter(
                    StudentProgress.topic_id == content.topic_id,
                    StudentProgress.status == ProgressStatus.COMPLETED,
                )
                .first()
            )

            avg_completion_rate = progress_stats.avg_completion or 0.0
            avg_watch_duration = progress_stats.avg_duration or 0.0

            # Get most popular quality
            # TODO: Query from ContentView table when it's created
            popular_quality = "1080p"  # Default

            return {
                "cache_key": cache_key,
                "total_views": total_views,
                "unique_viewers": unique_viewers,
                "avg_watch_duration": float(avg_watch_duration),
                "avg_completion_rate": float(avg_completion_rate),
                "popular_quality": popular_quality,
            }

        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return None

    def _check_achievements(
        self, db: Session, student_id: str, progress: StudentProgress
    ) -> Optional[str]:
        """
        Check if student unlocked any achievements.

        Args:
            db: Database session
            student_id: Student user ID
            progress: Student progress record

        Returns:
            Achievement name if unlocked, None otherwise
        """
        # Count completed topics
        completed_count = (
            db.query(func.count(StudentProgress.topic_id))
            .filter(
                StudentProgress.student_id == student_id,
                StudentProgress.status == ProgressStatus.COMPLETED,
            )
            .scalar()
            or 0
        )

        # First completion achievement
        if completed_count == 1:
            return "First Video Complete"

        # Milestone achievements
        if completed_count == 10:
            return "Ten Topics Mastered"
        elif completed_count == 50:
            return "Halfway There"
        elif completed_count == 100:
            return "Century Club"

        return None

    def _calculate_streak(self, db: Session, student_id: str) -> int:
        """
        Calculate student's learning streak in days.

        Args:
            db: Database session
            student_id: Student user ID

        Returns:
            Number of consecutive days with completed content
        """
        try:
            # Get completions ordered by date
            completions = (
                db.query(
                    func.date(StudentProgress.completed_at).label("completion_date")
                )
                .filter(
                    StudentProgress.student_id == student_id,
                    StudentProgress.status == ProgressStatus.COMPLETED,
                    StudentProgress.completed_at.isnot(None),
                )
                .distinct()
                .order_by(func.date(StudentProgress.completed_at).desc())
                .all()
            )

            if not completions:
                return 0

            # Calculate streak
            streak = 0
            today = datetime.utcnow().date()

            for completion in completions:
                expected_date = today - timedelta(days=streak)
                if completion.completion_date == expected_date:
                    streak += 1
                else:
                    break

            return streak

        except Exception as e:
            logger.error(f"Failed to calculate streak: {e}")
            return 0
