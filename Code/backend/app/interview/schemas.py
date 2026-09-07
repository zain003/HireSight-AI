"""Schemas for the live interview module APIs."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    CodingChallengeEvaluation,
    FrameAnalysisResult,
    InterviewReport,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    TestCaseResult,
)
from app.interview.domain.scoring_models import (
    FiveDimensionScores,
    TailoredFeedback,
)


class LiveInterviewStartRequest(BaseModel):
    job_post_id: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None
    candidate_skills: List[str] = Field(default_factory=list)
    candidate_name: Optional[str] = None
    num_questions: int = Field(default=20, ge=4, le=30)


class LiveInterviewQuestion(BaseModel):
    question_id: str
    question_index: int
    question_text: str
    question_type: str
    stage: Optional[str] = None
    difficulty: Optional[str] = None
    parent_question_id: Optional[str] = None
    # Passed through for coding evaluation (starter code, public tests); omitted for verbal-only questions.
    coding_challenge: Optional[Dict[str, Any]] = None


class InterviewSessionState(BaseModel):
    session_id: str
    current_question_index: int
    total_questions: int
    completed_evaluations_count: int
    current_question: Optional[Dict[str, Any]] = None
    questions: List[LiveInterviewQuestion] = Field(default_factory=list)
    status: str


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
    # Enhanced metrics
    behavioral_metrics: Optional[Dict[str, float]] = None
    vocal_metrics: Optional[Dict[str, float]] = None


class InterviewReportResponse(BaseModel):
    session_id: str
    status: str
    aggregate_scores: Dict[str, Any]
    report: InterviewReport
    # Enhanced recruiter report
    recruiter_report: Optional[Dict[str, Any]] = None


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


# --- Local code execution (stdin / stdout public tests) ---

SUPPORTED_CODE_LANGS = frozenset({"python", "javascript", "c", "cpp", "java"})

_CODE_LANG_ALIASES = {
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "c++": "cpp",
    "cplusplus": "cpp",
}


class CodingRunTestCaseIn(BaseModel):
    stdin: str = ""
    expected_stdout: str = ""
    description: Optional[str] = None


class RunCodeRequest(BaseModel):
    """Run candidate source against public test cases (trusted caller sends cases from session)."""

    language: str
    source_code: str = Field(..., max_length=400_000)
    test_cases: List[CodingRunTestCaseIn] = Field(..., min_length=1, max_length=24)
    timeout_seconds: Optional[float] = Field(default=None, ge=1.0, le=60.0)

    @field_validator("language")
    @classmethod
    def normalize_lang(cls, v: str) -> str:
        key = (v or "").strip().lower()
        key = _CODE_LANG_ALIASES.get(key, key)
        if key not in SUPPORTED_CODE_LANGS:
            raise ValueError(
                f"Unsupported language: {v}. Use one of: {sorted(SUPPORTED_CODE_LANGS)}."
            )
        return key


class CodingRunTestResult(BaseModel):
    index: int
    passed: bool
    stdin: str = ""
    expected_stdout: str = ""
    actual_stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    description: Optional[str] = None
    error: Optional[str] = None


class RunCodeResponse(BaseModel):
    compile_success: bool
    compile_output: str = ""
    missing_tools: List[str] = Field(default_factory=list)
    results: List[CodingRunTestResult]
    all_passed: bool


# Alias for spec contract compliance
RunPublicCodeResponse = RunCodeResponse


class SubmitCodingChallengeRequest(BaseModel):
    """Candidate submission of coding challenge code for server-side evaluation."""
    challenge_id: str
    language: str
    source_code: str = Field(..., max_length=400_000)
    question_index: Optional[int] = None

    @field_validator("language")
    @classmethod
    def normalize_lang(cls, v: str) -> str:
        key = (v or "").strip().lower()
        key = _CODE_LANG_ALIASES.get(key, key)
        if key not in SUPPORTED_CODE_LANGS:
            raise ValueError(
                f"Unsupported language: {v}. Use one of: {sorted(SUPPORTED_CODE_LANGS)}."
            )
        return key


# --- Role & Competency Configuration (FEAT-001) ---

class CompetencyWeightOut(BaseModel):
    competency_area: str
    importance_weight: float
    required_concepts: List[str]


class RoleDetailOut(BaseModel):
    id: str
    title: str
    description: str
    competencies: List[CompetencyWeightOut]


class RoleConfigResponse(BaseModel):
    supported_roles: List[RoleDetailOut]
    default_seniority: str
    seniority_levels: List[str]


class RoleFitCompetencyBreakdown(BaseModel):
    competency_area: str
    importance_weight: float
    coverage_ratio: float
    weighted_score: float
    matched_concepts: List[str]
    missing_concepts: List[str]


class RoleFitRequest(BaseModel):
    role: str
    skills: List[str] = Field(default_factory=list)


class RoleFitResponse(BaseModel):
    role: str
    overall_fit_score: float
    competency_breakdown: List[RoleFitCompetencyBreakdown]
    matched_skills: List[str]
    missing_concepts: List[str]
    total_required_concepts: int
    total_matched_concepts: int


# --- Recruiter Report Export (FEAT-009) ---

class RecruiterReportExportPayload(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    scores: FiveDimensionScores
    feedback: TailoredFeedback
    questions_summary: List[Dict[str, Any]] = Field(default_factory=list)
    coding_summary: Optional[Dict[str, Any]] = None
    cv_summary: ObservableCVMetrics
    vocal_summary: ObservableVocalMetrics


class LiveSTTRequest(BaseModel):
    audio_base64: str
    audio_format: str = "webm"
    language: str = "en"


class LiveSTTResponse(BaseModel):
    text: str


