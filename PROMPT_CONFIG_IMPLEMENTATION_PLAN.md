# Prompt Configuration Implementation Plan

**Date**: November 5, 2025
**Status**: Design Complete, Ready for Implementation

## Two-Track Approach

### Track 1: Immediate Solution (For Demo - 2 hours)
**Goal**: Fix Gemini 2.5 Flash `out_of_scope` issue NOW for demo readiness

**Implementation**:
1. Add simple `PROMPT_TEMPLATES` config in `backend/app/core/config.py`
2. Load templates from environment variables or JSON config file
3. Update NLU service to use configurable prompt
4. Deploy with improved prompt for Gemini 2.5 Flash

**Benefits**:
- ✅ Demo-ready today
- ✅ No database changes required
- ✅ Easy to tweak prompt via environment variables
- ✅ Can be hot-swapped without redeployment (config service)

### Track 2: Full Solution (Post-Demo - 3-4 weeks)
**Goal**: Enterprise-grade prompt management system

**Implementation**: See `PROMPT_CONFIGURATION_DESIGN.md` for full details

**Benefits**:
- SuperAdmin UI for prompt editing
- A/B testing and analytics
- Versioning and rollback
- Guardrails and safety controls

## Immediate Solution - Detailed Implementation

### Step 1: Create Prompt Templates Config (15 min)

**File**: `backend/app/core/prompt_templates.py`

```python
"""
Configurable AI Prompt Templates

For MVP: Load from this file
For Production: Load from database (see PROMPT_CONFIGURATION_DESIGN.md)
"""
import os
import json
from typing import Dict, Any

# Load custom templates from environment if provided
CUSTOM_TEMPLATES_JSON = os.getenv("AI_PROMPT_TEMPLATES_JSON")

DEFAULT_TEMPLATES = {
    "nlu_extraction_gemini_25": {
        "name": "NLU Topic Extraction - Gemini 2.5 Flash",
        "description": "Optimized for Gemini 2.5 Flash - addresses conservative out_of_scope behavior",
        "model_name": "gemini-2.5-flash",
        "temperature": 0.2,
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

    For MVP: Returns hardcoded templates
    TODO: Load from database when prompt management system is implemented

    Args:
        template_key: Template identifier

    Returns:
        Dict containing template configuration
    """
    # Try loading custom templates from environment
    if CUSTOM_TEMPLATES_JSON:
        try:
            custom_templates = json.loads(CUSTOM_TEMPLATES_JSON)
            if template_key in custom_templates:
                return custom_templates[template_key]
        except json.JSONDecodeError:
            pass  # Fall back to defaults

    # Return default template
    return DEFAULT_TEMPLATES.get(template_key, DEFAULT_TEMPLATES["nlu_extraction_gemini_25"])


def render_template(template_key: str, variables: Dict[str, Any]) -> str:
    """
    Render a prompt template with given variables.

    Args:
        template_key: Template identifier
        variables: Dictionary of variables to interpolate

    Returns:
        Rendered prompt string
    """
    template_config = get_template(template_key)
    template_str = template_config["template"]

    # Simple string formatting (use Jinja2 in production)
    return template_str.format(**variables)


def get_model_config(template_key: str) -> Dict[str, Any]:
    """
    Get model configuration for a template.

    Returns:
        Dict with model_name, temperature, etc.
    """
    template_config = get_template(template_key)
    return {
        "model_name": template_config.get("model_name", "gemini-2.5-flash"),
        "temperature": template_config.get("temperature", 0.2),
        "top_p": template_config.get("top_p", 0.8),
        "top_k": template_config.get("top_k", 40),
        "max_output_tokens": template_config.get("max_output_tokens", 512),
    }
```

### Step 2: Update NLU Service (30 min)

**File**: `backend/app/services/nlu_service.py`

```python
# Add import
from app.core.prompt_templates import render_template, get_model_config

# In _build_extraction_prompt method, replace entire method:
def _build_extraction_prompt(
    self,
    student_query: str,
    topics: List[Dict],
    grade_level: int,
    recent_topics: List[str],
    subject_context: Optional[str],
) -> str:
    """Build prompt for Gemini topic extraction using configurable template."""

    # Format topics as JSON for prompt
    topics_json = json.dumps(topics, indent=2)

    # Format recent topics
    recent_str = ", ".join(recent_topics) if recent_topics else "None"

    # Subject context
    subject_str = subject_context if subject_context else "Any STEM subject"

    # Render from template
    prompt = render_template(
        template_key="nlu_extraction_gemini_25",
        variables={
            "student_query": student_query,
            "grade_level": grade_level,
            "topics_json": topics_json,
            "recent_topics": recent_str,
            "subject_context": subject_str,
        }
    )

    return prompt

# In __init__, use template config for model:
def __init__(self, project_id: str = None, location: str = "us-central1"):
    """Initialize NLU service with Vertex AI."""
    self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "vividly-dev-rich")
    self.location = location

    # Get model config from template
    model_config = get_model_config("nlu_extraction_gemini_25")
    self.model_name = model_config["model_name"]

    # Rest of init...
```

### Step 3: Environment Variable Override (Optional)

Create `backend/.env.prompt-templates` for easy testing:

```bash
# Override prompt templates with custom JSON
# Useful for quick tweaks without code changes
AI_PROMPT_TEMPLATES_JSON='{
  "nlu_extraction_gemini_25": {
    "name": "Custom NLU Prompt",
    "model_name": "gemini-2.5-flash",
    "temperature": 0.1,
    "template": "Your custom prompt here with {variables}..."
  }
}'
```

### Step 4: Deploy (30 min)

1. Create `prompt_templates.py` file
2. Update `nlu_service.py` to use templates
3. Build and deploy push worker
4. Test with E2E tests

## Testing Plan

### Unit Tests
```python
def test_prompt_template_rendering():
    """Test that templates render correctly with variables."""
    from app.core.prompt_templates import render_template

    prompt = render_template(
        "nlu_extraction_gemini_25",
        {
            "student_query": "Explain photosynthesis",
            "grade_level": 10,
            "topics_json": "[]",
            "recent_topics": "None",
            "subject_context": "Biology"
        }
    )

    assert "photosynthesis" in prompt.lower()
    assert "10" in prompt
    assert "only set out_of_scope=true for clearly non-academic" in prompt.lower()
```

### Integration Tests
```bash
# Run E2E test after deployment
python3 scripts/test_mvp_demo_readiness.py
```

Expected result:
- ✅ Test 1: Authentication - PASS
- ✅ Test 2: Clarification Workflow - PASS
- ✅ Test 3: Happy Path Content Generation - PASS

## Deployment Commands

```bash
# 1. Build push worker with new template system
cd backend
gcloud builds submit \
  --config=cloudbuild.push-worker.yaml \
  --project=vividly-dev-rich \
  --timeout=15m

# 2. Deploy
gcloud run services update dev-vividly-push-worker \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --image=us-central1-docker.pkg.dev/vividly-dev-rich/vividly/push-worker:latest

# 3. Test
python3 scripts/test_mvp_demo_readiness.py
```

## Migration Path to Full Solution

Once the full prompt management system (Track 2) is implemented:

1. Database migration to create `ai_prompt_templates` table
2. Migrate existing templates from `prompt_templates.py` to database
3. Update `get_template()` function to query database instead of hardcoded dict
4. Add SuperAdmin UI
5. Deprecate `prompt_templates.py` (keep for backward compatibility)

## Success Metrics

**Immediate** (Track 1):
- ✅ E2E tests pass
- ✅ No more `out_of_scope` false positives
- ✅ MVP is demo-ready

**Long-term** (Track 2):
- Prompt update time: 2 minutes (vs 30 minutes deployment)
- A/B test success rate improvement: >10%
- Prompt iteration velocity: 5x faster
- Zero downtime for prompt updates

## Next Steps

1. **Immediate**: Implement Track 1 (2 hours) - Fix for demo
2. **This Week**: Review and approve `PROMPT_CONFIGURATION_DESIGN.md`
3. **Next Sprint**: Implement Track 2 Phase 1 (database schema)
4. **Following Sprints**: Complete Track 2 implementation

Would you like me to proceed with Track 1 implementation now?
