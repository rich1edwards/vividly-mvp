# Content Generation Module

**Purpose:** Generate personalized educational content (scripts, audio, video) from student queries

**Token Budget:** ~30K tokens (interface + implementation + tests)

**Status:** ✅ Interface defined, 🚧 Implementation migration in progress

---

## What This Module Does

Transforms a student's question like "Explain photosynthesis with basketball" into personalized educational content:

1. **Script Generation** - Creates engaging educational script
2. **Audio Generation** - Converts script to speech
3. **Video Generation** - Creates visual content (optional, expensive)

## Module Interface

```python
from modules.content_generation import create_content_service, GenerationRequest

# Create service (with dependency injection)
service = create_content_service({
    'vertex_client': vertex_client,
    'storage_client': storage_client,
    # ... other dependencies
})

# Generate content
request = GenerationRequest(
    student_query="Explain photosynthesis with basketball",
    student_id="student_123",
    grade_level=10,
    interest="basketball",
    requested_modalities=["text", "audio"]  # Skip video for cost savings
)

result = await service.generate(request)

# Use result
if result.is_successful:
    script = result.content["script"]
    audio_url = result.content["audio"]["audio_url"]
    cost = result.total_cost_usd  # Track costs
```

## Dependencies

**External Services:**
- Vertex AI (Gemini) - Content generation
- Google Text-to-Speech - Audio generation
- Vertex AI Video - Video generation (optional)
- Google Cloud Storage - Asset storage

**Database Models:**
- `Topic` - Educational topics/standards
- `ContentMetadata` - Generated content records

**Other Modules:**
- `modules/rag` - Retrieval for context (optional)
- `modules/integrations` - External API clients

## Cost Profile

| Modality Combination | Time | Cost | Use Case |
|---------------------|------|------|----------|
| Text only | ~5s | $0.005 | Quick answers, previews |
| Text + Audio | ~15s | $0.017 | Audio learning, accessibility |
| Text + Audio + Video | ~60s | $0.200 | Full multimedia experience |

**Cost Savings:** Text-only saves 97.5% vs full video ($0.005 vs $0.200)

## Architecture

### Pipeline Stages

```
Student Query → NLU → RAG → Script → Audio → Video → Result
                ↓     ↓       ↓       ↓       ↓
                1     2       3       4       5
```

1. **NLU (Natural Language Understanding)** - Parse query intent
2. **RAG (Retrieval)** - Get relevant educational context
3. **Script Generation** - Create educational content
4. **Audio Generation** - Text-to-speech
5. **Video Generation** - Visual content (OPTIONAL based on modalities)

### Key Files

```
modules/content_generation/
├── interface.py          # PUBLIC API (load this in other modules)
├── service.py            # Main orchestration (PRIVATE)
├── steps/
│   ├── nlu.py           # Query understanding
│   ├── rag.py           # Context retrieval
│   ├── script.py        # Script generation
│   ├── audio.py         # Audio generation
│   └── video.py         # Video generation
├── __init__.py          # Module exports
├── README.md            # This file
└── tests/
    └── test_generation.py
```

## Usage Examples

### Example 1: Text-Only Generation (Fast & Cheap)

```python
request = GenerationRequest(
    student_query="What causes seasons?",
    student_id="student_456",
    grade_level=8,
    requested_modalities=["text"]  # Skip audio and video
)

result = await service.generate(request)
# Returns in ~5 seconds, costs $0.005
```

### Example 2: Full Multimedia (Slow & Expensive)

```python
request = GenerationRequest(
    student_query="How do rockets work?",
    student_id="student_789",
    grade_level=11,
    interest="space",
    requested_modalities=["text", "audio", "video"]
)

result = await service.generate(request)
# Returns in ~60 seconds, costs $0.200
```

### Example 3: Audio Learning (Middle Ground)

```python
request = GenerationRequest(
    student_query="Explain osmosis",
    student_id="student_101",
    grade_level=10,
    requested_modalities=["text", "audio"]
)

result = await service.generate(request)
# Returns in ~15 seconds, costs $0.017
```

## Error Handling

```python
result = await service.generate(request)

if result.status == GenerationStatus.FAILED:
    print(f"Generation failed: {result.error}")

elif result.status == GenerationStatus.PARTIAL:
    print(f"Partial success, failed: {result.failed_modalities}")
    # Can still use successfully generated modalities
    if result.has_script:
        use_script(result.content["script"])

elif result.status == GenerationStatus.COMPLETED:
    print("Full success!")
    use_all_content(result.content)
```

## Testing

```bash
# Run module tests (fast, no external dependencies)
pytest backend/modules/content_generation/tests/ -v

# Run with mocked external services
pytest backend/modules/content_generation/tests/ --mock-external

# Run integration tests (slow, uses real Vertex AI)
pytest backend/modules/content_generation/tests/ --integration
```

## Performance

**Target Latencies:**
- Text only: < 10 seconds (p95)
- Text + Audio: < 20 seconds (p95)
- Full video: < 90 seconds (p95)

**Current Performance:** (To be measured after migration)

## Migration Status

- [x] Interface defined (`interface.py`)
- [x] Module structure created
- [ ] Migrate `content_generation_service.py` → `service.py`
- [ ] Extract pipeline steps into separate files
- [ ] Update imports across codebase
- [ ] Write module tests
- [ ] Update API endpoints to use new interface
- [ ] Update worker to use new interface
- [ ] Deploy and validate

**Estimated Migration Time:** 2-3 hours

## Future Enhancements

1. **Streaming Generation** - Return content as it's generated
2. **Caching** - Cache common queries
3. **Batch Generation** - Generate multiple requests in parallel
4. **A/B Testing** - Test different generation prompts
5. **Quality Metrics** - Track content quality scores
6. **Cost Optimization** - Dynamic model selection based on query complexity

---

**Module Owner:** Development Team
**Last Updated:** 2025-11-04
**Status:** Interface defined, implementation migration pending
