"""
API v1 endpoints package.
"""
from app.api.v1.endpoints import auth, students, teachers, classes, admin, topics, content, cache, notifications

__all__ = ["auth", "students", "teachers", "classes", "admin", "topics", "content", "cache", "notifications"]
