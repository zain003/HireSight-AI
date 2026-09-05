"""
FEAT-008 End-to-End Verification Suite: Tailored Feedback & Skill Gap Analysis Engine.

Validates:
1. Question-level evidence mapping (linking missed concepts directly to remediation).
2. Target role gap analysis (flagging competencies with score < 60%).
3. Sandboxed coding evaluation analysis (public vs hidden test outcomes).
4. Physical communication & behavioral metric observations (WPM, pause ratio, gaze, head pose, blink CPM).
5. All 7 feedback categories populated.
6. Edge case handling (100% score, 0 questions answered).
7. Execution latency benchmark (< 150ms).
8. RecruiterReport integration & schema integrity.
"""

import sys
import time
from datetime import datetime
from typing import Dict, List

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


def run_verification():
    print("=" * 80)
    print("HireSIGHT FEAT-008: Tailored Feedback Engine Verification Suite")
    print("=" * 80)

    checks_passed = 0
    total_checks = 10
    benchmarks: Dict[str, float] = {}

    # Check 1: Missed Concept Remediation Mapping
    print("\n[Check 1/10] Verifying missed concept evidence mapping (ACID & Concurrency)...")
    evals = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain database transactions and ACID properties.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Transactions group operations together.",
            relevance_score=5.0,
            depth_score=4.0,
            accuracy_score=40.0,
            is_correct=False,
            key_points_covered=["Transaction grouping"],
            missed_points=["ACID properties", "Isolation levels", "Rollback semantics"],
        )
    ]
    fb1 = generate_tailored_feedback(
        evaluations=evals,
        coding_evaluation=None,
        role_competencies=get_role_competency_matrix(StandardRole.BACKEND_ENGINEER),
        vocal_metrics=ObservableVocalMetrics(speaking_rate_wpm=130.0, pause_duration_ratio=0.18, speech_clarity_score=80.0),
        cv_metrics=ObservableCVMetrics(gaze_stability_ratio=80.0, head_pose_variance=80.0, frame_presence_ratio=95.0, blink_frequency_cpm=16.0),
    )
    assert any("ACID properties" in w for w in fb1.weakest_technical_areas), "Missed ACID not in weakest areas"
    assert any("ACID" in r or "database transaction" in r.lower() for r in fb1.actionable_improvement_recommendations), "ACID remediation missing"
    print("  -> Passed: Missed concept directly mapped to Question 1 and concrete database remediation generated.")
    checks_passed += 1

    # Check 2: Sandboxed Coding Hidden Test Failure Analysis
    print("\n[Check 2/10] Verifying coding challenge hidden test failure feedback...")
    coding_eval = CodingChallengeEvaluation(
        challenge_id="lru-cache",
        language="python",
        source_code="class LRUCache: pass",
        compile_success=True,
        public_tests_passed=2,
        public_tests_total=2,
        hidden_tests_passed=0,
        hidden_tests_total=4,
        overall_coding_score=33.3,
        execution_time_total_ms=52.0,
        peak_memory_kb=1024.0,
        results=[],
    )
    fb2 = generate_tailored_feedback(
        evaluations=[],
        coding_evaluation=coding_eval,
        role_competencies=[],
        vocal_metrics=None,
        cv_metrics=None,
    )
    assert "2/2 public" in fb2.coding_analysis_summary
    assert "failed 4/4 hidden" in fb2.coding_analysis_summary
    assert any("edge-case" in r.lower() or "boundary" in r.lower() for r in fb2.actionable_improvement_recommendations)
    print("  -> Passed: Hidden test failures accurately summarized and edge-case testing recommendation produced.")
    checks_passed += 1

    # Check 3: Non-Empty Output for All 7 Sections
    print("\n[Check 3/10] Verifying all 7 feedback categories are populated...")
    assert len(fb1.strongest_technical_areas) > 0, "strongest_technical_areas is empty"
    assert len(fb1.weakest_technical_areas) > 0, "weakest_technical_areas is empty"
    assert len(fb1.coding_analysis_summary) > 0, "coding_analysis_summary is empty"
    assert len(fb1.communication_observations) > 0, "communication_observations is empty"
    assert len(fb1.behavioral_observations) > 0, "behavioral_observations is empty"
    assert len(fb1.missing_role_skills) > 0, "missing_role_skills is empty"
    assert len(fb1.actionable_improvement_recommendations) > 0, "actionable_improvement_recommendations is empty"
    print("  -> Passed: All 7 feedback categories non-empty and structured.")
    checks_passed += 1

    # Check 4: Objective Physical Signals in Vocal Communication Observations
    print("\n[Check 4/10] Verifying vocal communication observations (WPM, pause ratio, clarity)...")
    vocal = ObservableVocalMetrics(
        speaking_rate_wpm=112.5,
        pause_duration_ratio=0.28,
        speech_clarity_score=72.0,
        acoustic_flags=["low_energy_segment"],
    )
    fb4 = generate_tailored_feedback(evaluations=[], vocal_metrics=vocal, cv_metrics=None)
    comm_str = " ".join(fb4.communication_observations)
    assert "112.5 WPM" in comm_str, "WPM missing from communication observations"
    assert "28.0%" in comm_str, "Pause ratio missing from communication observations"
    assert "72.0/100" in comm_str, "Clarity score missing from communication observations"
    print("  -> Passed: Communication observations reflect exact measured acoustic signals.")
    checks_passed += 1

    # Check 5: Objective Physical Signals in CV Observations
    print("\n[Check 5/10] Verifying behavioral CV observations (gaze stability, head pose, blink CPM)...")
    cv = ObservableCVMetrics(
        gaze_stability_ratio=66.5,
        head_pose_variance=64.0,
        frame_presence_ratio=88.0,
        blink_frequency_cpm=22.0,
        observable_flags=["frequent_gaze_deviation"],
    )
    fb5 = generate_tailored_feedback(evaluations=[], vocal_metrics=None, cv_metrics=cv)
    beh_str = " ".join(fb5.behavioral_observations)
    assert "66.5%" in beh_str, "Gaze ratio missing"
    assert "64.0%" in beh_str, "Head pose missing"
    assert "88.0%" in beh_str, "Presence missing"
    assert "22.0 blinks per minute" in beh_str, "Blink CPM missing"
    print("  -> Passed: CV observations reflect exact measured facial/gaze dynamics.")
    checks_passed += 1

    # Check 6: Target Role Competency Gap Analysis (< 60% threshold)
    print("\n[Check 6/10] Verifying role competency gap analysis (< 60% threshold)...")
    eval_frontend = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain Web Performance & Core Vitals (LCP, FID, CLS).",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Web performance is important for users.",
            relevance_score=3.0,
            depth_score=3.0,
            accuracy_score=30.0,
            is_correct=False,
            key_points_covered=[],
            missed_points=["LCP/FID/CLS Optimization", "Code Splitting & Lazy Loading"],
        )
    ]
    fb6 = generate_tailored_feedback(
        evaluations=eval_frontend,
        role_competencies=get_role_competency_matrix(StandardRole.FRONTEND_ENGINEER),
    )
    assert any("Web Performance & Core Vitals" in gap for gap in fb6.missing_role_skills)
    print("  -> Passed: Web Performance competency identified as role gap (< 60% score).")
    checks_passed += 1

    # Check 7: Perfect Score Edge Case (Advanced Mastery & Leadership Recommendations)
    print("\n[Check 7/10] Verifying perfect score edge case (100% on everything)...")
    eval_perfect = [
        AnswerEvaluation(
            question_index=0,
            question_text="Explain distributed consensus and Raft algorithm.",
            question_type=QuestionType.TECHNICAL,
            candidate_transcript="Leader election, log replication, safety invariants.",
            relevance_score=10.0,
            depth_score=10.0,
            accuracy_score=100.0,
            is_correct=True,
            key_points_covered=["Leader Election", "Log Replication", "Safety Invariants"],
            missed_points=[],
        )
    ]
    fb7 = generate_tailored_feedback(
        evaluations=eval_perfect,
        coding_evaluation=CodingChallengeEvaluation(
            challenge_id="perfect-sol",
            language="python",
            source_code="pass",
            compile_success=True,
            public_tests_passed=5,
            public_tests_total=5,
            hidden_tests_passed=5,
            hidden_tests_total=5,
            overall_coding_score=100.0,
            execution_time_total_ms=10.0,
            peak_memory_kb=256.0,
            results=[],
        ),
        role_competencies=get_role_competency_matrix(StandardRole.BACKEND_ENGINEER),
    )
    assert any("distributed systems" in r.lower() or "leadership" in r.lower() for r in fb7.actionable_improvement_recommendations)
    print("  -> Passed: Advanced mastery and leadership recommendations generated for top performers.")
    checks_passed += 1

    # Check 8: Zero Answers Edge Case (Foundational Roadmap Fallback)
    print("\n[Check 8/10] Verifying zero answers answered edge case...")
    fb8 = generate_tailored_feedback(
        evaluations=[],
        coding_evaluation=None,
        role_competencies=get_role_competency_matrix(StandardRole.FULLSTACK_ENGINEER),
    )
    assert isinstance(fb8, TailoredFeedback)
    assert len(fb8.actionable_improvement_recommendations) > 0
    assert any("foundational" in r.lower() or "review" in r.lower() or "mock" in r.lower() for r in fb8.actionable_improvement_recommendations)
    print("  -> Passed: Foundational technical roadmap returned gracefully without crashing.")
    checks_passed += 1

    # Check 9: RecruiterReport Integration
    print("\n[Check 9/10] Verifying RecruiterReportGenerator tailored feedback integration...")
    generator = RecruiterReportGenerator()
    report = generator.generate_report(
        candidate_name="Jane Doe",
        job_role="backend_engineer",
        session_start=datetime.utcnow(),
        session_end=datetime.utcnow(),
        evaluations=evals,
        behavioral_metrics=[],
        vocal_metrics=[],
        coding_results=[],
    )
    assert hasattr(report, "tailored_feedback")
    assert report.tailored_feedback is not None
    assert "strongest_technical_areas" in report.tailored_feedback
    assert "actionable_improvement_recommendations" in report.tailored_feedback
    print("  -> Passed: tailored_feedback embedded cleanly into RecruiterReport.")
    checks_passed += 1

    # Check 10: Execution Latency Benchmark (< 150ms limit)
    print("\n[Check 10/10] Benchmarking feedback generation latency across 100 iterations...")
    times = []
    for _ in range(100):
        t0 = time.perf_counter()
        generate_tailored_feedback(
            evaluations=evals,
            coding_evaluation=coding_eval,
            role_competencies=get_role_competency_matrix(StandardRole.BACKEND_ENGINEER),
            vocal_metrics=vocal,
            cv_metrics=cv,
        )
        times.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(times) / len(times)
    max_ms = max(times)
    benchmarks["avg_latency_ms"] = avg_ms
    benchmarks["max_latency_ms"] = max_ms
    print(f"  -> Average Latency: {avg_ms:.3f}ms | Max Latency: {max_ms:.3f}ms (Target: < 150.0ms)")
    assert avg_ms < 150.0, f"Average latency {avg_ms}ms exceeds 150ms limit"
    checks_passed += 1

    print("\n" + "=" * 80)
    print(f"VERIFICATION SUMMARY: {checks_passed}/{total_checks} CHECKS PASSED (100% SUCCESS RATE)")
    print("=" * 80)
    return checks_passed == total_checks, benchmarks


if __name__ == "__main__":
    success, benchmarks = run_verification()
    if not success:
        sys.exit(1)
