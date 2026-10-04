import asyncio
import os
import sys

backend_dir = r"f:\FYP Project\Code\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.interview.services.llm_service import generate_rubric_backed_plan, _generate_fallback_rubric_plan
from app.interview.domain.interview_models import QuestionStage

async def main():
    print("Testing DevOps Job with candidate having MERN profile...")
    job_role = "DevOps"
    required_job_skills = ["Git", "Github", "Vercel", "Render", "AWS", "Docker", "Kubernetes"]
    candidate_skills = ["React", "Express.js", "Node.js", "MongoDB", "MERN", "JavaScript"]
    candidate_projects = [{"name": "E-Commerce App", "description": "Built using MERN stack with JWT and Mongo"}]
    
    # 1. Test Fallback Plan
    print("\n--- 1. Testing Fallback Plan ---")
    fallback_plan = _generate_fallback_rubric_plan(
        job_role=job_role,
        seniority="mid",
        candidate_skills=candidate_skills,
        candidate_projects=candidate_projects,
        total_questions=20,
        required_job_skills=required_job_skills,
    )
    print(f"Fallback Plan Total Questions: {len(fallback_plan)}")
    mern_in_fallback = []
    coding_chals = []
    for i, q in enumerate(fallback_plan):
        safe_text = q.question_text[:100].encode("ascii", "replace").decode()
        print(f"Q{i+1} [{q.stage.value}] ({q.competency_area}): {safe_text}...")
        if "mern" in q.question_text.lower() or "express" in q.question_text.lower():
            mern_in_fallback.append((i+1, q.stage.value, q.question_text))
        if q.stage == QuestionStage.CODING:
            ch_title = q.coding_challenge.get("title") if q.coding_challenge else "None"
            coding_chals.append(ch_title)
    
    print(f"MERN/Express questions in DevOps fallback plan: {len(mern_in_fallback)}")
    assert len(mern_in_fallback) == 0, f"Found MERN questions in DevOps fallback: {mern_in_fallback}"
    print(f"Coding challenges in fallback: {coding_chals}")
    assert len(coding_chals) == 2, f"Expected 2 coding challenges, got {len(coding_chals)}"
    assert coding_chals[0] != coding_chals[1], "Coding challenges must be distinct!"
    assert "Sliding Window API Rate Limiter" not in coding_chals[0], "First challenge should not be rate limiter"

    # 2. Test Full generate_rubric_backed_plan (async)
    print("\n--- 2. Testing generate_rubric_backed_plan ---")
    plan = await generate_rubric_backed_plan(
        job_role=job_role,
        seniority="mid",
        candidate_skills=candidate_skills,
        candidate_projects=candidate_projects,
        total_questions=20,
        job_description="We are seeking a DevOps Engineer to manage our AWS infrastructure, Docker/Kubernetes clusters, and CI/CD pipelines.",
        required_job_skills=required_job_skills,
    )
    print(f"\nGenerated Plan Total Questions: {len(plan)}")
    mern_in_plan = []
    plan_coding = []
    stage_counts = {}
    for i, q in enumerate(plan):
        st = q.stage.value if q.stage else "unknown"
        stage_counts[st] = stage_counts.get(st, 0) + 1
        safe_text = q.question_text[:100].encode("ascii", "replace").decode()
        print(f"Q{i+1} [{st}] ({q.competency_area}): {safe_text}...")
        if q.stage in {QuestionStage.CORE_TECHNICAL, QuestionStage.DEEP_DIVE}:
            if "mern" in q.question_text.lower() or "express" in q.question_text.lower():
                mern_in_plan.append((i+1, st, q.question_text))
        if q.stage == QuestionStage.CODING:
            ch_title = q.coding_challenge.get("title") if q.coding_challenge else "None"
            plan_coding.append(ch_title)
            print(f"   -> Coding challenge title: {ch_title}")
    
    print(f"\nStage counts: {stage_counts}")
    print(f"MERN/Express questions in technical/system design: {len(mern_in_plan)}")
    print(f"Coding challenges generated: {plan_coding}")
    assert len(mern_in_plan) == 0, f"Found MERN in technical/system design: {mern_in_plan}"
    assert len(plan) == 20, f"Expected 20 questions, got {len(plan)}"
    assert stage_counts.get("icebreaker", 0) == 4, f"Expected 4 icebreaker questions, got {stage_counts.get('icebreaker')}"
    assert stage_counts.get("core_technical", 0) == 6, f"Expected 6 core technical questions, got {stage_counts.get('core_technical')}"
    assert stage_counts.get("deep_dive", 0) == 3, f"Expected 3 deep dive questions, got {stage_counts.get('deep_dive')}"
    assert stage_counts.get("coding", 0) == 2, f"Expected 2 coding questions, got {stage_counts.get('coding')}"
    assert stage_counts.get("behavioral", 0) == 3, f"Expected 3 behavioral questions, got {stage_counts.get('behavioral')}"
    assert stage_counts.get("closing", 0) == 2, f"Expected 2 closing questions, got {stage_counts.get('closing')}"

    print("\n========================================================")
    print("ALL DEVOPS INTERVIEW PLAN VALIDATION TESTS PASSED!")
    print("========================================================")

if __name__ == "__main__":
    asyncio.run(main())
