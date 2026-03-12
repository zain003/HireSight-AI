"""
Service logic for job post creation and retrieval.
"""
from app.auth.job_post_model import JobPost
from app.auth.job_post_schemas import JobPostCreate
from typing import List

class JobPostService:
    """Service for job post operations"""
    @staticmethod
    async def create_job_post(job_post_data: JobPostCreate):
        job_post = JobPost(
            title=job_post_data.title,
            description=job_post_data.description,
            required_skills=job_post_data.required_skills,
            domain=job_post_data.domain,
            created_by="admin"
        )
        await job_post.insert()
        return job_post

    @staticmethod
    async def get_all_job_posts() -> List[JobPost]:
        return await JobPost.find({}).to_list()
