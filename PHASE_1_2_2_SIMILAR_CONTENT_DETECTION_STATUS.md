# Phase 1.2.2: Similar Content Detection - Implementation Status

**Started**: Session 12 (current)
**Status**: Backend service implemented ✅, API endpoint and frontend IN PROGRESS

## Overview

Phase 1.2.2 implements similar content detection to help students discover existing relevant videos before generating new content, reducing duplicate content generation and improving content discovery.

## Completed Work

### 1. Backend Similarity Detection Service ✅

**File**: `backend/app/services/content_similarity_service.py` (290 lines)

**Features Implemented**:
- Multi-factor similarity scoring algorithm
- Topic matching (+50 points)
- Subject/Interest matching (+30 points)
- Keyword extraction and matching (+10 points per keyword)
- Recency bonus (+5 points for videos <7 days old)
- Configurable similarity thresholds (high: 60+, medium: 40-59)
- Filtering by completion status (only completed videos)
- Student-owned content boost (+5 points)

**Algorithm Details**:
```python
# Scoring weights (matches frontend RelatedVideosSidebar.tsx)
TOPIC_MATCH_SCORE = 50
SUBJECT_MATCH_SCORE = 30
KEYWORD_MATCH_SCORE = 10  # per keyword
RECENCY_BONUS_SCORE = 5

# Thresholds
HIGH_SIMILARITY_THRESHOLD = 60  # Very likely duplicate
MEDIUM_SIMILARITY_THRESHOLD = 40  # Related content
```

**Key Methods**:
- `calculate_similarity_score(content_a, content_b)` - Core scoring algorithm
- `_extract_keywords(text)` - NLP keyword extraction with stop-word filtering
- `find_similar_content(db, topic_id, interest, student_query, student_id, limit=5)` - Main search method
- `format_similarity_result(result)` - API response formatting
- `get_similarity_service()` - Singleton accessor

**Database Optimization**:
- Pre-filters by topic_id before scoring (reduces candidates)
- Only queries completed, non-archived content
- Limits results to top 5 by default

## Remaining Work

### 2. Pydantic Schemas for API (TODO)

**File**: `backend/app/schemas/content.py` (append to existing)

**Required Schemas**:
```python
class SimilarContentRequest(BaseModel):
    """Request to find similar content."""
    topic_id: Optional[str]
    interest: Optional[str]
    student_query: Optional[str]
    limit: int = Field(default=5, ge=1, le=10)

class SimilarContentItem(BaseModel):
    """Single similar content item."""
    content_id: str
    cache_key: str
    title: str
    description: Optional[str]
    topic_id: str
    topic_name: str
    interest: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    created_at: str
    views: int
    average_rating: Optional[float]
    similarity_score: int
    similarity_level: str  # "high" | "medium"
    is_own_content: bool

class SimilarContentResponse(BaseModel):
    """Response with list of similar content."""
    similar_content: List[SimilarContentItem]
    total_found: int
    has_high_similarity: bool  # True if any item has score >= 60
```

### 3. Backend API Endpoint (TODO)

**File**: `backend/app/api/v1/endpoints/content.py` (add endpoint)

**Endpoint Specification**:
- **Route**: `POST /api/v1/content/check-similar`
- **Authentication**: Required (current_user)
- **Request Body**: SimilarContentRequest
- **Response**: SimilarContentResponse (200 OK)
- **Error Handling**: 400 Bad Request, 500 Internal Server Error

**Implementation**:
```python
@router.post("/check-similar", response_model=SimilarContentResponse)
async def check_similar_content(
    request: SimilarContentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check for similar existing content before generating new content.

    Helps students discover relevant existing videos and reduces
    unnecessary duplicate content generation.
    """
    try:
        similarity_service = get_similarity_service()

        similar_results = similarity_service.find_similar_content(
            db=db,
            topic_id=request.topic_id,
            interest=request.interest,
            student_query=request.student_query,
            student_id=current_user.user_id,
            limit=request.limit
        )

        formatted_results = [
            similarity_service.format_similarity_result(result)
            for result in similar_results
        ]

        has_high_similarity = any(
            item["similarity_score"] >= similarity_service.HIGH_SIMILARITY_THRESHOLD
            for item in formatted_results
        )

        return SimilarContentResponse(
            similar_content=formatted_results,
            total_found=len(formatted_results),
            has_high_similarity=has_high_similarity
        )

    except Exception as e:
        logger.error(f"Failed to check similar content: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check for similar content"
        )
```

### 4. Backend Unit Tests (TODO)

**File**: `backend/tests/test_content_similarity_service.py` (new file)

**Test Coverage Required**:
- Test similarity scoring algorithm with various inputs
- Test keyword extraction (including stop-word filtering)
- Test database queries (mocked)
- Test threshold classification (high/medium/low)
- Test student-owned content boost
- Test empty results handling
- Test error handling

**Example Test Structure**:
```python
def test_calculate_similarity_score_exact_match():
    """Test scoring when topic and interest match exactly."""
    service = ContentSimilarityService()

    content_a = {
        "topic_id": "topic_123",
        "interest": "basketball",
        "student_query": "photosynthesis in plants"
    }

    content_b = Mock(
        topic_id="topic_123",
        interest="basketball",
        title="Photosynthesis explained using plants",
        description="How plants make food",
        created_at=datetime.utcnow()
    )

    score = service.calculate_similarity_score(content_a, content_b)

    # Topic (50) + Interest (30) + Keywords (2*10) + Recency (5) = 105
    assert score >= 100
```

### 5. Frontend API Client Update (TODO)

**File**: `frontend/src/api/content.ts`

**Add Method**:
```typescript
export const checkSimilarContent = async (params: {
  topic_id?: string;
  interest?: string;
  student_query?: string;
  limit?: number;
}): Promise<SimilarContentResponse> => {
  const response = await apiClient.post('/api/v1/content/check-similar', params);
  return response.data;
};

export interface SimilarContentItem {
  content_id: string;
  cache_key: string;
  title: string;
  description?: string;
  topic_id: string;
  topic_name: string;
  interest?: string;
  video_url?: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  created_at: string;
  views: number;
  average_rating?: number;
  similarity_score: number;
  similarity_level: 'high' | 'medium';
  is_own_content: boolean;
}

export interface SimilarContentResponse {
  similar_content: SimilarContentItem[];
  total_found: number;
  has_high_similarity: boolean;
}
```

### 6. SimilarContentBanner Component (TODO)

**File**: `frontend/src/components/SimilarContentBanner.tsx` (new file, ~200 lines)

**Features**:
- Displays when similar content detected (similarity >= 40)
- Shows top 3 similar videos with thumbnails
- "Watch Existing Video" button for each item
- "Generate New Version Anyway" button to dismiss
- Different styling for high similarity (warning) vs medium (info)
- Dismissible with X button
- Mobile-responsive grid layout
- Accessibility (ARIA labels, keyboard navigation)

**Component Structure**:
```tsx
export interface SimilarContentBannerProps {
  similarContent: SimilarContentItem[];
  hasHighSimilarity: boolean;
  onWatchVideo: (cacheKey: string) => void;
  onGenerateAnyway: () => void;
  onDismiss: () => void;
}

export const SimilarContentBanner: React.FC<SimilarContentBannerProps> = ({
  similarContent,
  hasHighSimilarity,
  onWatchVideo,
  onGenerateAnyway,
  onDismiss
}) => {
  // Implementation
};
```

### 7. ContentRequestForm Integration (TODO)

**File**: `frontend/src/pages/student/ContentRequestForm.tsx`

**Changes Required**:
1. Add state for similar content detection
2. Call `checkSimilarContent` API when form fields change (debounced)
3. Show SimilarContentBanner when similar content found
4. Handle "Watch Existing Video" navigation
5. Handle "Generate Anyway" dismissal

**Implementation Approach**:
```tsx
const [similarContent, setSimilarContent] = useState<SimilarContentItem[]>([]);
const [showSimilarBanner, setShowSimilarBanner] = useState(false);
const [checkingSimilar, setCheckingSimilar] = useState(false);

// Debounced similarity check
const checkForSimilarContent = useMemo(
  () =>
    debounce(async (topic_id, interest, student_query) => {
      if (!topic_id && !student_query) return;

      setCheckingSimilar(true);
      try {
        const result = await contentApi.checkSimilarContent({
          topic_id,
          interest,
          student_query,
          limit: 3
        });

        if (result.total_found > 0) {
          setSimilarContent(result.similar_content);
          setShowSimilarBanner(true);
        } else {
          setSimilarContent([]);
          setShowSimilarBanner(false);
        }
      } catch (error) {
        console.error('Failed to check similar content:', error);
      } finally {
        setCheckingSimilar(false);
      }
    }, 500),
  []
);

// Trigger check when form fields change
useEffect(() => {
  checkForSimilarContent(formData.topic_id, formData.interest, formData.student_query);
}, [formData.topic_id, formData.interest, formData.student_query]);
```

### 8. E2E Tests (TODO)

**File**: `tests/e2e/test_similar_content_detection.spec.ts` (new file)

**Test Scenarios**:
1. Similar content detected - shows banner
2. No similar content - no banner shown
3. Click "Watch Existing Video" - navigates to video player
4. Click "Generate Anyway" - dismisses banner and proceeds
5. High similarity warning display
6. Medium similarity info display

### 9. GitHub Actions CI/CD Test (TODO)

**File**: `.github/workflows/test-similar-content.yml` (new file)

**Workflow**:
- Run on PR to main
- Execute backend unit tests
- Execute E2E tests
- Upload test reports as artifacts

## Architecture Decisions

### Why This Algorithm?

1. **Matches Frontend Pattern**: Uses same weights as `RelatedVideosSidebar.tsx` for consistency
2. **Multi-Factor Scoring**: Considers topic, interest, keywords, and recency
3. **Keyword Extraction**: Simple but effective stop-word filtering
4. **Database Efficiency**: Pre-filters by topic before scoring
5. **Tunable Thresholds**: Easy to adjust HIGH/MEDIUM cutoffs

### Future Enhancements

1. **Advanced NLP**: Replace keyword extraction with TF-IDF or embeddings
2. **Personalization**: Factor in student's viewing history
3. **Collaborative Filtering**: "Students who watched X also watched Y"
4. **Caching**: Cache similarity scores for frequently requested topics
5. **A/B Testing**: Test different threshold values
6. **Analytics**: Track how often similar content is used vs new generation

## Testing Strategy

### Unit Tests
- Similarity scoring algorithm correctness
- Keyword extraction edge cases
- Database query construction
- Error handling

### Integration Tests
- API endpoint with real database
- Service + database interaction
- Authentication + authorization

### E2E Tests
- Full user flow: form → similar content banner → watch video
- Full user flow: form → similar content banner → generate anyway
- Mobile responsiveness
- Accessibility

## Performance Considerations

1. **Database Indexing**: Ensure indexes on `topic_id`, `status`, `archived`
2. **Query Optimization**: Limit candidate pool with WHERE clauses
3. **Debouncing**: Frontend debounces API calls (500ms)
4. **Caching**: Consider Redis cache for hot topics

## Monitoring & Metrics

### Key Metrics to Track
- Similar content detection rate (% of requests with results)
- High similarity rate (% with score >= 60)
- User action distribution:
  - Watch existing video (conversion)
  - Generate anyway (override)
  - Dismiss banner (ignore)
- Performance: API response time for similarity check
- Error rate: Failed similarity checks

### Logging
- Log all similarity checks with scores
- Log user actions (watch/generate/dismiss)
- Log errors with full context

## Next Steps

1. ✅ Complete Pydantic schemas
2. ✅ Implement API endpoint
3. ✅ Write backend unit tests
4. ✅ Update frontend API client
5. ✅ Create SimilarContentBanner component
6. ✅ Integrate into ContentRequestForm
7. ✅ Write E2E tests
8. ✅ Add GitHub Actions workflow
9. ✅ Test end-to-end in dev environment
10. ✅ Deploy to production
11. ✅ Monitor metrics and iterate

## Files Modified/Created

### Backend
- ✅ `backend/app/services/content_similarity_service.py` (NEW, 290 lines)
- ⏳ `backend/app/schemas/content.py` (UPDATE, add 3 schemas)
- ⏳ `backend/app/api/v1/endpoints/content.py` (UPDATE, add 1 endpoint)
- ⏳ `backend/tests/test_content_similarity_service.py` (NEW, ~200 lines)

### Frontend
- ⏳ `frontend/src/api/content.ts` (UPDATE, add 1 method + 2 interfaces)
- ⏳ `frontend/src/components/SimilarContentBanner.tsx` (NEW, ~200 lines)
- ⏳ `frontend/src/pages/student/ContentRequestForm.tsx` (UPDATE, add similar content detection)

### Testing
- ⏳ `tests/e2e/test_similar_content_detection.spec.ts` (NEW, ~150 lines)
- ⏳ `.github/workflows/test-similar-content.yml` (NEW, ~50 lines)

### Documentation
- ✅ `PHASE_1_2_2_SIMILAR_CONTENT_DETECTION_STATUS.md` (THIS FILE)
- ⏳ `FRONTEND_UX_IMPLEMENTATION_PLAN.md` (UPDATE, mark Phase 1.2.2 complete)

---

**Total Estimated Lines of Code**: ~1,090 lines
**Completion**: ~26% (290/1090 lines)
**Next Session**: Complete remaining backend work, then frontend components
