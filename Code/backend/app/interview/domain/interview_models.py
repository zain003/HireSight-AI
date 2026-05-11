"""Pydantic domain models for the live interview module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    INTRODUCTION = "introduction"
    ICEBREAKER = "icebreaker"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    CV_BASED = "cv_based"
    CODING = "coding"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"
    SITUATIONAL = "situational"


class InterviewStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmotionLabel(str, Enum):
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    ENGAGED = "engaged"
    NERVOUS = "nervous"
    SUSPICIOUS = "suspicious"


class FrameAnalysisResult(BaseModel):
    blink_count: int = 0
    gaze_direction: str = "center"
    dominant_emotion: EmotionLabel = EmotionLabel.NEUTRAL
    face_detected: bool = True
    looking_away_ratio: float = 0.0
    suspicious_flags: List[str] = Field(default_factory=list)


class AnswerEvaluation(BaseModel):
    question_index: int = 0
    question_text: str = ""
    question_type: QuestionType = QuestionType.TECHNICAL
    candidate_transcript: str = ""
    relevance_score: float = 0.0
    depth_score: float = 0.0
    communication_score: float = 0.0
    key_points_covered: List[str] = Field(default_factory=list)
    missed_points: List[str] = Field(default_factory=list)
    is_correct: bool = False
    accuracy_score: float = 0.0
    follow_up_triggered: bool = False
    coaching_detected: bool = False
    frame_analysis: Optional[FrameAnalysisResult] = None
    evaluator_notes: str = ""


class InterviewReport(BaseModel):
    session_id: str
    candidate_id: str
    candidate_name: str
    job_role: str
    interview_date: datetime = Field(default_factory=datetime.utcnow)
    status: InterviewStatus = InterviewStatus.COMPLETED
    total_questions_asked: int = 0
    overall_score: float = 0.0
    technical_score: float = 0.0
    communication_score: float = 0.0
    behavioral_score: float = 0.0
    video_integrity_score: float = 0.0
    evaluations: List[AnswerEvaluation] = Field(default_factory=list)
    behavioral_summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendation: str = ""
    red_flags: List[str] = Field(default_factory=list)
    hiring_decision_notes: str = ""


class InterviewSession(BaseModel):
    session_id: str
    candidate_id: str
    candidate_name: str
    job_role: str
    job_description: Optional[str] = None
    candidate_skills: List[str] = Field(default_factory=list)
    questions: List[dict] = Field(default_factory=list)
    evaluations: List[AnswerEvaluation] = Field(default_factory=list)
    frame_snapshots: List[FrameAnalysisResult] = Field(default_factory=list)
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
