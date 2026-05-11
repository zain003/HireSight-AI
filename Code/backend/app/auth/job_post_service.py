"""
Service logic for job post creation and retrieval.
"""
from datetime import datetime
from typing import List, Optional

from beanie import PydanticObjectId

from app.auth.job_post_model import JobPost
from app.auth.job_post_schemas import JobPostCreate, JobPostUpdate


class JobPostService:
    """Service for job post operations"""
    @staticmethod
    async def create_job_post(job_post_data: JobPostCreate):
        job_post = JobPost(
            title=job_post_data.title,
            description=job_post_data.description,
            required_skills=job_post_data.required_skills,
            domain=job_post_data.domain,
            status=job_post_data.status,
            created_by="admin",
        )
        await job_post.insert()
        return job_post

    @staticmethod
    async def get_all_job_posts() -> List[JobPost]:
        posts = await JobPost.find({}).to_list()
        posts.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
        return posts

    @staticmethod
    async def get_job_post_by_id(job_post_id: str) -> Optional[JobPost]:
        try:
            oid = PydanticObjectId(job_post_id)
        except Exception:
            return None
        return await JobPost.get(oid)

    @staticmethod
    async def update_job_post(job_post_id: str, data: JobPostUpdate) -> Optional[JobPost]:
        job_post = await JobPostService.get_job_post_by_id(job_post_id)
        if not job_post:
            return None
        if data.title is not None:
            job_post.title = data.title
        if data.description is not None:
            job_post.description = data.description
        if data.required_skills is not None:
            job_post.required_skills = data.required_skills
        if data.domain is not None:
            job_post.domain = data.domain
        if data.status is not None:
            job_post.status = data.status
        job_post.updated_at = datetime.utcnow()
        await job_post.save()
        return job_post

    @staticmethod
    async def delete_job_post(job_post_id: str) -> bool:
        job_post = await JobPostService.get_job_post_by_id(job_post_id)
        if not job_post:
            return False
        await job_post.delete()
        return True
