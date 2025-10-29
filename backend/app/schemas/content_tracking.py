"""
Content Access Tracking Schemas (Story 3.2.2)

Pydantic models for view tracking, progress updates, and completion events.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ViewTrackingRequest(BaseModel):
    """Track content view event."""

    quality: str = Field(..., description="Video quality (1080p, 720p, 480p)")
    device_type: str = Field(..., description="Device type (desktop, mobile, tablet)")
    browser: Optional[str] = Field(None, description="Browser name")

    class Config:
        json_schema_extra = {
            "example": {
                "quality": "1080p",
                "device_type": "desktop",
                "browser": "Chrome"
            }
        }


class ProgressTrackingRequest(BaseModel):
    """Track content playback progress."""

    current_time_seconds: int = Field(..., ge=0, description="Current playback position")
    duration_seconds: int = Field(..., gt=0, description="Total content duration")
    playback_speed: float = Field(default=1.0, ge=0.25, le=2.0, description="Playback speed")
    paused: bool = Field(default=False, description="Whether playback is paused")

    class Config:
        json_schema_extra = {
            "example": {
                "current_time_seconds": 120,
                "duration_seconds": 180,
                "playback_speed": 1.0,
                "paused": False
            }
        }


class CompletionTrackingRequest(BaseModel):
    """Mark content as completed."""

    watch_duration_seconds: int = Field(..., ge=0, description="Total watch duration")
    completion_percentage: float = Field(..., ge=0, le=100, description="Percentage completed")
    skipped_segments: List[dict] = Field(default=[], description="Segments that were skipped")

    class Config:
        json_schema_extra = {
            "example": {
                "watch_duration_seconds": 178,
                "completion_percentage": 98.9,
                "skipped_segments": []
            }
        }


class CompletionResponse(BaseModel):
    """Response for completion tracking."""

    achievement_unlocked: Optional[str] = Field(None, description="Achievement earned")
    progress_updated: bool = Field(..., description="Whether progress was updated")
    streak_days: int = Field(default=0, description="Current learning streak")

    class Config:
        json_schema_extra = {
            "example": {
                "achievement_unlocked": "First Video Complete",
                "progress_updated": True,
                "streak_days": 4
            }
        }


class ContentAnalytics(BaseModel):
    """Content analytics summary."""

    cache_key: str = Field(..., description="Content cache key")
    total_views: int = Field(..., description="Total view count")
    unique_viewers: int = Field(..., description="Unique student count")
    avg_watch_duration: float = Field(..., description="Average watch duration (seconds)")
    avg_completion_rate: float = Field(..., description="Average completion percentage")
    popular_quality: str = Field(..., description="Most popular quality setting")

    class Config:
        json_schema_extra = {
            "example": {
                "cache_key": "abc123def456",
                "total_views": 1500,
                "unique_viewers": 450,
                "avg_watch_duration": 165.5,
                "avg_completion_rate": 87.3,
                "popular_quality": "1080p"
            }
        }
