# FEAT-006-BE: Sandboxed Hidden Test Runner & Coding Assessment Engine — P0

## Layer
Backend

## Goal
Implement a secure, isolated multi-language code execution engine that evaluates candidate solutions against both public and secret server-side hidden test cases with strict execution timeouts and memory metrics.

## Depends on
`000-shared-contracts.md`

## Context pack
```python
class TestCaseResult(BaseModel):
    test_id: int
    is_hidden: bool
    passed: bool
    runtime_ms: float
    memory_kb: float
    stdout: Optional[str] = None
    error_message: Optional[str] = None

class CodingChallengeEvaluation(BaseModel):
    challenge_id: str
    language: str
    source_code: str
    compile_success: bool
    public_tests_passed: int
    public_tests_total: int
    hidden_tests_passed: int
    hidden_tests_total: int
    overall_coding_score: float
    execution_time_total_ms: float
    peak_memory_kb: float
    results: List[TestCaseResult]
```

## Provides / Exposes
```python
POST /interview/coding/run-public -> RunPublicCodeResponse
POST /interview/live/{session_id}/submit-coding-challenge -> CodingChallengeEvaluation
```

## Scope (In)
- Subprocess sandbox execution for Python, JavaScript (Node), Java, C++, C.
- Public test runner endpoint for candidate iterative debugging.
- Secret hidden test runner endpoint executing server-stored hidden test suites.
- CPU timeout enforcement (3.0s per test case) and output truncation (max 10KB).
- Coding score calculation combining test case correctness and runtime efficiency.

## Scope (Out)
- In-browser Monaco editor component (covered in `FEAT-006-FE`).
- Final 5-dimension report collation (covered in `FEAT-007-BE`).

## Tech / files to touch
- `backend/app/interview/services/code_execution.py` [MODIFY]
- `backend/app/interview/routes.py` [MODIFY]
- `backend/app/interview/domain/coding_challenges.py` [NEW]

## Tests to write FIRST
- `test_python_solution_passes_all_tests`: Valid Python solution passes all public and hidden test cases.
- `test_infinite_loop_terminates_at_timeout`: Solution with `while True:` terminates in < 3.5s with `TimeoutError`.
- `test_hidden_test_inputs_not_leaked_in_response`: Response object omits `stdin` and `expected_output` for hidden tests.

## Implementation steps
1. Create `backend/app/interview/domain/coding_challenges.py` storing challenge definitions and hidden test suites.
2. Enhance `execute_code` in `code_execution.py` to accept hidden test lists and mask output for hidden cases.
3. Add `POST /interview/live/{session_id}/submit-coding-challenge` route to execute both public and hidden test suites and record `CodingChallengeEvaluation` in the session document.

## Acceptance criteria
- Candidate solutions execute in sandbox and return pass/fail per test case.
- Infinite loops or hanging processes killed within 3.0 seconds.
- Zero leakage of hidden test inputs/outputs in JSON response payloads.

## Definition of Done
- Unit tests for all 5 languages pass 100%.
- Hidden test cases evaluated correctly and persisted in `InterviewSession.coding_results`.
- Zero security escapes or open file handle leaks.

## Edge cases to handle
- Code produces 50MB of print output → truncates stdout at 10KB without server crash.
- Syntax or compilation error → returns `compile_success: false` and compiler stderr immediately.

## Pre-flight check
- Confirm `000-shared-contracts.md` is approved.

## What's next
- `FEAT-006-FE-coding-assessment-ui.md`
- `FEAT-006-VERIFY-coding-sandbox.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-006-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.
