"""
Skill matching logic for job posts and resumes.
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional


class SkillMatcher:
    """Skill matching between job post and resume/profile"""

    PHRASE_SKILLS = [
        "operating system",
        "kernel and system programming",
        "networking and security",
        "virtual memory",
        "system programming",
        "networking",
        "security",
        "kernel",
    ]

    COMMON_NORMALIZATIONS = {
        "kernal": "kernel",
        "secuirity": "security",
        "operating systems": "operating system",
        "os": "operating system",
        # Job-post typos vs resume wording
        "reddis": "redis",
        "postgre": "postgresql",
        "postgress": "postgresql",
        "postgres": "postgresql",
        "postgrsql": "postgresql",
        "postgesql": "postgresql",
        "postgreql": "postgresql",
        "potgresql": "postgresql",
        "progresql": "postgresql",
        "postsql": "postgresql",
        "django framework": "django",
        # Grafana / monitoring stack (common admin typos)
        "graphana": "grafana",
        "garafana": "grafana",
        "grafna": "grafana",
        "graphna": "grafana",
        "gaphana": "grafana",
        "grafaba": "grafana",
    }

    @staticmethod
    def _normalize_skill(skill: str) -> str:
        raw = (skill or "").strip()
        # Split accidental camel-case joins e.g. "SystemKernel"
        raw = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw)
        text = raw.lower()
        text = re.sub(r"[^a-z0-9+#./\s-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        for wrong, correct in SkillMatcher.COMMON_NORMALIZATIONS.items():
            text = re.sub(rf"\b{re.escape(wrong)}\b", correct, text)

        # Job-post typo often seen alongside kernel / OS roles
        text = re.sub(
            r"\bkernel\s+and\s+system\s+processing\b",
            "kernel and system programming",
            text,
        )

        return text

    @staticmethod
    def _explode_skill_entry(skill: str) -> List[str]:
        """
        Split a potentially compound skill entry into atomic skills.
        Handles comma/newline/slash/semicolon/and-separated lists.
        """
        if not skill:
            return []

        normalized = SkillMatcher._normalize_skill(skill)

        # Phrase extraction for badly merged skill strings, e.g.
        # "Operating SystemKernel and System ProgrammingNetworking and SecurityVirtual Memory"
        phrase_hits = []
        compact = re.sub(r"[^a-z0-9+#]", "", normalized)
        for phrase in SkillMatcher.PHRASE_SKILLS:
            phrase_norm = SkillMatcher._normalize_skill(phrase)
            phrase_compact = re.sub(r"[^a-z0-9+#]", "", phrase_norm)
            if phrase_norm in normalized or (phrase_compact and phrase_compact in compact):
                phrase_hits.append(phrase_norm)
        if len(phrase_hits) >= 2:
            return list(dict.fromkeys(phrase_hits))

        # Split by common separators; keep technical forms like C++, C#, Node.js
        parts = re.split(r"\s*(?:,|/|;|\||\n| and )\s*", normalized)
        return [p.strip() for p in parts if p and p.strip()]

    @staticmethod
    def _skills_to_atomic(skills: List[str]) -> List[str]:
        atomic = []
        for skill in skills or []:
            atomic.extend(SkillMatcher._explode_skill_entry(skill))
        # de-duplicate while preserving order
        return list(dict.fromkeys(atomic))

    @staticmethod
    def _is_match(job_skill: str, candidate_skill: str) -> bool:
        if job_skill == candidate_skill:
            return True

        def _tokens(text: str) -> List[str]:
            raw_tokens = re.findall(r"[a-z0-9+#]+", text)
            stop = {"and", "or", "the", "of", "in", "on", "for", "to", "a", "an"}
            return [t for t in raw_tokens if t not in stop]

        job_tokens = _tokens(job_skill)
        cand_tokens = _tokens(candidate_skill)

        # Multi-word job requirements: every job token must appear as its own token on the
        # resume side (no naive substring: "sql" must not match inside "postgresql").
        if len(job_tokens) >= 2:
            if set(job_tokens) <= set(cand_tokens):
                return True
            # Near-identical multi-word phrases only (typos), not substring containment.
            if min(len(job_skill), len(candidate_skill)) >= 12:
                similarity = SequenceMatcher(None, job_skill, candidate_skill).ratio()
                if similarity >= 0.93:
                    return True
            return False

        # Single-token job requirement: match only the same token or fuzzy typo — never
        # Python substring checks (`sql` in `postgresql`, `c` in `celery`, etc.).
        if len(job_tokens) == 1:
            jt = job_tokens[0]
            if jt in cand_tokens:
                return True
            lo, hi = len(job_skill), len(candidate_skill)
            shortest = min(lo, hi)
            if shortest >= 5:
                similarity = SequenceMatcher(None, job_skill, candidate_skill).ratio()
                # Short tokens: strict. Longer names: allow admin/job-post typos (e.g. Graphana/Grafana).
                threshold = 0.92 if shortest < 7 else 0.78
                if similarity >= threshold:
                    return True
            return False

        return False

    @staticmethod
    def _iter_resume_segments(full_text: str):
        """Yield normalized fragments where inline skill lists often appear."""
        if not (full_text or "").strip():
            return
        for line in full_text.splitlines():
            ln = line.strip()
            if len(ln) < 2:
                continue
            for chunk in re.split(r"[,;|•·▪►]+", ln):
                c = re.sub(r"^[\s\-–—•]+|[\s\-–—•]+$", "", chunk).strip()
                if len(c) >= 2:
                    yield SkillMatcher._normalize_skill(c)
            yield SkillMatcher._normalize_skill(ln)

    @staticmethod
    def _skill_evidence_in_resume(job_atom: str, full_text: str) -> bool:
        """
        True if normalized job_atom appears in resume prose or in a comma/bullet-like
        segment, using the same rules as _is_match (not loose token scattering).
        """
        if not full_text or not job_atom:
            return False
        norm_atom = SkillMatcher._normalize_skill(job_atom)
        if not norm_atom:
            return False
        norm_full = SkillMatcher._normalize_skill(full_text)

        def _tokens(text: str) -> List[str]:
            raw_tokens = re.findall(r"[a-z0-9+#]+", text)
            stop = {"and", "or", "the", "of", "in", "on", "for", "to", "a", "an"}
            return [t for t in raw_tokens if t not in stop]

        atom_tokens = _tokens(norm_atom)
        if len(atom_tokens) >= 2:
            if norm_atom in norm_full:
                return True
        else:
            if len(atom_tokens) == 1:
                t = atom_tokens[0]
                if re.search(rf"\b{re.escape(t)}\b", norm_full):
                    return True

        for seg in SkillMatcher._iter_resume_segments(full_text):
            if seg and SkillMatcher._is_match(norm_atom, seg):
                return True
        return False

    @staticmethod
    def flatten_candidate_skill_lists(
        skills: Optional[List[str]] = None,
        experienced_skills: Optional[List[str]] = None,
        known_skills: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Merge all resume/profile skill buckets. Extraction often puts tools in
        experienced_skills or known_skills while job matching used only `skills`.
        """
        out: List[str] = []
        for bucket in (skills, experienced_skills, known_skills):
            if bucket:
                out.extend(bucket)
        return out

    @staticmethod
    def match_skills(
        job_post_skills: List[str],
        candidate_skills: List[str],
        resume_full_text: Optional[str] = None,
    ) -> Dict:
        """
        Match required job skills against candidate skills.

        - `job_post_skills` are treated as canonical requirements (e.g. 4 items).
        - We explode/normalize them internally, but each original required skill
          counts at most once in match %, so you won't see 8 required skills when
          you only configured 4.
        - `resume_full_text` (if provided) adds a second pass that searches the
          raw document. Prefer leaving it None: PDF/OCR text often false-positives
          on short words; trust the extracted skill list instead.
        """
        # Normalize/explode candidate skills to atomic tokens
        candidate_atomic = SkillMatcher._skills_to_atomic(candidate_skills)

        # Precompute atomic variants for each original required skill
        required_variants = {
            original: SkillMatcher._skills_to_atomic([original])
            for original in job_post_skills or []
        }

        matched_original: List[str] = []
        missing_original: List[str] = []

        for original, variants in required_variants.items():
            if any(
                SkillMatcher._is_match(req_atom, cand)
                for req_atom in variants
                for cand in candidate_atomic
            ):
                matched_original.append(original)
            elif resume_full_text and any(
                SkillMatcher._skill_evidence_in_resume(req_atom, resume_full_text)
                for req_atom in variants
            ):
                matched_original.append(original)
            else:
                missing_original.append(original)

        # Extra candidate skills that do not satisfy any required skill
        extra_atomic: List[str] = []
        for cand in candidate_atomic:
            if not any(
                SkillMatcher._is_match(req_atom, cand)
                for variants in required_variants.values()
                for req_atom in variants
            ):
                extra_atomic.append(cand)

        return {
            "matched_skills": matched_original,
            "missing_skills": missing_original,
            "extra_skills": extra_atomic,
        }
