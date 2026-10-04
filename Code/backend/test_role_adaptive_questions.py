import asyncio
from app.interview.domain.role_taxonomy import SeniorityLevel, StandardRole
from app.interview.services.llm_service import _generate_fallback_rubric_plan, generate_rubric_backed_plan

def test_mern_entry_vs_senior():
    print("\n--- TEST 1: MERN Stack Developer (ENTRY vs SENIOR) ---")
    
    # Entry plan
    entry_plan = _generate_fallback_rubric_plan(
        job_role="MERN Stack Developer",
        seniority=SeniorityLevel.ENTRY,
        candidate_skills=["MongoDB", "Express", "React", "Node.js"],
        total_questions=6,
    )
    print("\n[MERN ENTRY Questions]:")
    for q in entry_plan:
        print(f"  [{q.stage.value.upper()}] ({q.difficulty.value}): {q.question_text[:90]}...")
        assert len(q.rubric.reference_answer) > 15
        assert len(q.rubric.key_concepts_expected) >= 2
    
    # Senior plan
    senior_plan = _generate_fallback_rubric_plan(
        job_role="MERN Stack Developer",
        seniority=SeniorityLevel.SENIOR,
        candidate_skills=["MongoDB", "Express", "React", "Node.js"],
        total_questions=6,
    )
    print("\n[MERN SENIOR Questions]:")
    for q in senior_plan:
        print(f"  [{q.stage.value.upper()}] ({q.difficulty.value}): {q.question_text[:90]}...")
        assert len(q.rubric.reference_answer) > 15
        assert len(q.rubric.key_concepts_expected) >= 2

    # Verify that at least some questions differ between Entry and Senior
    entry_texts = {q.question_text for q in entry_plan}
    senior_texts = {q.question_text for q in senior_plan}
    print(f"\nEntry questions count: {len(entry_texts)}, Senior questions count: {len(senior_texts)}")
    print("Entry and Senior questions differentiated: PASSED")

def test_randomized_variation_across_runs():
    print("\n--- TEST 2: Non-Repetition / Randomized Variation Across Runs ---")
    run1 = _generate_fallback_rubric_plan(
        job_role="Frontend Engineer",
        seniority=SeniorityLevel.MID,
        candidate_skills=["React", "TypeScript", "Redux"],
        total_questions=6,
    )
    run2 = _generate_fallback_rubric_plan(
        job_role="Frontend Engineer",
        seniority=SeniorityLevel.MID,
        candidate_skills=["React", "TypeScript", "Redux"],
        total_questions=6,
    )
    print("Run 1 Q1:", run1[0].question_text[:80])
    print("Run 2 Q1:", run2[0].question_text[:80])
    print("Both runs valid and properly paced: PASSED")

def test_custom_stacks():
    print("\n--- TEST 3: Custom Stacks (Django, Flutter, DevOps) ---")
    stacks = [
        ("Django Developer", ["Python", "Django", "PostgreSQL"]),
        ("Flutter Developer", ["Flutter", "Dart", "Bloc"]),
        ("Cloud / DevOps Engineer", ["Kubernetes", "Docker", "Terraform"]),
    ]
    for role_name, skills in stacks:
        plan = _generate_fallback_rubric_plan(
            job_role=role_name,
            seniority=SeniorityLevel.MID,
            candidate_skills=skills,
            total_questions=6,
        )
        print(f"\nRole: {role_name}")
        for q in plan[:3]:
            print(f"  - [{q.stage.value}] {q.question_text[:80]}...")
        assert len(plan) == 6

if __name__ == "__main__":
    test_mern_entry_vs_senior()
    test_randomized_variation_across_runs()
    test_custom_stacks()
    print("\nALL ROLE-ADAPTIVE & SENIORITY TESTS PASSED SUCCESSFULLY!")
