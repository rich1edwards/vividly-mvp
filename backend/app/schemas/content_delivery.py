"""
Content Delivery API Schemas (Story 3.2.1)

Pydantic models for signed URL generation and content delivery endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class SignedURLRequest(BaseModel):
    """Request for single signed URL."""

    asset_type: str = Field(..., description="Asset type: video, audio, script, thumbnail")
    quality: str = Field(default="1080p", description="Quality level for video (1080p, 720p, 480p)")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_type": "video",
                "quality": "1080p"
            }
        }


class SignedURLResponse(BaseModel):
    """Response with signed URL."""

    cache_key: str = Field(..., description="Content cache key")
    asset_type: str = Field(..., description="Asset type")
    quality: Optional[str] = Field(None, description="Quality level (for video)")
    url: str = Field(..., description="Signed GCS URL")
    expires_at: str = Field(..., description="ISO timestamp when URL expires")
    expires_in_seconds: int = Field(..., description="Seconds until URL expires")
    cdn_cache_status: str = Field(..., description="CDN cache status (HIT, MISS, BYPASS)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds (video/audio)")

    class Config:
        json_schema_extra = {
            "example": {
                "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                "asset_type": "video",
                "quality": "1080p",
                "url": "https://storage.googleapis.com/vividly-content-dev/videos/a7f3e2b1/1080p.mp4?signature=xyz&expires=1234567890",
                "expires_at": "2025-10-29T10:15:00Z",
                "expires_in_seconds": 900,
                "cdn_cache_status": "HIT",
                "file_size_bytes": 25600000,
                "duration_seconds": 180
            }
        }


class BatchURLRequestItem(BaseModel):
    """Single URL request in batch."""

    cache_key: str = Field(..., description="Content cache key", min_length=64, max_length=64)
    type: str = Field(..., description="Asset type: video, audio, script, thumbnail")
    quality: str = Field(default="1080p", description="Quality level for video")

    class Config:
        json_schema_extra = {
            "example": {
                "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                "type": "video",
                "quality": "720p"
            }
        }


class BatchURLRequest(BaseModel):
    """Request for multiple signed URLs."""

    requests: List[BatchURLRequestItem] = Field(..., description="List of URL requests", min_length=1, max_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "requests": [
                    {
                        "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                        "type": "video",
                        "quality": "720p"
                    },
                    {
                        "cache_key": "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0",
                        "type": "audio"
                    }
                ]
            }
        }


class BatchURLResponse(BaseModel):
    """Response with multiple signed URLs."""

    urls: List[SignedURLResponse] = Field(..., description="List of signed URLs")
    generated_at: str = Field(..., description="ISO timestamp when URLs were generated")
    expires_in_seconds: int = Field(..., description="Minimum expiration time across all URLs")

    class Config:
        json_schema_extra = {
            "example": {
                "urls": [
                    {
                        "cache_key": "a7f3e2b1...",
                        "asset_type": "video",
                        "quality": "720p",
                        "url": "https://storage.googleapis.com/...",
                        "expires_at": "2025-10-29T10:15:00Z",
                        "expires_in_seconds": 900,
                        "cdn_cache_status": "HIT",
                        "file_size_bytes": 15360000,
                        "duration_seconds": 180
                    },
                    {
                        "cache_key": "a7f3e2b1...",
                        "asset_type": "audio",
                        "quality": None,
                        "url": "https://storage.googleapis.com/...",
                        "expires_at": "2025-10-29T10:15:00Z",
                        "expires_in_seconds": 900,
                        "cdn_cache_status": "HIT",
                        "file_size_bytes": 5120000,
                        "duration_seconds": 180
                    }
                ],
                "generated_at": "2025-10-29T10:00:00Z",
                "expires_in_seconds": 900
            }
        }


class ContentAccessStats(BaseModel):
    """Content access statistics."""

    total_requests: int = Field(..., description="Total URL requests")
    video_requests: int = Field(..., description="Video URL requests")
    audio_requests: int = Field(..., description="Audio URL requests")
    script_requests: int = Field(..., description="Script URL requests")

    class Config:
        json_schema_extra = {
            "example": {
                "total_requests": 500,
                "video_requests": 300,
                "audio_requests": 150,
                "script_requests": 50
            }
        }
