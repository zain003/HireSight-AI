"""
Pydantic schemas for authentication module.
Follows Clean Architecture - Schema Layer.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
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
    username: str
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
