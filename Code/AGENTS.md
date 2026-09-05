# HireSIGHT - Antigravity Agent Guidelines & Rules

Welcome to **HireSIGHT** (AI-Powered Multimodal Automated Interviewer & Recruitment Assessment Platform).
This document defines operational rules, architectural invariants, coding standards, and best practices for Antigravity agents working in this repository.

---

## Mandatory Rule: Read Context Files Before Every Command & Action

Before executing any terminal command, modifying code, or starting any feature specification, agents **MUST** inspect and adhere to the relevant context documents:
- [`context/project-overview.md`](file:///d:/FYP/Code/context/project-overview.md): System architecture, multimodal pipelines, core invariants.
- [`context/project-scope.md`](file:///d:/FYP/Code/context/project-scope.md): In-scope vs. out-of-scope boundaries (offline STT, observable-only metrics).
- [`context/architecture.md`](file:///d:/FYP/Code/context/architecture.md): Technology stack, directory ownership, Beanie collections, access control.
- [`context/ui-context.md`](file:///d:/FYP/Code/context/ui-context.md): Technical dark-mode design system, color tokens, layout blueprints, component standards.
- [`context/code-standards.md`](file:///d:/FYP/Code/context/code-standards.md): FastAPI / Next.js / Pydantic v2 conventions and testing guidelines.
- [`context/ai-workflow-rules.md`](file:///d:/FYP/Code/context/ai-workflow-rules.md): Spec-driven workflow, pre-flight gate protocol, ambiguity resolution.
- [`context/progress-tracker.md`](file:///d:/FYP/Code/context/progress-tracker.md): Current implementation progress and milestones.
- [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md): Spec catalog, dependency graph, and verification status.
- [`context/feature-specs/000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md): Canonical schemas, DTOs, scoring models, cross-layer interfaces.
- [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md): Ambiguity log and assumptions.

Detailed rule definitions are located in [`.agents/rules/context-protocol.md`](file:///d:/FYP/Code/.agents/rules/context-protocol.md).

---

## 1. Project Overview & Architecture Boundaries

HireSIGHT combines Computer Vision (MediaPipe), Acoustic Vocal Analysis (Librosa/OpenSMILE), Offline STT (Vosk), Neural TTS (Edge-TTS), LLM Question Rubric Evaluation (Grok/Groq), and Sandboxed Code Execution to provide unbiased candidate assessments.

### Directory Ownership
- [`backend/app/resume/`](file:///d:/FYP/Code/backend/app/resume/): Resume parsing (PDF/DOCX/OCR), domain classification, candidate profile generation.
- [`backend/app/ai/`](file:///d:/FYP/Code/backend/app/ai/): Entity recognition (NER), skill normalization, and taxonomy extraction.
- [`backend/app/auth/`](file:///d:/FYP/Code/backend/app/auth/): JWT authentication, Candidate/Admin role management, job posting CRUD.
- [`backend/app/interview/`](file:///d:/FYP/Code/backend/app/interview/): Live interview session orchestration, question planning with rubrics, STT/TTS routing.
- [`backend/app/interview/services/`](file:///d:/FYP/Code/backend/app/interview/services/): Specialized engines (`behavioral_analysis.py`, `vocal_analysis.py`, `code_execution.py`, `llm_service.py`, `recruiter_report.py`).
- [`frontend/src/pages/`](file:///d:/FYP/Code/frontend/src/pages/): Next.js pages (Candidate portal, Live interview room, Admin dashboard, Recruiter report viewer).
- [`frontend/src/components/`](file:///d:/FYP/Code/frontend/src/components/): Modular UI components (`Interview`, `Admin`, `Resume`, `Candidate`, `Auth`).
- [`context/feature-specs/`](file:///d:/FYP/Code/context/feature-specs/): Spec-driven development units (`FEAT-XXX-*.md`), contracts, and dependency index.

---

## 2. Core System Invariants (Mandatory)

Every agent MUST uphold the following non-negotiable invariants:

1. **Explainable Scoring**: Every score in the 5-dimensional model (Technical, Communication, Behavioral, Problem-Solving, Resume Consistency) must be mathematically computable from observable evaluations, test results, and sensor metrics. Never inject arbitrary or opaque scores.
2. **Observable Physical Signals Only**: Computer vision and voice analysis must ONLY measure objective physical signals (e.g. `gaze_stability_ratio`, `head_pose_variance`, `speaking_rate_wpm`, `pause_duration_ratio`). NEVER claim psychological mind-reading (e.g. `is_lying`, `is_nervous`).
3. **Question Reference Rubrics**: Every generated technical question must include a pre-computed reference answer key, required technical concepts, and grading rubric generated at question creation time.
4. **Sandboxed Code Execution**: Candidate code execution must occur in an isolated subprocess with strict timeouts (max 5s compilation, max 3s per test case), restricted memory, and output buffer caps (max 10KB).
5. **Session Resilience**: Live interview progress must be persistently saved after every question. Page refresh or network interruption must resume from the current question index without state loss.
6. **Report Secrecy**: Candidate endpoints **MUST NEVER** return final hiring recommendations, recruiter evaluations, or behavioral flags to candidate sessions. Recruiter reports are strictly restricted to admin roles.

---

## 3. Spec-Driven Development Pipeline

All feature work follows the strict layered specification workflow defined in [`context/ai-workflow-rules.md`](file:///d:/FYP/Code/context/ai-workflow-rules.md):

```
Spec File Structure:
├── [FEAT-XXX-BE]: Backend schema, FastAPI routes, services, unit tests (80–150 lines)
├── [FEAT-XXX-FE]: Frontend UI components, state hooks, API integration (80–150 lines)
├── [FEAT-XXX-INT]: Cross-service events, background tasks, pipelines (80–150 lines)
└── [FEAT-XXX-VERIFY]: Acceptance checklist & automated verification suite
```

### Pre-Flight Gate Protocol
- Before starting any spec file, verify all items in its `Depends on:` field are completed and verified in [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md).
- Use the `hiresight-spec-workflow` skill to validate gates:
  ```powershell
  python .agents/skills/hiresight-spec-workflow/scripts/check_spec_gates.py
  ```

### Ambiguity Protocol
- If encountering an edge case or missing detail, **DO NOT silently guess**.
- Make the minimal reasonable assumption to maintain invariants and log it in [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md).
- If the ambiguity affects scoring weights or shared contracts in [`000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md), STOP and ask for human review.

---

## 4. Antigravity Skills in this Repository

The repository includes specialized workspace skills in `.agents/skills/`:

| Skill Name | Purpose |
| :--- | :--- |
| [`hiresight-spec-workflow`](file:///d:/FYP/Code/.agents/skills/hiresight-spec-workflow/SKILL.md) | Spec navigation, dependency checking, progress tracking, and deviation logging |
| [`hiresight-backend`](file:///d:/FYP/Code/.agents/skills/hiresight-backend/SKILL.md) | FastAPI, Beanie ODM, Async IO, MediaPipe, Librosa, LLM rubrics, and pytest runners |
| [`hiresight-frontend`](file:///d:/FYP/Code/.agents/skills/hiresight-frontend/SKILL.md) | Next.js, React 18, WebRTC video/audio capture, code editor workspace, and UI testing |
| [`hiresight-system-verify`](file:///d:/FYP/Code/.agents/skills/hiresight-system-verify/SKILL.md) | Full-system verification, invariant validation, and acceptance criteria verification |

---

## 5. Antigravity Slash Commands & Best Practices

When working on tasks in this repository, recommend or utilize the following slash commands:

- `/goal`: Use when executing complex, multi-step tasks (e.g. implementing full feature vertical slices, running end-to-end test sweeps).
- `/grill-me`: Use when planning major architectural refactors, schema migrations, or new AI engine integrations to align on edge cases.
- `/schedule`: Use for periodic health checks or background benchmark monitoring.
- `/learn`: Use when saving custom repository preferences, specific test fixtures, or localized environment configurations.

---

## 6. Quick Operational Commands

### Backend
```powershell
# Activate Python environment & start FastAPI dev server
cd d:\FYP\Code\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run backend test suite
pytest -v
python validate_system.py
```

### Frontend
```powershell
# Start Next.js development server
cd d:\FYP\Code\frontend
npm run dev

# Run build check
npm run build
```
