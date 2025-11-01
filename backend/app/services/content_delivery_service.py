"""
Content Delivery Service (Story 3.2.1)

Generates signed URLs for secure content delivery via GCS/CDN.
Supports video, audio, script, and thumbnail assets with quality selection.
"""
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from google.cloud import storage

logger = logging.getLogger(__name__)


class ContentDeliveryService:
    """Service for generating signed URLs for content delivery."""

    def __init__(self, gcs_client=None):
        """
        Initialize content delivery service.

        Args:
            gcs_client: Google Cloud Storage client (optional for testing)
        """
        self.gcs = gcs_client
        self.cdn_domain = os.getenv("CDN_DOMAIN", "cdn.vividly.edu")
        self.content_bucket = os.getenv("GCS_CONTENT_BUCKET", "vividly-content-dev")
        self.default_ttl_minutes = 15  # Story 3.2.1 requirement

        # Track access for analytics
        self.access_stats = {
            "total_requests": 0,
            "video_requests": 0,
            "audio_requests": 0,
            "script_requests": 0,
        }

    async def generate_signed_url(
        self,
        cache_key: str,
        asset_type: str = "video",
        quality: str = "1080p",
        ttl_minutes: int = 15,
    ) -> Dict:
        """
        Generate signed URL for content asset.

        URLs expire after 15 minutes (default) for security.

        Args:
            cache_key: Content cache key (SHA256 hash)
            asset_type: Type of asset ("video", "audio", "script", "thumbnail")
            quality: Quality level for video (e.g., "1080p", "720p", "480p")
            ttl_minutes: URL expiration time in minutes (default: 15)

        Returns:
            Dict with signed URL and metadata:
                - cache_key: Content cache key
                - asset_type: Asset type
                - quality: Quality level (for video)
                - url: Signed GCS URL
                - expires_at: ISO timestamp when URL expires
                - expires_in_seconds: Seconds until expiration
                - cdn_cache_status: CDN cache status ("HIT", "MISS", "BYPASS")
                - file_size_bytes: File size (if available)
                - duration_seconds: Duration (for video/audio)

        Raises:
            ValueError: If asset_type is invalid
            FileNotFoundError: If content does not exist

        Example:
            >>> service = ContentDeliveryService()
            >>> result = await service.generate_signed_url(
            ...     cache_key="a7f3e2b1c9d8f6e4...",
            ...     asset_type="video",
            ...     quality="1080p"
            ... )
            >>> print(result["url"])
            https://storage.googleapis.com/vividly-content-dev/videos/a7f3e2b1/1080p.mp4?...
        """
        # Validate asset type
        valid_types = ["video", "audio", "script", "thumbnail"]
        if asset_type not in valid_types:
            raise ValueError(
                f"Invalid asset_type: {asset_type}. Must be one of {valid_types}"
            )

        # Update access stats
        self.access_stats["total_requests"] += 1
        self.access_stats[f"{asset_type}_requests"] = (
            self.access_stats.get(f"{asset_type}_requests", 0) + 1
        )

        # Build GCS path
        gcs_path = self._build_gcs_path(cache_key, asset_type, quality)

        # Generate signed URL
        signed_url = await self._generate_gcs_signed_url(
            bucket_name=self.content_bucket, blob_path=gcs_path, ttl_minutes=ttl_minutes
        )

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        expires_in_seconds = ttl_minutes * 60

        # Get file metadata (if available)
        file_size = await self._get_file_size(self.content_bucket, gcs_path)
        duration = await self._get_duration(cache_key, asset_type)

        return {
            "cache_key": cache_key,
            "asset_type": asset_type,
            "quality": quality if asset_type == "video" else None,
            "url": signed_url,
            "expires_at": expires_at.isoformat() + "Z",
            "expires_in_seconds": expires_in_seconds,
            "cdn_cache_status": "BYPASS",  # Will be "HIT" or "MISS" when CDN is enabled
            "file_size_bytes": file_size,
            "duration_seconds": duration,
        }

    async def generate_batch_urls(self, requests: List[Dict]) -> Dict:
        """
        Generate multiple signed URLs in batch.

        Useful for fetching all assets for a content piece in one request.

        Args:
            requests: List of URL requests, each containing:
                - cache_key: Content cache key
                - type: Asset type
                - quality: Quality level (optional, for video)

        Returns:
            Dict with:
                - urls: List of signed URL results
                - generated_at: ISO timestamp
                - expires_in_seconds: Seconds until all URLs expire (min of all TTLs)

        Example:
            >>> requests = [
            ...     {"cache_key": "abc123", "type": "video", "quality": "1080p"},
            ...     {"cache_key": "abc123", "type": "audio"},
            ...     {"cache_key": "abc123", "type": "script"}
            ... ]
            >>> result = await service.generate_batch_urls(requests)
            >>> print(len(result["urls"]))
            3
        """
        urls = []
        min_ttl = float("inf")

        for req in requests:
            try:
                url_result = await self.generate_signed_url(
                    cache_key=req["cache_key"],
                    asset_type=req["type"],
                    quality=req.get("quality", "1080p"),
                    ttl_minutes=self.default_ttl_minutes,
                )
                urls.append(url_result)

                # Track minimum TTL
                if url_result["expires_in_seconds"] < min_ttl:
                    min_ttl = url_result["expires_in_seconds"]

            except Exception as e:
                logger.error(f"Failed to generate URL for {req}: {e}")
                urls.append(
                    {
                        "cache_key": req["cache_key"],
                        "asset_type": req["type"],
                        "error": str(e),
                        "url": None,
                    }
                )

        return {
            "urls": urls,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "expires_in_seconds": int(min_ttl) if min_ttl != float("inf") else 0,
        }

    def _build_gcs_path(self, cache_key: str, asset_type: str, quality: str) -> str:
        """
        Build GCS blob path for asset.

        Path structure:
        - videos/cache_key/quality.mp4
        - audio/cache_key/audio.mp3
        - scripts/cache_key/script.json
        - thumbnails/cache_key/thumbnail.jpg

        Args:
            cache_key: Content cache key
            asset_type: Asset type
            quality: Quality level (for video)

        Returns:
            GCS blob path
        """
        if asset_type == "video":
            return f"videos/{cache_key}/{quality}.mp4"
        elif asset_type == "audio":
            return f"audio/{cache_key}/audio.mp3"
        elif asset_type == "script":
            return f"scripts/{cache_key}/script.json"
        elif asset_type == "thumbnail":
            return f"thumbnails/{cache_key}/thumbnail.jpg"
        else:
            raise ValueError(f"Unknown asset_type: {asset_type}")

    async def _generate_gcs_signed_url(
        self, bucket_name: str, blob_path: str, ttl_minutes: int = 15
    ) -> str:
        """
        Generate signed GCS URL with expiration.

        Args:
            bucket_name: GCS bucket name
            blob_path: Blob path within bucket
            ttl_minutes: URL expiration time in minutes

        Returns:
            Signed URL string

        Raises:
            FileNotFoundError: If blob does not exist
        """
        if not self.gcs:
            # For testing without GCS: return mock URL
            logger.warning("GCS client not configured, returning mock URL")
            return f"https://storage.googleapis.com/{bucket_name}/{blob_path}?signature=mock&expires=mock"

        try:
            bucket = self.gcs.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            # Check if blob exists
            if not blob.exists():
                raise FileNotFoundError(f"Content not found: {blob_path}")

            # Generate signed URL
            signed_url = blob.generate_signed_url(
                version="v4", expiration=timedelta(minutes=ttl_minutes), method="GET"
            )

            return signed_url

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_path}: {e}")
            raise

    async def _get_file_size(self, bucket_name: str, blob_path: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            bucket_name: GCS bucket name
            blob_path: Blob path

        Returns:
            File size in bytes, or None if unavailable
        """
        if not self.gcs:
            return None

        try:
            bucket = self.gcs.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            if blob.exists():
                blob.reload()
                return blob.size

            return None

        except Exception as e:
            logger.error(f"Failed to get file size for {blob_path}: {e}")
            return None

    async def _get_duration(self, cache_key: str, asset_type: str) -> Optional[int]:
        """
        Get asset duration from metadata.

        Args:
            cache_key: Content cache key
            asset_type: Asset type

        Returns:
            Duration in seconds, or None if not applicable
        """
        # TODO: In production, fetch from content metadata database
        # For now, return None (will be populated when metadata is available)
        return None

    def get_access_stats(self) -> Dict:
        """
        Get content delivery statistics.

        Returns:
            Dict with access stats:
                - total_requests: Total URL requests
                - video_requests: Video URL requests
                - audio_requests: Audio URL requests
                - script_requests: Script URL requests
        """
        return self.access_stats.copy()

    def reset_access_stats(self):
        """Reset access statistics (for testing)."""
        self.access_stats = {
            "total_requests": 0,
            "video_requests": 0,
            "audio_requests": 0,
            "script_requests": 0,
        }
