"""
Cache API Schemas

Pydantic models for cache check and storage endpoints (Story 3.1.1).
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CacheCheckRequest(BaseModel):
    """Request to check if content exists in cache."""

    topic_id: str = Field(..., description="Canonical topic ID", min_length=1)
    interest: str = Field(..., description="Student interest", min_length=1)
    style: str = Field(default="standard", description="Content style")

    class Config:
        json_schema_extra = {
            "example": {
                "topic_id": "topic_phys_mech_newton_3",
                "interest": "basketball",
                "style": "standard",
            }
        }


class CacheCheckResponse(BaseModel):
    """Response from cache check."""

    cache_hit: bool = Field(..., description="True if content exists in cache")
    cache_key: Optional[str] = Field(None, description="Cache key if hit")
    status: Optional[str] = Field(
        None, description="Content status (completed, generating, etc.)"
    )
    video_url: Optional[str] = Field(None, description="CDN URL for video if available")
    audio_url: Optional[str] = Field(None, description="CDN URL for audio if available")
    script_url: Optional[str] = Field(
        None, description="GCS URL for script JSON if available"
    )
    thumbnail_url: Optional[str] = Field(
        None, description="CDN URL for thumbnail if available"
    )
    duration_seconds: Optional[int] = Field(
        None, description="Video duration in seconds"
    )
    generated_at: Optional[str] = Field(
        None, description="ISO timestamp when content was generated"
    )
    cached_at: Optional[str] = Field(
        None, description="ISO timestamp when content was cached"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cache_hit": True,
                "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                "status": "completed",
                "video_url": "https://cdn.vividly.edu/videos/a7f3e2b1.mp4",
                "audio_url": "https://cdn.vividly.edu/audio/a7f3e2b1.mp3",
                "script_url": "https://storage.googleapis.com/vividly-scripts-dev/a7f3e2b1.json",
                "thumbnail_url": "https://cdn.vividly.edu/thumbnails/a7f3e2b1.jpg",
                "duration_seconds": 180,
                "generated_at": "2025-10-25T10:00:00Z",
                "cached_at": "2025-10-25T10:05:00Z",
            }
        }


class CacheStoreRequest(BaseModel):
    """Request to store content metadata in cache."""

    cache_key: str = Field(..., description="Cache key", min_length=64, max_length=64)
    video_url: str = Field(..., description="CDN URL for video")
    audio_url: Optional[str] = Field(None, description="CDN URL for audio")
    script_url: Optional[str] = Field(None, description="GCS URL for script JSON")
    thumbnail_url: Optional[str] = Field(None, description="CDN URL for thumbnail")
    duration_seconds: int = Field(..., description="Video duration in seconds", gt=0)
    topic_id: str = Field(..., description="Topic ID", min_length=1)
    interest_id: str = Field(..., description="Interest ID", min_length=1)
    generated_at: str = Field(
        ..., description="ISO timestamp when content was generated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                "video_url": "https://cdn.vividly.edu/videos/a7f3e2b1.mp4",
                "audio_url": "https://cdn.vividly.edu/audio/a7f3e2b1.mp3",
                "script_url": "https://storage.googleapis.com/vividly-scripts-dev/a7f3e2b1.json",
                "thumbnail_url": "https://cdn.vividly.edu/thumbnails/a7f3e2b1.jpg",
                "duration_seconds": 180,
                "topic_id": "topic_phys_mech_newton_3",
                "interest_id": "int_basketball",
                "generated_at": "2025-10-25T10:00:00Z",
            }
        }


class CacheStoreResponse(BaseModel):
    """Response from cache storage."""

    success: bool = Field(..., description="True if storage succeeded")
    cache_key: str = Field(..., description="Cache key")
    message: str = Field(..., description="Success/error message")
    redis_stored: bool = Field(..., description="True if stored in Redis hot cache")
    gcs_stored: bool = Field(..., description="True if stored in GCS cold cache")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                "message": "Content cached successfully",
                "redis_stored": True,
                "gcs_stored": True,
            }
        }


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""

    cache_hits: int = Field(..., description="Total cache hits")
    cache_misses: int = Field(..., description="Total cache misses")
    hit_rate: float = Field(..., description="Cache hit rate (0.0-1.0)")
    redis_hits: int = Field(..., description="Redis hot cache hits")
    gcs_hits: int = Field(..., description="GCS cold cache hits")
    total_requests: int = Field(..., description="Total requests processed")

    class Config:
        json_schema_extra = {
            "example": {
                "cache_hits": 150,
                "cache_misses": 50,
                "hit_rate": 0.75,
                "redis_hits": 120,
                "gcs_hits": 30,
                "total_requests": 200,
            }
        }
