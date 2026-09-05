# 000-shared-contracts.md — Single Source of Truth

This file defines the shared data models, type definitions, API envelopes, and cross-cutting conventions across the HireSIGHT platform. All feature specs reference this file.

---

## Core Domain Models (Python Pydantic & TypeScript)

### 1. Seniority Level & Role Taxonomy
```python
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class SeniorityLevel(str, Enum):
    ENTRY = "entry"       # 0-2 years
    MID = "mid"           # 2-5 years
    SENIOR = "senior"     # 5-8 years
    LEAD = "lead"         # 8+ years

class StandardRole(str, Enum):
    FRONTEND_ENGINEER = "frontend_engineer"
    BACKEND_ENGINEER = "backend_engineer"
    FULLSTACK_ENGINEER = "fullstack_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    ML_ENGINEER = "ml_engineer"
    QA_AUTOMATION_ENGINEER = "qa_automation_engineer"

class CompetencyWeight(BaseModel):
    competency_area: str          # e.g., "System Design", "Concurrency", "Database Design"
    importance_weight: float      # 0.0 to 1.0 (sums to 1.0 per role)
    required_concepts: List[str]
```

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

export interface CompetencyWeight {
  competency_area: string;
  importance_weight: number;
  required_concepts: string[];
}
```

---

### 2. Question with Reference Rubric Model
```python
class QuestionStage(str, Enum):
    ICEBREAKER = "icebreaker"
    CORE_TECHNICAL = "core_technical"
    DEEP_DIVE = "deep_dive"
    CODING = "coding"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"

class QuestionRubric(BaseModel):
    reference_answer: str
    key_concepts_expected: List[str]
    depth_criteria: Dict[str, str]       # {"basic": "...", "intermediate": "...", "advanced": "..."}
    scoring_guide: Dict[str, float]      # {"relevance_max": 30, "depth_max": 40, "accuracy_max": 30}

class InterviewQuestion(BaseModel):
    question_id: str
    question_index: int
    stage: QuestionStage
    competency_area: str
    difficulty: SeniorityLevel
    question_text: str
    rubric: QuestionRubric
    coding_challenge_id: Optional[str] = None
```

```typescript
export type QuestionStage = 'icebreaker' | 'core_technical' | 'deep_dive' | 'coding' | 'closing' | 'follow_up';

export interface QuestionRubric {
  reference_answer: string;
  key_concepts_expected: string[];
  depth_criteria: Record<string, string>;
  scoring_guide: Record<string, number>;
}

export interface InterviewQuestion {
  question_id: string;
  question_index: int;
  stage: QuestionStage;
  competency_area: string;
  difficulty: SeniorityLevel;
  question_text: string;
  rubric: QuestionRubric;
  coding_challenge_id?: string;
}
```

---

### 3. Observable Computer Vision & Vocal Metrics
```python
class ObservableCVMetrics(BaseModel):
    gaze_stability_ratio: float      # 0-100 (percentage of frames looking at screen center)
    head_pose_variance: float        # 0-100 (inverse of angular variance in pitch/yaw/roll)
    facial_movement_dynamics: float  # 0-100 (measured micro-movement dynamics)
    frame_presence_ratio: float      # 0-100 (face detected frame ratio)
    blink_frequency_cpm: float       # Blinks per minute
    observable_flags: List[str]      # Observable physical anomalies only

class ObservableVocalMetrics(BaseModel):
    speaking_rate_wpm: float         # Words per minute (conversational norm: 120-160)
    pause_duration_ratio: float      # Total pause duration / total answer duration
    pitch_semitone_variance: float   # F0 dynamic range in semitones
    vocal_energy_rms: float          # Root Mean Square energy stability
    speech_clarity_score: float      # 0-100
    acoustic_flags: List[str]        # Measurable acoustic anomalies only
```

```typescript
export interface ObservableCVMetrics {
  gaze_stability_ratio: number;
  head_pose_variance: number;
  facial_movement_dynamics: number;
  frame_presence_ratio: number;
  blink_frequency_cpm: number;
  observable_flags: string[];
}

export interface ObservableVocalMetrics {
  speaking_rate_wpm: number;
  pause_duration_ratio: number;
  pitch_semitone_variance: number;
  vocal_energy_rms: number;
  speech_clarity_score: number;
  acoustic_flags: string[];
}
```

---

### 4. Sandboxed Coding Assessment Model
```python
class TestCaseResult(BaseModel):
    test_id: int
    is_hidden: bool
    passed: bool
    runtime_ms: float
    memory_kb: float
    stdout: Optional[str] = None     # Included ONLY for public test cases
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
    overall_coding_score: float      # 0-100
    execution_time_total_ms: float
    peak_memory_kb: float
    results: List[TestCaseResult]
```

```typescript
export interface TestCaseResult {
  test_id: number;
  is_hidden: boolean;
  passed: boolean;
  runtime_ms: number;
  memory_kb: number;
  stdout?: string;
  error_message?: string;
}

export interface CodingChallengeEvaluation {
  challenge_id: string;
  language: string;
  source_code: string;
  compile_success: boolean;
  public_tests_passed: number;
  public_tests_total: number;
  hidden_tests_passed: number;
  hidden_tests_total: number;
  overall_coding_score: number;
  execution_time_total_ms: number;
  peak_memory_kb: number;
  results: TestCaseResult[];
}
```

---

### 5. 5-Dimensional Explainable Scoring Model
```python
class ScoringWeights:
    TECHNICAL_KNOWLEDGE = 0.35
    CODING_ABILITY = 0.20
    ROLE_FIT = 0.15
    COMMUNICATION = 0.15
    BEHAVIORAL_INDICATORS = 0.15

class CandidateFitStatus(str, Enum):
    STRONG_FIT = "Strong Fit"        # >= 85 overall, >= 80 tech & coding
    POTENTIAL_FIT = "Potential Fit"  # 70-84 overall
    NEEDS_GROWTH = "Needs Growth"    # 55-69 overall
    NOT_A_FIT = "Not a Fit"          # < 55 overall

class FiveDimensionScores(BaseModel):
    technical_knowledge_score: float # 0-100 (Weight: 35%)
    coding_ability_score: float      # 0-100 (Weight: 20%)
    role_fit_score: float            # 0-100 (Weight: 15%)
    communication_score: float       # 0-100 (Weight: 15%)
    behavioral_indicators_score: float # 0-100 (Weight: 15%)
    overall_composite_score: float   # 0-100
    fit_status: CandidateFitStatus
    scoring_formula_audit: Dict[str, Any]
```

```typescript
export type CandidateFitStatus = 'Strong Fit' | 'Potential Fit' | 'Needs Growth' | 'Not a Fit';

export interface FiveDimensionScores {
  technical_knowledge_score: number;
  coding_ability_score: number;
  role_fit_score: number;
  communication_score: number;
  behavioral_indicators_score: number;
  overall_composite_score: number;
  fit_status: CandidateFitStatus;
  scoring_formula_audit: Record<string, any>;
}
```

---

## Standard API Response Envelope

```python
class APIResponseEnvelope(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str
```

```typescript
export interface APIResponseEnvelope<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}
```
