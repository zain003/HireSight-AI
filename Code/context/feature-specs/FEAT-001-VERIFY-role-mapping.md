# FEAT-001-VERIFY: Role Mapping & Configuration Verification

## Files being verified
- `FEAT-001-BE-role-competency-mapping.md`
- `FEAT-001-FE-interview-config-role-select.md`

## Verification Checks

### 1. Automated Backend Unit & API Tests
- [ ] Run `pytest backend/tests/test_role_mapping.py` — Pass / Fail
- [ ] Verify `infer_seniority_level(0)` returns `SeniorityLevel.ENTRY` — Pass / Fail
- [ ] Verify `infer_seniority_level(3)` returns `SeniorityLevel.MID` — Pass / Fail
- [ ] Verify `infer_seniority_level(7)` returns `SeniorityLevel.SENIOR` — Pass / Fail
- [ ] Verify `infer_seniority_level(10)` returns `SeniorityLevel.LEAD` — Pass / Fail
- [ ] Verify `GET /interview/config/roles` returns 200 with all 7 roles — Pass / Fail

### 2. Frontend Component & Integration Tests
- [ ] Verify `interview-setup.jsx` fetches and renders all 7 roles — Pass / Fail
- [ ] Verify selecting role and difficulty updates the agenda overview — Pass / Fail
- [ ] Verify clicking "Start Interview" passes role, difficulty, and language to `/interview/live/start` — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Role-to-competency weight sums to 1.0 for every role.
- [ ] Missing experience safely defaults to `ENTRY`.
- [ ] Zero unhandled frontend exceptions on failed network fetch.

## Report Output
- Save verification output to `feature-test-reports/FEAT-001-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
