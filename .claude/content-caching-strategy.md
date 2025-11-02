# Content Caching Strategy

## Overview

This document details the content caching strategy that enables efficient content reuse across students while maintaining personalization.

## Cache Key Design

### Composite Cache Key
Generated content is uniquely identified by three dimensions:
1. **topic_id**: The educational topic/concept (e.g., "topic_phys_mech_newton_3")
2. **grade_level**: Student's grade level (9-12)
3. **selected_interest**: The specific interest used in examples (e.g., "basketball")

### Why This Works

**Same Content, Different Students:**
- Student A (Grade 10, interests: ["basketball", "music"]) requests "Newton's Third Law"
- Student B (Grade 10, interests: ["basketball", "gaming", "cooking"]) requests "Newton's Third Law"
- Both students have "basketball" in their interests
- System generates content once using basketball examples
- Both students receive the same cached video

**Different Content for Different Contexts:**
- Student C (Grade 11, interests: ["basketball"]) requests same topic
  - Different grade level → Different content (more advanced)
- Student D (Grade 10, interests: ["music"]) requests same topic
  - Different interest → Different content (music-based examples)

## Cache Lookup Flow

### Before Content Generation

```python
def check_cache_before_generation(topic_id: str, grade_level: int, student_interests: List[str]) -> Optional[ContentMetadata]:
    """
    Check if cached content exists for any of the student's interests.

    Query:
        SELECT * FROM content_metadata
        WHERE topic_id = :topic_id
        AND grade_level = :grade_level
        AND interest_id IN (:student_interest_ids)
        AND status = 'completed'
        ORDER BY view_count DESC  -- Prefer popular content
        LIMIT 1
    """
    pass
```

**Cache Hit Scenario:**
```
Request: topic_phys_mech_newton_3 + grade_10 + student_interests=["basketball", "gaming"]
Cache Query: topic_phys_mech_newton_3 + grade_10 + interest_id IN ("int_basketball", "int_gaming")
Result: Found content with interest_id="int_basketball"
Action: Return cached content immediately ✓
```

**Cache Miss Scenario:**
```
Request: topic_phys_mech_newton_3 + grade_10 + student_interests=["cooking", "art"]
Cache Query: topic_phys_mech_newton_3 + grade_10 + interest_id IN ("int_cooking", "int_art")
Result: No matching content found
Action: Proceed to content generation ↓
```

## Content Generation Flow with Interest Selection

### Step 1: LLM Interest Selection

Pass ALL student interests to Gemini for intelligent selection:

```python
prompt = f"""
You are an educational content generator creating personalized explanations.

TOPIC: {topic_name}
RAG CONTENT: {rag_content}
GRADE LEVEL: {grade_level}
STUDENT INTERESTS: {student_interests}

TASK:
1. Analyze the educational topic and concepts
2. Review all student interests
3. SELECT EXACTLY ONE interest that creates the most natural, meaningful connection to this topic
4. Generate a 2-3 minute script using ONLY the selected interest for examples

RESPONSE FORMAT (JSON):
{{
  "selected_interest": "basketball",
  "reasoning": "Basketball involves forces, motion, and Newton's laws in action",
  "script": "..."
}}
"""
```

**Example LLM Response:**
```json
{
  "selected_interest": "basketball",
  "reasoning": "Newton's Third Law is clearly demonstrated in basketball through dribbling (ball pushes down, floor pushes up) and shooting (hands push ball, ball pushes back on hands)",
  "script": "Imagine you're shooting a basketball..."
}
```

### Step 2: Store with Selected Interest

After successful generation:

```python
content = ContentMetadata(
    content_id=generate_content_id(),
    topic_id="topic_phys_mech_newton_3",
    grade_level=10,
    interest_id="int_basketball",  # The ONE interest selected by LLM
    video_url="gs://...",
    script_content=script,
    status="completed"
)
db.add(content)
db.commit()
```

## Database Schema Requirements

### content_metadata Table Updates

```sql
-- Add grade_level column
ALTER TABLE content_metadata
ADD COLUMN grade_level INTEGER;

-- Add composite index for cache lookups
CREATE INDEX idx_content_cache_key
ON content_metadata(topic_id, grade_level, interest_id)
WHERE status = 'completed';

-- Add index for multi-interest lookups
CREATE INDEX idx_content_topic_grade_interest
ON content_metadata(topic_id, grade_level, interest_id, view_count DESC)
WHERE status = 'completed';
```

### Query Performance

With proper indexes:
- Cache lookup: O(1) with index on (topic_id, grade_level, interest_id)
- Multi-interest query: O(k) where k = number of student interests
- Expected performance: <10ms for cache check

## Cache Metrics and Optimization

### Key Metrics to Track

1. **Cache Hit Rate**: Percentage of requests served from cache
   - Target: >60% after initial content generation phase
   - Formula: `cache_hits / total_requests * 100`

2. **Interest Distribution**: Which interests are most common
   - Helps prioritize content generation
   - Identifies "universal" interests that maximize reuse

3. **Grade-Level Patterns**: Content usage by grade
   - Ensures balanced coverage across grades
   - Identifies grade levels needing more content

### Monitoring Query

```sql
-- Cache hit rate by topic
SELECT
    topic_id,
    COUNT(DISTINCT interest_id) as unique_variants,
    SUM(view_count) as total_views,
    AVG(view_count) as avg_reuse_per_variant
FROM content_metadata
WHERE status = 'completed'
GROUP BY topic_id
ORDER BY total_views DESC;
```

## Content Lifecycle

### 1. Initial Request (Cold Start)
- Student A requests topic with interests ["basketball", "music"]
- Cache miss → Generate new content
- LLM selects "basketball" as best fit
- Content created and cached
- **Result**: 1 content variant exists

### 2. Second Request (Cache Hit)
- Student B requests same topic with interests ["basketball", "gaming"]
- Cache lookup finds content with "basketball" interest
- Serve cached content immediately
- **Result**: No new generation, cache hit

### 3. Third Request (New Variant)
- Student C requests same topic with interests ["cooking", "art"]
- Cache lookup fails (no "cooking" or "art" variants exist)
- Generate new content, LLM selects "cooking"
- Content created and cached
- **Result**: 2 content variants exist

### 4. Mature State
- Topic has 5-7 interest variants covering common interests
- Cache hit rate: 70-80%
- Most students receive cached content
- Occasional new variants for rare interest combinations

## Implementation Checklist

- [ ] Add `grade_level` column to `content_metadata` table
- [ ] Create composite index on `(topic_id, grade_level, interest_id)`
- [ ] Update `ContentMetadata` model to include `grade_level`
- [ ] Implement cache lookup logic in content generation service
- [ ] Update LLM prompt to return selected interest in structured format
- [ ] Store selected interest in `interest_id` field after generation
- [ ] Add cache hit/miss logging for metrics
- [ ] Create dashboard for cache performance monitoring
- [ ] Set up alerts for low cache hit rates

## Benefits

1. **Cost Reduction**: Generate content once, serve to many students
2. **Faster Response**: Cache hits return instantly (vs 2-3 min generation)
3. **Consistent Quality**: Popular content variants are well-tested
4. **Scalability**: System scales horizontally with cache reuse
5. **Resource Efficiency**: Reduces Gemini API calls, TTS usage, rendering time

## Trade-offs

1. **Storage Cost**: Each topic×grade×interest combination stored separately
   - Mitigation: ~5-7 interests are common, total variants per topic: ~30-50
   - Cost: Minimal compared to generation cost savings

2. **Personalization Granularity**: Same content for students with same interest
   - Mitigation: Interest selection is already personalized
   - Benefit: Consistency in educational quality

3. **Content Freshness**: Old cached content may not reflect latest RAG data
   - Mitigation: TTL on cached content (6-12 months)
   - Regeneration cycle for popular content

## Related Files
- Content Generation Service: `app/services/content_generation_service.py`
- Cache Service: `app/services/cache_service.py`
- Content Metadata Model: `app/models/content_metadata.py`
- RAG Pipeline Architecture: `.claude/rag-pipeline-architecture.md`
