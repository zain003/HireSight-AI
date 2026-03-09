"""
Business logic for authentication module.
Follows Clean Architecture - Service Layer.
MongoDB version using Beanie ODM.
"""
from typing import Optional
import uuid
from datetime import datetime

from app.auth.models import User, Profile, Session as SessionModel
from app.auth.schemas import UserCreate, ProfileCreate, SessionCreate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError


class AuthService:
    """Service class for authentication operations (MongoDB version)"""
    
    async def create_user(self, user_data: UserCreate) -> User:
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
        existing_user = await User.find_one(
            {"$or": [{"email": user_data.email}, {"username": user_data.username}]}
        )
        
        if existing_user:
            raise ValidationError("User with this email or username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await db_user.insert()
        
        return db_user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username
            password: Plain password
            
        Returns:
            User object if authenticated, None otherwise
        """
        user = await User.find_one({"username": username})
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await User.get(user_id)
    
    async def create_or_update_profile(self, user_id: str, profile_data: ProfileCreate) -> Profile:
        """
        Create or update user profile.
        
        Args:
            user_id: User ID (MongoDB ObjectId as string)
            profile_data: Profile data
            
        Returns:
            Created/updated profile object
        """
        # Check if profile exists
        profile = await Profile.find_one({"user_id": user_id})
        
        if profile:
            # Update existing profile
            profile.job_role = profile_data.job_role
            profile.difficulty_level = profile_data.difficulty_level
            profile.experience_years = profile_data.experience_years
            profile.updated_at = datetime.utcnow()
            await profile.save()
        else:
            # Create new profile
            profile = Profile(
                user_id=user_id,
                job_role=profile_data.job_role,
                difficulty_level=profile_data.difficulty_level,
                experience_years=profile_data.experience_years,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await profile.insert()
        
        return profile
    
    async def get_profile(self, user_id: str) -> Optional[Profile]:
        """Get user profile"""
        return await Profile.find_one({"user_id": user_id})
    
    async def update_profile_resume(
        self, user_id: str, resume_path: str,
        skills: list = None, experienced_skills: list = None, known_skills: list = None,
        domain: str = None, job_titles: list = None, education: list = None,
        projects: list = None, certifications: list = None,
        companies: list = None, experience_years: int = None,
        job_role: str = None,
    ) -> Profile:
        """
        Update profile with resume information.
        Creates profile if it doesn't exist.
        
        NOTE: MongoDB stores lists natively - no JSON serialization needed!
        """
        profile = await Profile.find_one({"user_id": user_id})
        
        if not profile:
            profile = Profile(
                user_id=user_id,
                resume_path=resume_path,
                skills=skills or [],
                experienced_skills=experienced_skills or [],
                known_skills=known_skills or [],
                domain=domain,
                job_titles=job_titles or [],
                education=education or [],
                projects=projects or [],
                certifications=certifications or [],
                companies=companies or [],
                experience_years=experience_years,
                job_role=job_role,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await profile.insert()
        else:
            profile.resume_path = resume_path
            if skills is not None:
                profile.skills = skills
            if experienced_skills is not None:
                profile.experienced_skills = experienced_skills
            if known_skills is not None:
                profile.known_skills = known_skills
            if domain:
                profile.domain = domain
            if job_titles is not None:
                profile.job_titles = job_titles
            if education is not None:
                profile.education = education
            if projects is not None:
                profile.projects = projects
            if certifications is not None:
                profile.certifications = certifications
            if companies is not None:
                profile.companies = companies
            if experience_years is not None:
                profile.experience_years = experience_years
            if job_role:
                profile.job_role = job_role
            profile.updated_at = datetime.utcnow()
            await profile.save()
        
        return profile
    
    async def create_session(self, user_id: str, session_data: SessionCreate) -> SessionModel:
        """
        Create a new interview session.
        
        Args:
            user_id: User ID (MongoDB ObjectId as string)
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
            status="active",
            created_at=datetime.utcnow()
        )
        
        await db_session.insert()
        
        return db_session
    
    async def get_user_sessions(self, user_id: str):
        """Get all sessions for a user"""
        return await SessionModel.find({"user_id": user_id}).to_list()
