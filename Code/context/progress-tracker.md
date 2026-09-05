# Progress Tracker - HireSIGHT

## Current Phase

**Phase**: Active Specification Authoring & Core Engine Refinement (Aligning platform with `context/project-scope.md`).

## Current Goal

Establish the complete spec-driven blueprint in `context/feature-specs/` and prepare implementation units for Role Mapping, Rubric-backed Question Generation, Session State Resilience, Normalized CV & Acoustic Engines, Sandboxed Hidden Test Execution, 5-Dimensional Explainable Scoring, Tailored Feedback, and PDF Report Export.

---

## Status Breakdown

### Completed Features (Baseline & Feature Specs)
- ✅ Multi-format resume text parser with PDF, DOCX, image support and OCR fallback (`backend/app/resume/`).
- ✅ Computing domain resume validation filters (`backend/app/resume/service.py`).
- ✅ JWT Authentication and Role-based Route Protection (`backend/app/auth/`).
- ✅ Live interview video feed UI and Edge-TTS synthesis (`frontend/src/pages/interview.jsx`).
- ✅ Offline speech-to-text with local Vosk Kaldi model (`backend/app/interview/services/stt_service.py`).
- ✅ Subprocess multi-language code runner for public test cases (`backend/app/interview/services/code_execution.py`).
- ✅ Admin dashboard for job posting and candidate list management (`frontend/src/pages/admin-dashboard.jsx`).
- ✅ **FEAT-001-BE**: Standardized Role & Competency Mapping Engine (`backend/app/interview/domain/role_taxonomy.py`, `backend/app/interview/services/role_mapping_service.py`, `GET /interview/config/roles`, `POST /interview/config/role-fit`, 12/12 unit tests passing).
- ✅ **FEAT-001-FE**: Pre-Interview Role & Difficulty Selection UI (`frontend/src/pages/interview-setup.jsx`, `frontend/src/components/Interview/InterviewConfigCard.jsx`, `frontend/src/services/interviewService.js`, production build validated).
- ✅ **FEAT-001-VERIFY**: Role Mapping & Pre-Interview Configuration End-to-End Verification Suite (`backend/test_feat_001_verification.py`, 14/14 checks passing, `feature-test-reports/FEAT-001-test-report.md`).

### In Progress / Upcoming Specs
- 📋 **FEAT-002-BE** (P0 - Ready): Rubric-Backed Question Generation Engine (`backend/app/interview/services/llm_service.py`).
- 🔄 **FEAT-002-VERIFY**: Rubric-Backed Question Engine Verification (`FEAT-002-VERIFY-question-engine.md`).
- 🔄 **FEAT-003**: Session State Resilience (`backend/app/interview/application/interview_service.py`).
- 🔄 **FEAT-004**: Computer Vision Refinement (Normalized gaze & 3D head pose).
- 🔄 **FEAT-005**: Acoustic Speech Analysis Refinement (WPM, pause ratios).
- 🔄 **FEAT-006**: Coding Sandbox Security & Hidden Tests.
- 🔄 **FEAT-007**: 5-Dimensional Explainable Scoring Engine.
- 🔄 **FEAT-008**: Tailored Feedback Generation.
- 🔄 **FEAT-009**: PDF & JSON Report Export.

---

## Architecture Decision Records (ADRs)

- **ADR-001 (5-Dimensional Scoring Model)**: Switched from legacy 4-factor scoring to explicit 5-factor scoring (Tech Knowledge 35%, Coding 20%, Role Fit 15%, Communication 15%, Behavioral 15%) per `project-scope.md` to ensure holistic role-alignment evaluation.
- **ADR-002 (Objective Physical Metrics for CV/Audio)**: Prohibited speculative emotion labeling in computer vision and voice analysis. All metrics must represent measurable physical indicators (normalized gaze ratio, head rotation in degrees, speech rate in WPM, pause duration ratio).
- **ADR-003 (Pre-Computed Question Rubrics)**: Every generated question must carry a reference answer key and grading rubric stored in MongoDB to ensure consistent, explainable evaluation.
- **ADR-004 (Server-Side Hidden Test Evaluation)**: Hidden test cases are never sent to the client browser to prevent hardcoded solutions and ensure authentic algorithmic evaluation.

---

## Session Notes

- Added Antigravity workspace rules (`AGENTS.md`), custom skills (`hiresight-spec-workflow`, `hiresight-backend`, `hiresight-frontend`, `hiresight-system-verify`), `.agents/rules/context-protocol.md`, and automated verification scripts.
- Implemented **FEAT-001-BE**: Standardized 7 tech roles (`StandardRole`), 4 seniority tiers (`SeniorityLevel`), complete competency matrices with weights summing to 1.0, candidate profile matching (`map_profile_to_role_fit`), and API endpoints (`GET /interview/config/roles`, `POST /interview/config/role-fit`).
- Implemented **FEAT-001-FE**: Pre-interview calibration page (`interview-setup.jsx`), role and difficulty selection card component (`InterviewConfigCard.jsx`), dynamic 4-stage agenda preview, profile skill coverage calculator, and API integration in `interviewService.js`.
- Implemented & Executed **FEAT-001-VERIFY**: Ran end-to-end verification suite across backend taxonomy, FastAPI routes, and frontend contract compliance (14/14 automated checks passing with 100% success rate, generated [`feature-test-reports/FEAT-001-test-report.md`](file:///d:/FYP/Code/feature-test-reports/FEAT-001-test-report.md)). All FEAT-001 specs are now completely verified and closed.

