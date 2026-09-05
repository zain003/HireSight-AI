# FEAT-002-BE: Rubric-Backed Question Generation Engine — P0

## Layer
Backend

## Goal
Generate personalized, stage-paced interview questions that store pre-computed reference answers, expected technical concepts, and grading rubrics alongside every question for deterministic, explainable evaluation.

## Depends on
`FEAT-001-BE-role-competency-mapping.md`

## Context pack
```python
class QuestionStage(str, Enum):
    ICEBREAKER = "icebreaker"
    CORE_TECHNICAL = "core_technical"
    DEEP_DIVE = "deep_dive"
    CODING = "coding"
    CLOSING = "closing"

class QuestionRubric(BaseModel):
    reference_answer: str
    key_concepts_expected: List[str]
    depth_criteria: Dict[str, str]
    scoring_guide: Dict[str, float]

class InterviewQuestion(BaseModel):
    question_id: str
    question_index: int
    stage: QuestionStage
    competency_area: str
    difficulty: SeniorityLevel
    question_text: str
    rubric: QuestionRubric
```

## Provides / Exposes
```python
async def generate_rubric_backed_plan(
    job_role: StandardRole,
    seniority: SeniorityLevel,
    candidate_skills: List[str],
    candidate_projects: List[Dict],
    total_questions: int = 6
) -> List[InterviewQuestion]: ...
```

## Scope (In)
- Question generation combining role competency weights, candidate resume details, and target difficulty.
- Every question generated must include `reference_answer`, `key_concepts_expected`, and `depth_criteria`.
- Deterministic stage sequencing: 1 Icebreaker → 3 Core Technical / Deep Dive → 1 Coding → 1 Closing.
- Fallback question bank with complete rubrics if LLM provider is unavailable.

## Scope (Out)
- Real-time speech transcription (covered in `FEAT-005-BE`).
- Real-time video/audio delivery (covered in `FEAT-003-BE`).

## Tech / files to touch
- `backend/app/interview/services/llm_service.py` [MODIFY]
- `backend/app/interview/domain/interview_models.py` [MODIFY]
- `backend/app/interview/application/interview_service.py` [MODIFY]

## Tests to write FIRST
- `test_plan_contains_required_stages`: Generated plan contains `icebreaker`, `core_technical`, `coding`, and `closing`.
- `test_every_question_has_non_empty_rubric`: Every question object contains non-empty `reference_answer` and `key_concepts_expected`.
- `test_fallback_plan_on_llm_error`: When LLM call throws exception, generator returns valid fallback plan with complete rubrics.

## Implementation steps
1. Extend `InterviewQuestion` and `QuestionRubric` schemas in `backend/app/interview/domain/interview_models.py`.
2. Update prompt in `backend/app/interview/services/llm_service.py` to require JSON output with reference answers and rubrics for each stage.
3. Update `_fallback_question_plan` to populate comprehensive reference answers and expected concept lists for all fallback questions.
4. Update `InterviewService.start_interview` to persist rubrics in `InterviewSession.questions`.

## Acceptance criteria
- Generated interview plan contains exactly the requested number of questions.
- 100% of generated questions have valid `rubric` containing `reference_answer` and at least 2 `key_concepts_expected`.
- If external LLM times out, fallback question plan generates with valid rubrics in < 50ms.

## Definition of Done
- Unit tests pass with 100% success rate.
- Database schema stores and loads rubrics accurately without serialization loss.
- Zero type/lint errors.

## Edge cases to handle
- Candidate has no projects on resume → CV deep dive falls back to core technical competency without error.
- LLM outputs malformed JSON rubric → parser falls back to default role rubric without failing session start.

## Pre-flight check
- Confirm `FEAT-001-VERIFY` passed.

## What's next
- `FEAT-002-VERIFY-question-engine.md`
- `FEAT-003-BE-session-state-sync.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-002-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if data models in `000-shared-contracts.md` require modification.
