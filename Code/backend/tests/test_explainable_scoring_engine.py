"""Unit tests for the 5-Dimensional Explainable Scoring Engine (FEAT-007-BE)."""

import pytest
from typing import Dict, List

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


def test_weights_sum_to_one():
    """Verify that scoring weights sum exactly to 1.00 (100%) with role fit removed."""
    assert ScoringWeights.TECHNICAL_KNOWLEDGE == 0.45
    assert ScoringWeights.CODING_ABILITY == 0.25
    assert ScoringWeights.ROLE_FIT == 0.0
    assert ScoringWeights.COMMUNICATION == 0.15
    assert ScoringWeights.BEHAVIORAL_INDICATORS == 0.15

    total = (
        ScoringWeights.TECHNICAL_KNOWLEDGE
        + ScoringWeights.CODING_ABILITY
        + ScoringWeights.ROLE_FIT
        + ScoringWeights.COMMUNICATION
        + ScoringWeights.BEHAVIORAL_INDICATORS
    )
    assert abs(total - 1.00) < 1e-9
    assert abs(ScoringWeights.total_weight() - 1.00) < 1e-9


def test_composite_score_calculation():
    """Verify exact mathematical weighted sum calculation with 4 active dimensions."""
    tech = 80.0
    coding = 85.0
    comm = 85.0
    beh = 90.0

    expected_composite = round(
        0.45 * tech + 0.25 * coding + 0.15 * comm + 0.15 * beh, 2
    )
    # 0.45*80=36.0, 0.25*85=21.25, 0.15*85=12.75, 0.15*90=13.5 => 83.50
    assert expected_composite == 83.50

    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.5,
        )
    ]
    coding_results = [{"overall_coding_score": 85.0, "compile_success": True}]
    role_fit_data = {"overall_fit_score": 70.0}
    vocal_metrics = [ObservableVocalMetrics(speech_clarity_score=85.0, speaking_rate_wpm=140.0)]
    cv_metrics = [
        ObservableCVMetrics(
            gaze_stability_ratio=90.0,
            head_pose_variance=90.0,
            frame_presence_ratio=90.0,
            facial_movement_dynamics=90.0,
        )
    ]

    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=coding_results,
        role_fit_data=role_fit_data,
        vocal_metrics=vocal_metrics,
        cv_metrics=cv_metrics,
    )

    assert isinstance(scores, FiveDimensionScores)
    assert abs(scores.technical_knowledge_score - 80.0) < 0.5
    assert abs(scores.coding_ability_score - 85.0) < 0.5
    assert abs(scores.overall_composite_score - 83.50) < 1.0


def test_strong_fit_thresholds():
    """Verify CandidateFitStatus classification for Strong Fit (>= 85 overall, >= 80 tech)."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=9.0,
            depth_score=9.0,
            accuracy_score=90.0,
            communication_score=9.0,
        )
    ]
    coding_results = [{"overall_coding_score": 90.0, "compile_success": True}]
    role_fit_data = {"overall_fit_score": 85.0}
    vocal_metrics = [ObservableVocalMetrics(speech_clarity_score=90.0, speaking_rate_wpm=140.0)]
    cv_metrics = [
        ObservableCVMetrics(
            gaze_stability_ratio=90.0,
            head_pose_variance=90.0,
            frame_presence_ratio=95.0,
            facial_movement_dynamics=85.0,
        )
    ]

    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=coding_results,
        role_fit_data=role_fit_data,
        vocal_metrics=vocal_metrics,
        cv_metrics=cv_metrics,
    )

    assert scores.overall_composite_score >= 85.0
    assert scores.technical_knowledge_score >= 80.0
    assert scores.fit_status == CandidateFitStatus.STRONG_FIT


def test_all_fit_status_thresholds():
    """Verify Potential Fit, Needs Growth, and Not a Fit threshold transitions."""
    # Potential Fit: 70-84 overall
    pot_evals = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=7.5,
            depth_score=7.5,
            accuracy_score=75.0,
            communication_score=7.5,
        )
    ]
    pot_scores = calculate_five_dimension_scores(
        evaluations=pot_evals,
        coding_results=[{"overall_coding_score": 75.0}],
        role_fit_data={"overall_fit_score": 75.0},
        vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=75.0, speaking_rate_wpm=130.0)],
        cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=75.0, head_pose_variance=75.0, frame_presence_ratio=80.0)],
    )
    assert 70.0 <= pot_scores.overall_composite_score < 85.0
    assert pot_scores.fit_status == CandidateFitStatus.POTENTIAL_FIT

    # Needs Growth: 55-69 overall
    growth_evals = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=6.0,
            depth_score=6.0,
            accuracy_score=60.0,
            communication_score=6.0,
        )
    ]
    growth_scores = calculate_five_dimension_scores(
        evaluations=growth_evals,
        coding_results=[{"overall_coding_score": 60.0}],
        role_fit_data={"overall_fit_score": 60.0},
        vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=60.0, speaking_rate_wpm=110.0)],
        cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=60.0, head_pose_variance=60.0, frame_presence_ratio=70.0)],
    )
    assert 55.0 <= growth_scores.overall_composite_score < 70.0
    assert growth_scores.fit_status == CandidateFitStatus.NEEDS_GROWTH

    # Not a Fit: < 55 overall
    not_fit_evals = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=4.0,
            depth_score=4.0,
            accuracy_score=40.0,
            communication_score=4.0,
        )
    ]
    not_fit_scores = calculate_five_dimension_scores(
        evaluations=not_fit_evals,
        coding_results=[{"overall_coding_score": 40.0}],
        role_fit_data={"overall_fit_score": 40.0},
        vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=40.0, speaking_rate_wpm=90.0)],
        cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=40.0, head_pose_variance=40.0, frame_presence_ratio=50.0)],
    )
    assert not_fit_scores.overall_composite_score < 55.0
    assert not_fit_scores.fit_status == CandidateFitStatus.NOT_A_FIT


def test_scoring_audit_contains_all_steps():
    """Verify that scoring_formula_audit object contains all 5 dimension breakdowns, weights, and formula."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=7.0,
            accuracy_score=85.0,
            communication_score=8.0,
        )
    ]
    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=[{"overall_coding_score": 90.0}],
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[ObservableVocalMetrics(speech_clarity_score=80.0, speaking_rate_wpm=135.0)],
        cv_metrics=[ObservableCVMetrics(gaze_stability_ratio=85.0, head_pose_variance=80.0, frame_presence_ratio=90.0)],
    )

    audit = scores.scoring_formula_audit
    assert isinstance(audit, dict)
    assert "formula" in audit
    assert "weights" in audit
    assert "dimension_scores" in audit
    assert "weighted_contributions" in audit
    assert "dimension_audits" in audit

    # Check weights breakdown
    assert audit["weights"]["technical_knowledge"] == 0.45
    assert audit["weights"]["coding_ability"] == 0.25
    assert audit["weights"]["communication"] == 0.15
    assert audit["weights"]["behavioral_indicators"] == 0.15

    # Check active dimension audits exist
    dim_audits = audit["dimension_audits"]
    assert "technical_knowledge" in dim_audits
    assert "coding_ability" in dim_audits
    assert "communication" in dim_audits
    assert "behavioral_indicators" in dim_audits


def test_skipped_coding_defaults_to_zero():
    """Candidate skipped coding challenge → coding score defaults to 0.0 without crashing."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.0,
        )
    ]
    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=[],  # Skipped coding
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[],
        cv_metrics=[],
    )

    assert scores.coding_ability_score == 0.0
    assert scores.scoring_formula_audit["dimension_audits"]["coding_ability"]["status"] == "skipped_or_none"
    assert scores.overall_composite_score > 0.0


def test_no_video_frames_defaults_to_zero_with_audit():
    """No video frames available → behavioral indicator scores 0.0 with audit note."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.0,
        )
    ]
    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=[{"overall_coding_score": 80.0}],
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[],
        cv_metrics=[],  # No video
    )

    assert scores.behavioral_indicators_score == 0.0
    audit_beh = scores.scoring_formula_audit["dimension_audits"]["behavioral_indicators"]
    assert audit_beh["status"] == "no_data"
    assert "No video frames" in audit_beh["note"]
    # 15% behavioral weight is deducted with 0.0 score => 0.45*80 + 0.25*80 + 0.15*80 + 0.15*0 = 68.0
    assert scores.scoring_formula_audit["effective_weights"]["behavioral_indicators"] == 0.15
    assert abs(scores.overall_composite_score - 68.0) < 0.5


def test_uncalibrated_camera_presence_deducts_weights():
    """Candidate camera misaligned (presence < 25%) → marked insufficient_video_data and deducted from composite."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.0,
        )
    ]
    # CV metrics where face was only detected in 10% of frames (misaligned / off-camera)
    cv_metrics = [
        ObservableCVMetrics(
            gaze_stability_ratio=90.0,
            head_pose_variance=90.0,
            frame_presence_ratio=10.0,  # Below 25% threshold
            facial_movement_dynamics=80.0,
        )
    ]

    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=[{"overall_coding_score": 80.0}],
        role_fit_data={"overall_fit_score": 80.0},
        vocal_metrics=[],
        cv_metrics=cv_metrics,
    )

    assert scores.behavioral_indicators_score == 0.0
    audit_beh = scores.scoring_formula_audit["dimension_audits"]["behavioral_indicators"]
    assert audit_beh["status"] == "insufficient_video_data"
    assert audit_beh["is_calibrated"] is False
    assert "presence < 25%" in audit_beh["note"]
    # 15% behavioral weight is preserved and deducted => composite should be 68.0
    assert scores.scoring_formula_audit["effective_weights"]["behavioral_indicators"] == 0.15
    assert abs(scores.overall_composite_score - 68.0) < 0.5


def test_no_fake_eye_contact_when_camera_misaligned():
    """RecruiterReportGenerator must not invent fake compliments or high scores for uncalibrated video."""
    from datetime import datetime
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.0,
            candidate_transcript="I implemented an asynchronous worker pipeline using Redis queues.",
        )
    ]
    # Misaligned camera
    cv_metrics = [
        ObservableCVMetrics(
            gaze_stability_ratio=95.0,
            head_pose_variance=95.0,
            frame_presence_ratio=5.0,  # Face not in view
            facial_movement_dynamics=90.0,
        )
    ]

    generator = RecruiterReportGenerator()
    report = generator.generate_report(
        candidate_name="Test Candidate",
        job_role="Senior Python Engineer",
        session_start=datetime(2026, 9, 14, 10, 0),
        session_end=datetime(2026, 9, 14, 10, 30),
        evaluations=evaluations,
        behavioral_metrics=cv_metrics,
        vocal_metrics=[],
        coding_results=[{"overall_coding_score": 85.0}],
        role_fit_data={"overall_fit_score": 80.0},
    )

    # Behavioral score must be 0.0, not fake 73.0
    assert report.behavioral_score == 0.0
    assert report.eye_contact_score == 0.0
    # Strengths must NOT claim good eye contact
    for s in report.strengths:
        assert "eye contact" not in s.lower()
        assert "attentive" not in s.lower()
    # Narrative must mention uncalibrated video
    assert "uncalibrated" in report.behavioral_analysis.lower() or "not detected" in report.behavioral_analysis.lower()


def test_mongodb_serialized_behavioral_metrics_calibration():
    """Verify that serialized BehavioralMetrics dicts stored in MongoDB calibrate and contribute 15% weight."""
    evaluations = [
        AnswerEvaluation(
            question_index=0,
            question_type=QuestionType.TECHNICAL,
            relevance_score=8.0,
            depth_score=8.0,
            accuracy_score=80.0,
            communication_score=8.0,
        )
    ]
    # Serialized dictionary format as saved by to_serializable(BehavioralMetrics)
    serialized_cv_metrics = [
        {
            "eye_contact_score": 85.0,
            "head_stability_score": 90.0,
            "facial_engagement_score": 75.0,
            "fidgeting_score": 90.0,
            "confidence_posture_score": 90.0,
            "attention_span_score": 100.0,
            "red_flags": [],
            "frame_count": 6,
            "analysis_details": {
                "gaze_stability_ratio": 85.0,
                "head_pose_variance": 90.0,
                "facial_movement_dynamics": 75.0,
                "frame_presence_ratio": 100.0,
                "blink_frequency_cpm": 18.0,
            },
            "observable_cv_metrics": {
                "gaze_stability_ratio": 85.0,
                "head_pose_variance": 90.0,
                "facial_movement_dynamics": 75.0,
                "frame_presence_ratio": 100.0,
                "blink_frequency_cpm": 18.0,
                "observable_flags": [],
            },
        }
    ]

    scores = calculate_five_dimension_scores(
        evaluations=evaluations,
        coding_results=[{"overall_coding_score": 80.0}],
        role_fit_data={},
        vocal_metrics=[{"speech_clarity_score": 80.0, "speaking_rate_wpm": 140.0}],
        cv_metrics=serialized_cv_metrics,
    )

    assert scores.scoring_formula_audit["dimension_audits"]["behavioral_indicators"]["is_calibrated"] is True
    assert scores.scoring_formula_audit["effective_weights"]["behavioral_indicators"] == 0.15
    assert scores.behavioral_indicators_score > 80.0
    assert abs(scores.overall_composite_score - 80.0) < 2.0


