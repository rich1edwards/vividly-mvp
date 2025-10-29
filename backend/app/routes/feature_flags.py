"""
Feature Flag API Routes

REST API for managing feature flags.

Endpoints:
- GET /api/v1/feature-flags - List all flags
- POST /api/v1/feature-flags - Create new flag (admin only)
- GET /api/v1/feature-flags/{key} - Get flag details
- PUT /api/v1/feature-flags/{key} - Update flag (admin only)
- DELETE /api/v1/feature-flags/{key} - Delete flag (admin only)
- POST /api/v1/feature-flags/{key}/overrides - Set user override (admin only)
- DELETE /api/v1/feature-flags/{key}/overrides/{user_id} - Remove override (admin only)
- GET /api/v1/feature-flags/audit - Get audit log (admin only)
- GET /api/v1/feature-flags/check/{key} - Check if flag is enabled (authenticated)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..middleware.auth import get_current_active_user, require_admin
from ..services.feature_flag_service import FeatureFlagService
from ..services.cache_service import CacheService
from ..models.feature_flag import FeatureFlag, FeatureFlagOverride, FeatureFlagAudit

router = APIRouter(prefix="/api/v1/feature-flags", tags=["Feature Flags"])


# Request/Response Models

class CreateFeatureFlagRequest(BaseModel):
    """Request to create a new feature flag."""

    key: str = Field(..., min_length=1, max_length=255, description="Unique flag key")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: Optional[str] = Field(None, description="Flag description")
    enabled: bool = Field(False, description="Initial enabled state")
    rollout_percentage: int = Field(0, ge=0, le=100, description="Initial rollout percentage (0-100)")
    organization_id: Optional[str] = Field(None, description="Organization ID (null for global)")

    @validator("key")
    def validate_key(cls, v):
        """Validate flag key format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Flag key must contain only alphanumeric characters, underscores, and hyphens")
        return v


class UpdateFeatureFlagRequest(BaseModel):
    """Request to update a feature flag."""

    enabled: Optional[bool] = Field(None, description="New enabled state")
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100, description="New rollout percentage")


class SetOverrideRequest(BaseModel):
    """Request to set user override."""

    user_id: str = Field(..., description="User ID")
    enabled: bool = Field(..., description="Override state")
    reason: Optional[str] = Field(None, description="Reason for override")


class FeatureFlagResponse(BaseModel):
    """Feature flag response."""

    id: str
    key: str
    name: str
    description: Optional[str]
    enabled: bool
    rollout_percentage: int
    organization_id: Optional[str]
    created_at: str
    updated_at: str


class FlagCheckResponse(BaseModel):
    """Response for flag check."""

    key: str
    enabled: bool
    reason: Optional[str] = None  # 'override', 'rollout', 'global', etc.


# Dependencies


def get_db() -> Session:
    """Get database session (placeholder - implement based on your DB setup)."""
    # This should be replaced with your actual database dependency
    raise NotImplementedError("Database dependency not configured")


def get_feature_flag_service(db: Session = Depends(get_db)) -> FeatureFlagService:
    """Get feature flag service instance."""
    cache = CacheService()  # Use your cache service instance
    return FeatureFlagService(db, cache)


# Routes


@router.get("", response_model=List[FeatureFlagResponse])
async def list_flags(
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    List all feature flags.

    Admin only. Returns all flags (org-specific and global).
    """
    query = service.db.query(FeatureFlag)

    if organization_id:
        query = query.filter(FeatureFlag.organization_id == organization_id)

    flags = query.all()
    return [flag.to_dict() for flag in flags]


@router.post("", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_flag(
    request: CreateFeatureFlagRequest,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Create a new feature flag.

    Admin only.
    """
    try:
        flag = service.create_flag(
            key=request.key,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            rollout_percentage=request.rollout_percentage,
            organization_id=request.organization_id,
            created_by=current_user.id,
        )
        return flag.to_dict()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_flag(
    key: str,
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Get feature flag details.

    Admin only.
    """
    flag = service._get_flag(key, organization_id)
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

    return flag.to_dict()


@router.put("/{key}", response_model=FeatureFlagResponse)
async def update_flag(
    key: str,
    request: UpdateFeatureFlagRequest,
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Update a feature flag.

    Admin only. Can update enabled state and rollout percentage.
    """
    flag = service.update_flag(
        flag_key=key,
        enabled=request.enabled,
        rollout_percentage=request.rollout_percentage,
        organization_id=organization_id,
    )

    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")

    return flag.to_dict()


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flag(
    key: str,
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Delete a feature flag.

    Admin only.
    """
    success = service.delete_flag(key, organization_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag not found")


@router.post("/{key}/overrides", status_code=status.HTTP_201_CREATED)
async def set_override(
    key: str,
    request: SetOverrideRequest,
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Set user-specific override for a feature flag.

    Admin only. Useful for beta testing or debugging.
    """
    try:
        override = service.set_user_override(
            flag_key=key,
            user_id=request.user_id,
            enabled=request.enabled,
            reason=request.reason,
            created_by=current_user.id,
            organization_id=organization_id,
        )
        return override.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{key}/overrides/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_override(
    key: str,
    user_id: str,
    organization_id: Optional[str] = None,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Remove user-specific override.

    Admin only.
    """
    success = service.remove_user_override(key, user_id, organization_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found")


@router.get("/audit/log")
async def get_audit_log(
    flag_key: Optional[str] = None,
    limit: int = 100,
    current_user=Depends(require_admin),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Get audit log for feature flag changes.

    Admin only.
    """
    logs = service.get_audit_log(flag_key, limit)
    return [log.to_dict() for log in logs]


@router.get("/check/{key}", response_model=FlagCheckResponse)
async def check_flag(
    key: str,
    current_user=Depends(get_current_active_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Check if a feature flag is enabled for the current user.

    Authenticated users only. Returns true/false based on flag state,
    rollout percentage, and user-specific overrides.
    """
    enabled = service.is_enabled(
        flag_key=key,
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id) if current_user.organization_id else None,
    )

    return FlagCheckResponse(key=key, enabled=enabled)


@router.get("/all/check")
async def check_all_flags(
    current_user=Depends(get_current_active_user),
    service: FeatureFlagService = Depends(get_feature_flag_service),
):
    """
    Check all feature flags for the current user.

    Authenticated users only. Returns dictionary of flag_key -> enabled.
    """
    flags = service.get_all_flags(
        user_id=str(current_user.id),
        organization_id=str(current_user.organization_id) if current_user.organization_id else None,
    )

    return flags
