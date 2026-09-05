"""
FEAT-007 Verification Suite: 5-Dimensional Explainable Scoring Engine End-to-End Verification.
Executes all verification checks defined in context/feature-specs/FEAT-007-VERIFY-explainable-scoring.md
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend root in path
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.interview.domain.scoring_models import (
    CandidateFitStatus,
    FiveDimensionScores,
    ScoringWeights,
)
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionType,
)
from app.interview.services.recruiter_report import (
    RecruiterReportGenerator,
    calculate_five_dimension_scores,
)
from app.interview.services.analysis_service import AnalysisService


def run_verification():
    report_lines = []

    def log(msg=""):
        try:
            print(msg)
        except Exception:
            pass
        report_lines.append(msg)

    log("# FEAT-007 Verification Test Report: 5-Dimensional Explainable Scoring Engine")
    log(f"**Execution Timestamp**: {datetime.now(timezone.utc).isoformat()}")
    log("**Target Spec**: `context/feature-specs/FEAT-007-BE-explainable-scoring-engine.md`")
    log("**Verification Spec**: `context/feature-specs/FEAT-007-VERIFY-explainable-scoring.md`")
    log()
    log("---")
    log()

    checks_passed = 0
    checks_total = 10

    # ----------------------------------------------------
    # Check 1: Mathematical Weight Sum Invariance
    # ----------------------------------------------------
    log("### Check 1: Mathematical Weight Sum Invariance (100% Normalized)")
    w_tech = ScoringWeights.TECHNICAL_KNOWLEDGE
    w_coding = ScoringWeights.CODING_ABILITY
    w_role = ScoringWeights.ROLE_FIT
    w_comm = ScoringWeights.COMMUNICATION
    w_beh = ScoringWeights.BEHAVIORAL_INDICATORS
    total_w = w_tech + w_coding + w_role + w_comm + w_beh

    log(f"- Technical Knowledge Weight: {w_tech * 100:.1f}% ({w_tech})")
    log(f"- Coding Ability Weight: {w_coding * 100:.1f}% ({w_coding})")
    log(f"- Role Fit Weight: {w_role * 100:.1f}% ({w_role})")
    log(f"- Communication Weight: {w_comm * 100:.1f}% ({w_comm})")
    log(f"- Behavioral Indicators Weight: {w_beh * 100:.1f}% ({w_beh})")
    log(f"- Total Sum of Weights: {total_w:.4f}")

    if abs(total_w - 1.00) < 1e-9 and w_tech == 0.35 and w_coding == 0.20 and w_role == 0.15 and w_comm == 0.15 and w_beh == 0.15:
        log("✅ **Check 1 PASSED**: Scoring weights sum exactly to 1.00 (100%).")
        checks_passed += 1
    else:
        log("❌ **Check 1 FAILED**: Weights do not sum to 1.00.")
    log()

    # ----------------------------------------------------
    # Check 2: Composite Calculation Accuracy Across 20 Synthetic Profiles
    # ----------------------------------------------------
    log("### Check 2: Composite Score Accuracy Across 20 Synthetic Profiles")
    all_profiles_accurate = True
    for i in range(20):
        t = 50.0 + (i * 2.5)
        c = 40.0 + (i * 3.0)
        r = 60.0 + (i * 1.8)
        cm = 55.0 + (i * 2.2)
        b = 65.0 + (i * 1.5)

        evals = [AnswerEvaluation(relevance_score=t/10.0, depth_score=t/10.0, accuracy_score=t, communication_score=cm/10.0)]
        coding = [{"overall_coding_score": c}]
        role_fit = {"overall_fit_score": r}
        vocal = [ObservableVocalMetrics(speech_clarity_score=cm, speaking_rate_wpm=140.0, pause_duration_ratio=0.20)]
        cv = [ObservableCVMetrics(gaze_stability_ratio=b, head_pose_variance=b, frame_presence_ratio=b, facial_movement_dynamics=b)]

        res = calculate_five_dimension_scores(
            evaluations=evals,
            coding_results=coding,
            role_fit_data=role_fit,
            vocal_metrics=vocal,
            cv_metrics=cv,
        )

        expected_from_dimensions = round(
            0.35 * res.technical_knowledge_score
            + 0.20 * res.coding_ability_score
            + 0.15 * res.role_fit_score
            + 0.15 * res.communication_score
            + 0.15 * res.behavioral_indicators_score,
            2,
        )

        if abs(res.overall_composite_score - expected_from_dimensions) > 1e-6:
            all_profiles_accurate = False
            log(f"  Profile {i+1} mismatch: calculated={res.overall_composite_score}, expected={expected_from_dimensions}")

    if all_profiles_accurate:
        log("✅ **Check 2 PASSED**: Exact composite calculation verified across 20 distinct synthetic candidate profiles.")
        checks_passed += 1
    else:
        log("❌ **Check 2 FAILED**: Composite score discrepancy detected.")
    log()

    # ----------------------------------------------------
    # Check 3: CandidateFitStatus Boundary Threshold Classification
    # ----------------------------------------------------
    log("### Check 3: CandidateFitStatus Boundary Threshold Classification")
    # Using verbal-only for exact calibration in boundary tests
    test_cases = [
        # (tech, coding, role_fit, comm, beh, expected_status)
        (90.0, 90.0, 90.0, 90.0, 90.0, CandidateFitStatus.STRONG_FIT),
        (85.0, 85.0, 85.0, 85.0, 85.0, CandidateFitStatus.STRONG_FIT),
        (75.0, 95.0, 95.0, 95.0, 95.0, CandidateFitStatus.POTENTIAL_FIT), # Tech < 80 despite high overall
        (84.9, 84.9, 84.9, 84.9, 84.9, CandidateFitStatus.POTENTIAL_FIT), # Overall 84.9 < 85.0
        (70.0, 70.0, 70.0, 70.0, 70.0, CandidateFitStatus.POTENTIAL_FIT), # Overall 70.0
        (69.9, 69.9, 69.9, 69.9, 69.9, CandidateFitStatus.NEEDS_GROWTH),  # Overall 69.9 < 70.0
        (55.0, 55.0, 55.0, 55.0, 55.0, CandidateFitStatus.NEEDS_GROWTH),  # Overall 55.0
        (54.9, 54.9, 54.9, 54.9, 54.9, CandidateFitStatus.NOT_A_FIT),     # Overall 54.9 < 55.0
        (30.0, 30.0, 30.0, 30.0, 30.0, CandidateFitStatus.NOT_A_FIT),
    ]

    boundaries_passed = True
    for idx, (t, c, r, cm, b, expected_status) in enumerate(test_cases):
        evals = [AnswerEvaluation(relevance_score=t/10.0, depth_score=t/10.0, accuracy_score=t, communication_score=cm/10.0)]
        res = calculate_five_dimension_scores(
            evaluations=evals,
            coding_results=[{"overall_coding_score": c}],
            role_fit_data={"overall_fit_score": r},
            vocal_metrics=[],  # verbal-only communication matches cm exactly
            cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=b, head_pose_variance=b, frame_presence_ratio=b, facial_movement_dynamics=b)],
        )
        if res.fit_status != expected_status:
            boundaries_passed = False
            log(f"  Boundary case {idx+1} failed: got {res.fit_status}, expected {expected_status} (overall={res.overall_composite_score}, tech={res.technical_knowledge_score})")

    if boundaries_passed:
        log("✅ **Check 3 PASSED**: All FitStatus boundary conditions and multi-variable thresholds verified.")
        checks_passed += 1
    else:
        log("❌ **Check 3 FAILED**: FitStatus boundary condition failed.")
    log()

    # ----------------------------------------------------
    # Check 4: Mathematical Scoring Audit Trail Completeness
    # ----------------------------------------------------
    log("### Check 4: Mathematical Scoring Audit Trail Completeness")
    evals = [
        AnswerEvaluation(question_index=0, question_type=QuestionType.TECHNICAL, relevance_score=8.5, depth_score=8.0, accuracy_score=85.0, communication_score=8.0),
        AnswerEvaluation(question_index=1, question_type=QuestionType.TECHNICAL, relevance_score=9.0, depth_score=8.5, accuracy_score=90.0, communication_score=8.5),
    ]
    res = calculate_five_dimension_scores(
        evaluations=evals,
        coding_results=[{"overall_coding_score": 92.0, "compile_success": True}],
        role_fit_data={"role": "backend_engineer", "overall_fit_score": 84.0, "matched_skills": ["python", "sql", "fastapi"], "missing_concepts": ["k8s"]},
        vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=88.0, speaking_rate_wpm=145.0, pause_duration_ratio=0.18)],
        cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=91.0, head_pose_variance=88.0, frame_presence_ratio=95.0, facial_movement_dynamics=82.0)],
    )

    audit = res.scoring_formula_audit
    required_audit_keys = ["formula", "weights", "dimension_scores", "weighted_contributions", "overall_composite_score", "fit_status", "dimension_audits"]
    required_dim_audits = ["technical_knowledge", "coding_ability", "role_fit", "communication", "behavioral_indicators"]

    has_all_keys = all(k in audit for k in required_audit_keys)
    has_all_dim_audits = all(k in audit.get("dimension_audits", {}) for k in required_dim_audits)

    log(f"- Formula: `{audit.get('formula')}`")
    log(f"- Weights Breakdown: {audit.get('weights')}")
    log(f"- Weighted Contributions: {audit.get('weighted_contributions')}")
    log(f"- Dimensions Audited: {list(audit.get('dimension_audits', {}).keys())}")

    if has_all_keys and has_all_dim_audits:
        log("✅ **Check 4 PASSED**: Scoring formula audit contains complete mathematical equation, weights, and per-dimension breakdowns.")
        checks_passed += 1
    else:
        log("❌ **Check 4 FAILED**: Incomplete scoring audit structure.")
    log()

    # ----------------------------------------------------
    # Check 5: Edge Case: Skipped Coding Challenge Handled Gracefully
    # ----------------------------------------------------
    log("### Check 5: Edge Case: Skipped Coding Challenge Graceful Fallback")
    res_skip = calculate_five_dimension_scores(
        evaluations=evals,
        coding_results=[],  # No coding attempted
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[],
        cv_metrics=[],
    )

    log(f"- Coding Score: {res_skip.coding_ability_score}")
    log(f"- Coding Audit Status: {res_skip.scoring_formula_audit['dimension_audits']['coding_ability']['status']}")
    log(f"- Overall Composite: {res_skip.overall_composite_score}")

    if res_skip.coding_ability_score == 0.0 and res_skip.scoring_formula_audit['dimension_audits']['coding_ability']['status'] == "skipped_or_none" and res_skip.overall_composite_score > 0.0:
        log("✅ **Check 5 PASSED**: Skipped coding challenge defaults to 0.0 without crashing and records audit trail.")
        checks_passed += 1
    else:
        log("❌ **Check 5 FAILED**: Skipped coding challenge error.")
    log()

    # ----------------------------------------------------
    # Check 6: Edge Case: Missing Video Frames Handled Gracefully
    # ----------------------------------------------------
    log("### Check 6: Edge Case: Missing Video Frames Graceful Fallback")
    res_novideo = calculate_five_dimension_scores(
        evaluations=evals,
        coding_results=[{"overall_coding_score": 80.0}],
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[],
        cv_metrics=[],  # No frames
    )

    log(f"- Behavioral Indicators Score: {res_novideo.behavioral_indicators_score}")
    log(f"- Behavioral Audit Status: {res_novideo.scoring_formula_audit['dimension_audits']['behavioral_indicators']['status']}")
    log(f"- Audit Note: {res_novideo.scoring_formula_audit['dimension_audits']['behavioral_indicators']['note']}")

    if res_novideo.behavioral_indicators_score == 0.0 and res_novideo.scoring_formula_audit['dimension_audits']['behavioral_indicators']['status'] == "no_data":
        log("✅ **Check 6 PASSED**: Missing video frames defaults to 0.0 with audit note.")
        checks_passed += 1
    else:
        log("❌ **Check 6 FAILED**: Missing video frames error.")
    log()

    # ----------------------------------------------------
    # Check 7: RecruiterReportGenerator Integration
    # ----------------------------------------------------
    log("### Check 7: RecruiterReportGenerator Integration with 5D Scoring")
    generator = RecruiterReportGenerator()
    report = generator.generate_report(
        candidate_name="Alice Recruiter Test",
        job_role="Fullstack Engineer",
        session_start=datetime.now(timezone.utc),
        session_end=datetime.now(timezone.utc),
        evaluations=evals,
        behavioral_metrics=[
            ObservableCVMetrics(gaze_stability_ratio=88.0, head_pose_variance=85.0, frame_presence_ratio=90.0, facial_movement_dynamics=80.0)
        ],
        vocal_metrics=[
            ObservableVocalMetrics(speech_clarity_score=85.0, speaking_rate_wpm=140.0, pause_duration_ratio=0.20)
        ],
        coding_results=[{"overall_coding_score": 90.0}],
        role_fit_data={"overall_fit_score": 85.0},
    )

    log(f"- RecruiterReport overall_score: {report.overall_score}")
    log(f"- RecruiterReport technical_score: {report.technical_score}")
    log(f"- RecruiterReport coding_score: {report.coding_score}")
    log(f"- RecruiterReport role_fit_score: {report.role_fit_score}")
    log(f"- RecruiterReport fit_status: {report.fit_status}")
    log(f"- FiveDimensionScores attached: {bool(report.five_dimension_scores)}")

    if report.five_dimension_scores is not None and report.scoring_formula_audit is not None and report.role_fit_score == 85.0:
        log("✅ **Check 7 PASSED**: RecruiterReportGenerator generates 5-dimensional scores and attaches audit.")
        checks_passed += 1
    else:
        log("❌ **Check 7 FAILED**: RecruiterReportGenerator 5D integration issue.")
    log()

    # ----------------------------------------------------
    # Check 8: AnalysisService Harmonization
    # ----------------------------------------------------
    log("### Check 8: AnalysisService Harmonization with 5D Scoring Weights")
    analysis = AnalysisService()
    scores_dict = analysis.calculate_scores(
        evaluations=evals,
        frame_snapshots=[],
        coding_results=[{"overall_coding_score": 90.0}],
        role_fit_data={"overall_fit_score": 85.0},
    )

    log(f"- AnalysisService scores: {scores_dict}")

    if "technical_score" in scores_dict and "coding_score" in scores_dict and "role_fit_score" in scores_dict and "communication_score" in scores_dict and "behavioral_score" in scores_dict:
        log("✅ **Check 8 PASSED**: AnalysisService calculates all 5 dimensions.")
        checks_passed += 1
    else:
        log("❌ **Check 8 FAILED**: AnalysisService 5D harmonization issue.")
    log()

    # ----------------------------------------------------
    # Check 9: Zero Black-Box Scoring Invariant
    # ----------------------------------------------------
    log("### Check 9: Explainable Scoring Invariant (Zero Opaque Numbers)")
    calc_composite = (
        0.35 * res.technical_knowledge_score
        + 0.20 * res.coding_ability_score
        + 0.15 * res.role_fit_score
        + 0.15 * res.communication_score
        + 0.15 * res.behavioral_indicators_score
    )
    diff = abs(res.overall_composite_score - round(calc_composite, 2))

    log(f"- Composite Score in Model: {res.overall_composite_score}")
    log(f"- Mathematical Linear Combination: {round(calc_composite, 2)}")
    log(f"- Absolute Difference: {diff}")

    if diff < 1e-6:
        log("✅ **Check 9 PASSED**: 100% mathematical explainability verified. Zero black-box score injection.")
        checks_passed += 1
    else:
        log("❌ **Check 9 FAILED**: Discrepancy between composite and dimensional terms.")
    log()

    # ----------------------------------------------------
    # Check 10: Performance & Latency Benchmark
    # ----------------------------------------------------
    log("### Check 10: Performance & Latency Benchmark (< 5ms execution)")
    t_start = time.perf_counter()
    for _ in range(200):
        calculate_five_dimension_scores(
            evaluations=evals,
            coding_results=[{"overall_coding_score": 90.0}],
            role_fit_data={"overall_fit_score": 85.0},
            vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=85.0, speaking_rate_wpm=140.0)],
            cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=90.0, head_pose_variance=90.0)],
        )
    t_end = time.perf_counter()
    avg_latency_ms = ((t_end - t_start) / 200.0) * 1000.0

    log(f"- Average Execution Latency: {avg_latency_ms:.3f} ms (Target: < 5.0 ms)")

    if avg_latency_ms < 5.0:
        log("✅ **Check 10 PASSED**: Calculation throughput high and latency well below ceiling.")
        checks_passed += 1
    else:
        log("❌ **Check 10 FAILED**: High latency detected.")
    log()

    # ----------------------------------------------------
    # Summary
    # ----------------------------------------------------
    log("---")
    log(f"## Summary: {checks_passed}/{checks_total} Verification Checks Passed")
    status_str = "PASSED" if checks_passed == checks_total else "FAILED"
    log(f"**Overall Status**: **{status_str}**")

    # Save to report file
    report_path = REPO_ROOT / "feature-test-reports" / "FEAT-007-test-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    log(f"\nReport successfully saved to: {report_path}")
    return checks_passed == checks_total


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
