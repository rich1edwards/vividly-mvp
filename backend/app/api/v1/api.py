"""
API v1 router aggregation.

Combines all endpoint routers for the v1 API.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, students, teachers, classes, admin, topics, content, cache, notifications


api_router = APIRouter()

# Include all endpoint routers
# Note: Students and Teachers routers have prefixes defined in their own files
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(students.router, tags=["Students"])
api_router.include_router(teachers.router, tags=["Teachers"])
api_router.include_router(classes.router, prefix="/classes", tags=["Classes"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(topics.router, tags=["Topics & Interests"])
api_router.include_router(content.router, prefix="/content", tags=["Content Metadata"])

# Internal API endpoints (Sprint 3)
api_router.include_router(cache.router, prefix="/internal/v1", tags=["Cache (Internal)"])
api_router.include_router(notifications.router, prefix="/internal/v1/notifications", tags=["Notifications (Internal)"])

# User-facing notification endpoints
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
