  How to Start the Backend

  cd /Users/richedwards/AI-Dev-Projects/Vividly/backend
  source venv/bin/activate
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  The API will be available at:
  - API Base: http://localhost:8000/api/v1/
  - Docs: http://localhost:8000/api/docs (Swagger UI)
  - Health Check: http://localhost:8000/health

  Configuration Details

  Database:
  - PostgreSQL 15.14 on Cloud SQL
  - Public IP: 34.56.211.136
  - Database: vividly
  - User: vividly
  - Password: Retrieved from GCP Secret Manager

  Authentication:
  - JWT tokens with HS256 algorithm
  - 24-hour access tokens
  - 30-day refresh tokens
  - Securely generated 512-bit secret key

  Environment:
  - Debug mode: ON
  - Python: 3.12.11
  - FastAPI: 0.104.1
  - 22 database tables deployed
  - 127 performance indexes
