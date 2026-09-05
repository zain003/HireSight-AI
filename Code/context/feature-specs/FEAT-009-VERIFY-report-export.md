# FEAT-009-VERIFY: Recruiter Report Export Verification

## Files being verified
- `FEAT-009-BE-pdf-report-generator.md`
- `FEAT-009-FE-report-export-view.md`

## Verification Checks

### 1. Automated Unit & Export Tests
- [ ] Run `pytest backend/tests/test_pdf_report_export.py` — Pass / Fail
- [ ] Verify PDF generation produces valid PDF structure (`%PDF` header, non-empty stream) — Pass / Fail
- [ ] Verify JSON export contains full 5-dimension scores, feedback, and question list — Pass / Fail
- [ ] Verify candidate token receives HTTP 403 when calling export endpoints — Pass / Fail
- [ ] Verify admin token receives HTTP 200 with valid binary stream — Pass / Fail

### 2. Frontend UI & Download Checks
- [ ] Verify "Download PDF" initiates valid file download with `.pdf` extension — Pass / Fail
- [ ] Verify 5-dimension score meters and radar charts render without distortion — Pass / Fail
- [ ] Verify "View Scoring Math" modal displays complete mathematical audit trail — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Downloadable PDF report contains all required sections from `project-scope.md`.
- [ ] Role fit explanation and fit status reasoning are clearly presented.
- [ ] All export endpoints strictly enforce admin authorization.

## Report Output
- Save verification output to `feature-test-reports/FEAT-009-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
