"""
Pydantic schemas for resume module.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class ResumeUploadResponse(BaseModel):
    """Response for resume upload"""
    message: str
    file_path: str
    file_size: int


class ExperienceInfo(BaseModel):
    """Experience information"""
    years: Optional[int] = None
    summary: str = ""
    companies: List[str] = []


class EducationInfo(BaseModel):
    """Education entry"""
    degree: str
    institution: str = ""
    year: Optional[str] = None


class ProjectInfo(BaseModel):
    """Project entry"""
    name: str
    description: str = ""


class ResumeParseResponse(BaseModel):
    """Response for resume parsing"""
    skills: List[str]
    job_titles: List[str] = []
    experience: ExperienceInfo
    education: List[EducationInfo] = []
    projects: List[ProjectInfo] = []
    certifications: List[str] = []
    domain: str
    raw_text_length: int
    extraction_json_path: str = ""
    message: str = "Resume parsed successfully"


class ResumeParseDebugResponse(ResumeParseResponse):
    """Response for debug resume parsing with traceability fields."""
    experienced_skills: List[str] = []
    known_skills: List[str] = []
    ner_entities: Dict[str, List[str]] = {}
    raw_text: str = ""
    debug_file_path: str = ""


class SkillExtractionRequest(BaseModel):
    """Request for skill extraction from text"""
    text: str
    use_embeddings: bool = True
