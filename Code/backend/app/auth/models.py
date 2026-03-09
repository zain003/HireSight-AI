"""
MongoDB document models for authentication module.
Follows Clean Architecture - Data Layer.
Uses Beanie ODM (Object Document Mapper) for MongoDB.
"""
from beanie import Document, Indexed, Link
from pydantic import Field, EmailStr
from typing import Optional, List
from datetime import datetime


class User(Document):
    """User document for authentication"""
    
    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # Collection name
        indexes = [
            "email",
            "username",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "is_active": True,
            }
        }


class Profile(Document):
    """User profile with job role and difficulty preferences"""
    
    user_id: Indexed(str)  # Reference to User._id
    job_role: Optional[str] = None
    difficulty_level: Optional[str] = None  # easy, medium, hard
    resume_path: Optional[str] = None
    
    # Skills stored as native lists (no JSON serialization needed!)
    skills: Optional[List[str]] = Field(default_factory=list)
    experienced_skills: Optional[List[str]] = Field(default_factory=list)
    known_skills: Optional[List[str]] = Field(default_factory=list)
    
    # Other fields as native types
    experience_years: Optional[int] = None
    domain: Optional[str] = None
    job_titles: Optional[List[str]] = Field(default_factory=list)
    education: Optional[List[dict]] = Field(default_factory=list)
    projects: Optional[List[dict]] = Field(default_factory=list)
    certifications: Optional[List[str]] = Field(default_factory=list)
    companies: Optional[List[str]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "profiles"
        indexes = [
            "user_id",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "job_role": "Software Engineer",
                "difficulty_level": "medium",
                "skills": ["Python", "FastAPI", "MongoDB"],
                "experienced_skills": ["Python", "FastAPI"],
                "known_skills": ["MongoDB"],
            }
        }


class Session(Document):
    """Interview session tracking"""
    
    session_id: Indexed(str, unique=True)
    user_id: Indexed(str)  # Reference to User._id
    job_role: str
    difficulty_level: str
    status: str = "active"  # active, completed, abandoned
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "sessions"
        indexes = [
            "session_id",
            "user_id",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "user_id": "507f1f77bcf86cd799439011",
                "job_role": "Software Engineer",
                "difficulty_level": "medium",
                "status": "active",
            }
        }
