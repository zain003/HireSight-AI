"""
Admin Candidates Service — Roster Query, Multi-Criteria Filtering, Pagination & Report Builder.
Implements Issue 02 requirements for HireSIGHT.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.auth.job_post_model import JobPost
from app.auth.models import Profile, User
from app.auth.schemas import CandidateRosterItem, CandidateRosterResponse
from app.interview.models import InterviewSession


def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # Strip timezone z/offset if present for simple comparison
        cleaned = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except Exception:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return None


def _extract_overall_score(session: Optional[InterviewSession]) -> Optional[float]:
    if not session:
        return None
    if session.aggregate_scores and session.aggregate_scores.get("overall_score") is not None:
        try:
            return float(session.aggregate_scores["overall_score"])
        except (ValueError, TypeError):
            pass
    if session.recruiter_report:
        rep = session.recruiter_report
        if rep.get("overall_score") is not None:
            try:
                return float(rep["overall_score"])
            except (ValueError, TypeError):
                pass
        five_dim = rep.get("five_dimension_scores")
        if isinstance(five_dim, dict) and five_dim.get("overall_composite_score") is not None:
            try:
                return float(five_dim["overall_composite_score"])
            except (ValueError, TypeError):
                pass
    return None


def _extract_recommendation(session: Optional[InterviewSession]) -> Optional[str]:
    if not session or not session.recruiter_report:
        return None
    rep = session.recruiter_report
    rec = rep.get("fit_status") or rep.get("hiring_recommendation")
    if rec:
        return str(rec).strip()
    five_dim = rep.get("five_dimension_scores")
    if isinstance(five_dim, dict) and five_dim.get("fit_status"):
        return str(five_dim["fit_status"]).strip()
    return None


async def get_candidate_roster(
    search: Optional[str] = None,
    statuses: Optional[List[str]] = None,
    role: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    recommendations: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "date_desc",
    page: int = 1,
    page_size: int = 10,
    job_post_id: Optional[str] = None,
) -> CandidateRosterResponse:
    """
    Fetch, aggregate, multi-filter, sort, and paginate candidate records across User, Profile, and InterviewSession.
    """
    # 1. Fetch raw data from collections
    users = await User.find({}).to_list()
    profiles = await Profile.find({}).to_list()
    job_posts = await JobPost.find({}).to_list()
    sessions = await InterviewSession.find({}).to_list()

    profiles_by_user = {p.user_id: p for p in profiles if p.user_id}
    jobs_by_id = {str(j.id): j for j in job_posts}
    
    # Map sessions by user_id and also retain individual session items
    sessions_by_user: Dict[str, List[InterviewSession]] = {}
    for s in sessions:
        uid = getattr(s, "user_id", None) or getattr(s, "candidate_id", None)
        if uid:
            sessions_by_user.setdefault(str(uid), []).append(s)

    # 2. Build candidate roster items
    raw_items: List[CandidateRosterItem] = []
    seen_user_ids = set()

    # Case A: Build from interview sessions first
    for s in sessions:
        uid = str(getattr(s, "user_id", "") or getattr(s, "candidate_id", "") or "")
        u = next((usr for usr in users if str(usr.id) == uid), None)
        p = profiles_by_user.get(uid)
        jp = jobs_by_id.get(str(s.job_post_id)) if s.job_post_id else None

        c_name = s.candidate_name or (u.full_name if u else None) or (u.username if u else None) or "Candidate"
        email = u.email if u else None
        job_role_val = (
            (jp.title if jp else None)
            or s.job_role
            or (p.job_role if p else None)
            or "Software Engineer"
        )
        job_title_val = jp.title if jp else (s.job_role or "Standard Assessment")

        score = _extract_overall_score(s)
        rec = _extract_recommendation(s)
        five_dim = None
        if s.recruiter_report and isinstance(s.recruiter_report.get("five_dimension_scores"), dict):
            five_dim = s.recruiter_report.get("five_dimension_scores")

        dur_mins = None
        if s.recruiter_report and s.recruiter_report.get("session_duration_minutes") is not None:
            try:
                dur_mins = float(s.recruiter_report["session_duration_minutes"])
            except (ValueError, TypeError):
                pass
        elif s.started_at and s.ended_at:
            dur_mins = round((s.ended_at - s.started_at).total_seconds() / 60.0, 1)

        st = (s.status or "in_progress").lower()
        if st not in ("completed", "in_progress", "not_started", "abandoned"):
            st = "in_progress"

        item = CandidateRosterItem(
            user_id=uid or str(s.id),
            candidate_name=c_name,
            email=email,
            username=u.username if u else None,
            job_role=job_role_val,
            job_post_id=str(s.job_post_id) if s.job_post_id else None,
            job_post_title=job_title_val,
            session_id=s.session_id,
            status=st,
            started_at=s.started_at,
            ended_at=s.ended_at,
            overall_score=score,
            five_dimension_scores=five_dim,
            hiring_recommendation=rec,
            fit_status=rec,
            duration_minutes=dur_mins,
            has_report=bool(s.recruiter_report),
            experience_years=p.experience_years if p else None,
            resume_score=getattr(p, "resume_score", None) if p else None,
            skills=list(dict.fromkeys([*(p.skills or [] if p else []), *(s.candidate_skills or [])])),
        )
        raw_items.append(item)
        if uid:
            seen_user_ids.add(uid)

    # Case B: Include registered users who have not started any interview session (only if no specific job_post_id is requested)
    if not job_post_id:
        for u in users:
            uid = str(u.id)
            if uid not in seen_user_ids:
                p = profiles_by_user.get(uid)
                item = CandidateRosterItem(
                    user_id=uid,
                    candidate_name=u.full_name or u.username or "Candidate",
                    email=u.email,
                    username=u.username,
                    job_role=p.job_role if p else "Software Engineer",
                    job_post_id=None,
                    job_post_title="General Candidate",
                    session_id=None,
                    status="not_started",
                    started_at=None,
                    ended_at=None,
                    overall_score=None,
                    five_dimension_scores=None,
                    hiring_recommendation=None,
                    fit_status=None,
                    duration_minutes=None,
                    has_report=False,
                    experience_years=p.experience_years if p else None,
                    resume_score=getattr(p, "resume_score", None) if p else None,
                    skills=p.skills if p else [],
                )
                raw_items.append(item)

    # 3. Calculate Global Facets before filtering
    available_roles_set = set()
    available_recs_set = set()
    status_counts = {"total": len(raw_items), "completed": 0, "in_progress": 0, "not_started": 0}

    for item in raw_items:
        if item.job_role:
            available_roles_set.add(item.job_role)
        if item.job_post_title:
            available_roles_set.add(item.job_post_title)
        if item.hiring_recommendation:
            available_recs_set.add(item.hiring_recommendation)
        st = item.status.lower()
        if st == "completed":
            status_counts["completed"] += 1
        elif st in ("in_progress", "abandoned"):
            status_counts["in_progress"] += 1
        else:
            status_counts["not_started"] += 1

    # 4. Multi-Criteria Filtering (AND logic)
    filtered = raw_items

    # Filter: job_post_id
    if job_post_id:
        filtered = [
            i for i in filtered
            if i.job_post_id == str(job_post_id) or str(job_post_id).strip() in (i.job_post_id or "")
        ]

    # Filter: Free text Search (Candidate Name, Email, Username, Role)
    if search and search.strip():
        q = search.strip().lower()
        filtered = [
            i for i in filtered
            if q in (i.candidate_name or "").lower()
            or q in (i.email or "").lower()
            or q in (i.username or "").lower()
            or q in (i.job_role or "").lower()
            or any(q in s.lower() for s in i.skills)
        ]

    # Filter: Status (multi-select)
    if statuses:
        status_filter_set = {s.lower().strip() for s in statuses if s.strip()}
        if status_filter_set and "all" not in status_filter_set:
            filtered = [i for i in filtered if i.status.lower() in status_filter_set]

    # Filter: Role
    if role and role.strip() and role.strip().lower() != "all":
        r_target = role.strip().lower()
        filtered = [
            i for i in filtered
            if r_target in (i.job_role or "").lower() or r_target in (i.job_post_title or "").lower()
        ]

    # Filter: Score range
    if min_score is not None:
        filtered = [i for i in filtered if i.overall_score is not None and i.overall_score >= float(min_score)]
    if max_score is not None:
        filtered = [i for i in filtered if i.overall_score is not None and i.overall_score <= float(max_score)]

    # Filter: Recommendation (multi-select or single)
    if recommendations:
        rec_set = {r.lower().strip() for r in recommendations if r.strip()}
        if rec_set and "all" not in rec_set:
            filtered = [
                i for i in filtered
                if i.hiring_recommendation and i.hiring_recommendation.lower().strip() in rec_set
            ]

    # Filter: Date range
    parsed_start = _parse_iso_date(start_date)
    parsed_end = _parse_iso_date(end_date)
    if parsed_start:
        filtered = [
            i for i in filtered
            if (i.ended_at or i.started_at) and (i.ended_at or i.started_at) >= parsed_start
        ]
    if parsed_end:
        filtered = [
            i for i in filtered
            if (i.ended_at or i.started_at) and (i.ended_at or i.started_at) <= parsed_end
        ]

    # 5. Sorting
    sort_key = (sort_by or "date_desc").lower()
    if sort_key == "score_desc":
        filtered.sort(
            key=lambda x: (
                x.overall_score is not None,
                x.overall_score or 0.0,
                x.ended_at or x.started_at or datetime.min,
            ),
            reverse=True,
        )
    elif sort_key == "score_asc":
        filtered.sort(
            key=lambda x: (
                x.overall_score is None,
                x.overall_score if x.overall_score is not None else 999.0,
                x.ended_at or x.started_at or datetime.min,
            )
        )
    elif sort_key == "date_asc":
        filtered.sort(
            key=lambda x: (
                x.ended_at or x.started_at or datetime.max
            )
        )
    elif sort_key == "name_asc":
        filtered.sort(key=lambda x: (x.candidate_name or "").lower())
    elif sort_key == "name_desc":
        filtered.sort(key=lambda x: (x.candidate_name or "").lower(), reverse=True)
    elif sort_key == "status":
        status_priority = {"completed": 1, "in_progress": 2, "not_started": 3, "abandoned": 4}
        filtered.sort(key=lambda x: status_priority.get(x.status.lower(), 5))
    else:  # default: date_desc
        filtered.sort(
            key=lambda x: (
                x.ended_at or x.started_at or datetime.min
            ),
            reverse=True,
        )

    # 6. Pagination
    total_count = len(filtered)
    page_val = max(1, page)
    page_size_val = max(1, min(100, page_size))
    total_pages = max(1, math.ceil(total_count / page_size_val))

    start_idx = (page_val - 1) * page_size_val
    end_idx = start_idx + page_size_val
    paginated_items = filtered[start_idx:end_idx]

    return CandidateRosterResponse(
        items=paginated_items,
        total_count=total_count,
        page=page_val,
        page_size=page_size_val,
        total_pages=total_pages,
        available_roles=sorted(list(available_roles_set)),
        available_recommendations=sorted(list(available_recs_set)),
        status_counts=status_counts,
    )


async def get_candidate_session_report(session_id: str) -> Dict[str, Any]:
    """
    Retrieve full candidate report dossier directly by session ID.
    Handles both job-linked and standalone sessions gracefully.
    """
    session = await InterviewSession.find_one({"session_id": session_id})
    if not session:
        raise ValueError("Interview session not found")

    user = await User.get(session.user_id) if session.user_id else None
    profile = await Profile.find_one({"user_id": session.user_id}) if session.user_id else None
    job_post = await JobPost.get(session.job_post_id) if session.job_post_id else None

    c_name = session.candidate_name or (user.full_name if user else None) or "Candidate"
    email = user.email if user else None
    job_role = (
        (job_post.title if job_post else None)
        or session.job_role
        or (profile.job_role if profile else None)
        or "Software Engineer"
    )

    return {
        "session_id": session.session_id,
        "job_post_id": session.job_post_id,
        "job_title": job_post.title if job_post else job_role,
        "job_role": job_role,
        "candidate_info": {
            "name": c_name,
            "email": email,
            "username": user.username if user else None,
            "experience_years": profile.experience_years if profile else None,
            "skills": profile.skills if profile else (session.candidate_skills or []),
            "resume_score": getattr(profile, "resume_score", None) if profile else None,
        },
        "interview_info": {
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_minutes": (
                session.recruiter_report.get("session_duration_minutes")
                if session.recruiter_report
                else (
                    round((session.ended_at - session.started_at).total_seconds() / 60.0, 1)
                    if session.started_at and session.ended_at
                    else None
                )
            ),
            "status": session.status,
            "total_questions": len(session.questions),
            "evaluations_count": len(session.evaluations),
        },
        "recruiter_report": session.recruiter_report,
        "aggregate_scores": session.aggregate_scores or {},
        "questions_count": len(session.questions),
        "evaluations_count": len(session.evaluations),
        "has_report": bool(session.recruiter_report),
    }
