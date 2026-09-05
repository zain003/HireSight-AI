---
name: hiresight-system-verify
description: End-to-end system verification, invariant checking, and quality gating for HireSIGHT. Use this skill before marking any feature spec or release as done, checking database readiness, testing offline AI model presence, or executing acceptance suites.
---

# HireSIGHT System Verification & Quality Gating

This skill outlines the rigorous Definition of Done (DoD) checklist and automated verification procedures for the HireSIGHT platform.

## 1. Definition of Done (DoD) Checklist

Before marking any feature unit complete or concluding a development milestone:

- [ ] **Zero Failing Tests**: All unit, integration, and verification scripts execute with exit code `0`.
- [ ] **Invariant Conformance**:
  - Explainable scoring verified (all 5 dimensional sub-scores mathematically substantiated).
  - Computer vision and vocal metrics restricted to observable physical indicators.
  - Question reference rubrics properly stored in session records.
  - Sandboxed code execution strictly isolated with timeout limits.
  - Recruiter report secrecy preserved (no admin evaluations exposed to candidates).
- [ ] **Contract Compliance**: Request/response schemas match [`000-shared-contracts.md`](file:///d:/FYP/Code/context/feature-specs/000-shared-contracts.md).
- [ ] **Clean Builds**: Both backend starts cleanly and frontend builds without TypeScript/JSX syntax errors (`npm run build`).
- [ ] **Documentation Sync**: Update [`context/feature-specs/INDEX.md`](file:///d:/FYP/Code/context/feature-specs/INDEX.md) and [`context/progress-tracker.md`](file:///d:/FYP/Code/context/progress-tracker.md).

---

## 2. Automated System Verification Script

Run the automated verification script:
```powershell
python .agents/skills/hiresight-system-verify/scripts/verify_system.py
```

This script checks:
1. Workspace structure and configuration files.
2. Offline model weights (Vosk ASR model in `backend/models/`).
3. Backend dependencies and test scripts.
4. Feature specification consistency and dependency gates.
5. Frontend configuration and package dependencies.

---

## 3. Individual Test Suites

### Run Backend Unit & Validation Tests
```powershell
python .agents/skills/hiresight-backend/scripts/run_backend_tests.py
```

### Run Spec Dependency Gate Verification
```powershell
python .agents/skills/hiresight-spec-workflow/scripts/check_spec_gates.py
```

### Validate Frontend Production Bundle
```powershell
cd d:\FYP\Code\frontend
npm run build
```
