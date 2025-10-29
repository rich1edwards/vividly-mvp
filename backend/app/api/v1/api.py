"""
API v1 router aggregation.

Combines all endpoint routers for the v1 API.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, students, teachers


api_router = APIRouter()

# Include all endpoint routers
# Note: Students and Teachers routers have prefixes defined in their own files
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(students.router, tags=["Students"])
api_router.include_router(teachers.router, tags=["Teachers"])
