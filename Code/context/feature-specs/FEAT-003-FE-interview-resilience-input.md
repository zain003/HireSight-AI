# FEAT-003-FE: Interview Resilience & Input Fallback UI — P0

## Layer
Frontend

## Goal
Enhance the live interview UI to automatically recover session state on page refresh, provide a seamless voice/text input toggle for microphone failures, and maintain synchronized question progression during dynamic follow-ups.

## Depends on
`FEAT-003-BE-session-state-sync.md`

## Context pack
```typescript
export interface InterviewSessionState {
  session_id: string;
  current_question_index: number;
  total_questions: number;
  completed_evaluations_count: number;
  current_question?: {
    question_id: string;
    question_index: number;
    stage: string;
    question_text: string;
  };
  status: string;
}
```

## Consumes
- `GET /interview/live/{session_id}/state`
- `POST /interview/live/{session_id}/answer`

## Scope (In)
- On-mount session recovery: call `GET /state` to restore current question and previous answer count on browser reload.
- Dual input mode: interactive switch between Voice (WebRTC audio recording) and Text (Markdown response textarea).
- Smooth progression indicators displaying remaining questions and follow-up badges.

## Scope (Out)
- Code editor interface (covered in `FEAT-006-FE`).
- Computer vision canvas landmark rendering (covered in `FEAT-004-BE`).

## Tech / files to touch
- `frontend/src/pages/interview.jsx` [MODIFY]
- `frontend/src/components/Interview/InputModeSelector.jsx` [NEW]
- `frontend/src/services/interviewService.js` [MODIFY]

## Tests to write FIRST
- `test_session_mount_restores_state`: On page reload with existing `sessionId` query param, fetches state and renders current question.
- `test_input_toggle_switches_input_component`: Toggling to "Text Input" renders textarea and disables microphone recording requirement.
- `test_follow_up_display_badge`: When returned response has `follow_up_question`, displays follow-up alert banner.

## Implementation steps
1. Add `fetchSessionState(sessionId)` to `interviewService.js`.
2. Create `InputModeSelector.jsx` with Voice vs Text mode buttons.
3. Update `interview.jsx` to load session state on mount, support text submission payload, and display dynamic follow-up indicators.

## Acceptance criteria
- Refreshing browser at question 3 restores question 3 with timer intact.
- Candidate can submit text answers if microphone is unavailable.
- Dynamic follow-up questions display a distinct "Follow-up" badge.

## Definition of Done
- Component tests pass with 100% success rate.
- Verified in mobile and desktop viewports.
- No unhandled promise rejections on network retries.

## Edge cases to handle
- Candidate switches input mode mid-answer → preserves current transcript/text draft.
- Session already completed → automatically redirects to interview completion view.

## Pre-flight check
- Confirm `FEAT-003-BE` passed all verification steps.

## What's next
- `FEAT-003-VERIFY-session-sync.md`
- `FEAT-004-BE-cv-facial-movement-engine.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-003-FE] — [ambiguity] — [assumption]`.
3. Stop and flag if API contract changes.
