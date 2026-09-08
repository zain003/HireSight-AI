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


@pytest.mark.parametrize("total_q", [4, 6, 8, 12, 20])
def test_variable_question_counts_and_phases(total_q: int):
    """Fallback generator correctly constructs exact requested question counts across phases."""
    for role in StandardRole:
        plan = _generate_fallback_rubric_plan(
            job_role=role,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Engineering"],
            candidate_projects=[{"name": "App"}],
            total_questions=total_q,
        )
        assert len(plan) == total_q, f"Expected {total_q} questions for {role}, got {len(plan)}"
        stages = [q.stage for q in plan]
        assert QuestionStage.ICEBREAKER in stages
        assert QuestionStage.CODING in stages
        assert QuestionStage.CLOSING in stages
        if total_q >= 7:
            assert QuestionStage.BEHAVIORAL in stages
        # Verify indices are strictly sequential from 0 to total_q - 1
        indices = [q.question_index for q in plan]
        assert indices == list(range(total_q))


@pytest.mark.anyio
async def test_full_20_question_plan_generation():
    """Generating full 20-question interview plan contains all 6 phases in sequential order."""
    plan = await generate_rubric_backed_plan(
        job_role=StandardRole.BACKEND_ENGINEER,
        seniority=SeniorityLevel.SENIOR,
        candidate_skills=["Python", "PostgreSQL", "Kafka"],
        candidate_projects=[{"name": "Distributed Ledger"}],
        total_questions=20,
    )
    assert len(plan) == 20
    stages = [q.stage for q in plan]
    assert QuestionStage.ICEBREAKER in stages
    assert QuestionStage.CORE_TECHNICAL in stages
    assert QuestionStage.DEEP_DIVE in stages
    assert QuestionStage.CODING in stages
    assert QuestionStage.BEHAVIORAL in stages
    assert QuestionStage.CLOSING in stages

    # Coding question must be followed by subsequent behavioral and closing phases
    coding_indices = [i for i, q in enumerate(plan) if q.stage == QuestionStage.CODING]
    assert len(coding_indices) >= 1
    last_coding_idx = max(coding_indices)
    assert last_coding_idx < len(plan) - 1, "Coding challenge must not be forced as the final question"
    assert any(q.stage == QuestionStage.BEHAVIORAL for q in plan[last_coding_idx + 1:])
    assert any(q.stage == QuestionStage.CLOSING for q in plan[last_coding_idx + 1:])


@pytest.mark.parametrize("total_q", [4, 6, 8, 10, 12, 15, 20, 25, 30])
def test_zero_question_repetitions_across_all_roles_and_sizes(total_q: int):
    """Zero duplicate question texts are generated for any role or question count."""
    for role in StandardRole:
        plan = _generate_fallback_rubric_plan(
            job_role=role,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Python", "Engineering"],
            candidate_projects=[{"name": "System"}],
            total_questions=total_q,
        )
        texts = [q.question_text for q in plan]
        assert len(texts) == len(set(texts)), (
            f"Duplicate questions detected in {role.value} for total_q={total_q}!"
        )
        for q in plan:
            assert q.rubric.reference_answer and len(q.rubric.reference_answer.strip()) > 10
            assert len(q.rubric.key_concepts_expected) >= 2


def test_fallback_question_bank_zero_duplicates_with_sparse_skills():
    """Skill fallback generator produces 100% unique questions even with 0 or 1 candidate skills."""
    from app.interview.services.llm_service import _build_fallback_question_bank

    for skills in [[], ["Python"], ["Python", "FastAPI"]]:
        bank = _build_fallback_question_bank(
            job_role="backend_engineer",
            required_job_skills=[],
            candidate_skills=skills,
            candidate_projects=[],
            candidate_job_titles=[],
            candidate_certifications=[],
            candidate_companies=[],
            experience_years=3,
        )
        texts = [q["question_text"] for q in bank]
        assert len(texts) == len(set(texts)), f"Duplicate questions in skill bank with {len(skills)} skills"


@pytest.mark.anyio
async def test_followup_question_zero_duplicates():
    """Consecutive follow-up generation produces distinct questions without repeating prompts."""
    from app.interview.services.llm_service import generate_followup_question

    asked = []
    for stage in ["introduction", "behavioral", "cv_based", "technical"]:
        for _ in range(3):
            fu = await generate_followup_question(
                job_role="Software Engineer",
                original_question="Describe your architecture",
                candidate_answer="It was fast",
                conversation_history=[],
                asked_questions=asked,
                stage=stage,
            )
            q_text = fu["question_text"]
            assert q_text not in asked, f"Duplicate follow-up detected: {q_text}"
            asked.append(q_text)


@pytest.mark.parametrize("total_q", [6, 10, 15, 20])
def test_strict_stage_ordering_invariance_all_roles(total_q: int):
    """All plans across all 7 roles strictly follow canonical stage sequence without phase jumping."""
    stage_rank = {
        QuestionStage.ICEBREAKER: 0,
        QuestionStage.CORE_TECHNICAL: 1,
        QuestionStage.DEEP_DIVE: 2,
        QuestionStage.CODING: 3,
        QuestionStage.BEHAVIORAL: 4,
        QuestionStage.CLOSING: 5,
    }

    for role in StandardRole:
        plan = _generate_fallback_rubric_plan(
            job_role=role,
            seniority=SeniorityLevel.MID,
            candidate_skills=["Python", "System Design"],
            candidate_projects=[{"name": "Production App"}],
            total_questions=total_q,
        )
        ranks = [stage_rank[q.stage] for q in plan]
        assert ranks == sorted(ranks), f"Stage order scrambled in {role.value} for total_q={total_q}: {[q.stage.value for q in plan]}"


def test_followup_stage_normalization_preserves_canonical_stages():
    """_normalize_followup_stage maps aliases correctly and preserves all 6 canonical stages."""
    from app.interview.services.llm_service import _normalize_followup_stage

    assert _normalize_followup_stage("icebreaker") == "icebreaker"
    assert _normalize_followup_stage("intro") == "icebreaker"
    assert _normalize_followup_stage("core_technical") == "core_technical"
    assert _normalize_followup_stage("technical") == "core_technical"
    assert _normalize_followup_stage("deep_dive") == "deep_dive"
    assert _normalize_followup_stage("cv_based") == "deep_dive"
    assert _normalize_followup_stage("coding") == "coding"
    assert _normalize_followup_stage("behavioral") == "behavioral"
    assert _normalize_followup_stage("closing") == "closing"
    assert _normalize_followup_stage("unknown_stage") == "core_technical"



