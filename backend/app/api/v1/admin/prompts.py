"""
Enterprise Prompt Management System - Admin API Endpoints
Following Andrew Ng's principle: "Build it right, think about the future"
Created: 2025-11-06

This module provides CRUD operations for:
- Prompt templates with versioning and A/B testing
- Guardrails configuration
- Performance analytics
- A/B test experiment management

All endpoints require SUPER_ADMIN role.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.prompt_template import (
    PromptTemplate,
    PromptExecution,
    PromptGuardrail,
    ABTestExperiment,
)
from app.services.prompt_management_service import PromptManagementService
from pydantic import BaseModel, Field, validator


router = APIRouter(prefix="/admin/prompts", tags=["admin-prompts"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class CreateTemplateRequest(BaseModel):
    """Request schema for creating a new prompt template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    template_text: str = Field(..., min_length=1)
    variables: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=False)
    ab_test_group: Optional[str] = Field(None, max_length=50)
    traffic_percentage: int = Field(default=0, ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "nlu_topic_extraction",
                "description": "Extract learning topics from user queries",
                "category": "nlu",
                "template_text": "Extract topics from: {{ user_query }}",
                "variables": ["user_query"],
                "is_active": False,
                "traffic_percentage": 0,
            }
        }


class UpdateTemplateRequest(BaseModel):
    """Request schema for updating a template (creates new version)."""

    description: Optional[str] = None
    template_text: Optional[str] = None
    variables: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "template_text": "Updated prompt: {{ user_query }}",
                "variables": ["user_query"],
            }
        }


class CreateGuardrailRequest(BaseModel):
    """Request schema for creating a guardrail."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    guardrail_type: str = Field(..., min_length=1, max_length=100)
    is_active: bool = Field(default=True)
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    action: str = Field(..., pattern="^(block|warn|log)$")
    config: Dict[str, Any] = Field(...)
    applies_to_templates: List[str] = Field(default_factory=list)
    applies_to_categories: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "pii_detection_ssn",
                "description": "Detect Social Security Numbers",
                "guardrail_type": "pii_detection",
                "is_active": True,
                "severity": "critical",
                "action": "block",
                "config": {
                    "patterns": ["\\d{3}-\\d{2}-\\d{4}"],
                    "case_sensitive": False,
                },
                "applies_to_categories": ["nlu", "script_generation"],
            }
        }


class UpdateGuardrailRequest(BaseModel):
    """Request schema for updating a guardrail."""

    description: Optional[str] = None
    is_active: Optional[bool] = None
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low)$")
    action: Optional[str] = Field(None, pattern="^(block|warn|log)$")
    config: Optional[Dict[str, Any]] = None
    applies_to_templates: Optional[List[str]] = None
    applies_to_categories: Optional[List[str]] = None


class CreateABTestRequest(BaseModel):
    """Request schema for creating an A/B test experiment."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_name: str = Field(..., min_length=1, max_length=255)
    control_template_id: uuid.UUID
    variant_template_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=5)
    traffic_allocation: Dict[str, int] = Field(...)
    primary_metric: str = Field(..., min_length=1, max_length=100)
    target_improvement_percentage: Optional[float] = None
    minimum_sample_size: int = Field(default=1000, ge=100)
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None

    @validator("traffic_allocation")
    def validate_traffic_allocation(cls, v):
        """Ensure traffic allocation sums to 100."""
        total = sum(v.values())
        if total != 100:
            raise ValueError(f"Traffic allocation must sum to 100, got {total}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "nlu_clarity_test_nov_2025",
                "description": "Test improved clarity in NLU prompts",
                "template_name": "nlu_topic_extraction",
                "control_template_id": "123e4567-e89b-12d3-a456-426614174000",
                "variant_template_ids": ["123e4567-e89b-12d3-a456-426614174001"],
                "traffic_allocation": {"control": 50, "variant_a": 50},
                "primary_metric": "success_rate",
                "minimum_sample_size": 1000,
            }
        }


class TemplatePerformanceResponse(BaseModel):
    """Response schema for template performance metrics."""

    template_id: str
    template_name: str
    version: int
    total_executions: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_response_time_ms: Optional[float]
    avg_token_count: Optional[int]
    avg_cost_usd: Optional[float]
    guardrail_violation_count: int
    last_executed_at: Optional[datetime]


# ============================================================================
# Template Management Endpoints
# ============================================================================


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Create a new prompt template.

    Requires SUPER_ADMIN role.
    """
    # Check if template name already exists
    existing = (
        db.query(PromptTemplate).filter(PromptTemplate.name == request.name).first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template with name '{request.name}' already exists. Use update endpoint to create new version.",
        )

    # Create template
    template = PromptTemplate(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        category=request.category,
        template_text=request.template_text,
        variables=request.variables,
        version=1,
        is_active=request.is_active,
        ab_test_group=request.ab_test_group,
        traffic_percentage=request.traffic_percentage,
        created_by=current_user.email,
        updated_by=current_user.email,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "status": "success",
        "message": "Template created successfully",
        "template": template.to_dict(),
    }


@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    ab_test_group: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    List all prompt templates with optional filtering.

    Query parameters:
    - category: Filter by category (e.g., 'nlu', 'clarification')
    - is_active: Filter by active status
    - ab_test_group: Filter by A/B test group
    - skip: Pagination offset
    - limit: Max results per page (1-100)

    Requires SUPER_ADMIN role.
    """
    query = db.query(PromptTemplate)

    # Apply filters
    if category:
        query = query.filter(PromptTemplate.category == category)
    if is_active is not None:
        query = query.filter(PromptTemplate.is_active == is_active)
    if ab_test_group:
        query = query.filter(PromptTemplate.ab_test_group == ab_test_group)

    # Get total count
    total = query.count()

    # Apply pagination and fetch
    templates = (
        query.order_by(desc(PromptTemplate.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "templates": [t.to_dict() for t in templates],
    }


@router.get("/templates/{template_id}")
async def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific template.

    Requires SUPER_ADMIN role.
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Include version history
    version_history = []
    if template.parent_version_id:
        parent = (
            db.query(PromptTemplate)
            .filter(PromptTemplate.id == template.parent_version_id)
            .first()
        )
        while parent:
            version_history.append(
                {
                    "version": parent.version,
                    "created_at": parent.created_at.isoformat()
                    if parent.created_at
                    else None,
                    "created_by": parent.created_by,
                }
            )
            parent = (
                db.query(PromptTemplate)
                .filter(PromptTemplate.id == parent.parent_version_id)
                .first()
            )

    return {
        "status": "success",
        "template": template.to_dict(),
        "version_history": version_history,
    }


@router.put("/templates/{template_id}")
async def update_template(
    template_id: uuid.UUID,
    request: UpdateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Update a template by creating a new version.

    This preserves immutability - the original template is not modified.
    Instead, a new version is created with the updated content.

    Requires SUPER_ADMIN role.
    """
    original_template = (
        db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    )

    if not original_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Create new version
    new_template = PromptTemplate(
        id=uuid.uuid4(),
        name=original_template.name,
        description=request.description
        if request.description is not None
        else original_template.description,
        category=original_template.category,
        template_text=request.template_text
        if request.template_text is not None
        else original_template.template_text,
        variables=request.variables
        if request.variables is not None
        else original_template.variables,
        version=original_template.version + 1,
        parent_version_id=template_id,
        is_active=False,  # New versions start inactive
        ab_test_group=original_template.ab_test_group,
        traffic_percentage=original_template.traffic_percentage,
        created_by=current_user.email,
        updated_by=current_user.email,
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    return {
        "status": "success",
        "message": f"Created version {new_template.version} of template '{original_template.name}'",
        "template": new_template.to_dict(),
    }


@router.post("/templates/{template_id}/activate")
async def activate_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Activate a template version.

    This will deactivate all other versions of the same template
    (with the same name and ab_test_group).

    Requires SUPER_ADMIN role.
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Deactivate other versions with same name and ab_test_group
    db.query(PromptTemplate).filter(
        and_(
            PromptTemplate.name == template.name,
            PromptTemplate.ab_test_group == template.ab_test_group,
            PromptTemplate.id != template_id,
        )
    ).update(
        {
            "is_active": False,
            "deactivated_at": func.now(),
            "deactivated_by": current_user.email,
        }
    )

    # Activate target template
    template.is_active = True
    template.updated_by = current_user.email
    template.updated_at = func.now()

    db.commit()

    return {
        "status": "success",
        "message": f"Activated template version {template.version}",
        "template_id": str(template.id),
    }


@router.post("/templates/{template_id}/deactivate")
async def deactivate_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Deactivate a template version.

    Requires SUPER_ADMIN role.
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    template.is_active = False
    template.deactivated_at = func.now()
    template.deactivated_by = current_user.email

    db.commit()

    return {
        "status": "success",
        "message": f"Deactivated template version {template.version}",
        "template_id": str(template.id),
    }


# ============================================================================
# Guardrail Management Endpoints
# ============================================================================


@router.post("/guardrails", status_code=status.HTTP_201_CREATED)
async def create_guardrail(
    request: CreateGuardrailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Create a new guardrail configuration.

    Requires SUPER_ADMIN role.
    """
    # Check if guardrail name already exists
    existing = (
        db.query(PromptGuardrail)
        .filter(PromptGuardrail.name == request.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Guardrail with name '{request.name}' already exists",
        )

    # Create guardrail
    guardrail = PromptGuardrail(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        guardrail_type=request.guardrail_type,
        is_active=request.is_active,
        severity=request.severity,
        action=request.action,
        config=request.config,
        applies_to_templates=request.applies_to_templates,
        applies_to_categories=request.applies_to_categories,
        created_by=current_user.email,
        updated_by=current_user.email,
    )

    db.add(guardrail)
    db.commit()
    db.refresh(guardrail)

    return {
        "status": "success",
        "message": "Guardrail created successfully",
        "guardrail": guardrail.to_dict(),
    }


@router.get("/guardrails")
async def list_guardrails(
    guardrail_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    List all guardrails with optional filtering.

    Query parameters:
    - guardrail_type: Filter by type (e.g., 'pii_detection')
    - is_active: Filter by active status
    - severity: Filter by severity level
    - skip: Pagination offset
    - limit: Max results per page (1-100)

    Requires SUPER_ADMIN role.
    """
    query = db.query(PromptGuardrail)

    # Apply filters
    if guardrail_type:
        query = query.filter(PromptGuardrail.guardrail_type == guardrail_type)
    if is_active is not None:
        query = query.filter(PromptGuardrail.is_active == is_active)
    if severity:
        query = query.filter(PromptGuardrail.severity == severity)

    # Get total count
    total = query.count()

    # Apply pagination and fetch
    guardrails = (
        query.order_by(desc(PromptGuardrail.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "guardrails": [g.to_dict() for g in guardrails],
    }


@router.get("/guardrails/{guardrail_id}")
async def get_guardrail(
    guardrail_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific guardrail.

    Requires SUPER_ADMIN role.
    """
    guardrail = (
        db.query(PromptGuardrail)
        .filter(PromptGuardrail.id == guardrail_id)
        .first()
    )

    if not guardrail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guardrail not found"
        )

    return {"status": "success", "guardrail": guardrail.to_dict()}


@router.put("/guardrails/{guardrail_id}")
async def update_guardrail(
    guardrail_id: uuid.UUID,
    request: UpdateGuardrailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Update a guardrail configuration.

    Unlike templates, guardrails are mutable - they don't use versioning.

    Requires SUPER_ADMIN role.
    """
    guardrail = (
        db.query(PromptGuardrail)
        .filter(PromptGuardrail.id == guardrail_id)
        .first()
    )

    if not guardrail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guardrail not found"
        )

    # Update fields if provided
    if request.description is not None:
        guardrail.description = request.description
    if request.is_active is not None:
        guardrail.is_active = request.is_active
    if request.severity is not None:
        guardrail.severity = request.severity
    if request.action is not None:
        guardrail.action = request.action
    if request.config is not None:
        guardrail.config = request.config
    if request.applies_to_templates is not None:
        guardrail.applies_to_templates = request.applies_to_templates
    if request.applies_to_categories is not None:
        guardrail.applies_to_categories = request.applies_to_categories

    guardrail.updated_by = current_user.email
    guardrail.updated_at = func.now()

    db.commit()
    db.refresh(guardrail)

    return {
        "status": "success",
        "message": "Guardrail updated successfully",
        "guardrail": guardrail.to_dict(),
    }


@router.post("/guardrails/{guardrail_id}/activate")
async def activate_guardrail(
    guardrail_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Activate a guardrail.

    Requires SUPER_ADMIN role.
    """
    guardrail = (
        db.query(PromptGuardrail)
        .filter(PromptGuardrail.id == guardrail_id)
        .first()
    )

    if not guardrail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guardrail not found"
        )

    guardrail.is_active = True
    guardrail.updated_by = current_user.email
    guardrail.updated_at = func.now()

    db.commit()

    return {
        "status": "success",
        "message": f"Activated guardrail '{guardrail.name}'",
        "guardrail_id": str(guardrail.id),
    }


@router.post("/guardrails/{guardrail_id}/deactivate")
async def deactivate_guardrail(
    guardrail_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Deactivate a guardrail.

    Requires SUPER_ADMIN role.
    """
    guardrail = (
        db.query(PromptGuardrail)
        .filter(PromptGuardrail.id == guardrail_id)
        .first()
    )

    if not guardrail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guardrail not found"
        )

    guardrail.is_active = False
    guardrail.updated_by = current_user.email
    guardrail.updated_at = func.now()

    db.commit()

    return {
        "status": "success",
        "message": f"Deactivated guardrail '{guardrail.name}'",
        "guardrail_id": str(guardrail.id),
    }


# ============================================================================
# Performance Analytics Endpoints
# ============================================================================


@router.get("/performance/overview")
async def get_performance_overview(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Get overall prompt system performance metrics.

    Query parameters:
    - days: Number of days to look back (1-90)

    Requires SUPER_ADMIN role.
    """
    # Calculate date threshold
    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    # Total executions in period
    total_executions = (
        db.query(func.count(PromptExecution.id))
        .filter(PromptExecution.executed_at >= start_date)
        .scalar()
    )

    # Success/failure breakdown
    success_count = (
        db.query(func.count(PromptExecution.id))
        .filter(
            and_(
                PromptExecution.executed_at >= start_date,
                PromptExecution.status == "success",
            )
        )
        .scalar()
    )

    failure_count = (
        db.query(func.count(PromptExecution.id))
        .filter(
            and_(
                PromptExecution.executed_at >= start_date,
                PromptExecution.status == "failure",
            )
        )
        .scalar()
    )

    # Average metrics
    avg_metrics = (
        db.query(
            func.avg(PromptExecution.execution_time_ms).label("avg_time"),
            func.avg(PromptExecution.token_count).label("avg_tokens"),
            func.avg(PromptExecution.cost_usd).label("avg_cost"),
        )
        .filter(PromptExecution.executed_at >= start_date)
        .first()
    )

    # Guardrail violations
    violation_count = (
        db.query(func.count(PromptExecution.id))
        .filter(
            and_(
                PromptExecution.executed_at >= start_date,
                PromptExecution.guardrail_violations != [],
            )
        )
        .scalar()
    )

    # Top templates by usage
    top_templates = (
        db.query(
            PromptExecution.template_name,
            func.count(PromptExecution.id).label("execution_count"),
        )
        .filter(PromptExecution.executed_at >= start_date)
        .group_by(PromptExecution.template_name)
        .order_by(desc("execution_count"))
        .limit(10)
        .all()
    )

    return {
        "status": "success",
        "period_days": days,
        "metrics": {
            "total_executions": total_executions or 0,
            "success_count": success_count or 0,
            "failure_count": failure_count or 0,
            "success_rate": (
                round((success_count / total_executions) * 100, 2)
                if total_executions > 0
                else 0
            ),
            "avg_response_time_ms": (
                round(avg_metrics.avg_time, 2) if avg_metrics.avg_time else None
            ),
            "avg_token_count": (
                round(avg_metrics.avg_tokens, 0) if avg_metrics.avg_tokens else None
            ),
            "avg_cost_usd": (
                round(avg_metrics.avg_cost, 6) if avg_metrics.avg_cost else None
            ),
            "guardrail_violation_count": violation_count or 0,
            "guardrail_violation_rate": (
                round((violation_count / total_executions) * 100, 2)
                if total_executions > 0
                else 0
            ),
        },
        "top_templates": [
            {"template_name": t[0], "execution_count": t[1]} for t in top_templates
        ],
    }


@router.get("/performance/templates/{template_id}")
async def get_template_performance(
    template_id: uuid.UUID,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Get detailed performance metrics for a specific template.

    Query parameters:
    - days: Number of days to look back (1-90)

    Requires SUPER_ADMIN role.
    """
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Calculate date threshold
    from datetime import datetime, timedelta

    start_date = datetime.utcnow() - timedelta(days=days)

    # Get executions in period
    executions = (
        db.query(PromptExecution)
        .filter(
            and_(
                PromptExecution.template_id == template_id,
                PromptExecution.executed_at >= start_date,
            )
        )
        .all()
    )

    total_executions = len(executions)
    success_count = len([e for e in executions if e.status == "success"])
    failure_count = len([e for e in executions if e.status == "failure"])

    # Calculate averages
    avg_response_time = (
        sum(e.execution_time_ms for e in executions if e.execution_time_ms)
        / len([e for e in executions if e.execution_time_ms])
        if any(e.execution_time_ms for e in executions)
        else None
    )

    avg_token_count = (
        sum(e.token_count for e in executions if e.token_count)
        / len([e for e in executions if e.token_count])
        if any(e.token_count for e in executions)
        else None
    )

    avg_cost = (
        sum(e.cost_usd for e in executions if e.cost_usd)
        / len([e for e in executions if e.cost_usd])
        if any(e.cost_usd for e in executions)
        else None
    )

    # Guardrail violations
    violation_count = len([e for e in executions if e.guardrail_violations])

    # Recent errors
    recent_errors = (
        db.query(PromptExecution)
        .filter(
            and_(
                PromptExecution.template_id == template_id,
                PromptExecution.status == "failure",
                PromptExecution.executed_at >= start_date,
            )
        )
        .order_by(desc(PromptExecution.executed_at))
        .limit(10)
        .all()
    )

    return {
        "status": "success",
        "template_id": str(template_id),
        "template_name": template.name,
        "version": template.version,
        "period_days": days,
        "metrics": {
            "total_executions": total_executions,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (
                round((success_count / total_executions) * 100, 2)
                if total_executions > 0
                else 0
            ),
            "avg_response_time_ms": round(avg_response_time, 2)
            if avg_response_time
            else None,
            "avg_token_count": round(avg_token_count, 0)
            if avg_token_count
            else None,
            "avg_cost_usd": round(avg_cost, 6) if avg_cost else None,
            "guardrail_violation_count": violation_count,
            "guardrail_violation_rate": (
                round((violation_count / total_executions) * 100, 2)
                if total_executions > 0
                else 0
            ),
        },
        "recent_errors": [
            {
                "execution_id": str(e.id),
                "error_message": e.error_message,
                "error_type": e.error_type,
                "executed_at": e.executed_at.isoformat() if e.executed_at else None,
            }
            for e in recent_errors
        ],
    }


# ============================================================================
# A/B Test Management Endpoints
# ============================================================================


@router.post("/ab-tests", status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    request: CreateABTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Create a new A/B test experiment.

    Requires SUPER_ADMIN role.
    """
    # Check if experiment name already exists
    existing = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.name == request.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A/B test with name '{request.name}' already exists",
        )

    # Verify control template exists
    control_template = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.id == request.control_template_id)
        .first()
    )
    if not control_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control template {request.control_template_id} not found",
        )

    # Verify variant templates exist
    for variant_id in request.variant_template_ids:
        variant = db.query(PromptTemplate).filter(PromptTemplate.id == variant_id).first()
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant template {variant_id} not found",
            )

    # Create experiment
    experiment = ABTestExperiment(
        id=uuid.uuid4(),
        name=request.name,
        description=request.description,
        template_name=request.template_name,
        status="draft",
        control_template_id=request.control_template_id,
        variant_template_ids=request.variant_template_ids,
        traffic_allocation=request.traffic_allocation,
        primary_metric=request.primary_metric,
        target_improvement_percentage=request.target_improvement_percentage,
        minimum_sample_size=request.minimum_sample_size,
        scheduled_start_date=request.scheduled_start_date,
        scheduled_end_date=request.scheduled_end_date,
        created_by=current_user.email,
        updated_by=current_user.email,
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {
        "status": "success",
        "message": "A/B test experiment created successfully",
        "experiment": experiment.to_dict(),
    }


@router.get("/ab-tests")
async def list_ab_tests(
    status_filter: Optional[str] = Query(None, alias="status"),
    template_name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    List all A/B test experiments with optional filtering.

    Query parameters:
    - status: Filter by experiment status
    - template_name: Filter by template name
    - skip: Pagination offset
    - limit: Max results per page (1-100)

    Requires SUPER_ADMIN role.
    """
    query = db.query(ABTestExperiment)

    # Apply filters
    if status_filter:
        query = query.filter(ABTestExperiment.status == status_filter)
    if template_name:
        query = query.filter(ABTestExperiment.template_name == template_name)

    # Get total count
    total = query.count()

    # Apply pagination and fetch
    experiments = (
        query.order_by(desc(ABTestExperiment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "experiments": [e.to_dict() for e in experiments],
    }


@router.get("/ab-tests/{experiment_id}")
async def get_ab_test(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific A/B test experiment.

    Requires SUPER_ADMIN role.
    """
    experiment = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.id == experiment_id)
        .first()
    )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="A/B test experiment not found"
        )

    return {"status": "success", "experiment": experiment.to_dict()}


@router.post("/ab-tests/{experiment_id}/start")
async def start_ab_test(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Start an A/B test experiment.

    This will activate all template variants according to traffic allocation.

    Requires SUPER_ADMIN role.
    """
    experiment = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.id == experiment_id)
        .first()
    )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="A/B test experiment not found"
        )

    if experiment.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is already active",
        )

    # Update experiment status
    experiment.status = "active"
    experiment.actual_start_date = func.now()
    experiment.updated_by = current_user.email
    experiment.updated_at = func.now()

    db.commit()

    return {
        "status": "success",
        "message": f"Started A/B test experiment '{experiment.name}'",
        "experiment_id": str(experiment.id),
    }


@router.post("/ab-tests/{experiment_id}/stop")
async def stop_ab_test(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
) -> Dict[str, Any]:
    """
    Stop an A/B test experiment.

    Requires SUPER_ADMIN role.
    """
    experiment = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.id == experiment_id)
        .first()
    )

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="A/B test experiment not found"
        )

    if experiment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is not active",
        )

    # Update experiment status
    experiment.status = "completed"
    experiment.actual_end_date = func.now()
    experiment.updated_by = current_user.email
    experiment.updated_at = func.now()

    db.commit()

    return {
        "status": "success",
        "message": f"Stopped A/B test experiment '{experiment.name}'",
        "experiment_id": str(experiment.id),
    }
