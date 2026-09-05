"""Answer scoring and interview report builder."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    FrameAnalysisResult,
    InterviewReport,
    InterviewSession,
    InterviewStatus,
    QuestionType,
)


from app.interview.domain.scoring_models import (
    CandidateFitStatus,
    FiveDimensionScores,
    ScoringWeights,
)


class AnalysisService:
    """
    Aggregates per-answer evaluations into overall interview scores
    and generates the final hiring report with 5-dimensional explainability.
    """

    WEIGHT_TECHNICAL = ScoringWeights.TECHNICAL_KNOWLEDGE
    WEIGHT_CODING = ScoringWeights.CODING_ABILITY
    WEIGHT_ROLE_FIT = ScoringWeights.ROLE_FIT
    WEIGHT_COMMUNICATION = ScoringWeights.COMMUNICATION
    WEIGHT_BEHAVIORAL = ScoringWeights.BEHAVIORAL_INDICATORS

    THRESHOLD_STRONG = 85.0
    THRESHOLD_RECOMMEND = 70.0
    THRESHOLD_BORDERLINE = 55.0

    def calculate_scores(
        self,
        evaluations: List[AnswerEvaluation],
        frame_snapshots: List[FrameAnalysisResult],
        coding_results: Optional[List[Dict]] = None,
        role_fit_data: Optional[Dict] = None,
    ) -> Dict[str, float]:
        if not evaluations:
            return {
                "technical_score": 0.0,
                "coding_score": 0.0,
                "role_fit_score": 0.0,
                "communication_score": 0.0,
                "behavioral_score": 0.0,
                "video_integrity_score": 100.0,
                "overall_score": 0.0,
            }

        def avg(items: List[AnswerEvaluation], key: str) -> float:
            if not items:
                return 0.0
            return round(sum(getattr(item, key, 0.0) or 0.0 for item in items) / len(items) * 10, 1)

        tech_evals = [
            e
            for e in evaluations
            if e.question_type
            in (
                QuestionType.TECHNICAL,
                QuestionType.CV_BASED,
                getattr(QuestionType, "CORE_TECHNICAL", None),
                getattr(QuestionType, "DEEP_DIVE", None),
            )
        ]
        target_tech = tech_evals if tech_evals else evaluations

        # Technical rubric-weighted calculation
        q_tech_scores = []
        for e in target_tech:
            rel = min(100.0, max(0.0, float(e.relevance_score or 0.0) * 10.0 if float(e.relevance_score or 0.0) <= 10.0 else float(e.relevance_score or 0.0)))
            dep = min(100.0, max(0.0, float(e.depth_score or 0.0) * 10.0 if float(e.depth_score or 0.0) <= 10.0 else float(e.depth_score or 0.0)))
            acc = min(100.0, max(0.0, float(e.accuracy_score or 0.0)))
            q_tech_scores.append(rel * 0.30 + dep * 0.40 + acc * 0.30)
        technical_score = round(sum(q_tech_scores) / len(q_tech_scores), 1) if q_tech_scores else 0.0

        # Coding calculation
        if coding_results:
            c_scores = [float(cr.get("overall_coding_score", 100.0 if cr.get("all_passed") else 0.0)) for cr in coding_results]
            coding_score = round(sum(c_scores) / len(c_scores), 1) if c_scores else 0.0
        else:
            coding_score = 0.0

        # Role fit calculation
        role_fit_score = float((role_fit_data or {}).get("overall_fit_score", 0.0))

        # Communication calculation
        comm_scores = [min(100.0, max(0.0, float(e.communication_score or 0.0) * 10.0 if float(e.communication_score or 0.0) <= 10.0 else float(e.communication_score or 0.0))) for e in evaluations]
        communication_score = round(sum(comm_scores) / len(comm_scores), 1) if comm_scores else 0.0

        # Behavioral & Video calculation
        if frame_snapshots:
            flag_penalty = sum(len(s.suspicious_flags) for s in frame_snapshots) * 10
            gaze_penalty = (sum(s.looking_away_ratio for s in frame_snapshots) / len(frame_snapshots)) * 50
            video_score = round(max(0.0, 100.0 - flag_penalty - gaze_penalty), 1)
            behavioral_score = video_score
        else:
            video_score = 100.0
            behavioral_score = 0.0 if not evaluations else 70.0

        overall = round(
            technical_score * self.WEIGHT_TECHNICAL
            + coding_score * self.WEIGHT_CODING
            + role_fit_score * self.WEIGHT_ROLE_FIT
            + communication_score * self.WEIGHT_COMMUNICATION
            + behavioral_score * self.WEIGHT_BEHAVIORAL,
            1,
        )

        return {
            "technical_score": technical_score,
            "coding_score": coding_score,
            "role_fit_score": role_fit_score,
            "communication_score": communication_score,
            "behavioral_score": behavioral_score,
            "video_integrity_score": video_score,
            "overall_score": overall,
        }


    def get_recommendation(self, overall_score: float) -> str:
        if overall_score >= self.THRESHOLD_STRONG:
            return "Strongly Recommend"
        if overall_score >= self.THRESHOLD_RECOMMEND:
            return "Recommend"
        if overall_score >= self.THRESHOLD_BORDERLINE:
            return "Borderline"
        return "Not Recommend"

    def collect_red_flags(
        self,
        evaluations: List[AnswerEvaluation],
        frame_snapshots: List[FrameAnalysisResult],
    ) -> List[str]:
        flags = set()
        for snap in frame_snapshots:
            for flag in snap.suspicious_flags:
                flags.add(flag)

        avg_score = (
            sum((e.relevance_score + e.depth_score) / 2 for e in evaluations) / max(len(evaluations), 1)
        )
        if avg_score < 3.0:
            flags.add("Consistently low answer quality across all questions")

        return list(flags)

    def score_single_answer(self, evaluation: AnswerEvaluation) -> float:
        return round(
            (
                evaluation.relevance_score * 0.4
                + evaluation.depth_score * 0.35
                + evaluation.communication_score * 0.25
            )
            * 10,
            1,
        )

    def build_report(self, session: InterviewSession, summary: Dict) -> InterviewReport:
        scores = self.calculate_scores(session.evaluations, session.frame_snapshots)
        flags = self.collect_red_flags(session.evaluations, session.frame_snapshots)

        return InterviewReport(
            session_id=session.session_id,
            candidate_id=session.candidate_id,
            candidate_name=session.candidate_name,
            job_role=session.job_role,
            interview_date=session.started_at or datetime.utcnow(),
            status=InterviewStatus.COMPLETED,
            total_questions_asked=len(session.evaluations),
            overall_score=scores["overall_score"],
            technical_score=scores["technical_score"],
            communication_score=scores["communication_score"],
            behavioral_score=scores["behavioral_score"],
            video_integrity_score=scores["video_integrity_score"],
            evaluations=session.evaluations,
            behavioral_summary=summary.get("behavioral_summary", ""),
            strengths=summary.get("strengths", []),
            weaknesses=summary.get("weaknesses", []),
            recommendation=summary.get(
                "recommendation", self.get_recommendation(scores["overall_score"])
            ),
            red_flags=summary.get("red_flags", flags),
            hiring_decision_notes=summary.get("hiring_decision_notes", ""),
        )
