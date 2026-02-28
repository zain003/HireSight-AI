"""
Database models for authentication module.
Follows Clean Architecture - Data Layer.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")


class Profile(Base):
    """User profile with job role and difficulty preferences"""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    job_role = Column(String(100))
    difficulty_level = Column(String(50))  # easy, medium, hard
    resume_path = Column(String(500))
    skills = Column(Text)  # JSON string of skills
    experience_years = Column(Integer)
    domain = Column(String(100))
    job_titles = Column(Text)  # JSON string of job titles
    education = Column(Text)  # JSON string of education entries
    projects = Column(Text)  # JSON string of projects
    certifications = Column(Text)  # JSON string of certifications
    companies = Column(Text)  # JSON string of companies
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class Session(Base):
    """Interview session tracking"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_role = Column(String(100))
    difficulty_level = Column(String(50))
    status = Column(String(50), default="active")  # active, completed, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
