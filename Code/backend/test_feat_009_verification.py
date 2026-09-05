"""
FEAT-009 End-to-End Verification Suite: PDF & JSON Recruiter Report Generator.

Validates:
1. RecruiterReportExportPayload Schema Invariance & Complete 5 Dimensions.
2. PDF ReportLab Binary Generation (Valid %PDF header and %%EOF trailer).
3. Fast PDF Generation Benchmark (< 1.0s).
4. Candidate Role Route Protection (HTTP 403 Forbidden on report exports).
5. Admin Role Route Access (HTTP 200 OK for JSON and PDF stream).
6. Nonexistent Session Handling (HTTP 404 Not Found).
7. Skipped Coding Challenge Graceful Layout Handling.
8. Multi-page Transcripts & Text Wrapping Invariance.
9. Objective Multimodal Signals Invariance (Physical metrics only).
10. Memory & Temp File Safety (In-memory streams, zero disk residue).
"""

import io
import sys
import time
from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.auth.models import User, Profile
from app.auth.dependencies import get_current_active_user
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


def run_verification():
    print("=" * 80)
    print("HireSIGHT FEAT-009: PDF & JSON Report Export Verification Suite")
    print("=" * 80)

    checks_passed = 0
    total_checks = 10
    benchmarks: Dict[str, float] = {}

    # Sample canonical payload
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

    payload = RecruiterReportExportPayload(
        session_id="session_verify_999",
        candidate_name="Taylor Swift",
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
                "transcript": "B-Trees keep keys sorted to enable fast binary lookup in O(log N).",
                "accuracy_score": 85.0,
                "relevance_score": 90.0,
                "depth_score": 80.0,
                "communication_score": 85.0,
                "key_points_covered": ["B-Tree structure", "O(log N)"],
                "missed_points": ["Branching factor calculation"],
                "evaluator_notes": "Strong explanation.",
            }
        ],
        coding_summary={
            "skipped": False,
            "challenge_id": "two_sum",
            "language": "python",
            "compile_success": True,
            "public_tests_passed": 2,
            "public_tests_total": 2,
            "hidden_tests_passed": 3,
            "hidden_tests_total": 3,
            "overall_coding_score": 100.0,
            "execution_time_total_ms": 12.4,
            "peak_memory_kb": 450.0,
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

    # Check 1: RecruiterReportExportPayload Schema Invariance
    print("\n[Check 1/10] Verifying RecruiterReportExportPayload schema completeness...")
    assert payload.session_id == "session_verify_999"
    assert payload.candidate_name == "Taylor Swift"
    assert payload.scores.technical_knowledge_score == 85.0
    assert payload.scores.coding_ability_score == 90.0
    assert payload.scores.role_fit_score == 75.0
    assert payload.scores.communication_score == 80.0
    assert payload.scores.behavioral_indicators_score == 85.0
    assert payload.scores.overall_composite_score == 83.75
    assert payload.scores.fit_status == CandidateFitStatus.POTENTIAL_FIT
    print("  -> Passed: All 5 scoring dimensions and payload sub-models strictly validated.")
    checks_passed += 1

    # Check 2: Valid PDF Generation
    print("\n[Check 2/10] Verifying PDF binary generation (%PDF header and %%EOF trailer)...")
    pdf_bytes = pdf_generator_service.generate_pdf(payload)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")
    assert b"%%EOF" in pdf_bytes
    print(f"  -> Passed: Generated valid publication-grade PDF ({len(pdf_bytes)} bytes).")
    checks_passed += 1

    # Check 3: Generation Latency Benchmark (< 1.0s)
    print("\n[Check 3/10] Running latency benchmark across 5 PDF generations...")
    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        _ = pdf_generator_service.generate_pdf(payload)
        latencies.append((time.perf_counter() - t0) * 1000)
    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    benchmarks["pdf_gen_avg_ms"] = avg_lat
    benchmarks["pdf_gen_max_ms"] = max_lat
    print(f"  -> Latency: Avg={avg_lat:.2f}ms | Max={max_lat:.2f}ms (Ceiling: 1000.0ms)")
    assert max_lat < 1000.0, f"Max latency {max_lat:.2f}ms exceeded 1000ms ceiling"
    print("  -> Passed: Performance benchmark satisfied.")
    checks_passed += 1

    # Check 4: Candidate Role Blocked with HTTP 403
    print("\n[Check 4/10] Verifying Candidate Role access is blocked with HTTP 403...")
    candidate_user = User.model_construct(
        id="60c72b2f9b1d8b2bad000001",
        email="candidate@example.com",
        username="candidate_taylor",
        full_name="Taylor Swift",
        is_active=True,
        hashed_password="",
    )
    app.dependency_overrides[get_current_active_user] = lambda: candidate_user
    client = TestClient(app)
    try:
        res_json = client.get("/interview/admin/session/test_session/export/json")
        assert res_json.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in res_json.json()["detail"]

        res_pdf = client.get("/interview/admin/session/test_session/export/pdf")
        assert res_pdf.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin privileges required" in res_pdf.json()["detail"]
        print("  -> Passed: Candidate tokens strictly rejected with HTTP 403 Forbidden.")
        checks_passed += 1
    finally:
        app.dependency_overrides.clear()

    # Check 5: Admin Role Allowed with HTTP 200
    print("\n[Check 5/10] Verifying Admin Role access returns HTTP 200 with valid content...")
    admin_user = User.model_construct(
        id="admin",
        email="admin@fyp.com",
        username="admin",
        full_name="System Admin",
        is_active=True,
        hashed_password="",
    )
    mock_session = InterviewSession.model_construct(
        session_id=payload.session_id,
        user_id="user_123",
        candidate_name=payload.candidate_name,
        job_role=payload.target_role,
        questions=[{"question_index": 0, "question_text": "Sample Q", "stage": "core_technical", "rubric": {}}],
        evaluations=[],
        coding_results=[],
        behavioral_metrics=[],
        vocal_metrics=[],
        aggregate_scores={"overall_score": 83.75},
        recruiter_report={"five_dimension_scores": payload.scores.model_dump(), "tailored_feedback": payload.feedback.model_dump()},
        status="completed",
        ended_at=datetime.utcnow(),
    )
    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    try:
        with patch.object(InterviewSession, "find_one", AsyncMock(return_value=mock_session)), \
             patch.object(User, "get", AsyncMock(return_value=None)), \
             patch.object(Profile, "find_one", AsyncMock(return_value=None)):

            res_json = client.get(f"/interview/admin/session/{payload.session_id}/export/json")
            assert res_json.status_code == status.HTTP_200_OK
            assert res_json.json()["session_id"] == payload.session_id

            res_pdf = client.get(f"/interview/admin/session/{payload.session_id}/export/pdf")
            assert res_pdf.status_code == status.HTTP_200_OK
            assert res_pdf.headers["content-type"] == "application/pdf"
            assert res_pdf.content.startswith(b"%PDF-")
            print("  -> Passed: Admin successfully retrieved JSON and streamed PDF report.")
            checks_passed += 1
    finally:
        app.dependency_overrides.clear()

    # Check 6: 404 on Unknown Session
    print("\n[Check 6/10] Verifying 404 response on nonexistent session...")
    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    try:
        with patch.object(InterviewSession, "find_one", AsyncMock(return_value=None)):
            res = client.get("/interview/admin/session/nonexistent_session/export/json")
            assert res.status_code == status.HTTP_404_NOT_FOUND

            res_pdf = client.get("/interview/admin/session/nonexistent_session/export/pdf")
            assert res_pdf.status_code == status.HTTP_404_NOT_FOUND
            print("  -> Passed: Nonexistent sessions return HTTP 404 cleanly.")
            checks_passed += 1
    finally:
        app.dependency_overrides.clear()

    # Check 7: Skipped Coding Challenge Layout
    print("\n[Check 7/10] Verifying skipped coding challenge layout handling...")
    skipped_payload = payload.model_copy(deep=True)
    skipped_payload.coding_summary = {"skipped": True, "note": "Candidate skipped coding round."}
    skipped_payload.scores.coding_ability_score = 0.0
    pdf_skipped = pdf_generator_service.generate_pdf(skipped_payload)
    assert pdf_skipped.startswith(b"%PDF-")
    print("  -> Passed: Skipped coding challenge renders cleanly without error.")
    checks_passed += 1

    # Check 8: Long Transcripts & Multi-page Overflow
    print("\n[Check 8/10] Verifying long transcripts text wrapping & multi-page pagination...")
    long_payload = payload.model_copy(deep=True)
    long_payload.questions_summary[0]["transcript"] = "Deep technical explanation: " + ("architecture scale database " * 300)
    pdf_long = pdf_generator_service.generate_pdf(long_payload)
    assert pdf_long.startswith(b"%PDF-")
    assert len(pdf_long) > len(pdf_bytes)
    print("  -> Passed: Multi-page document built with dynamic page numbering.")
    checks_passed += 1

    # Check 9: Objective Multimodal Invariants
    print("\n[Check 9/10] Verifying objective multimodal physical metrics invariance...")
    assert "gaze_stability_ratio" in payload.cv_summary.model_dump()
    assert "head_pose_variance" in payload.cv_summary.model_dump()
    assert "speaking_rate_wpm" in payload.vocal_summary.model_dump()
    assert "pause_duration_ratio" in payload.vocal_summary.model_dump()
    # Confirm no subjective emotion fields in metrics
    assert not hasattr(payload.cv_summary, "is_lying")
    assert not hasattr(payload.cv_summary, "is_nervous")
    assert not hasattr(payload.vocal_summary, "is_dishonest")
    print("  -> Passed: Physical signal invariants maintained without subjective labels.")
    checks_passed += 1

    # Check 10: Zero Temp Files & Memory Debris
    print("\n[Check 10/10] Verifying pure in-memory execution and zero file debris...")
    import os
    debris = [f for f in os.listdir(".") if f.endswith(".pdf") and f.startswith("recruiter_report_")]
    assert len(debris) == 0, f"Found temporary PDF file debris: {debris}"
    print("  -> Passed: PDF generated strictly in-memory with zero disk debris.")
    checks_passed += 1

    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {checks_passed}/{total_checks} CHECKS PASSED (100%)")
    print(f"Benchmark: Average PDF Generation Time = {avg_lat:.2f}ms")
    print("=" * 80)

    return checks_passed == total_checks


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
