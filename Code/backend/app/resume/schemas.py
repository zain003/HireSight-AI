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


class ResumeParseResponse(BaseModel):
    """Response for resume parsing"""
    skills: List[str]
    experience: ExperienceInfo
    domain: str
    raw_text_length: int
    message: str = "Resume parsed successfully"


class SkillExtractionRequest(BaseModel):
    """Request for skill extraction from text"""
    text: str
    use_embeddings: bool = True
