"""
Unit tests for content delivery service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict

from app.services.content_delivery_service import ContentDeliveryService


@pytest.mark.unit
class TestContentDeliveryServiceInitialization:
    """Test service initialization."""

    def test_init_with_default_settings(self):
        """Test initialization with default settings."""
        service = ContentDeliveryService()

        assert service.gcs is None
        assert service.cdn_domain == "cdn.vividly.edu"
        assert service.content_bucket == "vividly-content-dev"
        assert service.default_ttl_minutes == 15
        assert service.access_stats["total_requests"] == 0

    def test_init_with_custom_client(self):
        """Test initialization with custom GCS client."""
        mock_gcs = Mock()
        service = ContentDeliveryService(gcs_client=mock_gcs)

        assert service.gcs == mock_gcs

    @patch.dict(
        "os.environ",
        {"CDN_DOMAIN": "custom-cdn.com", "GCS_CONTENT_BUCKET": "custom-bucket"},
    )
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        service = ContentDeliveryService()

        assert service.cdn_domain == "custom-cdn.com"
        assert service.content_bucket == "custom-bucket"


@pytest.mark.unit
class TestGenerateSignedURL:
    """Test signed URL generation."""

    @pytest.mark.asyncio
    async def test_generate_signed_url_video(self):
        """Test generating signed URL for video."""
        service = ContentDeliveryService()

        result = await service.generate_signed_url(
            cache_key="test_cache_key_123",
            asset_type="video",
            quality="1080p",
            ttl_minutes=15,
        )

        assert result["cache_key"] == "test_cache_key_123"
        assert result["asset_type"] == "video"
        assert result["quality"] == "1080p"
        assert "url" in result
        assert "expires_at" in result
        assert result["expires_in_seconds"] == 900  # 15 minutes
        assert service.access_stats["total_requests"] == 1
        assert service.access_stats["video_requests"] == 1

    @pytest.mark.asyncio
    async def test_generate_signed_url_audio(self):
        """Test generating signed URL for audio."""
        service = ContentDeliveryService()

        result = await service.generate_signed_url(
            cache_key="audio_key_456", asset_type="audio", ttl_minutes=10
        )

        assert result["asset_type"] == "audio"
        assert result["quality"] is None  # Audio doesn't have quality
        assert result["expires_in_seconds"] == 600  # 10 minutes
        assert service.access_stats["audio_requests"] == 1

    @pytest.mark.asyncio
    async def test_generate_signed_url_script(self):
        """Test generating signed URL for script."""
        service = ContentDeliveryService()

        result = await service.generate_signed_url(
            cache_key="script_789", asset_type="script"
        )

        assert result["asset_type"] == "script"
        assert service.access_stats["script_requests"] == 1

    @pytest.mark.asyncio
    async def test_generate_signed_url_thumbnail(self):
        """Test generating signed URL for thumbnail."""
        service = ContentDeliveryService()

        result = await service.generate_signed_url(
            cache_key="thumb_abc", asset_type="thumbnail"
        )

        assert result["asset_type"] == "thumbnail"

    @pytest.mark.asyncio
    async def test_generate_signed_url_invalid_type(self):
        """Test error on invalid asset type."""
        service = ContentDeliveryService()

        with pytest.raises(ValueError, match="Invalid asset_type"):
            await service.generate_signed_url(
                cache_key="test", asset_type="invalid_type"
            )

    @pytest.mark.asyncio
    async def test_generate_signed_url_custom_ttl(self):
        """Test signed URL with custom TTL."""
        service = ContentDeliveryService()

        result = await service.generate_signed_url(
            cache_key="test", asset_type="video", ttl_minutes=30
        )

        assert result["expires_in_seconds"] == 1800  # 30 minutes

    @pytest.mark.asyncio
    async def test_generate_signed_url_updates_stats(self):
        """Test that URL generation updates access stats."""
        service = ContentDeliveryService()

        await service.generate_signed_url(cache_key="test1", asset_type="video")
        await service.generate_signed_url(cache_key="test2", asset_type="video")
        await service.generate_signed_url(cache_key="test3", asset_type="audio")

        assert service.access_stats["total_requests"] == 3
        assert service.access_stats["video_requests"] == 2
        assert service.access_stats["audio_requests"] == 1


@pytest.mark.unit
class TestBatchURLGeneration:
    """Test batch URL generation."""

    @pytest.mark.asyncio
    async def test_generate_batch_urls_success(self):
        """Test generating multiple URLs in batch."""
        service = ContentDeliveryService()

        requests = [
            {"cache_key": "test1", "type": "video", "quality": "1080p"},
            {"cache_key": "test2", "type": "audio"},
            {"cache_key": "test3", "type": "script"},
        ]

        result = await service.generate_batch_urls(requests)

        assert len(result["urls"]) == 3
        assert "generated_at" in result
        assert result["expires_in_seconds"] == 900  # Min of all TTLs
        assert all("url" in url_result for url_result in result["urls"])

    @pytest.mark.asyncio
    async def test_generate_batch_urls_empty(self):
        """Test batch generation with empty list."""
        service = ContentDeliveryService()

        result = await service.generate_batch_urls([])

        assert result["urls"] == []
        assert result["expires_in_seconds"] == 0

    @pytest.mark.asyncio
    async def test_generate_batch_urls_with_errors(self):
        """Test batch generation handles errors gracefully."""
        service = ContentDeliveryService()

        requests = [
            {"cache_key": "test1", "type": "video", "quality": "1080p"},
            {"cache_key": "test2", "type": "invalid_type"},  # This will fail
            {"cache_key": "test3", "type": "audio"},
        ]

        result = await service.generate_batch_urls(requests)

        assert len(result["urls"]) == 3
        assert result["urls"][1]["url"] is None
        assert "error" in result["urls"][1]
        assert result["urls"][0]["url"] is not None  # First succeeded
        assert result["urls"][2]["url"] is not None  # Third succeeded

    @pytest.mark.asyncio
    async def test_generate_batch_urls_minimum_ttl(self):
        """Test that batch returns minimum TTL of all URLs."""
        service = ContentDeliveryService()

        # All URLs will have same TTL (default 15 min)
        requests = [
            {"cache_key": "test1", "type": "video"},
            {"cache_key": "test2", "type": "audio"},
        ]

        result = await service.generate_batch_urls(requests)

        assert result["expires_in_seconds"] == 900  # 15 minutes


@pytest.mark.unit
class TestBuildGCSPath:
    """Test GCS path building."""

    def test_build_gcs_path_video(self):
        """Test building GCS path for video."""
        service = ContentDeliveryService()

        path = service._build_gcs_path("test_key", "video", "1080p")

        assert path == "videos/test_key/1080p.mp4"

    def test_build_gcs_path_audio(self):
        """Test building GCS path for audio."""
        service = ContentDeliveryService()

        path = service._build_gcs_path("test_key", "audio", "1080p")

        assert path == "audio/test_key/audio.mp3"

    def test_build_gcs_path_script(self):
        """Test building GCS path for script."""
        service = ContentDeliveryService()

        path = service._build_gcs_path("test_key", "script", "")

        assert path == "scripts/test_key/script.json"

    def test_build_gcs_path_thumbnail(self):
        """Test building GCS path for thumbnail."""
        service = ContentDeliveryService()

        path = service._build_gcs_path("test_key", "thumbnail", "")

        assert path == "thumbnails/test_key/thumbnail.jpg"

    def test_build_gcs_path_invalid_type(self):
        """Test error on invalid asset type."""
        service = ContentDeliveryService()

        with pytest.raises(ValueError, match="Unknown asset_type"):
            service._build_gcs_path("test", "invalid", "")

    def test_build_gcs_path_video_qualities(self):
        """Test building paths for different video qualities."""
        service = ContentDeliveryService()

        path_1080p = service._build_gcs_path("key", "video", "1080p")
        path_720p = service._build_gcs_path("key", "video", "720p")
        path_480p = service._build_gcs_path("key", "video", "480p")

        assert "1080p.mp4" in path_1080p
        assert "720p.mp4" in path_720p
        assert "480p.mp4" in path_480p


@pytest.mark.unit
class TestGenerateGCSSignedURL:
    """Test GCS signed URL generation."""

    @pytest.mark.asyncio
    async def test_generate_gcs_signed_url_without_client(self):
        """Test URL generation without GCS client (mock mode)."""
        service = ContentDeliveryService()

        url = await service._generate_gcs_signed_url(
            bucket_name="test-bucket", blob_path="videos/test/1080p.mp4", ttl_minutes=15
        )

        assert url.startswith("https://storage.googleapis.com/")
        assert "test-bucket" in url
        assert "signature=mock" in url

    @pytest.mark.asyncio
    async def test_generate_gcs_signed_url_with_client(self):
        """Test URL generation with GCS client."""
        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.generate_signed_url.return_value = (
            "https://signed-url.com/test?signature=real"
        )

        service = ContentDeliveryService(gcs_client=mock_gcs)

        url = await service._generate_gcs_signed_url(
            bucket_name="test-bucket", blob_path="videos/test/1080p.mp4", ttl_minutes=15
        )

        assert url == "https://signed-url.com/test?signature=real"
        mock_blob.exists.assert_called_once()
        mock_blob.generate_signed_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_gcs_signed_url_blob_not_found(self):
        """Test error when blob doesn't exist."""
        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        service = ContentDeliveryService(gcs_client=mock_gcs)

        with pytest.raises(FileNotFoundError, match="Content not found"):
            await service._generate_gcs_signed_url(
                bucket_name="test-bucket", blob_path="videos/nonexistent/1080p.mp4"
            )


@pytest.mark.unit
class TestGetFileSize:
    """Test file size retrieval."""

    @pytest.mark.asyncio
    async def test_get_file_size_without_client(self):
        """Test file size retrieval without GCS client."""
        service = ContentDeliveryService()

        size = await service._get_file_size("bucket", "path/to/file.mp4")

        assert size is None

    @pytest.mark.asyncio
    async def test_get_file_size_with_client(self):
        """Test file size retrieval with GCS client."""
        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.size = 1024000

        service = ContentDeliveryService(gcs_client=mock_gcs)

        size = await service._get_file_size("bucket", "path/to/file.mp4")

        assert size == 1024000
        mock_blob.reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_size_blob_not_exists(self):
        """Test file size when blob doesn't exist."""
        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()

        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        service = ContentDeliveryService(gcs_client=mock_gcs)

        size = await service._get_file_size("bucket", "nonexistent.mp4")

        assert size is None


@pytest.mark.unit
class TestGetDuration:
    """Test duration retrieval."""

    @pytest.mark.asyncio
    async def test_get_duration_returns_none(self):
        """Test duration retrieval (not yet implemented)."""
        service = ContentDeliveryService()

        duration = await service._get_duration("cache_key", "video")

        # Currently returns None (TODO in code)
        assert duration is None


@pytest.mark.unit
class TestAccessStats:
    """Test access statistics tracking."""

    def test_get_access_stats(self):
        """Test retrieving access statistics."""
        service = ContentDeliveryService()
        service.access_stats = {
            "total_requests": 100,
            "video_requests": 60,
            "audio_requests": 30,
            "script_requests": 10,
        }

        stats = service.get_access_stats()

        assert stats["total_requests"] == 100
        assert stats["video_requests"] == 60
        assert stats["audio_requests"] == 30
        assert stats["script_requests"] == 10

    def test_get_access_stats_returns_copy(self):
        """Test that get_access_stats returns a copy, not reference."""
        service = ContentDeliveryService()
        service.access_stats["total_requests"] = 50

        stats = service.get_access_stats()
        stats["total_requests"] = 999  # Modify copy

        # Original should be unchanged
        assert service.access_stats["total_requests"] == 50

    def test_reset_access_stats(self):
        """Test resetting access statistics."""
        service = ContentDeliveryService()
        service.access_stats = {
            "total_requests": 100,
            "video_requests": 60,
            "audio_requests": 30,
            "script_requests": 10,
        }

        service.reset_access_stats()

        assert service.access_stats["total_requests"] == 0
        assert service.access_stats["video_requests"] == 0
        assert service.access_stats["audio_requests"] == 0
        assert service.access_stats["script_requests"] == 0

    @pytest.mark.asyncio
    async def test_access_stats_increment_correctly(self):
        """Test that stats increment correctly with multiple requests."""
        service = ContentDeliveryService()

        await service.generate_signed_url("key1", "video")
        await service.generate_signed_url("key2", "video")
        await service.generate_signed_url("key3", "audio")
        await service.generate_signed_url("key4", "script")
        await service.generate_signed_url("key5", "video")

        stats = service.get_access_stats()

        assert stats["total_requests"] == 5
        assert stats["video_requests"] == 3
        assert stats["audio_requests"] == 1
        assert stats["script_requests"] == 1
