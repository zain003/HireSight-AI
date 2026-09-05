# AI Workflow Rules - HireSIGHT

## Approach & Spec-Driven Development

1. **Spec-Driven Execution**: Work is planned, implemented, and verified strictly against specification files located in `context/feature-specs/`.
2. **Layered Splitting**: Every feature unit is divided by its architectural layer:
   - `[FEAT-XXX-BE]`: Backend schema changes, FastAPI routes, domain business logic, services, unit tests.
   - `[FEAT-XXX-FE]`: Frontend UI components, state hooks, and client-side validation wired to backend endpoints.
   - `[FEAT-XXX-INT]`: Cross-feature event triggers, background tasks, or multi-service pipelines (e.g. video + audio frame aggregation).
   - `[FEAT-XXX-VERIFY]`: Machine-checkable verification checklist and acceptance test suite confirming the Definition of Done.
3. **Size Discipline**: Each spec file must strictly target **80–150 lines**. If a layer exceeds this, split into sub-units (e.g. `BE-schema.md` and `BE-logic.md`).
4. **Priority Hierarchy**: Every file carries a priority tag:
   - `P0`: MVP-critical path (Launch-blocking).
   - `P1`: Essential for complete candidate/admin lifecycle (Required before release).
   - `P2`: Quality-of-life enhancements and performance optimizations.

---

## Pre-Flight & Dependency Rules

- **Strict Dependency Ordering**: Every `FE`, `INT`, or downstream spec must list exact dependency file IDs under `Depends on:`.
- **Pre-flight Gate**: An agent must NEVER start implementing a file until all prerequisites listed in `Depends on:` have a passing `VERIFY` file recorded in `context/feature-specs/INDEX.md`.
- **Self-Contained Context Packs**: Every downstream spec must contain inlined type signatures and contract interfaces in its `Context pack:` so it can be implemented in a fresh session without memory of previous conversations.

---

## Ambiguity Resolution Protocol

If an implementation encounters an unspecified case or edge condition:
1. **Do NOT silently guess.**
2. Make the minimal reasonable assumption required to maintain system invariants.
3. Log the decision immediately in [`context/feature-specs/DEVIATIONS.md`](file:///d:/FYP/Code/context/feature-specs/DEVIATIONS.md) as:
   `[FILE-ID] — [Ambiguity Description] — [Assumption Made]`
4. If the assumption affects data models in `000-shared-contracts.md` or scoring weights in `architecture.md`, STOP and request human review.

---

## Verification & Definition of Done

Before marking any feature unit complete:
1. **Zero Failing Tests**: All unit, integration, and verification tests must pass 100%. No skipped or flaky tests.
2. **Invariant Compliance**: Confirm no invariant from `context/architecture.md` is violated.
3. **Acceptance Criteria**: Check every binary acceptance criterion defined in the spec.
4. **Code Quality**: Ensure strict type annotations, clean lints, and no leftover debugging logs.
5. **Documentation Sync**: Update `context/feature-specs/INDEX.md` and `context/progress-tracker.md` to reflect completed work.

---

## Protected Directories & Files

Do not modify without explicit instruction:
- Third-party AI model weights (`backend/models/vosk-*`).
- Core infrastructure configuration files (`docker-compose.yml`, root setup scripts) unless required for feature runtime dependencies.
