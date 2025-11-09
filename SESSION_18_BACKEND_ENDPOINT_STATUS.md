# Session 18: Backend Endpoint Status for Phase 2.2

**Date**: 2025-01-08
**Status**: Backend endpoints verified and documented
**Action Required**: Update frontend API paths to match backend routes

---

## Executive Summary

The backend already has **most** of the required endpoints for Phase 2.2 (Teacher Class Dashboard) implementation. However, there are **path mismatches** between the frontend API service and the actual backend routes that need to be corrected.

### Backend Endpoints Status

| Endpoint | Frontend Expected | Backend Actual | Status | Notes |
|----------|------------------|----------------|--------|-------|
| Get Teacher Dashboard | `GET /api/v1/teachers/{teacher_id}/dashboard` | `GET /api/v1/teachers/{teacher_id}/dashboard` | ✅ **READY** | Exact match |
| Get Class Details | `GET /api/v1/classes/{class_id}` | `GET /api/v1/classes/{class_id}` | ✅ **READY** | Exact match |
| Update Class | `PATCH /api/v1/classes/{class_id}` | `PATCH /api/v1/classes/{class_id}` | ✅ **READY** | Exact match |
| Archive Class | `DELETE /api/v1/classes/{class_id}` | `DELETE /api/v1/classes/{class_id}` | ✅ **READY** | Exact match |
| Get Class Roster | `GET /api/v1/classes/{class_id}/students` | `GET /api/v1/classes/{class_id}/students` | ✅ **READY** | Exact match |
| Remove Student | `DELETE /api/v1/classes/{class_id}/students/{student_id}` | `DELETE /api/v1/classes/{class_id}/students/{student_id}` | ✅ **READY** | Exact match |
| Get Class Metrics | `GET /api/v1/classes/{class_id}/metrics` | N/A | ⚠️ **MISSING** | Needs implementation |
| Get Student Detail | `GET /api/v1/students/{student_id}/detail` | N/A | ⚠️ **MISSING** | Needs implementation |
| Bulk Content Request | `POST /api/v1/classes/{class_id}/bulk-content-request` | N/A | ⚠️ **MISSING** | Needs implementation |
| Get Analytics | `GET /api/v1/classes/{class_id}/analytics` | N/A | ⚠️ **MISSING** | Needs implementation |
| Export Class Data | `GET /api/v1/classes/{class_id}/export/{type}` | N/A | ⚠️ **MISSING** | Needs implementation |

---

## Phase 2.2 Implementation Strategy

### Can Implement Now (Backend Ready) ✅

**Priority 1: TeacherClassDashboard Core Features**
- Dashboard header with class info (✅ `getClass`)
- Basic metric cards (use roster data for now)
- Class settings/edit modal (✅ `patchClass`)
- Archive class functionality (✅ `archiveClass`)

**Priority 2: StudentRosterTable**
- Full roster display (✅ `getRoster`)
- Student removal (✅ `removeStudentFromClass`)
- Sorting and filtering (client-side)

### Need Backend First (Missing Endpoints) ⚠️

**Phase 2.2 Extended**:
- Live metric cards (`getClassMetrics` - calculate from existing data as temporary solution)

**Phase 2.3**:
- StudentDetailPage (`getStudentDetail` - can build from existing student endpoints)

**Phase 2.4**:
- BulkContentRequestModal (`bulkContentRequest` - backend needed)

**Phase 2.5**:
- ClassAnalyticsDashboard (`getAnalytics`, `exportClassData` - backend needed)

---

## Backend Route Configuration

### API Mounting Structure

From `/backend/app/api/v1/api.py`:

```python
api_router.include_router(teachers.router, tags=["Teachers"])  # No prefix (has own)
api_router.include_router(classes.router, prefix="/classes", tags=["Classes"])
```

### Teachers Router

**File**: `/backend/app/api/v1/endpoints/teachers.py`
**Prefix**: `/teachers` (defined in router: `router = APIRouter(prefix="/teachers")`)

**Endpoints**:
- `POST /teachers/classes` - Create class ✅
- `GET /teachers/{teacher_id}/classes` - Get teacher's classes ✅
- `GET /teachers/classes/{class_id}` - Get class details ✅ (DUPLICATE - see note)
- `PATCH /teachers/classes/{class_id}` - Update class ✅ (DUPLICATE - see note)
- `DELETE /teachers/classes/{class_id}` - Archive class ✅ (DUPLICATE - see note)
- `GET /teachers/classes/{class_id}/students` - Get roster ✅ (DUPLICATE - see note)
- `DELETE /teachers/classes/{class_id}/students/{student_id}` - Remove student ✅ (DUPLICATE)
- `POST /teachers/student-requests` - Create student account request ✅
- `GET /teachers/{teacher_id}/student-requests` - Get requests ✅
- `GET /teachers/{teacher_id}/dashboard` - Get dashboard ✅

### Classes Router (Canonical)

**File**: `/backend/app/api/v1/endpoints/classes.py`
**Prefix**: `/classes` (from api.py)

**Endpoints** (These are the ones to use):
- `GET /classes/{class_id}` - Get class details ✅
- `PATCH /classes/{class_id}` - Update class ✅
- `DELETE /classes/{class_id}` - Archive class ✅
- `GET /classes/{class_id}/students` - Get roster ✅
- `DELETE /classes/{class_id}/students/{student_id}` - Remove student ✅

**⚠️ IMPORTANT NOTE**: There are **duplicate endpoints** for class operations:
- `/teachers/classes/{class_id}` (teachers.py - teacher-specific auth)
- `/classes/{class_id}` (classes.py - multi-role auth)

**Recommendation**: Use `/classes/{class_id}` routes (canonical, more flexible auth).

---

## Frontend API Service Updates Needed

### Current Issues in `frontend/src/api/teacher.ts`

The frontend API service is already using the **correct paths** for Phase 2.2! No changes needed for:

✅ `getTeacherDashboard` - `/api/v1/teachers/{teacher_id}/dashboard`
✅ `getClass` - `/api/v1/classes/{class_id}`
✅ `patchClass` - `/api/v1/classes/{class_id}`
✅ `archiveClass` - `/api/v1/classes/{class_id}`
✅ `getRoster` - `/api/v1/classes/{class_id}/students`

### Legacy Methods Need Path Updates

The **legacy methods** (from Phase 1) use incorrect paths and should be deprecated:

```typescript
// DEPRECATED - Use getClass() instead
async getClassDetail(classId: string): Promise<Class> {
  const response = await apiClient.get<Class>(ENDPOINTS.TEACHER_CLASS_DETAIL(classId))
  // ❌ Uses: /teachers/classes/${classId} (old path)
  // ✅ Should use: /classes/${classId}
  return response.data
}

// DEPRECATED - Use patchClass() instead
async updateClass(classId: string, data): Promise<Class> {
  const response = await apiClient.put<Class>(
    ENDPOINTS.TEACHER_CLASS_DETAIL(classId),  // ❌ Old path
    data
  )
  return response.data
}

// DEPRECATED - Use archiveClass() instead
async deleteClass(classId: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.TEACHER_CLASS_DETAIL(classId))  // ❌ Old path
}

// DEPRECATED - Use getRoster() instead
async getClassRoster(classId: string): Promise<ClassRoster> {
  const response = await apiClient.get<ClassRoster>(
    ENDPOINTS.TEACHER_CLASS_ROSTER(classId)  // ❌ Old path
  )
  return response.data
}
```

**Action**: Mark legacy methods as deprecated, update documentation to reference new methods.

---

## Missing Backend Endpoints (To Implement)

### 1. Get Class Metrics

**Endpoint**: `GET /api/v1/classes/{class_id}/metrics`

**Purpose**: Dashboard metric cards (student count, request count, completion rate, active students)

**Response Schema**:
```typescript
interface ClassMetrics {
  total_students: number
  total_requests: number
  completion_rate: number  // 0-100
  active_students_30d: number
  recent_activity?: Activity[]
}
```

**Temporary Solution**: Calculate from existing data:
- `total_students` - from `getRoster().total_students`
- `total_requests` - query content_requests table (can add to roster response)
- `completion_rate` - calculate from progress data
- `active_students_30d` - query recent activity (can add to dashboard)

**Priority**: **Medium** - Can use roster data as workaround

---

### 2. Get Student Detail

**Endpoint**: `GET /api/v1/students/{student_id}/detail`

**Purpose**: Student detail page with full profile and progress

**Response Schema**:
```typescript
interface StudentDetail {
  user_id: string
  email: string
  first_name: string
  last_name: string
  grade_level?: number
  classes: { class_id: string; class_name: string; enrolled_at: string }[]
  progress_summary: {
    videos_requested: number
    videos_watched: number
    topics_completed: number
    avg_watch_time: number
  }
  recent_activity: Activity[]
  interests?: string[]
}
```

**Temporary Solution**: Aggregate from existing endpoints:
- User info from roster
- Classes from enrollments
- Progress from existing progress endpoints
- Activity from notifications/events

**Priority**: **Low** - Phase 2.3 feature, can aggregate data client-side

---

### 3. Bulk Content Request

**Endpoint**: `POST /api/v1/classes/{class_id}/bulk-content-request`

**Purpose**: Generate content for multiple students at once

**Request Schema**:
```typescript
interface BulkContentRequest {
  student_ids: string[]
  query: string
  topic?: string
  subject?: string
  schedule?: {
    generate_now: boolean
    scheduled_for?: string
  }
  notify_students: boolean
}
```

**Response Schema**:
```typescript
interface BulkContentRequestResponse {
  batch_id: string
  total_requests: number
  successful: number
  failed: number
  requests: {
    student_id: string
    request_id?: string
    status: 'success' | 'failed'
    error?: string
  }[]
}
```

**Priority**: **Medium** - Phase 2.4 feature, needed for bulk operations workflow

---

### 4. Get Class Analytics

**Endpoint**: `GET /api/v1/classes/{class_id}/analytics?start_date={date}&end_date={date}`

**Purpose**: Charts and graphs for analytics dashboard

**Response Schema**: Already defined in `ClassAnalytics` interface

**Priority**: **Low** - Phase 2.5 feature

---

### 5. Export Class Data

**Endpoint**: `GET /api/v1/classes/{class_id}/export/{type}`

**Purpose**: Download CSV/Excel exports

**Types**: `roster | analytics | requests`

**Response**: `Blob` (CSV file)

**Priority**: **Low** - Phase 2.5 feature

---

## Implementation Approach

### Phase 1: Build with Available Endpoints (This Session)

**Components to Build**:
1. ✅ TeacherClassDashboard page
   - Class header with edit/archive
   - Basic metric cards (use roster data)
   - Tab navigation (students tab only for now)
   - Real-time updates via WebSocket

2. ✅ StudentRosterTable component
   - Full roster display
   - Sortable columns
   - Student removal
   - Bulk selection UI (actions disabled until bulk endpoint ready)

3. ✅ Route integration in App.tsx

4. ✅ Comprehensive tests

### Phase 2: Backend Endpoints (Parallel or Next Session)

Implement missing endpoints in priority order:
1. `GET /classes/{class_id}/metrics` (metrics cards)
2. `POST /classes/{class_id}/bulk-content-request` (bulk operations)
3. `GET /students/{student_id}/detail` (student detail page)
4. `GET /classes/{class_id}/analytics` (analytics dashboard)
5. `GET /classes/{class_id}/export/{type}` (data export)

### Phase 3: Integration (Follow-up Session)

Once backend endpoints are ready:
- Enable bulk operations in StudentRosterTable
- Build StudentDetailPage
- Build ClassAnalyticsDashboard
- Enable export functionality

---

## Summary

**✅ Ready to Build**: TeacherClassDashboard + StudentRosterTable with current backend endpoints

**⚠️ Missing**: 5 endpoints for extended features (metrics, bulk ops, analytics, export)

**🎯 Strategy**: Build core dashboard now, add extended features as backend endpoints become available

**📝 Next Step**: Update frontend API service to deprecate legacy methods, then implement TeacherClassDashboard component

---

**Session Status**: Backend verification complete
**Blocker Status**: No blockers for Phase 2.2 core features
**Ready to Proceed**: YES - TeacherClassDashboard implementation

🤖 Generated with Claude Code (Andrew Ng methodology: Verify infrastructure first)

Co-Authored-By: Claude <noreply@anthropic.com>
