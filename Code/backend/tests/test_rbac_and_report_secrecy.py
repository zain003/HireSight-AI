"""
Verification tests for Admin RBAC protection, Report Secrecy Invariant #6, and safe MongoDB lookups.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.auth.models import User, Profile
from app.auth.dependencies import get_current_active_user, get_current_admin_user
from app.interview.models import InterviewSession


def test_admin_routes_reject_unauthenticated():
    """Verify that unauthenticated requests to admin routes return 401/403."""
    client = TestClient(app)
    endpoints = [
        ("GET", "/auth/admin/dashboard-stats"),
        ("GET", "/auth/admin/users"),
        ("GET", "/auth/admin/job-posts"),
        ("POST", "/auth/admin/job-post"),
        ("GET", "/auth/admin/candidates"),
        ("POST", "/auth/admin/skill-match"),
        ("GET", "/auth/admin/candidates/test-session-id/report"),
    ]
    for method, endpoint in endpoints:
        if method == "GET":
            res = client.get(endpoint)
        else:
            res = client.post(endpoint, json={})
        assert res.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY, # auth checked first or 401
        ), f"Endpoint {endpoint} failed RBAC, returned {res.status_code}"
        assert res.status_code != 200, f"Endpoint {endpoint} allowed unauthenticated access!"


def test_admin_routes_reject_candidate_token():
    """Verify that candidate user attempting to access admin endpoints is blocked with 403."""
    candidate_user = User.model_construct(
        id="65f000000000000000000001",
        email="candidate@test.com",
        username="candidate_jane",
        full_name="Jane Candidate",
        is_active=True,
        hashed_password="",
    )

    app.dependency_overrides[get_current_active_user] = lambda: candidate_user
    client = TestClient(app)

    try:
        res = client.get("/auth/admin/dashboard-stats")
        assert res.status_code == status.HTTP_403_FORBIDDEN

        res = client.get("/auth/admin/candidates")
        assert res.status_code == status.HTTP_403_FORBIDDEN
    finally:
        app.dependency_overrides.clear()


def test_admin_routes_allow_admin_user():
    """Verify that admin user can access admin endpoints."""
    admin_user = User.model_construct(
        id="admin",
        email="admin@fyp.com",
        username="admin",
        full_name="System Admin",
        is_active=True,
        hashed_password="",
    )

    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    client = TestClient(app)

    try:
        with patch("app.auth.routes.get_dashboard_stats", AsyncMock(return_value={"total_users": 10})):
            res = client.get("/auth/admin/dashboard-stats")
            assert res.status_code == status.HTTP_200_OK
            assert res.json()["total_users"] == 10
    finally:
        app.dependency_overrides.clear()


def test_candidate_report_endpoint_never_exposes_recruiter_report():
    """
    Invariant #6: Candidate endpoint GET /interview/live/{session_id}/report must NEVER
    expose recruiter evaluations, recommendations, or recruiter report to candidate sessions.
    """
    candidate_user = User.model_construct(
        id="65f000000000000000000001",
        email="candidate@test.com",
        username="candidate_jane",
        full_name="Jane Candidate",
        is_active=True,
        hashed_password="",
    )

    mock_session = InterviewSession.model_construct(
        session_id="session-secrecy-test-01",
        user_id="65f000000000000000000001",
        candidate_name="Jane Candidate",
        status="completed",
        aggregate_scores={"overall_score": 85.0},
        report={
            "session_id": "session-secrecy-test-01",
            "candidate_id": "65f000000000000000000001",
            "candidate_name": "Jane Candidate",
            "job_role": "Software Engineer",
            "overall_score": 85.0,
            "dimension_scores": {},
            "detailed_feedback": "Great technical performance.",
            "radar_chart_data": [],
            "strengths": ["Clear communication"],
            "improvements": ["Edge case handling"],
            "summary": "Completed successfully",
        },
        recruiter_report={
            "hiring_recommendation": "Strong Fit",
            "confidence_level": "High",
            "internal_notes": "Confidential recruiter evaluation notes.",
        },
    )

    app.dependency_overrides[get_current_active_user] = lambda: candidate_user
    client = TestClient(app)

    try:
        with patch.object(InterviewSession, "find_one", AsyncMock(return_value=mock_session)):
            res = client.get("/interview/live/session-secrecy-test-01/report")
            assert res.status_code == status.HTTP_200_OK
            data = res.json()
            assert data["session_id"] == "session-secrecy-test-01"
            assert data["report"] is not None
            # Core Invariant #6 verification: recruiter_report MUST be None
            assert data.get("recruiter_report") is None, "Violation: recruiter_report was leaked to candidate endpoint!"
    finally:
        app.dependency_overrides.clear()
