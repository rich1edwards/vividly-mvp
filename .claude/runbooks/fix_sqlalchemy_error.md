# Runbook: Fix SQLAlchemy Model Errors

**Module:** Database Models
**Estimated Tokens:** 10-15K
**Estimated Time:** 15-30 minutes
**Difficulty:** Easy

---

## When to Use This Runbook

**Symptoms:**
- Error message contains "SQLAlchemy", "Mapper", "relationship", "failed to initialize"
- Error mentions "failed to locate a name"
- Database queries fail with mapper configuration errors
- ALL database operations blocked (not just one model)

**Example Error:**
```
sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize -
can't proceed with initialization of other mappers. Triggering mapper:
'Mapper[Organization(organizations)]'. Original exception was: When initializing
mapper Mapper[Organization(organizations)], expression 'FeatureFlag' failed to
locate a name ('FeatureFlag').
```

---

## Root Cause Pattern

SQLAlchemy errors follow a consistent pattern:

1. **Model has relationship** to another model
2. **Referenced model doesn't exist** or has issues
3. **SQLAlchemy auto-discovers** all models in `app/models/`
4. **Mapper initialization fails** for the broken model
5. **ALL mappers fail** (cascading failure)
6. **Result:** Database completely unusable

**Key Insight:** ONE broken relationship blocks ENTIRE database.

---

## Investigation Steps

### Step 1: Identify the Erroring Model (2 minutes)

From error message, find:
```
Triggering mapper: 'Mapper[Organization(organizations)]'
                           ^^^^^^^^^^^^
                           This is the problem model
```

### Step 2: Read ONLY the Erroring Model File (3 minutes)

```bash
# Don't grep the whole codebase - go directly to the file
cat backend/app/models/organization.py
```

**Look for:** `relationship(` definitions

### Step 3: Check Each Relationship (5 minutes)

For each `relationship()`, verify:

**Check 1: Does the referenced model exist?**
```python
# In organization.py:
schools = relationship("School", ...)
                       ^^^^^^^^
# Does backend/app/models/school.py exist?
ls backend/app/models/school.py  # If no file → PROBLEM
```

**Check 2: Is foreign key defined correctly?**
```python
# WRONG:
users = relationship("User", foreign_keys="User.organization_id")
                                         ^^^^^^^^^^^^^^^^^^^^^^
                                         String won't work!

# RIGHT:
users = relationship("User", foreign_keys=[organization_id])
                                          ^^^^^^^^^^^^^^^^^^
                                          Column object reference
```

**Check 3: Does back_populates match?**
```python
# In organization.py:
users = relationship("User", back_populates="organization")

# In user.py - must have matching relationship:
organization = relationship("Organization", back_populates="users")
```

---

## Fix Pattern (Choose ONE)

### Option A: Comment Out Broken Relationship (FAST - 2 minutes)

**Use when:** Model is Work-In-Progress, not needed immediately

```python
# Relationships
# TEMPORARY: Commented out - FeatureFlag model doesn't exist yet
# TODO: Implement FeatureFlag model before uncommenting
# feature_flags = relationship(
#     "FeatureFlag",
#     back_populates="organization",
#     cascade="all, delete-orphan",
# )
```

**⚠️ WARNING:** If model has MULTIPLE broken relationships, comment out ALL of them.
Partial fixes don't work - SQLAlchemy will find the next broken one.

### Option B: Disable Entire Model (SAFEST - 1 minute)

**Use when:** Model has multiple issues or is completely WIP

```bash
# Rename file so SQLAlchemy won't discover it
git mv backend/app/models/organization.py \
       backend/app/models/organization.py.disabled

# Add TODO comment
echo "# TODO: Re-enable when dependencies implemented" > \
  backend/app/models/organization.py.disabled.txt
```

**To re-enable later:**
```bash
git mv backend/app/models/organization.py.disabled \
       backend/app/models/organization.py
```

### Option C: Fix the Relationship (THOROUGH - 15-30 minutes)

**Use when:** Model is needed in production NOW

1. **Implement missing model** (e.g., create `feature_flag.py`)
2. **Fix foreign key syntax** (use column object, not string)
3. **Verify back_populates** matches on both sides
4. **Test in Python console:**

```python
from backend.app.models import Organization, FeatureFlag
# If no errors → relationships are valid
```

---

## Deployment Steps

### 1. Make Fix (Option A, B, or C above)

### 2. Commit Immediately

```bash
git add backend/app/models/
git commit -m "Fix SQLAlchemy: Comment out broken Organization.feature_flags relationship

FeatureFlag model doesn't exist, causing mapper initialization to fail.
Commenting out until FeatureFlag is implemented.

Fixes: SQLAlchemy mapper error blocking all DB queries"
```

### 3. Push and Build

```bash
git push

# Trigger build from CLEAN committed code (no local changes)
cd backend
gcloud builds submit --config=cloudbuild.content-worker.yaml
```

### 4. Deploy and Test

```bash
# Update Cloud Run job with new image
gcloud run jobs update dev-vividly-content-worker \
  --region=us-central1 \
  --image=<new-image-digest>

# Test execution
gcloud run jobs execute dev-vividly-content-worker \
  --region=us-central1 \
  --wait
```

### 5. CRITICAL: Validate NO Errors

```bash
# Check logs for SQLAlchemy errors (should be ZERO after fix)
gcloud logging read \
  'resource.type="cloud_run_job" "sqlalchemy"' \
  --freshness=5m \
  --limit=10

# Expected: No new errors with timestamp after deployment
```

---

## Common Mistakes

### ❌ Mistake 1: Commenting Out Only Some Relationships

```python
# BAD: Commented out schools, but left feature_flags
# schools = relationship("School", ...)  # Commented
feature_flags = relationship("FeatureFlag", ...)  # Still active!
```

**Why it fails:** SQLAlchemy will error on feature_flags next.

**Fix:** Comment out ALL broken relationships at once.

### ❌ Mistake 2: Building from Local Source

```python
# BAD: Building while code is modified
git status  # Shows modified files
gcloud builds submit  # Uploads local changes!
```

**Why it fails:** Build uses uncommitted code, not what's in Git.

**Fix:** Stash changes, build from clean commit.

### ❌ Mistake 3: Leaving Model in `__init__.py`

```python
# In backend/app/models/__init__.py:
from app.models.organization import Organization  # BAD if Organization has issues
```

**Why it fails:** Python imports file even if not used.

**Fix:** Remove from __init__.py OR disable model file completely.

---

## Prevention

### Design Rule: "Don't Commit Broken Relationships"

Before committing a model with relationships:

1. ✅ Verify referenced models exist
2. ✅ Test relationship in Python console
3. ✅ Check back_populates on both sides
4. ✅ Use column objects for foreign_keys, not strings

### Code Review Checklist

- [ ] All relationship() references existing models
- [ ] Foreign keys use column objects (not strings)
- [ ] back_populates matches on both sides
- [ ] No circular import issues

---

## Success Criteria

**Fix is successful when:**

- [ ] Build completes without errors
- [ ] Worker executes successfully
- [ ] **NO SQLAlchemy errors in logs**
- [ ] Database queries work normally
- [ ] Other models not affected

**Total Time:** Usually < 30 minutes from discovery to validation

---

## Related Issues

- **Circular Imports:** Use string references in relationships, not direct imports
- **Missing Foreign Keys:** Add Column with ForeignKey to model
- **Mapper Already Configured:** Usually means model imported twice

---

**Session 10 Lesson:** After 3 attempts to comment out relationships individually,
the correct fix was to disable the entire Organization model. When in doubt, disable completely.

**Last Updated:** 2025-11-04
**Tested:** Session 8, 9, 10 (Organization model saga)
