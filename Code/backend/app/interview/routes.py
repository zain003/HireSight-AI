import asyncio
import base64
import io
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_active_user, get_current_admin_user
from app.auth.job_post_model import JobPost
from app.auth.models import Profile, User
from app.interview.application.interview_service import InterviewService
from app.interview.domain.role_taxonomy import SeniorityLevel, StandardRole
from app.interview.models import InterviewSession
from app.interview.schemas import (
    CodingChallengeEvaluation,
    FaceRegisterRequest,
    FaceVerifyRequest,
    FrameAnalyzeRequest,
    FrameAnalyzeResponse,
    InterviewReportResponse,
    InterviewSessionState,
    LiveInterviewStartRequest,
    LiveInterviewStartResponse,
    LiveInterviewQuestion,
    RecruiterReportExportPayload,
    RoleConfigResponse,
    RoleFitRequest,
    RoleFitResponse,
    RunCodeRequest,
    RunCodeResponse,
    RunPublicCodeResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SubmitCodingChallengeRequest,
    TTSRequest,
    TTSResponse,
)
from app.interview.services import FaceService, TTSService
from app.interview.services.pdf_generator_service import pdf_generator_service
from app.interview.services.code_execution import (
    DEFAULT_COMPILE_TIMEOUT_SEC,
    DEFAULT_RUN_TIMEOUT_SEC,
    evaluate_coding_challenge,
    execute_code,
)
from app.interview.services.role_mapping_service import (
    get_supported_roles_config,
    infer_seniority_level,
    map_profile_to_role_fit,
)


router = APIRouter()

interview_service = InterviewService()
face_service = FaceService()
tts_service = TTSService()


@router.get("/config/roles", response_model=RoleConfigResponse)
async def get_interview_roles_config(
    experience_years: Optional[int] = Query(
        None, description="Optional verified candidate experience in years"
    ),
):
    """Retrieve supported standardized roles, competency clusters, and inferred seniority."""
    config = get_supported_roles_config(experience_years=experience_years)
    return RoleConfigResponse(**config)


@router.post("/config/role-fit", response_model=RoleFitResponse)
async def analyze_candidate_role_fit(
    request: RoleFitRequest,
):
    """Analyze candidate skill overlap and coverage against a target role's competency matrix."""
    try:
        role_enum = StandardRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{request.role}'. Supported roles: {[r.value for r in StandardRole]}",
        )
    fit_data = map_profile_to_role_fit(profile_skills=request.skills, role=role_enum)
    return RoleFitResponse(**fit_data)



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


@router.get("/live/{session_id}/state", response_model=InterviewSessionState)
async def get_live_session_state(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve current synchronization and question state for live interview recovery."""
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    state_data = interview_service.get_session_state(session)
    return InterviewSessionState(**state_data)


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

    # Guard against concurrent answer submissions for the same session
    lock_acquired = await interview_service.submission_lock.acquire(session_id)
    if not lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Concurrent answer submission in progress for this session",
        )

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
    finally:
        await interview_service.submission_lock.release(session_id)

    follow_up_question = None
    if result.get("follow_up_question"):
        follow_up_question = LiveInterviewQuestion(**result["follow_up_question"])

    return SubmitAnswerResponse(
        transcript=result["transcript"],
        evaluation=result["evaluation"],
        per_answer_score=result["per_answer_score"],
        follow_up_question=follow_up_question,
        behavioral_metrics=result.get("behavioral_metrics"),
        vocal_metrics=result.get("vocal_metrics"),
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
        recruiter_report=session.recruiter_report
    )


@router.get("/admin/session/{session_id}/recruiter-report")
async def get_recruiter_report_admin(
    session_id: str,
    _admin: User = Depends(get_current_admin_user),
):
    """
    Get comprehensive recruiter report for hiring decision.
    This endpoint is for HR/recruiters to make hiring decisions.
    """
    session = await InterviewSession.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if not session.recruiter_report:
        raise HTTPException(
            status_code=404, 
            detail="Recruiter report not generated yet. Complete the interview first."
        )
    
    return {
        "session_id": session.session_id,
        "candidate_name": session.candidate_name,
        "job_role": session.job_role,
        "status": session.status,
        "recruiter_report": session.recruiter_report,
        "generated_at": session.ended_at.isoformat() if session.ended_at else None
    }


@router.get("/admin/session/{session_id}/export/json", response_model=RecruiterReportExportPayload)
async def export_recruiter_report_json(
    session_id: str,
    _admin: User = Depends(get_current_admin_user),
):
    """
    Export candidate recruiter assessment report as structured JSON for ATS integration.
    Strictly protected for admin roles only.
    """
    session = await InterviewSession.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    user = await User.get(session.user_id) if session.user_id else None
    profile = await Profile.find_one({"user_id": session.user_id}) if session.user_id else None

    return pdf_generator_service.build_export_payload(session, user=user, profile=profile)


@router.get("/admin/session/{session_id}/export/pdf")
async def export_recruiter_report_pdf(
    session_id: str,
    _admin: User = Depends(get_current_admin_user),
):
    """
    Generate and stream publication-grade multi-page PDF recruiter dossier.
    Strictly protected for admin roles only.
    """
    session = await InterviewSession.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    user = await User.get(session.user_id) if session.user_id else None
    profile = await Profile.find_one({"user_id": session.user_id}) if session.user_id else None

    payload = pdf_generator_service.build_export_payload(session, user=user, profile=profile)
    pdf_bytes = await asyncio.to_thread(pdf_generator_service.generate_pdf, payload)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=recruiter_report_{session_id}.pdf",
            "Content-Length": str(len(pdf_bytes)),
        },
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


@router.post("/coding/run-public", response_model=RunPublicCodeResponse)
@router.post("/coding/run", response_model=RunCodeResponse)
async def run_code_sample_tests(
    request: RunCodeRequest,
    _user: User = Depends(get_current_active_user),
):
    """
    Execute candidate code locally against stdin/stdout public tests (subprocess).
    Requires Python / Node / JDK / gcc / g++ on the server PATH as configured.
    """

    def _sync_run() -> RunCodeResponse:
        run_sec = request.timeout_seconds or DEFAULT_RUN_TIMEOUT_SEC
        return execute_code(
            language=request.language,
            source_code=request.source_code,
            test_cases=list(request.test_cases),
            run_timeout_sec=run_sec,
            compile_timeout_sec=min(max(DEFAULT_COMPILE_TIMEOUT_SEC, run_sec), 60.0),
        )

    return await asyncio.to_thread(_sync_run)


@router.post("/live/{session_id}/submit-coding-challenge", response_model=CodingChallengeEvaluation)
async def submit_live_coding_challenge(
    session_id: str,
    request: SubmitCodingChallengeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Evaluate candidate coding solution against both public and secret hidden test suites.
    Persists evaluation in session document with zero leakage of hidden inputs/outputs.
    """
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    evaluation = await asyncio.to_thread(
        evaluate_coding_challenge,
        challenge_id=request.challenge_id,
        language=request.language,
        source_code=request.source_code,
    )

    # Store coding result in session
    if not hasattr(session, 'coding_results') or session.coding_results is None:
        session.coding_results = []

    eval_dict = evaluation.model_dump()
    eval_dict["timestamp"] = datetime.utcnow().isoformat()
    eval_dict["question_index"] = request.question_index
    session.coding_results.append(eval_dict)

    await session.save()
    return evaluation


@router.post("/live/{session_id}/submit-coding-result")
async def submit_coding_result(
    session_id: str,
    request: RunCodeResponse,
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit coding challenge results for tracking in final report.
    Called after candidate runs code tests (legacy compatible).
    """
    session = await InterviewSession.find_one(
        {"session_id": session_id, "user_id": str(current_user.id)}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # Store coding result
    if not hasattr(session, 'coding_results') or session.coding_results is None:
        session.coding_results = []
    
    session.coding_results.append({
        "compile_success": request.compile_success,
        "all_passed": request.all_passed,
        "passed_count": sum(1 for r in request.results if r.passed),
        "total_count": len(request.results),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    await session.save()
    
    return {"status": "success", "message": "Coding result recorded"}
