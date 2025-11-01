"""
Interest and StudentInterest Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class InterestBase(BaseModel):
    """Base Interest schema."""
    interest_id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class InterestResponse(InterestBase):
    """Interest response schema."""
    display_order: Optional[int] = None

    class Config:
        from_attributes = True


class StudentInterestCreate(BaseModel):
    """Schema for creating student interests."""
    interest_ids: List[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Student must select between 2-5 interests"
    )


class StudentInterestResponse(BaseModel):
    """Student interest response schema."""
    student_id: str
    interest_id: str
    created_at: datetime
    interest: InterestResponse

    class Config:
        from_attributes = True


class StudentInterestsListResponse(BaseModel):
    """Response schema for student's interests list."""
    interests: List[InterestResponse]
    count: int
