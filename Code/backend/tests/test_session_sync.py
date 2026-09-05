"""
Unit and integration tests for FEAT-003-BE: Session State Synchronization & Dynamic Follow-up Engine.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.interview.application.interview_service import (
    InterviewService,
    SessionSubmissionLock,
)
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    InterviewStatus,
    QuestionStage,
    QuestionType,
    SeniorityLevel,
)
from app.interview.models import InterviewSession
from app.interview.schemas import InterviewSessionState


def _make_dummy_session(total_questions: int = 4) -> InterviewSession:
    questions = []
    stages = [
        QuestionStage.ICEBREAKER,
        QuestionStage.CORE_TECHNICAL,
        QuestionStage.DEEP_DIVE,
        QuestionStage.CLOSING,
    ]
    for i in range(total_questions):
        st = stages[i % len(stages)].value
        questions.append({
            "question_id": f"q_{i + 1}",
            "question_index": i,
            "question_text": f"Question {i + 1} text",
            "question_type": st,
            "stage": st,
            "competency_area": "Engineering",
            "difficulty": SeniorityLevel.MID.value,
            "rubric": {
                "reference_answer": f"Reference answer for question {i + 1}",
                "key_concepts_expected": ["Concept A", "Concept B"],
                "depth_criteria": {"basic": "b", "intermediate": "i", "advanced": "a"},
                "scoring_guide": {"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            },
        })

    session = InterviewSession.model_construct(
        session_id="test_sess_001",
        user_id="user_123",
        candidate_id="cand_123",
        candidate_name="Jane Doe",
        job_role="backend_engineer",
        questions=questions,
        current_question_index=0,
        evaluations=[],
        frame_snapshots=[],
        status=InterviewStatus.IN_PROGRESS.value,
    )
    return session


@pytest.mark.anyio
async def test_session_state_returns_current_question():
    """get_session_state returns question matching current_question_index accurately."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=4)
    session.current_question_index = 2

    state = service.get_session_state(session)
    assert state["session_id"] == "test_sess_001"
    assert state["current_question_index"] == 2
    assert state["total_questions"] == 4
    assert state["completed_evaluations_count"] == 0
    assert state["current_question"]["question_id"] == "q_3"
    assert state["current_question"]["question_index"] == 2
    assert state["status"] == InterviewStatus.IN_PROGRESS.value

    # Validate against Pydantic schema
    validated = InterviewSessionState(**state)
    assert validated.current_question["question_id"] == "q_3"


@pytest.mark.anyio
async def test_follow_up_insertion_renumbers_subsequent_questions():
    """When a dynamic follow-up is inserted at index 1, original question 2 becomes question 3."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=4)

    mock_eval = AnswerEvaluation(
        question_index=0,
        question_text=session.questions[0]["question_text"],
        follow_up_triggered=True,
    )

    with patch.object(service.stt_service, "transcribe", new_callable=AsyncMock, return_value="Test answer"), \
         patch.object(service.face_service, "analyze", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("app.interview.application.interview_service.evaluate_answer_interview", new_callable=AsyncMock, return_value=mock_eval), \
         patch("app.interview.application.interview_service.generate_followup_question", new_callable=AsyncMock, return_value={
             "question_text": "Can you elaborate on concurrency safety?",
             "stage": "core_technical",
             "difficulty": "mid",
         }), \
         patch("app.interview.models.InterviewSession.save", new_callable=AsyncMock):

        result = await service.process_answer(
            session=session,
            question_index=0,
            audio_base64=None,
            transcript_text="Test answer",
            frame_base64_list=[],
        )

        assert result["follow_up_question"] is not None
        assert len(session.questions) == 5
        # Verify strict sequential indices
        for idx, q in enumerate(session.questions):
            assert q["question_index"] == idx

        # Verify follow-up was inserted at index 1
        assert session.questions[1]["question_type"] == QuestionType.FOLLOW_UP.value
        assert session.questions[1]["question_text"] == "Can you elaborate on concurrency safety?"
        assert session.questions[1]["parent_question_id"] == "q_1"

        # Verify original q_2 was pushed to index 2
        assert session.questions[2]["question_id"] == "q_2"
        assert session.questions[2]["question_index"] == 2


@pytest.mark.anyio
async def test_follow_up_parent_question_id_linking():
    """Dynamic follow-up questions include explicit parent-child linking to the original question."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=3)

    mock_eval = AnswerEvaluation(
        question_index=0,
        question_text=session.questions[0]["question_text"],
        follow_up_triggered=True,
    )

    with patch.object(service.stt_service, "transcribe", new_callable=AsyncMock, return_value="My answer"), \
         patch.object(service.face_service, "analyze", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("app.interview.application.interview_service.evaluate_answer_interview", new_callable=AsyncMock, return_value=mock_eval), \
         patch("app.interview.application.interview_service.generate_followup_question", new_callable=AsyncMock, return_value={
             "question_text": "Why choose that approach?",
             "stage": "icebreaker",
         }), \
         patch("app.interview.models.InterviewSession.save", new_callable=AsyncMock):

        await service.process_answer(
            session=session,
            question_index=0,
            audio_base64=None,
            transcript_text="My answer",
            frame_base64_list=[],
        )

        follow_up = session.questions[1]
        assert follow_up["parent_question_id"] == "q_1"
        assert "fu_q_1" in follow_up["question_id"]


@pytest.mark.anyio
async def test_max_follow_up_limits_enforced():
    """Enforces max 3 follow-ups per stage and max 9 follow-ups per interview."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=10)

    # 1. Test stage limit (MAX_FOLLOWUPS_PER_STAGE = 3)
    # Simulate existing 3 follow-ups in 'core_technical'
    for k in range(3):
        session.questions.append({
            "question_id": f"fu_test_{k}",
            "question_index": len(session.questions),
            "question_text": f"Follow-up {k}",
            "question_type": QuestionType.FOLLOW_UP.value,
            "stage": "core_technical",
        })

    session.questions[1]["stage"] = "core_technical"
    # Answering question 0 first so question 1 is the next expected question
    session.evaluations.append(AnswerEvaluation(question_index=0, candidate_transcript="Ans 0"))
    mock_eval = AnswerEvaluation(question_index=1, follow_up_triggered=True)

    with patch.object(service.stt_service, "transcribe", new_callable=AsyncMock, return_value="Ans"), \
         patch.object(service.face_service, "analyze", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("app.interview.application.interview_service.evaluate_answer_interview", new_callable=AsyncMock, return_value=mock_eval), \
         patch("app.interview.application.interview_service.generate_followup_question", new_callable=AsyncMock) as mock_gen, \
         patch("app.interview.models.InterviewSession.save", new_callable=AsyncMock):

        res = await service.process_answer(
            session=session,
            question_index=1,
            audio_base64=None,
            transcript_text="Ans",
            frame_base64_list=[],
        )

        # Stage limit reached -> no follow-up should be generated or added
        assert res["follow_up_question"] is None
        mock_gen.assert_not_called()

    # 2. Test interview limit (MAX_FOLLOWUPS_PER_INTERVIEW = 9)
    session_all_fu = _make_dummy_session(total_questions=15)
    for k in range(9):
        session_all_fu.questions.append({
            "question_id": f"fu_global_{k}",
            "question_index": len(session_all_fu.questions),
            "question_text": f"Follow-up {k}",
            "question_type": QuestionType.FOLLOW_UP.value,
            "stage": f"stage_{k}",
        })

    with patch.object(service.stt_service, "transcribe", new_callable=AsyncMock, return_value="Ans"), \
         patch.object(service.face_service, "analyze", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("app.interview.application.interview_service.evaluate_answer_interview", new_callable=AsyncMock, return_value=mock_eval), \
         patch("app.interview.application.interview_service.generate_followup_question", new_callable=AsyncMock) as mock_gen_global, \
         patch("app.interview.models.InterviewSession.save", new_callable=AsyncMock):

        res_global = await service.process_answer(
            session=session_all_fu,
            question_index=0,
            audio_base64=None,
            transcript_text="Ans",
            frame_base64_list=[],
        )
        assert res_global["follow_up_question"] is None
        mock_gen_global.assert_not_called()


@pytest.mark.anyio
async def test_concurrent_answer_submissions_lock():
    """SessionSubmissionLock grants access to single request and rejects concurrent requests."""
    lock = SessionSubmissionLock()
    sess_id = "concurrent_test_session"

    # First request acquires lock
    acq1 = await lock.acquire(sess_id)
    assert acq1 is True

    # Second simultaneous request fails to acquire lock
    acq2 = await lock.acquire(sess_id)
    assert acq2 is False

    # Once first request releases, subsequent acquire succeeds
    await lock.release(sess_id)
    acq3 = await lock.acquire(sess_id)
    assert acq3 is True
    await lock.release(sess_id)


@pytest.mark.anyio
async def test_already_answered_question_rejected():
    """Candidate submitting answer for already answered question raises ValueError."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=3)

    # Question 0 already evaluated
    session.evaluations.append(AnswerEvaluation(question_index=0, candidate_transcript="Ans 1"))
    session.current_question_index = 1

    with pytest.raises(ValueError, match="already been answered"):
        await service.process_answer(
            session=session,
            question_index=0,
            audio_base64=None,
            transcript_text="Trying to re-answer question 0",
            frame_base64_list=[],
        )


@pytest.mark.anyio
async def test_out_of_order_question_rejected():
    """Candidate submitting answer out of sequential order raises ValueError."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=4)
    # Question 0 not yet answered, submitting for question 2
    with pytest.raises(ValueError, match="out of order"):
        await service.process_answer(
            session=session,
            question_index=2,
            audio_base64=None,
            transcript_text="Skipping questions",
            frame_base64_list=[],
        )


@pytest.mark.anyio
async def test_session_status_transitions_to_completed_on_final_question():
    """Session status transitions to completed upon evaluating the final question."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=2)

    mock_eval = AnswerEvaluation(question_index=1, follow_up_triggered=False)

    # First answer question 0
    session.evaluations.append(AnswerEvaluation(question_index=0, follow_up_triggered=False))
    session.current_question_index = 1

    with patch.object(service.stt_service, "transcribe", new_callable=AsyncMock, return_value="Final answer"), \
         patch.object(service.face_service, "analyze", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("app.interview.application.interview_service.evaluate_answer_interview", new_callable=AsyncMock, return_value=mock_eval), \
         patch("app.interview.models.InterviewSession.save", new_callable=AsyncMock):

        await service.process_answer(
            session=session,
            question_index=1,
            audio_base64=None,
            transcript_text="Final answer",
            frame_base64_list=[],
        )

        assert session.current_question_index == 2
        assert session.status == InterviewStatus.COMPLETED.value
        assert session.ended_at is not None

        state = service.get_session_state(session)
        assert state["status"] == InterviewStatus.COMPLETED.value
        assert state["current_question"] is None
        assert state["completed_evaluations_count"] == 2


@pytest.mark.anyio
async def test_session_state_recovery_after_reload():
    """State endpoint accurately reflects session recovery after mid-interview page reload."""
    service = InterviewService()
    session = _make_dummy_session(total_questions=5)

    # Simulate completed 2 questions out of 5
    session.evaluations.append(AnswerEvaluation(question_index=0, candidate_transcript="Answer 1"))
    session.evaluations.append(AnswerEvaluation(question_index=1, candidate_transcript="Answer 2"))
    session.current_question_index = 2

    state = service.get_session_state(session)
    assert state["session_id"] == "test_sess_001"
    assert state["current_question_index"] == 2
    assert state["total_questions"] == 5
    assert state["completed_evaluations_count"] == 2
    assert state["current_question"]["question_index"] == 2
    assert state["current_question"]["question_id"] == "q_3"
    assert state["status"] == InterviewStatus.IN_PROGRESS.value
