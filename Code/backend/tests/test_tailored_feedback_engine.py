"""Unit tests for FEAT-008-BE: Tailored Feedback & Skill Gap Analysis Engine."""

import time
from datetime import datetime
import pytest

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    CodingChallengeEvaluation,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionType,
    TestCaseResult,
)
from app.interview.domain.role_taxonomy import (
    CompetencyWeight,
    StandardRole,
    get_role_competency_matrix,
)
from app.interview.domain.scoring_models import TailoredFeedback
from app.interview.services.feedback_generator import generate_tailored_feedback
from app.interview.services.recruiter_report import RecruiterReportGenerator


def test_feedback_identifies_missed_concepts():
    """Verify missed question concepts like 'ACID properties' produce specific database remediation recommendations."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain database transactions and ACID properties in relational databases.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Transactions ensure safety in databases.",
            relevance_score=6.0,
            depth_score=4.0,
            accuracy_score=45.0,
            is_correct=False,
            key_points_covered=["Atomicity"],
            missed_points=["ACID properties", "Isolation levels", "Consistency guarantees"],
        ),
        AnswerEvaluation(
            question_index=1,
            question_text="How do you handle asynchronous concurrency in backend web services?",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="We use async and await with an event loop.",
            relevance_score=8.5,
            depth_score=8.0,
            accuracy_score=85.0,
            is_correct=True,
            key_points_covered=["Event Loop", "Async/Await", "Non-blocking I/O"],
            missed_points=[],
        ),
    ]

    backend_comps = get_role_competency_matrix(StandardRole.BACKEND_ENGINEER)
    vocal = ObservableVocalMetrics(speaking_rate_wpm=135.0, pause_duration_ratio=0.18, speech_clarity_score=82.0)
    cv = ObservableCVMetrics(gaze_stability_ratio=80.0, head_pose_variance=78.0, frame_presence_ratio=95.0, blink_frequency_cpm=16.0)

    feedback = generate_tailored_feedback(
        evaluations=evaluations,
        coding_evaluation=None,
        role_competencies=backend_comps,
        vocal_metrics=vocal,
        cv_metrics=cv,
    )

    assert isinstance(feedback, TailoredFeedback)
    # Weakest areas must reference missed ACID concepts on Question 1
    assert any("ACID properties" in w for w in feedback.weakest_technical_areas)
    # Actionable recommendations must include specific database isolation / ACID remediation
    assert any(
        "ACID" in r or "database transaction" in r.lower() or "isolation" in r.lower()
        for r in feedback.actionable_improvement_recommendations
    )
    # Strongest technical areas must highlight covered Async/Await concepts
    assert any("Async/Await" in s or "Event Loop" in s for s in feedback.strongest_technical_areas)


def test_coding_feedback_mentions_failed_hidden_tests():
    """Candidate failing hidden tests receives edge-case testing recommendation and clear coding summary."""
    coding_eval = CodingChallengeEvaluation(
        challenge_id="two-sum-ii",
        language="python",
        source_code="def solution(): pass",
        compile_success=True,
        public_tests_passed=2,
        public_tests_total=2,
        hidden_tests_passed=1,
        hidden_tests_total=3,
        overall_coding_score=60.0,
        execution_time_total_ms=45.2,
        peak_memory_kb=1024.0,
        results=[
            TestCaseResult(test_id=1, is_hidden=False, passed=True, runtime_ms=10.0, memory_kb=512.0),
            TestCaseResult(test_id=2, is_hidden=False, passed=True, runtime_ms=12.0, memory_kb=512.0),
            TestCaseResult(test_id=3, is_hidden=True, passed=True, runtime_ms=11.0, memory_kb=512.0),
            TestCaseResult(test_id=4, is_hidden=True, passed=False, runtime_ms=12.2, memory_kb=512.0),
        ],
    )

    feedback = generate_tailored_feedback(
        evaluations=[],
        coding_evaluation=coding_eval,
        role_competencies=[],
        vocal_metrics=ObservableVocalMetrics(speaking_rate_wpm=140.0),
        cv_metrics=ObservableCVMetrics(frame_presence_ratio=90.0),
    )

    # Coding summary must mention public pass and hidden failure count
    assert "2/2 public test cases" in feedback.coding_analysis_summary
    assert "failed 2/3 hidden test cases" in feedback.coding_analysis_summary
    # Actionable recommendations must specifically include edge-case testing guidance
    assert any(
        "edge-case" in r.lower() or "boundary" in r.lower()
        for r in feedback.actionable_improvement_recommendations
    )


def test_feedback_non_empty_for_all_sections():
    """Verify that all 7 feedback categories are populated with non-empty lists or strings."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_text="Describe RESTful API principles.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="REST uses HTTP methods.",
            relevance_score=7.0,
            depth_score=6.0,
            accuracy_score=70.0,
            is_correct=True,
            key_points_covered=["HTTP Methods", "Statelessness"],
            missed_points=["Idempotency", "HATEOAS"],
        )
    ]

    backend_comps = get_role_competency_matrix(StandardRole.BACKEND_ENGINEER)
    vocal = ObservableVocalMetrics(speaking_rate_wpm=145.0, pause_duration_ratio=0.15, speech_clarity_score=80.0)
    cv = ObservableCVMetrics(gaze_stability_ratio=75.0, head_pose_variance=72.0, frame_presence_ratio=90.0, blink_frequency_cpm=18.0)

    feedback = generate_tailored_feedback(
        evaluations=evaluations,
        coding_evaluation=None,
        role_competencies=backend_comps,
        vocal_metrics=vocal,
        cv_metrics=cv,
    )

    assert len(feedback.strongest_technical_areas) > 0
    assert len(feedback.weakest_technical_areas) > 0
    assert len(feedback.coding_analysis_summary) > 0
    assert len(feedback.communication_observations) > 0
    assert len(feedback.behavioral_observations) > 0
    assert len(feedback.missing_role_skills) > 0
    assert len(feedback.actionable_improvement_recommendations) > 0


def test_feedback_perfect_score_advanced_recommendations():
    """Edge case: Candidate scored 100% on everything -> provides advanced mastery and leadership recommendations."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain database sharding vs replication.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Comprehensive explanation of horizontal sharding, consensus protocols, and read replicas.",
            relevance_score=10.0,
            depth_score=10.0,
            accuracy_score=100.0,
            is_correct=True,
            key_points_covered=["Horizontal Sharding", "Replication Lag", "Consensus Protocols", "Partition Keys"],
            missed_points=[],
        ),
        AnswerEvaluation(
            question_index=1,
            question_text="Design an event-driven notification service.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Kafka event streaming with consumer groups, DLQ, and idempotent consumers.",
            relevance_score=10.0,
            depth_score=10.0,
            accuracy_score=100.0,
            is_correct=True,
            key_points_covered=["Kafka", "Dead Letter Queue", "Idempotency"],
            missed_points=[],
        ),
    ]

    coding_eval = CodingChallengeEvaluation(
        challenge_id="merge-intervals",
        language="python",
        source_code="def solution(): pass",
        compile_success=True,
        public_tests_passed=3,
        public_tests_total=3,
        hidden_tests_passed=5,
        hidden_tests_total=5,
        overall_coding_score=100.0,
        execution_time_total_ms=18.5,
        peak_memory_kb=512.0,
        results=[],
    )

    backend_comps = get_role_competency_matrix(StandardRole.BACKEND_ENGINEER)
    vocal = ObservableVocalMetrics(speaking_rate_wpm=140.0, pause_duration_ratio=0.18, speech_clarity_score=90.0)
    cv = ObservableCVMetrics(gaze_stability_ratio=88.0, head_pose_variance=85.0, frame_presence_ratio=98.0, blink_frequency_cpm=15.0)

    feedback = generate_tailored_feedback(
        evaluations=evaluations,
        coding_evaluation=coding_eval,
        role_competencies=backend_comps,
        vocal_metrics=vocal,
        cv_metrics=cv,
    )

    # Must generate advanced mastery & leadership recommendations
    assert any(
        "distributed systems" in r.lower() or "consensus" in r.lower() or "leadership" in r.lower() or "mentoring" in r.lower()
        for r in feedback.actionable_improvement_recommendations
    )
    # Coding summary must confirm 100% passed
    assert "successfully passed all" in feedback.coding_analysis_summary.lower()


def test_feedback_zero_answers_graceful_fallback():
    """Edge case: Candidate answered zero questions -> returns foundational technical roadmap without crashing."""
    frontend_comps = get_role_competency_matrix(StandardRole.FRONTEND_ENGINEER)

    feedback = generate_tailored_feedback(
        evaluations=[],
        coding_evaluation=None,
        role_competencies=frontend_comps,
        vocal_metrics=None,
        cv_metrics=None,
    )

    assert isinstance(feedback, TailoredFeedback)
    assert len(feedback.strongest_technical_areas) > 0
    assert len(feedback.weakest_technical_areas) > 0
    assert "skipped" in feedback.coding_analysis_summary.lower() or "not submitted" in feedback.coding_analysis_summary.lower()
    assert len(feedback.missing_role_skills) > 0
    assert len(feedback.actionable_improvement_recommendations) > 0
    assert any("foundational" in r.lower() or "review" in r.lower() or "mock" in r.lower() for r in feedback.actionable_improvement_recommendations)


def test_feedback_communication_and_cv_observations():
    """Verify communication and CV observations strictly cite objective physical metrics."""
    vocal = ObservableVocalMetrics(
        speaking_rate_wpm=105.0,
        pause_duration_ratio=0.32,
        speech_clarity_score=68.0,
        acoustic_flags=["low_clarity_detected"],
    )
    cv = ObservableCVMetrics(
        gaze_stability_ratio=62.0,
        head_pose_variance=58.0,
        frame_presence_ratio=82.0,
        blink_frequency_cpm=24.0,
        observable_flags=["excessive_head_movement"],
    )

    feedback = generate_tailored_feedback(
        evaluations=[],
        coding_evaluation=None,
        role_competencies=[],
        vocal_metrics=vocal,
        cv_metrics=cv,
    )

    # Communication observations
    comm_text = " ".join(feedback.communication_observations)
    assert "105.0 WPM" in comm_text
    assert "32.0%" in comm_text
    assert "68.0/100" in comm_text

    # CV observations
    beh_text = " ".join(feedback.behavioral_observations)
    assert "62.0%" in beh_text
    assert "82.0%" in beh_text
    assert "24.0 blinks per minute" in beh_text


def test_role_competency_gap_under_60_percent():
    """Verify role competency gap analysis accurately flags underperforming skill areas (< 60%)."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain database indexing strategies and query execution plans.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Indexes make queries faster.",
            relevance_score=4.0,
            depth_score=3.0,
            accuracy_score=35.0,
            is_correct=False,
            key_points_covered=["B-Tree"],
            missed_points=["Indexing Strategies", "Execution Plans", "Composite Indexing"],
        )
    ]

    backend_comps = get_role_competency_matrix(StandardRole.BACKEND_ENGINEER)

    feedback = generate_tailored_feedback(
        evaluations=evaluations,
        coding_evaluation=None,
        role_competencies=backend_comps,
        vocal_metrics=None,
        cv_metrics=None,
    )

    # Database Architecture competency area must be flagged as a skill gap
    assert any("Database Architecture" in gap for gap in feedback.missing_role_skills)


def test_feedback_generation_latency():
    """Verify feedback generation executes in < 150ms per candidate session."""
    evaluations = [
        AnswerEvaluation(
            question_index=i,
            question_text=f"Question {i} regarding technical system design and databases.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript=f"Candidate response for question {i}.",
            relevance_score=8.0,
            depth_score=7.0,
            accuracy_score=80.0,
            is_correct=True,
            key_points_covered=["Concept A", "Concept B"],
            missed_points=["Concept C"],
        )
        for i in range(10)
    ]

    backend_comps = get_role_competency_matrix(StandardRole.BACKEND_ENGINEER)
    vocal = ObservableVocalMetrics(speaking_rate_wpm=140.0, pause_duration_ratio=0.18, speech_clarity_score=85.0)
    cv = ObservableCVMetrics(gaze_stability_ratio=82.0, head_pose_variance=80.0, frame_presence_ratio=95.0, blink_frequency_cpm=16.0)

    start_time = time.perf_counter()
    feedback = generate_tailored_feedback(
        evaluations=evaluations,
        coding_evaluation=None,
        role_competencies=backend_comps,
        vocal_metrics=vocal,
        cv_metrics=cv,
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert elapsed_ms < 150.0, f"Feedback generation took {elapsed_ms:.2f}ms, exceeding 150ms limit"
    assert isinstance(feedback, TailoredFeedback)


def test_recruiter_report_integration():
    """Verify RecruiterReportGenerator integrates tailored_feedback into RecruiterReport seamlessly."""
    generator = RecruiterReportGenerator()
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain RESTful APIs.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="REST APIs use standard HTTP verbs.",
            relevance_score=8.0,
            depth_score=7.0,
            accuracy_score=80.0,
            is_correct=True,
            key_points_covered=["HTTP Verbs", "Statelessness"],
            missed_points=["HATEOAS"],
        )
    ]

    report = generator.generate_report(
        candidate_name="Alex Mercer",
        job_role="backend_engineer",
        session_start=datetime.utcnow(),
        session_end=datetime.utcnow(),
        evaluations=evaluations,
        behavioral_metrics=[],
        vocal_metrics=[],
        coding_results=[],
    )

    assert hasattr(report, "tailored_feedback")
    assert report.tailored_feedback is not None
    assert isinstance(report.tailored_feedback, dict)
    assert "strongest_technical_areas" in report.tailored_feedback
    assert "actionable_improvement_recommendations" in report.tailored_feedback
    assert len(report.tailored_feedback["actionable_improvement_recommendations"]) > 0
