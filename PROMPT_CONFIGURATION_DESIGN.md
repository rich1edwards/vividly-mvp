# Configurable NLU Prompt System Design

**Date**: November 5, 2025
**Purpose**: Enable SuperAdmin to manage AI prompts with guardrails and versioning
**Context**: Gemini 2.5 Flash migration revealed need for prompt flexibility

## Executive Summary

Implement a database-driven prompt configuration system that allows SuperAdmins to:
1. Edit NLU prompts without code deployments
2. Add safety guardrails and validation rules
3. Version prompts with rollback capability
4. A/B test different prompt strategies
5. Monitor prompt performance metrics

## Database Schema

### Table: `ai_prompt_templates`

```sql
CREATE TABLE ai_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    prompt_type VARCHAR(50) NOT NULL,  -- 'nlu_extraction', 'script_generation', etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Template content
    template_text TEXT NOT NULL,  -- Jinja2 template with {{variables}}
    system_instructions TEXT,     -- System-level instructions for AI

    -- Model configuration
    model_name VARCHAR(100),      -- e.g., 'gemini-2.5-flash'
    temperature DECIMAL(3,2),     -- 0.00-1.00
    top_p DECIMAL(3,2),
    top_k INTEGER,
    max_output_tokens INTEGER,

    -- Guardrails
    guardrails JSONB,             -- See guardrails schema below

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT false,
    parent_version_id UUID REFERENCES ai_prompt_templates(id),

    -- A/B Testing
    traffic_percentage INTEGER DEFAULT 0,  -- 0-100
    experiment_name VARCHAR(255),

    -- Performance metrics
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    avg_response_time_ms INTEGER,

    -- Audit
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP,

    -- Constraints
    UNIQUE(prompt_type, version),
    CHECK (temperature >= 0 AND temperature <= 1),
    CHECK (top_p >= 0 AND top_p <= 1),
    CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100)
);

CREATE INDEX idx_prompt_templates_type_active ON ai_prompt_templates(prompt_type, is_active);
CREATE INDEX idx_prompt_templates_experiment ON ai_prompt_templates(experiment_name) WHERE experiment_name IS NOT NULL;
```

### Table: `ai_prompt_executions`

```sql
CREATE TABLE ai_prompt_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Prompt reference
    template_id UUID REFERENCES ai_prompt_templates(id),
    prompt_type VARCHAR(50) NOT NULL,

    -- Execution context
    request_id UUID,  -- Link to content_requests if applicable
    input_variables JSONB,  -- Variables passed to template
    rendered_prompt TEXT,   -- Final prompt sent to AI

    -- AI response
    model_response TEXT,
    response_metadata JSONB,  -- Full AI response metadata

    -- Performance
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    token_count INTEGER,

    -- Outcome
    status VARCHAR(20),  -- 'success', 'failed', 'blocked_by_guardrail'
    error_message TEXT,
    guardrail_violations JSONB,

    -- Quality metrics
    confidence_score DECIMAL(3,2),
    user_feedback VARCHAR(20),  -- 'helpful', 'not_helpful'

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prompt_executions_template ON ai_prompt_executions(template_id);
CREATE INDEX idx_prompt_executions_request ON ai_prompt_executions(request_id);
CREATE INDEX idx_prompt_executions_status ON ai_prompt_executions(status, created_at DESC);
```

## Guardrails Schema (JSONB)

```json
{
  "input_validation": {
    "max_length": 1000,
    "min_length": 3,
    "allowed_languages": ["en"],
    "blocked_patterns": [
      "regex:password|credit card|ssn",
      "exact:ignore previous instructions"
    ]
  },
  "output_validation": {
    "required_fields": ["confidence", "topic_id", "clarification_needed"],
    "field_constraints": {
      "confidence": {"min": 0.0, "max": 1.0},
      "topic_id": {"pattern": "^topic_[a-z_]+$"},
      "out_of_scope": {"allowed_values": [true, false]}
    },
    "max_response_length": 2000,
    "blocked_content": [
      "type:pii",
      "type:hate_speech",
      "type:misinformation"
    ]
  },
  "safety_settings": {
    "harm_categories": {
      "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
      "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
      "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
      "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH"
    }
  },
  "rate_limiting": {
    "max_calls_per_minute": 60,
    "max_calls_per_hour": 1000
  },
  "cost_controls": {
    "max_tokens_per_call": 2000,
    "alert_threshold_usd": 100.0
  }
}
```

## Prompt Template Format (Jinja2)

```jinja2
You are an educational AI assistant specializing in high school STEM subjects.

Your task is to analyze student queries and map them to standardized educational topics.

Available Topics (Grade {{ grade_level }}):
{{ topics_json }}

Student Information:
- Grade Level: {{ grade_level }}
- Subject Context: {{ subject_context }}
- Previous Topics: {{ recent_topics }}

Instructions:
1. Identify the primary academic concept in the query
2. Map to ONE of the available topic_ids above
3. If ambiguous, set clarification_needed=true and provide questions
4. {{ guardrail_scope_instruction }}  <!-- Configurable! -->
5. Consider grade-appropriateness (Grade {{ grade_level }})
6. Respond ONLY with valid JSON (no markdown, no explanation)

Output Format (JSON only):
{
  "confidence": 0.95,
  "topic_id": "topic_phys_mech_newton_3",
  "topic_name": "Newton's Third Law",
  "clarification_needed": false,
  "clarifying_questions": [],
  "out_of_scope": false,
  "reasoning": "Clear reference to Newton's Third Law"
}

Few-Shot Examples:
{{ few_shot_examples }}

Now analyze this student query:
Query: "{{ student_query }}"

Respond with JSON only:
```

## API Endpoints (SuperAdmin)

### 1. List Prompt Templates
```
GET /api/v1/superadmin/prompts
Query params: type, is_active, experiment_name
```

### 2. Get Prompt Template
```
GET /api/v1/superadmin/prompts/{id}
```

### 3. Create Prompt Template
```
POST /api/v1/superadmin/prompts
Body: {
  "prompt_type": "nlu_extraction",
  "name": "NLU Topic Extraction - Gemini 2.5 Optimized",
  "description": "Tuned for Gemini 2.5 Flash conservative behavior",
  "template_text": "...",
  "system_instructions": "...",
  "model_name": "gemini-2.5-flash",
  "temperature": 0.2,
  "guardrails": {...}
}
```

### 4. Update Prompt Template
```
PUT /api/v1/superadmin/prompts/{id}
Body: {partial update}
```

### 5. Activate Prompt Template
```
POST /api/v1/superadmin/prompts/{id}/activate
Body: {
  "traffic_percentage": 100,  // 0-100 for A/B testing
  "deactivate_others": true   // Set other versions to inactive
}
```

### 6. Deactivate Prompt Template
```
POST /api/v1/superadmin/prompts/{id}/deactivate
```

### 7. Create New Version
```
POST /api/v1/superadmin/prompts/{id}/new-version
Body: {
  "changes": {...},
  "change_notes": "Fixed out_of_scope being too conservative"
}
```

### 8. Rollback to Version
```
POST /api/v1/superadmin/prompts/{id}/rollback
```

### 9. Get Prompt Analytics
```
GET /api/v1/superadmin/prompts/{id}/analytics
Query params: start_date, end_date
Response: {
  "usage_count": 1523,
  "success_rate": 0.94,
  "avg_response_time_ms": 1200,
  "guardrail_blocks": 5,
  "confidence_distribution": {...},
  "top_errors": [...]
}
```

### 10. Test Prompt Template
```
POST /api/v1/superadmin/prompts/{id}/test
Body: {
  "input_variables": {
    "student_query": "Explain photosynthesis",
    "grade_level": 10,
    "topics_json": "..."
  }
}
Response: {
  "rendered_prompt": "...",
  "ai_response": {...},
  "guardrail_checks": {...},
  "execution_time_ms": 1150
}
```

## Service Layer Updates

### NLUService Refactoring

```python
class NLUService:
    def __init__(self, ...):
        self.prompt_manager = PromptTemplateManager()

    async def extract_topic(self, ...):
        # Get active prompt template
        template = await self.prompt_manager.get_active_template(
            prompt_type="nlu_extraction"
        )

        # Validate input against guardrails
        input_valid, violations = await self.prompt_manager.validate_input(
            template=template,
            student_query=student_query
        )

        if not input_valid:
            return self._guardrail_blocked_response(violations)

        # Render prompt from template
        prompt = await self.prompt_manager.render_template(
            template=template,
            variables={
                "student_query": student_query,
                "grade_level": grade_level,
                "topics_json": topics_json,
                "recent_topics": recent_topics,
                ...
            }
        )

        # Call AI with template's model config
        response = await self._call_ai_with_template_config(
            prompt=prompt,
            template=template
        )

        # Validate output against guardrails
        output_valid, violations = await self.prompt_manager.validate_output(
            template=template,
            response=response
        )

        if not output_valid:
            return self._guardrail_blocked_response(violations)

        # Log execution for analytics
        await self.prompt_manager.log_execution(
            template_id=template.id,
            input_variables={...},
            response=response,
            success=True
        )

        return response
```

## Migration Strategy

### Phase 1: Schema & Models (Week 1)
1. Create database migration
2. Create SQLAlchemy models
3. Add seed data with current NLU prompt

### Phase 2: Service Layer (Week 1-2)
1. Implement PromptTemplateManager
2. Update NLUService to use templates
3. Add guardrail validation logic
4. Test backward compatibility

### Phase 3: API & SuperAdmin UI (Week 2-3)
1. Implement SuperAdmin API endpoints
2. Add authentication/authorization
3. Create SuperAdmin UI for prompt management
4. Add analytics dashboard

### Phase 4: Testing & Rollout (Week 3-4)
1. A/B test new prompts
2. Monitor performance metrics
3. Gradually increase traffic to new prompts
4. Document best practices

## Immediate Quick Win (For Demo)

Create seed prompt template that fixes the current Gemini 2.5 issue:

```sql
INSERT INTO ai_prompt_templates (
    prompt_type, name, description, template_text,
    model_name, temperature, is_active, version,
    guardrails
) VALUES (
    'nlu_extraction',
    'NLU Topic Extraction - Gemini 2.5 Flash',
    'Optimized for Gemini 2.5 Flash - less conservative on out_of_scope',
    '...template with modified instruction 4...',
    'gemini-2.5-flash',
    0.2,
    true,
    1,
    '{
      "input_validation": {"max_length": 1000, "min_length": 3},
      "output_validation": {
        "required_fields": ["confidence", "topic_id", "clarification_needed", "out_of_scope"]
      }
    }'::jsonb
);
```

## Benefits

1. **Agility**: Update prompts without code deployments
2. **Safety**: Guardrails prevent prompt injection and inappropriate content
3. **Observability**: Track prompt performance and user satisfaction
4. **Experimentation**: A/B test prompts to optimize quality
5. **Governance**: Version control and audit trail for compliance
6. **Cost Control**: Rate limiting and token budgets
7. **Multi-Model**: Easy to test different AI models

## Future Enhancements

1. **Prompt Marketplace**: Share successful prompts across organizations
2. **Auto-Optimization**: ML-driven prompt improvement suggestions
3. **Multi-Language**: Template translations
4. **Chain-of-Thought**: Support for multi-step prompt chains
5. **Fine-Tuning Integration**: Export successful prompts for model fine-tuning
