"""Schemas for the live interview module APIs."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.interview.domain.interview_models import AnswerEvaluation, FrameAnalysisResult, InterviewReport


class LiveInterviewStartRequest(BaseModel):
    job_post_id: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None
    candidate_skills: List[str] = Field(default_factory=list)
    candidate_name: Optional[str] = None
    num_questions: int = Field(default=8, ge=4, le=12)


class LiveInterviewQuestion(BaseModel):
    question_id: str
    question_index: int
    question_text: str
    question_type: str


class LiveInterviewStartResponse(BaseModel):
    session_id: str
    questions: List[LiveInterviewQuestion]


class SubmitAnswerRequest(BaseModel):
    question_index: int
    audio_base64: Optional[str] = None
    transcript_text: Optional[str] = None
    audio_format: str = "webm"
    language: str = "en"
    frame_base64_list: List[str] = Field(default_factory=list)


class SubmitAnswerResponse(BaseModel):
    transcript: str
    evaluation: AnswerEvaluation
    per_answer_score: float
    follow_up_question: Optional[LiveInterviewQuestion] = None


class InterviewReportResponse(BaseModel):
    session_id: str
    status: str
    aggregate_scores: Dict[str, float]
    report: InterviewReport


class FaceRegisterRequest(BaseModel):
    image_base64: str


class FaceVerifyRequest(BaseModel):
    image_base64: str


class FrameAnalyzeRequest(BaseModel):
    frame_base64_list: List[str] = Field(default_factory=list)


class FrameAnalyzeResponse(BaseModel):
    analysis: FrameAnalysisResult


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    rate: Optional[str] = None
    pitch: Optional[str] = None


class TTSResponse(BaseModel):
    audio_base64: str
    format: str = "mp3"
