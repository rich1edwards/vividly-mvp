# Sprint 2 Quick Reference Card

**Sprint Goal**: Backend Completion + Frontend Foundation
**Duration**: 2-3 weeks
**Status**: 🟡 Ready to Start

---

## 📋 Sprint 2 at a Glance

| Phase | Duration | Priority | Status |
|-------|----------|----------|--------|
| **Phase 1**: Backend Completion | Days 1-5 | P0 | 🔴 Not Started |
| **Phase 2**: Frontend Foundation | Days 3-8 | P0 | 🔴 Not Started |
| **Phase 3**: Database & Deployment | Days 6-10 | P1 | 🔴 Not Started |
| **Phase 4**: Integration & Testing | Days 8-12 | P1 | 🔴 Not Started |

---

## 🎯 Key Objectives

### Must Deliver (P0)
1. ✅ **100% Test Pass Rate** - All 66 tests passing
2. ✅ **80% Code Coverage** - Comprehensive test coverage
3. ✅ **Working Authentication** - Frontend login/register
4. ✅ **Student Onboarding** - Register → Interests → Dashboard
5. ✅ **Teacher Class Management** - Create classes, view roster
6. ✅ **Backend Deployed** - Cloud Run with Cloud SQL
7. ✅ **Frontend Deployed** - Cloud Storage + CDN

### Should Deliver (P1)
- E2E tests for critical flows
- CI/CD pipelines operational
- API documentation complete
- Manual testing complete

---

## 🔴 Current Blockers (From Sprint 1)

1. **28 Failing Tests**
   - Auth endpoints: 8 tests
   - Student endpoints: 11 tests
   - Teacher endpoints: 9 tests

2. **No Frontend Application**
   - React app not yet created
   - Only E2E test infrastructure exists

3. **Database Not Deployed**
   - Migrations not run on Cloud SQL
   - No sample data loaded

4. **No Deployment Pipeline**
   - Backend not on Cloud Run
   - Frontend not deployed
   - No CI/CD configured

---

## 📊 Sprint 1 Outcomes

### What We Delivered
- ✅ Backend models with foreign keys
- ✅ Service layer (70% complete)
- ✅ API endpoints defined
- ✅ 66 tests created (38 passing)
- ✅ Security testing framework
- ✅ Playwright E2E setup

### Current Metrics
- **Test Pass Rate**: 58% (38/66)
- **Code Coverage**: 41%
- **Passing Tests**: 38
- **Failing Tests**: 28
- **Test Errors**: 0

### Target Metrics for Sprint 2
- **Test Pass Rate**: 100% (66/66)
- **Code Coverage**: ≥80%
- **API Response Time**: <200ms p95
- **Frontend Load Time**: <2s

---

## 🚀 Quick Start Guide

### Day 1: Backend Focus
```bash
# 1. Fix auth endpoint tests
cd backend
pytest tests/integration/test_auth_endpoints.py -v

# 2. Fix specific failing test
pytest tests/integration/test_auth_endpoints.py::test_register_student_success -vv

# 3. Run all tests with coverage
pytest tests/ --cov=app --cov-report=html

# 4. View coverage report
open htmlcov/index.html
```

### Day 3: Frontend Setup
```bash
# 1. Create React app
npm create vite@latest frontend -- --template react-ts
cd frontend

# 2. Install dependencies
npm install react-router-dom @tanstack/react-query zustand axios react-hook-form zod

# 3. Install UI tools
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn-ui@latest init

# 4. Start development
npm run dev
```

### Day 6: Deployment
```bash
# 1. Run database migrations
cd backend
alembic upgrade head

# 2. Build and deploy backend
docker build -t backend .
gcloud run deploy backend --source .

# 3. Build and deploy frontend
cd frontend
npm run build
gsutil -m rsync -r dist/ gs://vividly-frontend/
```

---

## 📚 Key Commands

### Backend Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_auth_service.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run failing tests only
pytest tests/ --lf

# Stop on first failure
pytest tests/ -x
```

### Frontend Development
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run E2E tests
npm run test:e2e

# Run linting
npm run lint
```

### Deployment
```bash
# Backend deployment
gcloud run deploy backend --source . --region us-central1

# Frontend deployment
gsutil -m rsync -r dist/ gs://vividly-frontend/

# Invalidate CDN cache
gcloud compute url-maps invalidate-cdn-cache vividly-lb --path "/*"
```

---

## 🔧 Tech Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (Cloud SQL)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.5
- **Testing**: pytest 7.4
- **Auth**: JWT (python-jose)

### Frontend
- **Framework**: React 18.3
- **Language**: TypeScript 5+
- **Build Tool**: Vite 5+
- **Styling**: TailwindCSS 3+
- **Components**: shadcn/ui
- **Router**: React Router v6
- **State**: Zustand + React Query
- **Forms**: react-hook-form + zod
- **Testing**: Playwright

### Infrastructure
- **Backend Hosting**: Cloud Run
- **Frontend Hosting**: Cloud Storage + CDN
- **Database**: Cloud SQL (PostgreSQL)
- **Secrets**: Secret Manager
- **Logging**: Cloud Logging
- **CI/CD**: GitHub Actions

---

## 📝 Essential Files

### Planning Documents
- `SPRINT_2_PLAN.md` - Detailed sprint plan
- `SPRINT_2_CHECKLIST.md` - Implementation checklist
- `SPRINT_2_QUICK_REFERENCE.md` - This file

### Backend Key Files
- `backend/app/main.py` - FastAPI application
- `backend/app/services/auth_service.py` - Auth business logic
- `backend/app/services/student_service.py` - Student business logic
- `backend/app/services/teacher_service.py` - Teacher business logic
- `backend/tests/conftest.py` - Test fixtures
- `backend/pytest.ini` - pytest configuration
- `backend/requirements.txt` - Python dependencies

### Frontend Key Files (To Create)
- `frontend/src/App.tsx` - Main application
- `frontend/src/lib/api.ts` - API client
- `frontend/src/stores/authStore.ts` - Auth state
- `frontend/src/pages/auth/LoginPage.tsx` - Login page
- `frontend/src/pages/auth/RegisterPage.tsx` - Registration page
- `frontend/src/pages/student/DashboardPage.tsx` - Student dashboard
- `frontend/src/pages/teacher/DashboardPage.tsx` - Teacher dashboard

### Deployment Files
- `backend/Dockerfile` - Backend container
- `.github/workflows/backend-ci-cd.yml` - Backend pipeline
- `.github/workflows/frontend-ci-cd.yml` - Frontend pipeline
- `terraform/main.tf` - Infrastructure as code

---

## 🐛 Common Issues & Solutions

### Issue: Tests Failing with 404
**Problem**: Endpoint returns 404
**Solution**: Ensure endpoint is registered in router and main app
```python
# In app/api/v1/api.py
from app.api.v1.endpoints import auth
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# In app/main.py
from app.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")
```

### Issue: CORS Errors in Frontend
**Problem**: API calls blocked by CORS
**Solution**: Configure CORS in backend
```python
# In app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Database Connection Fails
**Problem**: Cannot connect to Cloud SQL
**Solution**: Check Cloud SQL Proxy or VPC connector
```bash
# Option 1: Use Cloud SQL Proxy locally
cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432

# Option 2: Update DATABASE_URL
export DATABASE_URL="postgresql://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"
```

### Issue: Token Validation Fails
**Problem**: JWT token rejected
**Solution**: Check secret key and algorithm match
```python
# Backend must use same secret key
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Frontend must send token in header
headers: {
  'Authorization': `Bearer ${token}`
}
```

---

## 🎯 Daily Goals

### Days 1-2: Fix Backend Tests
- [ ] Fix all auth endpoint tests (8)
- [ ] Fix student endpoint tests (11)
- [ ] Fix teacher endpoint tests (9)
- **Goal**: 66/66 tests passing

### Days 3-4: Frontend Setup + Auth
- [ ] Create React app with TypeScript
- [ ] Build login and registration pages
- [ ] Implement authentication flow
- **Goal**: Can login/register

### Days 5-6: Student Dashboard
- [ ] Build interest selection
- [ ] Build student dashboard
- [ ] Implement class joining
- **Goal**: Student onboarding complete

### Days 7-8: Teacher Dashboard
- [ ] Build class management
- [ ] Build class roster
- [ ] Implement student requests
- **Goal**: Teacher can create classes

### Days 9-10: Deployment
- [ ] Deploy backend to Cloud Run
- [ ] Deploy frontend to Cloud Storage
- [ ] Set up CI/CD pipelines
- **Goal**: Production deployment

### Days 11-12: Testing & Polish
- [ ] Run E2E tests
- [ ] Complete manual testing
- [ ] Fix bugs
- **Goal**: Sprint 2 complete

---

## 📈 Success Criteria

Sprint 2 is successful when:
- ✅ All 66 tests passing
- ✅ Code coverage ≥ 80%
- ✅ Student can complete full onboarding
- ✅ Teacher can create and manage classes
- ✅ Backend deployed and accessible
- ✅ Frontend deployed and accessible
- ✅ E2E tests passing
- ✅ No P0/P1 bugs
- ✅ Ready to demo

---

## 🔗 Quick Links

- **API Docs** (local): http://localhost:8000/docs
- **Frontend** (local): http://localhost:5173
- **GitHub**: https://github.com/your-org/vividly
- **Cloud Console**: https://console.cloud.google.com
- **Test Reports**: `backend/htmlcov/index.html`
- **Playwright Reports**: `frontend/playwright-report/index.html`

---

## 📞 Need Help?

- **Backend Issues**: Check `app/services/` implementation
- **Frontend Issues**: Check React DevTools and Network tab
- **Deployment Issues**: Check Cloud Run logs
- **Database Issues**: Check Cloud SQL logs
- **Test Failures**: Run with `-vv` flag for details

---

**Last Updated**: 2025-10-28
**Sprint Start Date**: TBD
**Sprint End Date**: TBD
**Team**: Backend (1-2), Frontend (1-2), DevOps (1), QA (1)
