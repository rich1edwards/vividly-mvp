"""
API v1 router aggregation.

Combines all endpoint routers for the v1 API.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, students, teachers


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(teachers.router)
