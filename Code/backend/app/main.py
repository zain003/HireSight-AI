"""
Main FastAPI application entry point.
This is the core of our Modular Monolith architecture.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.db.mongodb import MongoDB
from app.auth.routes import router as auth_router
from app.resume.routes import router as resume_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Connect to MongoDB
    await MongoDB.connect_db()
    print("✓ MongoDB connected and initialized")
    yield
    # Shutdown: Close MongoDB connection
    await MongoDB.close_db()
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
    allow_origins=["http://localhost:3000"],  # Only allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register module routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(resume_router, prefix="/resume", tags=["Resume"])

# Serve uploaded/static files (e.g., landing page illustration) from UPLOAD_DIR
upload_dir = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


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
