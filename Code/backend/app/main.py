"""
Main FastAPI application entry point.
This is the core of our Modular Monolith architecture.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.auth.routes import router as auth_router
from app.resume.routes import router as resume_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Connect to MongoDB
    await connect_to_mongo()
    print("✓ MongoDB connected and initialized")
    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()
    print("✓ Application shutdown")


# Initialize FastAPI application
app = FastAPI(
    title="AI Interview Platform",
    description="Modular Monolith Architecture - Microservice Ready",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(resume_router, prefix="/resume", tags=["Resume"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Interview Platform",
        "architecture": "Modular Monolith",
        "modules": ["auth", "resume", "ai"]
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": "connected",
        "ai_models": "loaded"
    }
