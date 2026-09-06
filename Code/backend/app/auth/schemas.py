"""
Pydantic schemas for authentication module.
Follows Clean Architecture - Schema Layer.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: str  # MongoDB ObjectId as string
    is_active: bool
    created_at: datetime


# Profile Schemas
class ProfileCreate(BaseModel):
    """Schema for creating/updating profile"""
    job_role: str = Field(..., min_length=2, max_length=100)
    difficulty_level: str = Field(..., pattern="^(easy|medium|hard)$")
    experience_years: Optional[int] = Field(None, ge=0, le=50)


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    id: str  # MongoDB ObjectId as string
    user_id: str
    job_role: Optional[str] = None
    difficulty_level: Optional[str] = None
    experience_years: Optional[int] = None
    resume_path: Optional[str] = None
    skills: Optional[List[str]] = None  # Native list (no JSON serialization!)
    experienced_skills: Optional[List[str]] = None
    known_skills: Optional[List[str]] = None
    domain: Optional[str] = None
    job_titles: Optional[List[str]] = None
    education: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    certifications: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    resume_structured: Optional[Dict[str, Any]] = None
    resume_extraction_json_path: Optional[str] = None
    created_at: datetime


# Session Schemas
class SessionCreate(BaseModel):
    """Schema for creating interview session"""
    job_role: str
    difficulty_level: str = Field(..., pattern="^(easy|medium|hard)$")


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str  # MongoDB ObjectId as string
    session_id: str
    user_id: str
    job_role: str
    difficulty_level: str
    status: str
    created_at: datetime


# Token Schemas
class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None  # Changed from int to str
    username: Optional[str] = None


# ── Candidate Roster & Admin Report Schemas (Issue 02) ─────────────────────────

class CandidateRosterItem(BaseModel):
    """Candidate entry in the recruiter admin roster"""
    user_id: str
    candidate_name: str
    email: Optional[str] = None
    username: Optional[str] = None
    job_role: Optional[str] = None
    job_post_id: Optional[str] = None
    job_post_title: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "not_started"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    five_dimension_scores: Optional[Dict[str, Any]] = None
    hiring_recommendation: Optional[str] = None
    fit_status: Optional[str] = None
    duration_minutes: Optional[float] = None
    has_report: bool = False
    experience_years: Optional[int] = None
    resume_score: Optional[float] = None
    skills: List[str] = Field(default_factory=list)


class CandidateRosterResponse(BaseModel):
    """Paginated response for candidate roster with facet metadata"""
    items: List[CandidateRosterItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    available_roles: List[str] = Field(default_factory=list)
    available_recommendations: List[str] = Field(default_factory=list)
    status_counts: Dict[str, int] = Field(default_factory=dict)

