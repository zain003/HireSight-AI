"""
API routes for resume module.
Follows Clean Architecture - API Layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import os
import shutil
from pathlib import Path

from app.resume.schemas import (
    ResumeUploadResponse,
    ResumeParseResponse,
    SkillExtractionRequest,
    ExperienceInfo,
    EducationInfo,
    ProjectInfo,
)
from app.resume.service import ResumeService
from app.auth.dependencies import get_current_active_user
from app.auth.models import User, Profile
from app.core.config import settings
from app.core.exceptions import FileProcessingError
from app.auth.job_post_model import JobPost
from beanie import PydanticObjectId
from app.auth.skill_matcher import SkillMatcher


router = APIRouter()


# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
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
    
    # Create user-specific directory (using string ID for MongoDB)
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
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and parse resume file.
    
    Pipeline:
    1. Uploads the resume file
    2. Extracts text (pdfplumber / python-docx / Tesseract OCR)
    3. Uses BERT-NER (yashpwr/resume-ner-bert-v2) to extract entities:
       Skills, Job Titles, Companies, Education, Experience
    4. Detects domain using weighted scoring on job titles + skills
    5. Classifies skills into Experienced vs Known categories
    6. Updates user profile with all extracted information
    
    Requires authentication.
    """
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, f"resume_{current_user.id}{file_ext}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        resume_service = ResumeService()
        extracted_data = await resume_service.save_resume_to_profile(str(current_user.id), file_path)
        
        return ResumeParseResponse(
            skills=extracted_data["skills"],
            job_titles=extracted_data["job_titles"],
            experience=ExperienceInfo(**extracted_data["experience"]),
            education=[EducationInfo(**e) for e in extracted_data["education"]],
            projects=[ProjectInfo(**p) for p in extracted_data["projects"]],
            certifications=extracted_data["certifications"],
            domain=extracted_data["domain"],
            raw_text_length=extracted_data["raw_text_length"],
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
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract skills from raw text.
    
    Useful for testing or extracting skills from job descriptions.
    
    - **text**: Input text to analyze
    - **use_embeddings**: Whether to use semantic matching (default: true)
    
    Requires authentication.
    """
    resume_service = ResumeService()
    skills = resume_service.extract_skills_from_text(request.text, request.use_embeddings)
    
    return {
        "skills": skills,
        "count": len(skills)
    }


@router.post("/match-skills")
async def match_resume_to_job(
    job_post_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a resume and match its skills to a job post's required skills.
    Returns the match percentage and both skill lists.
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Save file temporarily
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, f"resume_{current_user.id}{file_ext}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract skills from resume
        resume_service = ResumeService()
        extracted_data = await resume_service.save_resume_to_profile(str(current_user.id), file_path)
        resume_skills = set(extracted_data["skills"])

        # Fetch job post and required skills
        job_post = await JobPost.get(PydanticObjectId(job_post_id))
        if not job_post:
            raise HTTPException(status_code=404, detail="Job post not found")
        job_skills = set(job_post.required_skills)

        match_result = SkillMatcher.match_skills(list(job_skills), list(resume_skills))
        matched_count = len(match_result.get("matched_skills", []))
        job_count = len(job_skills)
        match_percent = int(100 * matched_count / job_count) if job_count else 0

        return {
            "match_percent": match_percent,
            "matched_skills": match_result.get("matched_skills", []),
            "missing_skills": match_result.get("missing_skills", []),
            "extra_skills": match_result.get("extra_skills", []),
            "resume_skills": list(resume_skills),
            "job_skills": list(job_skills),
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
