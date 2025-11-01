"""
Feature Flag Service

Service for checking and managing feature flags with support for:
- Global and organization-specific flags
- Percentage-based rollout (consistent hashing)
- User-specific overrides
- Caching for performance
"""

import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.feature_flag import FeatureFlag, FeatureFlagOverride, FeatureFlagAudit

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    Service for feature flag operations.

    Usage:
        service = FeatureFlagService(db)
        if service.is_enabled("video_generation_v2", user_id="user123"):
            # Show new feature
    """

    def __init__(self, db: Session, cache_service: Optional[Any] = None):
        """
        Initialize feature flag service.

        Args:
            db: Database session
            cache_service: Optional cache service for performance
        """
        self.db = db
        self.cache = cache_service
        self.cache_ttl = 300  # 5 minutes

    def is_enabled(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.

        Evaluation order:
        1. User-specific override (if exists)
        2. Organization-specific flag (if org_id provided)
        3. Global flag
        4. Percentage rollout (if enabled)

        Args:
            flag_key: Feature flag key (e.g., "video_generation_v2")
            user_id: Optional user ID for override check and rollout
            organization_id: Optional organization ID for org-specific flags

        Returns:
            True if flag is enabled, False otherwise
        """
        # Check cache first
        cache_key = f"feature_flag:{flag_key}:{user_id}:{organization_id}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # 1. Check for user-specific override
        if user_id:
            override = self._get_user_override(flag_key, user_id)
            if override is not None:
                self._cache_result(cache_key, override)
                return override

        # 2. Get flag (org-specific or global)
        flag = self._get_flag(flag_key, organization_id)

        if not flag:
            # Flag doesn't exist, default to disabled
            self._cache_result(cache_key, False)
            return False

        # 3. Check if flag is enabled
        if not flag.enabled:
            self._cache_result(cache_key, False)
            return False

        # 4. Check rollout percentage
        if flag.rollout_percentage == 100:
            # Fully rolled out
            self._cache_result(cache_key, True)
            return True
        elif flag.rollout_percentage == 0:
            # Not rolled out
            self._cache_result(cache_key, False)
            return False
        else:
            # Partial rollout - use consistent hashing
            if not user_id:
                # No user ID, can't determine rollout
                self._cache_result(cache_key, False)
                return False

            enabled = self._check_rollout(flag_key, user_id, flag.rollout_percentage)
            self._cache_result(cache_key, enabled)
            return enabled

    def get_all_flags(
        self,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Get all feature flags and their states for a user.

        Args:
            user_id: Optional user ID
            organization_id: Optional organization ID

        Returns:
            Dictionary mapping flag keys to enabled state
        """
        # Get all flags (org-specific and global)
        flags = (
            self.db.query(FeatureFlag)
            .filter(
                or_(
                    FeatureFlag.organization_id == organization_id,
                    FeatureFlag.organization_id.is_(None),
                )
            )
            .all()
        )

        result = {}
        for flag in flags:
            # Use is_enabled to properly evaluate overrides and rollout
            result[flag.key] = self.is_enabled(flag.key, user_id, organization_id)

        return result

    def create_flag(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        enabled: bool = False,
        rollout_percentage: int = 0,
        organization_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> FeatureFlag:
        """
        Create a new feature flag.

        Args:
            key: Unique flag key
            name: Display name
            description: Optional description
            enabled: Initial enabled state
            rollout_percentage: Initial rollout percentage (0-100)
            organization_id: Optional organization ID
            created_by: User ID of creator

        Returns:
            Created FeatureFlag
        """
        flag = FeatureFlag(
            key=key,
            name=name,
            description=description,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            organization_id=organization_id,
            created_by=created_by,
        )

        self.db.add(flag)
        self.db.commit()
        self.db.refresh(flag)

        # Clear cache
        self._clear_flag_cache(key, organization_id)

        logger.info(
            f"Created feature flag: {key} (enabled={enabled}, rollout={rollout_percentage}%)"
        )
        return flag

    def update_flag(
        self,
        flag_key: str,
        enabled: Optional[bool] = None,
        rollout_percentage: Optional[int] = None,
        organization_id: Optional[str] = None,
    ) -> Optional[FeatureFlag]:
        """
        Update a feature flag.

        Args:
            flag_key: Flag key to update
            enabled: New enabled state
            rollout_percentage: New rollout percentage
            organization_id: Organization ID for org-specific flag

        Returns:
            Updated FeatureFlag or None if not found
        """
        flag = self._get_flag(flag_key, organization_id)
        if not flag:
            logger.warning(f"Feature flag not found: {flag_key}")
            return None

        # Update fields
        if enabled is not None:
            flag.enabled = enabled
        if rollout_percentage is not None:
            if 0 <= rollout_percentage <= 100:
                flag.rollout_percentage = rollout_percentage
            else:
                raise ValueError("rollout_percentage must be between 0 and 100")

        flag.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(flag)

        # Clear cache
        self._clear_flag_cache(flag_key, organization_id)

        logger.info(
            f"Updated feature flag: {flag_key} (enabled={flag.enabled}, rollout={flag.rollout_percentage}%)"
        )
        return flag

    def delete_flag(self, flag_key: str, organization_id: Optional[str] = None) -> bool:
        """
        Delete a feature flag.

        Args:
            flag_key: Flag key to delete
            organization_id: Organization ID for org-specific flag

        Returns:
            True if deleted, False if not found
        """
        flag = self._get_flag(flag_key, organization_id)
        if not flag:
            return False

        self.db.delete(flag)
        self.db.commit()

        # Clear cache
        self._clear_flag_cache(flag_key, organization_id)

        logger.info(f"Deleted feature flag: {flag_key}")
        return True

    def set_user_override(
        self,
        flag_key: str,
        user_id: str,
        enabled: bool,
        reason: Optional[str] = None,
        created_by: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> FeatureFlagOverride:
        """
        Set user-specific feature flag override.

        Args:
            flag_key: Flag key
            user_id: User ID
            enabled: Override state
            reason: Optional reason for override
            created_by: User ID of admin creating override
            organization_id: Organization ID for org-specific flag

        Returns:
            Created or updated FeatureFlagOverride
        """
        flag = self._get_flag(flag_key, organization_id)
        if not flag:
            raise ValueError(f"Feature flag not found: {flag_key}")

        # Check if override exists
        override = (
            self.db.query(FeatureFlagOverride)
            .filter(
                and_(
                    FeatureFlagOverride.flag_id == flag.id,
                    FeatureFlagOverride.user_id == user_id,
                )
            )
            .first()
        )

        if override:
            # Update existing
            override.enabled = enabled
            override.reason = reason
        else:
            # Create new
            override = FeatureFlagOverride(
                flag_id=flag.id,
                user_id=user_id,
                enabled=enabled,
                reason=reason,
                created_by=created_by,
            )
            self.db.add(override)

        self.db.commit()
        self.db.refresh(override)

        # Clear cache for this user
        cache_key = f"feature_flag:{flag_key}:{user_id}:*"
        if self.cache:
            self.cache.delete_pattern(cache_key)

        logger.info(f"Set override for {flag_key}, user {user_id}: {enabled}")
        return override

    def remove_user_override(
        self, flag_key: str, user_id: str, organization_id: Optional[str] = None
    ) -> bool:
        """
        Remove user-specific feature flag override.

        Args:
            flag_key: Flag key
            user_id: User ID
            organization_id: Organization ID for org-specific flag

        Returns:
            True if removed, False if not found
        """
        flag = self._get_flag(flag_key, organization_id)
        if not flag:
            return False

        override = (
            self.db.query(FeatureFlagOverride)
            .filter(
                and_(
                    FeatureFlagOverride.flag_id == flag.id,
                    FeatureFlagOverride.user_id == user_id,
                )
            )
            .first()
        )

        if not override:
            return False

        self.db.delete(override)
        self.db.commit()

        # Clear cache
        cache_key = f"feature_flag:{flag_key}:{user_id}:*"
        if self.cache:
            self.cache.delete_pattern(cache_key)

        logger.info(f"Removed override for {flag_key}, user {user_id}")
        return True

    def get_audit_log(
        self,
        flag_key: Optional[str] = None,
        limit: int = 100,
    ) -> List[FeatureFlagAudit]:
        """
        Get audit log for feature flag changes.

        Args:
            flag_key: Optional flag key to filter by
            limit: Maximum number of records to return

        Returns:
            List of FeatureFlagAudit records
        """
        query = self.db.query(FeatureFlagAudit)

        if flag_key:
            flag = self._get_flag(flag_key, None)
            if flag:
                query = query.filter(FeatureFlagAudit.flag_id == flag.id)

        return query.order_by(FeatureFlagAudit.changed_at.desc()).limit(limit).all()

    # Private helper methods

    def _get_flag(
        self, flag_key: str, organization_id: Optional[str] = None
    ) -> Optional[FeatureFlag]:
        """Get feature flag, preferring org-specific over global."""
        # Try org-specific first
        if organization_id:
            flag = (
                self.db.query(FeatureFlag)
                .filter(
                    and_(
                        FeatureFlag.key == flag_key,
                        FeatureFlag.organization_id == organization_id,
                    )
                )
                .first()
            )
            if flag:
                return flag

        # Fall back to global
        return (
            self.db.query(FeatureFlag)
            .filter(
                and_(
                    FeatureFlag.key == flag_key,
                    FeatureFlag.organization_id.is_(None),
                )
            )
            .first()
        )

    def _get_user_override(self, flag_key: str, user_id: str) -> Optional[bool]:
        """Get user-specific override if exists."""
        # This requires joining with flags table
        override = (
            self.db.query(FeatureFlagOverride)
            .join(FeatureFlag)
            .filter(
                and_(
                    FeatureFlag.key == flag_key,
                    FeatureFlagOverride.user_id == user_id,
                )
            )
            .first()
        )

        return override.enabled if override else None

    def _check_rollout(
        self, flag_key: str, user_id: str, rollout_percentage: int
    ) -> bool:
        """
        Check if user is in rollout percentage using consistent hashing.

        This ensures the same user always gets the same result for a given flag.
        """
        # Create hash of flag_key + user_id
        hash_input = f"{flag_key}:{user_id}".encode("utf-8")
        hash_digest = hashlib.sha256(hash_input).hexdigest()

        # Convert first 8 chars of hash to int (0-4294967295)
        hash_int = int(hash_digest[:8], 16)

        # Map to 0-100 range
        bucket = hash_int % 100

        # User is in rollout if their bucket is less than rollout_percentage
        return bucket < rollout_percentage

    def _cache_result(self, cache_key: str, result: bool):
        """Cache flag evaluation result."""
        if self.cache:
            self.cache.set(cache_key, result, ttl=self.cache_ttl)

    def _clear_flag_cache(self, flag_key: str, organization_id: Optional[str] = None):
        """Clear all cache entries for a flag."""
        if self.cache:
            pattern = f"feature_flag:{flag_key}:*"
            self.cache.delete_pattern(pattern)
