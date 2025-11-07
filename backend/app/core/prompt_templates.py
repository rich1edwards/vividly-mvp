"""
Configurable AI Prompt Templates

UPDATED Session 11 Part 19: Full Enterprise Prompt Management System Integration
- Primary: Load from database (if available)
- Fallback: Load from this file (backwards compatible)
- Execution Logging: All prompt executions logged to database for analytics

This module provides backwards-compatible integration between the original file-based
system (Track 1 MVP) and the new database-driven Enterprise Prompt Management System
(Track 2). Services continue working seamlessly whether database is available or not.

Migration Path:
1. Before DB migration: Uses DEFAULT_TEMPLATES (current behavior)
2. After DB migration: Loads from database with A/B testing, guardrails, metrics
3. Zero downtime: Graceful fallback ensures continuity

Monitoring & Observability (Session 11 Part 19):
- Structured logging with metrics for Cloud Logging
- Database connectivity monitoring
- Fallback usage tracking
- Template loading performance metrics
- Error rate tracking
- Prompt execution logging for analytics and A/B testing
"""
import os
import json
import time
import uuid
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Monitoring: Template source tracking for observability
class TemplateSource(str, Enum):
    """Track where templates are loaded from for monitoring"""
    DATABASE = "database"
    ENVIRONMENT = "environment"
    FILE_DEFAULT = "file_default"
    ERROR = "error"

# Monitoring: Metrics tracking
_template_metrics = {
    "database_success": 0,
    "database_errors": 0,
    "environment_usage": 0,
    "file_fallback_usage": 0,
    "total_requests": 0,
}

def get_metrics() -> Dict[str, int]:
    """Return current metrics for monitoring dashboard"""
    return _template_metrics.copy()

def reset_metrics() -> None:
    """Reset metrics (for testing or daily rollover)"""
    global _template_metrics
    _template_metrics = {
        "database_success": 0,
        "database_errors": 0,
        "environment_usage": 0,
        "file_fallback_usage": 0,
        "total_requests": 0,
    }

# Load custom templates from environment if provided
CUSTOM_TEMPLATES_JSON = os.getenv("AI_PROMPT_TEMPLATES_JSON")

DEFAULT_TEMPLATES = {
    "nlu_extraction_gemini_25": {
        "name": "NLU Topic Extraction - Gemini 2.5 Flash",
        "description": "Optimized for Gemini 2.5 Flash - addresses conservative out_of_scope behavior",
        "model_name": "gemini-2.5-flash",
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 2048,  # Increased from 512 - prompt was hitting token limit
        "template": """You are an educational AI assistant specializing in high school STEM subjects.

Your task is to analyze student queries and map them to standardized educational topics.

Available Topics (Grade {grade_level}):
{topics_json}

Student Information:
- Grade Level: {grade_level}
- Subject Context: {subject_context}
- Previous Topics: {recent_topics}

Instructions:
1. Identify the primary academic concept in the query
2. Map to ONE of the available topic_ids above
3. If ambiguous, set clarification_needed=true and provide questions
4. IMPORTANT: Only set out_of_scope=true for clearly non-academic queries (entertainment, personal advice, commercial content)
5. ALL science, math, biology, chemistry, physics, and educational topics are IN SCOPE
6. When uncertain about scope, prefer clarification_needed=true over out_of_scope=true
7. Consider grade-appropriateness (Grade {grade_level})
8. Respond ONLY with valid JSON (no markdown, no explanation)

Output Format (JSON only):
{{
  "confidence": 0.95,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": false,
  "reasoning": "Clear reference to Newton's Third Law"
}}

Few-Shot Examples:

Query: "Explain Newton's Third Law using basketball"
Response: {{"confidence": 0.98, "topic_id": "topic_phys_mech_newton_3", "topic_name": "Newton's Third Law", "clarification_needed": false, "clarifying_questions": [], "out_of_scope": false, "reasoning": "Clear reference to Newton's Third Law in physics"}}

Query: "Tell me about the scientific method"
Response: {{"confidence": 0.85, "topic_id": "topic_sci_method", "topic_name": "Scientific Method", "clarification_needed": false, "clarifying_questions": [], "out_of_scope": false, "reasoning": "Educational query about fundamental scientific process"}}

Query: "Explain how photosynthesis works"
Response: {{"confidence": 0.95, "topic_id": "topic_bio_photosynthesis", "topic_name": "Photosynthesis", "clarification_needed": false, "clarifying_questions": [], "out_of_scope": false, "reasoning": "Clear biology topic appropriate for high school"}}

Query: "Tell me about gravity"
Response: {{"confidence": 0.65, "topic_id": null, "topic_name": null, "clarification_needed": true, "clarifying_questions": ["Are you interested in Newton's Law of Universal Gravitation?", "Or gravitational acceleration on Earth?"], "out_of_scope": false, "reasoning": "Multiple valid interpretations - need clarification"}}

Query: "What's the best pizza place?"
Response: {{"confidence": 0.99, "topic_id": null, "topic_name": null, "clarification_needed": false, "clarifying_questions": [], "out_of_scope": true, "reasoning": "Not related to STEM education - personal recommendation request"}}

Now analyze this student query:
Query: "{student_query}"

Respond with JSON only:"""
    }
}


def get_template(template_key: str = "nlu_extraction_gemini_25") -> Dict[str, Any]:
    """
    Get a prompt template by key.

    Integration Strategy (Zero Downtime):
    1. Try database first (if available)
    2. Fallback to environment override (if configured)
    3. Fallback to DEFAULT_TEMPLATES (always works)

    Args:
        template_key: Template identifier

    Returns:
        Dict containing template configuration

    Raises:
        KeyError: If template_key not found in any source
    """
    # Monitoring: Track request and measure performance
    start_time = time.time()
    _template_metrics["total_requests"] += 1
    source = TemplateSource.FILE_DEFAULT  # Default assumption

    # PHASE 1: Try loading from database (Enterprise Prompt Management System)
    try:
        from app.core.database import get_db
        from app.models.prompt_template import PromptTemplate as PromptTemplateModel
        from sqlalchemy import and_

        # Get database session
        db = next(get_db())
        try:
            # Direct database query (synchronous) - no async needed
            db_template = db.query(PromptTemplateModel).filter(
                and_(
                    PromptTemplateModel.name == template_key,
                    PromptTemplateModel.is_active == True,
                    PromptTemplateModel.ab_test_group.is_(None),  # Not part of A/B test
                )
            ).first()

            if db_template:
                elapsed_ms = (time.time() - start_time) * 1000
                source = TemplateSource.DATABASE
                _template_metrics["database_success"] += 1

                # Structured logging for Cloud Logging
                logger.info(
                    f"Template loaded from database",
                    extra={
                        "template_key": template_key,
                        "template_version": db_template.version,
                        "source": source.value,
                        "latency_ms": elapsed_ms,
                        "database_available": True,
                    }
                )

                # Convert SQLAlchemy model to compatible dict format
                return {
                    "name": db_template.name,
                    "description": db_template.description or "",
                    "model_name": db_template.model_config.get("model_name", "gemini-2.5-flash"),
                    "temperature": db_template.model_config.get("temperature", 0.2),
                    "top_p": db_template.model_config.get("top_p", 0.8),
                    "top_k": db_template.model_config.get("top_k", 40),
                    "max_output_tokens": db_template.model_config.get("max_output_tokens", 512),
                    "template": db_template.template_text,
                }
        finally:
            db.close()

    except Exception as e:
        # Database unavailable or template not found - graceful fallback
        _template_metrics["database_errors"] += 1

        # Structured logging for monitoring
        logger.warning(
            f"Database lookup failed, using fallback",
            extra={
                "template_key": template_key,
                "error_type": type(e).__name__,
                "error_message": str(e)[:200],  # Truncate for logging
                "database_available": False,
            }
        )

    # PHASE 2: Try loading custom templates from environment
    if CUSTOM_TEMPLATES_JSON:
        try:
            custom_templates = json.loads(CUSTOM_TEMPLATES_JSON)
            if template_key in custom_templates:
                elapsed_ms = (time.time() - start_time) * 1000
                source = TemplateSource.ENVIRONMENT
                _template_metrics["environment_usage"] += 1

                logger.info(
                    f"Template loaded from environment",
                    extra={
                        "template_key": template_key,
                        "source": source.value,
                        "latency_ms": elapsed_ms,
                    }
                )
                return custom_templates[template_key]
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI_PROMPT_TEMPLATES_JSON: {e}")
            # Fall through to defaults

    # PHASE 3: Return default template (backwards compatibility)
    if template_key not in DEFAULT_TEMPLATES:
        elapsed_ms = (time.time() - start_time) * 1000
        source = TemplateSource.ERROR

        logger.error(
            f"Template not found in any source",
            extra={
                "template_key": template_key,
                "source": source.value,
                "latency_ms": elapsed_ms,
                "error": "template_not_found",
            }
        )
        raise KeyError(f"Template '{template_key}' not found in DEFAULT_TEMPLATES")

    elapsed_ms = (time.time() - start_time) * 1000
    _template_metrics["file_fallback_usage"] += 1

    logger.info(
        f"Template loaded from file defaults",
        extra={
            "template_key": template_key,
            "source": source.value,
            "latency_ms": elapsed_ms,
        }
    )
    return DEFAULT_TEMPLATES[template_key]


def render_template(template_key: str, variables: Dict[str, Any]) -> str:
    """
    Render a prompt template with given variables.

    Args:
        template_key: Template identifier
        variables: Dictionary of variables to interpolate

    Returns:
        Rendered prompt string

    Raises:
        KeyError: If template_key not found or required variable missing
    """
    template_config = get_template(template_key)
    template_str = template_config["template"]

    # Simple string formatting (use Jinja2 in Track 2 for more advanced features)
    try:
        rendered = template_str.format(**variables)
        logger.debug(f"Rendered template '{template_key}' with {len(variables)} variables")
        return rendered
    except KeyError as e:
        logger.error(f"Missing variable in template '{template_key}': {e}")
        raise


def get_model_config(template_key: str = "nlu_extraction_gemini_25") -> Dict[str, Any]:
    """
    Get model configuration for a template.

    Args:
        template_key: Template identifier

    Returns:
        Dict with model_name, temperature, etc.

    Raises:
        KeyError: If template_key not found
    """
    template_config = get_template(template_key)
    return {
        "model_name": template_config.get("model_name", "gemini-2.5-flash"),
        "temperature": template_config.get("temperature", 0.2),
        "top_p": template_config.get("top_p", 0.8),
        "top_k": template_config.get("top_k", 40),
        "max_output_tokens": template_config.get("max_output_tokens", 512),
    }


def list_templates() -> Dict[str, str]:
    """
    List all available template keys and their names.

    Returns:
        Dict mapping template_key to template name
    """
    return {
        key: config["name"]
        for key, config in DEFAULT_TEMPLATES.items()
    }


def log_prompt_execution(
    template_key: str,
    success: bool,
    response_time_ms: float,
    input_token_count: Optional[int] = None,
    output_token_count: Optional[int] = None,
    cost_usd: Optional[float] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Log a prompt execution to the database for analytics.

    Following Andrew Ng's "test everything" principle - we log ALL prompt executions
    to enable:
    - Performance monitoring and optimization
    - A/B test effectiveness measurement
    - Cost tracking and budget optimization
    - Error pattern detection
    - Usage analytics and dashboards

    This function gracefully degrades if the database is unavailable (e.g., before
    migration or if the database is down). It will never block or crash the main
    application flow.

    Args:
        template_key: The template that was executed
        success: Whether the execution succeeded
        response_time_ms: How long the execution took (milliseconds)
        input_token_count: Number of input tokens (if available)
        output_token_count: Number of output tokens (if available)
        cost_usd: Estimated cost in USD (if calculated)
        error_message: Error message if execution failed
        metadata: Additional context (user_id, request_id, etc.)

    Returns:
        str: Execution ID if logging succeeded, None if it failed

    Raises:
        Does not raise exceptions - logs errors and returns None on failure
    """
    start_time = time.time()

    try:
        from app.core.database import get_db
        from app.models.prompt_template import (
            PromptTemplate as PromptTemplateModel,
            PromptExecution as PromptExecutionModel,
        )
        from sqlalchemy import and_

        # Get database session
        db = next(get_db())
        try:
            # Find the template in the database
            db_template = db.query(PromptTemplateModel).filter(
                and_(
                    PromptTemplateModel.name == template_key,
                    PromptTemplateModel.is_active == True,
                )
            ).first()

            # If template not in database, log to Cloud Logging but don't create execution record
            if not db_template:
                logger.info(
                    f"Prompt execution (template not in DB)",
                    extra={
                        "template_key": template_key,
                        "success": success,
                        "response_time_ms": response_time_ms,
                        "input_tokens": input_token_count,
                        "output_tokens": output_token_count,
                        "cost_usd": cost_usd,
                        "error_message": error_message,
                        "metadata": metadata,
                        "database_template_found": False,
                    }
                )
                return None

            # Create execution record
            execution_id = uuid.uuid4()
            execution = PromptExecutionModel(
                id=execution_id,
                template_id=db_template.id,
                executed_at=datetime.utcnow(),
                success=success,
                response_time_ms=response_time_ms,
                input_token_count=input_token_count,
                output_token_count=output_token_count,
                total_token_count=(input_token_count or 0) + (output_token_count or 0) if input_token_count or output_token_count else None,
                cost_usd=cost_usd,
                error_message=error_message[:1000] if error_message else None,  # Truncate to DB limit
                metadata=metadata or {},
            )

            db.add(execution)
            db.commit()

            elapsed_ms = (time.time() - start_time) * 1000

            # Structured logging for Cloud Logging
            logger.info(
                f"Prompt execution logged",
                extra={
                    "execution_id": str(execution_id),
                    "template_key": template_key,
                    "template_id": str(db_template.id),
                    "template_version": db_template.version,
                    "success": success,
                    "response_time_ms": response_time_ms,
                    "input_tokens": input_token_count,
                    "output_tokens": output_token_count,
                    "total_tokens": execution.total_token_count,
                    "cost_usd": cost_usd,
                    "logging_latency_ms": elapsed_ms,
                    "database_available": True,
                }
            )

            return str(execution_id)

        finally:
            db.close()

    except Exception as e:
        # Graceful degradation: log error but don't crash
        elapsed_ms = (time.time() - start_time) * 1000

        logger.warning(
            f"Failed to log prompt execution to database (non-blocking)",
            extra={
                "template_key": template_key,
                "success": success,
                "response_time_ms": response_time_ms,
                "error_type": type(e).__name__,
                "error_message": str(e)[:200],  # Truncate for logging
                "logging_latency_ms": elapsed_ms,
                "database_available": False,
            }
        )

        # Still log to Cloud Logging for observability
        logger.info(
            f"Prompt execution (DB logging failed)",
            extra={
                "template_key": template_key,
                "success": success,
                "response_time_ms": response_time_ms,
                "input_tokens": input_token_count,
                "output_tokens": output_token_count,
                "cost_usd": cost_usd,
                "error_message": error_message,
                "metadata": metadata,
            }
        )

        return None


def calculate_gemini_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-2.5-flash"
) -> float:
    """
    Calculate cost in USD for Gemini API usage.

    Following Andrew Ng's principle: "build it right" - accurate cost tracking
    is critical for budget optimization and ROI analysis.

    Pricing as of 2025-11-06 for Gemini 2.5 Flash:
    - Input: $0.075 per 1M tokens
    - Output: $0.30 per 1M tokens

    Args:
        input_tokens: Number of input tokens consumed
        output_tokens: Number of output tokens generated
        model: Model name (default: gemini-2.5-flash)

    Returns:
        float: Estimated cost in USD

    Example:
        >>> calculate_gemini_cost(1000, 500)
        0.000225  # $0.075/M * 1000 + $0.30/M * 500
    """
    # Gemini 2.5 Flash pricing (updated 2025-11-06)
    # Source: https://ai.google.dev/pricing
    PRICING = {
        "gemini-2.5-flash": {
            "input_per_million": 0.075,
            "output_per_million": 0.30,
        },
        # Future-proof: Add other models as needed
        "gemini-pro": {
            "input_per_million": 0.50,
            "output_per_million": 1.50,
        },
    }

    # Get pricing for the specified model (default to Flash)
    model_pricing = PRICING.get(model, PRICING["gemini-2.5-flash"])

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * model_pricing["input_per_million"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output_per_million"]

    total_cost = input_cost + output_cost

    logger.debug(
        f"Cost calculation: {input_tokens} input + {output_tokens} output = ${total_cost:.6f}"
    )

    return total_cost


# Migration path to Track 2 (Database-driven system):
# When implementing Track 2, replace get_template() to query database instead of DEFAULT_TEMPLATES
# All other functions remain compatible - just swap the data source
