"""
Cache Service for Content Metadata

Provides two-tier caching (Redis hot cache + GCS cold cache) for content metadata,
along with API response caching, session data, and rate limiting using Redis.

Sprint 3.1.1: Cache Key Generation & Lookup
- SHA256-based deterministic cache keys
- Redis hot cache (TTL 1 hour, <100ms p95)
- GCS cold cache fallback (permanent storage)
- Cache statistics tracking
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any, Dict, Tuple
from datetime import timedelta, datetime
import redis
from functools import wraps

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service.

    Features:
    - Key-value caching with TTL
    - JSON serialization
    - Cache invalidation patterns
    - Session storage
    """

    def __init__(self, redis_url: Optional[str] = None, gcs_client=None):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (default: from environment)
            gcs_client: Google Cloud Storage client for cold cache (optional)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        self.gcs = gcs_client

        # Cache statistics (Story 3.1.1 requirement)
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "redis_hits": 0,
            "gcs_hits": 0,
        }

    # ========================================================================
    # Story 3.1.1: Cache Key Generation & Two-Tier Lookup
    # ========================================================================

    def generate_cache_key(
        self,
        topic_id: str,
        interest: str,
        style: str = "standard"
    ) -> str:
        """
        Generate deterministic cache key from content parameters.

        Uses SHA256 hash of: topic_id|interest|style
        This ensures the same inputs always produce the same cache key.

        Args:
            topic_id: Canonical topic ID (e.g., "topic_phys_mech_newton_3")
            interest: Student interest (e.g., "basketball")
            style: Content style (default: "standard")

        Returns:
            Cache key as hex string (64 characters)

        Example:
            >>> cache.generate_cache_key("topic_newton_1", "basketball", "standard")
            "a7f3e2b1c9d8f6e4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0"
        """
        # Normalize inputs (lowercase, strip whitespace)
        topic_id = topic_id.strip().lower()
        interest = interest.strip().lower()
        style = style.strip().lower()

        # Build cache key string with pipe delimiter
        cache_input = f"{topic_id}|{interest}|{style}"

        # Generate SHA256 hash (deterministic)
        cache_key = hashlib.sha256(cache_input.encode('utf-8')).hexdigest()

        logger.debug(f"Generated cache key: {cache_key} for {cache_input}")

        return cache_key

    async def check_content_cache(
        self,
        topic_id: str,
        interest: str,
        style: str = "standard"
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if content exists in cache (Redis hot cache → GCS cold cache).

        Two-tier cache strategy:
        1. Check Redis hot cache (fast, <100ms p95)
        2. If miss, check GCS cold cache (slower, permanent storage)
        3. If GCS hit, warm up Redis for next time

        Args:
            topic_id: Canonical topic ID
            interest: Student interest
            style: Content style (default: "standard")

        Returns:
            Tuple of (cache_hit: bool, metadata: dict | None)
                cache_hit: True if found in either Redis or GCS
                metadata: Content metadata dict if found, None otherwise

        Example:
            >>> hit, metadata = await cache.check_content_cache("topic_newton_1", "basketball")
            >>> if hit:
            ...     print(f"Video URL: {metadata['video_url']}")
        """
        # Generate cache key
        cache_key = self.generate_cache_key(topic_id, interest, style)

        # 1. Check Redis hot cache (fast path <100ms)
        try:
            redis_data = await self._check_redis_content(cache_key)
            if redis_data:
                self.stats["cache_hits"] += 1
                self.stats["redis_hits"] += 1
                logger.info(f"Cache HIT (Redis): {cache_key}")
                return True, redis_data
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
            # Fall through to GCS check

        # 2. Check GCS cold cache (slow path, but permanent)
        if self.gcs:
            try:
                gcs_data = await self._check_gcs_content(cache_key)
                if gcs_data:
                    # Warm up Redis cache for next time
                    await self._store_redis_content(cache_key, gcs_data)

                    self.stats["cache_hits"] += 1
                    self.stats["gcs_hits"] += 1
                    logger.info(f"Cache HIT (GCS): {cache_key}")
                    return True, gcs_data
            except Exception as e:
                logger.error(f"GCS check failed: {e}")

        # 3. Cache miss
        self.stats["cache_misses"] += 1
        logger.info(f"Cache MISS: {cache_key}")
        return False, None

    async def _check_redis_content(self, cache_key: str) -> Optional[Dict]:
        """
        Check Redis for cached content metadata.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Metadata dict if found, None otherwise
        """
        try:
            # Get from Redis with namespace prefix
            data = self.client.get(f"content:metadata:{cache_key}")

            if data:
                # Parse JSON
                metadata = json.loads(data)
                return metadata

            return None

        except Exception as e:
            logger.error(f"Redis get failed for {cache_key}: {e}")
            return None

    async def _check_gcs_content(self, cache_key: str) -> Optional[Dict]:
        """
        Check GCS for cached content metadata.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Metadata dict if found, None otherwise
        """
        if not self.gcs:
            return None

        try:
            bucket_name = os.getenv("GCS_CACHE_BUCKET", "vividly-content-cache-dev")
            blob_path = f"metadata/{cache_key}.json"

            # Get bucket
            bucket = self.gcs.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            # Check if exists
            if not blob.exists():
                return None

            # Download and parse JSON
            data = blob.download_as_text()
            metadata = json.loads(data)

            return metadata

        except Exception as e:
            logger.error(f"GCS get failed for {cache_key}: {e}")
            return None

    async def _store_redis_content(self, cache_key: str, metadata: Dict) -> bool:
        """
        Store metadata in Redis with 1-hour TTL.

        Args:
            cache_key: Cache key
            metadata: Content metadata dict

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize to JSON
            data = json.dumps(metadata)

            # Store in Redis with 1 hour TTL (Story 3.1.1 requirement)
            self.client.setex(
                f"content:metadata:{cache_key}",
                timedelta(hours=1),
                data
            )

            logger.debug(f"Stored in Redis: {cache_key} (TTL: 1 hour)")
            return True

        except Exception as e:
            logger.error(f"Redis store failed for {cache_key}: {e}")
            return False

    async def store_content_cache(
        self,
        cache_key: str,
        metadata: Dict
    ) -> bool:
        """
        Store content metadata in both Redis and GCS.

        Args:
            cache_key: Cache key
            metadata: Content metadata including:
                - video_url: CDN URL for video
                - audio_url: CDN URL for audio
                - script_url: GCS URL for script JSON
                - thumbnail_url: CDN URL for thumbnail
                - duration_seconds: Video duration
                - topic_id: Topic ID
                - interest_id: Interest ID
                - generated_at: ISO timestamp

        Returns:
            True if successful, False otherwise
        """
        # Add timestamp if not present
        if "cached_at" not in metadata:
            metadata["cached_at"] = datetime.utcnow().isoformat()

        # Store in both caches
        redis_success = await self._store_redis_content(cache_key, metadata)
        gcs_success = await self._store_gcs_content(cache_key, metadata)

        if redis_success and gcs_success:
            logger.info(f"Cached content: {cache_key}")
            return True
        elif gcs_success:
            logger.warning(f"Cached to GCS only (Redis failed): {cache_key}")
            return True
        else:
            logger.error(f"Cache storage failed: {cache_key}")
            return False

    async def _store_gcs_content(self, cache_key: str, metadata: Dict) -> bool:
        """
        Store metadata in GCS (permanent cold cache).

        Args:
            cache_key: Cache key
            metadata: Content metadata dict

        Returns:
            True if successful, False otherwise
        """
        if not self.gcs:
            logger.warning("GCS client not configured, skipping cold cache storage")
            return False

        try:
            bucket_name = os.getenv("GCS_CACHE_BUCKET", "vividly-content-cache-dev")
            blob_path = f"metadata/{cache_key}.json"

            # Get bucket
            bucket = self.gcs.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            # Set metadata
            blob.metadata = {
                "content-type": "application/json",
                "cache-control": "public, max-age=3600"
            }

            # Upload JSON
            data = json.dumps(metadata, indent=2)
            blob.upload_from_string(
                data,
                content_type="application/json"
            )

            logger.debug(f"Stored in GCS: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"GCS store failed for {cache_key}: {e}")
            return False

    async def invalidate_content_cache(
        self,
        cache_key: str,
        invalidate_redis: bool = True,
        invalidate_gcs: bool = False
    ) -> bool:
        """
        Invalidate cached content.

        Typically only invalidates Redis (hot cache). GCS is preserved
        for audit and recovery purposes.

        Args:
            cache_key: Cache key to invalidate
            invalidate_redis: Invalidate Redis hot cache (default: True)
            invalidate_gcs: Invalidate GCS cold cache (default: False, for audit)

        Returns:
            True if successful
        """
        success = True

        # Invalidate Redis
        if invalidate_redis:
            try:
                self.client.delete(f"content:metadata:{cache_key}")
                logger.info(f"Invalidated Redis cache: {cache_key}")
            except Exception as e:
                logger.error(f"Redis invalidation failed: {e}")
                success = False

        # Invalidate GCS (rare - only for content removal)
        if invalidate_gcs and self.gcs:
            try:
                bucket_name = os.getenv("GCS_CACHE_BUCKET", "vividly-content-cache-dev")
                blob_path = f"metadata/{cache_key}.json"

                bucket = self.gcs.bucket(bucket_name)
                blob = bucket.blob(blob_path)

                if blob.exists():
                    blob.delete()
                    logger.info(f"Invalidated GCS cache: {cache_key}")
            except Exception as e:
                logger.error(f"GCS invalidation failed: {e}")
                success = False

        return success

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics (Story 3.1.1 requirement).

        Returns:
            Dict with cache stats:
                - cache_hits: Total cache hits
                - cache_misses: Total cache misses
                - hit_rate: Cache hit rate (0.0 - 1.0)
                - redis_hits: Redis hot cache hits
                - gcs_hits: GCS cold cache hits
                - total_requests: Total requests processed
        """
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]

        hit_rate = (
            self.stats["cache_hits"] / total_requests
            if total_requests > 0
            else 0.0
        )

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": round(hit_rate, 3),
            "redis_hits": self.stats["redis_hits"],
            "gcs_hits": self.stats["gcs_hits"],
            "total_requests": total_requests,
        }

    def reset_cache_stats(self):
        """Reset cache statistics (for testing)."""
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "redis_hits": 0,
            "gcs_hits": 0,
        }

    # ========================================================================
    # Original Cache Service Methods (General Purpose)
    # ========================================================================

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized if dict/list)
            ttl: Time-to-live in seconds (None = no expiration)

        Returns:
            True if successful
        """
        try:
            # Serialize value if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)

        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Pattern with wildcards (e.g., "user:123:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter key.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value or None on error
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            print(f"Cache increment error for key {key}: {e}")
            return None

    def ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Seconds remaining, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Cache TTL error for key {key}: {e}")
            return None


# ============================================================================
# Caching Decorators
# ============================================================================

def cached(
    ttl: int = 300,
    key_prefix: str = "cache",
    key_fn: Optional[callable] = None
):
    """
    Decorator to cache function results.

    Args:
        ttl: Cache TTL in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
        key_fn: Optional function to generate cache key from args

    Usage:
        @cached(ttl=600, key_prefix="user")
        def get_user(user_id: str):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache service from app state or create new
            cache = CacheService()

            # Generate cache key
            if key_fn:
                cache_key = f"{key_prefix}:{key_fn(*args, **kwargs)}"
            else:
                # Default: use function name and args
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# ============================================================================
# Common Caching Patterns
# ============================================================================

class UserCache:
    """Cache for user data."""

    def __init__(self, cache: CacheService):
        self.cache = cache
        self.ttl = 3600  # 1 hour

    def get_user(self, user_id: str) -> Optional[dict]:
        """Get user from cache."""
        return self.cache.get(f"user:{user_id}")

    def set_user(self, user_id: str, user_data: dict) -> bool:
        """Cache user data."""
        return self.cache.set(f"user:{user_id}", user_data, ttl=self.ttl)

    def invalidate_user(self, user_id: str) -> bool:
        """Invalidate user cache."""
        return self.cache.delete(f"user:{user_id}")


class ContentCache:
    """Cache for generated content metadata."""

    def __init__(self, cache: CacheService):
        self.cache = cache
        self.ttl = 7200  # 2 hours

    def get_content(self, content_id: str) -> Optional[dict]:
        """Get content metadata from cache."""
        return self.cache.get(f"content:{content_id}")

    def set_content(self, content_id: str, content_data: dict) -> bool:
        """Cache content metadata."""
        return self.cache.set(f"content:{content_id}", content_data, ttl=self.ttl)

    def invalidate_content(self, content_id: str) -> bool:
        """Invalidate content cache."""
        return self.cache.delete(f"content:{content_id}")

    def invalidate_student_content(self, student_id: str) -> int:
        """Invalidate all content for a student."""
        return self.cache.delete_pattern(f"content:student:{student_id}:*")


class SessionCache:
    """Cache for user sessions."""

    def __init__(self, cache: CacheService):
        self.cache = cache
        self.ttl = 86400  # 24 hours

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        return self.cache.get(f"session:{session_id}")

    def set_session(self, session_id: str, session_data: dict) -> bool:
        """Store session data."""
        return self.cache.set(f"session:{session_id}", session_data, ttl=self.ttl)

    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        return self.cache.delete(f"session:{session_id}")

    def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        return self.cache.delete_pattern(f"session:*:user:{user_id}")


# ============================================================================
# Example Usage
# ============================================================================

"""
# Initialize cache service
from app.services.cache_service import CacheService, UserCache

cache = CacheService()
user_cache = UserCache(cache)

# Cache user data
user_cache.set_user("user_123", {
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
})

# Get from cache
user_data = user_cache.get_user("user_123")


# Use caching decorator
@cached(ttl=600, key_prefix="api")
def get_student_progress(student_id: str):
    # Expensive database query
    return db.query(Progress).filter(Progress.student_id == student_id).all()


# Cache with custom key function
@cached(
    ttl=3600,
    key_prefix="content",
    key_fn=lambda student_id, topic_id: f"{student_id}:{topic_id}"
)
def get_content_for_topic(student_id: str, topic_id: str):
    return db.query(Content).filter(
        Content.student_id == student_id,
        Content.topic_id == topic_id
    ).all()
"""
