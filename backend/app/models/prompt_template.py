"""
Enterprise Prompt Management System - SQLAlchemy Models
Following Andrew Ng's principle: "Build it right, think about the future"
Created: 2025-11-06
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    Text,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.core.database import Base
from app.core.database_types import GUID, JSON


class PromptTemplate(Base):
    """
    Prompt template with versioning and A/B testing support.

    This table stores prompt templates that can be dynamically loaded and rendered
    with Jinja2. Supports:
    - Versioning: Track changes over time with parent_version_id
    - A/B Testing: Multiple variants can be active simultaneously
    - Performance Metrics: Track execution stats for optimization
    """

    __tablename__ = "prompt_templates"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Template identity
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(
        String(100), index=True
    )  # 'nlu', 'clarification', 'script_generation'

    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(JSON, default=[])  # Array of required variable names

    # Versioning
    version = Column(Integer, nullable=False, default=1)
    parent_version_id = Column(
        GUID, ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True
    )
    is_active = Column(Boolean, default=False, index=True)

    # A/B Testing
    ab_test_group = Column(String(50))  # 'control', 'variant_a', 'variant_b'
    traffic_percentage = Column(Integer, default=0)
    ab_test_start_date = Column(TIMESTAMP)
    ab_test_end_date = Column(TIMESTAMP)

    # Performance metrics (auto-updated by triggers)
    total_executions = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Float)
    avg_token_count = Column(Integer)
    avg_cost_usd = Column(Float)

    # Metadata
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_by = Column(String(255))
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    deactivated_at = Column(TIMESTAMP)
    deactivated_by = Column(String(255))

    # Relationships
    executions = relationship(
        "PromptExecution", back_populates="template", cascade="all, delete-orphan"
    )
    child_versions = relationship(
        "PromptTemplate", backref="parent_version", remote_side=[id]
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "traffic_percentage >= 0 AND traffic_percentage <= 100",
            name="check_traffic_percentage",
        ),
        UniqueConstraint(
            "name", "is_active", "ab_test_group", name="unique_active_template"
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "template_text": self.template_text,
            "variables": self.variables,
            "version": self.version,
            "parent_version_id": str(self.parent_version_id)
            if self.parent_version_id
            else None,
            "is_active": self.is_active,
            "ab_test_group": self.ab_test_group,
            "traffic_percentage": self.traffic_percentage,
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round((self.success_count / self.total_executions * 100), 2)
            if self.total_executions > 0
            else 0,
            "avg_response_time_ms": self.avg_response_time_ms,
            "avg_token_count": self.avg_token_count,
            "avg_cost_usd": float(self.avg_cost_usd) if self.avg_cost_usd else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return round((self.success_count / self.total_executions) * 100, 2)


class PromptExecution(Base):
    """
    Audit log for every prompt execution with metrics.

    This table logs every time a prompt is rendered and executed, capturing:
    - Input/output data for debugging
    - Performance metrics for optimization
    - Guardrail violations for safety monitoring
    - Error tracking for reliability
    """

    __tablename__ = "prompt_executions"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Template reference
    template_id = Column(
        GUID,
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_name = Column(String(255), nullable=False, index=True)
    template_version = Column(Integer, nullable=False)
    ab_test_group = Column(String(50))

    # Execution context
    user_id = Column(String(255), index=True)
    request_id = Column(GUID, index=True)  # Links to content_requests
    session_id = Column(String(255))

    # Input/Output
    input_variables = Column(JSON, nullable=False)
    rendered_prompt = Column(Text, nullable=False)
    model_response = Column(Text)

    # Performance metrics
    execution_time_ms = Column(Integer)
    token_count = Column(Integer)
    cost_usd = Column(Float)

    # Status
    status = Column(
        String(50), nullable=False, index=True
    )  # 'success', 'failure', 'partial'
    error_message = Column(Text)
    error_type = Column(String(100))

    # Guardrails
    guardrail_violations = Column(JSON, default=[])
    guardrail_action = Column(String(50))  # 'allow', 'block', 'warn'

    # Metadata
    executed_at = Column(TIMESTAMP, default=func.now(), index=True)
    environment = Column(String(50))  # 'dev', 'staging', 'production'

    # Relationships
    template = relationship("PromptTemplate", back_populates="executions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "template_id": str(self.template_id),
            "template_name": self.template_name,
            "template_version": self.template_version,
            "ab_test_group": self.ab_test_group,
            "user_id": self.user_id,
            "request_id": str(self.request_id) if self.request_id else None,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "token_count": self.token_count,
            "cost_usd": float(self.cost_usd) if self.cost_usd else None,
            "guardrail_violations": self.guardrail_violations,
            "guardrail_action": self.guardrail_action,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "environment": self.environment,
        }


class PromptGuardrail(Base):
    """
    Configure safety rules for prompts.

    This table defines guardrails that are evaluated during prompt execution:
    - PII Detection: Prevent leaking sensitive information
    - Toxic Content: Block harmful content
    - Prompt Injection: Detect manipulation attempts
    - Content Policy: Enforce organizational policies
    """

    __tablename__ = "prompt_guardrails"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Guardrail identity
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    guardrail_type = Column(String(100), nullable=False, index=True)

    # Configuration
    is_active = Column(Boolean, default=True, index=True)
    severity = Column(String(50), nullable=False)  # 'critical', 'high', 'medium', 'low'
    action = Column(String(50), nullable=False)  # 'block', 'warn', 'log'

    # Rule definition (flexible JSON structure)
    config = Column(JSON, nullable=False)

    # Applicability
    # Using JSON type for arrays to support both PostgreSQL and SQLite
    applies_to_templates = Column(JSON, default=[])  # Empty = applies to all
    applies_to_categories = Column(JSON, default=[])

    # Performance tracking
    total_checks = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)

    # Metadata
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_by = Column(String(255))
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "guardrail_type": self.guardrail_type,
            "is_active": self.is_active,
            "severity": self.severity,
            "action": self.action,
            "config": self.config,
            "applies_to_templates": self.applies_to_templates,
            "applies_to_categories": self.applies_to_categories,
            "total_checks": self.total_checks,
            "violation_count": self.violation_count,
            "violation_rate": round((self.violation_count / self.total_checks * 100), 2)
            if self.total_checks > 0
            else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ABTestExperiment(Base):
    """
    Manage A/B test experiments with statistical tracking.

    This table orchestrates A/B tests for prompt templates:
    - Traffic allocation across variants
    - Statistical significance tracking
    - Winner declaration
    - Experiment lifecycle management
    """

    __tablename__ = "ab_test_experiments"

    # Primary key
    id = Column(GUID, primary_key=True, default=uuid.uuid4)

    # Experiment identity
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    template_name = Column(String(255), nullable=False, index=True)

    # Experiment status
    status = Column(
        String(50), nullable=False, index=True
    )  # 'draft', 'active', 'paused', 'completed', 'cancelled'

    # Experiment configuration
    control_template_id = Column(
        GUID, ForeignKey("prompt_templates.id", ondelete="RESTRICT"), nullable=False
    )
    # Using JSON type for GUID array to support both PostgreSQL and SQLite
    variant_template_ids = Column(JSON, nullable=False)

    # Traffic allocation
    traffic_allocation = Column(
        JSON, nullable=False
    )  # {"control": 50, "variant_a": 25, "variant_b": 25}

    # Success metrics
    primary_metric = Column(
        String(100), nullable=False
    )  # 'success_rate', 'avg_response_time_ms', etc.
    target_improvement_percentage = Column(Float)
    minimum_sample_size = Column(Integer, default=1000)

    # Statistical tracking
    total_executions = Column(Integer, default=0)
    control_executions = Column(Integer, default=0)
    variant_executions = Column(
        JSON, default={}
    )  # {"variant_a": 500, "variant_b": 500}

    control_metric_value = Column(Float)
    variant_metric_values = Column(
        JSON, default={}
    )  # {"variant_a": 0.85, "variant_b": 0.90}

    statistical_significance = Column(Float)  # p-value
    confidence_level = Column(Float, default=0.95)

    # Winner declaration
    winner_variant = Column(String(50))
    winner_declared_at = Column(TIMESTAMP)
    winner_declared_by = Column(String(255))

    # Timeline
    scheduled_start_date = Column(TIMESTAMP)
    actual_start_date = Column(TIMESTAMP)
    scheduled_end_date = Column(TIMESTAMP)
    actual_end_date = Column(TIMESTAMP)

    # Metadata
    created_by = Column(String(255))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_by = Column(String(255))
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    control_template = relationship(
        "PromptTemplate", foreign_keys=[control_template_id]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "template_name": self.template_name,
            "status": self.status,
            "control_template_id": str(self.control_template_id),
            "variant_template_ids": [str(vid) for vid in self.variant_template_ids],
            "traffic_allocation": self.traffic_allocation,
            "primary_metric": self.primary_metric,
            "total_executions": self.total_executions,
            "control_executions": self.control_executions,
            "variant_executions": self.variant_executions,
            "control_metric_value": self.control_metric_value,
            "variant_metric_values": self.variant_metric_values,
            "statistical_significance": self.statistical_significance,
            "confidence_level": self.confidence_level,
            "winner_variant": self.winner_variant,
            "sample_status": "sufficient"
            if self.total_executions >= self.minimum_sample_size
            else "collecting",
            "scheduled_start_date": self.scheduled_start_date.isoformat()
            if self.scheduled_start_date
            else None,
            "actual_start_date": self.actual_start_date.isoformat()
            if self.actual_start_date
            else None,
            "scheduled_end_date": self.scheduled_end_date.isoformat()
            if self.scheduled_end_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
