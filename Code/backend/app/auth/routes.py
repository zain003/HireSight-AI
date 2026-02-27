"""
API routes for authentication module.
Follows Clean Architecture - API Layer.
No business logic here, delegates to service layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    ProfileCreate, ProfileResponse,
    SessionCreate, SessionResponse
)
from app.auth.service import AuthService
from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.core.security import create_access_token
from app.core.exceptions import ValidationError, AuthenticationError


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: Unique username (3-50 characters)
    - **password**: Strong password (min 8 characters)
    - **full_name**: Optional full name
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(user_data)
        return user
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    - **username**: Username
    - **password**: Password
    
    Returns JWT access token for subsequent requests.
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/profile", response_model=ProfileResponse)
async def create_or_update_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update user profile.
    
    - **job_role**: Target job role (e.g., "Software Engineer")
    - **difficulty_level**: Interview difficulty (easy, medium, hard)
    - **experience_years**: Years of experience (optional)
    
    Requires authentication.
    """
    auth_service = AuthService(db)
    profile = auth_service.create_or_update_profile(current_user.id, profile_data)
    return profile


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.
    Requires authentication.
    """
    auth_service = AuthService(db)
    profile = auth_service.get_profile(current_user.id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.post("/start-session", response_model=SessionResponse)
async def start_interview_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start a new interview session.
    
    - **job_role**: Job role for this session
    - **difficulty_level**: Difficulty level (easy, medium, hard)
    
    Returns a unique session_id for tracking the interview.
    Requires authentication.
    """
    auth_service = AuthService(db)
    session = auth_service.create_session(current_user.id, session_data)
    return session


@router.get("/sessions", response_model=list[SessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all interview sessions for current user.
    Requires authentication.
    """
    auth_service = AuthService(db)
    sessions = auth_service.get_user_sessions(current_user.id)
    return sessions
