---
name: hiresight-spec-workflow
description: Guide and execute HireSIGHT's Spec-Driven Development workflow. Use this skill when implementing new features from context/feature-specs/, checking pre-flight dependency gates in INDEX.md, validating spec line sizes, managing DEVIATIONS.md, or updating progress tracking.
---

# HireSIGHT Spec-Driven Development Workflow

This skill standardizes how Antigravity agents navigate, implement, and track feature specifications across the HireSIGHT codebase.

## 1. Spec Architecture & Layers

All feature specifications reside in [`context/feature-specs/`](file:///d:/FYP/Code/context/feature-specs/). Each feature is divided into modular, self-contained units constrained to **80–150 lines**:

- **`FEAT-XXX-BE-<name>.md`**: Backend schema changes, FastAPI endpoints, service logic, and unit test suites.
- **`FEAT-XXX-FE-<name>.md`**: Frontend UI components, state management, and API client integration.
- **`FEAT-XXX-INT-<name>.md`**: Cross-service pipelines, background event orchestration, or multimodal frame aggregation.
- **`FEAT-XXX-VERIFY-<name>.md`**: Machine-checkable verification checklist and acceptance test suite.

---

## 2. Pre-Flight Gate Protocol

Before writing or editing code for any spec unit:

1. **Verify Prerequisites**:
   Open the target spec and check the `Depends on:` section.
   Confirm that all prerequisite files have a status of `VERIFIED (Done)` in [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md).

2. **Automated Gate Check**:
   Run the gate checker script to validate dependencies and spec line bounds:
   ```powershell
   python .agents/skills/hiresight-spec-workflow/scripts/check_spec_gates.py
   ```

3. **Check Contract Invariants**:
   Read [`context/feature-specs/000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md) to ensure request/response payloads align with global schemas.

---

## 3. Implementation Workflow

Follow this strict sequence during implementation:

1. **Implement Layer**:
   - For `BE`: Implement models in `app/*/models.py`, domain rules in `app/*/service.py`, and endpoints in `app/*/routes.py`.
   - For `FE`: Build modular React components in `frontend/src/components/`, wire routes in `frontend/src/pages/`, and use centralized API clients in `frontend/src/services/api.js`.
2. **Execute Unit Tests**:
   - Write and run unit tests for all new functions and endpoints.
3. **Handle Edge Cases & Deviations**:
   - If encountering unspecified behavior, make the minimal safe assumption to preserve system invariants.
   - Record the deviation immediately in [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md):
     ```markdown
     - **[FEAT-XXX-BE]**: [Brief description of ambiguity] -> [Decision / Assumption made]
     ```
   - If the deviation impacts shared contracts or 5-dimensional scoring weights, **STOP** and ask for human confirmation.

---

## 4. Verification & Progress Sync

Once implementation is complete:

1. Execute the verification checklist from `FEAT-XXX-VERIFY-*.md`.
2. Update [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md) to mark the spec completed.
3. Update [`context/progress-tracker.md`](file:///d:/FYP/Code/context/progress-tracker.md) with completed deliverables.
