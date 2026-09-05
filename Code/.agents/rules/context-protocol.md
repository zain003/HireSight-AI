# Mandatory Context Reading Protocol - HireSIGHT

## Core Rule: Read Context Before Every Command & Action

Before executing any command (PowerShell, CLI, test runners, build tools, server starts), proposing code edits, or implementing feature specifications, the agent **MUST** inspect and adhere to the relevant context documents in the `context/` directory.

---

## 1. Context File Reference Map

Whenever working on tasks in this repository, always read and cross-reference the corresponding context files:

| Context File | Primary Purpose | When to Read |
| :--- | :--- | :--- |
| [`context/project-overview.md`](file:///d:/FYP/Code/context/project-overview.md) | High-level system architecture, multimodal pipelines, core invariants | Before starting any new module or reviewing system boundaries |
| [`context/project-scope.md`](file:///d:/FYP/Code/context/project-scope.md) | Strict in-scope vs. out-of-scope boundaries (e.g., offline STT, observable-only metrics) | Before introducing any new feature, library, or scoring metric |
| [`context/architecture.md`](file:///d:/FYP/Code/context/architecture.md) | Directory ownership, technology stack, Beanie ODM collections, access control | Before creating files, modifying database schemas, or adding API endpoints |
| [`context/ui-context.md`](file:///d:/FYP/Code/context/ui-context.md) | Technical dark-mode design system, color tokens, layout blueprints, component standards | Before building, styling, or modifying any frontend component, page, or UI layout |
| [`context/code-standards.md`](file:///d:/FYP/Code/context/code-standards.md) | Backend (FastAPI, Pydantic v2, Async) and Frontend (Next.js, React 18) coding conventions | Before writing, editing, or refactoring backend/frontend code |
| [`context/ai-workflow-rules.md`](file:///d:/FYP/Code/context/ai-workflow-rules.md) | Spec-driven execution rules, 80–150 line discipline, pre-flight gate protocol, ambiguity resolution | Before implementing or updating any feature spec |
| [`context/progress-tracker.md`](file:///d:/FYP/Code/context/progress-tracker.md) | Project status, completed components, ongoing tasks, and next steps | Before selecting or planning tasks, and after completing feature milestones |
| [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md) | Complete spec catalog, dependency graph, and verification status | Before executing any spec to verify all upstream dependencies have passed |
| [`context/feature-specs/000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md) | Canonical data models, DTOs, scoring models, and cross-layer interfaces | Before writing schemas, API endpoints, or frontend API integration hooks |
| [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md) | Log of all assumptions made during ambiguity resolution | When encountering edge cases, or before making architectural assumptions |

---

## 2. Pre-Command Execution Checklist

Before running any command via shell tools (`run_command` or similar):

1. **Verify Working Directory**:
   - Backend commands must run from [`backend/`](file:///d:/FYP/Code/backend/) (with `.\venv\Scripts\activate` if running Python scripts).
   - Frontend commands must run from [`frontend/`](file:///d:/FYP/Code/frontend/).
   - Root verification scripts must run from workspace root [`/`](file:///d:/FYP/Code/).

2. **Check Pre-Flight Spec Gates**:
   - If the command relates to a feature unit (`FEAT-XXX`), ensure all prerequisites in `context/feature-specs/INDEX.md` have been verified.

3. **Validate Invariants**:
   - Ensure the command or code does not violate core invariants (e.g., no psychological mind-reading labels, no candidate access to recruiter reports, no un-sandboxed code execution).

4. **Verify Dependencies & Models**:
   - Verify that required models, schemas, and endpoints comply with [`context/feature-specs/000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md).

---

## 3. Ambiguity & Deviation Protocol

If any context requirement appears conflicting or underspecified:
- **DO NOT** guess silently.
- Check [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md) for existing logged assumptions.
- Log the minimal reasonable assumption in `DEVIATIONS.md` if it does not alter scoring invariants or shared contracts.
- Stop and seek clarification if the change impacts shared contracts or scoring formulas.
