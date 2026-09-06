"""
Unit tests for Admin Dashboard Candidate Roster & Report Endpoints (Issue 02 / FEAT-010).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

from app.auth.models import User, Profile
from app.auth.job_post_model import JobPost
from app.interview.models import InterviewSession
from app.auth.admin_candidates_service import (
    get_candidate_roster,
    get_candidate_session_report,
)


@pytest.fixture
def sample_users():
    u1 = MagicMock(spec=User)
    u1.id = ObjectId("650000000000000000000001")
    u1.email = "alice@example.com"
    u1.username = "alice"
    u1.full_name = "Alice Smith"
    u1.created_at = datetime(2026, 1, 15, 10, 0, 0)
    u1.is_active = True

    u2 = MagicMock(spec=User)
    u2.id = ObjectId("650000000000000000000002")
    u2.email = "bob@example.com"
    u2.username = "bob"
    u2.full_name = "Bob Jones"
    u2.created_at = datetime(2026, 1, 20, 10, 0, 0)
    u2.is_active = True

    u3 = MagicMock(spec=User)
    u3.id = ObjectId("650000000000000000000003")
    u3.email = "carol@example.com"
    u3.username = "carol"
    u3.full_name = "Carol White"
    u3.created_at = datetime(2026, 2, 1, 10, 0, 0)
    u3.is_active = True

    return [u1, u2, u3]


@pytest.fixture
def sample_profiles():
    p1 = MagicMock(spec=Profile)
    p1.user_id = "650000000000000000000001"
    p1.job_role = "Backend Engineer"
    p1.experience_years = 4
    p1.skills = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    p1.resume_score = 88.0

    p2 = MagicMock(spec=Profile)
    p2.user_id = "650000000000000000000002"
    p2.job_role = "Frontend Engineer"
    p2.experience_years = 2
    p2.skills = ["React", "TypeScript", "Next.js", "Tailwind"]
    p2.resume_score = 72.0

    p3 = MagicMock(spec=Profile)
    p3.user_id = "650000000000000000000003"
    p3.job_role = "ML Engineer"
    p3.experience_years = 5
    p3.skills = ["PyTorch", "Python", "Transformers"]
    p3.resume_score = 91.0

    return [p1, p2, p3]


@pytest.fixture
def sample_job_posts():
    jp1 = MagicMock(spec=JobPost)
    jp1.id = ObjectId("651000000000000000000001")
    jp1.title = "Senior Backend Engineer"
    jp1.required_skills = ["Python", "PostgreSQL"]

    return [jp1]


@pytest.fixture
def sample_sessions():
    s1 = MagicMock(spec=InterviewSession)
    s1.id = ObjectId("652000000000000000000001")
    s1.session_id = "session_alice_completed"
    s1.user_id = "650000000000000000000001"
    s1.candidate_id = "650000000000000000000001"
    s1.candidate_name = "Alice Smith"
    s1.job_post_id = "651000000000000000000001"
    s1.job_role = "Senior Backend Engineer"
    s1.status = "completed"
    s1.started_at = datetime(2026, 2, 10, 10, 0, 0)
    s1.ended_at = datetime(2026, 2, 10, 10, 45, 0)
    s1.candidate_skills = ["Python", "FastAPI"]
    s1.aggregate_scores = {"overall_score": 87.5}
    s1.recruiter_report = {
        "overall_score": 87.5,
        "hiring_recommendation": "Strong Fit",
        "fit_status": "Strong Fit",
        "session_duration_minutes": 45.0,
        "five_dimension_scores": {
            "technical_knowledge_score": 90.0,
            "coding_ability_score": 85.0,
            "role_fit_score": 88.0,
            "communication_score": 84.0,
            "behavioral_indicators_score": 86.0,
            "overall_composite_score": 87.5,
            "fit_status": "Strong Fit",
        },
    }
    s1.questions = [{"question_id": "q1"}, {"question_id": "q2"}]
    s1.evaluations = [{"relevance_score": 9.0}]

    s2 = MagicMock(spec=InterviewSession)
    s2.id = ObjectId("652000000000000000000002")
    s2.session_id = "session_bob_inprogress"
    s2.user_id = "650000000000000000000002"
    s2.candidate_id = "650000000000000000000002"
    s2.candidate_name = "Bob Jones"
    s2.job_post_id = None
    s2.job_role = "Frontend Engineer"
    s2.status = "in_progress"
    s2.started_at = datetime(2026, 2, 12, 14, 0, 0)
    s2.ended_at = None
    s2.candidate_skills = ["React"]
    s2.aggregate_scores = {"overall_score": 64.0}
    s2.recruiter_report = None
    s2.questions = [{"question_id": "q1"}]
    s2.evaluations = []

    return [s1, s2]


@pytest.mark.anyio
async def test_get_candidate_roster_unfiltered(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.User.find") as mock_u_find, \
         patch("app.auth.admin_candidates_service.Profile.find") as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.find") as mock_j_find, \
         patch("app.auth.admin_candidates_service.InterviewSession.find") as mock_s_find:

        mock_u_find.return_value.to_list = AsyncMock(return_value=sample_users)
        mock_p_find.return_value.to_list = AsyncMock(return_value=sample_profiles)
        mock_j_find.return_value.to_list = AsyncMock(return_value=sample_job_posts)
        mock_s_find.return_value.to_list = AsyncMock(return_value=sample_sessions)

        result = await get_candidate_roster()

        # Alice (completed), Bob (in_progress), Carol (not_started)
        assert result.total_count == 3
        assert result.status_counts["completed"] == 1
        assert result.status_counts["in_progress"] == 1
        assert result.status_counts["not_started"] == 1

        alice = next(i for i in result.items if i.candidate_name == "Alice Smith")
        assert alice.status == "completed"
        assert alice.overall_score == 87.5
        assert alice.hiring_recommendation == "Strong Fit"
        assert alice.has_report is True

        bob = next(i for i in result.items if i.candidate_name == "Bob Jones")
        assert bob.status == "in_progress"
        assert bob.overall_score == 64.0
        assert bob.has_report is False

        carol = next(i for i in result.items if i.candidate_name == "Carol White")
        assert carol.status == "not_started"
        assert carol.overall_score is None


@pytest.mark.anyio
async def test_get_candidate_roster_filter_search(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.User.find") as mock_u_find, \
         patch("app.auth.admin_candidates_service.Profile.find") as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.find") as mock_j_find, \
         patch("app.auth.admin_candidates_service.InterviewSession.find") as mock_s_find:

        mock_u_find.return_value.to_list = AsyncMock(return_value=sample_users)
        mock_p_find.return_value.to_list = AsyncMock(return_value=sample_profiles)
        mock_j_find.return_value.to_list = AsyncMock(return_value=sample_job_posts)
        mock_s_find.return_value.to_list = AsyncMock(return_value=sample_sessions)

        # Search by email
        result = await get_candidate_roster(search="alice@example.com")
        assert result.total_count == 1
        assert result.items[0].candidate_name == "Alice Smith"

        # Search by skill
        result_skill = await get_candidate_roster(search="PyTorch")
        assert result_skill.total_count == 1
        assert result_skill.items[0].candidate_name == "Carol White"


@pytest.mark.anyio
async def test_get_candidate_roster_filter_score_range(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.User.find") as mock_u_find, \
         patch("app.auth.admin_candidates_service.Profile.find") as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.find") as mock_j_find, \
         patch("app.auth.admin_candidates_service.InterviewSession.find") as mock_s_find:

        mock_u_find.return_value.to_list = AsyncMock(return_value=sample_users)
        mock_p_find.return_value.to_list = AsyncMock(return_value=sample_profiles)
        mock_j_find.return_value.to_list = AsyncMock(return_value=sample_job_posts)
        mock_s_find.return_value.to_list = AsyncMock(return_value=sample_sessions)

        # min_score >= 80
        res_high = await get_candidate_roster(min_score=80.0)
        assert res_high.total_count == 1
        assert res_high.items[0].candidate_name == "Alice Smith"

        # max_score < 70
        res_low = await get_candidate_roster(max_score=70.0)
        assert res_low.total_count == 1
        assert res_low.items[0].candidate_name == "Bob Jones"


@pytest.mark.anyio
async def test_get_candidate_roster_filter_status_multiselect(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.User.find") as mock_u_find, \
         patch("app.auth.admin_candidates_service.Profile.find") as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.find") as mock_j_find, \
         patch("app.auth.admin_candidates_service.InterviewSession.find") as mock_s_find:

        mock_u_find.return_value.to_list = AsyncMock(return_value=sample_users)
        mock_p_find.return_value.to_list = AsyncMock(return_value=sample_profiles)
        mock_j_find.return_value.to_list = AsyncMock(return_value=sample_job_posts)
        mock_s_find.return_value.to_list = AsyncMock(return_value=sample_sessions)

        # Multi-select: completed or not_started
        res = await get_candidate_roster(statuses=["completed", "not_started"])
        assert res.total_count == 2
        names = {i.candidate_name for i in res.items}
        assert names == {"Alice Smith", "Carol White"}


@pytest.mark.anyio
async def test_get_candidate_roster_sorting_and_pagination(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.User.find") as mock_u_find, \
         patch("app.auth.admin_candidates_service.Profile.find") as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.find") as mock_j_find, \
         patch("app.auth.admin_candidates_service.InterviewSession.find") as mock_s_find:

        mock_u_find.return_value.to_list = AsyncMock(return_value=sample_users)
        mock_p_find.return_value.to_list = AsyncMock(return_value=sample_profiles)
        mock_j_find.return_value.to_list = AsyncMock(return_value=sample_job_posts)
        mock_s_find.return_value.to_list = AsyncMock(return_value=sample_sessions)

        # Sort by score desc, page_size 1
        res_page1 = await get_candidate_roster(sort_by="score_desc", page=1, page_size=1)
        assert res_page1.total_count == 3
        assert res_page1.total_pages == 3
        assert len(res_page1.items) == 1
        assert res_page1.items[0].candidate_name == "Alice Smith"

        res_page2 = await get_candidate_roster(sort_by="score_desc", page=2, page_size=1)
        assert res_page2.items[0].candidate_name == "Bob Jones"


@pytest.mark.anyio
async def test_get_candidate_session_report_direct(sample_users, sample_profiles, sample_job_posts, sample_sessions):
    with patch("app.auth.admin_candidates_service.InterviewSession.find_one", new_callable=AsyncMock) as mock_s_find, \
         patch("app.auth.admin_candidates_service.User.get", new_callable=AsyncMock) as mock_u_get, \
         patch("app.auth.admin_candidates_service.Profile.find_one", new_callable=AsyncMock) as mock_p_find, \
         patch("app.auth.admin_candidates_service.JobPost.get", new_callable=AsyncMock) as mock_j_get:

        mock_s_find.return_value = sample_sessions[0]
        mock_u_get.return_value = sample_users[0]
        mock_p_find.return_value = sample_profiles[0]
        mock_j_get.return_value = sample_job_posts[0]

        report = await get_candidate_session_report("session_alice_completed")
        assert report["session_id"] == "session_alice_completed"
        assert report["candidate_info"]["name"] == "Alice Smith"
        assert report["candidate_info"]["email"] == "alice@example.com"
        assert report["recruiter_report"]["fit_status"] == "Strong Fit"
        assert report["has_report"] is True


@pytest.mark.anyio
async def test_get_candidate_session_report_not_found():
    with patch("app.auth.admin_candidates_service.InterviewSession.find_one", new_callable=AsyncMock) as mock_s_find:
        mock_s_find.return_value = None
        with pytest.raises(ValueError, match="Interview session not found"):
            await get_candidate_session_report("unknown_session")
