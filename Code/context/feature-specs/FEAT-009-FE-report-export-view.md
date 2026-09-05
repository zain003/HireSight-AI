# FEAT-009-FE: Recruiter Report Export & Download UI — P1

## Layer
Frontend

## Goal
Enhance the admin Recruiter Report Viewer to display the full 5-dimensional breakdown, fit rationale, and provide one-click download buttons for PDF and JSON report exports.

## Depends on
`FEAT-009-BE-pdf-report-generator.md`

## Context pack
```typescript
export interface RecruiterReportExportPayload {
  session_id: string;
  candidate_name: string;
  target_role: string;
  scores: FiveDimensionScores;
  feedback: TailoredFeedback;
  questions_summary: any[];
}
```

## Consumes
- `GET /interview/admin/session/{session_id}/export/pdf`
- `GET /interview/admin/session/{session_id}/export/json`

## Scope (In)
- "Download PDF Report" action button triggering binary stream download with loading state.
- "Export JSON" action button copying or downloading structured session payload.
- 5-Dimensional score breakdown visualization card (Tech, Coding, Role Fit, Comm, Beh).
- Mathematical audit log modal explaining exact score contributions.

## Scope (Out)
- Candidate interview execution (covered in `FEAT-003-FE`).
- Server-side PDF binary compilation (covered in `FEAT-009-BE`).

## Tech / files to touch
- `frontend/src/components/Interview/RecruiterReportViewer.jsx` [MODIFY]
- `frontend/src/services/adminDashboardService.js` [MODIFY]

## Tests to write FIRST
- `test_renders_5_dimensional_scores`: Viewer renders cards for Technical, Coding, Role Fit, Communication, and Behavioral scores.
- `test_pdf_download_button_triggers_blob_download`: Clicking "Download PDF" calls export API and triggers browser download.
- `test_audit_modal_shows_formulas`: Clicking "View Scoring Math" displays mathematical audit modal.

## Implementation steps
1. Add `downloadReportPdf(sessionId)` and `exportReportJson(sessionId)` to `adminDashboardService.js`.
2. Update `RecruiterReportViewer.jsx` to render 5-dimension score meters and audit log modal.
3. Add action buttons for PDF download and JSON export with error boundary protection.

## Acceptance criteria
- Recruiter can download publication-ready PDF with one click.
- 5-Dimensional score cards accurately render all five categories.
- Scoring formula audit modal shows complete breakdown of weights and inputs.

## Definition of Done
- Component tests pass with 100% success rate.
- Verified in Chrome, Firefox, and Edge.
- Zero console errors during PDF stream download.

## Edge cases to handle
- Network interruption during large PDF download → shows retry toast alert.
- Admin token expired → redirects to admin login gracefully.

## Pre-flight check
- Confirm `FEAT-009-BE` passed all verification steps.

## What's next
- `FEAT-009-VERIFY-report-export.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-009-FE] — [ambiguity] — [assumption]`.
3. Stop and flag if API contract changes.
