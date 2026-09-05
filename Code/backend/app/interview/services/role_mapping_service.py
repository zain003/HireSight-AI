"""Service for role taxonomy, seniority inference, and profile competency mapping."""

import re
from typing import Any, Dict, List, Optional, Set

from app.interview.domain.role_taxonomy import (
    ROLE_COMPETENCY_MATRICES,
    ROLE_METADATA_REGISTRY,
    CompetencyWeight,
    SeniorityLevel,
    StandardRole,
    get_role_competency_matrix,
)


def infer_seniority_level(experience_years: Optional[int]) -> SeniorityLevel:
    """Infer candidate seniority level based on verified years of experience.

    Mapping Rules:
    - None / <= 2 years: ENTRY
    - 3 - 5 years: MID
    - 6 - 8 years: SENIOR
    - > 8 years: LEAD
    """
    if experience_years is None or experience_years <= 2:
        return SeniorityLevel.ENTRY
    elif experience_years <= 5:
        return SeniorityLevel.MID
    elif experience_years <= 8:
        return SeniorityLevel.SENIOR
    else:
        return SeniorityLevel.LEAD


def _normalize_skill(skill_str: str) -> str:
    """Normalize skill string for robust fuzzy matching."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s+#.]", " ", skill_str.lower())
    return " ".join(cleaned.split())


def _concept_matches(profile_skill_norm: str, concept_norm: str) -> bool:
    """Check whether a profile skill matches or intersects a required concept."""
    if profile_skill_norm == concept_norm:
        return True
    if profile_skill_norm in concept_norm or concept_norm in profile_skill_norm:
        # Check token-level containment if string is longer than 2 chars
        if len(profile_skill_norm) > 2 and len(concept_norm) > 2:
            return True
    # Token intersection check
    profile_tokens = set(profile_skill_norm.split())
    concept_tokens = set(concept_norm.split())
    # Exclude common stop words
    stopwords = {"and", "or", "the", "in", "for", "with", "of", "a", "an", "to"}
    meaningful_profile = profile_tokens - stopwords
    meaningful_concept = concept_tokens - stopwords
    return bool(meaningful_profile and (meaningful_profile & meaningful_concept))


def map_profile_to_role_fit(
    profile_skills: List[str], role: StandardRole
) -> Dict[str, Any]:
    """Map candidate profile skills against the competency matrix of a target role.

    Returns overall match score (0.0 - 100.0), per-competency coverage,
    matched concepts, and missing concepts.
    """
    matrix: List[CompetencyWeight] = get_role_competency_matrix(role)
    if not matrix:
        return {
            "role": role.value if isinstance(role, StandardRole) else str(role),
            "overall_fit_score": 0.0,
            "competency_breakdown": [],
            "matched_skills": [],
            "missing_concepts": [],
            "total_required_concepts": 0,
            "total_matched_concepts": 0,
        }

    normalized_profile_skills = [_normalize_skill(s) for s in (profile_skills or []) if s]

    total_weighted_score = 0.0
    competency_breakdown: List[Dict[str, Any]] = []
    all_matched_concepts: Set[str] = set()
    all_missing_concepts: List[str] = []
    total_required = 0
    total_matched = 0

    for item in matrix:
        required_concepts = item.required_concepts or []
        total_required += len(required_concepts)
        
        area_matched_concepts: List[str] = []
        area_missing_concepts: List[str] = []

        for concept in required_concepts:
            concept_norm = _normalize_skill(concept)
            matched = any(
                _concept_matches(ps, concept_norm)
                for ps in normalized_profile_skills
            )
            if matched:
                area_matched_concepts.append(concept)
                all_matched_concepts.add(concept)
                total_matched += 1
            else:
                area_missing_concepts.append(concept)
                all_missing_concepts.append(concept)

        coverage_ratio = (
            len(area_matched_concepts) / len(required_concepts)
            if required_concepts
            else 0.0
        )
        area_weighted_score = coverage_ratio * item.importance_weight * 100.0
        total_weighted_score += area_weighted_score

        competency_breakdown.append(
            {
                "competency_area": item.competency_area,
                "importance_weight": item.importance_weight,
                "coverage_ratio": round(coverage_ratio, 2),
                "weighted_score": round(area_weighted_score, 2),
                "matched_concepts": area_matched_concepts,
                "missing_concepts": area_missing_concepts,
            }
        )

    # Round final composite score
    overall_fit_score = round(min(100.0, max(0.0, total_weighted_score)), 1)

    return {
        "role": role.value if isinstance(role, StandardRole) else str(role),
        "overall_fit_score": overall_fit_score,
        "competency_breakdown": competency_breakdown,
        "matched_skills": sorted(list(all_matched_concepts)),
        "missing_concepts": all_missing_concepts,
        "total_required_concepts": total_required,
        "total_matched_concepts": total_matched,
    }


def get_supported_roles_config(
    experience_years: Optional[int] = None,
) -> Dict[str, Any]:
    """Retrieve full role taxonomy configuration with inferred seniority."""
    inferred_seniority = infer_seniority_level(experience_years)

    supported_roles = []
    for role in StandardRole:
        meta = ROLE_METADATA_REGISTRY.get(
            role, {"title": role.value.replace("_", " ").title(), "description": ""}
        )
        matrix = get_role_competency_matrix(role)

        supported_roles.append(
            {
                "id": role.value,
                "title": meta["title"],
                "description": meta["description"],
                "competencies": [
                    {
                        "competency_area": c.competency_area,
                        "importance_weight": c.importance_weight,
                        "required_concepts": c.required_concepts,
                    }
                    for c in matrix
                ],
            }
        )

    return {
        "supported_roles": supported_roles,
        "default_seniority": inferred_seniority.value,
        "seniority_levels": [level.value for level in SeniorityLevel],
    }
