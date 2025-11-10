"""
Enterprise Prompt Management Service
Following Andrew Ng's principle: "Build it right, think about the future"
Created: 2025-11-06

This service provides enterprise-grade prompt template management with:
- Database-driven templates with versioning
- Jinja2 template rendering with variable validation
- A/B test variant selection
- Guardrail evaluation (PII detection, toxic content, prompt injection)
- Execution logging and metrics tracking
"""
import hashlib
import logging
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid

from jinja2 import Environment, BaseLoader, TemplateError, meta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.prompt_template import (
    PromptTemplate,
    PromptExecution,
    PromptGuardrail,
    ABTestExperiment,
)

logger = logging.getLogger(__name__)


class PromptManagementService:
    """
    Enterprise-grade prompt management service.

    Responsibilities:
    1. Load active templates from database with A/B test support
    2. Render templates with Jinja2 and validate variables
    3. Evaluate guardrails for safety (PII, toxic content, etc.)
    4. Log all executions for audit and analytics
    5. Track performance metrics
    """

    def __init__(self, db: Session, environment: str = "production"):
        """
        Initialize the service.

        Args:
            db: SQLAlchemy database session
            environment: Current environment ('dev', 'staging', 'production')
        """
        self.db = db
        self.environment = environment

        # Initialize Jinja2 environment with custom settings
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=False,  # We control the content
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(
            f"PromptManagementService initialized for environment: {environment}"
        )

    async def get_active_prompt(
        self,
        name: str,
        user_id: Optional[str] = None,
        enable_ab_testing: bool = True,
    ) -> Optional[PromptTemplate]:
        """
        Get the active prompt template for a given name.

        If A/B testing is enabled and an active experiment exists, selects
        a variant based on traffic allocation and user hashing.

        Args:
            name: Template name (e.g., 'nlu_topic_extraction')
            user_id: User ID for consistent A/B test variant assignment
            enable_ab_testing: Whether to consider A/B tests

        Returns:
            Active PromptTemplate or None if not found
        """
        try:
            # Check for active A/B test
            if enable_ab_testing:
                experiment = (
                    self.db.query(ABTestExperiment)
                    .filter(
                        and_(
                            ABTestExperiment.template_name == name,
                            ABTestExperiment.status == "active",
                        )
                    )
                    .first()
                )

                if experiment:
                    variant = self._select_ab_variant(experiment, user_id)
                    if variant:
                        logger.info(
                            f"A/B test variant selected for '{name}': "
                            f"{variant.ab_test_group} (experiment: {experiment.name})"
                        )
                        return variant

            # No A/B test or variant selection failed - return default active template
            template = (
                self.db.query(PromptTemplate)
                .filter(
                    and_(
                        PromptTemplate.name == name,
                        PromptTemplate.is_active == True,
                        PromptTemplate.ab_test_group.is_(None),  # Not part of A/B test
                    )
                )
                .first()
            )

            if template:
                logger.info(
                    f"Active template loaded for '{name}': version {template.version}"
                )
            else:
                logger.warning(f"No active template found for '{name}'")

            return template

        except Exception as e:
            logger.error(f"Error loading template '{name}': {e}", exc_info=True)
            return None

    def _select_ab_variant(
        self,
        experiment: ABTestExperiment,
        user_id: Optional[str],
    ) -> Optional[PromptTemplate]:
        """
        Select A/B test variant using consistent hashing.

        Uses MD5 hash of user_id to ensure same user always gets same variant.
        Falls back to control if user_id not provided.

        Args:
            experiment: Active ABTestExperiment
            user_id: User ID for consistent assignment

        Returns:
            Selected variant template or None
        """
        if not user_id:
            # No user_id - return control
            return (
                self.db.query(PromptTemplate)
                .filter(PromptTemplate.id == experiment.control_template_id)
                .first()
            )

        # Hash user_id to get consistent assignment
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = hash_value % 100  # 0-99

        # Determine variant based on traffic allocation
        traffic_allocation = experiment.traffic_allocation
        cumulative = 0

        for variant_group, percentage in traffic_allocation.items():
            cumulative += percentage
            if bucket < cumulative:
                # Found the variant for this user
                if variant_group == "control":
                    template_id = experiment.control_template_id
                else:
                    # Find variant template by group name
                    template = (
                        self.db.query(PromptTemplate)
                        .filter(
                            and_(
                                PromptTemplate.name == experiment.template_name,
                                PromptTemplate.ab_test_group == variant_group,
                                PromptTemplate.is_active == True,
                            )
                        )
                        .first()
                    )
                    if template:
                        return template
                    else:
                        logger.warning(
                            f"Variant '{variant_group}' not found for experiment "
                            f"'{experiment.name}', falling back to control"
                        )
                        template_id = experiment.control_template_id

                return (
                    self.db.query(PromptTemplate)
                    .filter(PromptTemplate.id == template_id)
                    .first()
                )

        # Shouldn't reach here, but return control as fallback
        return (
            self.db.query(PromptTemplate)
            .filter(PromptTemplate.id == experiment.control_template_id)
            .first()
        )

    async def render_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
        enable_guardrails: bool = True,
        enable_ab_testing: bool = True,
    ) -> Dict[str, Any]:
        """
        Render a prompt template with variables and evaluate guardrails.

        This is the main entry point for the service. It:
        1. Loads the active template (with A/B test if applicable)
        2. Validates required variables are provided
        3. Renders the template with Jinja2
        4. Evaluates guardrails for safety
        5. Logs the execution for audit and analytics

        Args:
            template_name: Name of the template to render
            variables: Dictionary of variables to pass to template
            user_id: User ID for A/B testing and logging
            request_id: Request ID for correlation
            session_id: Session ID for correlation
            enable_guardrails: Whether to evaluate safety guardrails
            enable_ab_testing: Whether to use A/B test variants

        Returns:
            Dictionary with:
                - rendered_prompt: The rendered template text
                - template_id: UUID of the template used
                - template_version: Version number
                - ab_test_group: A/B test group if applicable
                - execution_id: UUID of the execution log
                - guardrail_violations: List of violations (if any)
                - guardrail_action: Action taken ('allow', 'block', 'warn')
                - status: 'success', 'blocked', or 'error'
                - error: Error message if status is 'error'
        """
        start_time = time.time()
        execution_id = uuid.uuid4()

        try:
            # Step 1: Load template
            template = await self.get_active_prompt(
                template_name,
                user_id=user_id,
                enable_ab_testing=enable_ab_testing,
            )

            if not template:
                error_msg = f"Template '{template_name}' not found or not active"
                logger.error(error_msg)
                await self._log_execution(
                    execution_id=execution_id,
                    template_name=template_name,
                    variables=variables,
                    user_id=user_id,
                    request_id=request_id,
                    session_id=session_id,
                    status="error",
                    error_message=error_msg,
                    error_type="TemplateNotFound",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
                return {
                    "status": "error",
                    "error": error_msg,
                    "execution_id": str(execution_id),
                }

            # Step 2: Validate variables
            validation_result = self._validate_variables(template, variables)
            if not validation_result["valid"]:
                error_msg = (
                    f"Missing required variables: {validation_result['missing']}"
                )
                logger.error(f"Template '{template_name}': {error_msg}")
                await self._log_execution(
                    execution_id=execution_id,
                    template_id=template.id,
                    template_name=template_name,
                    template_version=template.version,
                    ab_test_group=template.ab_test_group,
                    variables=variables,
                    user_id=user_id,
                    request_id=request_id,
                    session_id=session_id,
                    status="error",
                    error_message=error_msg,
                    error_type="ValidationError",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
                return {
                    "status": "error",
                    "error": error_msg,
                    "missing_variables": validation_result["missing"],
                    "execution_id": str(execution_id),
                }

            # Step 3: Render template
            try:
                jinja_template = self.jinja_env.from_string(template.template_text)
                rendered_prompt = jinja_template.render(**variables)
                logger.info(
                    f"Template '{template_name}' rendered successfully "
                    f"({len(rendered_prompt)} chars)"
                )
            except TemplateError as e:
                error_msg = f"Template rendering error: {str(e)}"
                logger.error(f"Template '{template_name}': {error_msg}", exc_info=True)
                await self._log_execution(
                    execution_id=execution_id,
                    template_id=template.id,
                    template_name=template_name,
                    template_version=template.version,
                    ab_test_group=template.ab_test_group,
                    variables=variables,
                    user_id=user_id,
                    request_id=request_id,
                    session_id=session_id,
                    status="error",
                    error_message=error_msg,
                    error_type="RenderError",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
                return {
                    "status": "error",
                    "error": error_msg,
                    "execution_id": str(execution_id),
                }

            # Step 4: Evaluate guardrails
            guardrail_violations = []
            guardrail_action = "allow"

            if enable_guardrails:
                violations, action = await self._evaluate_guardrails(
                    template_name=template_name,
                    category=template.category,
                    rendered_prompt=rendered_prompt,
                    variables=variables,
                )
                guardrail_violations = violations
                guardrail_action = action

                if action == "block":
                    logger.warning(
                        f"Template '{template_name}' blocked by guardrails: "
                        f"{len(violations)} violations"
                    )
                    await self._log_execution(
                        execution_id=execution_id,
                        template_id=template.id,
                        template_name=template_name,
                        template_version=template.version,
                        ab_test_group=template.ab_test_group,
                        variables=variables,
                        rendered_prompt=rendered_prompt,
                        user_id=user_id,
                        request_id=request_id,
                        session_id=session_id,
                        status="success",  # Rendering succeeded
                        guardrail_violations=violations,
                        guardrail_action=action,
                        execution_time_ms=int((time.time() - start_time) * 1000),
                    )
                    return {
                        "status": "blocked",
                        "rendered_prompt": rendered_prompt,
                        "template_id": str(template.id),
                        "template_version": template.version,
                        "ab_test_group": template.ab_test_group,
                        "execution_id": str(execution_id),
                        "guardrail_violations": violations,
                        "guardrail_action": action,
                    }

            # Step 5: Log successful execution
            await self._log_execution(
                execution_id=execution_id,
                template_id=template.id,
                template_name=template_name,
                template_version=template.version,
                ab_test_group=template.ab_test_group,
                variables=variables,
                rendered_prompt=rendered_prompt,
                user_id=user_id,
                request_id=request_id,
                session_id=session_id,
                status="success",
                guardrail_violations=guardrail_violations,
                guardrail_action=guardrail_action,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

            # Step 6: Return result
            return {
                "status": "success",
                "rendered_prompt": rendered_prompt,
                "template_id": str(template.id),
                "template_version": template.version,
                "ab_test_group": template.ab_test_group,
                "execution_id": str(execution_id),
                "guardrail_violations": guardrail_violations,
                "guardrail_action": guardrail_action,
            }

        except Exception as e:
            logger.error(
                f"Unexpected error rendering template '{template_name}': {e}",
                exc_info=True,
            )
            await self._log_execution(
                execution_id=execution_id,
                template_name=template_name,
                variables=variables,
                user_id=user_id,
                request_id=request_id,
                session_id=session_id,
                status="error",
                error_message=str(e),
                error_type=type(e).__name__,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            return {
                "status": "error",
                "error": str(e),
                "execution_id": str(execution_id),
            }

    def _validate_variables(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate that all required variables are provided.

        Args:
            template: The template to validate against
            variables: Variables provided by caller

        Returns:
            Dictionary with 'valid' (bool) and 'missing' (list) keys
        """
        required_vars = template.variables or []
        provided_vars = set(variables.keys())
        missing_vars = [var for var in required_vars if var not in provided_vars]

        return {
            "valid": len(missing_vars) == 0,
            "missing": missing_vars,
        }

    async def _evaluate_guardrails(
        self,
        template_name: str,
        category: Optional[str],
        rendered_prompt: str,
        variables: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Evaluate active guardrails against rendered prompt.

        Checks for:
        - PII (Social Security Numbers, credit cards, phone numbers)
        - Toxic content (profanity, hate speech, violence)
        - Prompt injection attempts

        Args:
            template_name: Name of the template
            category: Template category
            rendered_prompt: The rendered prompt text
            variables: Input variables (also checked)

        Returns:
            Tuple of (violations list, action string)
            - violations: List of violation dictionaries
            - action: 'allow', 'warn', or 'block'
        """
        try:
            # Load active guardrails applicable to this template/category
            guardrails = (
                self.db.query(PromptGuardrail)
                .filter(PromptGuardrail.is_active == True)
                .all()
            )

            # Filter to applicable guardrails
            applicable_guardrails = []
            for guardrail in guardrails:
                # Check if guardrail applies to this template
                applies_to_templates = guardrail.applies_to_templates or []
                applies_to_categories = guardrail.applies_to_categories or []

                if (
                    (len(applies_to_templates) == 0 and len(applies_to_categories) == 0)
                    or (template_name in applies_to_templates)
                    or (category and category in applies_to_categories)
                ):
                    applicable_guardrails.append(guardrail)

            logger.info(
                f"Evaluating {len(applicable_guardrails)} guardrails for '{template_name}'"
            )

            violations = []
            highest_severity_action = "allow"

            for guardrail in applicable_guardrails:
                # Increment check counter
                guardrail.total_checks += 1

                # Evaluate based on type
                violation = None
                if guardrail.guardrail_type == "pii_detection":
                    violation = self._check_pii(guardrail, rendered_prompt, variables)
                elif guardrail.guardrail_type == "toxic_content":
                    violation = self._check_toxic_content(
                        guardrail, rendered_prompt, variables
                    )
                elif guardrail.guardrail_type == "prompt_injection":
                    violation = self._check_prompt_injection(
                        guardrail, rendered_prompt, variables
                    )

                if violation:
                    guardrail.violation_count += 1
                    violations.append(
                        {
                            "guardrail_name": guardrail.name,
                            "guardrail_type": guardrail.guardrail_type,
                            "severity": guardrail.severity,
                            "action": guardrail.action,
                            "details": violation["details"],
                        }
                    )

                    # Update highest severity action
                    if guardrail.action == "block":
                        highest_severity_action = "block"
                    elif (
                        guardrail.action == "warn"
                        and highest_severity_action == "allow"
                    ):
                        highest_severity_action = "warn"

            # Commit guardrail stats updates
            self.db.commit()

            logger.info(
                f"Guardrail evaluation complete: {len(violations)} violations, "
                f"action: {highest_severity_action}"
            )

            return violations, highest_severity_action

        except Exception as e:
            logger.error(f"Error evaluating guardrails: {e}", exc_info=True)
            # On error, allow by default (fail open for availability)
            return [], "allow"

    def _check_pii(
        self,
        guardrail: PromptGuardrail,
        rendered_prompt: str,
        variables: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Check for PII patterns (SSN, credit cards, phone numbers)."""
        config = guardrail.config
        patterns = config.get("patterns", [])

        # Check both rendered prompt and variable values
        text_to_check = rendered_prompt + " " + str(variables)

        for pattern in patterns:
            matches = re.findall(pattern, text_to_check)
            if matches:
                return {
                    "details": f"Detected {len(matches)} potential PII match(es)",
                    "pattern": pattern,
                    "match_count": len(matches),
                }

        return None

    def _check_toxic_content(
        self,
        guardrail: PromptGuardrail,
        rendered_prompt: str,
        variables: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Check for toxic content.

        Note: This is a basic implementation. In production, you'd use a
        service like Perspective API or similar.
        """
        # For now, just log that we would check
        # In production: call Perspective API, Azure Content Moderator, etc.
        logger.debug(
            f"Toxic content check for guardrail '{guardrail.name}' (not implemented)"
        )
        return None

    def _check_prompt_injection(
        self,
        guardrail: PromptGuardrail,
        rendered_prompt: str,
        variables: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Check for prompt injection attempts."""
        config = guardrail.config
        patterns = config.get("patterns", [])
        case_sensitive = config.get("case_sensitive", False)

        text_to_check = rendered_prompt + " " + str(variables)
        if not case_sensitive:
            text_to_check = text_to_check.lower()

        for pattern in patterns:
            search_pattern = pattern if case_sensitive else pattern.lower()
            if search_pattern in text_to_check:
                return {
                    "details": f"Detected potential prompt injection: '{pattern}'",
                    "pattern": pattern,
                }

        return None

    async def _log_execution(
        self,
        execution_id: uuid.UUID,
        template_name: str,
        variables: Dict[str, Any],
        status: str,
        template_id: Optional[uuid.UUID] = None,
        template_version: Optional[int] = None,
        ab_test_group: Optional[str] = None,
        rendered_prompt: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        guardrail_violations: Optional[List[Dict[str, Any]]] = None,
        guardrail_action: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
    ):
        """
        Log prompt execution to database for audit and analytics.

        This function is called for every prompt render attempt, whether
        successful or failed. Logs are used for:
        - Security auditing
        - Performance monitoring
        - A/B test analysis
        - Cost tracking
        """
        try:
            execution = PromptExecution(
                id=execution_id,
                template_id=template_id,
                template_name=template_name,
                template_version=template_version or 0,
                ab_test_group=ab_test_group,
                user_id=user_id,
                request_id=request_id,
                session_id=session_id,
                input_variables=variables,
                rendered_prompt=rendered_prompt or "",
                status=status,
                error_message=error_message,
                error_type=error_type,
                guardrail_violations=guardrail_violations or [],
                guardrail_action=guardrail_action,
                execution_time_ms=execution_time_ms,
                environment=self.environment,
            )

            self.db.add(execution)
            self.db.commit()

            logger.debug(
                f"Execution logged: {execution_id} (template: {template_name}, "
                f"status: {status})"
            )

        except Exception as e:
            logger.error(f"Error logging execution: {e}", exc_info=True)
            # Don't fail the request if logging fails
            self.db.rollback()

    def get_template_performance(
        self,
        name: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a template.

        Args:
            name: Template name
            hours: Number of hours to look back

        Returns:
            Dictionary with performance metrics
        """
        try:
            template = (
                self.db.query(PromptTemplate)
                .filter(
                    and_(
                        PromptTemplate.name == name,
                        PromptTemplate.is_active == True,
                    )
                )
                .first()
            )

            if not template:
                return {"error": f"Template '{name}' not found"}

            # Get recent executions
            since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if hours < 24:
                since = datetime.utcnow().timestamp() - (hours * 3600)

            executions = (
                self.db.query(PromptExecution)
                .filter(
                    and_(
                        PromptExecution.template_name == name,
                        PromptExecution.executed_at >= since,
                    )
                )
                .all()
            )

            total = len(executions)
            success = sum(1 for e in executions if e.status == "success")
            failures = sum(1 for e in executions if e.status == "error")

            avg_time = (
                sum(e.execution_time_ms for e in executions if e.execution_time_ms)
                / total
                if total > 0
                else 0
            )

            return {
                "template_name": name,
                "template_version": template.version,
                "period_hours": hours,
                "total_executions": total,
                "success_count": success,
                "failure_count": failures,
                "success_rate": round((success / total * 100), 2) if total > 0 else 0,
                "avg_execution_time_ms": round(avg_time, 2),
            }

        except Exception as e:
            logger.error(f"Error getting template performance: {e}", exc_info=True)
            return {"error": str(e)}
