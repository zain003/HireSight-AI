"""
MongoDB document model for job posts.
"""
from beanie import Document, Indexed
from pydantic import Field
from typing import List, Optional
from datetime import datetime

class JobPost(Document):
    """Job post document for admin-created job posts"""
    title: str
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    created_by: str = Field(default="admin")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "job_posts"
        indexes = ["title", "domain"]

    class Config:
        json_schema_extra = {
            "example": {
                "title": "AI Engineer",
                "description": "Develop AI models and pipelines",
                "required_skills": ["Python", "Machine Learning", "Deep Learning"],
                "domain": "Computing",
                "created_by": "admin",
            }
        }
