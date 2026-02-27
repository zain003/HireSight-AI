"""
API routes for resume module.
Follows Clean Architecture - API Layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path

from app.db.session import get_db
from app.resume.schemas import (
    ResumeUploadResponse,
    ResumeParseResponse,
    SkillExtractionRequest,
    ExperienceInfo
)
from app.resume.service import ResumeService
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.core.config import settings
from app.core.exceptions import FileProcessingError


router = APIRouter()


# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload resume file.
    
    Accepts PDF, DOCX, and image files (PNG, JPG, JPEG).
    Maximum file size: 10MB.
    
    Requires authentication.
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create user-specific directory
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    file_path = os.path.join(user_dir, f"resume_{current_user.id}{file_ext}")
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        return {
            "message": "Resume uploaded successfully",
            "file_path": file_path,
            "file_size": file_size
        }
    
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and parse resume file.
    
    This endpoint:
    1. Uploads the resume file
    2. Extracts text from the file
    3. Uses AI to extract skills, experience, and domain
    4. Updates user profile with extracted information
    
    Returns structured data including:
    - List of extracted skills
    - Experience information
    - Detected professional domain
    
    Requires authentication.
    """
    # First, upload the file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create user-specific directory
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    file_path = os.path.join(user_dir, f"resume_{current_user.id}{file_ext}")
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse resume and save to profile
        resume_service = ResumeService(db)
        extracted_data = resume_service.save_resume_to_profile(current_user.id, file_path)
        
        return ResumeParseResponse(
            skills=extracted_data["skills"],
            experience=ExperienceInfo(**extracted_data["experience"]),
            domain=extracted_data["domain"],
            raw_text_length=extracted_data["raw_text_length"]
        )
    
    except FileProcessingError as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {str(e)}"
        )


@router.post("/extract-skills")
async def extract_skills(
    request: SkillExtractionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Extract skills from raw text.
    
    Useful for testing or extracting skills from job descriptions.
    
    - **text**: Input text to analyze
    - **use_embeddings**: Whether to use semantic matching (default: true)
    
    Requires authentication.
    """
    resume_service = ResumeService(db)
    skills = resume_service.extract_skills_from_text(request.text, request.use_embeddings)
    
    return {
        "skills": skills,
        "count": len(skills)
    }
