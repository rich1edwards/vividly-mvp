# Enterprise Prompt Management System - Implementation Plan

**Track 2: Enterprise-Grade Infrastructure**
**Estimated Duration:** 2-3 weeks
**Priority:** High (Post-MVP Foundation)
**Following:** Andrew Ng's principle "Build it right, think about the future"

---

## Executive Summary

Transform the current code-based prompt system into an enterprise-grade, database-driven platform with:
- **SuperAdmin UI** for non-technical prompt management
- **A/B Testing** infrastructure for prompt optimization
- **Versioning & Rollback** for safe prompt iterations
- **Advanced Guardrails** for safety and compliance
- **Audit Logging** for enterprise requirements

---

## Phase 1: Database Schema & Core Infrastructure (Week 1)

### 1.1 Database Schema Design

#### Table: `prompt_templates`
```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,  -- e.g., "nlu_topic_extraction"
    description TEXT,
    category VARCHAR(100),  -- "nlu", "clarification", "script_generation"
    template_text TEXT NOT NULL,  -- Jinja2 template
    template_variables JSONB,  -- {"required": ["query", "grade"], "optional": ["context"]}

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT false,
    parent_version_id UUID REFERENCES prompt_templates(id),

    -- A/B Testing
    ab_test_group VARCHAR(50),  -- null, "control", "variant_a", "variant_b"
    traffic_percentage INTEGER CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),

    -- Performance Metrics
    avg_response_time_ms FLOAT,
    success_rate FLOAT,
    total_invocations INTEGER DEFAULT 0,

    -- Metadata
    created_by VARCHAR(255),  -- user_id of creator
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_active_version UNIQUE (name, is_active) WHERE is_active = true
);

-- Indexes
CREATE INDEX idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active) WHERE is_active = true;
CREATE INDEX idx_prompt_templates_ab_test ON prompt_templates(ab_test_group) WHERE ab_test_group IS NOT NULL;
```

#### Table: `prompt_executions`
```sql
CREATE TABLE prompt_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_template_id UUID NOT NULL REFERENCES prompt_templates(id),

    -- Execution Context
    variables JSONB NOT NULL,  -- Input variables used
    rendered_prompt TEXT NOT NULL,  -- Final prompt after Jinja2 rendering
    model_name VARCHAR(100),  -- e.g., "gemini-2.5-flash"

    -- Results
    response_text TEXT,
    response_tokens INTEGER,
    execution_time_ms INTEGER,
    status VARCHAR(50),  -- "success", "error", "timeout"
    error_message TEXT,

    -- A/B Testing Metrics
    ab_test_group VARCHAR(50),
    conversion_metric FLOAT,  -- Custom metric (e.g., clarification_resolved=1.0)

    -- Guardrails
    guardrail_violations JSONB,  -- [{"rule": "no_pii", "violated": false}, ...]
    safety_score FLOAT CHECK (safety_score >= 0 AND safety_score <= 1),

    -- Metadata
    request_id UUID,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_prompt_executions_template ON prompt_executions(prompt_template_id);
CREATE INDEX idx_prompt_executions_status ON prompt_executions(status);
CREATE INDEX idx_prompt_executions_created_at ON prompt_executions(created_at DESC);
CREATE INDEX idx_prompt_executions_ab_test ON prompt_executions(ab_test_group) WHERE ab_test_group IS NOT NULL;
```

#### Table: `prompt_guardrails`
```sql
CREATE TABLE prompt_guardrails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Guardrail Configuration
    rule_type VARCHAR(50) NOT NULL,  -- "regex", "keyword", "model_check", "custom"
    rule_config JSONB NOT NULL,  -- Rule-specific configuration

    -- Enforcement
    enforcement_level VARCHAR(50) NOT NULL,  -- "blocking", "warning", "logging"
    applies_to VARCHAR(100)[],  -- ["nlu_topic_extraction", "clarification"]

    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example guardrail rules:
-- 1. PII Detection: {"type": "regex", "patterns": ["\\b\\d{3}-\\d{2}-\\d{4}\\b"], "message": "SSN detected"}
-- 2. Toxic Content: {"type": "model_check", "model": "perspective_api", "threshold": 0.7}
-- 3. Prompt Injection: {"type": "keyword", "keywords": ["ignore previous", "disregard instructions"]}
```

#### Table: `ab_test_experiments`
```sql
CREATE TABLE ab_test_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,

    -- Test Configuration
    control_template_id UUID NOT NULL REFERENCES prompt_templates(id),
    variant_template_ids UUID[] NOT NULL,  -- Array of variant template IDs

    -- Traffic Split
    traffic_allocation JSONB NOT NULL,  -- {"control": 50, "variant_a": 25, "variant_b": 25}

    -- Success Criteria
    primary_metric VARCHAR(100) NOT NULL,  -- "success_rate", "avg_response_time", "conversion"
    minimum_sample_size INTEGER NOT NULL DEFAULT 1000,
    significance_threshold FLOAT NOT NULL DEFAULT 0.05,  -- p-value threshold

    -- Status
    status VARCHAR(50) NOT NULL,  -- "draft", "running", "paused", "completed", "winner_declared"
    winner_template_id UUID REFERENCES prompt_templates(id),

    -- Metadata
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.2 Migration Scripts

**File:** `backend/migrations/create_enterprise_prompt_system.sql`

```sql
-- Run this migration after backing up production database
BEGIN;

-- Create tables
\i create_prompt_templates.sql
\i create_prompt_executions.sql
\i create_prompt_guardrails.sql
\i create_ab_test_experiments.sql

-- Migrate existing prompts from code to database
INSERT INTO prompt_templates (name, category, template_text, is_active, created_by)
VALUES
(
    'nlu_topic_extraction',
    'nlu',
    E'You are an expert educational content analyzer.\n\nStudent Query: {{ query }}\nGrade Level: {{ grade_level }}\n\nExtract the academic topic and determine if clarification is needed.',
    true,
    'system_migration'
),
(
    'clarification_questions',
    'clarification',
    E'Generate 3 clarifying questions for this vague query:\n\nQuery: {{ query }}\nContext: {{ context }}',
    true,
    'system_migration'
);

COMMIT;
```

### 1.3 Core Services Implementation

**File:** `backend/app/services/prompt_management_service.py`

```python
"""
Enterprise Prompt Management Service

Handles:
- Template rendering with Jinja2
- A/B test variant selection
- Guardrail enforcement
- Performance tracking
- Version management
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import jinja2
import random

from sqlalchemy import select, and_, or_
from app.database import get_db
from app.models.prompt_templates import (
    PromptTemplate, PromptExecution, PromptGuardrail, ABTestExperiment
)

logger = logging.getLogger(__name__)


class PromptManagementService:
    """Enterprise-grade prompt management with A/B testing and guardrails."""

    def __init__(self):
        self.jinja_env = jinja2.Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    async def get_active_prompt(
        self,
        name: str,
        user_id: Optional[str] = None,
        enable_ab_testing: bool = True
    ) -> PromptTemplate:
        """
        Get active prompt template, with optional A/B test variant selection.

        Args:
            name: Template name (e.g., "nlu_topic_extraction")
            user_id: User ID for consistent variant assignment
            enable_ab_testing: Whether to apply A/B test logic

        Returns:
            Active PromptTemplate (control or variant)
        """
        async with get_db() as session:
            # Check if template is in an active A/B test
            if enable_ab_testing:
                experiment = await self._get_active_experiment(session, name)
                if experiment:
                    variant = await self._select_ab_variant(
                        session, experiment, user_id
                    )
                    logger.info(
                        f"A/B test active for {name}: "
                        f"selected variant={variant.ab_test_group}"
                    )
                    return variant

            # No A/B test, return active template
            stmt = select(PromptTemplate).where(
                and_(
                    PromptTemplate.name == name,
                    PromptTemplate.is_active == True
                )
            )
            result = await session.execute(stmt)
            template = result.scalar_one_or_none()

            if not template:
                raise ValueError(f"No active template found for: {name}")

            return template

    async def render_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render prompt with guardrails and execution tracking.

        Returns:
            {
                "rendered_prompt": str,
                "template_id": UUID,
                "ab_test_group": Optional[str],
                "execution_id": UUID,
                "guardrail_violations": List[Dict]
            }
        """
        start_time = datetime.utcnow()

        # Get active template (with A/B test logic)
        template = await self.get_active_prompt(template_name, user_id)

        # Render Jinja2 template
        jinja_template = self.jinja_env.from_string(template.template_text)
        rendered_prompt = jinja_template.render(**variables)

        # Apply guardrails
        guardrail_violations = await self._check_guardrails(
            template.name, rendered_prompt
        )

        # Check if any blocking violations
        blocking_violations = [
            v for v in guardrail_violations
            if v["enforcement_level"] == "blocking"
        ]

        if blocking_violations:
            logger.error(
                f"Blocking guardrail violations for {template_name}: "
                f"{blocking_violations}"
            )
            raise ValueError(
                f"Prompt violates guardrails: "
                f"{[v['name'] for v in blocking_violations]}"
            )

        # Track execution
        execution_time_ms = (
            datetime.utcnow() - start_time
        ).total_seconds() * 1000

        execution_id = await self._log_execution(
            template_id=template.id,
            variables=variables,
            rendered_prompt=rendered_prompt,
            execution_time_ms=execution_time_ms,
            ab_test_group=template.ab_test_group,
            guardrail_violations=guardrail_violations,
            request_id=request_id,
            user_id=user_id
        )

        return {
            "rendered_prompt": rendered_prompt,
            "template_id": str(template.id),
            "template_version": template.version,
            "ab_test_group": template.ab_test_group,
            "execution_id": str(execution_id),
            "guardrail_violations": [
                v for v in guardrail_violations
                if v["enforcement_level"] == "warning"
            ]
        }

    async def _check_guardrails(
        self, template_name: str, rendered_prompt: str
    ) -> List[Dict[str, Any]]:
        """Check all active guardrails applicable to this template."""
        violations = []

        async with get_db() as session:
            stmt = select(PromptGuardrail).where(
                and_(
                    PromptGuardrail.is_active == True,
                    or_(
                        PromptGuardrail.applies_to.contains([template_name]),
                        PromptGuardrail.applies_to == []  # Applies to all
                    )
                )
            )
            result = await session.execute(stmt)
            guardrails = result.scalars().all()

            for guardrail in guardrails:
                violation = await self._evaluate_guardrail(
                    guardrail, rendered_prompt
                )
                if violation:
                    violations.append({
                        "name": guardrail.name,
                        "rule_type": guardrail.rule_type,
                        "enforcement_level": guardrail.enforcement_level,
                        "message": violation
                    })

        return violations

    async def _evaluate_guardrail(
        self, guardrail: PromptGuardrail, prompt: str
    ) -> Optional[str]:
        """Evaluate a single guardrail rule."""
        if guardrail.rule_type == "regex":
            import re
            patterns = guardrail.rule_config.get("patterns", [])
            for pattern in patterns:
                if re.search(pattern, prompt):
                    return f"Pattern matched: {pattern}"

        elif guardrail.rule_type == "keyword":
            keywords = guardrail.rule_config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in prompt.lower():
                    return f"Keyword detected: {keyword}"

        elif guardrail.rule_type == "max_length":
            max_len = guardrail.rule_config.get("max_length", 10000)
            if len(prompt) > max_len:
                return f"Prompt exceeds max length: {len(prompt)} > {max_len}"

        # Add more guardrail types as needed
        return None

    async def _select_ab_variant(
        self,
        session,
        experiment: ABTestExperiment,
        user_id: Optional[str]
    ) -> PromptTemplate:
        """Select A/B test variant based on traffic allocation."""
        traffic_allocation = experiment.traffic_allocation

        # Use user_id for consistent variant assignment
        if user_id:
            # Hash user_id to get consistent variant
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            rand_val = hash_val % 100
        else:
            # Random assignment if no user_id
            rand_val = random.randint(0, 99)

        # Determine which variant based on traffic allocation
        cumulative = 0
        for group, percentage in traffic_allocation.items():
            cumulative += percentage
            if rand_val < cumulative:
                # Find template with this ab_test_group
                if group == "control":
                    template_id = experiment.control_template_id
                else:
                    # Map variant name to template_id
                    variant_idx = ord(group.split("_")[1]) - ord("a")
                    template_id = experiment.variant_template_ids[variant_idx]

                stmt = select(PromptTemplate).where(
                    PromptTemplate.id == template_id
                )
                result = await session.execute(stmt)
                return result.scalar_one()

        # Fallback to control
        stmt = select(PromptTemplate).where(
            PromptTemplate.id == experiment.control_template_id
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _log_execution(
        self,
        template_id: UUID,
        variables: Dict[str, Any],
        rendered_prompt: str,
        execution_time_ms: float,
        ab_test_group: Optional[str],
        guardrail_violations: List[Dict],
        request_id: Optional[str],
        user_id: Optional[str]
    ) -> UUID:
        """Log prompt execution for analytics and debugging."""
        async with get_db() as session:
            execution = PromptExecution(
                prompt_template_id=template_id,
                variables=variables,
                rendered_prompt=rendered_prompt,
                execution_time_ms=int(execution_time_ms),
                status="success",
                ab_test_group=ab_test_group,
                guardrail_violations=guardrail_violations,
                request_id=request_id,
                user_id=user_id
            )
            session.add(execution)
            await session.commit()
            await session.refresh(execution)
            return execution.id

    async def create_version(
        self,
        parent_template_id: UUID,
        template_text: str,
        created_by: str,
        description: Optional[str] = None
    ) -> PromptTemplate:
        """Create new version of existing template."""
        async with get_db() as session:
            # Get parent template
            parent = await session.get(PromptTemplate, parent_template_id)
            if not parent:
                raise ValueError(f"Parent template not found: {parent_template_id}")

            # Create new version (inactive by default)
            new_version = PromptTemplate(
                name=parent.name,
                description=description or parent.description,
                category=parent.category,
                template_text=template_text,
                template_variables=parent.template_variables,
                version=parent.version + 1,
                is_active=False,
                parent_version_id=parent_template_id,
                created_by=created_by
            )

            session.add(new_version)
            await session.commit()
            await session.refresh(new_version)

            logger.info(
                f"Created new version for {parent.name}: "
                f"v{new_version.version} (id={new_version.id})"
            )

            return new_version

    async def activate_version(
        self, template_id: UUID, activated_by: str
    ) -> PromptTemplate:
        """Activate a template version (deactivates current active)."""
        async with get_db() as session:
            # Get template to activate
            template = await session.get(PromptTemplate, template_id)
            if not template:
                raise ValueError(f"Template not found: {template_id}")

            # Deactivate current active version
            stmt = select(PromptTemplate).where(
                and_(
                    PromptTemplate.name == template.name,
                    PromptTemplate.is_active == True
                )
            )
            result = await session.execute(stmt)
            current_active = result.scalar_one_or_none()

            if current_active:
                current_active.is_active = False
                current_active.deactivated_at = datetime.utcnow()

            # Activate new version
            template.is_active = True
            template.activated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(template)

            logger.info(
                f"Activated template {template.name} v{template.version} "
                f"(id={template.id}) by {activated_by}"
            )

            return template

    async def rollback_to_version(
        self, template_name: str, version: int, rolled_back_by: str
    ) -> PromptTemplate:
        """Rollback to a specific version."""
        async with get_db() as session:
            stmt = select(PromptTemplate).where(
                and_(
                    PromptTemplate.name == template_name,
                    PromptTemplate.version == version
                )
            )
            result = await session.execute(stmt)
            template = result.scalar_one_or_none()

            if not template:
                raise ValueError(
                    f"Version not found: {template_name} v{version}"
                )

            return await self.activate_version(template.id, rolled_back_by)


# Singleton
_prompt_service = None

def get_prompt_service() -> PromptManagementService:
    """Get singleton prompt management service."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptManagementService()
    return _prompt_service
```

---

## Phase 2: SuperAdmin UI (Week 2, Days 1-3)

### 2.1 Frontend Architecture

**Technology Stack:**
- React 18 with TypeScript
- TailwindCSS for styling
- React Query for data fetching
- React Router for navigation
- Monaco Editor for template editing
- Recharts for analytics visualization

### 2.2 Page Structure

#### Dashboard: `/admin/prompts`
- List all prompt templates
- Quick stats (total templates, active A/B tests, recent executions)
- Search and filter by category/status

#### Template Editor: `/admin/prompts/:id/edit`
- Monaco editor with Jinja2 syntax highlighting
- Variable autocomplete
- Live preview with sample data
- Version history sidebar
- Guardrail status indicators

#### A/B Test Console: `/admin/ab-tests`
- Create new experiments
- Configure traffic splits
- Monitor real-time metrics
- Declare winners
- Statistical significance calculator

#### Guardrails Manager: `/admin/guardrails`
- Configure safety rules
- Test guardrails against sample prompts
- View violation logs
- Enable/disable rules

### 2.3 Key Components

**File:** `frontend/src/pages/admin/PromptEditor.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import Editor from '@monaco-editor/react';
import {
  promptApi,
  PromptTemplate,
  GuardrailViolation
} from '@/api/prompts';

export const PromptEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [templateText, setTemplateText] = useState('');
  const [previewVars, setPreviewVars] = useState<Record<string, any>>({});
  const [renderedPreview, setRenderedPreview] = useState('');
  const [violations, setViolations] = useState<GuardrailViolation[]>([]);

  // Fetch template
  const { data: template, isLoading } = useQuery(
    ['prompt-template', id],
    () => promptApi.getTemplate(id!),
    { enabled: !!id }
  );

  // Preview mutation
  const previewMutation = useMutation(
    (vars: Record<string, any>) =>
      promptApi.previewTemplate(id!, templateText, vars),
    {
      onSuccess: (data) => {
        setRenderedPreview(data.rendered_prompt);
        setViolations(data.guardrail_violations);
      }
    }
  );

  // Save mutation
  const saveMutation = useMutation(
    () => promptApi.updateTemplate(id!, { template_text: templateText }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['prompt-template', id]);
        // Show success toast
      }
    }
  );

  // Create new version mutation
  const createVersionMutation = useMutation(
    () => promptApi.createVersion(id!, templateText),
    {
      onSuccess: (newVersion) => {
        navigate(`/admin/prompts/${newVersion.id}/edit`);
      }
    }
  );

  useEffect(() => {
    if (template) {
      setTemplateText(template.template_text);
      // Load sample variables
      const sampleVars = {};
      for (const [key, type] of Object.entries(template.template_variables.required)) {
        sampleVars[key] = getSampleValue(type);
      }
      setPreviewVars(sampleVars);
    }
  }, [template]);

  const handlePreview = () => {
    previewMutation.mutate(previewVars);
  };

  const handleSave = () => {
    if (template?.is_active) {
      // Require creating new version if editing active template
      createVersionMutation.mutate();
    } else {
      saveMutation.mutate();
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="flex h-screen">
      {/* Left: Editor */}
      <div className="w-1/2 border-r">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="text-xl font-bold">{template?.name}</h2>
          <p className="text-sm text-gray-600">
            Version {template?.version}
            {template?.is_active && (
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded">
                Active
              </span>
            )}
          </p>
        </div>

        <Editor
          height="calc(100vh - 200px)"
          defaultLanguage="jinja2"
          value={templateText}
          onChange={(value) => setTemplateText(value || '')}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on'
          }}
        />

        <div className="p-4 border-t flex gap-2">
          <button
            onClick={handlePreview}
            className="px-4 py-2 bg-blue-500 text-white rounded"
            disabled={previewMutation.isLoading}
          >
            Preview
          </button>

          <button
            onClick={handleSave}
            className="px-4 py-2 bg-green-500 text-white rounded"
            disabled={saveMutation.isLoading}
          >
            {template?.is_active ? 'Create New Version' : 'Save'}
          </button>
        </div>
      </div>

      {/* Right: Preview & Variables */}
      <div className="w-1/2 p-4 overflow-y-auto">
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Preview Variables</h3>
          {Object.entries(previewVars).map(([key, value]) => (
            <div key={key} className="mb-2">
              <label className="block text-sm font-medium mb-1">
                {key}
              </label>
              <input
                type="text"
                value={value}
                onChange={(e) =>
                  setPreviewVars({ ...previewVars, [key]: e.target.value })
                }
                className="w-full px-3 py-2 border rounded"
              />
            </div>
          ))}
        </div>

        {violations.length > 0 && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
            <h3 className="text-lg font-semibold mb-2 text-yellow-800">
              Guardrail Violations
            </h3>
            {violations.map((v, i) => (
              <div key={i} className="text-sm text-yellow-700">
                • {v.name}: {v.message}
              </div>
            ))}
          </div>
        )}

        <div>
          <h3 className="text-lg font-semibold mb-2">Rendered Prompt</h3>
          <div className="p-4 bg-gray-50 border rounded whitespace-pre-wrap">
            {renderedPreview || 'Click Preview to render...'}
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## Phase 3: A/B Testing Infrastructure (Week 2, Days 4-5)

### 3.1 A/B Test Manager Component

**File:** `frontend/src/pages/admin/ABTestConsole.tsx`

```typescript
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { abTestApi, ABTestExperiment, ABTestMetrics } from '@/api/ab-tests';

export const ABTestConsole: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);

  // Fetch active experiments
  const { data: experiments } = useQuery(
    'ab-experiments',
    abTestApi.listExperiments
  );

  // Fetch metrics for selected experiment
  const { data: metrics } = useQuery(
    ['ab-metrics', selectedExperiment],
    () => abTestApi.getMetrics(selectedExperiment!),
    { enabled: !!selectedExperiment, refetchInterval: 5000 }
  );

  // Declare winner mutation
  const declareWinnerMutation = useMutation(
    ({ experimentId, winnerId }: { experimentId: string; winnerId: string }) =>
      abTestApi.declareWinner(experimentId, winnerId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('ab-experiments');
        // Show success toast
      }
    }
  );

  const handleDeclareWinner = (winnerId: string) => {
    if (!selectedExperiment) return;

    if (confirm('Are you sure? This will activate the winning variant.')) {
      declareWinnerMutation.mutate({
        experimentId: selectedExperiment,
        winnerId
      });
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">A/B Test Console</h1>

      {/* Experiment List */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Active Experiments</h2>
        <div className="grid grid-cols-3 gap-4">
          {experiments?.map((exp) => (
            <div
              key={exp.id}
              onClick={() => setSelectedExperiment(exp.id)}
              className={`
                p-4 border rounded cursor-pointer
                ${selectedExperiment === exp.id ? 'border-blue-500 bg-blue-50' : ''}
              `}
            >
              <h3 className="font-semibold">{exp.name}</h3>
              <p className="text-sm text-gray-600">{exp.description}</p>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-1 bg-gray-100 text-xs rounded">
                  {exp.status}
                </span>
                <span className="px-2 py-1 bg-blue-100 text-xs rounded">
                  {exp.variant_count} variants
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics Dashboard */}
      {metrics && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">
            Experiment Metrics: {metrics.experiment_name}
          </h2>

          {/* Key Metrics Cards */}
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              title="Sample Size"
              value={metrics.total_samples}
              target={metrics.minimum_sample_size}
            />
            <MetricCard
              title="Statistical Significance"
              value={`${(metrics.p_value * 100).toFixed(2)}%`}
              isSignificant={metrics.p_value < 0.05}
            />
            <MetricCard
              title="Best Performer"
              value={metrics.best_variant_name}
              improvement={`+${metrics.improvement_percentage}%`}
            />
            <MetricCard
              title="Confidence Level"
              value={`${metrics.confidence_level}%`}
            />
          </div>

          {/* Performance Chart */}
          <div className="bg-white p-6 border rounded">
            <h3 className="text-lg font-semibold mb-4">
              {metrics.primary_metric} by Variant
            </h3>
            <BarChart width={800} height={400} data={metrics.variant_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="variant_name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="metric_value" fill="#3b82f6" />
              <Bar dataKey="sample_size" fill="#10b981" />
            </BarChart>
          </div>

          {/* Winner Declaration */}
          {metrics.can_declare_winner && (
            <div className="bg-green-50 border border-green-200 p-6 rounded">
              <h3 className="text-lg font-semibold text-green-800 mb-2">
                Ready to Declare Winner
              </h3>
              <p className="text-sm text-green-700 mb-4">
                Sufficient sample size reached with statistical significance.
                Variant "{metrics.best_variant_name}" shows {metrics.improvement_percentage}%
                improvement over control.
              </p>
              <button
                onClick={() => handleDeclareWinner(metrics.best_variant_id)}
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Declare "{metrics.best_variant_name}" as Winner
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  target?: number;
  isSignificant?: boolean;
  improvement?: string;
}> = ({ title, value, target, isSignificant, improvement }) => (
  <div className="bg-white p-4 border rounded">
    <div className="text-sm text-gray-600 mb-1">{title}</div>
    <div className="text-2xl font-bold">{value}</div>
    {target && (
      <div className="text-xs text-gray-500">Target: {target}</div>
    )}
    {isSignificant !== undefined && (
      <div className={`text-xs mt-1 ${isSignificant ? 'text-green-600' : 'text-gray-500'}`}>
        {isSignificant ? '✓ Significant' : '○ Not yet significant'}
      </div>
    )}
    {improvement && (
      <div className="text-sm text-green-600 font-semibold">{improvement}</div>
    )}
  </div>
);
```

---

## Phase 4: Integration & Testing (Week 3)

### 4.1 Update Existing Services

**File:** `backend/app/services/nlu_service.py` (Updated)

```python
# OLD CODE:
# prompt = f"Extract topic from: {student_query}"

# NEW CODE:
from app.services.prompt_management_service import get_prompt_service

async def extract_topic(student_query: str, grade_level: int, student_id: str):
    prompt_service = get_prompt_service()

    # Render prompt with A/B testing and guardrails
    prompt_data = await prompt_service.render_prompt(
        template_name="nlu_topic_extraction",
        variables={
            "query": student_query,
            "grade_level": grade_level
        },
        user_id=student_id,
        request_id=get_request_id()  # From FastAPI context
    )

    # Use rendered prompt
    response = await gemini_client.generate(prompt_data["rendered_prompt"])

    # Log performance for A/B test metrics
    await prompt_service.log_performance(
        execution_id=prompt_data["execution_id"],
        success=response.success,
        conversion_metric=1.0 if response.topic_extracted else 0.0
    )

    return response
```

### 4.2 Comprehensive Testing

**Test Suite:**
1. Unit tests for guardrail evaluation
2. Integration tests for A/B variant selection
3. E2E tests for version rollback
4. Load tests for prompt rendering performance
5. UI tests for SuperAdmin console

---

## Phase 5: Documentation & Training (Week 3, Days 4-5)

### 5.1 Admin User Guide

Create comprehensive documentation:
- How to create new prompt templates
- Best practices for prompt engineering
- A/B testing workflow
- Interpreting statistical significance
- Guardrail configuration examples
- Version management and rollback procedures

### 5.2 API Documentation

Generate OpenAPI docs for:
- `POST /api/admin/prompts` - Create template
- `GET /api/admin/prompts/{id}` - Get template
- `PUT /api/admin/prompts/{id}` - Update template
- `POST /api/admin/prompts/{id}/versions` - Create version
- `POST /api/admin/prompts/{id}/activate` - Activate version
- `GET /api/admin/ab-tests` - List experiments
- `POST /api/admin/ab-tests` - Create experiment
- `POST /api/admin/ab-tests/{id}/winner` - Declare winner

---

## Success Metrics

### Week 1 Completion Criteria:
- [ ] All database tables created and migrated
- [ ] Core PromptManagementService implemented
- [ ] Unit tests passing (>90% coverage)
- [ ] Existing prompts migrated to database

### Week 2 Completion Criteria:
- [ ] SuperAdmin UI deployed and accessible
- [ ] Template editor functional with live preview
- [ ] A/B test console shows real-time metrics
- [ ] Guardrails manager fully operational

### Week 3 Completion Criteria:
- [ ] All existing services integrated
- [ ] E2E tests passing (100%)
- [ ] Performance benchmarks met (< 100ms prompt rendering)
- [ ] Documentation complete
- [ ] Training session conducted

---

## Risk Mitigation

### Risk 1: Performance Degradation
**Mitigation:** Cache rendered prompts in Redis with TTL

### Risk 2: Database Migration Failure
**Mitigation:** Test on staging, full backup before production migration

### Risk 3: A/B Test Bias
**Mitigation:** Implement proper randomization and statistical validation

### Risk 4: Guardrail False Positives
**Mitigation:** Warning-only mode first, then gradual enforcement

---

## Cost Analysis

### Infrastructure Costs:
- PostgreSQL storage: ~$50/month (10GB)
- Redis cache: ~$30/month (1GB)
- Additional compute: ~$100/month (UI hosting)
- **Total:** ~$180/month

### Development Time:
- Phase 1: 40 hours (Week 1)
- Phase 2: 24 hours (Week 2, Days 1-3)
- Phase 3: 16 hours (Week 2, Days 4-5)
- Phase 4: 32 hours (Week 3, Days 1-3)
- Phase 5: 8 hours (Week 3, Days 4-5)
- **Total:** 120 hours (~3 weeks)

---

## Next Immediate Action

Since you've chosen Option B, the immediate next step is:

**START PHASE 1.1: Database Schema Design**

I will create the migration script to set up the prompt_templates, prompt_executions, prompt_guardrails, and ab_test_experiments tables.

Ready to proceed?
