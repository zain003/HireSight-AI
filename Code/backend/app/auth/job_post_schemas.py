"""
Pydantic schemas for job post creation and response.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class JobPostCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    domain: Optional[str] = None

class JobPostResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    required_skills: List[str]
    domain: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
