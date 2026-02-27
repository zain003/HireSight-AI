"""
Business logic for authentication module.
Follows Clean Architecture - Service Layer.
No direct database or API logic here.
"""
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from app.auth.models import User, Profile, Session as SessionModel
from app.auth.schemas import UserCreate, ProfileCreate, SessionCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            ValidationError: If user already exists
        """
        # Check if user exists
        existing_user = self.db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise ValidationError("User with this email or username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username
            password: Plain password
            
        Returns:
            User object if authenticated, None otherwise
        """
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_or_update_profile(self, user_id: int, profile_data: ProfileCreate) -> Profile:
        """
        Create or update user profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data
            
        Returns:
            Created/updated profile object
        """
        # Check if profile exists
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        
        if profile:
            # Update existing profile
            profile.job_role = profile_data.job_role
            profile.difficulty_level = profile_data.difficulty_level
            profile.experience_years = profile_data.experience_years
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile = Profile(
                user_id=user_id,
                job_role=profile_data.job_role,
                difficulty_level=profile_data.difficulty_level,
                experience_years=profile_data.experience_years
            )
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_profile(self, user_id: int) -> Optional[Profile]:
        """Get user profile"""
        return self.db.query(Profile).filter(Profile.user_id == user_id).first()
    
    def update_profile_resume(self, user_id: int, resume_path: str, skills: str = None, domain: str = None) -> Profile:
        """
        Update profile with resume information.
        Creates profile if it doesn't exist.
        
        Args:
            user_id: User ID
            resume_path: Path to uploaded resume
            skills: Extracted skills (JSON string)
            domain: Detected domain
            
        Returns:
            Updated profile object
        """
        profile = self.db.query(Profile).filter(Profile.user_id == user_id).first()
        
        if not profile:
            # Auto-create profile if it doesn't exist
            profile = Profile(
                user_id=user_id,
                resume_path=resume_path,
                skills=skills,
                domain=domain
            )
            self.db.add(profile)
        else:
            # Update existing profile
            profile.resume_path = resume_path
            if skills:
                profile.skills = skills
            if domain:
                profile.domain = domain
            profile.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def create_session(self, user_id: int, session_data: SessionCreate) -> SessionModel:
        """
        Create a new interview session.
        
        Args:
            user_id: User ID
            session_data: Session creation data
            
        Returns:
            Created session object
        """
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        db_session = SessionModel(
            session_id=session_id,
            user_id=user_id,
            job_role=session_data.job_role,
            difficulty_level=session_data.difficulty_level,
            status="active"
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session
    
    def get_user_sessions(self, user_id: int):
        """Get all sessions for a user"""
        return self.db.query(SessionModel).filter(SessionModel.user_id == user_id).all()
