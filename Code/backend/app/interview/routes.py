"""Live interview module routes."""

import base64
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_active_user
from app.auth.job_post_model import JobPost
from app.auth.models import Profile, User
from app.interview.application.interview_service import InterviewService
from app.interview.models import InterviewSession
from app.interview.schemas import (
    FaceRegisterRequest,
    FaceVerifyRequest,
    FrameAnalyzeRequest,
    FrameAnalyzeResponse,
    InterviewReportResponse,
    LiveInterviewStartRequest,
    LiveInterviewStartResponse,
    LiveInterviewQuestion,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    TTSRequest,
    TTSResponse,
)
from app.interview.services import FaceService, TTSService


router = APIRouter()

interview_service = InterviewService()
face_service = FaceService()
tts_service = TTSService()


@router.post("/live/start", response_model=LiveInterviewStartResponse)
async def start_live_interview(
    request: LiveInterviewStartRequest,
    current_user: User = Depends(get_current_active_user),
):
    profile = await Profile.find_one({"user_id": str(current_user.id)})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Upload resume first.")

    job_role = request.job_role or profile.job_role or "Software Engineer"
    job_description = request.job_description or ""
    candidate_skills = request.candidate_skills or list(
        dict.fromkeys(
            [
                *(profile.skills or []),
                *(profile.experienced_skills or []),
                *(profile.known_skills or []),
            ]
        )
    )

    job_post_id = request.job_post_id
    required_job_skills = []
    if job_post_id:
        job_post = await JobPost.get(job_post_id)
        if job_post:
            job_role = job_post.title or job_role
            job_description = job_post.description or job_description
            if job_post.required_skills:
                required_job_skills = list(job_post.required_skills)
                candidate_skills = list(dict.fromkeys([*candidate_skills, *job_post.required_skills]))

    candidate_name = request.candidate_name or current_user.full_name or current_user.username

    session = await interview_service.start_interview(
        candidate_id=str(current_user.id),
        candidate_name=candidate_name,
        job_role=job_role,
        job_description=job_description,
        candidate_skills=candidate_skills,
        required_job_skills=required_job_skills,
        total_questions=request.num_questions,
        candidate_projects=profile.projects or [],
        candidate_job_titles=profile.job_titles or [],
        candidate_certifications=profile.certifications or [],
        candidate_companies=profile.companies or [],
        experience_years=profile.experience_years,
        job_post_id=str(job_post_id) if job_post_id else None,
    )

    return LiveInterviewStartResponse(
        session_id=session.session_id,
        questions=[LiveInterviewQuestion(**q) for q in session.questions],
    )


@router.post("/live/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_live_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    try:
        result = await interview_service.process_answer(
            session=session,
            question_index=request.question_index,
            audio_base64=request.audio_base64,
            transcript_text=request.transcript_text,
            frame_base64_list=request.frame_base64_list,
            audio_format=request.audio_format,
            language=request.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    follow_up_question = None
    if result.get("follow_up_question"):
        follow_up_question = LiveInterviewQuestion(**result["follow_up_question"])

    return SubmitAnswerResponse(
        transcript=result["transcript"],
        evaluation=result["evaluation"],
        per_answer_score=result["per_answer_score"],
        follow_up_question=follow_up_question,
    )


@router.post("/live/{session_id}/end", response_model=InterviewReportResponse)
async def end_live_interview(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    result = await interview_service.end_interview(session)
    return InterviewReportResponse(
        session_id=session.session_id,
        status=session.status,
        aggregate_scores=result["scores"],
        report=result["report"],
    )


@router.get("/live/{session_id}/report", response_model=InterviewReportResponse)
async def get_live_report(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if not session.report:
        raise HTTPException(status_code=404, detail="Interview report not generated yet")

    return InterviewReportResponse(
        session_id=session.session_id,
        status=session.status,
        aggregate_scores=session.aggregate_scores or {},
        report=session.report,
    )


@router.post("/live/{session_id}/register-face")
async def register_face(
    session_id: str,
    request: FaceRegisterRequest,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    image_bytes = base64.b64decode(request.image_base64)
    ok = face_service.register_face(image_bytes, session.candidate_id)
    return {"registered": ok}


@router.post("/live/{session_id}/verify-face")
async def verify_face(
    session_id: str,
    request: FaceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    image_bytes = base64.b64decode(request.image_base64)
    return face_service.verify_face(image_bytes, session.candidate_id)


@router.post("/live/{session_id}/analyze-frame", response_model=FrameAnalyzeResponse)
async def analyze_frame(
    session_id: str,
    request: FrameAnalyzeRequest,
    current_user: User = Depends(get_current_active_user),
):
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    analysis = await face_service.analyze(request.frame_base64_list)
    return FrameAnalyzeResponse(analysis=analysis)


@router.post("/live/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    audio_bytes = await tts_service.synthesize(
        text=request.text,
        voice=request.voice or "en-US-JennyNeural",
        rate=request.rate or "+0%",
        pitch=request.pitch or "+0%",
    )
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii") if audio_bytes else ""
    return TTSResponse(audio_base64=audio_b64, format="mp3")
