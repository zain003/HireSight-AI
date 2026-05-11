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
    status: str = Field(default="active", pattern="^(active|draft|closed)$")


class JobPostUpdate(BaseModel):
    """Partial update for job posts (admin). Omit fields to leave unchanged."""
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    domain: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|draft|closed)$")


class JobPostResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    required_skills: List[str]
    domain: Optional[str] = None
    status: str = "active"
    """Distinct candidates who started a live interview tied to this job post."""
    applicant_count: int = 0
    created_by: str
    created_at: datetime
    updated_at: datetime
