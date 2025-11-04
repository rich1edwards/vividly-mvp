# Architecture for Sustainable Claude-Driven Development

**Author:** Andrew Ng's Systematic Methodology
**Date:** 2025-11-04
**Problem:** Context window exhaustion preventing effective development
**Solution:** Modular architecture + session-based workflow

---

## The Fundamental Problem

### Current State
- **Codebase Size:** ~100 files, growing rapidly
- **Context Consumption:** 90K+ tokens per debugging session
- **Session Pattern:** Deep debugging → context overflow → lost state
- **Result:** Cannot complete complex tasks in single session

### Root Cause Analysis

**Why Context Explodes:**
1. **Monolithic Investigation:** Reading entire files to find one issue
2. **Historical Baggage:** Loading session notes from previous work
3. **Broad Search:** Grepping entire codebase for patterns
4. **Deep Stacks:** Following error traces through multiple layers
5. **Documentation Overhead:** Creating comprehensive handoff docs

**This is NOT a bug - it's a feature.** Complex systems require complex context.

---

## The Andrew Ng Solution: "Divide and Conquer with Interfaces"

### Core Principle
> "If you can't hold the entire system in context, design the system so you don't have to."

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Layer 1: CONTRACTS                       │
│  (Interfaces, Schemas, API Specs - NEVER CHANGE)            │
│  - Small, focused, well-documented                           │
│  - Can be loaded in <5K tokens                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                Layer 2: INDEPENDENT MODULES                  │
│  (Each module < 30K tokens, can be understood in isolation)  │
│  - Content Generation Module                                 │
│  - RAG/Retrieval Module                                      │
│  - User Management Module                                    │
│  - Worker/Queue Module                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│             Layer 3: INTEGRATION & ORCHESTRATION             │
│  (Thin layer, delegates to modules via contracts)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Immediate Restructuring Plan

### Phase 1: Create Module Boundaries (Week 1)

#### 1.1 Define Modules

**Modules to Create:**
```
backend/
├── modules/
│   ├── content_generation/   # Video/Audio/Script generation
│   ├── rag/                   # Retrieval-Augmented Generation
│   ├── user_auth/             # Authentication & Authorization
│   ├── request_tracking/      # Request lifecycle management
│   ├── worker/                # Background job processing
│   └── integrations/          # External APIs (Vertex AI, GCS, etc.)
```

**Each Module Has:**
```
module_name/
├── README.md              # What it does, dependencies, contract
├── interface.py           # Public API (the contract)
├── service.py             # Implementation
├── models.py              # Database models (if any)
├── tests/                 # Module-specific tests
└── __init__.py            # Expose only interface
```

#### 1.2 Module Contracts (Interfaces)

**Example: Content Generation Module**

```python
# modules/content_generation/interface.py
"""
Content Generation Module Contract

DEPENDENCIES: None (receives data, returns result)
EXTERNAL CALLS: Vertex AI (for generation), GCS (for storage)
DATABASE: Reads topics, writes content_metadata
"""

from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class GenerationRequest:
    """Input contract - what the module needs"""
    student_query: str
    student_id: str
    grade_level: int
    interest: Optional[str] = None
    requested_modalities: List[str] = ["video"]

@dataclass
class GenerationResult:
    """Output contract - what the module returns"""
    status: str  # "completed", "failed"
    content: Dict[str, Any]  # script, audio, video
    metadata: Dict[str, Any]  # timestamps, costs, etc.
    error: Optional[str] = None

class ContentGenerationInterface:
    """
    The ONLY way to interact with content generation.
    Implementation details are hidden.
    """
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request"""
        raise NotImplementedError
```

**Key Insight:** Claude can load ONLY this interface file (<500 tokens) and understand how to use the module WITHOUT reading implementation.

### Phase 2: Session-Based Development Workflow

#### 2.1 Pre-Session Prep (You Do This)

**Before starting Claude session:**

1. **Identify the module** you want to work on
2. **Create a focused task file:**

```markdown
# TASK: Fix Content Generation Text-Only Mode
## Module: content_generation
## Files Needed:
- modules/content_generation/interface.py (contract)
- modules/content_generation/service.py (implementation)
- modules/content_generation/README.md (docs)

## Context from Previous Session:
- Dual modality feature added in Phase 1B
- Text-only should skip video generation
- Need to verify cost savings logging

## Success Criteria:
1. Text-only requests skip video generation
2. Logs show "$0.183 saved" message
3. Tests pass
4. No regression in video mode
```

3. **Start Claude with focused prompt:**
```
"Load module: content_generation
Task file: TASK_CONTENT_GENERATION_TEXT_MODE.md
Use ONLY files in modules/content_generation/
Do NOT load other modules or session history"
```

#### 2.2 Session Types (Different Modes)

**Type A: Single Module Development**
- Load: 1 module (contract + implementation + tests)
- Context: ~20-30K tokens
- Duration: Full session available for work
- Use for: Feature implementation, bug fixes

**Type B: Module Integration**
- Load: 2-3 module contracts (interfaces only, not implementations)
- Load: Integration layer code
- Context: ~15-20K tokens
- Use for: Connecting modules, API endpoints

**Type C: Investigation/Debugging**
- Load: Error logs + affected module
- Use: Grep/Read tools to locate issue
- Create: Minimal fix in focused area
- Context: ~30-40K tokens

**Type D: Architecture Review**
- Load: All module READMEs + interfaces
- No implementation code
- Context: ~10-15K tokens
- Use for: Planning, design decisions

### Phase 3: Development Runbooks

#### 3.1 Common Task Runbooks

**Runbook: Add New API Endpoint**

```markdown
# Runbook: Add New API Endpoint

## Module: API Layer
## Estimated Tokens: 15K
## Estimated Time: 30 minutes

### Steps:
1. Load: backend/app/api/v1/endpoints/ (relevant file)
2. Load: Pydantic schema for request/response
3. Load: Service interface that endpoint will call
4. Implement: Endpoint function (10-20 lines)
5. Test: Integration test
6. Update: API documentation

### Files Touched: 3-4 maximum
### Context Budget: Safe for full session
```

**Runbook: Fix SQLAlchemy Model Error**

```markdown
# Runbook: Fix SQLAlchemy Model Error

## Module: Database Models
## Estimated Tokens: 10-15K
## Estimated Time: 20 minutes

### Pattern Recognition:
- Error mentions "Mapper", "relationship", "failed to locate"
  → Missing or incorrect model relationship

### Investigation Steps:
1. Read ONLY the erroring model file (e.g., organization.py)
2. Check relationship definitions
3. Verify referenced models exist
4. Check foreign key columns exist in database

### Fix Pattern:
- Comment out broken relationship
- Add TODO with explanation
- Commit immediately
- Build and deploy
- Validate in logs

### Files Touched: 1-2 maximum
### Context Budget: Very safe
```

#### 3.2 Runbook Library Location

```
PROJECT_ROOT/
├── .claude/
│   ├── runbooks/
│   │   ├── add_api_endpoint.md
│   │   ├── fix_sqlalchemy_error.md
│   │   ├── add_new_feature.md
│   │   ├── deploy_to_production.md
│   │   └── investigate_worker_failure.md
│   ├── modules/
│   │   └── (metadata about each module)
│   └── session_templates/
│       └── (starter prompts for different session types)
```

---

## Migration Strategy: Refactor Incrementally

### Week 1: Foundation
- [ ] Create `backend/modules/` directory structure
- [ ] Write interface files for 5 main modules
- [ ] Write README for each module
- [ ] NO implementation changes yet (just organization)

### Week 2: Content Generation Module
- [ ] Move content_generation_service.py → modules/content_generation/service.py
- [ ] Create interface.py with clean contracts
- [ ] Update imports across codebase
- [ ] Tests still pass

### Week 3: RAG Module
- [ ] Move rag_service.py → modules/rag/service.py
- [ ] Extract retrieval logic into focused module
- [ ] Separate embeddings, vector search, ranking

### Week 4: Worker Module
- [ ] Move content_worker.py → modules/worker/worker.py
- [ ] Create worker interface (pub/sub abstraction)
- [ ] Module can be tested independently

### Week 5-6: Remaining Modules
- [ ] User Auth module
- [ ] Request Tracking module
- [ ] Integrations module (Vertex AI, GCS, etc.)

### Week 7: Integration Layer
- [ ] Thin API layer that delegates to modules
- [ ] Thin worker layer that delegates to modules
- [ ] All business logic in modules

### Week 8: Documentation & Runbooks
- [ ] Complete runbook library
- [ ] Module dependency map
- [ ] Session templates for common tasks

---

## Technical Implementation Details

### Module Interface Pattern

```python
# modules/{module_name}/__init__.py
"""
Expose ONLY the interface, hide implementation details
"""
from .interface import (
    {Module}Interface,
    {Module}Request,
    {Module}Result,
)
from .service import {Module}Service

# Factory function for dependency injection
def create_{module}_service(dependencies: Dict) -> {Module}Interface:
    """
    Create module service with dependencies.
    This is the ONLY way to instantiate the module.
    """
    return {Module}Service(**dependencies)

__all__ = [
    "{Module}Interface",
    "{Module}Request",
    "{Module}Result",
    "create_{module}_service",
]

# DO NOT EXPORT: service.py, models.py, internal helpers
```

### Session State Management

**Problem:** Claude forgets context between sessions
**Solution:** Structured state files

```
.claude/state/
├── current_session.json        # Active session metadata
├── module_status.json          # Which modules are stable/WIP
├── known_issues.json           # Open bugs/tech debt
└── deployment_history.json     # Last 10 deployments
```

**Example: current_session.json**
```json
{
  "session_id": "session_10",
  "started_at": "2025-11-04T02:43:00Z",
  "module_focus": "content_generation",
  "task": "Fix SQLAlchemy mapper errors",
  "files_modified": [
    "backend/app/models/organization.py"
  ],
  "commits_created": [
    "4291f22"
  ],
  "builds_triggered": [
    "a879e323"
  ],
  "next_steps": [
    "Validate no SQLAlchemy errors in logs",
    "Test dual modality text-only feature",
    "Apply database migration"
  ],
  "blocking_issues": []
}
```

**Loading State in New Session:**
```
"Claude, load session state from .claude/state/current_session.json
Continue from where we left off."
```

---

## Context Budget Management

### Token Allocation Strategy

**Total Budget:** 200K tokens (Claude 3.5 Sonnet)
**Reserve:** 50K tokens for responses/reasoning
**Usable:** 150K tokens for context

**Allocation:**
```
System Prompts:           5K tokens   (3%)
Session State:           10K tokens   (7%)
Module Interface:         5K tokens   (3%)
Module Implementation:   30K tokens  (20%)
Tests:                   10K tokens   (7%)
Working Memory:          40K tokens  (27%)
Documentation:           10K tokens   (7%)
Error Context:           20K tokens  (13%)
Buffer:                  20K tokens  (13%)
────────────────────────────────────────
Total:                  150K tokens (100%)
```

### Red Flags (Stop and Refactor)

**If you see these patterns, STOP and refactor:**

1. **Reading 10+ files to understand one feature**
   → Module boundaries are wrong

2. **Grep returning 50+ matches across codebase**
   → Abstraction is missing

3. **Error stack trace crosses 5+ modules**
   → Too much coupling

4. **Can't explain module in <500 words**
   → Module is too complex

5. **Tests require mocking 8+ dependencies**
   → Module has too many responsibilities

---

## Specific Fixes for Current Codebase

### Immediate Actions (This Week)

#### 1. Extract Content Generation Module

**Current:** Monolithic `content_generation_service.py` (800+ lines)

**Target Structure:**
```
modules/content_generation/
├── interface.py           # Contract (<100 lines)
├── service.py            # Orchestration (<200 lines)
├── steps/
│   ├── nlu.py           # Query understanding
│   ├── rag.py           # Context retrieval
│   ├── script.py        # Script generation
│   ├── audio.py         # Audio generation
│   └── video.py         # Video generation
└── tests/
```

**Benefits:**
- Each step file < 150 lines
- Can work on video generation without loading audio code
- Tests are focused and fast
- Easy to add new modalities

#### 2. Separate Database Models from Business Logic

**Current:** Models mixed with services, circular dependencies

**Target:**
```
modules/data/
├── models/              # SQLAlchemy models ONLY
│   ├── user.py
│   ├── content.py
│   └── request.py
├── repositories/        # Database access layer
│   ├── user_repo.py
│   └── content_repo.py
└── schemas/             # Pydantic schemas for API
    └── ...
```

**Rule:** Services never import SQLAlchemy models directly. They use repositories.

#### 3. Worker as Thin Orchestrator

**Current:** `content_worker.py` contains business logic

**Target:**
```python
# modules/worker/worker.py (THIN - <150 lines)
async def process_message(message: PubSubMessage):
    """Worker only orchestrates, doesn't implement"""

    # Parse message
    request = parse_content_request(message)

    # Delegate to module
    from modules.content_generation import create_content_service
    service = create_content_service(get_dependencies())
    result = await service.generate(request)

    # Handle result
    await save_result(result)
```

**Benefits:**
- Worker is trivial to understand
- Business logic is in modules (testable)
- Can test content generation without Pub/Sub

---

## Development Workflow Examples

### Example 1: "Add Text+Image Modality"

**Session Type:** Single Module Development
**Module:** content_generation
**Context Budget:** 30K tokens

**Session Plan:**
```markdown
1. Load: modules/content_generation/interface.py
2. Load: modules/content_generation/steps/image.py (create if needed)
3. Task: Implement image generation step
4. Test: In module tests (no integration needed yet)
5. Commit: "Add image generation step to content module"

DO NOT load: Worker code, API code, other modules
Integration will be separate session
```

### Example 2: "Fix RAG Retrieval Bug"

**Session Type:** Investigation/Debugging
**Module:** rag
**Context Budget:** 25K tokens

**Session Plan:**
```markdown
1. Load: Error logs (recent failures)
2. Load: modules/rag/interface.py (understand contract)
3. Load: modules/rag/retrieval.py (implementation)
4. Identify: Bug in vector search logic
5. Fix: Update retrieval.py ONLY
6. Test: Module tests
7. Commit: "Fix vector search scoring in RAG module"

DO NOT: Investigate how RAG is called (not relevant to bug)
DO NOT: Look at content generation (separate concern)
```

### Example 3: "Deploy New Feature to Production"

**Session Type:** Deployment
**Module:** None (orchestration task)
**Context Budget:** 15K tokens

**Session Plan:**
```markdown
1. Load: Runbook: deploy_to_production.md
2. Load: .claude/state/deployment_history.json
3. Execute: Deployment steps from runbook
4. Validate: Health checks
5. Monitor: Error logs for 10 minutes
6. Update: deployment_history.json

DO NOT: Read feature code (already tested)
DO NOT: Make code changes (deployment only)
```

---

## Success Metrics

### Module Quality Metrics

**Good Module:**
- Interface file < 200 lines
- Implementation < 500 lines per file
- Can be explained in README < 1000 words
- < 5 direct dependencies
- > 80% test coverage
- Can be understood in < 20K tokens

**Bad Module (Needs Refactoring):**
- Interface unclear or missing
- Single file > 1000 lines
- README is vague or missing
- > 10 dependencies
- < 50% test coverage
- Requires > 40K tokens to understand

### Session Efficiency Metrics

**Effective Session:**
- Completes defined task
- < 60% context usage
- Creates < 3 commits
- Touches < 5 files
- Clear handoff for next session

**Ineffective Session (Refactor Needed):**
- Runs out of context
- Touches > 10 files
- Creates > 5 commits
- "Just needs one more thing" repeatedly
- Unclear what was accomplished

---

## Long-Term Vision

### 6 Months from Now

**Codebase Structure:**
```
✅ 12 well-defined modules
✅ Each module < 30K tokens
✅ 90% of work happens in single module
✅ Clear contracts between all modules
✅ Comprehensive runbook library
✅ Session templates for all common tasks
```

**Development Workflow:**
```
✅ Sessions complete in < 50% context budget
✅ Most bugs fixed in < 15 minutes
✅ Features added without touching core
✅ Onboarding new Claude session takes < 5 minutes
✅ Technical debt is contained to specific modules
```

**Quality Metrics:**
```
✅ 95%+ test coverage per module
✅ Zero cross-module imports (only interfaces)
✅ Deployment takes < 10 minutes
✅ Rollback takes < 2 minutes
✅ New feature development: 1-2 sessions average
```

---

## Implementation Priority

### This Week (Critical)

1. **Create module directory structure** ✅ Quick win
2. **Write 5 module interface files** ✅ Forces clarity
3. **Create 3 key runbooks** ✅ Immediate productivity boost
4. **Extract content_generation module** ✅ Biggest pain point

### Next Week (Important)

5. **Extract RAG module** ✅ Second biggest pain point
6. **Extract worker module** ✅ Simplifies debugging
7. **Create session state system** ✅ Better handoffs
8. **Write module READMEs** ✅ Documentation

### Month 2 (Valuable)

9. **Extract remaining modules** ✅ Complete modularization
10. **Build integration tests** ✅ Confidence in refactoring
11. **Create module dependency map** ✅ Visualization
12. **Expand runbook library** ✅ Cover all common tasks

---

## Conclusion: The Andrew Ng Way

### Core Philosophy

> "Good architecture isn't about clever abstractions. It's about making it EASY to do the RIGHT thing and HARD to do the WRONG thing."

**In practice:**
- ✅ Easy: Work on single module in isolation
- ✅ Easy: Understand what module does from interface
- ✅ Easy: Test module without integration
- ✅ Easy: Deploy module changes independently
- ❌ Hard: Create circular dependencies
- ❌ Hard: Mix concerns across modules
- ❌ Hard: Deploy breaking changes
- ❌ Hard: Write code that's impossible to test

### The Path Forward

**Current State:** Monolithic, context-hungry, hard to navigate
**Target State:** Modular, context-efficient, easy to navigate
**Migration:** Incremental, module by module, no big-bang rewrite

**Next Session Should:**
1. Complete current SQLAlchemy fix validation
2. Create initial module structure
3. Write first 3 module interfaces
4. Extract content_generation module

**This is not a refactoring project. This is building SUSTAINABLE architecture for CONTINUOUS DEVELOPMENT with Claude.**

---

**Document Status:** DRAFT v1
**Next Review:** After module extraction pilot
**Owner:** Development Team
**Methodology:** Andrew Ng's Systematic Approach

**Remember:** "Perfect is the enemy of good. But GOOD is the enemy of TERRIBLE. We need GOOD architecture NOW."
