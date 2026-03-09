"""
Business logic for resume module.
Follows Clean Architecture - Service Layer.
MongoDB version - no JSON serialization needed!
"""
import os
from typing import Dict, List, Tuple

from app.resume.parser import get_parser
from app.ai.extraction import get_extraction_service
from app.auth.service import AuthService
from app.core.exceptions import FileProcessingError, NotFoundError


class ResumeService:
    """Service class for resume operations (MongoDB version)"""

    # Computing-related keywords for validation
    COMPUTING_KEYWORDS = {
        # Core computing terms
        "software", "developer", "engineer", "programming", "coding", "algorithm",
        "database", "api", "frontend", "backend", "fullstack", "full-stack",
        "web development", "mobile development", "app development",
        "computer science", "information technology", "it", "tech",
        
        # Programming languages (common ones)
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "php", "ruby", "swift", "kotlin", "scala", "react", "angular", "vue",
        
        # Technologies
        "docker", "kubernetes", "aws", "azure", "gcp", "cloud", "devops",
        "machine learning", "deep learning", "artificial intelligence", "ai",
        "data science", "data analysis", "sql", "nosql", "mongodb", "postgresql",
        "git", "github", "gitlab", "ci/cd", "jenkins", "terraform",
        
        # Job roles
        "software engineer", "data scientist", "data engineer", "ml engineer",
        "devops engineer", "cloud engineer", "qa engineer", "sdet",
        "frontend developer", "backend developer", "full stack developer",
        "mobile developer", "game developer", "security engineer",
    }

    # Non-computing keywords that indicate wrong field
    NON_COMPUTING_KEYWORDS = {
        # Medical
        "doctor", "physician", "surgeon", "nurse", "medical", "hospital",
        "patient", "clinical", "pharmacy", "pharmacist", "mbbs", "md",
        "healthcare", "diagnosis", "treatment", "medicine",
        
        # Civil/Mechanical
        "civil engineer", "mechanical engineer", "construction", "building",
        "structural", "architecture", "autocad", "revit", "surveying",
        "concrete", "steel", "hvac", "plumbing", "electrical wiring",
        
        # Sales/Business (non-tech)
        "sales representative", "sales executive", "salesman", "salesperson",
        "retail", "customer service representative", "cashier", "store manager",
        "insurance agent", "real estate agent", "broker",
        
        # Other non-computing
        "teacher", "professor", "lecturer", "accountant", "lawyer", "attorney",
        "chef", "cook", "driver", "mechanic", "plumber", "electrician",
        "farmer", "agriculture", "textile", "fashion designer",
    }

    def __init__(self):
        self.parser = get_parser()
        self.extraction_service = get_extraction_service()
        self.auth_service = AuthService()

    def _validate_computing_resume(self, text: str, extracted_data: Dict) -> Tuple[bool, str]:
        """
        Multi-layered validation to ensure resume is computing-related.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        text_lower = text.lower()
        
        # ═══════════════════════════════════════════════════════════════════
        # LAYER 1: Check for non-computing keywords (REJECT immediately)
        # ═══════════════════════════════════════════════════════════════════
        non_computing_matches = []
        for keyword in self.NON_COMPUTING_KEYWORDS:
            if keyword in text_lower:
                non_computing_matches.append(keyword)
        
        if len(non_computing_matches) >= 3:
            return False, (
                f"❌ This resume appears to be from a non-computing field. "
                f"Detected: {', '.join(non_computing_matches[:3])}. "
                f"This system only accepts resumes for Software Engineering, Data Science, "
                f"DevOps, Cloud Engineering, and other computing/IT fields."
            )
        
        # ═══════════════════════════════════════════════════════════════════
        # LAYER 2: Check extracted skills (PRIMARY validation)
        # ═══════════════════════════════════════════════════════════════════
        skills = extracted_data.get("skills", [])
        
        if len(skills) < 3:
            return False, (
                f"❌ Insufficient technical skills detected ({len(skills)} found). "
                f"This system requires resumes with at least 3 computing/technical skills "
                f"(e.g., Python, Java, React, AWS, Docker, SQL, etc.). "
                f"Please ensure your resume highlights your technical expertise."
            )
        
        # ═══════════════════════════════════════════════════════════════════
        # LAYER 3: Check domain classification
        # ═══════════════════════════════════════════════════════════════════
        domain = extracted_data.get("domain", "general")
        
        if domain == "general":
            # Check if there are computing keywords in text as fallback
            computing_keyword_count = sum(
                1 for keyword in self.COMPUTING_KEYWORDS 
                if keyword in text_lower
            )
            
            if computing_keyword_count < 5:
                return False, (
                    f"❌ Could not identify a computing domain from your resume. "
                    f"This system only accepts resumes for: Software Engineering, "
                    f"Data Science, Machine Learning, DevOps, Cloud Engineering, "
                    f"Mobile Development, QA/Testing, Cybersecurity, and other IT fields. "
                    f"Please ensure your resume clearly mentions your technical role and skills."
                )
        
        # ═══════════════════════════════════════════════════════════════════
        # LAYER 4: Check job titles (SUPPLEMENTARY validation)
        # ═══════════════════════════════════════════════════════════════════
        job_titles = extracted_data.get("job_titles", [])
        
        # If we have skills but no job titles, check text for computing keywords
        if len(job_titles) == 0 and len(skills) >= 3:
            computing_keyword_count = sum(
                1 for keyword in self.COMPUTING_KEYWORDS 
                if keyword in text_lower
            )
            
            if computing_keyword_count < 3:
                return False, (
                    f"❌ Could not identify computing-related job roles in your resume. "
                    f"Please ensure your resume includes job titles like: Software Engineer, "
                    f"Data Scientist, DevOps Engineer, Full Stack Developer, etc."
                )
        
        # ═══════════════════════════════════════════════════════════════════
        # LAYER 5: Cross-validation (skills + domain + keywords)
        # ═══════════════════════════════════════════════════════════════════
        computing_keyword_count = sum(
            1 for keyword in self.COMPUTING_KEYWORDS 
            if keyword in text_lower
        )
        
        # Strong validation: Must have good skills AND computing keywords
        if len(skills) >= 3 and computing_keyword_count >= 5:
            return True, ""
        
        # Moderate validation: Good skills with recognized domain
        if len(skills) >= 5 and domain != "general":
            return True, ""
        
        # Weak signal: Has some skills but not enough evidence
        if len(skills) >= 3 and computing_keyword_count < 5:
            return False, (
                f"⚠️ Your resume has some technical skills ({len(skills)} found) but lacks "
                f"sufficient computing context. Please ensure your resume clearly describes "
                f"your software development, data science, or IT experience with specific "
                f"projects, technologies, and achievements."
            )
        
        # Default reject
        return False, (
            f"❌ This resume does not meet the requirements for computing/IT fields. "
            f"Please upload a resume with technical skills, programming experience, "
            f"and computing-related job roles."
        )

    def parse_resume(self, file_path: str) -> Dict:
        """
        Parse resume file and extract information.
        Validates that resume is computing-related.

        Args:
            file_path: Path to resume file

        Returns:
            Dictionary with extracted information

        Raises:
            FileProcessingError: If parsing fails or resume is not computing-related
        """
        # Extract text from file
        text = self.parser.parse_file(file_path)

        if not text or len(text) < 50:
            raise FileProcessingError(
                "❌ Could not extract sufficient text from resume. "
                "Please ensure your resume is a valid PDF, DOCX, or image file with readable text."
            )

        # Extract structured information using AI
        extracted_data = self.extraction_service.extract_all(text)

        # ✅ VALIDATE: Ensure resume is computing-related
        is_valid, error_message = self._validate_computing_resume(text, extracted_data)
        
        if not is_valid:
            raise FileProcessingError(error_message)

        return extracted_data

    async def save_resume_to_profile(self, user_id: str, file_path: str) -> Dict:
        """
        Parse resume and save extracted information to user profile.
        
        MongoDB version - stores lists natively (no JSON serialization!)

        Args:
            user_id: User ID (MongoDB ObjectId as string)
            file_path: Path to uploaded resume

        Returns:
            Extracted information
        """
        # Parse resume
        extracted_data = self.parse_resume(file_path)

        # MongoDB stores lists natively - no JSON serialization needed! 🎉
        skills = extracted_data["skills"]
        experienced_skills = extracted_data["experienced_skills"]
        known_skills = extracted_data["known_skills"]
        job_titles = extracted_data["job_titles"]
        education = extracted_data["education"]
        projects = extracted_data["projects"]
        certifications = extracted_data["certifications"]
        companies = extracted_data["experience"].get("companies", [])
        domain = extracted_data["domain"]
        experience_years = extracted_data["experience"].get("years")

        # Determine job_role from extracted job titles
        job_role = extracted_data["job_titles"][0] if extracted_data["job_titles"] else None

        await self.auth_service.update_profile_resume(
            user_id=user_id,
            resume_path=file_path,
            skills=skills,
            experienced_skills=experienced_skills,
            known_skills=known_skills,
            domain=domain,
            job_titles=job_titles,
            education=education,
            projects=projects,
            certifications=certifications,
            companies=companies,
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
