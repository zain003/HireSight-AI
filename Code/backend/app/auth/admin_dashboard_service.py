"""Aggregates real metrics for the admin dashboard (MongoDB / Beanie)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.auth.job_post_model import JobPost
from app.auth.models import User, Profile
from app.interview.models import InterviewSession


async def count_interview_candidates_for_job(job_post_id: str) -> int:
    """Distinct users who started an interview session linked to this job post."""
    if not job_post_id:
        return 0
    sessions = await InterviewSession.find(
        InterviewSession.job_post_id == job_post_id
    ).to_list()
    if not sessions:
        # Some sessions may store id with alternate formatting
        alt = str(job_post_id).strip()
        sessions = await InterviewSession.find({"job_post_id": alt}).to_list()
    return len({s.user_id for s in sessions if getattr(s, "user_id", None)})


async def get_dashboard_stats() -> Dict[str, Any]:
    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=7)

    all_jobs = await JobPost.find({}).to_list()
    total_job_posts = len(all_jobs)

    def _st(p: JobPost) -> str:
        s = (getattr(p, "status", None) or "active").lower()
        return s if s in ("active", "draft", "closed") else "active"

    active_job_posts = sum(1 for p in all_jobs if _st(p) == "active")
    draft_job_posts = sum(1 for p in all_jobs if _st(p) == "draft")
    closed_job_posts = sum(1 for p in all_jobs if _st(p) == "closed")

    job_posts_this_week = sum(
        1 for p in all_jobs if (p.created_at or datetime.min) >= week_start
    )

    total_registered_users = await User.count()
    users_this_week = await User.find(User.created_at >= week_start).count()

    _profiles = await Profile.find({}).to_list()
    profiles_with_resume = sum(
        1 for p in _profiles if (getattr(p, "resume_path", None) or "").strip()
    )

    interviews_today = await InterviewSession.find(
        InterviewSession.started_at >= day_start
    ).count()
    interviews_this_week = await InterviewSession.find(
        InterviewSession.started_at >= week_start
    ).count()

    skill_set = set()
    for p in all_jobs:
        for s in p.required_skills or []:
            if s:
                skill_set.add(s.strip())

    return {
        "total_job_posts": total_job_posts,
        "active_job_posts": active_job_posts,
        "draft_job_posts": draft_job_posts,
        "closed_job_posts": closed_job_posts,
        "job_posts_created_this_week": job_posts_this_week,
        "total_registered_users": total_registered_users,
        "users_registered_this_week": users_this_week,
        "profiles_with_resume": profiles_with_resume,
        "interviews_today": interviews_today,
        "interviews_this_week": interviews_this_week,
        "unique_skills_listed": len(skill_set),
    }


async def list_users_for_admin() -> List[Dict[str, Any]]:
    users = await User.find({}).to_list()
    users.sort(key=lambda u: u.created_at or datetime.min, reverse=True)
    profiles = await Profile.find({}).to_list()
    by_uid = {p.user_id: p for p in profiles if p.user_id}
    out: List[Dict[str, Any]] = []
    for u in users:
        uid = str(u.id)
        p = by_uid.get(uid)
        out.append(
            {
                "id": uid,
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() + "Z" if u.created_at else None,
                "has_resume": bool(p and (p.resume_path or "").strip()),
                "job_role": p.job_role if p else None,
                "skills_count": len(p.skills or []) if p else 0,
            }
        )
    return out


def job_post_to_response_dict(job_post: JobPost, applicant_count: int) -> Dict[str, Any]:
    st = getattr(job_post, "status", None) or "active"
    if st not in ("active", "draft", "closed"):
        st = "active"
    return {
        "id": str(job_post.id),
        "title": job_post.title,
        "description": job_post.description,
        "required_skills": job_post.required_skills or [],
        "domain": job_post.domain,
        "status": st,
        "applicant_count": applicant_count,
        "created_by": job_post.created_by,
        "created_at": job_post.created_at,
        "updated_at": job_post.updated_at,
    }
