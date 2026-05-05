"""Main interview orchestration service."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.interview.domain.interview_models import (
    AnswerEvaluation,
    InterviewStatus,
    QuestionType,
)
from app.interview.models import InterviewSession
from app.interview.services import (
    AnalysisService,
    FaceService,
    STTService,
    generate_followup_question,
    generate_question_plan,
    generate_report_summary,
    evaluate_answer_interview,
)


class InterviewService:
    def __init__(self):
        self.stt_service = STTService()
        self.face_service = FaceService()
        self.analysis_service = AnalysisService()

    async def start_interview(
        self,
        candidate_id: str,
        candidate_name: str,
        job_role: str,
        job_description: str,
        candidate_skills: List[str],
        total_questions: int,
        job_post_id: Optional[str] = None,
    ) -> InterviewSession:
        plan = await generate_question_plan(
            job_role=job_role,
            job_description=job_description,
            candidate_skills=candidate_skills,
            total_questions=total_questions,
        )

        questions = []
        for idx, q in enumerate(plan):
            q_text = (q.get("question_text") or "").strip()
            q_type = (q.get("question_type") or "technical").strip().lower()
            if q_type == "icebreaker":
                question_type = QuestionType.ICEBREAKER
            elif q_type == "behavioral":
                question_type = QuestionType.BEHAVIORAL
            elif q_type == "follow_up":
                question_type = QuestionType.FOLLOW_UP
            elif q_type == "closing":
                question_type = QuestionType.CLOSING
            elif q_type == "situational":
                question_type = QuestionType.SITUATIONAL
            else:
                question_type = QuestionType.TECHNICAL

            questions.append(
                {
                    "question_id": f"q_{idx + 1}",
                    "question_index": idx,
                    "question_text": q_text,
                    "question_type": question_type.value,
                }
            )

        session_id = f"int_{uuid.uuid4().hex[:12]}"
        session = InterviewSession(
            session_id=session_id,
            user_id=candidate_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_post_id=job_post_id,
            job_role=job_role,
            job_description=job_description,
            candidate_skills=candidate_skills,
            questions=questions,
            evaluations=[],
            frame_snapshots=[],
            status=InterviewStatus.IN_PROGRESS.value,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await session.insert()
        return session

    async def process_answer(
        self,
        session: InterviewSession,
        question_index: int,
        audio_base64: Optional[str],
        transcript_text: Optional[str],
        frame_base64_list: List[str],
        audio_format: str = "webm",
        language: str = "en",
    ) -> Dict:
        if question_index < 0 or question_index >= len(session.questions):
            raise ValueError("Invalid question index")

        question = session.questions[question_index]
        question_text = question.get("question_text") or ""
        question_type = question.get("question_type") or QuestionType.TECHNICAL.value

        transcript = await self.stt_service.transcribe(
            audio_base64=audio_base64,
            transcript_text=transcript_text,
            language=language,
            audio_format=audio_format,
        )

        frame_analysis = await self.face_service.analyze(frame_base64_list)
        evaluation = await evaluate_answer_interview(
            question_text=question_text,
            question_type=question_type,
            candidate_transcript=transcript,
            job_role=session.job_role,
            frame_analysis=frame_analysis,
        )

        evaluation.question_index = question_index
        evaluation.question_text = question_text
        evaluation.question_type = QuestionType(question_type)

        session.evaluations.append(evaluation)
        session.frame_snapshots.append(frame_analysis)
        session.current_question_index = max(session.current_question_index, question_index + 1)
        session.updated_at = datetime.utcnow()

        follow_up_question = None
        if evaluation.follow_up_triggered:
            follow_up = await generate_followup_question(
                job_role=session.job_role,
                original_question=question_text,
                candidate_answer=transcript,
                conversation_history=[
                    {"role": "user", "content": question_text},
                    {"role": "assistant", "content": transcript},
                ],
            )
            if follow_up:
                follow_up_question = {
                    "question_id": f"q_{len(session.questions) + 1}",
                    "question_index": question_index + 1,
                    "question_text": follow_up.get("question_text", ""),
                    "question_type": QuestionType.FOLLOW_UP.value,
                }
                session.questions.insert(question_index + 1, follow_up_question)
                for idx, q in enumerate(session.questions):
                    q["question_index"] = idx

        await session.save()

        per_answer_score = self.analysis_service.score_single_answer(evaluation)
        return {
            "transcript": transcript,
            "evaluation": evaluation,
            "per_answer_score": per_answer_score,
            "follow_up_question": follow_up_question,
        }

    async def end_interview(self, session: InterviewSession) -> Dict:
        scores = self.analysis_service.calculate_scores(
            session.evaluations, session.frame_snapshots
        )
        summary = await generate_report_summary(
            candidate_name=session.candidate_name,
            job_role=session.job_role,
            evaluations=session.evaluations,
            overall_score=scores["overall_score"],
            video_integrity_score=scores["video_integrity_score"],
        )

        report = self.analysis_service.build_report(session, summary)
        session.report = report
        session.status = InterviewStatus.COMPLETED.value
        session.ended_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.aggregate_scores = scores
        await session.save()

        return {"scores": scores, "report": report}
