"""
API routes for authentication module.
Follows Clean Architecture - API Layer.
No business logic here, delegates to service layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.auth.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    ProfileCreate, ProfileResponse,
    SessionCreate, SessionResponse
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


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile.
    Requires authentication.
    """
    auth_service = AuthService()
    profile = await auth_service.get_profile(str(current_user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
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
