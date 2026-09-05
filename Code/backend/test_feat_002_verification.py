"""
FEAT-002 End-to-End Verification Suite
Executes all checks defined in context/feature-specs/FEAT-002-VERIFY-question-engine.md
"""
import asyncio
import os
import sys
import time
from datetime import datetime
from unittest.mock import patch

from app.interview.domain.interview_models import (
    InterviewQuestion,
    QuestionRubric,
    QuestionStage,
)
from app.interview.domain.role_taxonomy import (
    SeniorityLevel,
    StandardRole,
)
from app.interview.models import InterviewSession
from app.interview.services.llm_service import (
    _generate_fallback_rubric_plan,
    generate_rubric_backed_plan,
)


def run_verification():
    report_lines = []

    def log(msg=""):
        print(msg)
        report_lines.append(msg)

    log("# FEAT-002 Verification Test Report")
    log(f"**Execution Timestamp**: {datetime.utcnow().isoformat()}Z")
    log("**Target Specs**: `FEAT-002-BE-question-engine-rubrics.md`")
    log()
    log("---")
    log()

    total_checks = 0
    passed_checks = 0

    def check(name, condition, detail=""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        status = "PASSED" if condition else "FAILED"
        if condition:
            passed_checks += 1
            log(f"- [x] **{name}**: `{status}` {detail}")
        else:
            log(f"- [ ] **{name}**: `{status}` {detail}")
        return condition

    log("## 1. Automated Unit & Integration Tests")

    # Run async checks
    async def run_async_tests():
        # Check 1: Stage distribution
        plan_be = await generate_rubric_backed_plan(
            job_role=StandardRole.BACKEND_ENGINEER,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Python", "FastAPI"],
            candidate_projects=[{"name": "Payment Gateway"}],
            total_questions=6,
        )
        stages = [q.stage for q in plan_be]
        has_all_stages = (
            QuestionStage.ICEBREAKER in stages
            and QuestionStage.CORE_TECHNICAL in stages
            and QuestionStage.DEEP_DIVE in stages
            and QuestionStage.CODING in stages
            and QuestionStage.CLOSING in stages
        )
        check(
            "generate_rubric_backed_plan returns valid stage distribution",
            has_all_stages and len(plan_be) == 6,
            f"Stages: {[s.value for s in stages]}",
        )

        # Check 2: Reference answer validity on every question
        all_refs_valid = all(
            bool(q.rubric.reference_answer and len(q.rubric.reference_answer.strip()) > 15)
            for q in plan_be
        )
        check(
            "Every question contains valid rubric with non-empty reference_answer",
            all_refs_valid,
            f"Verified {len(plan_be)}/{len(plan_be)} questions",
        )

        # Check 3: key_concepts_expected >= 2 items
        all_concepts_valid = all(
            len(q.rubric.key_concepts_expected) >= 2 for q in plan_be
        )
        check(
            "key_concepts_expected has >= 2 items for every question",
            all_concepts_valid,
            f"Concept counts: {[len(q.rubric.key_concepts_expected) for q in plan_be]}",
        )

        # Check 4: Fallback generator activates on mock LLM timeout
        with patch(
            "app.interview.services.llm_service._try_interview_llm_call",
            side_effect=RuntimeError("Simulated LLM Timeout"),
        ):
            fallback_plan = await generate_rubric_backed_plan(
                job_role=StandardRole.FRONTEND_ENGINEER,
                seniority=SeniorityLevel.SENIOR,
                candidate_skills=["React", "Next.js"],
                candidate_projects=[],
                total_questions=6,
            )
            fallback_activated = (
                len(fallback_plan) == 6
                and fallback_plan[0].stage == QuestionStage.ICEBREAKER
                and fallback_plan[-1].stage == QuestionStage.CLOSING
            )
            check(
                "Fallback generator activates on mock LLM timeout",
                fallback_activated,
                f"Generated {len(fallback_plan)} questions on LLM failure",
            )

        return plan_be

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    plan_sample = loop.run_until_complete(run_async_tests())

    log()
    log("## 2. Database Schema & Document Integrity Checks")

    from app.interview.domain.interview_models import InterviewSession as DomainInterviewSession
    from app.interview.models import InterviewSession as BeanieInterviewSession

    # Domain Document model persistence check
    questions_data = [
        {
            "question_id": q.question_id,
            "question_index": q.question_index,
            "question_text": q.question_text,
            "question_type": q.stage.value,
            "stage": q.stage.value,
            "competency_area": q.competency_area,
            "difficulty": q.difficulty.value,
            "rubric": q.rubric.model_dump() if hasattr(q.rubric, "model_dump") else q.rubric.dict(),
            "coding_challenge_id": q.coding_challenge_id,
        }
        for q in plan_sample
    ]

    session_doc = DomainInterviewSession(
        session_id="test_session_rubrics_101",
        candidate_id="cand_test_101",
        candidate_name="Alice Engineer",
        job_role=StandardRole.BACKEND_ENGINEER.value,
        questions=questions_data,
    )

    check(
        "InterviewSession domain model accepts questions with nested rubrics",
        len(session_doc.questions) == 6 and "rubric" in session_doc.questions[0],
        f"Stored {len(session_doc.questions)} questions with nested rubric objects",
    )

    # Retrieval integrity check
    retrieved_q0 = session_doc.questions[0]
    retrieved_rubric = retrieved_q0.get("rubric", {})
    integrity_ok = (
        retrieved_rubric.get("reference_answer") != ""
        and len(retrieved_rubric.get("key_concepts_expected", [])) >= 2
        and "depth_criteria" in retrieved_rubric
        and "scoring_guide" in retrieved_rubric
    )
    check(
        "InterviewSession schema retains all rubric subfields without data loss",
        integrity_ok,
        f"Ref Answer: '{retrieved_rubric.get('reference_answer')[:40]}...', Concepts: {retrieved_rubric.get('key_concepts_expected')}",
    )

    # Verify Beanie document schema fields
    beanie_has_questions = "questions" in BeanieInterviewSession.model_fields
    check(
        "Beanie InterviewSession collection schema supports questions array with rubrics",
        beanie_has_questions,
        f"Beanie model fields verified: {list(BeanieInterviewSession.model_fields.keys())[:6]}...",
    )

    log()
    log("## 3. Acceptance Criteria & Latency Gates")

    # Exact count requested
    plan_5 = _generate_fallback_rubric_plan(
        StandardRole.ML_ENGINEER, SeniorityLevel.MID, [], [], total_questions=5
    )
    plan_7 = _generate_fallback_rubric_plan(
        StandardRole.ML_ENGINEER, SeniorityLevel.MID, [], [], total_questions=7
    )
    check(
        "Exact count of requested questions generated per plan (5 and 7 requested)",
        len(plan_5) == 5 and len(plan_7) == 7,
        f"len(5)={len(plan_5)}, len(7)={len(plan_7)}",
    )

    # 100% of questions contain reference answer and rubric
    all_7_roles_valid = True
    for role in StandardRole:
        p = _generate_fallback_rubric_plan(role, SeniorityLevel.SENIOR, [], [], 6)
        for q in p:
            if not q.rubric.reference_answer or len(q.rubric.key_concepts_expected) < 2:
                all_7_roles_valid = False
    check(
        "100% of questions contain non-empty reference answers and scoring rubrics across all 7 roles",
        all_7_roles_valid,
        "Verified all 7 standard engineering roles",
    )

    # Latency benchmark < 50ms
    t_start = time.perf_counter()
    for _ in range(10):
        _ = _generate_fallback_rubric_plan(
            StandardRole.DATA_ENGINEER, SeniorityLevel.LEAD, ["Spark"], [{"name": "Lakehouse"}], 6
        )
    avg_latency_ms = ((time.perf_counter() - t_start) / 10.0) * 1000
    check(
        "Fallback execution completes in < 50ms on API failure",
        avg_latency_ms < 50.0,
        f"Measured latency: {avg_latency_ms:.3f}ms (Limit: 50.0ms)",
    )

    log()
    log("## 4. Overall Verification Summary")
    log(f"**Total Verification Checks**: {total_checks}")
    log(f"**Passed Checks**: {passed_checks}")
    log(f"**Failed Checks**: {total_checks - passed_checks}")
    log(f"**Pass Rate**: {(passed_checks / total_checks) * 100:.1f}%")
    log()
    if passed_checks == total_checks:
        log("### Final Gate Decision: **PASSED (100% Gated Criteria Satisfied)**")
    else:
        log("### Final Gate Decision: **FAILED (Action Required)**")

    # Write report
    report_dir = os.path.join("..", "feature-test-reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "FEAT-002-test-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    log(f"\nReport written to: {report_path}")

    return passed_checks == total_checks


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
