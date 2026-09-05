# FEAT-006-VERIFY: Coding Sandbox & Hidden Tests Verification

## Files being verified
- `FEAT-006-BE-coding-sandbox-hidden-tests.md`
- `FEAT-006-FE-coding-assessment-ui.md`

## Verification Checks

### 1. Automated Unit & Sandbox Tests
- [ ] Run `pytest backend/tests/test_code_execution_sandbox.py` — Pass / Fail
- [ ] Verify Python execution compiles and runs public & hidden tests — Pass / Fail
- [ ] Verify JavaScript (Node) execution runs public & hidden tests — Pass / Fail
- [ ] Verify hard timeout enforcement kills infinite loops in <= 3.5s — Pass / Fail
- [ ] Verify hidden test inputs/outputs are never returned in public test route — Pass / Fail

### 2. Frontend UI & Submission Tests
- [ ] Verify code editor renders syntax and updates on language switch — Pass / Fail
- [ ] Verify "Run Public Tests" displays per-test results and stdout logs — Pass / Fail
- [ ] Verify "Submit Challenge" saves result and advances interview flow — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Multi-language code execution works reliably in sandbox.
- [ ] Hidden tests are securely evaluated on server side only.
- [ ] Timeout and output truncation safeguards function as designed.

## Report Output
- Save verification output to `feature-test-reports/FEAT-006-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
