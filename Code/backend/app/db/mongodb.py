"""
MongoDB database configuration using Motor (async MongoDB driver).
Follows Clean Architecture - Database Layer.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from app.auth.models import User, Profile, Session
from app.auth.job_post_model import JobPost
from app.interview.models import InterviewSession
from app.core.config import settings


class MongoDB:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        mongodb_url = settings.MONGODB_URL
        database_name = settings.MONGODB_DATABASE
        
        cls.client = AsyncIOMotorClient(mongodb_url)
        
        # Initialize Beanie with document models
        await init_beanie(
            database=cls.client[database_name],
            document_models=[User, Profile, Session, JobPost, InterviewSession]
        )
        
        print(f"[OK] Connected to MongoDB: {database_name}")
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("[OK] MongoDB connection closed")


# Dependency for FastAPI routes
async def get_database():
    """Get database instance (for dependency injection)"""
    return MongoDB.client
