"""
Comprehensive Recruiter Report Generator and 5-Dimensional Explainable Scoring Engine.
Consolidates all evaluation metrics into actionable hiring decision report with complete mathematical audit trail.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    FrameAnalysisResult,
    InterviewReport,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionType,
)
from app.interview.domain.scoring_models import (
    CandidateFitStatus,
    FiveDimensionScores,
    ScoringWeights,
)
from app.interview.services.behavioral_analysis import BehavioralMetrics
from app.interview.services.vocal_analysis import VocalMetrics
from app.interview.services.feedback_generator import generate_tailored_feedback



def calculate_five_dimension_scores(
    evaluations: Optional[List[AnswerEvaluation]] = None,
    coding_results: Optional[List[Dict]] = None,
    role_fit_data: Optional[Dict] = None,
    vocal_metrics: Optional[List[Any]] = None,
    cv_metrics: Optional[List[Any]] = None,
) -> FiveDimensionScores:
    """
    Calculate transparent, explainable 5-dimensional scores with complete mathematical audit trail.

    Dimensions:
    1. Technical Knowledge (35%): Rubric-weighted average (30% relevance + 40% depth + 30% accuracy)
    2. Coding Ability (20%): Hidden and public test case pass score (defaults to 0.0 if skipped)
    3. Role Fit (15%): Profile competency coverage alignment (defaults to 0.0 if no profile)
    4. Communication (15%): Verbal rubric score (60%) + acoustic speech clarity & speaking rate (40%)
    5. Behavioral Indicators (15%): Observable CV signals (gaze, head pose, presence, dynamics)

    Returns:
        FiveDimensionScores with all dimension scores, overall composite score, fit status, and audit dictionary.
    """
    evaluations = evaluations or []
    coding_results = coding_results or []
    role_fit_data = role_fit_data or {}
    vocal_metrics = vocal_metrics or []
    cv_metrics = cv_metrics or []

    # 1. Technical Knowledge (35%)
    tech_evals = [
        e for e in evaluations
        if (getattr(e, "question_type", None) in [
            QuestionType.TECHNICAL,
            QuestionType.CV_BASED,
            getattr(QuestionType, "CORE_TECHNICAL", None),
            getattr(QuestionType, "DEEP_DIVE", None),
            getattr(QuestionType, "FOLLOW_UP", None),
        ] or getattr(getattr(e, "question_type", None), "value", "") in [
            "technical", "core_technical", "deep_dive", "cv_based", "follow_up"
        ])
    ]
    target_tech_evals = tech_evals if tech_evals else evaluations

    tech_question_audits = []
    if target_tech_evals:
        q_scores = []
        for e in target_tech_evals:
            rel_raw = float(getattr(e, "relevance_score", 0.0) or 0.0)
            rel_norm = min(100.0, max(0.0, rel_raw * 10.0 if rel_raw <= 10.0 else rel_raw))

            depth_raw = float(getattr(e, "depth_score", 0.0) or 0.0)
            depth_norm = min(100.0, max(0.0, depth_raw * 10.0 if depth_raw <= 10.0 else depth_raw))

            acc_raw = float(getattr(e, "accuracy_score", 0.0) or 0.0)
            acc_norm = min(100.0, max(0.0, acc_raw))

            # Rubric weights: 30% relevance, 40% depth, 30% accuracy
            q_score = (rel_norm * 0.30) + (depth_norm * 0.40) + (acc_norm * 0.30)
            q_scores.append(q_score)
            tech_question_audits.append({
                "question_index": getattr(e, "question_index", 0),
                "relevance_raw": rel_raw,
                "depth_raw": depth_raw,
                "accuracy_raw": acc_raw,
                "rubric_weighted_score": round(q_score, 2),
            })
        technical_score = round(sum(q_scores) / len(q_scores), 2)
        tech_audit = {
            "status": "evaluated",
            "evaluations_count": len(target_tech_evals),
            "relevance_mean": round(sum(a["relevance_raw"] for a in tech_question_audits) / len(tech_question_audits), 2),
            "depth_mean": round(sum(a["depth_raw"] for a in tech_question_audits) / len(tech_question_audits), 2),
            "accuracy_mean": round(sum(a["accuracy_raw"] for a in tech_question_audits) / len(tech_question_audits), 2),
            "per_question_scores": tech_question_audits,
            "final_score": technical_score,
        }
    else:
        technical_score = 0.0
        tech_audit = {
            "status": "no_data",
            "note": "No technical evaluations available",
            "final_score": 0.0,
        }

    # 2. Coding Ability (20%)
    if coding_results:
        # Deduplicate per distinct challenge/question_index (keep latest attempt)
        dedup_coding = {}
        for idx, cr in enumerate(coding_results):
            if isinstance(cr, dict):
                key = cr.get("question_index")
                if key is None:
                    key = cr.get("challenge_id", cr.get("title", f"challenge_{idx}"))
                dedup_coding[key] = cr
            else:
                q_idx = getattr(cr, "question_index", None)
                c_id = getattr(cr, "challenge_id", None)
                key = q_idx if q_idx is not None else (c_id or f"challenge_{idx}")
                dedup_coding[key] = cr
        unique_coding = list(dedup_coding.values())

        c_scores = []
        coding_details = []
        for idx, cr in enumerate(unique_coding):
            if isinstance(cr, dict):
                if "overall_coding_score" in cr:
                    c_score = float(cr["overall_coding_score"])
                elif cr.get("all_passed", False):
                    c_score = 100.0
                elif cr.get("compile_success", False) is False:
                    c_score = 0.0
                else:
                    passed = cr.get("passed", cr.get("passed_count", 0))
                    total = max(1, cr.get("total", cr.get("total_count", 1)))
                    c_score = (passed / total) * 100.0
                coding_details.append({
                    "challenge_index": idx,
                    "compile_success": cr.get("compile_success", True),
                    "score": round(c_score, 2),
                })
            else:
                c_score = float(getattr(cr, "overall_coding_score", 0.0))
                coding_details.append({
                    "challenge_index": idx,
                    "compile_success": getattr(cr, "compile_success", True),
                    "score": round(c_score, 2),
                })
            c_scores.append(c_score)
        coding_score = round(sum(c_scores) / len(c_scores), 2)
        coding_audit = {
            "status": "evaluated",
            "challenges_count": len(unique_coding),
            "details": coding_details,
            "final_score": coding_score,
        }
    else:
        coding_score = 0.0
        coding_audit = {
            "status": "skipped_or_none",
            "note": "Candidate skipped coding challenge or no coding challenges submitted",
            "final_score": 0.0,
        }

    # 3. Role Fit (15%)
    if role_fit_data and any(k in role_fit_data for k in ["overall_fit_score", "role_fit_score"]):
        role_fit_score = float(role_fit_data.get("overall_fit_score", role_fit_data.get("role_fit_score", 0.0)))
        role_fit_score = round(min(100.0, max(0.0, role_fit_score)), 2)
        role_fit_audit = {
            "status": "evaluated",
            "role": role_fit_data.get("role", "custom"),
            "matched_skills_count": len(role_fit_data.get("matched_skills", [])),
            "missing_concepts_count": len(role_fit_data.get("missing_concepts", [])),
            "final_score": role_fit_score,
        }
    else:
        role_fit_score = 0.0
        role_fit_audit = {
            "status": "no_data",
            "note": "No profile competency role fit data provided",
            "final_score": 0.0,
        }

    # 4. Communication (15%)
    verbal_scores = []
    for e in evaluations:
        comm_raw = float(getattr(e, "communication_score", 0.0) or 0.0)
        comm_norm = min(100.0, max(0.0, comm_raw * 10.0 if comm_raw <= 10.0 else comm_raw))
        verbal_scores.append(comm_norm)
    verbal_mean = (sum(verbal_scores) / len(verbal_scores)) if verbal_scores else None

    vocal_scores = []
    vocal_audit_items = []
    for vm in vocal_metrics:
        if isinstance(vm, dict):
            acoustic_flags = vm.get("acoustic_flags", vm.get("red_flags", []))
            clarity = float(vm.get("speech_clarity_score", vm.get("clarity", 0.0)))
            wpm = float(vm.get("speaking_rate_wpm", vm.get("speech_rate", 0.0)))
            pause = float(vm.get("pause_duration_ratio", vm.get("pause_pattern", 0.0)))
        else:
            acoustic_flags = getattr(vm, "acoustic_flags", getattr(vm, "red_flags", []))
            clarity = float(getattr(vm, "speech_clarity_score", 0.0))
            wpm = float(getattr(vm, "speaking_rate_wpm", 0.0))
            pause = float(getattr(vm, "pause_duration_ratio", 0.0))

        # Check if this metric was from a text input / no-audio question
        is_empty_audio = (
            (wpm == 0.0 and clarity == 0.0 and pause == 0.0)
            or any("no audio" in str(f).lower() or "empty" in str(f).lower() or "not provided" in str(f).lower() for f in acoustic_flags)
        )
        if is_empty_audio:
            continue

        # If candidate was completely silent (0 WPM with near-zero energy or pure pause)
        if wpm == 0.0 and (clarity == 0.0 or pause >= 0.90):
            v_score = 0.0
        else:
            # Conversational WPM norm: 120-160
            if 120.0 <= wpm <= 160.0:
                rate_score = 100.0
            elif wpm < 120.0:
                rate_score = max(0.0, 100.0 - (120.0 - wpm) * 1.0)
            else:
                rate_score = max(0.0, 100.0 - (wpm - 160.0) * 1.0)

            # Pause duration ratio norm: 0.10 - 0.25
            if 0.10 <= pause <= 0.25:
                pause_score = 100.0
            else:
                pause_score = max(0.0, 100.0 - abs(pause - 0.20) * 200.0)

            v_score = clarity * 0.50 + rate_score * 0.30 + pause_score * 0.20

        vocal_scores.append(v_score)
        vocal_audit_items.append({"clarity": clarity, "wpm": wpm, "pause_ratio": pause, "vocal_score": round(v_score, 2)})

    vocal_mean = (sum(vocal_scores) / len(vocal_scores)) if vocal_scores else None

    if verbal_mean is not None and vocal_mean is not None:
        communication_score = round(verbal_mean * 0.60 + vocal_mean * 0.40, 2)
        comm_status = "verbal_and_vocal"
    elif verbal_mean is not None:
        communication_score = round(verbal_mean, 2)
        comm_status = "written_text_mode"
    elif vocal_mean is not None:
        communication_score = round(vocal_mean, 2)
        comm_status = "vocal_only"
    else:
        communication_score = 0.0
        comm_status = "no_data"

    comm_audit = {
        "status": comm_status,
        "verbal_score": round(verbal_mean, 2) if verbal_mean is not None else None,
        "vocal_score": round(vocal_mean, 2) if vocal_mean is not None else None,
        "vocal_details": vocal_audit_items,
        "final_score": communication_score,
        "input_mode": "text" if comm_status == "written_text_mode" else "voice",
    }

    # 5. Behavioral Indicators (15%)
    if cv_metrics:
        beh_scores = []
        beh_details = []
        presence_values = []
        for cm in cv_metrics:
            if isinstance(cm, dict):
                obs = cm.get("observable_cv_metrics") if isinstance(cm.get("observable_cv_metrics"), dict) else {}
                details = cm.get("analysis_details") if isinstance(cm.get("analysis_details"), dict) else {}
                gaze = float(
                    obs.get("gaze_stability_ratio")
                    or details.get("gaze_stability_ratio")
                    or cm.get("gaze_stability_ratio")
                    or cm.get("eye_contact_score")
                    or cm.get("eye_contact")
                    or 0.0
                )
                head = float(
                    obs.get("head_pose_variance")
                    or details.get("head_pose_variance")
                    or cm.get("head_pose_variance")
                    or cm.get("head_stability_score")
                    or cm.get("head_stability")
                    or 0.0
                )
                presence = float(
                    obs.get("frame_presence_ratio")
                    or details.get("frame_presence_ratio")
                    or cm.get("frame_presence_ratio")
                    or cm.get("attention_span_score")
                    or cm.get("attention_span")
                    or 0.0
                )
                dynamics = float(
                    obs.get("facial_movement_dynamics")
                    or details.get("facial_movement_dynamics")
                    or cm.get("facial_movement_dynamics")
                    or cm.get("facial_engagement_score")
                    or cm.get("engagement")
                    or 0.0
                )
            elif hasattr(cm, "gaze_stability_ratio"):
                gaze = float(getattr(cm, "gaze_stability_ratio", 0.0) or 0.0)
                head = float(getattr(cm, "head_pose_variance", 0.0) or 0.0)
                presence = float(getattr(cm, "frame_presence_ratio", 0.0) or 0.0)
                dynamics = float(getattr(cm, "facial_movement_dynamics", 0.0) or 0.0)
            elif hasattr(cm, "eye_contact_score"):
                gaze = float(getattr(cm, "eye_contact_score", 0.0) or 0.0)
                head = float(getattr(cm, "head_stability_score", 0.0) or 0.0)
                presence = float(getattr(cm, "attention_span_score", 0.0) or 0.0)
                dynamics = float(getattr(cm, "facial_engagement_score", 0.0) or 0.0)
            else:
                gaze, head, presence, dynamics = 0.0, 0.0, 0.0, 0.0

            # Normalize ratios in (0.0, 1.0] to 0-100 percentage scale
            if 0.0 < gaze <= 1.0:
                gaze = gaze * 100.0
            if 0.0 < head <= 1.0:
                head = head * 100.0
            if 0.0 < presence <= 1.0:
                presence = presence * 100.0
            if 0.0 < dynamics <= 1.0:
                dynamics = dynamics * 100.0

            b_score = gaze * 0.35 + head * 0.25 + presence * 0.25 + dynamics * 0.15
            beh_scores.append(b_score)
            presence_values.append(presence)
            beh_details.append({"gaze": gaze, "head_pose": head, "presence": presence, "dynamics": dynamics, "score": round(b_score, 2)})

        avg_presence = (sum(presence_values) / len(presence_values)) if presence_values else 0.0

        # Video is calibrated only if average frame presence meets or exceeds 25%
        if avg_presence >= 25.0:
            behavioral_indicators_score = round(sum(beh_scores) / len(beh_scores), 2)
            is_behavioral_calibrated = True
            beh_audit = {
                "status": "evaluated",
                "is_calibrated": True,
                "frames_analyzed": len(cv_metrics),
                "avg_presence_ratio": round(avg_presence, 2),
                "details": beh_details,
                "final_score": behavioral_indicators_score,
            }
        else:
            behavioral_indicators_score = 0.0
            is_behavioral_calibrated = False
            beh_audit = {
                "status": "insufficient_video_data",
                "is_calibrated": False,
                "frames_analyzed": len(cv_metrics),
                "avg_presence_ratio": round(avg_presence, 2),
                "note": "Candidate face was not detected in camera view (presence < 25%) or tracking was uncalibrated. 15% behavioral indicator weight applied with deduction (raw score: 0.0) in composite evaluation.",
                "final_score": 0.0,
            }
    else:
        behavioral_indicators_score = 0.0
        is_behavioral_calibrated = False
        beh_audit = {
            "status": "no_data",
            "is_calibrated": False,
            "note": "No video frames or CV metrics available. 15% behavioral indicator weight applied with deduction (raw score: 0.0) in composite evaluation.",
            "final_score": 0.0,
        }

    # Overall Composite Calculation (Role Fit Removed)
    # Canonical Weights strictly maintained at 100%:
    # Technical 45%, Coding 25%, Communication 15%, Behavioral 15%
    # If behavioral video tracking is uncalibrated or missing, the 15% weight is preserved
    # and deducted from the overall composite score (raw score: 0.0) rather than excluded.
    eff_w_tech = ScoringWeights.TECHNICAL_KNOWLEDGE
    eff_w_coding = ScoringWeights.CODING_ABILITY
    eff_w_role = 0.0
    eff_w_comm = ScoringWeights.COMMUNICATION
    eff_w_beh = ScoringWeights.BEHAVIORAL_INDICATORS
    overall_composite_score = round(
        eff_w_tech * technical_score
        + eff_w_coding * coding_score
        + eff_w_comm * communication_score
        + eff_w_beh * behavioral_indicators_score,
        2,
    )
    if is_behavioral_calibrated:
        formula_str = (
            "0.45 * technical_knowledge + 0.25 * coding_ability + 0.15 * communication + 0.15 * behavioral_indicators"
        )
    else:
        formula_str = (
            "0.45 * technical_knowledge + 0.25 * coding_ability + 0.15 * communication + 0.15 * behavioral_indicators "
            "(Behavioral indicators deducted due to uncalibrated/missing camera tracking)"
        )

    # Fit Status Classification
    coding_qualifies = coding_score >= 75.0 if coding_results else True
    if overall_composite_score >= 85.0 and technical_score >= 80.0 and coding_qualifies:
        fit_status = CandidateFitStatus.STRONG_FIT
    elif overall_composite_score >= 70.0:
        fit_status = CandidateFitStatus.POTENTIAL_FIT
    elif overall_composite_score >= 55.0:
        fit_status = CandidateFitStatus.NEEDS_GROWTH
    else:
        fit_status = CandidateFitStatus.NOT_A_FIT

    scoring_formula_audit = {
        "formula": formula_str,
        "weights": ScoringWeights.as_dict(),
        "effective_weights": {
            "technical_knowledge": round(eff_w_tech, 4),
            "coding_ability": round(eff_w_coding, 4),
            "role_fit": 0.0,
            "communication": round(eff_w_comm, 4),
            "behavioral_indicators": round(eff_w_beh, 4),
        },
        "dimension_scores": {
            "technical_knowledge_score": technical_score,
            "coding_ability_score": coding_score,
            "role_fit_score": 0.0,
            "communication_score": communication_score,
            "behavioral_indicators_score": behavioral_indicators_score,
        },
        "weighted_contributions": {
            "technical_knowledge": round(eff_w_tech * technical_score, 2),
            "coding_ability": round(eff_w_coding * coding_score, 2),
            "role_fit": 0.0,
            "communication": round(eff_w_comm * communication_score, 2),
            "behavioral_indicators": round(eff_w_beh * behavioral_indicators_score, 2),
        },
        "overall_composite_score": overall_composite_score,
        "fit_status": fit_status.value,
        "dimension_audits": {
            "technical_knowledge": tech_audit,
            "coding_ability": coding_audit,
            "communication": comm_audit,
            "behavioral_indicators": beh_audit,
        },
    }

    return FiveDimensionScores(
        technical_knowledge_score=technical_score,
        coding_ability_score=coding_score,
        role_fit_score=0.0,
        communication_score=communication_score,
        behavioral_indicators_score=behavioral_indicators_score,
        overall_composite_score=overall_composite_score,
        fit_status=fit_status,
        scoring_formula_audit=scoring_formula_audit,
    )


@dataclass
class RecruiterReport:
    """Comprehensive recruiter report with hiring recommendation."""
    # Candidate Info
    candidate_name: str
    job_role: str
    interview_date: str
    session_duration_minutes: float
    
    # Overall Scores (0-100)
    overall_score: float
    hiring_recommendation: str  # "Strong Fit", "Potential Fit", "Needs Growth", "Not a Fit" (or "Strong Hire", etc.)
    confidence_level: str  # "High", "Medium", "Low"
    
    # Category Scores
    technical_score: float
    communication_score: float
    behavioral_score: float
    coding_score: float
    
    # Detailed Metrics
    vocal_confidence: float
    eye_contact_score: float
    attention_span: float
    speech_clarity: float
    fidgeting_score: float
    
    # Red Flags & Strengths
    red_flags: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    
    # Question Performance
    questions_answered: int
    questions_skipped: int
    follow_ups_triggered: int
    coding_challenges_passed: int
    coding_challenges_total: int
    
    # Detailed Analysis
    technical_analysis: str
    behavioral_analysis: str
    communication_analysis: str
    coding_analysis: str
    
    # Decision Summary
    executive_summary: str
    detailed_recommendation: str
    next_steps: str

    # 5-Dimensional Explainable Scoring
    role_fit_score: float = 0.0
    fit_status: Optional[str] = None
    five_dimension_scores: Optional[Dict[str, Any]] = None
    scoring_formula_audit: Optional[Dict[str, Any]] = None

    # Evidence-Anchored Tailored Feedback
    tailored_feedback: Optional[Dict[str, Any]] = None


class RecruiterReportGenerator:
    """
    Generates comprehensive recruiter reports from interview data.
    Consolidates technical, behavioral, vocal, and coding metrics with explainable 5-dimensional scoring.
    """
    
    def generate_report(
        self,
        candidate_name: str,
        job_role: str,
        session_start: datetime,
        session_end: datetime,
        evaluations: List[AnswerEvaluation],
        behavioral_metrics: List[BehavioralMetrics],
        vocal_metrics: List[VocalMetrics],
        coding_results: List[Dict],
        aggregate_scores: Optional[Dict] = None,
        role_fit_data: Optional[Dict] = None,
    ) -> RecruiterReport:
        """
        Generate comprehensive recruiter report using explainable 5-dimensional scoring.
        """
        # Calculate duration
        duration = (session_end - session_start).total_seconds() / 60
        
        # Aggregate behavioral metrics
        avg_behavioral = self._aggregate_behavioral_metrics(behavioral_metrics)
        
        # Aggregate vocal metrics
        avg_vocal = self._aggregate_vocal_metrics(vocal_metrics)
        
        # Analyze technical performance
        technical_analysis = self._analyze_technical_performance(evaluations)
        
        # Analyze coding performance
        coding_analysis = self._analyze_coding_performance(coding_results)
        
        # 5-Dimensional Explainable Scoring Engine
        five_dim = calculate_five_dimension_scores(
            evaluations=evaluations,
            coding_results=coding_results,
            role_fit_data=role_fit_data or (aggregate_scores.get("role_fit_data") if aggregate_scores else None) or {},
            vocal_metrics=vocal_metrics,
            cv_metrics=behavioral_metrics,
        )

        technical_score = five_dim.technical_knowledge_score
        coding_score = five_dim.coding_ability_score
        role_fit_score = five_dim.role_fit_score
        communication_score = five_dim.communication_score
        behavioral_score = five_dim.behavioral_indicators_score
        overall_score = five_dim.overall_composite_score
        fit_status_str = five_dim.fit_status.value

        # Generate Evidence-Anchored Tailored Feedback
        from app.interview.domain.role_taxonomy import (
            StandardRole,
            get_role_competency_matrix,
            parse_standard_role,
        )
        standard_role = parse_standard_role(job_role)
        role_comps = get_role_competency_matrix(standard_role)

        coding_eval_target = None
        if coding_results:
            coding_eval_target = coding_results[0] if len(coding_results) == 1 else coding_results

        tailored_fb = generate_tailored_feedback(
            evaluations=evaluations,
            coding_evaluation=coding_eval_target,
            role_competencies=role_comps,
            vocal_metrics=vocal_metrics,
            cv_metrics=behavioral_metrics,
        )
        
        # Collect red flags and strengths
        all_red_flags = self._collect_all_red_flags(
            evaluations, behavioral_metrics, vocal_metrics
        )

        # Hiring recommendation
        recommendation, confidence = self._determine_hiring_recommendation(
            overall_score,
            technical_score,
            behavioral_score,
            coding_score,
            len(all_red_flags),
            fit_status_val=fit_status_str,
        )
        strengths = self._identify_strengths(
            technical_score,
            communication_score,
            behavioral_score,
            coding_score,
            avg_behavioral,
            avg_vocal
        )
        improvements = self._identify_improvements(
            technical_score,
            communication_score,
            behavioral_score,
            coding_score,
            all_red_flags
        )
        
        # Question statistics
        questions_answered = len(evaluations)
        questions_skipped = sum(
            1 for e in evaluations 
            if "skip" in e.candidate_transcript.lower()
        )
        follow_ups = sum(1 for e in evaluations if e.follow_up_triggered)
        
        # Generate narrative analyses
        tech_narrative = self._generate_technical_narrative(
            technical_analysis, evaluations
        )
        behavioral_narrative = self._generate_behavioral_narrative(
            avg_behavioral, behavioral_metrics
        )
        communication_narrative = self._generate_communication_narrative(
            avg_vocal, communication_score
        )
        coding_narrative = self._generate_coding_narrative(coding_analysis)
        
        # Executive summary
        executive_summary = self._generate_executive_summary(
            candidate_name,
            job_role,
            overall_score,
            recommendation,
            strengths[:3],
            all_red_flags[:3]
        )
        
        # Detailed recommendation
        detailed_rec = self._generate_detailed_recommendation(
            recommendation,
            overall_score,
            technical_score,
            behavioral_score,
            coding_score,
            all_red_flags
        )
        
        # Next steps
        next_steps = self._generate_next_steps(recommendation, improvements)
        
        return RecruiterReport(
            candidate_name=candidate_name,
            job_role=job_role,
            interview_date=session_start.strftime("%Y-%m-%d %H:%M"),
            session_duration_minutes=round(duration, 1),
            overall_score=round(overall_score, 1),
            hiring_recommendation=recommendation,
            confidence_level=confidence,
            technical_score=round(technical_score, 1),
            communication_score=round(communication_score, 1),
            behavioral_score=round(behavioral_score, 1),
            coding_score=round(coding_score, 1),
            vocal_confidence=round(avg_vocal.get("vocal_confidence", 0), 1),
            eye_contact_score=round(avg_behavioral.get("eye_contact", 0), 1),
            attention_span=round(avg_behavioral.get("attention_span", 0), 1),
            speech_clarity=round(avg_vocal.get("clarity", 0), 1),
            fidgeting_score=round(avg_behavioral.get("fidgeting", 0), 1),
            red_flags=all_red_flags,
            strengths=strengths,
            areas_for_improvement=improvements,
            questions_answered=questions_answered,
            questions_skipped=questions_skipped,
            follow_ups_triggered=follow_ups,
            coding_challenges_passed=coding_analysis["passed"],
            coding_challenges_total=coding_analysis["total"],
            technical_analysis=tech_narrative,
            behavioral_analysis=behavioral_narrative,
            communication_analysis=communication_narrative,
            coding_analysis=coding_narrative,
            executive_summary=executive_summary,
            detailed_recommendation=detailed_rec,
            next_steps=next_steps,
            role_fit_score=round(role_fit_score, 1),
            fit_status=fit_status_str,
            five_dimension_scores=five_dim.model_dump(),
            scoring_formula_audit=five_dim.scoring_formula_audit,
            tailored_feedback=tailored_fb.model_dump(),
        )


    
    def _aggregate_behavioral_metrics(
        self, 
        behavioral_metrics: List[Any]
    ) -> Dict:
        """Aggregate behavioral metrics across all questions."""
        if not behavioral_metrics:
            return {
                "eye_contact": 0.0,
                "head_stability": 0.0,
                "engagement": 0.0,
                "fidgeting": 0.0,
                "confidence_posture": 0.0,
                "attention_span": 0.0,
                "is_video_available": False,
                "video_status": "no_video_provided",
            }
        
        eye_contacts = []
        head_stabilities = []
        engagements = []
        fidgetings = []
        confidence_postures = []
        attention_spans = []

        for m in behavioral_metrics:
            if isinstance(m, dict):
                obs = m.get("observable_cv_metrics") if isinstance(m.get("observable_cv_metrics"), dict) else {}
                details = m.get("analysis_details") if isinstance(m.get("analysis_details"), dict) else {}
                gaze = float(
                    obs.get("gaze_stability_ratio")
                    or details.get("gaze_stability_ratio")
                    or m.get("gaze_stability_ratio")
                    or m.get("eye_contact_score")
                    or m.get("eye_contact")
                    or 0.0
                )
                head = float(
                    obs.get("head_pose_variance")
                    or details.get("head_pose_variance")
                    or m.get("head_pose_variance")
                    or m.get("head_stability_score")
                    or m.get("head_stability")
                    or 0.0
                )
                engagement = float(
                    obs.get("facial_movement_dynamics")
                    or details.get("facial_movement_dynamics")
                    or m.get("facial_movement_dynamics")
                    or m.get("facial_engagement_score")
                    or m.get("engagement")
                    or 0.0
                )
                fidgeting = float(
                    m.get("fidgeting_score")
                    or m.get("fidgeting")
                    or head
                    or 0.0
                )
                presence = float(
                    obs.get("frame_presence_ratio")
                    or details.get("frame_presence_ratio")
                    or m.get("frame_presence_ratio")
                    or m.get("attention_span_score")
                    or m.get("attention_span")
                    or 0.0
                )
                posture = float(
                    m.get("confidence_posture_score")
                    or m.get("confidence_posture")
                    or head
                    or 0.0
                )
            elif hasattr(m, "gaze_stability_ratio"):
                gaze = float(getattr(m, "gaze_stability_ratio", 0.0) or 0.0)
                head = float(getattr(m, "head_pose_variance", 0.0) or 0.0)
                engagement = float(getattr(m, "facial_movement_dynamics", 0.0) or 0.0)
                fidgeting = float(getattr(m, "head_pose_variance", 0.0) or 0.0)
                presence = float(getattr(m, "frame_presence_ratio", 0.0) or 0.0)
                posture = float(getattr(m, "gaze_stability_ratio", 0.0) or 0.0)
            elif hasattr(m, "eye_contact_score"):
                gaze = float(getattr(m, "eye_contact_score", 0.0) or 0.0)
                head = float(getattr(m, "head_stability_score", 0.0) or 0.0)
                engagement = float(getattr(m, "facial_engagement_score", 0.0) or 0.0)
                fidgeting = float(getattr(m, "fidgeting_score", 0.0) or 0.0)
                presence = float(getattr(m, "attention_span_score", 0.0) or 0.0)
                posture = float(getattr(m, "confidence_posture_score", 0.0) or 0.0)
            else:
                gaze, head, engagement, fidgeting, presence, posture = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

            # Normalize ratios in (0.0, 1.0] to 0-100 percentage scale
            if 0.0 < gaze <= 1.0:
                gaze *= 100.0
            if 0.0 < head <= 1.0:
                head *= 100.0
            if 0.0 < engagement <= 1.0:
                engagement *= 100.0
            if 0.0 < fidgeting <= 1.0:
                fidgeting *= 100.0
            if 0.0 < presence <= 1.0:
                presence *= 100.0
            if 0.0 < posture <= 1.0:
                posture *= 100.0

            eye_contacts.append(gaze)
            head_stabilities.append(head)
            engagements.append(engagement)
            fidgetings.append(fidgeting)
            confidence_postures.append(posture)
            attention_spans.append(presence)

        n = len(behavioral_metrics)
        avg_attention = sum(attention_spans) / n if n else 0.0
        is_calibrated = avg_attention >= 25.0

        return {
            "eye_contact": sum(eye_contacts) / n if is_calibrated else 0.0,
            "head_stability": sum(head_stabilities) / n if is_calibrated else 0.0,
            "engagement": sum(engagements) / n if is_calibrated else 0.0,
            "fidgeting": sum(fidgetings) / n if is_calibrated else 0.0,
            "confidence_posture": sum(confidence_postures) / n if is_calibrated else 0.0,
            "attention_span": avg_attention if is_calibrated else 0.0,
            "is_video_available": is_calibrated,
            "video_status": "calibrated" if is_calibrated else "insufficient_face_tracking",
        }
    
    def _aggregate_vocal_metrics(self, vocal_metrics: List[Any]) -> Dict:
        """Aggregate vocal metrics across all questions."""
        if not vocal_metrics:
            return {
                "vocal_confidence": 0,
                "clarity": 0,
                "pitch_variance": 0,
                "speech_rate": 0,
                "pause_pattern": 0,
                "tone_consistency": 0,
                "communication_effectiveness": 0
            }
        
        vocal_confidences = []
        clarities = []
        pitch_variances = []
        speech_rates = []
        pause_patterns = []
        tone_consistencies = []
        communication_effectivenesses = []

        valid_metrics = []
        for m in vocal_metrics:
            if isinstance(m, dict):
                flags = m.get("acoustic_flags", m.get("red_flags", []))
                wpm = float(m.get("speaking_rate_wpm", m.get("speech_rate", 0.0)))
                clarity = float(m.get("speech_clarity_score", m.get("clarity", 0.0)))
            else:
                flags = getattr(m, "acoustic_flags", getattr(m, "red_flags", []))
                wpm = float(getattr(m, "speaking_rate_wpm", getattr(m, "speech_rate_score", 0.0)))
                clarity = float(getattr(m, "speech_clarity_score", 0.0))

            if (wpm == 0 and clarity == 0) or any("no audio" in str(f).lower() or "empty" in str(f).lower() for f in flags):
                continue
            valid_metrics.append(m)

        if not valid_metrics:
            return {
                "vocal_confidence": 0.0,
                "clarity": 0.0,
                "pitch_variance": 0.0,
                "speech_rate": 0.0,
                "pause_pattern": 0.0,
                "tone_consistency": 0.0,
                "communication_effectiveness": 0.0,
                "is_text_mode": True,
            }

        for m in valid_metrics:
            if isinstance(m, dict):
                vocal_confidences.append(float(m.get("vocal_confidence", m.get("speech_clarity_score", 70.0))))
                clarities.append(float(m.get("clarity", m.get("speech_clarity_score", 70.0))))
                pitch_variances.append(float(m.get("pitch_variance", m.get("pitch_semitone_variance", 70.0))))
                speech_rates.append(float(m.get("speech_rate", m.get("speaking_rate_wpm", 140.0))))
                pause_patterns.append(float(m.get("pause_pattern", 75.0)))
                tone_consistencies.append(float(m.get("tone_consistency", 70.0)))
                communication_effectivenesses.append(float(m.get("communication_effectiveness", 70.0)))
            elif hasattr(m, "vocal_confidence_score"):
                vocal_confidences.append(float(m.vocal_confidence_score))
                clarities.append(float(m.speech_clarity_score))
                pitch_variances.append(float(m.pitch_variance_score))
                speech_rates.append(float(m.speech_rate_score))
                pause_patterns.append(float(m.pause_pattern_score))
                tone_consistencies.append(float(m.tone_consistency_score))
                communication_effectivenesses.append(float(m.communication_effectiveness))
            elif hasattr(m, "speech_clarity_score"):
                vocal_confidences.append(float(m.speech_clarity_score))
                clarities.append(float(m.speech_clarity_score))
                pitch_variances.append(float(m.pitch_semitone_variance))
                speech_rates.append(min(100.0, max(0.0, float(m.speaking_rate_wpm) / 1.6)))
                pause_patterns.append(max(0.0, 100.0 - abs(float(m.pause_duration_ratio) - 0.20) * 200.0))
                tone_consistencies.append(float(m.speech_clarity_score))
                communication_effectivenesses.append(float(m.speech_clarity_score))
            else:
                vocal_confidences.append(70.0)
                clarities.append(70.0)
                pitch_variances.append(70.0)
                speech_rates.append(70.0)
                pause_patterns.append(70.0)
                tone_consistencies.append(70.0)
                communication_effectivenesses.append(70.0)

        n = len(valid_metrics)
        return {
            "vocal_confidence": sum(vocal_confidences) / n,
            "clarity": sum(clarities) / n,
            "pitch_variance": sum(pitch_variances) / n,
            "speech_rate": sum(speech_rates) / n,
            "pause_pattern": sum(pause_patterns) / n,
            "tone_consistency": sum(tone_consistencies) / n,
            "communication_effectiveness": sum(communication_effectivenesses) / n,
            "is_text_mode": False,
        }
    
    def _analyze_technical_performance(
        self, 
        evaluations: List[AnswerEvaluation]
    ) -> Dict:
        """Analyze technical question performance with scale normalization."""
        if not evaluations:
            return {"score": 0, "strong_areas": [], "weak_areas": []}
        
        # Filter technical questions
        tech_evals = [
            e for e in evaluations 
            if getattr(e.question_type, "value", str(e.question_type)) in ["technical", "core_technical", "deep_dive", "cv_based", "follow_up"]
        ]
        if not tech_evals:
            tech_evals = evaluations
        
        # Calculate average scores with proper scale normalization (0-10 -> 0-100)
        relevance_norms = []
        depth_norms = []
        accuracy_norms = []
        for e in tech_evals:
            r = float(getattr(e, "relevance_score", 0.0) or 0.0)
            d = float(getattr(e, "depth_score", 0.0) or 0.0)
            a = float(getattr(e, "accuracy_score", 0.0) or 0.0)
            relevance_norms.append(r * 10.0 if r <= 10.0 else r)
            depth_norms.append(d * 10.0 if d <= 10.0 else d)
            accuracy_norms.append(min(100.0, max(0.0, a)))

        avg_relevance = sum(relevance_norms) / len(relevance_norms)
        avg_depth = sum(depth_norms) / len(depth_norms)
        avg_accuracy = sum(accuracy_norms) / len(accuracy_norms)
        
        # Overall technical score weighted by rubric
        technical_score = round(avg_relevance * 0.30 + avg_depth * 0.40 + avg_accuracy * 0.30, 1)
        
        # Identify strong/weak areas
        strong_areas = []
        weak_areas = []
        
        if avg_relevance >= 70:
            strong_areas.append("Relevant and focused answers")
        elif avg_relevance < 50:
            weak_areas.append("Answers often lacked relevance")
        
        if avg_depth >= 70:
            strong_areas.append("Deep technical knowledge")
        elif avg_depth < 50:
            weak_areas.append("Superficial technical understanding")
        
        if avg_accuracy >= 70:
            strong_areas.append("Accurate technical details")
        elif avg_accuracy < 50:
            weak_areas.append("Factual inaccuracies in responses")
        
        return {
            "score": technical_score,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
            "avg_relevance": avg_relevance,
            "avg_depth": avg_depth,
            "avg_accuracy": avg_accuracy
        }
    
    def _analyze_coding_performance(self, coding_results: List[Dict]) -> Dict:
        """Analyze coding challenge performance with deduplication by challenge."""
        if not coding_results:
            return {"score": 0, "passed": 0, "total": 0, "pass_rate": 0.0}
        
        # Deduplicate per distinct challenge/question_index (keep latest attempt)
        dedup_coding = {}
        for idx, cr in enumerate(coding_results):
            if isinstance(cr, dict):
                key = cr.get("question_index")
                if key is None:
                    key = cr.get("challenge_id", cr.get("title", f"challenge_{idx}"))
                dedup_coding[key] = cr
            else:
                q_idx = getattr(cr, "question_index", None)
                c_id = getattr(cr, "challenge_id", None)
                key = q_idx if q_idx is not None else (c_id or f"challenge_{idx}")
                dedup_coding[key] = cr
        
        unique_results = list(dedup_coding.values())
        total = len(unique_results)
        passed = sum(
            1 for r in unique_results
            if (isinstance(r, dict) and (
                r.get("all_passed", False)
                or float(r.get("overall_coding_score", 0.0)) >= 70.0
                or (r.get("public_tests_total", 0) > 0 and r.get("public_tests_passed", 0) == r.get("public_tests_total"))
                or (r.get("total_count", 0) > 0 and r.get("passed_count", 0) == r.get("total_count"))
            )) or (not isinstance(r, dict) and float(getattr(r, "overall_coding_score", 0.0)) >= 70.0)
        )
        
        scores = []
        for r in unique_results:
            if isinstance(r, dict):
                if "overall_coding_score" in r:
                    scores.append(float(r["overall_coding_score"]))
                elif r.get("all_passed"):
                    scores.append(100.0)
                elif r.get("public_tests_total", 0) > 0:
                    scores.append((r.get("public_tests_passed", 0) / r.get("public_tests_total", 1)) * 100.0)
                elif r.get("total_count", 0) > 0:
                    scores.append((r.get("passed_count", 0) / r.get("total_count", 1)) * 100.0)
                else:
                    scores.append(0.0)
            else:
                scores.append(float(getattr(r, "overall_coding_score", 0.0)))
        
        score = round(sum(scores) / len(scores), 1) if scores else 0.0
        pass_rate = (passed / total) if total > 0 else 0.0
        
        return {
            "score": score,
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate
        }
    
    def _calculate_communication_score(
        self,
        evaluations: List[AnswerEvaluation],
        avg_vocal: Dict
    ) -> float:
        """Calculate overall communication score."""
        if not evaluations:
            return 0.0
        
        # Communication from evaluations
        comm_norms = []
        for e in evaluations:
            c = float(getattr(e, "communication_score", 0.0) or 0.0)
            comm_norms.append(c * 10.0 if c <= 10.0 else c)
        avg_comm = sum(comm_norms) / len(comm_norms)
        
        # Vocal effectiveness (check if real vocal data or empty text mode)
        vocal_effectiveness = avg_vocal.get("communication_effectiveness", 0.0)
        is_text_mode = avg_vocal.get("is_text_mode", False)
        
        if not is_text_mode and vocal_effectiveness > 0:
            communication_score = avg_comm * 0.6 + vocal_effectiveness * 0.4
        else:
            communication_score = avg_comm
        
        return round(communication_score, 1)
    
    def _calculate_behavioral_score(self, avg_behavioral: Dict) -> float:
        """Calculate overall behavioral score."""
        # Weighted combination of behavioral metrics
        if not avg_behavioral.get("is_video_available", False) or avg_behavioral.get("attention_span", 0.0) < 25.0:
            return 0.0

        score = (
            avg_behavioral.get("eye_contact", 0.0) * 0.35 +
            avg_behavioral.get("head_stability", 0.0) * 0.25 +
            avg_behavioral.get("attention_span", 0.0) * 0.25 +
            avg_behavioral.get("engagement", 0.0) * 0.15
        )
        return round(score, 1)
    
    def _determine_hiring_recommendation(
        self,
        overall_score: float,
        technical_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flag_count: int,
        fit_status_val: Optional[str] = None,
    ) -> tuple:
        """Determine hiring recommendation and confidence level aligned with 5D fit status."""
        if fit_status_val:
            val_norm = str(fit_status_val).strip()
            if val_norm in ("Strong Fit", "Strong Hire"):
                return "Strong Fit", "High"
            if val_norm in ("Potential Fit", "Hire"):
                return "Potential Fit", "High" if overall_score >= 80 else "Medium"
            if val_norm in ("Needs Growth", "Maybe"):
                return "Needs Growth", "Medium" if overall_score >= 65 else "Low"
            if val_norm in ("Not a Fit", "No Hire"):
                return "Not a Fit", "High" if overall_score < 50 else "Medium"

        # Fallback calculation if fit_status_val is not provided
        if overall_score >= 85 and technical_score >= 80:
            return "Strong Fit", "High"
        if overall_score >= 70:
            return "Potential Fit", "High" if overall_score >= 80 else "Medium"
        if overall_score >= 55:
            return "Needs Growth", "Medium" if overall_score >= 65 else "Low"
        return "Not a Fit", "High" if overall_score < 50 else "Medium"
    
    def _collect_all_red_flags(
        self,
        evaluations: List[AnswerEvaluation],
        behavioral_metrics: List[Any],
        vocal_metrics: List[Any]
    ) -> List[str]:
        """Collect all red flags from all sources."""
        red_flags = []
        
        # From behavioral analysis
        for bm in behavioral_metrics:
            if hasattr(bm, "red_flags"):
                red_flags.extend(bm.red_flags)
            elif hasattr(bm, "observable_flags"):
                red_flags.extend(bm.observable_flags)
            elif isinstance(bm, dict):
                red_flags.extend(bm.get("red_flags", bm.get("observable_flags", [])))
        
        # From vocal analysis (ignore benign text-mode audio missing flags)
        for vm in vocal_metrics:
            flags = []
            if hasattr(vm, "red_flags"):
                flags = vm.red_flags
            elif hasattr(vm, "acoustic_flags"):
                flags = vm.acoustic_flags
            elif isinstance(vm, dict):
                flags = vm.get("red_flags", vm.get("acoustic_flags", []))
            for f in flags:
                f_str = str(f)
                if "no audio" in f_str.lower() or "empty" in f_str.lower() or "not provided" in f_str.lower():
                    continue
                red_flags.append(f_str)
        
        # From answer evaluations
        for e in evaluations:
            if e.coaching_detected:
                red_flags.append("Coaching detected - external assistance suspected")
            if not e.is_correct and e.accuracy_score < 30:
                red_flags.append(f"Very poor answer to: {e.question_text[:60]}...")
        
        # Deduplicate
        return list(dict.fromkeys(red_flags))

    
    def _identify_strengths(
        self,
        technical_score: float,
        communication_score: float,
        behavioral_score: float,
        coding_score: float,
        avg_behavioral: Dict,
        avg_vocal: Dict
    ) -> List[str]:
        """Identify candidate strengths."""
        strengths = []
        
        if technical_score >= 80:
            strengths.append("Strong technical knowledge and problem-solving skills")
        
        if coding_score >= 80:
            strengths.append("Excellent coding ability with clean, efficient solutions")
        
        if communication_score >= 80:
            strengths.append("Clear and effective communication skills")
        
        is_video_calibrated = avg_behavioral.get("is_video_available", False) and avg_behavioral.get("attention_span", 0.0) >= 25.0

        if is_video_calibrated:
            if behavioral_score >= 80:
                strengths.append("Professional demeanor and strong interview presence")
            if avg_behavioral.get("eye_contact", 0.0) >= 80:
                strengths.append("Maintained excellent eye contact throughout")
            if avg_behavioral.get("attention_span", 0.0) >= 85:
                strengths.append("Highly focused and attentive")
        
        if avg_vocal.get("vocal_confidence", 0) >= 80 or avg_vocal.get("clarity", 0) >= 80:
            strengths.append("Spoke with confidence and clear vocal articulation")
        
        return strengths if strengths else ["Candidate completed the interview session"]
    
    def _identify_improvements(
        self,
        technical_score: float,
        communication_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flags: List[str]
    ) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        if technical_score < 60:
            improvements.append("Strengthen technical fundamentals and domain knowledge")
        
        if coding_score < 60:
            improvements.append("Practice coding problems and algorithmic thinking")
        
        if communication_score < 60:
            improvements.append("Improve verbal communication structure and articulation")
        
        # Check if camera was uncalibrated or missing vs. low calibrated score
        is_camera_uncalibrated = any(
            "camera" in str(rf).lower() or "no face detected" in str(rf).lower() or "uncalibrated" in str(rf).lower()
            for rf in red_flags
        )
        if is_camera_uncalibrated:
            improvements.append("Ensure camera is centered at eye level with good lighting for optimal video tracking")
        elif 0.0 < behavioral_score < 60:
            improvements.append("Work on interview presence, camera eye contact, and composure")
        
        if "eye contact" in " ".join(red_flags).lower() and not is_camera_uncalibrated:
            improvements.append("Maintain better eye orientation with the interviewer during responses")
        
        if "nervous" in " ".join(red_flags).lower() or "fidget" in " ".join(red_flags).lower():
            improvements.append("Practice mock interview scenarios to build confidence and reduce fidgeting")
        
        return improvements if improvements else ["Continue ongoing professional development"]
    
    def _generate_technical_narrative(
        self, 
        technical_analysis: Dict,
        evaluations: List[AnswerEvaluation]
    ) -> str:
        """Generate technical performance narrative."""
        score = technical_analysis["score"]
        strong = technical_analysis["strong_areas"]
        weak = technical_analysis["weak_areas"]
        
        narrative = f"The candidate demonstrated a technical proficiency score of {score:.1f}/100. "
        
        if score >= 75:
            narrative += "Overall technical performance was strong. "
        elif score >= 60:
            narrative += "Technical performance was adequate but showed room for improvement. "
        else:
            narrative += "Technical performance indicated significant knowledge gaps. "
        
        if strong:
            narrative += "Strengths included: " + ", ".join(strong) + ". "
        
        if weak:
            narrative += "Areas needing improvement: " + ", ".join(weak) + "."
        
        return narrative
    
    def _generate_behavioral_narrative(
        self,
        avg_behavioral: Dict,
        behavioral_metrics: List[Any]
    ) -> str:
        """Generate objective, calibrated behavioral analysis narrative."""
        is_calibrated = avg_behavioral.get("is_video_available", False)
        attention = avg_behavioral.get("attention_span", 0.0)
        eye_contact = avg_behavioral.get("eye_contact", 0.0)
        head_stability = avg_behavioral.get("head_stability", 0.0)
        confidence = avg_behavioral.get("confidence_posture", 0.0)
        
        if not is_calibrated or attention < 25.0 or not behavioral_metrics:
            return (
                "Video behavioral tracking was uncalibrated or candidate's face was not detected in camera view during the session. "
                "Non-verbal behavioral indicators were deducted in the overall composite score due to incomplete camera tracking."
            )
        
        narrative_parts = []
        
        if eye_contact >= 75.0:
            narrative_parts.append(f"consistent eye orientation toward the screen ({eye_contact:.1f}%)")
        elif eye_contact >= 50.0:
            narrative_parts.append(f"moderate visual focus with periodic screen divergence ({eye_contact:.1f}%)")
        else:
            narrative_parts.append(f"frequent off-screen gaze shifts ({eye_contact:.1f}%)")
            
        if head_stability >= 75.0:
            narrative_parts.append(f"steady posture and minimal head rotation ({head_stability:.1f}%)")
        else:
            narrative_parts.append(f"active head movement during responses ({head_stability:.1f}%)")
            
        if attention >= 85.0:
            narrative_parts.append(f"and steady camera frame presence ({attention:.1f}%).")
        else:
            narrative_parts.append(f"with occasional movement near camera frame boundaries ({attention:.1f}%).")
            
        return "Behavioral analysis demonstrated " + ", ".join(narrative_parts)
    
    def _generate_communication_narrative(
        self,
        avg_vocal: Dict,
        communication_score: float
    ) -> str:
        """Generate communication analysis narrative."""
        is_text_mode = avg_vocal.get("is_text_mode", False)
        if is_text_mode:
            return (
                f"Written communication was evaluated with a score of {communication_score:.1f}/100. "
                "The candidate articulated responses clearly and professionally with good structure, clarity, and terminology."
            )

        vocal_conf = avg_vocal.get("vocal_confidence", 0)
        clarity = avg_vocal.get("clarity", 0)
        
        narrative = f"Communication effectiveness scored {communication_score:.1f}/100. "
        
        if vocal_conf >= 70:
            narrative += "The candidate spoke with confidence and conviction. "
        else:
            narrative += "Vocal delivery showed signs of hesitation or uncertainty. "
        
        if clarity >= 70:
            narrative += "Speech was clear and easy to understand."
        else:
            narrative += "Speech clarity could be improved."
        
        return narrative
    
    def _generate_coding_narrative(self, coding_analysis: Dict) -> str:
        """Generate coding performance narrative."""
        passed = coding_analysis["passed"]
        total = coding_analysis["total"]
        
        if total == 0:
            return "No coding challenges were completed."
        
        narrative = f"Completed {passed} out of {total} coding challenges successfully. "
        
        if passed == total:
            narrative += "Excellent coding performance with all test cases passed."
        elif passed >= total * 0.67:
            narrative += "Good coding ability demonstrated."
        elif passed >= total * 0.33:
            narrative += "Partial coding success; needs more practice."
        else:
            narrative += "Coding challenges were largely unsuccessful."
        
        return narrative
    
    def _generate_executive_summary(
        self,
        candidate_name: str,
        job_role: str,
        overall_score: float,
        recommendation: str,
        strengths: List[str],
        red_flags: List[str]
    ) -> str:
        """Generate executive summary for quick decision-making."""
        summary = f"{candidate_name} interviewed for {job_role} position. "
        summary += f"Overall score: {overall_score:.1f}/100. "
        summary += f"Recommendation: **{recommendation}**.\n\n"
        
        if strengths:
            summary += "**Key Strengths:** " + strengths[0]
            if len(strengths) > 1:
                summary += "; " + strengths[1]
            summary += ".\n\n"
        
        if red_flags:
            summary += "**Concerns:** " + red_flags[0]
            if len(red_flags) > 1:
                summary += "; " + red_flags[1]
            summary += "."
        
        return summary
    
    def _generate_detailed_recommendation(
        self,
        recommendation: str,
        overall_score: float,
        technical_score: float,
        behavioral_score: float,
        coding_score: float,
        red_flags: List[str]
    ) -> str:
        """Generate detailed hiring recommendation."""
        rec = f"**{recommendation}** - Overall Score: {overall_score:.1f}/100\n\n"
        
        rec += f"- Technical: {technical_score:.1f}/100\n"
        rec += f"- Behavioral: {behavioral_score:.1f}/100\n"
        rec += f"- Coding: {coding_score:.1f}/100\n\n"
        
        if recommendation == "Strong Hire":
            rec += "This candidate exceeded expectations across all dimensions. "
            rec += "Strong technical skills, professional demeanor, and excellent coding ability. "
            rec += "Recommend moving to offer stage immediately."
        
        elif recommendation == "Hire":
            rec += "This candidate meets the requirements for the position. "
            rec += "Solid technical foundation and appropriate skill level. "
            rec += "Recommend proceeding with hiring process."
        
        elif recommendation == "Maybe":
            rec += "This candidate shows potential but has some concerns. "
            if red_flags:
                rec += f"Key concerns include: {', '.join(red_flags[:2])}. "
            rec += "Recommend additional interview or assessment before final decision."
        
        else:  # No Hire
            rec += "This candidate does not meet the requirements for the position. "
            rec += "Significant gaps in technical knowledge, communication, or professionalism. "
            rec += "Recommend not proceeding with this candidate."
        
        return rec
    
    def _generate_next_steps(
        self, 
        recommendation: str,
        improvements: List[str]
    ) -> str:
        """Generate next steps based on recommendation."""
        if recommendation == "Strong Hire":
            return "• Extend offer immediately\n• Schedule onboarding\n• Prepare welcome package"
        
        elif recommendation == "Hire":
            return "• Proceed with reference checks\n• Prepare offer letter\n• Schedule team meet-and-greet"
        
        elif recommendation == "Maybe":
            steps = "• Schedule follow-up technical interview\n"
            steps += "• Consider take-home assignment\n"
            if improvements:
                steps += f"• Assess: {improvements[0]}"
            return steps
        
        else:  # No Hire
            return "• Send rejection email\n• Provide constructive feedback if requested\n• Keep profile for future openings"
