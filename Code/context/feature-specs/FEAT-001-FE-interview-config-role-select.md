# FEAT-001-FE: Pre-Interview Configuration & Role Selection UI — P0

## Layer
Frontend

## Goal
Provide an intuitive pre-interview setup screen for candidates to review extracted profile data, select or confirm their target job role, adjust difficulty level, and preview the structured interview agenda.

## Depends on
`FEAT-001-BE-role-competency-mapping.md`

## Context pack
```typescript
export type SeniorityLevel = 'entry' | 'mid' | 'senior' | 'lead';
export type StandardRole =
  | 'frontend_engineer'
  | 'backend_engineer'
  | 'fullstack_engineer'
  | 'devops_engineer'
  | 'data_engineer'
  | 'ml_engineer'
  | 'qa_automation_engineer';

export interface RoleConfigOption {
  role_id: StandardRole;
  display_name: string;
  inferred_seniority: SeniorityLevel;
  competency_areas: string[];
}
```

## Consumes
`GET /interview/config/roles` → Returns `{ roles: RoleConfigOption[] }`

## Scope (In)
- Interactive role selection dropdown/cards with display names and competency tags.
- Seniority level selector (Entry, Mid, Senior, Lead) pre-populated with inferred seniority.
- Coding language preference selector (Python, JavaScript, Java, C++, C).
- Visual interview agenda preview showing stages (Icebreaker → Technical → Coding → Closing).

## Scope (Out)
- Live interview video stream and question delivery (covered in `FEAT-003-FE`).
- Backend role mapping engine (covered in `FEAT-001-BE`).

## Tech / files to touch
- `frontend/src/pages/interview-setup.jsx` [NEW]
- `frontend/src/components/Interview/InterviewConfigCard.jsx` [NEW]
- `frontend/src/services/interviewService.js` [MODIFY]

## Tests to write FIRST
- `test_renders_role_options`: Renders all roles received from API.
- `test_seniority_selection_updates_state`: Changing seniority selector updates local configuration state.
- `test_start_interview_submits_config`: Clicking "Start Assessment" posts configured role and seniority to `/interview/live/start`.

## Implementation steps
1. Add `getRoleConfigs()` in `frontend/src/services/interviewService.js`.
2. Create `InterviewConfigCard.jsx` displaying role selection, seniority radio buttons, and language dropdown.
3. Create `interview-setup.jsx` page fetching role configurations on mount, binding user selections, and navigating to `/interview` on submit.

## Acceptance criteria
- Candidate can select any of the 7 supported roles.
- Changing difficulty level updates the displayed stage durations and question count.
- Submitting configuration navigates to live interview screen with valid session parameters.

## Definition of Done
- Component tests pass with 100% success rate.
- Responsive UI rendering cleanly on mobile and desktop viewports.
- No React console warnings or unhandled promise rejections.

## Edge cases to handle
- Profile missing skills → Role selector prompts candidate to select role manually.
- Network failure loading `/interview/config/roles` → Displays retry banner.

## Pre-flight check
- Confirm `FEAT-001-BE` passes all acceptance criteria.

## What's next
- `FEAT-001-VERIFY-role-mapping.md`
- `FEAT-002-BE-question-engine-rubrics.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-001-FE] — [ambiguity] — [assumption]`.
3. Stop and flag if data contract with backend changes.
