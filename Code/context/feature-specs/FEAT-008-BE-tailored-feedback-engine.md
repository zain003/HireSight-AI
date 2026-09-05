# FEAT-008-BE: Tailored Feedback & Skill Gap Analysis Engine — P1

## Layer
Backend

## Goal
Generate evidence-anchored candidate feedback, identifying technical strengths/weaknesses, coding insights, communication observations, and concrete skill gap remediation roadmaps directly tied to interview results.

## Depends on
`FEAT-007-BE-explainable-scoring-engine.md`

## Context pack
```python
class TailoredFeedback(BaseModel):
    strongest_technical_areas: List[str]
    weakest_technical_areas: List[str]
    coding_analysis_summary: str
    communication_observations: List[str]
    behavioral_observations: List[str]
    missing_role_skills: List[str]
    actionable_improvement_recommendations: List[str]
```

## Provides / Exposes
```python
def generate_tailored_feedback(
    evaluations: List[AnswerEvaluation],
    coding_evaluation: Optional[CodingChallengeEvaluation],
    role_competencies: List[CompetencyWeight],
    vocal_metrics: ObservableVocalMetrics,
    cv_metrics: ObservableCVMetrics
) -> TailoredFeedback: ...
```

## Scope (In)
- Question-level evidence mapping (linking missed concepts directly to questions asked).
- Target role gap analysis (identifying role competencies with score < 60%).
- Concrete improvement suggestions (naming specific technologies, patterns, or practice areas).
- Zero generic boilerplate phrases; all feedback anchored to candidate's actual session data.

## Scope (Out)
- PDF document generation (covered in `FEAT-009-BE`).
- Overall numerical score math (covered in `FEAT-007-BE`).

## Tech / files to touch
- `backend/app/interview/services/feedback_generator.py` [NEW]
- `backend/app/interview/services/recruiter_report.py` [MODIFY]

## Tests to write FIRST
- `test_feedback_identifies_missed_concepts`: Question with missed concept "ACID properties" results in specific database remediation recommendation.
- `test_coding_feedback_mentions_failed_hidden_tests`: Candidate failing hidden tests receives edge-case testing recommendation.
- `test_feedback_non_empty_for_all_sections`: Output contains non-empty lists for all 7 feedback categories.

## Implementation steps
1. Create `backend/app/interview/services/feedback_generator.py` implementing `generate_tailored_feedback`.
2. Extract candidate missed concepts from `AnswerEvaluation.missed_points`.
3. Compare demonstrated competencies against `CompetencyWeight` for the target role to generate `missing_role_skills`.
4. Integrate `TailoredFeedback` into `RecruiterReport` in `recruiter_report.py`.

## Acceptance criteria
- Generated recommendations directly reference concepts or questions from the interview.
- Skill gaps highlight target role requirements that were not demonstrated.
- Zero generic boilerplate text produced.

## Definition of Done
- Unit tests for feedback generation pass 100%.
- Generates complete feedback object in < 150ms.
- Clean lint and Pydantic validation.

## Edge cases to handle
- Candidate scored 100% on everything → provides advanced mastery and leadership recommendations.
- Candidate answered zero questions → returns foundational technical roadmap without crashing.

## Pre-flight check
- Confirm `FEAT-007-VERIFY` passed.

## What's next
- `FEAT-008-VERIFY-tailored-feedback.md`
- `FEAT-009-BE-pdf-report-generator.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-008-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.
