"""
Unit tests for cache service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import timedelta
import json

from app.services.cache_service import (
    CacheService,
    UserCache,
    ContentCache,
    SessionCache,
)


@pytest.mark.unit
class TestCacheServiceInitialization:
    """Test cache service initialization."""

    @patch('redis.from_url')
    def test_init_with_default_settings(self, mock_redis):
        """Test initialization with default settings."""
        service = CacheService()

        assert service.redis_url == "redis://localhost:6379/0"
        assert service.gcs is None
        assert service.stats["cache_hits"] == 0
        assert service.stats["cache_misses"] == 0
        mock_redis.assert_called_once()

    @patch('redis.from_url')
    def test_init_with_custom_redis_url(self, mock_redis):
        """Test initialization with custom Redis URL."""
        service = CacheService(redis_url="redis://custom:6380/1")

        assert service.redis_url == "redis://custom:6380/1"
        mock_redis.assert_called_with("redis://custom:6380/1", decode_responses=True)

    @patch('redis.from_url')
    def test_init_with_gcs_client(self, mock_redis):
        """Test initialization with GCS client."""
        mock_gcs = Mock()
        service = CacheService(gcs_client=mock_gcs)

        assert service.gcs == mock_gcs


@pytest.mark.unit
class TestGenerateCacheKey:
    """Test cache key generation."""

    @patch('redis.from_url')
    def test_generate_cache_key_deterministic(self, mock_redis):
        """Test cache key generation is deterministic."""
        service = CacheService()

        key1 = service.generate_cache_key("topic_1", "basketball", "standard")
        key2 = service.generate_cache_key("topic_1", "basketball", "standard")

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length

    @patch('redis.from_url')
    def test_generate_cache_key_normalization(self, mock_redis):
        """Test cache key normalization (case, whitespace)."""
        service = CacheService()

        key1 = service.generate_cache_key("Topic_1", " Basketball ", "Standard")
        key2 = service.generate_cache_key("topic_1", "basketball", "standard")

        assert key1 == key2

    @patch('redis.from_url')
    def test_generate_cache_key_different_inputs(self, mock_redis):
        """Test different inputs produce different keys."""
        service = CacheService()

        key1 = service.generate_cache_key("topic_1", "basketball", "standard")
        key2 = service.generate_cache_key("topic_2", "basketball", "standard")
        key3 = service.generate_cache_key("topic_1", "soccer", "standard")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


@pytest.mark.unit
class TestCheckContentCache:
    """Test content cache checking (two-tier)."""

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_check_content_cache_redis_hit(self, mock_redis):
        """Test cache hit from Redis (hot cache)."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        metadata = {"video_url": "http://test.com/video.mp4", "duration": 120}
        mock_client.get.return_value = json.dumps(metadata)

        service = CacheService()
        hit, data = await service.check_content_cache("topic_1", "basketball")

        assert hit is True
        assert data == metadata
        assert service.stats["cache_hits"] == 1
        assert service.stats["redis_hits"] == 1
        assert service.stats["gcs_hits"] == 0

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_check_content_cache_gcs_hit(self, mock_redis):
        """Test cache hit from GCS (cold cache)."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None  # Redis miss

        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True

        metadata = {"video_url": "http://test.com/video.mp4", "duration": 120}
        mock_blob.download_as_text.return_value = json.dumps(metadata)

        service = CacheService(gcs_client=mock_gcs)
        hit, data = await service.check_content_cache("topic_1", "basketball")

        assert hit is True
        assert data == metadata
        assert service.stats["cache_hits"] == 1
        assert service.stats["redis_hits"] == 0
        assert service.stats["gcs_hits"] == 1
        # Should have warmed up Redis
        mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_check_content_cache_miss(self, mock_redis):
        """Test cache miss (not in Redis or GCS)."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None

        service = CacheService()
        hit, data = await service.check_content_cache("topic_1", "basketball")

        assert hit is False
        assert data is None
        assert service.stats["cache_misses"] == 1


@pytest.mark.unit
class TestStoreContentCache:
    """Test storing content in cache."""

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_store_content_cache_success(self, mock_redis):
        """Test successful content storage."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        service = CacheService(gcs_client=mock_gcs)
        cache_key = service.generate_cache_key("topic_1", "basketball", "standard")
        metadata = {"video_url": "http://test.com/video.mp4"}

        result = await service.store_content_cache(cache_key, metadata)

        assert result is True
        mock_client.setex.assert_called_once()
        mock_blob.upload_from_string.assert_called_once()

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_store_content_cache_redis_only(self, mock_redis):
        """Test storage succeeds with Redis but no GCS."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        service = CacheService()  # No GCS client
        cache_key = "test_key"
        metadata = {"video_url": "http://test.com/video.mp4"}

        result = await service.store_content_cache(cache_key, metadata)

        # Should succeed even without GCS
        assert result is False  # GCS storage failed


@pytest.mark.unit
class TestInvalidateContentCache:
    """Test cache invalidation."""

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_invalidate_redis_only(self, mock_redis):
        """Test invalidating Redis cache only."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        service = CacheService()
        result = await service.invalidate_content_cache("test_key", invalidate_redis=True, invalidate_gcs=False)

        assert result is True
        mock_client.delete.assert_called_once_with("content:metadata:test_key")

    @pytest.mark.asyncio
    @patch('redis.from_url')
    async def test_invalidate_redis_and_gcs(self, mock_redis):
        """Test invalidating both Redis and GCS."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        mock_gcs = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True

        service = CacheService(gcs_client=mock_gcs)
        result = await service.invalidate_content_cache("test_key", invalidate_redis=True, invalidate_gcs=True)

        assert result is True
        mock_client.delete.assert_called_once()
        mock_blob.delete.assert_called_once()


@pytest.mark.unit
class TestCacheStats:
    """Test cache statistics."""

    @patch('redis.from_url')
    def test_get_cache_stats_with_hits(self, mock_redis):
        """Test cache stats calculation."""
        service = CacheService()
        service.stats = {
            "cache_hits": 80,
            "cache_misses": 20,
            "redis_hits": 70,
            "gcs_hits": 10,
        }

        stats = service.get_cache_stats()

        assert stats["cache_hits"] == 80
        assert stats["cache_misses"] == 20
        assert stats["hit_rate"] == 0.8  # 80/100
        assert stats["total_requests"] == 100

    @patch('redis.from_url')
    def test_get_cache_stats_empty(self, mock_redis):
        """Test cache stats with no requests."""
        service = CacheService()

        stats = service.get_cache_stats()

        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0

    @patch('redis.from_url')
    def test_reset_cache_stats(self, mock_redis):
        """Test resetting cache statistics."""
        service = CacheService()
        service.stats["cache_hits"] = 100

        service.reset_cache_stats()

        assert service.stats["cache_hits"] == 0
        assert service.stats["cache_misses"] == 0


@pytest.mark.unit
class TestGeneralCacheMethods:
    """Test general-purpose cache methods."""

    @patch('redis.from_url')
    def test_get_value(self, mock_redis):
        """Test getting value from cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = '{"key": "value"}'

        service = CacheService()
        result = service.get("test_key")

        assert result == {"key": "value"}
        mock_client.get.assert_called_once_with("test_key")

    @patch('redis.from_url')
    def test_get_value_not_found(self, mock_redis):
        """Test getting non-existent value."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.get.return_value = None

        service = CacheService()
        result = service.get("nonexistent")

        assert result is None

    @patch('redis.from_url')
    def test_set_value_with_ttl(self, mock_redis):
        """Test setting value with TTL."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        service = CacheService()
        result = service.set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        mock_client.setex.assert_called_once()

    @patch('redis.from_url')
    def test_set_value_without_ttl(self, mock_redis):
        """Test setting value without TTL."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.set.return_value = True

        service = CacheService()
        result = service.set("test_key", "value")

        assert result is True
        mock_client.set.assert_called_once()

    @patch('redis.from_url')
    def test_delete_key(self, mock_redis):
        """Test deleting key."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.delete.return_value = 1

        service = CacheService()
        result = service.delete("test_key")

        assert result is True
        mock_client.delete.assert_called_once_with("test_key")

    @patch('redis.from_url')
    def test_delete_pattern(self, mock_redis):
        """Test deleting keys by pattern."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.keys.return_value = ["key1", "key2", "key3"]
        mock_client.delete.return_value = 3

        service = CacheService()
        result = service.delete_pattern("user:*")

        assert result == 3
        mock_client.keys.assert_called_once_with("user:*")

    @patch('redis.from_url')
    def test_exists_key(self, mock_redis):
        """Test checking if key exists."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.exists.return_value = 1

        service = CacheService()
        result = service.exists("test_key")

        assert result is True

    @patch('redis.from_url')
    def test_increment_counter(self, mock_redis):
        """Test incrementing counter."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.incrby.return_value = 5

        service = CacheService()
        result = service.increment("counter", amount=2)

        assert result == 5
        mock_client.incrby.assert_called_once_with("counter", 2)

    @patch('redis.from_url')
    def test_get_ttl(self, mock_redis):
        """Test getting TTL for key."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.ttl.return_value = 300

        service = CacheService()
        result = service.ttl("test_key")

        assert result == 300


@pytest.mark.unit
class TestUserCache:
    """Test user cache helper."""

    @patch('redis.from_url')
    def test_get_user(self, mock_redis):
        """Test getting user from cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        user_data = {"id": "user_123", "name": "John"}
        mock_client.get.return_value = json.dumps(user_data)

        cache = CacheService()
        user_cache = UserCache(cache)
        result = user_cache.get_user("user_123")

        assert result == user_data

    @patch('redis.from_url')
    def test_set_user(self, mock_redis):
        """Test setting user in cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        cache = CacheService()
        user_cache = UserCache(cache)
        result = user_cache.set_user("user_123", {"name": "John"})

        assert result is True

    @patch('redis.from_url')
    def test_invalidate_user(self, mock_redis):
        """Test invalidating user cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.delete.return_value = 1

        cache = CacheService()
        user_cache = UserCache(cache)
        result = user_cache.invalidate_user("user_123")

        assert result is True


@pytest.mark.unit
class TestContentCacheHelper:
    """Test content cache helper."""

    @patch('redis.from_url')
    def test_get_content(self, mock_redis):
        """Test getting content from cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        content_data = {"id": "content_123", "title": "Video"}
        mock_client.get.return_value = json.dumps(content_data)

        cache = CacheService()
        content_cache = ContentCache(cache)
        result = content_cache.get_content("content_123")

        assert result == content_data

    @patch('redis.from_url')
    def test_set_content(self, mock_redis):
        """Test setting content in cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        cache = CacheService()
        content_cache = ContentCache(cache)
        result = content_cache.set_content("content_123", {"title": "Video"})

        assert result is True

    @patch('redis.from_url')
    def test_invalidate_student_content(self, mock_redis):
        """Test invalidating all content for a student."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.keys.return_value = ["key1", "key2"]
        mock_client.delete.return_value = 2

        cache = CacheService()
        content_cache = ContentCache(cache)
        result = content_cache.invalidate_student_content("student_123")

        assert result == 2


@pytest.mark.unit
class TestSessionCache:
    """Test session cache helper."""

    @patch('redis.from_url')
    def test_get_session(self, mock_redis):
        """Test getting session from cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        session_data = {"user_id": "user_123", "expires": "2024-12-31"}
        mock_client.get.return_value = json.dumps(session_data)

        cache = CacheService()
        session_cache = SessionCache(cache)
        result = session_cache.get_session("session_123")

        assert result == session_data

    @patch('redis.from_url')
    def test_set_session(self, mock_redis):
        """Test setting session in cache."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.setex.return_value = True

        cache = CacheService()
        session_cache = SessionCache(cache)
        result = session_cache.set_session("session_123", {"user_id": "user_123"})

        assert result is True

    @patch('redis.from_url')
    def test_delete_session(self, mock_redis):
        """Test deleting session."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.delete.return_value = 1

        cache = CacheService()
        session_cache = SessionCache(cache)
        result = session_cache.delete_session("session_123")

        assert result is True

    @patch('redis.from_url')
    def test_delete_user_sessions(self, mock_redis):
        """Test deleting all sessions for a user."""
        mock_client = Mock()
        mock_redis.return_value = mock_client
        mock_client.keys.return_value = ["session1", "session2"]
        mock_client.delete.return_value = 2

        cache = CacheService()
        session_cache = SessionCache(cache)
        result = session_cache.delete_user_sessions("user_123")

        assert result == 2
