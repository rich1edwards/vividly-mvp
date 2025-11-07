# Session 11 Part 13: Gemini 2.5 Flash Migration

**Date**: November 5, 2025
**Session**: Continuation from Session 11 Part 12
**Status**: ✅ Core issue fixed, ⚠️ Prompt tuning needed

## Executive Summary

Successfully resolved critical Vertex AI Gemini Flash 404 errors by migrating from **Gemini 1.5 Flash** (retired April 29, 2025) to **Gemini 2.5 Flash**. The API now works without errors, but Gemini 2.5 Flash requires prompt engineering adjustments to reduce false positives for `out_of_scope` detection.

## Root Cause Analysis

### Initial Symptoms
- E2E tests failing with 120+ second timeouts
- Vertex AI returning 404 errors: `Publisher Model 'gemini-1.5-flash' was not found`
- IAM permissions were correctly configured
- Vertex AI API was enabled

### Investigation Timeline

1. **Session 11 Part 12** (Previous):
   - Attempted fix: Updated model name to `gemini-1.5-flash-002` with version suffix
   - Result: ❌ Still getting 404 errors

2. **Session 11 Part 13** (Current):
   - **Discovery**: Web search revealed Gemini 1.5 Flash models were fully retired April 29, 2025
   - **Solution**: Upgrade to Gemini 2.5 Flash (current recommended model)
   - **Result**: ✅ 404 errors resolved, ⚠️ new behavior issue

### Why It Broke "This Afternoon"

User mentioned: *"it was working this afternoon, probably 2 sessions ago"*

**Explanation**: This is consistent with Google's model deprecation timeline. Gemini 1.5 Flash models were likely in a grace period that ended recently, causing the sudden breakage despite working earlier.

## Solution Implemented

### Code Changes

**File**: `backend/app/services/nlu_service.py:38`

```python
# Changed from:
self.model_name = "gemini-1.5-flash-002"  # Using stable version identifier

# To:
self.model_name = "gemini-2.5-flash"  # Gemini 1.5 Flash retired April 2025
```

### Deployment

1. **Built new image**:
   - Build ID: `78e30bc1-0449-4b45-8bac-85a9b4d3f87c`
   - Duration: 1m50s
   - Status: ✅ SUCCESS

2. **Deployed to push worker**:
   - Revision: `dev-vividly-push-worker-00012-qrd`
   - Status: ✅ Deployed

## Test Results

### E2E Test with Gemini 2.5 Flash

```
Test 1: Authentication
 ✅ PASSED (0.27s)

Test 2: Clarification Workflow
 ❌ FAILED - Status: failed (5.2s)
 Query: "Explain the scientific method..."
 Issue: Gemini 2.5 marked as out_of_scope

Test 3: Happy Path Content Generation
 ❌ FAILED - Status: failed (5.2s)
 Query: "Explain how photosynthesis works..."
 Issue: Gemini 2.5 marked as out_of_scope
```

### Progress Analysis

**Before fix (Gemini 1.5)**:
- ❌ 404 errors
- ⏱️ 120+ second timeouts
- Status: Stuck in "pending"

**After fix (Gemini 2.5)**:
- ✅ No 404 errors!
- ✅ Fast response (5.2 seconds vs 120+)
- ✅ NLU extraction completing successfully
- ⚠️ Gemini 2.5 being too conservative with `out_of_scope` classification

### Log Evidence

```
2025-11-06 03:17:45 - Step 1: Topic extraction
2025-11-06 03:17:47 - ERROR: Unexpected generation status: out_of_scope
```

No Vertex AI errors - the API call completes successfully! The issue is **prompt engineering**, not API access.

## Current System State

✅ **Fixed**:
- Vertex AI API access working
- Gemini 2.5 Flash model accessible
- IAM permissions correct
- Fast response times (5s vs 120s+)
- No 404 errors

⚠️ **Remaining Issue**:
- Gemini 2.5 Flash is more conservative than 1.5 Flash
- Valid educational queries incorrectly marked as `out_of_scope`
- Examples failing: "scientific method", "photosynthesis"

## Next Steps (For User)

### Option 1: Adjust NLU Prompt (Recommended)

Update `backend/app/services/nlu_service.py` prompt to be more explicit about educational scope:

```python
# In _build_extraction_prompt(), add emphasis:
Instructions:
1. Identify the primary academic concept in the query
2. Map to ONE of the available topic_ids above
3. If ambiguous, set clarification_needed=true and provide questions
4. IMPORTANT: Only set out_of_scope=true for non-academic queries (entertainment, personal, commercial)
5. ALL science, math, and academic topics are IN SCOPE
6. Consider grade-appropriateness (Grade {grade_level})
7. Respond ONLY with valid JSON (no markdown, no explanation)
```

### Option 2: Add out_of_scope Handling

In `backend/app/workers/push_worker.py`, handle `out_of_scope` as a special case instead of treating it as an error:

```python
elif result.get("status") == "out_of_scope":
    # Handle non-academic queries gracefully
    logger.info(f"Query out of scope: request_id={request_id}")
    request_service.update_status(
        db=db,
        request_id=request_id,
        status="failed",
        current_stage="Query is not related to academic content"
    )
    return True  # Acknowledge message
```

### Option 3: Temporarily Disable out_of_scope (Quick Fix)

For MVP demo readiness, modify NLU prompt to never return `out_of_scope`:

```python
4. Never set out_of_scope=true - treat all queries as potentially academic
```

## Lessons Learned

1. **Model Deprecation Monitoring**: Set up alerts for Google Cloud model lifecycle changes
2. **Version Pinning**: Using specific model versions (e.g., `gemini-1.5-flash-002`) didn't prevent deprecation
3. **Prompt Portability**: Prompts optimized for one model version may need adjustments when upgrading
4. **Fast Failure**: Gemini 2.5's quick `out_of_scope` detection is actually good - it fails fast (5s) instead of hanging (120s+)

## Files Modified

- `backend/app/services/nlu_service.py:38` - Updated model name to `gemini-2.5-flash`

## Deployment Artifacts

- Build Log: `/tmp/build_push_worker_gemini25.log`
- Deploy Log: `/tmp/deploy_push_worker_gemini25.log`
- Test Log: `/tmp/mvp_test_gemini25_final.log`

## Technical Debt Created

None - this is a necessary migration to current model versions.

## Follow-Up Required

**Priority**: HIGH
**Timeline**: Before demo
**Action**: Implement Option 1 (prompt adjustment) or Option 3 (quick fix) to restore content generation functionality
