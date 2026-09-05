# FEAT-004-VERIFY: Computer Vision Engine Verification

## Files being verified
- `FEAT-004-BE-cv-facial-movement-engine.md`

## Verification Checks

### 1. Automated Unit & Algorithmic Tests
- [ ] Run `pytest backend/tests/test_behavioral_cv_engine.py` — Pass / Fail
- [ ] Verify resolution invariance test (480p vs 1080p yields < 1% difference) — Pass / Fail
- [ ] Verify `solvePnP` head pose estimates frontal orientation within ±5° — Pass / Fail
- [ ] Verify blink detection correctly counts simulated eye closures — Pass / Fail
- [ ] Verify output schema contains only `ObservableCVMetrics` without emotion labels — Pass / Fail

### 2. Performance & Benchmark Checks
- [ ] Verify average frame processing latency is < 20ms per frame — Pass / Fail
- [ ] Verify memory allocation does not leak across 100 consecutive frame batch runs — Pass / Fail

### 3. Acceptance Criteria Checklist
- [ ] Normalized eye gaze is resolution-independent.
- [ ] Head pose Euler angles use 3D perspective-n-point solver.
- [ ] Zero unsupported psychological claims in metric output.

## Report Output
- Save verification output to `feature-test-reports/FEAT-004-test-report.md`.
- If any test fails, diagnose, resolve immediately, and re-run.
- Update `INDEX.md` status to ☑ Passed only when 100% checks pass.
