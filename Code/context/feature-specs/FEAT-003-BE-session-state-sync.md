# FEAT-003-BE: Session State Synchronization & Dynamic Follow-up Engine — P0

## Layer
Backend

## Goal
Provide a resilient, deterministic interview state engine that tracks current/remaining questions, supports safe insertion of adaptive follow-up questions without index corruption, and enables session recovery on reload.

## Depends on
`FEAT-002-BE-question-engine-rubrics.md`

## Context pack
```python
class InterviewSessionState(BaseModel):
    session_id: str
    current_question_index: int
    total_questions: int
    completed_evaluations_count: int
    current_question: Optional[Dict[str, Any]]
    status: str
```

## Provides / Exposes
```python
GET /interview/live/{session_id}/state -> InterviewSessionState
POST /interview/live/{session_id}/answer -> SubmitAnswerResponse
```

## Scope (In)
- Dynamic insertion of follow-up questions with explicit parent-child linking (`parent_question_id`).
- Strict index re-normalization so `current_question_index` accurately tracks progression.
- Session state endpoint returning current question, answered count, and completed evaluation summaries.

## Scope (Out)
- Browser audio recording hooks (covered in `FEAT-003-FE`).
- Computer vision landmark extraction (covered in `FEAT-004-BE`).

## Tech / files to touch
- `backend/app/interview/application/interview_service.py` [MODIFY]
- `backend/app/interview/routes.py` [MODIFY]
- `backend/app/interview/models.py` [MODIFY]

## Tests to write FIRST
- `test_session_state_endpoint_returns_current_question`: Assert `GET /state` returns question matching `current_question_index`.
- `test_follow_up_insertion_renumbers_subsequent_questions`: When follow-up is inserted at index 2, question 3 becomes question 4.
- `test_max_follow_up_limit_enforced`: Cannot add more than 3 follow-ups per stage or 9 total per interview.

## Implementation steps
1. Add `GET /interview/live/{session_id}/state` endpoint to `backend/app/interview/routes.py`.
2. Update `InterviewService.process_answer` to assign unique IDs to follow-up questions and safely insert them into `session.questions` with renumbered indices.
3. Update session serialization to ensure atomic updates in MongoDB when answer evaluation completes.

## Acceptance criteria
- `GET /interview/live/{session_id}/state` returns accurate current question and completion count.
- Dynamic follow-up insertion preserves total question order with sequential zero-based indices.
- Session status transitions to `completed` upon evaluating the final question.

## Definition of Done
- Unit tests for session sync and follow-up limits pass 100%.
- Concurrent answer submissions for same session are rejected with HTTP 409 conflict.
- Clean lint and strict type annotations.

## Edge cases to handle
- Candidate submits answer for already answered question → returns existing evaluation or HTTP 400.
- Browser disconnects mid-interview → reconnecting to `/state` resumes at exact uncompleted question.

## Pre-flight check
- Confirm `FEAT-002-VERIFY` passed.

## What's next
- `FEAT-003-FE-interview-resilience-input.md`
- `FEAT-003-VERIFY-session-sync.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-003-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.
