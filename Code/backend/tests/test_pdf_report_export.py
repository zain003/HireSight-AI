"""
Unit and integration tests for PDF & JSON Report Export Service (FEAT-009-BE).
"""

import io
import time
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.auth.models import User, Profile
from app.auth.dependencies import get_current_active_user, get_current_admin_user
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionType,
)
from app.interview.domain.scoring_models import (
    CandidateFitStatus,
    FiveDimensionScores,
    ScoringWeights,
    TailoredFeedback,
)
from app.interview.models import InterviewSession
from app.interview.schemas import RecruiterReportExportPayload
from app.interview.services.pdf_generator_service import (
    PDFReportGenerator,
    pdf_generator_service,
)


@pytest.fixture
def sample_payload() -> RecruiterReportExportPayload:
    scores = FiveDimensionScores(
        technical_knowledge_score=85.0,
        coding_ability_score=90.0,
        role_fit_score=75.0,
        communication_score=80.0,
        behavioral_indicators_score=85.0,
        overall_composite_score=83.75,
        fit_status=CandidateFitStatus.POTENTIAL_FIT,
        scoring_formula_audit={"audit": "0.35*85 + 0.20*90 + 0.15*75 + 0.15*80 + 0.15*85 = 83.75"},
    )

    feedback = TailoredFeedback(
        strongest_technical_areas=["Database indexing", "Distributed concurrency"],
        weakest_technical_areas=["ACID isolation levels"],
        coding_analysis_summary="Passed all 5/5 test cases with optimal time complexity.",
        communication_observations=["Speaking rate 138 WPM within optimal conversational range."],
        behavioral_observations=["Maintained 88% gaze stability on screen center."],
        missing_role_skills=["gRPC distributed protocols"],
        actionable_improvement_recommendations=["Review PostgreSQL serialization anomaly benchmarks."],
    )

    return RecruiterReportExportPayload(
        session_id="session_test_456",
        candidate_name="Alex Morgan",
        target_role="backend_engineer",
        scores=scores,
        feedback=feedback,
        questions_summary=[
            {
                "question_index": 0,
                "question_text": "Explain database indexing strategies using B-Trees.",
                "question_type": "technical",
                "stage": "core_technical",
                "competency_area": "Database Design",
                "difficulty": "senior",
                "rubric": {
                    "reference_answer": "B-Trees maintain sorted data with logarithmic search time.",
                    "key_concepts_expected": ["B-Tree", "Logarithmic", "Self-balancing"],
                },
                "transcript": "B-Trees keep keys sorted to enable fast logarithmic search in O(log N).",
                "accuracy_score": 85.0,
                "relevance_score": 90.0,
                "depth_score": 80.0,
                "communication_score": 85.0,
                "key_points_covered": ["B-Tree structure", "O(log N)"],
                "missed_points": ["Branching factor calculation"],
                "evaluator_notes": "Strong and concise explanation.",
            },
            {
                "question_index": 1,
                "question_text": "How do you mitigate race conditions in distributed systems?",
                "question_type": "technical",
                "stage": "deep_dive",
                "competency_area": "Concurrency & Distributed Systems",
                "difficulty": "senior",
                "rubric": {
                    "reference_answer": "Optimistic locking with versioning or distributed locks like Redlock.",
                    "key_concepts_expected": ["Distributed Lock", "Optimistic Locking", "Idempotency"],
                },
                "transcript": "We use optimistic locking with version columns or Redis-based distributed mutexes.",
                "accuracy_score": 90.0,
                "relevance_score": 85.0,
                "depth_score": 85.0,
                "communication_score": 90.0,
                "key_points_covered": ["Optimistic locking", "Redis distributed mutex"],
                "missed_points": [],
                "evaluator_notes": "Well articulated.",
            },
        ],
        coding_summary={
            "skipped": False,
            "challenge_id": "reverse_linked_list",
            "language": "python",
            "compile_success": True,
            "public_tests_passed": 2,
            "public_tests_total": 2,
            "hidden_tests_passed": 3,
            "hidden_tests_total": 3,
            "overall_coding_score": 100.0,
            "execution_time_total_ms": 14.5,
            "peak_memory_kb": 512.0,
        },
        cv_summary=ObservableCVMetrics(
            gaze_stability_ratio=88.5,
            head_pose_variance=82.0,
            facial_movement_dynamics=74.0,
            frame_presence_ratio=95.0,
            blink_frequency_cpm=16.5,
            observable_flags=[],
        ),
        vocal_summary=ObservableVocalMetrics(
            speaking_rate_wpm=138.0,
            pause_duration_ratio=0.15,
            pitch_semitone_variance=3.2,
            vocal_energy_rms=0.18,
            speech_clarity_score=85.0,
            acoustic_flags=[],
        ),
    )


@pytest.fixture
def mock_interview_session(sample_payload) -> InterviewSession:
    session = InterviewSession.model_construct(
        session_id=sample_payload.session_id,
        user_id="user_test_789",
        candidate_id="user_test_789",
        candidate_name=sample_payload.candidate_name,
        job_role=sample_payload.target_role,
        questions=[
            {
                "question_index": 0,
                "question_text": "Explain database indexing strategies using B-Trees.",
                "question_type": "technical",
                "stage": "core_technical",
                "competency_area": "Database Design",
                "difficulty": "senior",
                "rubric": {
                    "reference_answer": "B-Trees maintain sorted data with logarithmic search time.",
                    "key_concepts_expected": ["B-Tree", "Logarithmic", "Self-balancing"],
                },
            }
        ],
        evaluations=[
            AnswerEvaluation(
                question_index=0,
                question_text="Explain database indexing strategies using B-Trees.",
                question_type=QuestionType.TECHNICAL,
                candidate_transcript="B-Trees keep keys sorted to enable fast logarithmic search.",
                accuracy_score=85.0,
                relevance_score=90.0,
                depth_score=80.0,
                communication_score=85.0,
                is_correct=True,
                key_points_covered=["B-Tree", "Logarithmic"],
                missed_points=[],
            )
        ],
        behavioral_metrics=[
            {
                "gaze_stability_ratio": 88.5,
                "head_pose_variance": 82.0,
                "facial_movement_dynamics": 74.0,
                "frame_presence_ratio": 95.0,
                "blink_frequency_cpm": 16.5,
                "observable_flags": [],
            }
        ],
        vocal_metrics=[
            {
                "speaking_rate_wpm": 138.0,
                "pause_duration_ratio": 0.15,
                "pitch_semitone_variance": 3.2,
                "vocal_energy_rms": 0.18,
                "speech_clarity_score": 85.0,
                "acoustic_flags": [],
            }
        ],
        coding_results=[
            {
                "challenge_id": "reverse_linked_list",
                "language": "python",
                "compile_success": True,
                "public_tests_passed": 2,
                "public_tests_total": 2,
                "hidden_tests_passed": 3,
                "hidden_tests_total": 3,
                "overall_coding_score": 100.0,
                "execution_time_total_ms": 14.5,
                "peak_memory_kb": 512.0,
            }
        ],
        aggregate_scores={"overall_score": 83.75},
        recruiter_report={
            "five_dimension_scores": sample_payload.scores.model_dump(),
            "tailored_feedback": sample_payload.feedback.model_dump(),
        },
        status="completed",
        ended_at=datetime.utcnow(),
    )
    return session


def test_json_export_contains_all_5_dimensions(mock_interview_session):
    """Assert JSON export payload contains all 5 scoring dimensions and complete sub-models."""
    payload = pdf_generator_service.build_export_payload(mock_interview_session)

    assert isinstance(payload, RecruiterReportExportPayload)
    assert payload.session_id == "session_test_456"
    assert payload.candidate_name == "Alex Morgan"
    assert payload.target_role == "backend_engineer"

    # Verify 5 dimensions
    scores = payload.scores
    assert scores.technical_knowledge_score == 85.0
    assert scores.coding_ability_score == 90.0
    assert scores.role_fit_score >= 0.0
    assert scores.communication_score >= 0.0
    assert scores.behavioral_indicators_score >= 0.0
    assert scores.overall_composite_score > 0.0
    assert isinstance(scores.fit_status, CandidateFitStatus)

    # Verify Tailored Feedback
    fb = payload.feedback
    assert len(fb.strongest_technical_areas) > 0
    assert len(fb.actionable_improvement_recommendations) > 0

    # Verify Multimodal CV & Vocal Summaries
    assert payload.cv_summary.gaze_stability_ratio == 88.5
    assert payload.vocal_summary.speaking_rate_wpm == 138.0

    # Verify Questions & Coding
    assert len(payload.questions_summary) == 1
    assert payload.coding_summary is not None
    assert payload.coding_summary["overall_coding_score"] == 100.0


def test_pdf_generation_returns_valid_pdf_bytes(sample_payload):
    """Assert PDF export returns valid %PDF magic bytes and generates in < 1.0s."""
    t0 = time.perf_counter()
    pdf_bytes = pdf_generator_service.generate_pdf(sample_payload)
    elapsed = time.perf_counter() - t0

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
    assert b"%%EOF" in pdf_bytes
    assert elapsed < 1.0, f"PDF generation took {elapsed:.3f}s (must be < 1.0s)"


def test_pdf_generation_skipped_coding(sample_payload):
    """Assert PDF generation handles skipped coding round cleanly without errors."""
    sample_payload.coding_summary = {
        "skipped": True,
        "note": "Candidate skipped coding round.",
    }
    sample_payload.scores.coding_ability_score = 0.0

    pdf_bytes = pdf_generator_service.generate_pdf(sample_payload)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000


def test_pdf_generation_long_transcripts(sample_payload):
    """Assert PDF generation wraps multi-page and long transcripts cleanly."""
    long_text = "Detailed explanation of concurrency: " + ("mutex lock condition variables " * 200)
    sample_payload.questions_summary[0]["transcript"] = long_text

    pdf_bytes = pdf_generator_service.generate_pdf(sample_payload)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000


def test_unauthorized_candidate_cannot_access_export():
    """Candidate role request returns HTTP 403 Forbidden on report export endpoints."""
    candidate_user = User.model_construct(
        id="60c72b2f9b1d8b2bad000001",
        email="candidate@example.com",
        username="candidate_jane",
        full_name="Jane Candidate",
        is_active=True,
        hashed_password="",
    )

    app.dependency_overrides[get_current_active_user] = lambda: candidate_user

    client = TestClient(app)
    try:
        res_json = client.get("/interview/admin/session/test_session_id/export/json")
        assert res_json.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in res_json.json()["detail"]

        res_pdf = client.get("/interview/admin/session/test_session_id/export/pdf")
        assert res_pdf.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in res_pdf.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_admin_can_access_export_json_and_pdf(mock_interview_session):
    """Admin role request returns HTTP 200 with structured JSON and valid PDF streaming response."""
    admin_user = User.model_construct(
        id="admin",
        email="admin@fyp.com",
        username="admin",
        full_name="System Admin",
        is_active=True,
        hashed_password="",
    )

    app.dependency_overrides[get_current_active_user] = lambda: admin_user

    client = TestClient(app)
    try:
        with patch.object(InterviewSession, "find_one", AsyncMock(return_value=mock_interview_session)), \
             patch.object(User, "get", AsyncMock(return_value=None)), \
             patch.object(Profile, "find_one", AsyncMock(return_value=None)):

            # Test JSON Export
            res_json = client.get(f"/interview/admin/session/{mock_interview_session.session_id}/export/json")
            assert res_json.status_code == status.HTTP_200_OK
            data = res_json.json()
            assert data["session_id"] == mock_interview_session.session_id
            assert data["candidate_name"] == mock_interview_session.candidate_name
            assert "scores" in data
            assert "feedback" in data
            assert "questions_summary" in data
            assert "cv_summary" in data
            assert "vocal_summary" in data

            # Test PDF Export
            res_pdf = client.get(f"/interview/admin/session/{mock_interview_session.session_id}/export/pdf")
            assert res_pdf.status_code == status.HTTP_200_OK
            assert res_pdf.headers["content-type"] == "application/pdf"
            assert "attachment;" in res_pdf.headers["content-disposition"]
            assert res_pdf.content.startswith(b"%PDF-")
    finally:
        app.dependency_overrides.clear()


def test_export_404_on_unknown_session():
    """Admin request for nonexistent session returns HTTP 404 Not Found."""
    admin_user = User.model_construct(
        id="admin",
        email="admin@fyp.com",
        username="admin",
        full_name="System Admin",
        is_active=True,
        hashed_password="",
    )

    app.dependency_overrides[get_current_active_user] = lambda: admin_user

    client = TestClient(app)
    try:
        with patch.object(InterviewSession, "find_one", AsyncMock(return_value=None)):
            res = client.get("/interview/admin/session/nonexistent_session/export/json")
            assert res.status_code == status.HTTP_404_NOT_FOUND

            res_pdf = client.get("/interview/admin/session/nonexistent_session/export/pdf")
            assert res_pdf.status_code == status.HTTP_404_NOT_FOUND
    finally:
        app.dependency_overrides.clear()
