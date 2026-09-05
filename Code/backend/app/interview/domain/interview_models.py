"""Pydantic domain models for the live interview module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.interview.domain.role_taxonomy import SeniorityLevel


class QuestionStage(str, Enum):
    """Paced stages for structured, explainable live interviews."""
    ICEBREAKER = "icebreaker"
    CORE_TECHNICAL = "core_technical"
    DEEP_DIVE = "deep_dive"
    CODING = "coding"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class QuestionRubric(BaseModel):
    """Deterministic grading rubric and reference answer key for an interview question."""
    reference_answer: str
    key_concepts_expected: List[str] = Field(default_factory=list)
    depth_criteria: Dict[str, str] = Field(
        default_factory=lambda: {
            "basic": "Candidate demonstrates superficial understanding with partial concepts.",
            "intermediate": "Candidate explains standard working principles and typical use cases.",
            "advanced": "Candidate explains deep internal mechanics, performance trade-offs, and edge cases.",
        }
    )
    scoring_guide: Dict[str, float] = Field(
        default_factory=lambda: {
            "relevance_max": 30.0,
            "depth_max": 40.0,
            "accuracy_max": 30.0,
        }
    )


class InterviewQuestion(BaseModel):
    """Structured interview question with stage pacing and reference evaluation rubric."""
    question_id: str
    question_index: int
    stage: QuestionStage
    competency_area: str
    difficulty: SeniorityLevel
    question_text: str
    rubric: QuestionRubric
    coding_challenge_id: Optional[str] = None
    coding_challenge: Optional[Dict[str, Any]] = None


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


class ObservableCVMetrics(BaseModel):
    """Normalized observable computer vision metrics from video frames."""
    gaze_stability_ratio: float = 0.0      # 0-100 (percentage of frames looking at screen center)
    head_pose_variance: float = 0.0        # 0-100 (inverse of angular variance in pitch/yaw/roll)
    facial_movement_dynamics: float = 0.0  # 0-100 (measured micro-movement dynamics)
    frame_presence_ratio: float = 0.0      # 0-100 (face detected frame ratio)
    blink_frequency_cpm: float = 0.0       # Blinks per minute
    observable_flags: List[str] = Field(default_factory=list)  # Observable physical anomalies only


class ObservableVocalMetrics(BaseModel):
    """Normalized observable acoustic and vocal pattern metrics from audio streams."""
    speaking_rate_wpm: float = 0.0         # Words per minute (conversational norm: 120-160)
    pause_duration_ratio: float = 0.0      # Total pause duration / total answer duration (0.0 to 1.0)
    pitch_semitone_variance: float = 0.0   # F0 dynamic range in semitones
    vocal_energy_rms: float = 0.0          # Root Mean Square energy stability
    speech_clarity_score: float = 0.0      # 0-100 (spectral & harmonic stability)
    acoustic_flags: List[str] = Field(default_factory=list)  # Measurable acoustic anomalies only


class FrameAnalysisResult(BaseModel):
    blink_count: int = 0
    gaze_direction: str = "center"
    dominant_emotion: EmotionLabel = EmotionLabel.NEUTRAL
    face_detected: bool = True
    looking_away_ratio: float = 0.0
    suspicious_flags: List[str] = Field(default_factory=list)
    observable_cv_metrics: Optional[ObservableCVMetrics] = None


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
