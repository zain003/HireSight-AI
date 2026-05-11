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


class AnalysisService:
    """
    Aggregates per-answer evaluations into overall interview scores
    and generates the final hiring report.
    """

    WEIGHT_TECHNICAL = 0.35
    WEIGHT_COMMUNICATION = 0.25
    WEIGHT_BEHAVIORAL = 0.25
    WEIGHT_VIDEO = 0.15

    THRESHOLD_STRONG = 85.0
    THRESHOLD_RECOMMEND = 70.0
    THRESHOLD_BORDERLINE = 55.0

    def calculate_scores(
        self,
        evaluations: List[AnswerEvaluation],
        frame_snapshots: List[FrameAnalysisResult],
    ) -> Dict[str, float]:
        if not evaluations:
            return {
                "technical_score": 0.0,
                "communication_score": 0.0,
                "behavioral_score": 0.0,
                "video_integrity_score": 100.0,
                "overall_score": 0.0,
            }

        def avg(items: List[AnswerEvaluation], key: str) -> float:
            if not items:
                return 0.0
            return round(sum(getattr(item, key) for item in items) / len(items) * 10, 1)

        tech_evals = [
            e
            for e in evaluations
            if e.question_type
            in (QuestionType.TECHNICAL, QuestionType.CV_BASED, QuestionType.CODING)
        ]
        beh_evals = [
            e
            for e in evaluations
            if e.question_type in (QuestionType.BEHAVIORAL, QuestionType.FOLLOW_UP)
        ]

        technical_score = avg(tech_evals, "depth_score") if tech_evals else avg(evaluations, "depth_score")
        communication_score = avg(evaluations, "communication_score")
        behavioral_score = avg(beh_evals, "relevance_score") if beh_evals else avg(evaluations, "relevance_score")

        if frame_snapshots:
            flag_penalty = sum(len(s.suspicious_flags) for s in frame_snapshots) * 10
            gaze_penalty = (sum(s.looking_away_ratio for s in frame_snapshots) / len(frame_snapshots)) * 50
            video_score = round(max(0.0, 100.0 - flag_penalty - gaze_penalty), 1)
        else:
            video_score = 100.0

        overall = round(
            technical_score * self.WEIGHT_TECHNICAL
            + communication_score * self.WEIGHT_COMMUNICATION
            + behavioral_score * self.WEIGHT_BEHAVIORAL
            + video_score * self.WEIGHT_VIDEO,
            1,
        )

        return {
            "technical_score": technical_score,
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
