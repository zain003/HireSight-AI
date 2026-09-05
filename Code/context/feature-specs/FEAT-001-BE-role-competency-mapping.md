# FEAT-001-BE: Role & Competency Mapping Engine — P0

## Layer
Backend

## Goal
Provide standardized job role taxonomy, automated seniority level inference from candidate profile experience, and competency-cluster weighting for interview planning.

## Depends on
`000-shared-contracts.md`

## Context pack
```python
class SeniorityLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"

class StandardRole(str, Enum):
    FRONTEND_ENGINEER = "frontend_engineer"
    BACKEND_ENGINEER = "backend_engineer"
    FULLSTACK_ENGINEER = "fullstack_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    ML_ENGINEER = "ml_engineer"
    QA_AUTOMATION_ENGINEER = "qa_automation_engineer"

class CompetencyWeight(BaseModel):
    competency_area: str
    importance_weight: float
    required_concepts: List[str]
```

## Provides / Exposes
```python
def infer_seniority_level(experience_years: Optional[int]) -> SeniorityLevel: ...
def get_role_competency_matrix(role: StandardRole) -> List[CompetencyWeight]: ...
def map_profile_to_role_fit(profile_skills: List[str], role: StandardRole) -> Dict[str, Any]: ...
```
Endpoint: `GET /interview/config/roles` → Returns supported roles, default seniority, and competency clusters.

## Scope (In)
- Standardized taxonomy of 7 tech roles with defined competency weights.
- Seniority classification logic based on verified years of experience.
- Matching extracted profile skills against role-required competency concepts.

## Scope (Out)
- Pre-interview UI configuration screen (covered in `FEAT-001-FE-interview-config-role-select.md`).
- Question generation logic (covered in `FEAT-002-BE-question-engine-rubrics.md`).

## Tech / files to touch
- `backend/app/interview/domain/role_taxonomy.py` [NEW]
- `backend/app/interview/services/role_mapping_service.py` [NEW]
- `backend/app/interview/routes.py` [MODIFY]

## Tests to write FIRST
- `test_infer_seniority_entry`: Assert 1 year returns `SeniorityLevel.ENTRY`.
- `test_infer_seniority_senior`: Assert 6 years returns `SeniorityLevel.SENIOR`.
- `test_role_competency_weights_sum_to_one`: For each role in `StandardRole`, assert sum of `importance_weight` equals `1.0`.
- `test_get_roles_endpoint_returns_200`: Assert `GET /interview/config/roles` returns 200 with all 7 roles.

## Implementation steps
1. Create `backend/app/interview/domain/role_taxonomy.py` defining role enum and hardcoded competency matrices with weights summing to 1.0.
2. Create `backend/app/interview/services/role_mapping_service.py` with `infer_seniority_level` and `map_profile_to_role_fit`.
3. Add `GET /interview/config/roles` endpoint in `backend/app/interview/routes.py` returning available roles, competency clusters, and inferred seniority.

## Acceptance criteria
- `infer_seniority_level(None)` returns `SeniorityLevel.ENTRY`.
- `infer_seniority_level(4)` returns `SeniorityLevel.MID`.
- All 7 roles in `StandardRole` have defined competency matrices where weights sum to `1.0`.
- `GET /interview/config/roles` returns HTTP 200 with complete role taxonomy.

## Definition of Done
- Unit tests for role mapping pass with 100% success rate.
- `GET /interview/config/roles` response validated against Pydantic schema.
- Zero lint/typecheck errors.

## Edge cases to handle
- Candidate profile has `experience_years = 0` or `None` → defaults to `ENTRY`.
- Candidate selected role with 0 overlapping skills → returns 0.0 match score without crashing.

## Pre-flight check
- Confirm `000-shared-contracts.md` is approved.

## What's next
- `FEAT-001-FE-interview-config-role-select.md`
- `FEAT-001-VERIFY-role-mapping.md`

## Ambiguity Resolution Protocol
1. Do NOT silently guess.
2. Make the smallest reasonable assumption needed to proceed.
3. Log in `specs/DEVIATIONS.md` as: `[FEAT-001-BE] — [ambiguity] — [assumption]`.
4. Stop and flag if data models in `000-shared-contracts.md` require modification.
