"""5-Dimensional Explainable Scoring domain models for HireSIGHT.

Defines canonical weights, candidate fit status classifications, and the 5-dimensional
scoring model with full mathematical audit capabilities.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScoringWeights:
    """Canonical weights for the explainable scoring model (Role Fit removed).

    Weights sum exactly to 1.00 (100%):
    - Technical Knowledge: 45%
    - Coding Ability: 25%
    - Communication: 15%
    - Behavioral Indicators: 15%
    """

    TECHNICAL_KNOWLEDGE = 0.45
    CODING_ABILITY = 0.25
    ROLE_FIT = 0.0
    COMMUNICATION = 0.15
    BEHAVIORAL_INDICATORS = 0.15

    @classmethod
    def as_dict(cls) -> Dict[str, float]:
        return {
            "technical_knowledge": cls.TECHNICAL_KNOWLEDGE,
            "coding_ability": cls.CODING_ABILITY,
            "communication": cls.COMMUNICATION,
            "behavioral_indicators": cls.BEHAVIORAL_INDICATORS,
        }

    @classmethod
    def total_weight(cls) -> float:
        return sum(cls.as_dict().values())


class CandidateFitStatus(str, Enum):
    """Deterministic candidate role-alignment fit classification."""

    STRONG_FIT = "Strong Fit"        # >= 85 overall, >= 80 tech & coding
    POTENTIAL_FIT = "Potential Fit"  # 70-84 overall
    NEEDS_GROWTH = "Needs Growth"    # 55-69 overall
    NOT_A_FIT = "Not a Fit"          # < 55 overall


class FiveDimensionScores(BaseModel):
    """Transparent scoring breakdown with mathematical audit trail."""

    technical_knowledge_score: float = Field(
        ..., ge=0.0, le=100.0, description="Technical knowledge and depth score (Weight: 45%)"
    )
    coding_ability_score: float = Field(
        ..., ge=0.0, le=100.0, description="Sandboxed code execution & test score (Weight: 25%)"
    )
    role_fit_score: Optional[float] = Field(
        default=0.0, ge=0.0, le=100.0, description="Deprecated / 0% weight"
    )
    communication_score: float = Field(
        ..., ge=0.0, le=100.0, description="Verbal & acoustic communication score (Weight: 15%)"
    )
    behavioral_indicators_score: float = Field(
        ..., ge=0.0, le=100.0, description="Observable computer vision dynamics score (Weight: 15%)"
    )
    overall_composite_score: float = Field(
        ..., ge=0.0, le=100.0, description="Weighted composite score across active dimensions (0-100)"
    )
    fit_status: CandidateFitStatus = Field(
        ..., description="Deterministic multi-variable candidate fit classification"
    )
    scoring_formula_audit: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete mathematical audit trail including formulas, raw inputs, and normalized terms",
    )


class TailoredFeedback(BaseModel):
    """Evidence-anchored tailored candidate feedback across technical, coding, communication, and role gaps."""

    strongest_technical_areas: List[str] = Field(
        default_factory=list,
        description="Technical concepts and competencies where candidate demonstrated mastery",
    )
    weakest_technical_areas: List[str] = Field(
        default_factory=list,
        description="Technical concepts and questions where candidate showed gaps or missed key points",
    )
    coding_analysis_summary: str = Field(
        default="",
        description="Concise summary of coding performance, test pass rates, and runtime/edge-case handling",
    )
    communication_observations: List[str] = Field(
        default_factory=list,
        description="Objective observations on speaking rate, pause ratios, and clarity (physical metrics only)",
    )
    behavioral_observations: List[str] = Field(
        default_factory=list,
        description="Objective observations on gaze stability, head pose, blink frequency, and frame presence",
    )
    missing_role_skills: List[str] = Field(
        default_factory=list,
        description="Role-specific competencies and concepts with sub-60% demonstrated coverage",
    )
    actionable_improvement_recommendations: List[str] = Field(
        default_factory=list,
        description="Concrete, technology-specific remediation roadmap and practice areas",
    )

