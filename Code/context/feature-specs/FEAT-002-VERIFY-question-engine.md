# FEAT-002-VERIFY: Question Engine & Rubrics Verification

## Files being verified
- `FEAT-002-BE-question-engine-rubrics.md`

## Verification Checks

### 1. Automated Unit & Integration Tests
- [ ] Run `pytest backend/tests/test_question_rubric_engine.py` — Pass / Fail
- [ ] Verify `generate_rubric_backed_plan` returns valid stage distribution — Pass / Fail
- [ ] Verify every question contains a valid `rubric` with `reference_answer` — Pass / Fail
- [ ] Verify `key_concepts_expected` has >= 2 items for every technical question — Pass / Fail
- [ ] Verify fallback generator activates on mock LLM timeout — Pass / Fail

### 2. Database Integrity Checks
- [ ] Verify `InterviewSession` document stores `rubric` inside `questions` array without schema rejection — Pass / Fail
- [ ] Verify querying `InterviewSession` by `session_id` retrieves all rubrics intact — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Exactly the requested number of questions generated per plan.
- [ ] 100% of questions contain non-empty reference answers and scoring rubrics.
- [ ] Fallback execution completes in < 50ms on API failure.

## Report Output
- Save verification output to `feature-test-reports/FEAT-002-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
