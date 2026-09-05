# FEAT-007-BE: 5-Dimensional Explainable Scoring Engine — P0

## Layer
Backend

## Goal
Implement a transparent, explainable 5-dimensional scoring model combining Technical Knowledge (35%), Coding Ability (20%), Role Fit (15%), Communication (15%), and Behavioral Indicators (15%) with a complete mathematical audit trail.

## Depends on
`FEAT-001-BE`, `FEAT-002-BE`, `FEAT-004-BE`, `FEAT-005-BE`, `FEAT-006-BE`

## Context pack
```python
class FiveDimensionScores(BaseModel):
    technical_knowledge_score: float
    coding_ability_score: float
    role_fit_score: float
    communication_score: float
    behavioral_indicators_score: float
    overall_composite_score: float
    fit_status: CandidateFitStatus
    scoring_formula_audit: Dict[str, Any]
```

## Provides / Exposes
```python
def calculate_five_dimension_scores(
    evaluations: List[AnswerEvaluation],
    coding_results: List[Dict],
    role_fit_data: Dict,
    vocal_metrics: List[ObservableVocalMetrics],
    cv_metrics: List[ObservableCVMetrics]
) -> FiveDimensionScores: ...
```

## Scope (In)
- Exact mathematical calculation of all 5 dimensions (0-100 scale).
- Weighted composite calculation: `0.35*Tech + 0.20*Coding + 0.15*RoleFit + 0.15*Comm + 0.15*Beh`.
- Deterministic Fit Status classification: Strong Fit, Potential Fit, Needs Growth, Not a Fit.
- Generation of `scoring_formula_audit` object containing weights, raw sub-scores, and calculation steps.

## Scope (Out)
- Feedback narrative phrasing (covered in `FEAT-008-BE`).
- PDF layout compilation (covered in `FEAT-009-BE`).

## Tech / files to touch
- `backend/app/interview/services/recruiter_report.py` [MODIFY]
- `backend/app/interview/services/analysis_service.py` [MODIFY]
- `backend/app/interview/domain/scoring_models.py` [NEW]

## Tests to write FIRST
- `test_weights_sum_to_one`: 0.35 + 0.20 + 0.15 + 0.15 + 0.15 == 1.00.
- `test_composite_score_calculation`: Given scores [80, 90, 70, 85, 90], composite is exactly `81.75`.
- `test_strong_fit_thresholds`: Overall >= 85 and Tech >= 80 yields `Strong Fit`.
- `test_scoring_audit_contains_all_steps`: Audit dictionary contains input breakdown for all 5 dimensions.

## Implementation steps
1. Create `scoring_models.py` with `FiveDimensionScores`, `CandidateFitStatus`, and `ScoringWeights`.
2. Implement `calculate_five_dimension_scores` in `recruiter_report.py` replacing legacy 4-category logic.
3. Populate `scoring_formula_audit` tracking every mathematical term and its input source.
4. Save 5-dimensional scores to `InterviewSession.aggregate_scores` and `InterviewSession.recruiter_report`.

## Acceptance criteria
- Final overall composite score matches the exact weighted sum of the 5 dimensions.
- Every score has an audit record showing source values, weights, and normalization logic.
- Fit status is determined strictly by defined multi-variable thresholds.

## Definition of Done
- Unit tests for scoring engine pass 100%.
- Scoring audit verified as mathematically transparent and reproducible.
- Zero type errors or missing dictionary keys.

## Edge cases to handle
- Candidate skipped coding challenge → coding score defaults to 0.0 without crashing.
- No video frames available → behavioral indicator scores 0.0 with audit note.

## Pre-flight check
- Confirm `FEAT-004-VERIFY`, `FEAT-005-VERIFY`, and `FEAT-006-VERIFY` passed.

## What's next
- `FEAT-007-VERIFY-explainable-scoring.md`
- `FEAT-008-BE-tailored-feedback-engine.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Log assumption in `specs/DEVIATIONS.md` as: `[FEAT-007-BE] — [ambiguity] — [assumption]`.
3. Stop and flag if scoring weights in `000-shared-contracts.md` require modification.
