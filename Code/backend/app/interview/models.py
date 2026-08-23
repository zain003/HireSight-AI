"""Interview module data models."""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    FrameAnalysisResult,
    InterviewReport,
    InterviewStatus,
)


class InterviewSession(Document):
    """Stores questions, evaluations, and report data for a live interview."""

    session_id: Indexed(str, unique=True)
    user_id: Indexed(str)
    candidate_id: str
    candidate_name: str
    job_post_id: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None
    required_job_skills: List[str] = Field(default_factory=list)
    candidate_skills: List[str] = Field(default_factory=list)
    status: str = InterviewStatus.IN_PROGRESS.value

    questions: List[Dict[str, Any]] = Field(default_factory=list)
    current_question_index: int = 0

    evaluations: List[AnswerEvaluation] = Field(default_factory=list)
    frame_snapshots: List[FrameAnalysisResult] = Field(default_factory=list)
    report: Optional[InterviewReport] = None
    
    # Enhanced evaluation metrics
    behavioral_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    vocal_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    coding_results: List[Dict[str, Any]] = Field(default_factory=list)
    recruiter_report: Optional[Dict[str, Any]] = None

    aggregate_scores: Dict[str, float] = Field(default_factory=dict)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_sessions"
        indexes = ["session_id", "user_id"]
