# Running Deviations & Assumptions Log

This document records all minor assumptions, scope adaptations, and edge case resolutions made during the implementation of feature specs in HireSIGHT.

## Format

`[FILE-ID] — [What was ambiguous] — [Assumption made] — [Date]`

---

## Log Entries

- `[INITIAL-SETUP]` — Initialized deviations log following `context/feature-specs/plan.md` standards — 2026-09-05.
- `[ADR-001]` — Aligned final scoring model to 5 dimensions (Technical 35%, Coding 20%, Role Fit 15%, Communication 15%, Behavioral 15%) per `project-scope.md` Stage 10 — 2026-09-05.
- `[ADR-002]` — Constrained Computer Vision & Vocal analysis strictly to observable physical metrics to comply with bias-resistance requirements — 2026-09-05.
- `[FEAT-003-BE]` — Implemented in-memory `SessionSubmissionLock` for concurrent submission rejection (HTTP 409) and strict sequential validation on answer index progression — 2026-09-05.
- `[FEAT-003-FE]` — Enforced voice-only interview responses with automated speech-to-text transcription; disabled manual keyboard typing and manual text editing in live interview rooms — 2026-10-07.
- `[NON-COMPUTING-DETECTION]` — Expanded taxonomy with non-computing domains (medical_healthcare, engineering, finance, legal) and degrees (MD, MBBS, MPH), and built 6-layer validation engine preventing non-computing candidates with secondary tech tools from misclassification into computing roles — 2026-10-08.
