# FEAT-003-VERIFY: Session State Synchronization Verification

## Files being verified
- `FEAT-003-BE-session-state-sync.md`
- `FEAT-003-FE-interview-resilience-input.md`

## Verification Checks

### 1. Automated Backend Unit & API Tests
- [ ] Run `pytest backend/tests/test_session_sync.py` — Pass / Fail
- [ ] Verify `GET /interview/live/{session_id}/state` returns accurate index and total questions — Pass / Fail
- [ ] Verify inserting a follow-up renumbers all subsequent questions sequentially — Pass / Fail
- [ ] Verify stage follow-up limit (max 3) and total interview limit (max 9) are enforced — Pass / Fail

### 2. Frontend State Recovery & Input Tests
- [ ] Verify browser refresh during question 2 reloads question 2 without data loss — Pass / Fail
- [ ] Verify submitting text answer in text mode records answer and advances to next question — Pass / Fail
- [ ] Verify follow-up banner displays when follow-up is returned by backend — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Zero question index drift across multiple follow-up insertions.
- [ ] Resilient recovery across page reloads.
- [ ] Text and voice submission paths produce valid `AnswerEvaluation` entries.

## Report Output
- Save verification output to `feature-test-reports/FEAT-003-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
