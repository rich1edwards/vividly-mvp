# Session 11 Part 12: Vertex AI Access Investigation - INCOMPLETE

## Critical Discovery

**IAM Permission Grant Was NOT Sufficient!**

Despite granting `roles/aiplatform.user` to the service account, Vertex AI is STILL returning 404 errors.

## E2E Test Results

```
Test 1 (Authentication): ✅ PASSED
Test 2 (Clarification): ❌ FAILED - Timeout (requests stuck in "pending")
Test 3 (Happy Path): ❌ FAILED - Timeout (requests stuck in "pending")
```

## Push Worker Logs Show Ongoing 404 Errors

```
2025-11-06 01:50:40,754 - Gemini API error (attempt 1/3):
404 Publisher Model `projects/vividly-dev-rich/locations/us-central1/publishers/google/models/gemini-1.5-flash`
was not found or your project does not have access to it.
```

**This happened AFTER granting IAM permissions at 01:21 UTC** (over 30 minutes later).

## What Was Verified

1. ✅ Service account is correct: `758727113555-compute@developer.gserviceaccount.com`
2. ✅ IAM role is granted: `roles/aiplatform.user` (confirmed in policy output)
3. ✅ Vertex AI API is enabled: `aiplatform.googleapis.com`
4. ✅ Push worker is processing messages (no more 120s timeouts)
5. ✅ Database enum handling works correctly

## Remaining Blocker

**The model name `gemini-1.5-flash` cannot be accessed, even with correct IAM permissions.**

### Possible Causes

1. **Model Version Issue**: `gemini-1.5-flash` may not be the correct model identifier
   - May need full version like `gemini-1.5-flash-001` or `gemini-1.5-flash-002`
   - Publisher models use different naming than deployed custom models

2. **Region Issue**: Model may not be available in `us-central1`
   - Need to check which regions support Gemini Flash
   - May need to change region or use different model

3. **API Version Issue**: Vertex AI Python SDK may be using outdated model registry
   - May need to update SDK version
   - May need different import path for publisher models

4. **IAM Propagation Delay**: Though unlikely after 30+ minutes
   - Service may need restart to pick up new permissions
   - May need to redeploy push worker

## Next Session Priority Actions

### Option 1: Fix Model Name (RECOMMENDED - Fast)

Check Vertex AI documentation for correct Gemini Flash model identifier:
```bash
# Try these model names in nlu_service.py:
- "gemini-1.5-flash-001"
- "gemini-1.5-flash-002"
- "gemini-flash"
- "models/gemini-1.5-flash"
```

Update `/backend/app/services/nlu_service.py` line 14:
```python
self.model_name = "gemini-1.5-flash-001"  # Try with version suffix
```

### Option 2: Use Gemini Pro Instead (SAFE - Slower/More Expensive)

Update `/backend/app/services/nlu_service.py`:
```python
self.model_name = "gemini-1.5-pro"  # or "gemini-1.5-pro-001"
```

Gemini Pro is:
- More stable (GA product)
- Better documented
- More expensive
- Slower than Flash

### Option 3: Check Region Availability

Try different region if us-central1 doesn't support Gemini Flash:
```python
def __init__(self, project_id: str = None, location: str = "us-east1"):  # Try us-east1
```

### Option 4: Update Vertex AI SDK

The SDK may be outdated:
```bash
pip install --upgrade google-cloud-aiplatform
```

Then rebuild and redeploy push worker.

### Option 5: Verify With Simple Test Script

Create test to isolate the issue:
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="vividly-dev-rich", location="us-central1")

# Try different model names:
for model_name in ["gemini-1.5-flash", "gemini-1.5-flash-001", "gemini-1.5-pro"]:
    try:
        model = GenerativeModel(model_name)
        response = model.generate_content("Test")
        print(f"✅ {model_name} works!")
        break
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")
```

## Andrew Ng Lesson

**"Test the simplest thing first"** - Before complex IAM troubleshooting, verify the model NAME is correct. Publisher model names in Vertex AI often require version suffixes.

## Files Modified This Session

None - all changes were IAM policy updates.

## Commands Used

### Grant IAM Permission
```bash
gcloud projects add-iam-policy-binding vividly-dev-rich \
  --member=serviceAccount:758727113555-compute@developer.gserviceaccount.com \
  --role=roles/aiplatform.user
```

### Run E2E Test
```bash
python3 /Users/richedwards/AI-Dev-Projects/Vividly/scripts/test_mvp_demo_readiness.py
```

### Check Push Worker Logs
```bash
gcloud run services logs read dev-vividly-push-worker \
  --region=us-central1 \
  --project=vividly-dev-rich \
  --limit=100 | grep -i "error\|404"
```

## Recommendation for Next Session

**START HERE**: Try model name `"gemini-1.5-flash-001"` with version suffix. This is the most likely fix and takes <5 minutes to test.

If that doesn't work, escalate to Gemini Pro or investigate region availability.

---

**Status**: IAM permissions granted ✅, but model access still failing ❌. Need to fix model identifier.
