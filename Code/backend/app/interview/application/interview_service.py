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
    LIVE_INTERVIEW_TOTAL_QUESTIONS,
    AnalysisService,
    FaceService,
    STTService,
    generate_followup_question,
    generate_question_plan,
    generate_report_summary,
    generate_rubric_backed_plan,
    evaluate_answer_interview,
)
from app.interview.services.role_mapping_service import infer_seniority_level
from app.interview.services.behavioral_analysis import BehavioralAnalysisService
from app.interview.services.vocal_analysis import VocalAnalysisService
from app.interview.services.recruiter_report import RecruiterReportGenerator


import asyncio

class SessionSubmissionLock:
    """In-memory concurrency lock preventing duplicate simultaneous answer evaluations for the same session."""

    def __init__(self):
        self._active: set[str] = set()
        self._lock = asyncio.Lock()

    async def acquire(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._active:
                return False
            self._active.add(session_id)
            return True

    async def release(self, session_id: str) -> None:
        async with self._lock:
            self._active.discard(session_id)


class InterviewService:
    MAX_FOLLOWUPS_PER_STAGE = 3
    MAX_FOLLOWUPS_PER_INTERVIEW = 9

    def __init__(self):
        self.stt_service = STTService()
        self.face_service = FaceService()
        self.analysis_service = AnalysisService()
        # Enhanced analysis services
        self.behavioral_service = BehavioralAnalysisService()
        self.vocal_service = VocalAnalysisService()
        self.report_generator = RecruiterReportGenerator()
        self.submission_lock = SessionSubmissionLock()
        
        # Track behavioral and vocal metrics per question
        self.behavioral_metrics_per_question = []
        self.vocal_metrics_per_question = []

    async def start_interview(
        self,
        candidate_id: str,
        candidate_name: str,
        job_role: str,
        job_description: str,
        candidate_skills: List[str],
        total_questions: int,
        required_job_skills: Optional[List[str]] = None,
        candidate_projects: Optional[List[Dict]] = None,
        candidate_job_titles: Optional[List[str]] = None,
        candidate_certifications: Optional[List[str]] = None,
        candidate_companies: Optional[List[str]] = None,
        experience_years: Optional[int] = None,
        job_post_id: Optional[str] = None,
    ) -> InterviewSession:
        target_seniority = infer_seniority_level(experience_years)
        rubric_plan = await generate_rubric_backed_plan(
            job_role=job_role,
            seniority=target_seniority,
            candidate_skills=candidate_skills,
            candidate_projects=candidate_projects or [],
            total_questions=total_questions or 6,
            job_description=job_description,
            required_job_skills=required_job_skills or [],
        )

        questions = []
        for idx, q in enumerate(rubric_plan):
            q_type = q.stage.value if q.stage else "technical"
            rubric_dict = q.rubric.model_dump() if hasattr(q.rubric, "model_dump") else q.rubric.dict()
            entry = {
                "question_id": q.question_id or f"q_{idx + 1}",
                "question_index": idx,
                "question_text": q.question_text,
                "question_type": q_type,
                "stage": q.stage.value if q.stage else q_type,
                "competency_area": q.competency_area,
                "difficulty": q.difficulty.value if q.difficulty else target_seniority.value,
                "rubric": rubric_dict,
            }
            if q.coding_challenge_id:
                entry["coding_challenge_id"] = q.coding_challenge_id
            if q.coding_challenge:
                entry["coding_challenge"] = q.coding_challenge
            questions.append(entry)

        session_id = f"int_{uuid.uuid4().hex[:12]}"
        session = InterviewSession(
            session_id=session_id,
            user_id=candidate_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_post_id=job_post_id,
            job_role=job_role,
            job_description=job_description,
            required_job_skills=required_job_skills or [],
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

        if question_index < len(session.evaluations):
            raise ValueError(f"Question {question_index} has already been answered")

        if question_index != len(session.evaluations):
            raise ValueError(f"Question index {question_index} is out of order. Expected question {len(session.evaluations)}.")

        question = session.questions[question_index]
        question_text = question.get("question_text") or ""
        question_type = question.get("question_type") or QuestionType.TECHNICAL.value

        # 1. Transcribe audio
        transcript = await self.stt_service.transcribe(
            audio_base64=audio_base64,
            transcript_text=transcript_text,
            language=language,
            audio_format=audio_format,
        )

        # 2. Enhanced behavioral analysis (MediaPipe)
        behavioral_metrics = self.behavioral_service.analyze_frames(frame_base64_list)
        
        # 3. Enhanced vocal analysis (OpenSMILE + Vosk)
        vocal_metrics = await self.vocal_service.analyze_audio(
            audio_base64=audio_base64,
            transcript_text=transcript,
            audio_format=audio_format
        )
        
        # Store metrics for final report
        if not hasattr(session, 'behavioral_metrics'):
            session.behavioral_metrics = []
        if not hasattr(session, 'vocal_metrics'):
            session.vocal_metrics = []
            
        session.behavioral_metrics.append(behavioral_metrics)
        session.vocal_metrics.append(vocal_metrics)

        # 4. Legacy frame analysis (for compatibility)
        frame_analysis = await self.face_service.analyze(frame_base64_list)
        
        # 5. Answer evaluation (with enhanced metrics)
        evaluation = await evaluate_answer_interview(
            question_text=question_text,
            question_type=question_type,
            candidate_transcript=transcript,
            job_role=session.job_role,
            frame_analysis=frame_analysis,
        )

        evaluation.question_index = question_index
        evaluation.question_text = question_text
        try:
            evaluation.question_type = QuestionType(question_type)
        except ValueError:
            evaluation.question_type = QuestionType.TECHNICAL

        session.evaluations.append(evaluation)
        session.frame_snapshots.append(frame_analysis)
        session.current_question_index = question_index + 1
        session.updated_at = datetime.utcnow()

        follow_up_question = None
        current_q_type = (question.get("question_type") or "").strip().lower()
        is_current_follow_up = current_q_type == QuestionType.FOLLOW_UP.value
        is_coding = current_q_type == QuestionType.CODING.value
        existing_followups = [
            q for q in session.questions if (q.get("question_type") or "").strip().lower() == QuestionType.FOLLOW_UP.value
        ]
        current_stage = (question.get("stage") or question_type or "").strip().lower()
        stage_followups = [
            q
            for q in existing_followups
            if (q.get("stage") or "").strip().lower() == current_stage
        ]
        can_add_followup = (
            evaluation.follow_up_triggered
            and not is_current_follow_up  # never ask follow-up on a follow-up
            and not is_coding  # coding rounds use the judge later, not verbal follow-ups
            and len(existing_followups) < self.MAX_FOLLOWUPS_PER_INTERVIEW
            and len(stage_followups) < self.MAX_FOLLOWUPS_PER_STAGE
        )

        if can_add_followup:
            follow_up = await generate_followup_question(
                job_role=session.job_role,
                original_question=question_text,
                candidate_answer=transcript,
                asked_questions=[q.get("question_text", "") for q in session.questions],
                stage=question.get("stage") or question_type,
                conversation_history=[
                    {"role": "user", "content": question_text},
                    {"role": "assistant", "content": transcript},
                ],
            )
            if follow_up:
                parent_id = question.get("question_id", f"q_{question_index + 1}")
                follow_up_question = {
                    "question_id": f"fu_{parent_id}_{uuid.uuid4().hex[:6]}",
                    "question_index": question_index + 1,
                    "question_text": follow_up.get("question_text", ""),
                    "question_type": QuestionType.FOLLOW_UP.value,
                    "stage": follow_up.get("stage") or question.get("stage") or question_type,
                    "difficulty": follow_up.get("difficulty") or None,
                    "parent_question_id": question.get("question_id"),
                }
                session.questions.insert(question_index + 1, follow_up_question)
                for idx, q in enumerate(session.questions):
                    q["question_index"] = idx

        # Transition status if all questions completed
        if session.current_question_index >= len(session.questions):
            session.status = InterviewStatus.COMPLETED.value
            if not session.ended_at:
                session.ended_at = datetime.utcnow()

        await session.save()

        per_answer_score = self.analysis_service.score_single_answer(evaluation)
        
        return {
            "transcript": transcript,
            "evaluation": evaluation,
            "per_answer_score": per_answer_score,
            "follow_up_question": follow_up_question,
            "behavioral_metrics": {
                "eye_contact": behavioral_metrics.eye_contact_score,
                "confidence_posture": behavioral_metrics.confidence_posture_score,
                "attention_span": behavioral_metrics.attention_span_score,
                "fidgeting": behavioral_metrics.fidgeting_score
            },
            "vocal_metrics": {
                "vocal_confidence": vocal_metrics.vocal_confidence_score,
                "speech_clarity": vocal_metrics.speech_clarity_score,
                "communication_effectiveness": vocal_metrics.communication_effectiveness
            }
        }

    async def end_interview(self, session: InterviewSession) -> Dict:
        # Determine role fit data from profile skills
        from app.interview.domain.role_taxonomy import StandardRole
        from app.interview.services.role_mapping_service import map_profile_to_role_fit

        role_enum = None
        try:
            if session.job_role:
                role_enum = StandardRole(session.job_role)
        except Exception:
            role_enum = None

        role_fit_data = {}
        if role_enum:
            role_fit_data = map_profile_to_role_fit(
                profile_skills=session.candidate_skills or [],
                role=role_enum,
            )
        elif session.job_role:
            role_fit_data = {
                "role": session.job_role,
                "overall_fit_score": 75.0 if session.candidate_skills else 50.0,
                "matched_skills": session.candidate_skills or [],
            }

        # Calculate scores
        behavioral_metrics = getattr(session, "behavioral_metrics", [])
        vocal_metrics = getattr(session, "vocal_metrics", [])
        coding_results = getattr(session, "coding_results", [])

        scores = self.analysis_service.calculate_scores(
            evaluations=session.evaluations,
            frame_snapshots=session.frame_snapshots,
            coding_results=coding_results,
            role_fit_data=role_fit_data,
        )

        # Generate traditional summary
        summary = await generate_report_summary(
            candidate_name=session.candidate_name,
            job_role=session.job_role,
            evaluations=session.evaluations,
            overall_score=scores["overall_score"],
            video_integrity_score=scores["video_integrity_score"],
        )

        # Build traditional report
        report = self.analysis_service.build_report(session, summary)

        # Generate comprehensive 5-dimensional recruiter report
        recruiter_report = self.report_generator.generate_report(
            candidate_name=session.candidate_name,
            job_role=session.job_role or "Not specified",
            session_start=session.started_at,
            session_end=datetime.utcnow(),
            evaluations=session.evaluations,
            behavioral_metrics=behavioral_metrics,
            vocal_metrics=vocal_metrics,
            coding_results=coding_results,
            aggregate_scores=scores,
            role_fit_data=role_fit_data,
        )

        # Update scores with 5-dimensional explainable metrics
        if recruiter_report.five_dimension_scores:
            scores.update({
                "technical_knowledge_score": recruiter_report.technical_score,
                "coding_ability_score": recruiter_report.coding_score,
                "role_fit_score": recruiter_report.role_fit_score,
                "communication_score": recruiter_report.communication_score,
                "behavioral_indicators_score": recruiter_report.behavioral_score,
                "overall_composite_score": recruiter_report.overall_score,
                "fit_status": recruiter_report.fit_status,
            })

        # Store comprehensive report
        session.recruiter_report = recruiter_report.__dict__
        session.report = report
        session.status = InterviewStatus.COMPLETED.value
        session.ended_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.aggregate_scores = scores
        await session.save()

        return {
            "scores": scores,
            "report": report,
            "recruiter_report": recruiter_report.__dict__,
        }


    def get_session_state(self, session: InterviewSession) -> Dict[str, Any]:
        """Extract deterministic session state for synchronization & recovery."""
        curr_idx = session.current_question_index
        total_q = len(session.questions)
        curr_q = None
        if 0 <= curr_idx < total_q:
            q = session.questions[curr_idx]
            curr_q = {
                "question_id": q.get("question_id"),
                "question_index": q.get("question_index", curr_idx),
                "question_text": q.get("question_text"),
                "question_type": q.get("question_type"),
                "stage": q.get("stage"),
                "difficulty": q.get("difficulty"),
                "parent_question_id": q.get("parent_question_id"),
                "coding_challenge": q.get("coding_challenge"),
            }

        status = session.status
        if curr_idx >= total_q and total_q > 0 and status != InterviewStatus.COMPLETED.value:
            status = InterviewStatus.COMPLETED.value

        return {
            "session_id": session.session_id,
            "current_question_index": curr_idx,
            "total_questions": total_q,
            "completed_evaluations_count": len(session.evaluations),
            "current_question": curr_q,
            "status": status,
        }
