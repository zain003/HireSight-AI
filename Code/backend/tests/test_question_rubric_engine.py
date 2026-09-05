"""
Unit and integration tests for FEAT-002-BE: Rubric-Backed Question Generation Engine.
"""
import pytest
import time
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
from app.interview.services.llm_service import (
    _generate_fallback_rubric_plan,
    generate_rubric_backed_plan,
)


@pytest.mark.anyio
async def test_plan_contains_required_stages():
    """Generated plan contains icebreaker, core_technical, deep_dive, coding, and closing."""
    plan = await generate_rubric_backed_plan(
        job_role=StandardRole.BACKEND_ENGINEER,
        seniority=SeniorityLevel.MID,
        candidate_skills=["Python", "FastAPI", "PostgreSQL"],
        candidate_projects=[{"name": "E-Commerce Microservices"}],
        total_questions=6,
    )
    assert len(plan) == 6
    stages = [q.stage for q in plan]
    assert QuestionStage.ICEBREAKER in stages
    assert QuestionStage.CORE_TECHNICAL in stages
    assert QuestionStage.DEEP_DIVE in stages
    assert QuestionStage.CODING in stages
    assert QuestionStage.CLOSING in stages


@pytest.mark.anyio
async def test_every_question_has_non_empty_rubric():
    """Every question object contains non-empty reference_answer, depth_criteria, and scoring_guide."""
    plan = await generate_rubric_backed_plan(
        job_role=StandardRole.FRONTEND_ENGINEER,
        seniority=SeniorityLevel.SENIOR,
        candidate_skills=["React", "TypeScript", "Next.js"],
        candidate_projects=[{"name": "Analytics Dashboard"}],
        total_questions=6,
    )
    for q in plan:
        assert isinstance(q, InterviewQuestion)
        assert q.question_text and len(q.question_text.strip()) > 10
        assert isinstance(q.rubric, QuestionRubric)
        assert q.rubric.reference_answer and len(q.rubric.reference_answer.strip()) > 10
        assert isinstance(q.rubric.depth_criteria, dict)
        assert "basic" in q.rubric.depth_criteria
        assert "intermediate" in q.rubric.depth_criteria
        assert "advanced" in q.rubric.depth_criteria
        assert isinstance(q.rubric.scoring_guide, dict)
        assert "relevance_max" in q.rubric.scoring_guide


@pytest.mark.anyio
async def test_key_concepts_expected_minimum_count():
    """Key concepts expected has >= 2 items for every question."""
    for role in StandardRole:
        plan = _generate_fallback_rubric_plan(
            job_role=role,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Core Concepts"],
            candidate_projects=[],
            total_questions=6,
        )
        for q in plan:
            assert len(q.rubric.key_concepts_expected) >= 2, (
                f"Role {role} Question {q.question_id} has fewer than 2 key concepts: {q.rubric.key_concepts_expected}"
            )


@pytest.mark.anyio
async def test_fallback_plan_on_llm_error():
    """When LLM call throws an exception, generator returns valid fallback plan with complete rubrics."""
    with patch(
        "app.interview.services.llm_service._try_interview_llm_call",
        side_effect=RuntimeError("Mock LLM network timeout"),
    ):
        plan = await generate_rubric_backed_plan(
            job_role=StandardRole.ML_ENGINEER,
            seniority=SeniorityLevel.LEAD,
            candidate_skills=["PyTorch", "Transformers", "MLOps"],
            candidate_projects=[{"name": "LLM Serving Engine"}],
            total_questions=6,
        )
        assert len(plan) == 6
        assert plan[0].stage == QuestionStage.ICEBREAKER
        assert plan[-1].stage == QuestionStage.CLOSING
        assert plan[0].rubric.reference_answer != ""
        assert len(plan[0].rubric.key_concepts_expected) >= 2


@pytest.mark.anyio
async def test_candidate_no_projects_fallback():
    """Candidate has no projects on resume -> generator completes cleanly without error."""
    plan = await generate_rubric_backed_plan(
        job_role=StandardRole.DEVOPS_ENGINEER,
        seniority=SeniorityLevel.ENTRY,
        candidate_skills=["Docker", "Linux"],
        candidate_projects=[],
        total_questions=6,
    )
    assert len(plan) == 6
    for q in plan:
        assert q.question_text != ""
        assert "{project_clause}" not in q.question_text
        assert q.rubric.reference_answer != ""


@pytest.mark.anyio
async def test_malformed_llm_json_fallback():
    """When LLM outputs malformed JSON, generator gracefully recovers with valid fallback plan."""
    with patch(
        "app.interview.services.llm_service._try_interview_llm_call",
        return_value="[INVALID JSON RESPONSE <<MALFORMED>>",
    ):
        plan = await generate_rubric_backed_plan(
            job_role=StandardRole.DATA_ENGINEER,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Apache Spark", "SQL"],
            candidate_projects=[],
            total_questions=6,
        )
        assert len(plan) == 6
        assert all(isinstance(q, InterviewQuestion) for q in plan)
        assert all(len(q.rubric.key_concepts_expected) >= 2 for q in plan)


def test_fallback_latency_under_50ms():
    """Fallback question generation executes in < 50ms."""
    start = time.perf_counter()
    plan = _generate_fallback_rubric_plan(
        job_role=StandardRole.FULLSTACK_ENGINEER,
        seniority=SeniorityLevel.SENIOR,
        candidate_skills=["React", "FastAPI", "MongoDB"],
        candidate_projects=[{"name": "Portal"}],
        total_questions=6,
    )
    duration_ms = (time.perf_counter() - start) * 1000
    assert len(plan) == 6
    assert duration_ms < 50.0, f"Fallback took {duration_ms:.2f}ms, which exceeds 50ms gate limit"


def test_all_7_roles_and_seniorities_supported():
    """All 7 StandardRoles across all 4 SeniorityLevels generate complete rubric plans."""
    for role in StandardRole:
        for seniority in SeniorityLevel:
            plan = _generate_fallback_rubric_plan(
                job_role=role,
                seniority=seniority,
                candidate_skills=[],
                candidate_projects=[],
                total_questions=6,
            )
            assert len(plan) == 6, f"Failed for {role} at {seniority}"
            assert plan[0].difficulty == seniority
            for q in plan:
                assert q.rubric.reference_answer != ""
                assert len(q.rubric.key_concepts_expected) >= 2
