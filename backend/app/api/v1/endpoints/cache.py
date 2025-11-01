"""
Cache API Endpoints (Story 3.1.1)

Internal endpoints for cache checking and storage.
These endpoints are used by the content generation pipeline, not by end users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from app.core.database import get_db
from app.schemas.cache import (
    CacheCheckRequest,
    CacheCheckResponse,
    CacheStoreRequest,
    CacheStoreResponse,
    CacheStatsResponse,
)
from app.services.cache_service import CacheService

# from app.core.security import require_service_token  # TODO: Implement service-to-service auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


def get_cache_service() -> CacheService:
    """
    Dependency to get cache service instance.

    For production: Inject Redis and GCS clients
    For testing: Can inject mocks
    """
    # TODO: In production, initialize with actual Redis and GCS clients
    # from google.cloud import storage
    # gcs_client = storage.Client()
    return CacheService(gcs_client=None)


@router.post(
    "/check",
    response_model=CacheCheckResponse,
    summary="Check if content exists in cache",
    description="""
    Check if generated content exists in cache (Redis hot cache → GCS cold cache).

    This is an internal endpoint used by the content generation pipeline to avoid
    regenerating content that already exists.

    **Performance:**
    - Redis hot cache: <100ms p95
    - GCS cold cache fallback: <500ms p95

    **Cache Strategy:**
    1. Check Redis hot cache (TTL 1 hour)
    2. If miss, check GCS cold cache (permanent)
    3. If GCS hit, warm up Redis for next time
    """,
    status_code=status.HTTP_200_OK,
)
async def check_cache(
    request: CacheCheckRequest,
    cache_service: CacheService = Depends(get_cache_service),
    # service_token: str = Depends(require_service_token)  # Uncomment for service-to-service auth
):
    """
    Check if content exists in cache.

    Args:
        request: Cache check request with topic_id, interest, style
        cache_service: Cache service dependency

    Returns:
        CacheCheckResponse with cache_hit flag and metadata if found
    """
    try:
        # Check cache (Redis → GCS)
        cache_hit, metadata = await cache_service.check_content_cache(
            topic_id=request.topic_id, interest=request.interest, style=request.style
        )

        # Build response
        if cache_hit and metadata:
            return CacheCheckResponse(
                cache_hit=True,
                cache_key=metadata.get("cache_key"),
                status=metadata.get("status", "completed"),
                video_url=metadata.get("video_url"),
                audio_url=metadata.get("audio_url"),
                script_url=metadata.get("script_url"),
                thumbnail_url=metadata.get("thumbnail_url"),
                duration_seconds=metadata.get("duration_seconds"),
                generated_at=metadata.get("generated_at"),
                cached_at=metadata.get("cached_at"),
            )
        else:
            # Cache miss
            cache_key = cache_service.generate_cache_key(
                topic_id=request.topic_id,
                interest=request.interest,
                style=request.style,
            )
            return CacheCheckResponse(cache_hit=False, cache_key=cache_key, status=None)

    except Exception as e:
        logger.error(f"Cache check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache check failed",
        )


@router.post(
    "/store",
    response_model=CacheStoreResponse,
    summary="Store content metadata in cache",
    description="""
    Store generated content metadata in both Redis and GCS caches.

    This is an internal endpoint used by the content generation pipeline after
    successfully generating new content.

    **Storage:**
    - Redis: 1 hour TTL (hot cache)
    - GCS: Permanent (cold cache, audit trail)
    """,
    status_code=status.HTTP_201_CREATED,
)
async def store_cache(
    request: CacheStoreRequest,
    cache_service: CacheService = Depends(get_cache_service),
    # service_token: str = Depends(require_service_token)  # Uncomment for service-to-service auth
):
    """
    Store content metadata in cache.

    Args:
        request: Cache storage request with metadata
        cache_service: Cache service dependency

    Returns:
        CacheStoreResponse with success status
    """
    try:
        # Build metadata dict
        metadata = {
            "cache_key": request.cache_key,
            "video_url": request.video_url,
            "audio_url": request.audio_url,
            "script_url": request.script_url,
            "thumbnail_url": request.thumbnail_url,
            "duration_seconds": request.duration_seconds,
            "topic_id": request.topic_id,
            "interest_id": request.interest_id,
            "generated_at": request.generated_at,
            "status": "completed",
        }

        # Store in cache
        success = await cache_service.store_content_cache(
            cache_key=request.cache_key, metadata=metadata
        )

        # Check which caches succeeded
        redis_stored = cache_service.client is not None
        gcs_stored = cache_service.gcs is not None

        return CacheStoreResponse(
            success=success,
            cache_key=request.cache_key,
            message="Content cached successfully"
            if success
            else "Cache storage failed",
            redis_stored=redis_stored and success,
            gcs_stored=gcs_stored and success,
        )

    except Exception as e:
        logger.error(f"Cache storage failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache storage failed",
        )


@router.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="""
    Get cache performance statistics.

    Useful for monitoring cache hit rates and optimizing cache strategy.
    """,
    status_code=status.HTTP_200_OK,
)
async def get_cache_stats(
    cache_service: CacheService = Depends(get_cache_service),
    # admin_user: dict = Depends(require_admin)  # Uncomment for admin-only access
):
    """
    Get cache statistics.

    Args:
        cache_service: Cache service dependency

    Returns:
        CacheStatsResponse with cache statistics
    """
    try:
        stats = cache_service.get_cache_stats()
        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics",
        )


@router.delete(
    "/{cache_key}",
    summary="Invalidate cached content",
    description="""
    Invalidate content in Redis cache (hot cache).

    GCS cache (cold cache) is preserved by default for audit purposes.
    """,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def invalidate_cache(
    cache_key: str,
    invalidate_gcs: bool = False,
    cache_service: CacheService = Depends(get_cache_service),
    # admin_user: dict = Depends(require_admin)  # Uncomment for admin-only access
):
    """
    Invalidate cached content.

    Args:
        cache_key: Cache key to invalidate
        invalidate_gcs: Also invalidate GCS cold cache (default: False)
        cache_service: Cache service dependency

    Returns:
        204 No Content on success
    """
    try:
        success = await cache_service.invalidate_content_cache(
            cache_key=cache_key, invalidate_redis=True, invalidate_gcs=invalidate_gcs
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cache invalidation failed",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache invalidation failed",
        )
