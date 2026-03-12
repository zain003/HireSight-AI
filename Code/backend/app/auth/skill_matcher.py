"""
Skill matching logic for job posts and resumes.
"""
from app.auth.job_post_model import JobPost
from app.resume.service import ResumeService
from typing import List, Dict

class SkillMatcher:
    """Skill matching between job post and resume/profile"""
    @staticmethod
    def match_skills(job_post_skills: List[str], candidate_skills: List[str]) -> Dict:
        matched = [skill for skill in job_post_skills if skill.lower() in [s.lower() for s in candidate_skills]]
        missing = [skill for skill in job_post_skills if skill.lower() not in [s.lower() for s in candidate_skills]]
        extra = [skill for skill in candidate_skills if skill.lower() not in [s.lower() for s in job_post_skills]]
        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "extra_skills": extra
        }
