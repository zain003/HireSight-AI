"""
API routes for authentication module.
Follows Clean Architecture - API Layer.
No business logic here, delegates to service layer.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query

from app.auth.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    ProfileCreate, ProfileResponse,
    SessionCreate, SessionResponse,
    CandidateRosterResponse,
)
from app.auth.service import AuthService
from app.auth.admin_service import AdminAuthService
from app.auth.dependencies import get_current_active_user
from app.auth.models import User, Profile
from app.core.security import create_access_token
from app.core.exceptions import ValidationError, AuthenticationError
from app.auth.job_post_service import JobPostService
from app.auth.job_post_schemas import JobPostCreate, JobPostResponse, JobPostUpdate
from app.auth.skill_matcher import SkillMatcher
from app.auth.admin_dashboard_service import (
    get_dashboard_stats,
    list_users_for_admin,
    count_interview_candidates_for_job,
    job_post_to_response_dict,
)
from app.auth.admin_candidates_service import (
    get_candidate_roster,
    get_candidate_session_report,
)

router = APIRouter()



# ── Admin Routes ─────────────────────────────────────────────────────────────

@router.post("/admin/login", response_model=Token)
async def admin_login(login_data: UserLogin):
    """
    Authenticate admin and return JWT token.
    - **email**: Admin email
    - **password**: Admin password
    Returns JWT access token for admin.
    """
    admin_user = await AdminAuthService.authenticate_admin(login_data.email, login_data.password)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"user_id": admin_user["id"], "username": admin_user["username"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/admin/skill-match")
async def skill_match(job_post_id: str = Body(...), candidate_profile_id: str = Body(...)):
    """
    Match skills between a job post and a candidate profile.
    Returns matched, missing, and extra skills.
    """
    from app.auth.job_post_model import JobPost
    job_post = await JobPost.get(job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")
    candidate_profile = await Profile.get(candidate_profile_id)
    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    candidate_skills = SkillMatcher.flatten_candidate_skill_lists(
        candidate_profile.skills,
        getattr(candidate_profile, "experienced_skills", None),
        getattr(candidate_profile, "known_skills", None),
    )
    result = SkillMatcher.match_skills(job_post.required_skills, candidate_skills)
    return result


@router.post("/admin/job-post", response_model=JobPostResponse)
async def create_job_post(job_post_data: JobPostCreate):
    """
    Create a new job post (admin only).
    Requires admin authentication (handled externally).
    """
    job_post = await JobPostService.create_job_post(job_post_data)
    return job_post_to_response_dict(job_post, 0)


@router.get("/admin/dashboard-stats")
async def admin_dashboard_stats():
    """Real metrics for the admin dashboard (users, jobs, interviews, skills)."""
    return await get_dashboard_stats()


@router.get("/admin/users")
async def admin_list_users():
    """Registered candidates with optional profile / resume flags."""
    return await list_users_for_admin()


@router.get("/admin/job-posts", response_model=list[JobPostResponse])
async def get_all_job_posts():
    """
    Get all job posts (admin only).
    """
    job_posts = await JobPostService.get_all_job_posts()
    out = []
    for jp in job_posts:
        ac = await count_interview_candidates_for_job(str(jp.id))
        out.append(job_post_to_response_dict(jp, ac))
    return out


@router.get("/admin/job-posts/{job_post_id}", response_model=JobPostResponse)
async def get_job_post(job_post_id: str):
    """Get a single job post by id (admin)."""
    jp = await JobPostService.get_job_post_by_id(job_post_id)
    if not jp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job post not found")
    ac = await count_interview_candidates_for_job(str(jp.id))
    return job_post_to_response_dict(jp, ac)


@router.put("/admin/job-posts/{job_post_id}", response_model=JobPostResponse)
async def update_job_post(job_post_id: str, job_post_data: JobPostUpdate):
    """Update a job post (admin)."""
    jp = await JobPostService.update_job_post(job_post_id, job_post_data)
    if not jp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job post not found")
    ac = await count_interview_candidates_for_job(str(jp.id))
    return job_post_to_response_dict(jp, ac)


@router.delete("/admin/job-posts/{job_post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_post(job_post_id: str):
    """Delete a job post (admin)."""
    deleted = await JobPostService.delete_job_post(job_post_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job post not found")


@router.get("/admin/job-posts/{job_post_id}/candidates")
async def get_job_candidates(job_post_id: str):
    """
    Get all candidates who applied and completed interviews for a specific job.
    Returns list of candidates with their interview status and reports (admin only).
    """
    from app.auth.job_post_model import JobPost
    from app.interview.models import InterviewSession
    
    # Verify job post exists
    job_post = await JobPost.get(job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")
    
    # Get all interview sessions for this job
    sessions = await InterviewSession.find(
        {"job_post_id": job_post_id}
    ).to_list()
    
    candidates = []
    for session in sessions:
        # Get candidate profile
        profile = await Profile.find_one({"user_id": session.user_id})
        user = await User.get(session.user_id)
        
        candidate_data = {
            "session_id": session.session_id,
            "candidate_id": session.candidate_id,
            "candidate_name": session.candidate_name,
            "user_email": user.email if user else None,
            "status": session.status,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "overall_score": session.aggregate_scores.get("overall_score") if session.aggregate_scores else None,
            "has_report": bool(session.recruiter_report),
            "hiring_recommendation": session.recruiter_report.get("hiring_recommendation") if session.recruiter_report else None,
            "confidence_level": session.recruiter_report.get("confidence_level") if session.recruiter_report else None,
            # Profile info
            "experience_years": profile.experience_years if profile else None,
            "skills": profile.skills if profile else [],
            "resume_score": getattr(profile, "resume_score", None) if profile else None,
        }
        candidates.append(candidate_data)
    
    # Sort by overall score (highest first), then by date
    candidates.sort(key=lambda x: (
        -(x["overall_score"] or 0),
        x["ended_at"] or x["started_at"] or ""
    ), reverse=False)
    
    return {
        "job_post_id": job_post_id,
        "job_title": job_post.title,
        "job_role": getattr(job_post, "role", None),
        "total_candidates": len(candidates),
        "completed_interviews": sum(1 for c in candidates if c["status"] == "completed"),
        "candidates": candidates
    }


@router.get("/admin/job-posts/{job_post_id}/candidates/{session_id}/report")
async def get_candidate_report(job_post_id: str, session_id: str):
    """
    Get comprehensive interview report for a specific candidate (admin only).
    This endpoint is private - only admin who posted the job can access.
    """
    from app.auth.job_post_model import JobPost
    from app.interview.models import InterviewSession
    
    # Verify job post exists
    job_post = await JobPost.get(job_post_id)
    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")
    
    # Get interview session
    session = await InterviewSession.find_one({
        "session_id": session_id,
        "job_post_id": job_post_id
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found for this job")
    
    if not session.recruiter_report:
        raise HTTPException(
            status_code=404,
            detail="Interview report not generated yet. Interview may still be in progress."
        )
    
    # Get candidate info
    user = await User.get(session.user_id)
    profile = await Profile.find_one({"user_id": session.user_id})
    
    return {
        "session_id": session.session_id,
        "job_post_id": job_post_id,
        "job_title": job_post.title,
        "candidate_info": {
            "name": session.candidate_name,
            "email": user.email if user else None,
            "experience_years": profile.experience_years if profile else None,
            "skills": profile.skills if profile else [],
            "resume_score": getattr(profile, "resume_score", None) if profile else None,
        },
        "interview_info": {
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_minutes": session.recruiter_report.get("session_duration_minutes") if session.recruiter_report else None,
            "status": session.status,
        },
        "recruiter_report": session.recruiter_report,
        "aggregate_scores": session.aggregate_scores or {},
        "questions_count": len(session.questions),
        "evaluations_count": len(session.evaluations),
    }


@router.get("/admin/candidates", response_model=CandidateRosterResponse)
async def admin_get_candidate_roster(
    search: Optional[str] = Query(None, description="Search query by candidate name, email, role, or skill"),
    status: Optional[List[str]] = Query(None, description="Multi-select interview status filters (completed, in_progress, not_started)"),
    role: Optional[str] = Query(None, description="Filter by candidate target role or job title"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum overall score"),
    max_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum overall score"),
    recommendation: Optional[List[str]] = Query(None, description="Multi-select hire recommendations (Strong Fit, Potential Fit, Needs Growth, Not a Fit)"),
    start_date: Optional[str] = Query(None, description="Activity start date in ISO format"),
    end_date: Optional[str] = Query(None, description="Activity end date in ISO format"),
    sort_by: str = Query("date_desc", description="Sorting field (score_desc, score_asc, date_desc, date_asc, name_asc, name_desc, status)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    job_post_id: Optional[str] = Query(None, description="Optional job post ID filter"),
):
    """
    Retrieve paginated candidate assessment roster with multi-criteria filtering, search, and facets.
    Supports recruiter hiring workflows (Issue 02).
    """
    return await get_candidate_roster(
        search=search,
        statuses=status,
        role=role,
        min_score=min_score,
        max_score=max_score,
        recommendations=recommendation,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        job_post_id=job_post_id,
    )


@router.get("/admin/candidates/{session_id}/report")
async def admin_get_candidate_report_by_session(session_id: str):
    """
    Get full detailed candidate report dossier directly by session ID.
    Handles both job-linked and standalone sessions gracefully (Issue 02).
    """
    try:
        return await get_candidate_session_report(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── User Auth Routes ────────────────────────────────────────────────────────


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: Unique username (3-50 characters)
    - **password**: Strong password (min 8 characters)
    - **full_name**: Optional full name
    """
    try:
        auth_service = AuthService()
        user = await auth_service.create_user(user_data)
        user_dict = user.dict()
        user_dict["id"] = str(user.id)
        return user_dict
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    Authenticate user and return JWT token.
    
    - **email**: Email address
    - **password**: Password
    
    Returns JWT access token for subsequent requests.
    """
    auth_service = AuthService()
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": str(user.id), "username": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ── Authenticated User Routes ───────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    # Ensure id is string for response validation
    user_dict = current_user.dict()
    user_dict["id"] = str(current_user.id)
    return user_dict


@router.post("/profile", response_model=ProfileResponse)
async def create_or_update_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create or update user profile.
    
    - **job_role**: Target job role (e.g., "Software Engineer")
    - **difficulty_level**: Interview difficulty (easy, medium, hard)
    - **experience_years**: Years of experience (optional)
    
    Requires authentication.
    """
    auth_service = AuthService()
    profile = await auth_service.create_or_update_profile(str(current_user.id), profile_data)
    # Convert ObjectId to string for id field
    profile_dict = profile.dict()
    profile_dict["id"] = str(profile.id)
    return profile_dict


@router.get("/profile", response_model=Optional[ProfileResponse])
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile.
    Requires authentication. Returns null if profile is not yet created.
    """
    auth_service = AuthService()
    profile = await auth_service.get_profile(str(current_user.id))
    if not profile:
        return None
    # Convert ObjectId to string for id field
    profile_dict = profile.dict()
    profile_dict["id"] = str(profile.id)
    return profile_dict


@router.post("/start-session", response_model=SessionResponse)
async def start_interview_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a new interview session.
    
    - **job_role**: Job role for this session
    - **difficulty_level**: Difficulty level (easy, medium, hard)
    
    Returns a unique session_id for tracking the interview.
    Requires authentication.
    """
    auth_service = AuthService()
    session = await auth_service.create_session(str(current_user.id), session_data)
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def get_user_sessions(current_user: User = Depends(get_current_active_user)):
    """
    Get all interview sessions for current user.
    Requires authentication.
    """
    auth_service = AuthService()
    sessions = await auth_service.get_user_sessions(str(current_user.id))
    return sessions
