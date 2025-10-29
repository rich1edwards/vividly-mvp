"""
Redis Caching Service

Provides caching functionality for API responses, session data,
and rate limiting using Redis.
"""

import os
import json
from typing import Optional, Any
from datetime import timedelta
import redis
from functools import wraps


class CacheService:
    """
    Redis-based caching service.

    Features:
    - Key-value caching with TTL
    - JSON serialization
    - Cache invalidation patterns
    - Session storage
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL (default: from environment)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.client = redis.from_url(self.redis_url, decode_responses=True)

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
