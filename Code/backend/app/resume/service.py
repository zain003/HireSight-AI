"""
Business logic for resume module.
Follows Clean Architecture - Service Layer.
MongoDB version - no JSON serialization needed!
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
        # Common on CS resumes (avoid false negatives in validation)
        "software architecture", "system design", "microservices", "kubernetes",
        "full stack", "computer engineering", "information systems",
    }

    # Vast non-computing keywords and domains
    # NOTE: Avoid single ambiguous tokens like "architecture", "building", "construction",
    # "author" — they match software resumes ("Clean Architecture", "building APIs",
    # "pipeline construction", "co-author"). Prefer multi-word civil/trades phrases.
    NON_COMPUTING_KEYWORDS = {
        # Medical/Healthcare
        "doctor", "physician", "surgeon", "nurse", "medical", "hospital", "patient", "clinical", "pharmacy", "pharmacist", "mbbs", "md", "healthcare", "diagnosis", "treatment", "medicine", "dentist", "veterinarian", "optometrist", "radiologist", "therapist", "nutritionist", "paramedic", "midwife", "anesthetist",
        # Civil/Mechanical/Engineering (phrases only — not bare "architecture")
        "civil engineer", "mechanical engineer", "structural engineer", "site engineer", "road engineer", "bridge engineer", "construction laborer", "construction manager", "construction site", "building codes", "hvac", "plumbing", "electrical wiring", "autocad", "revit", "surveying", "concrete pour", "steel fabrication", "manufacturing", "production engineer", "industrial engineer", "mining engineer", "chemical engineer", "materials engineer",
        # Sales/Business/Finance
        "sales representative", "sales executive", "salesman", "salesperson", "retail", "customer service representative", "cashier", "store manager", "insurance agent", "real estate agent", "broker", "accountant", "finance", "financial analyst", "investment banker", "auditor", "tax consultant", "bookkeeper", "loan officer", "bank teller", "credit analyst", "mortgage advisor",
        # Law/Government
        "lawyer", "attorney", "judge", "paralegal", "legal assistant", "court clerk", "government officer", "public administrator", "policy analyst", "diplomat", "civil servant", "politician", "legislator", "regulator",
        # Education/Academia
        "teacher", "professor", "lecturer", "educator", "school principal", "school administrator", "tutor", "instructor", "education consultant", "curriculum designer", "academic advisor", "researcher", "scholar",
        # Hospitality/Tourism
        "chef", "cook", "waiter", "waitress", "bartender", "hotel manager", "concierge", "housekeeper", "event planner", "tour guide", "travel agent", "restaurant manager", "host", "hostess",
        # Logistics/Transport
        "driver", "truck driver", "pilot", "flight attendant", "shipping clerk", "warehouse manager", "logistics coordinator", "supply chain manager", "delivery person", "courier", "dispatcher",
        # Skilled Trades/Manual Labor
        "mechanic", "plumber", "electrician", "carpenter", "welder", "roofer", "mason", "painter", "gardener", "farmer", "agriculture", "fisherman", "textile worker", "factory worker", "machine operator", "construction laborer",
        # Arts/Media/Sports (omit bare "author" — matches "co-author" on tech papers)
        "artist", "musician", "actor", "actress", "dancer", "singer", "photographer", "videographer", "graphic designer", "fashion designer", "journalist", "reporter", "editor", "writer", "novelist", "coach", "athlete", "sports trainer", "referee", "umpire", "sports manager",
        # Other non-computing
        "beautician", "hair stylist", "makeup artist", "personal trainer", "fitness instructor", "real estate developer", "property manager", "event manager", "event coordinator", "interior designer", "landscaper", "pet groomer", "childcare worker", "babysitter", "nanny", "housekeeper", "janitor", "security guard", "bouncer", "doorman", "parking attendant", "laundry worker", "cleaner", "maintenance worker", "receptionist", "secretary", "admin assistant", "office manager", "office clerk", "data entry operator", "call center agent", "telemarketer", "customer support", "help desk", "community manager", "social worker", "counselor", "psychologist", "therapist", "nutritionist", "dietitian", "speech therapist", "occupational therapist", "physical therapist", "massage therapist", "chiropractor", "acupuncturist", "home health aide", "elder care worker", "funeral director", "mortician", "embalmer", "cemetery manager", "religious leader", "priest", "imam", "rabbi", "pastor", "monk", "nun", "missionary", "volunteer coordinator", "ngo worker", "charity worker", "fundraiser", "grant writer", "donor relations", "philanthropist"
    }

    # Non-computing domains from extraction service that are strictly rejected
    NON_COMPUTING_DOMAINS = {
        "medical_healthcare": "Medical & Healthcare",
        "civil_mechanical_engineering": "Civil & Mechanical Engineering",
        "finance_accounting": "Finance & Accounting",
        "sales_marketing": "Sales & Marketing",
        "legal": "Legal",
        "education_academia": "Education & Academia",
        "non_computing": "Non-Computing",
    }

    def __init__(self):
        self.parser = get_parser()
        self.extraction_service = get_extraction_service()
        self.auth_service = AuthService()

    def _validate_computing_resume(self, text: str, extracted_data: Dict) -> Tuple[bool, str]:
        """
        Multi-layered validation to ensure resume is computing-related.
        Detects and rejects non-computing professions (medical, civil, finance, sales, legal, etc.)
        even if auxiliary digital tools (Excel, Power BI, EHR, statistical packages) are mentioned.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        import re
        text_lower = text.lower()
        domain = extracted_data.get("domain", "general")
        job_titles = [str(t).lower() for t in extracted_data.get("job_titles", [])]
        education_entries = extracted_data.get("education", [])
        skills = extracted_data.get("skills", [])

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 0: Domain Classification Gate (REJECT if detected non-computing domain)
        # ═══════════════════════════════════════════════════════════════════
        if domain in self.NON_COMPUTING_DOMAINS:
            domain_label = self.NON_COMPUTING_DOMAINS[domain]
            return False, (
                f"❌ This resume appears to be from a non-computing field ({domain_label}). "
                f"Detected domain: {domain}. "
                f"This system only accepts resumes for Software Engineering, Data Science, "
                f"DevOps, Cloud Engineering, and other computing/IT fields."
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 1: Non-Computing Job Title Rejection
        # ═══════════════════════════════════════════════════════════════════
        non_comp_title_keywords = [
            "physician", "doctor", "internist", "surgeon", "medical officer",
            "cardiologist", "radiologist", "pathologist", "pediatrician", "nurse",
            "dentist", "pharmacist", "clinical officer", "attending physician",
            "resident physician", "civil engineer", "mechanical engineer",
            "structural engineer", "site engineer", "construction manager",
            "accountant", "auditor", "sales representative", "sales executive",
            "salesman", "lawyer", "attorney", "teacher", "headmaster"
        ]
        comp_title_keywords = [
            "software", "developer", "engineer", "architect", "programmer",
            "devops", "data scientist", "data engineer", "ml engineer", "cloud",
            "qa", "sdet", "frontend", "backend", "full stack", "fullstack"
        ]
        
        has_non_comp_title = any(
            any(nct in title for nct in non_comp_title_keywords)
            for title in job_titles
        )
        has_comp_title = any(
            any(ct in title for ct in comp_title_keywords)
            for title in job_titles
        )
        
        if has_non_comp_title and not has_comp_title:
            matched_titles = [
                title for title in job_titles
                if any(nct in title for nct in non_comp_title_keywords)
            ]
            return False, (
                f"❌ Non-computing professional role detected ({', '.join(matched_titles[:3])}). "
                f"This system only accepts resumes for Software Engineering, Data Science, "
                f"DevOps, Cloud Engineering, and other computing/IT fields."
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 2: Non-Computing Qualification / Education Gate
        # ═══════════════════════════════════════════════════════════════════
        non_comp_deg_keywords = ["mbbs", "md", "mph", "bds", "pharmd", "dvm", "nursing", "llb", "jd"]
        comp_deg_keywords = ["computer science", "software", "information technology", "data science", "computer engineering", "computing"]
        
        has_non_comp_deg = any(
            any(re.search(rf"\b{re.escape(ncd)}\b", str(e.get("degree", "")).lower()) for ncd in non_comp_deg_keywords)
            for e in education_entries if isinstance(e, dict)
        )
        has_comp_deg = any(
            any(cd in str(e.get("degree", "")).lower() for cd in comp_deg_keywords)
            for e in education_entries if isinstance(e, dict)
        )
        
        if has_non_comp_deg and not has_comp_deg and not has_comp_title:
            matched_degs = [
                str(e.get("degree", "")) for e in education_entries
                if isinstance(e, dict) and any(re.search(rf"\b{re.escape(ncd)}\b", str(e.get("degree", "")).lower()) for ncd in non_comp_deg_keywords)
            ]
            return False, (
                f"❌ Non-computing qualification detected ({', '.join(matched_degs[:3])}). "
                f"This platform is designed for computing and IT candidates."
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 3: Word-boundary Non-Computing Keyword Analysis
        # ═══════════════════════════════════════════════════════════════════
        non_computing_matches = []
        for keyword in self.NON_COMPUTING_KEYWORDS:
            if len(keyword) <= 4:
                if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                    non_computing_matches.append(keyword)
            else:
                if keyword in text_lower:
                    non_computing_matches.append(keyword)

        section_fields = [
            education_entries,
            extracted_data.get("job_titles", []),
            skills,
            extracted_data.get("projects", []),
            extracted_data.get("certifications", []),
        ]
        section_matches = []
        for section in section_fields:
            for entry in section:
                entry_str = str(entry).lower()
                for keyword in self.NON_COMPUTING_KEYWORDS:
                    if len(keyword) <= 4:
                        if re.search(rf"\b{re.escape(keyword)}\b", entry_str):
                            section_matches.append(keyword)
                    else:
                        if keyword in entry_str:
                            section_matches.append(keyword)

        if (len(non_computing_matches) >= 3 or len(section_matches) >= 2) and not (has_comp_title and has_comp_deg):
            return False, (
                f"❌ This resume appears to be from a non-computing field. "
                f"Detected: {', '.join((non_computing_matches + section_matches)[:5])}. "
                f"This system only accepts resumes for Software Engineering, Data Science, "
                f"DevOps, Cloud Engineering, and other computing/IT fields."
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 4: Technical Skills Verification (Minimum 3 skills)
        # ═══════════════════════════════════════════════════════════════════
        if len(skills) < 3:
            return False, (
                f"❌ Insufficient technical skills detected ({len(skills)} found). "
                f"This system requires resumes with at least 3 computing/technical skills "
                f"(e.g., Python, Java, React, AWS, Docker, SQL, etc.). "
                f"Please ensure your resume highlights your technical expertise."
            )

        # ═══════════════════════════════════════════════════════════════════
        # LAYER 5: Domain and Computing Keywords Cross-Validation
        # ═══════════════════════════════════════════════════════════════════
        computing_keyword_count = 0
        for kw in self.COMPUTING_KEYWORDS:
            if len(kw) <= 4:
                if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                    computing_keyword_count += 1
            else:
                if kw in text_lower:
                    computing_keyword_count += 1

        if domain == "general" and computing_keyword_count < 5:
            return False, (
                f"❌ Could not identify a computing domain from your resume. "
                f"This system only accepts resumes for: Software Engineering, "
                f"Data Science, Machine Learning, DevOps, Cloud Engineering, "
                f"Mobile Development, QA/Testing, Cybersecurity, and other IT fields. "
                f"Please ensure your resume clearly mentions your technical role and skills."
            )

        if len(job_titles) == 0 and len(skills) >= 3 and computing_keyword_count < 3:
            return False, (
                f"❌ Could not identify computing-related job roles in your resume. "
                f"Please ensure your resume includes job titles like: Software Engineer, "
                f"Data Scientist, DevOps Engineer, Full Stack Developer, etc."
            )

        if len(skills) >= 3 and computing_keyword_count >= 5:
            return True, ""

        if len(skills) >= 5 and domain not in self.NON_COMPUTING_DOMAINS and domain != "general":
            return True, ""

        if len(skills) >= 3 and computing_keyword_count < 5:
            return False, (
                f"⚠️ Your resume has some technical skills ({len(skills)} found) but lacks "
                f"sufficient computing context. Please ensure your resume clearly describes "
                f"your software development, data science, or IT experience with specific "
                f"projects, technologies, and achievements."
            )

        return False, (
            f"❌ This resume does not meet the requirements for computing/IT fields. "
            f"Please upload a resume with technical skills, programming experience, "
            f"and computing-related job roles."
        )

    def _build_resume_structured_snapshot(
        self, user_id: str, resume_file_path: str, extracted_data: Dict
    ) -> Dict:
        """Serializable snapshot for JSON file + MongoDB `resume_structured`."""
        exp = extracted_data.get("experience") or {}
        if not isinstance(exp, dict):
            exp = {}
        return {
            "user_id": user_id,
            "extracted_at": datetime.utcnow().isoformat() + "Z",
            "source_resume_file": os.path.basename(resume_file_path),
            "skills": list(extracted_data.get("skills") or []),
            "experienced_skills": list(extracted_data.get("experienced_skills") or []),
            "known_skills": list(extracted_data.get("known_skills") or []),
            "job_titles": list(extracted_data.get("job_titles") or []),
            "domain": extracted_data.get("domain"),
            "experience": dict(exp),
            "education": list(extracted_data.get("education") or []),
            "projects": list(extracted_data.get("projects") or []),
            "certifications": list(extracted_data.get("certifications") or []),
            "experience_years": exp.get("years"),
            "companies": list(exp.get("companies") or []),
        }

    def _write_resume_extraction_json(self, resume_dir: str, user_id: str, snapshot: Dict) -> str:
        """Write structured extraction to disk; returns absolute path."""
        os.makedirs(resume_dir, exist_ok=True)
        fname = f"cv_extraction_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        out_path = os.path.join(resume_dir, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        return out_path

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
        extracted_data["raw_text"] = text
        extracted_data["raw_text_length"] = len(text)

        # ✅ VALIDATE: Ensure resume is computing-related
        is_valid, error_message = self._validate_computing_resume(text, extracted_data)
        
        if not is_valid:
            raise FileProcessingError(error_message)

        return extracted_data

    def parse_resume_with_debug(self, file_path: str) -> Dict:
        """
        Parse resume and return enriched debug data so extraction quality
        can be inspected from API/UI.
        """
        text = self.parser.parse_file(file_path)
        if not text or len(text) < 50:
            raise FileProcessingError(
                "❌ Could not extract sufficient text from resume. "
                "Please ensure your resume is a valid PDF, DOCX, or image file with readable text."
            )

        extracted_data = self.extraction_service.extract_all(text, include_debug=True)

        is_valid, error_message = self._validate_computing_resume(text, extracted_data)
        if not is_valid:
            raise FileProcessingError(error_message)

        debug_payload = {
            "file_path": file_path,
            "parsed_at": datetime.utcnow().isoformat() + "Z",
            "raw_text_length": len(text),
            "raw_text": text,
            "structured": {
                "skills": extracted_data.get("skills", []),
                "experienced_skills": extracted_data.get("experienced_skills", []),
                "known_skills": extracted_data.get("known_skills", []),
                "job_titles": extracted_data.get("job_titles", []),
                "experience": extracted_data.get("experience", {}),
                "education": extracted_data.get("education", []),
                "projects": extracted_data.get("projects", []),
                "certifications": extracted_data.get("certifications", []),
                "domain": extracted_data.get("domain", "general"),
            },
            "debug": extracted_data.get("debug", {}),
        }

        # Save debug JSON beside uploaded resume for easy inspection.
        debug_file_path = os.path.join(
            os.path.dirname(file_path),
            f"parsed_resume_debug_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(debug_file_path, "w", encoding="utf-8") as f:
            json.dump(debug_payload, f, ensure_ascii=False, indent=2)

        extracted_data["debug_file_path"] = debug_file_path
        extracted_data["raw_text"] = text
        extracted_data["raw_text_length"] = len(text)
        extracted_data["ner_entities"] = extracted_data.get("debug", {}).get("ner_entities", {})
        return extracted_data

    async def save_resume_to_profile(
        self,
        user_id: str,
        file_path: str,
        include_debug: bool = False,
        preferred_job_role: Optional[str] = None,
    ) -> Dict:
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
        extracted_data = (
            self.parse_resume_with_debug(file_path)
            if include_debug
            else self.parse_resume(file_path)
        )

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

        # CV-derived title (may be wrong vs what the user is applying for)
        job_role_inferred = (
            extracted_data["job_titles"][0] if extracted_data["job_titles"] else None
        )

        resume_dir = os.path.dirname(file_path)
        structured_snapshot = self._build_resume_structured_snapshot(
            user_id, file_path, extracted_data
        )
        extraction_json_path = self._write_resume_extraction_json(
            resume_dir, user_id, structured_snapshot
        )
        extracted_data["extraction_json_path"] = extraction_json_path
        extracted_data["resume_structured"] = structured_snapshot

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
            job_role_inferred=job_role_inferred,
            job_role_preferred=preferred_job_role,
            resume_structured=structured_snapshot,
            resume_extraction_json_path=extraction_json_path,
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
