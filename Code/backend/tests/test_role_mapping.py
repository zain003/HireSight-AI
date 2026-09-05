import math
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.interview.domain.role_taxonomy import (
    ROLE_COMPETENCY_MATRICES,
    ROLE_METADATA_REGISTRY,
    SeniorityLevel,
    StandardRole,
    get_all_standard_roles,
    get_role_competency_matrix,
)
from app.interview.routes import router as interview_router
from app.interview.services.role_mapping_service import (
    get_supported_roles_config,
    infer_seniority_level,
    map_profile_to_role_fit,
)

test_app = FastAPI()
test_app.include_router(interview_router, prefix="/interview")
client = TestClient(test_app)


def test_infer_seniority_entry():
    """Test seniority inference for entry-level experience."""
    assert infer_seniority_level(None) == SeniorityLevel.ENTRY
    assert infer_seniority_level(0) == SeniorityLevel.ENTRY
    assert infer_seniority_level(1) == SeniorityLevel.ENTRY
    assert infer_seniority_level(2) == SeniorityLevel.ENTRY


def test_infer_seniority_mid():
    """Test seniority inference for mid-level experience."""
    assert infer_seniority_level(3) == SeniorityLevel.MID
    assert infer_seniority_level(4) == SeniorityLevel.MID
    assert infer_seniority_level(5) == SeniorityLevel.MID


def test_infer_seniority_senior():
    """Test seniority inference for senior-level experience."""
    assert infer_seniority_level(6) == SeniorityLevel.SENIOR
    assert infer_seniority_level(7) == SeniorityLevel.SENIOR
    assert infer_seniority_level(8) == SeniorityLevel.SENIOR


def test_infer_seniority_lead():
    """Test seniority inference for lead/principal experience."""
    assert infer_seniority_level(9) == SeniorityLevel.LEAD
    assert infer_seniority_level(10) == SeniorityLevel.LEAD
    assert infer_seniority_level(15) == SeniorityLevel.LEAD


def test_all_seven_standard_roles_present():
    """Assert all 7 standard engineering roles are registered."""
    roles = get_all_standard_roles()
    assert len(roles) == 7
    expected = {
        StandardRole.FRONTEND_ENGINEER,
        StandardRole.BACKEND_ENGINEER,
        StandardRole.FULLSTACK_ENGINEER,
        StandardRole.DEVOPS_ENGINEER,
        StandardRole.DATA_ENGINEER,
        StandardRole.ML_ENGINEER,
        StandardRole.QA_AUTOMATION_ENGINEER,
    }
    assert set(roles) == expected


def test_role_competency_weights_sum_to_one():
    """Assert for each role in StandardRole, the sum of importance_weight equals 1.0."""
    for role in StandardRole:
        matrix = get_role_competency_matrix(role)
        assert len(matrix) > 0, f"Role {role} has empty competency matrix."
        total_weight = sum(item.importance_weight for item in matrix)
        assert math.isclose(
            total_weight, 1.0, rel_tol=1e-5
        ), f"Competency weights for {role} sum to {total_weight}, expected 1.0."


def test_role_metadata_complete():
    """Assert all roles have defined title and description."""
    for role in StandardRole:
        meta = ROLE_METADATA_REGISTRY.get(role)
        assert meta is not None, f"Metadata missing for role {role}."
        assert "title" in meta and len(meta["title"]) > 0
        assert "description" in meta and len(meta["description"]) > 0


def test_map_profile_to_role_fit_empty():
    """Assert passing empty or non-matching profile skills returns 0.0 without crashing."""
    result_none = map_profile_to_role_fit(None, StandardRole.BACKEND_ENGINEER)
    assert result_none["overall_fit_score"] == 0.0
    assert result_none["total_matched_concepts"] == 0

    result_empty = map_profile_to_role_fit([], StandardRole.FRONTEND_ENGINEER)
    assert result_empty["overall_fit_score"] == 0.0
    assert result_empty["total_matched_concepts"] == 0

    result_unrelated = map_profile_to_role_fit(
        ["Cooking", "Gardening", "Woodworking"], StandardRole.ML_ENGINEER
    )
    assert result_unrelated["overall_fit_score"] == 0.0


def test_map_profile_to_role_fit_matching():
    """Assert matching skills yield positive weighted score and concept breakdown."""
    frontend_skills = ["React", "JavaScript", "HTML5", "CSS Grid", "Jest", "Redux"]
    result = map_profile_to_role_fit(frontend_skills, StandardRole.FRONTEND_ENGINEER)

    assert result["role"] == "frontend_engineer"
    assert result["overall_fit_score"] > 0.0
    assert len(result["matched_skills"]) > 0
    assert result["total_matched_concepts"] > 0
    assert len(result["competency_breakdown"]) == 5


def test_get_roles_config_structure():
    """Assert get_supported_roles_config returns expected dictionary structure."""
    config_entry = get_supported_roles_config(experience_years=1)
    assert config_entry["default_seniority"] == "entry"
    assert len(config_entry["supported_roles"]) == 7
    assert len(config_entry["seniority_levels"]) == 4

    config_senior = get_supported_roles_config(experience_years=7)
    assert config_senior["default_seniority"] == "senior"


def test_get_roles_endpoint_returns_200():
    """Assert GET /interview/config/roles returns HTTP 200 with complete role taxonomy."""
    response = client.get("/interview/config/roles?experience_years=4")
    assert response.status_code == 200
    data = response.json()

    assert "supported_roles" in data
    assert len(data["supported_roles"]) == 7
    assert data["default_seniority"] == "mid"
    assert "seniority_levels" in data
    assert "entry" in data["seniority_levels"]
    assert "senior" in data["seniority_levels"]


def test_post_role_fit_endpoint():
    """Assert POST /interview/config/role-fit returns HTTP 200 with skill analysis."""
    payload = {
        "role": "backend_engineer",
        "skills": ["FastAPI", "PostgreSQL", "Redis", "Docker", "REST API", "Kafka"],
    }
    response = client.post("/interview/config/role-fit", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["role"] == "backend_engineer"
    assert data["overall_fit_score"] > 0.0
    assert len(data["matched_skills"]) > 0
    assert len(data["competency_breakdown"]) == 5
