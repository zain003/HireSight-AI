# Feature Specifications Index — HireSIGHT

| File ID | Layer | Priority | Feature | Depends On | Description | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `000-shared-contracts.md` | Shared | P0 | Core Domain Models & Schemas | None | Single source of truth for types & models | ☑ Approved |
| `FEAT-001-BE-role-competency-mapping.md` | Backend | P0 | Role & Competency Mapping | `000-shared-contracts` | Standard role taxonomy & seniority inference | ☑ Done |
| `FEAT-001-FE-interview-config-role-select.md` | Frontend | P0 | Pre-Interview Configuration UI | `FEAT-001-BE` | Role & difficulty confirmation interface | ☑ Done |
| `FEAT-001-VERIFY-role-mapping.md` | Verify | P0 | Role Mapping Verification | `FEAT-001-BE`, `FEAT-001-FE` | End-to-end verification for role mapping | ☑ Done |
| `FEAT-002-BE-question-engine-rubrics.md` | Backend | P0 | Rubric-Backed Question Engine | `FEAT-001-BE` | Question generation with reference rubrics | ☑ Done |
| `FEAT-002-VERIFY-question-engine.md` | Verify | P0 | Question Engine Verification | `FEAT-002-BE` | Rubric generation & storage test suite | ☑ Passed |
| `FEAT-003-BE-session-state-sync.md` | Backend | P0 | Session State Synchronization | `FEAT-002-BE` | Dynamic follow-up & session recovery API | ☑ Done |
| `FEAT-003-FE-interview-resilience-input.md` | Frontend | P0 | Interview Resilience & Input Toggle | `FEAT-003-BE` | Question reload recovery & text/voice toggle | ☑ Done |
| `FEAT-003-VERIFY-session-sync.md` | Verify | P0 | Session Sync Verification | `FEAT-003-BE`, `FEAT-003-FE` | Multi-step recovery verification pass | ☑ Passed |
| `FEAT-004-BE-cv-facial-movement-engine.md` | Backend | P0 | Observable Computer Vision Engine | `000-shared-contracts` | Normalized gaze & 3D head pose estimation | ☑ Done |
| `FEAT-004-VERIFY-cv-engine.md` | Verify | P0 | CV Engine Verification | `FEAT-004-BE` | Landmark normalization & resolution tests | ☑ Passed |
| `FEAT-005-BE-vocal-acoustic-speech-engine.md` | Backend | P0 | Vocal Acoustic Analysis Engine | `000-shared-contracts` | Conversational WPM, pause ratio, & pitch | ☑ Done |
| `FEAT-005-VERIFY-vocal-engine.md` | Verify | P0 | Vocal Engine Verification | `FEAT-005-BE` | Audio conversion & acoustic feature tests | ☑ Passed |
| `FEAT-006-BE-coding-sandbox-hidden-tests.md` | Backend | P0 | Sandboxed Hidden Test Runner | `000-shared-contracts` | Server-side execution & private test cases | ☑ Done |
| `FEAT-006-FE-coding-assessment-ui.md` | Frontend | P1 | Coding Challenge Workspace UI | `FEAT-006-BE` | Code editor with public test runner | ☑ Done |
| `FEAT-006-VERIFY-coding-sandbox.md` | Verify | P0 | Coding Sandbox Verification | `FEAT-006-BE`, `FEAT-006-FE` | Sandbox isolation & hidden test tests | ☑ Passed |
| `FEAT-007-BE-explainable-scoring-engine.md` | Backend | P0 | 5-Dimensional Scoring Engine | `FEAT-001-BE` to `FEAT-006-BE` | Transparent 5-dim model & audit log | ☑ Done |
| `FEAT-007-VERIFY-explainable-scoring.md` | Verify | P0 | Explainable Scoring Verification | `FEAT-007-BE` | Weight calculations & mathematical audit | ☑ Passed |

| `FEAT-008-BE-tailored-feedback-engine.md` | Backend | P1 | Tailored Feedback & Skill Gap | `FEAT-007-BE` | Question-anchored actionable feedback | ☐ Ready |
| `FEAT-008-VERIFY-tailored-feedback.md` | Verify | P1 | Feedback Engine Verification | `FEAT-008-BE` | Skill gap roadmap & evidence tests | ☐ Ready |
| `FEAT-009-BE-pdf-report-generator.md` | Backend | P1 | PDF Recruiter Report Exporter | `FEAT-007-BE`, `FEAT-008-BE` | Publication-grade PDF report engine | ☐ Ready |
| `FEAT-009-FE-report-export-view.md` | Frontend | P1 | Recruiter Report Export View | `FEAT-009-BE` | PDF download & printable report UI | ☐ Ready |
| `FEAT-009-VERIFY-report-export.md` | Verify | P1 | Report Export Verification | `FEAT-009-BE`, `FEAT-009-FE` | PDF generation & layout verification | ☐ Ready |
