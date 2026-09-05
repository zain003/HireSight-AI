# FEAT-006-FE: Coding Challenge Workspace UI & Test Runner — P1

## Layer
Frontend

## Goal
Provide a full-featured online coding environment with syntax highlighting, language selector, public test runner with console output, and submission flow for final evaluation.

## Depends on
`FEAT-006-BE-coding-sandbox-hidden-tests.md`

## Context pack
```typescript
export interface RunCodeResponse {
  compile_success: boolean;
  all_passed: boolean;
  results: {
    test_id: number;
    is_hidden: boolean;
    passed: boolean;
    runtime_ms: number;
    stdout?: string;
    error_message?: string;
  }[];
}
```

## Consumes
- `POST /interview/coding/run-public`
- `POST /interview/live/{session_id}/submit-coding-challenge`

## Scope (In)
- Multi-language code editor (Python, JavaScript, Java, C++, C) with starter boilerplate.
- "Run Public Tests" button displaying per-test stdout, expected vs actual outputs, and execution time.
- "Submit Solution" button triggering server-side hidden test suite and advancing interview stage.
- Execution timer and memory badge.

## Scope (Out)
- Backend code compilation and execution isolation (covered in `FEAT-006-BE`).
- Overall interview score aggregation (covered in `FEAT-007-BE`).

## Tech / files to touch
- `frontend/src/components/Interview/CodingWorkspace.jsx` [MODIFY]
- `frontend/src/services/interviewService.js` [MODIFY]

## Tests to write FIRST
- `test_language_switch_updates_starter_code`: Changing language from Python to JS updates editor template.
- `test_run_public_tests_renders_results`: Clicking run renders pass/fail status for each public test.
- `test_submit_solution_triggers_completion`: Submitting solution calls submit endpoint and emits completion event.

## Implementation steps
1. Enhance `CodingWorkspace.jsx` to render test case tabs (Public Test 1, Public Test 2).
2. Wire "Run Tests" to `POST /interview/coding/run-public`.
3. Wire "Submit Challenge" to `POST /interview/live/{session_id}/submit-coding-challenge` with loading spinner.

## Acceptance criteria
- Candidate can write code, run public tests, and view console outputs.
- Test runner shows green/red status badges for each executed public test.
- Submitting final solution transitions interview state cleanly to the next stage.

## Definition of Done
- Component tests pass with 100% success rate.
- UI renders cleanly across desktop screen resolutions (>1024px).
- Zero uncaught exceptions during syntax error runs.

## Edge cases to handle
- Code execution times out → UI displays "Execution Timed Out (3.0s limit)" alert.
- Network disconnection during run → enables retry button without losing candidate code.

## Pre-flight check
- Confirm `FEAT-006-BE` passed all verification steps.

## What's next
- `FEAT-006-VERIFY-coding-sandbox.md`
- `FEAT-007-BE-explainable-scoring-engine.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-006-FE] — [ambiguity] — [assumption]`.
3. Stop and flag if API contract changes.
