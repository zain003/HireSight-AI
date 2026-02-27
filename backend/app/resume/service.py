"""
Business logic for resume module.
Follows Clean Architecture - Service Layer.
"""
from sqlalchemy.orm import Session
import os
import json
from typing import Dict

from app.resume.parser import get_parser
from app.ai.extraction import get_extraction_service
from app.auth.service import AuthService
from app.core.exceptions import FileProcessingError, NotFoundError


class ResumeService:
    """Service class for resume operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = get_parser()
        self.extraction_service = get_extraction_service()
        self.auth_service = AuthService(db)
    
    def parse_resume(self, file_path: str) -> Dict:
        """
        Parse resume file and extract information.
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Dictionary with extracted information
            
        Raises:
            FileProcessingError: If parsing fails
        """
        # Extract text from file
        text = self.parser.parse_file(file_path)
        
        if not text or len(text) < 50:
            raise FileProcessingError("Could not extract sufficient text from resume")
        
        # Extract structured information using AI
        extracted_data = self.extraction_service.extract_all(text)
        
        return extracted_data
    
    def save_resume_to_profile(self, user_id: int, file_path: str) -> Dict:
        """
        Parse resume and save extracted information to user profile.
        
        Args:
            user_id: User ID
            file_path: Path to uploaded resume
            
        Returns:
            Extracted information
        """
        # Parse resume
        extracted_data = self.parse_resume(file_path)
        
        # Update profile with extracted information
        skills_json = json.dumps(extracted_data["skills"])
        domain = extracted_data["domain"]
        
        self.auth_service.update_profile_resume(
            user_id=user_id,
            resume_path=file_path,
            skills=skills_json,
            domain=domain
        )
        
        return extracted_data
    
    def extract_skills_from_text(self, text: str, use_embeddings: bool = True) -> list:
        """
        Extract skills from raw text.
        
        Args:
            text: Input text
            use_embeddings: Whether to use semantic matching
            
        Returns:
            List of extracted skills
        """
        return self.extraction_service.extract_skills(text, use_embeddings)
