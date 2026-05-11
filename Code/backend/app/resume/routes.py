"""
API routes for resume module.
Follows Clean Architecture - API Layer.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import os
import shutil
from pathlib import Path

from app.resume.schemas import (
    ResumeUploadResponse,
    ResumeParseResponse,
    ResumeParseDebugResponse,
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
    job_role: Optional[str] = Form(
        None,
        description="Target role you are applying for (e.g. Django Developer). "
        "Saved to profile and overrides titles inferred from the CV.",
    ),
    current_user: User = Depends(get_current_active_user),
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
        extracted_data = await resume_service.save_resume_to_profile(
            str(current_user.id),
            file_path,
            preferred_job_role=job_role,
        )
        
        return ResumeParseResponse(
            skills=extracted_data["skills"],
            job_titles=extracted_data["job_titles"],
            experience=ExperienceInfo(**extracted_data["experience"]),
            education=[EducationInfo(**e) for e in extracted_data["education"]],
            projects=[ProjectInfo(**p) for p in extracted_data["projects"]],
            certifications=extracted_data["certifications"],
            domain=extracted_data["domain"],
            raw_text_length=extracted_data["raw_text_length"],
            extraction_json_path=extracted_data.get("extraction_json_path", ""),
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


@router.post("/parse-debug", response_model=ResumeParseDebugResponse)
async def parse_resume_debug(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Parse resume and return detailed debug payload:
    - raw parsed text
    - NER entities
    - structured extraction fields
    Also writes a JSON artifact file for manual inspection.
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
        extracted_data = resume_service.parse_resume_with_debug(file_path)

        return ResumeParseDebugResponse(
            skills=extracted_data["skills"],
            experienced_skills=extracted_data.get("experienced_skills", []),
            known_skills=extracted_data.get("known_skills", []),
            job_titles=extracted_data["job_titles"],
            experience=ExperienceInfo(**extracted_data["experience"]),
            education=[EducationInfo(**e) for e in extracted_data["education"]],
            projects=[ProjectInfo(**p) for p in extracted_data["projects"]],
            certifications=extracted_data["certifications"],
            domain=extracted_data["domain"],
            raw_text_length=extracted_data["raw_text_length"],
            ner_entities=extracted_data.get("ner_entities", {}),
            raw_text=extracted_data.get("raw_text", ""),
            debug_file_path=extracted_data.get("debug_file_path", ""),
        )
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume (debug): {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


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
    job_role: Optional[str] = Form(
        None,
        description="Your target job role; saved on profile and not overwritten by CV titles.",
    ),
    current_user: User = Depends(get_current_active_user),
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

        # Extract skills from resume and update profile
        resume_service = ResumeService()
        try:
            extracted_data = await resume_service.save_resume_to_profile(
                str(current_user.id),
                file_path,
                include_debug=True,
                preferred_job_role=job_role,
            )
        except FileProcessingError as e:
            # Surface validation/parsing errors (e.g. empty CV, non‑computing domain)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        resume_skills_flat = SkillMatcher.flatten_candidate_skill_lists(
            extracted_data.get("skills"),
            extracted_data.get("experienced_skills"),
            extracted_data.get("known_skills"),
        )
        resume_skills = list(dict.fromkeys(resume_skills_flat))

        # Fetch job post and required skills
        job_post = await JobPost.get(PydanticObjectId(job_post_id))
        if not job_post:
            raise HTTPException(status_code=404, detail="Job post not found")
        # Keep original required skill list for canonical matching
        job_skills = list(dict.fromkeys(job_post.required_skills or []))

        # Match against all extracted skill buckets (skills / experienced / known).
        # Do not scan raw resume text: PDF/OCR noise can false-positive short tokens.
        match_result = SkillMatcher.match_skills(job_skills, resume_skills)
        matched_count = len(match_result.get("matched_skills", []))
        job_count = len(job_skills)
        match_percent = int(100 * matched_count / job_count) if job_count else 0

        return {
            "match_percent": match_percent,
            "matched_skills": match_result.get("matched_skills", []),
            "missing_skills": match_result.get("missing_skills", []),
            "extra_skills": match_result.get("extra_skills", []),
            "resume_skills": resume_skills,
            "job_skills": job_skills,
            "extraction_json_path": extracted_data.get("extraction_json_path", ""),
            "debug_file_path": extracted_data.get("debug_file_path", ""),
            "ner_entities": extracted_data.get("ner_entities", {}),
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
