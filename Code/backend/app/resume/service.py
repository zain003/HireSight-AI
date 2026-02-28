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

        # Serialize all fields to JSON
        skills_json = json.dumps(extracted_data["skills"])
        job_titles_json = json.dumps(extracted_data["job_titles"])
        education_json = json.dumps(extracted_data["education"])
        projects_json = json.dumps(extracted_data["projects"])
        certifications_json = json.dumps(extracted_data["certifications"])
        companies_json = json.dumps(extracted_data["experience"].get("companies", []))
        domain = extracted_data["domain"]
        experience_years = extracted_data["experience"].get("years")

        # Determine job_role from extracted job titles
        job_role = extracted_data["job_titles"][0] if extracted_data["job_titles"] else None

        self.auth_service.update_profile_resume(
            user_id=user_id,
            resume_path=file_path,
            skills=skills_json,
            domain=domain,
            job_titles=job_titles_json,
            education=education_json,
            projects=projects_json,
            certifications=certifications_json,
            companies=companies_json,
            experience_years=experience_years,
            job_role=job_role,
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
