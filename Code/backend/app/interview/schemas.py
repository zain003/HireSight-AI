"""Schemas for the live interview module APIs."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

from app.interview.domain.interview_models import AnswerEvaluation, FrameAnalysisResult, InterviewReport


class LiveInterviewStartRequest(BaseModel):
    job_post_id: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None
    candidate_skills: List[str] = Field(default_factory=list)
    candidate_name: Optional[str] = None
    # Fixed product: 2 intro + 7 technical + 4 behavioral + 4 CV + 3 coding = 20.
    num_questions: int = Field(default=20, ge=20, le=20)


class LiveInterviewQuestion(BaseModel):
    question_id: str
    question_index: int
    question_text: str
    question_type: str
    stage: Optional[str] = None
    difficulty: Optional[str] = None
    # Passed through for coding evaluation (starter code, public tests); omitted for verbal-only questions.
    coding_challenge: Optional[Dict[str, Any]] = None


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
    aggregate_scores: Dict[str, float]
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
