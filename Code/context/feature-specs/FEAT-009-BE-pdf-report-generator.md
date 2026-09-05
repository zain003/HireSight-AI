# FEAT-009-BE: Comprehensive PDF & JSON Report Export Service — P1

## Layer
Backend

## Goal
Implement a server-side publication-grade PDF and structured JSON export service that compiles candidate overview, 5-dimensional scores, question-by-question rubric comparisons, coding benchmarks, observable physical metrics, and fit rationale into a downloadable recruiter report.

## Depends on
`FEAT-007-BE-explainable-scoring-engine.md`, `FEAT-008-BE-tailored-feedback-engine.md`

## Context pack
```python
class RecruiterReportExportPayload(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    scores: FiveDimensionScores
    feedback: TailoredFeedback
    questions_summary: List[Dict[str, Any]]
    coding_summary: Optional[Dict[str, Any]]
    cv_summary: ObservableCVMetrics
    vocal_summary: ObservableVocalMetrics
```

## Provides / Exposes
```python
GET /interview/admin/session/{session_id}/export/json -> RecruiterReportExportPayload
GET /interview/admin/session/{session_id}/export/pdf -> StreamingResponse (application/pdf)
```

## Scope (In)
- Dynamic PDF generation using ReportLab / WeasyPrint with clean layout, score cards, and tables.
- Executive candidate summary, target role match, and fit status explanation.
- Complete question-by-question transcripts with rubric comparison.
- Coding challenge execution details and observable CV/vocal physical metrics.
- JSON export endpoint for downstream ATS integration.

## Scope (Out)
- Candidate-facing result views (restricted by report secrecy invariant).
- Frontend PDF preview components (covered in `FEAT-009-FE`).

## Tech / files to touch
- `backend/app/interview/services/pdf_generator_service.py` [NEW]
- `backend/app/interview/routes.py` [MODIFY]
- `backend/requirements.txt` [MODIFY] (reportlab / weasyprint)

## Tests to write FIRST
- `test_json_export_contains_all_5_dimensions`: Assert JSON export response matches `RecruiterReportExportPayload`.
- `test_pdf_generation_returns_valid_pdf_bytes`: Assert PDF export returns HTTP 200 with `application/pdf` header and valid `%PDF` magic bytes.
- `test_unauthorized_candidate_cannot_access_export`: Candidate role request returns HTTP 403 Forbidden.

## Implementation steps
1. Add `reportlab` to `backend/requirements.txt`.
2. Create `backend/app/interview/services/pdf_generator_service.py` with multi-page styled PDF builder.
3. Add `GET /interview/admin/session/{session_id}/export/pdf` and `/export/json` routes with admin authorization dependency in `routes.py`.

## Acceptance criteria
- Generated PDF opens in standard PDF viewers with valid multi-page formatting.
- PDF includes all 5 score dimensions, Fit status rationale, and tailored improvement recommendations.
- Non-admin tokens are strictly blocked with HTTP 403.

## Definition of Done
- Unit and integration tests for PDF/JSON export pass 100%.
- PDF generation time < 1.0s.
- Zero memory leaks or temp file debris.

## Edge cases to handle
- Candidate skipped coding challenge → PDF renders "Coding Round Skipped" section cleanly.
- Very long question transcripts → text wrapping and pagination handle multi-page overflow cleanly.

## Pre-flight check
- Confirm `FEAT-007-VERIFY` and `FEAT-008-VERIFY` passed.

## What's next
- `FEAT-009-FE-report-export-view.md`
- `FEAT-009-VERIFY-report-export.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-009-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.
