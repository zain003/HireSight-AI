"""
MongoDB database configuration using Motor (async MongoDB driver).
Follows Clean Architecture - Database Layer.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
import os

from app.auth.models import User, Profile, Session


class MongoDB:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
        database_name = os.getenv("MONGODB_DATABASE", "hiresight_db")
        
        cls.client = AsyncIOMotorClient(mongodb_url)
        
        # Initialize Beanie with document models
        await init_beanie(
            database=cls.client[database_name],
            document_models=[User, Profile, Session]
        )
        
        print(f"✅ Connected to MongoDB: {database_name}")
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            print("✅ MongoDB connection closed")


# Dependency for FastAPI routes
async def get_database():
    """Get database instance (for dependency injection)"""
    return MongoDB.client
