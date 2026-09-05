"""
Tailored Feedback & Skill Gap Analysis Engine for HireSIGHT.

Generates evidence-anchored candidate feedback, identifying technical strengths/weaknesses,
coding insights, objective communication observations, and concrete skill gap remediation
roadmaps directly tied to interview results without generic boilerplate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from app.interview.domain.interview_models import (
    AnswerEvaluation,
    CodingChallengeEvaluation,
    ObservableCVMetrics,
    ObservableVocalMetrics,
    QuestionType,
)
from app.interview.domain.role_taxonomy import CompetencyWeight, StandardRole, get_role_competency_matrix
from app.interview.domain.scoring_models import TailoredFeedback


# Concept to domain practice remediation mapping for precise technical recommendations
CONCEPT_REMEDIATION_MAP: Dict[str, str] = {
    "acid": "Review and practice database transaction isolation levels (Read Committed, Repeatable Read, Serializable), ACID guarantees, and rollback semantics.",
    "transaction": "Practice designing robust multi-table database transactions with optimistic/pessimistic concurrency control and deadlock resolution.",
    "index": "Study database indexing strategies (B-Tree, Hash, GIN), composite indexes, and analyze slow queries using EXPLAIN ANALYZE execution plans.",
    "execution plan": "Study database query execution plans, index scans vs. sequential scans, and cost-based query optimization.",
    "async": "Deepen practical understanding of asynchronous I/O, event loops (asyncio/libuv), coroutines, and non-blocking network pipelines.",
    "concurrency": "Practice multithreading, multiprocessing, mutexes/semaphores, and race condition prevention in concurrent workflows.",
    "cache": "Implement distributed caching patterns (Cache-Aside, Write-Through, Write-Behind) with Redis and configure TTL eviction strategies.",
    "rest": "Practice designing RESTful API contracts following OpenAPI standards, proper HTTP status codes, idempotency, and versioning.",
    "graphql": "Build GraphQL schemas with efficient query resolution, DataLoader batching to prevent N+1 query problems, and rate limiting.",
    "grpc": "Study protocol buffers (Protobuf), unary vs. streaming gRPC communication, and schema evolution rules.",
    "docker": "Practice multi-stage Docker builds, image layer caching, non-root security contexts, and container resource constraints.",
    "kubernetes": "Work with Kubernetes deployment manifests, Pod resource requests/limits, Services, Ingress, and Horizontal Pod Autoscaling (HPA).",
    "ci/cd": "Build automated CI/CD pipelines with GitHub Actions or GitLab CI including linting, unit test gates, and automated container registry publishing.",
    "kafka": "Design event-driven architectures with Apache Kafka, focusing on partition keys, consumer groups, exactly-once semantics, and backpressure.",
    "spark": "Practice distributed batch and stream processing with PySpark, DataFrame transformations, partitioning, and cluster resource tuning.",
    "security": "Apply OWASP Top 10 mitigation strategies including SQL/NoSQL injection prevention, strict CORS/CSP configurations, and JWT validation.",
    "test": "Strengthen unit and integration test coverage using PyTest/Jest, mock external services with stubs, and practice Test-Driven Development (TDD).",
    "dom": "Master browser DOM manipulation, Event Bubbling/Capturing, and Web APIs without heavy abstraction layers.",
    "react": "Deepen understanding of React component lifecycle, custom hooks, Virtual DOM reconciliation, and state immutability patterns.",
    "state": "Practice client-side state management architectures (Zustand, Redux Toolkit, Context API) and state normalization.",
    "css": "Master modern responsive layout techniques using CSS Flexbox, Grid, and performance-friendly CSS transforms/transitions.",
    "performance": "Focus on Web Core Vitals (LCP, FID, CLS), asset bundle splitting, lazy loading, and rendering optimization.",
    "ml": "Review machine learning loss functions, gradient descent optimization algorithms, feature engineering, and cross-validation strategies.",
    "pytorch": "Practice deep learning model implementation in PyTorch, focusing on tensor operations, custom autograd functions, and GPU memory optimization.",
    "rag": "Implement Retrieval-Augmented Generation (RAG) pipelines with vector embeddings (Pinecone/Milvus), semantic search, and prompt chunking.",
    "llm": "Study LLM fine-tuning techniques (LoRA, QLoRA, PEFT), prompt engineering constraints, and hallucination reduction methods.",
}


def _concept_matches(text1: str, text2: str) -> bool:
    """Check if two concept/area descriptions match via substring, normalized tokens, or sub-phrases."""
    t1 = text1.lower()
    t2 = text2.lower()
    if not t1 or not t2:
        return False
    if t1 in t2 or t2 in t1:
        return True
    
    # Split composite names (e.g., "Indexing Strategies & Execution Plans", "Database Architecture & Query Optimization")
    delimiters = ["&", "/", ",", "(", ")", "-"]
    clean1 = t1
    clean2 = t2
    for d in delimiters:
        clean1 = clean1.replace(d, " ")
        clean2 = clean2.replace(d, " ")

    parts1 = [p.strip() for p in clean1.split() if len(p.strip()) >= 3 and p.strip() not in {"and", "the", "for", "with"}]
    parts2 = [p.strip() for p in clean2.split() if len(p.strip()) >= 3 and p.strip() not in {"and", "the", "for", "with"}]

    # If significant keywords match
    overlap = set(parts1).intersection(set(parts2))
    return len(overlap) > 0


def _extract_vocal_attributes(vocal_metrics: Any) -> Dict[str, Any]:
    """Extract normalized vocal metrics from diverse input representations."""
    if isinstance(vocal_metrics, list):
        if not vocal_metrics:
            return {"wpm": 140.0, "pause_ratio": 0.18, "speech_clarity": 75.0, "flags": [], "empty": True}
        wpm_vals, pause_vals, clarity_vals, flags = [], [], [], []
        for vm in vocal_metrics:
            attr = _extract_vocal_attributes(vm)
            wpm_vals.append(attr["wpm"])
            pause_vals.append(attr["pause_ratio"])
            clarity_vals.append(attr["speech_clarity"])
            flags.extend(attr.get("flags", []))
        n = max(1, len(vocal_metrics))
        return {
            "wpm": sum(wpm_vals) / n,
            "pause_ratio": sum(pause_vals) / n,
            "speech_clarity": sum(clarity_vals) / n,
            "flags": list(dict.fromkeys(flags)),
            "empty": False,
        }

    if isinstance(vocal_metrics, dict):
        return {
            "wpm": float(vocal_metrics.get("speaking_rate_wpm", vocal_metrics.get("speech_rate", 140.0))),
            "pause_ratio": float(vocal_metrics.get("pause_duration_ratio", vocal_metrics.get("pause_pattern", 0.18))),
            "speech_clarity": float(vocal_metrics.get("speech_clarity_score", vocal_metrics.get("clarity", 75.0))),
            "flags": list(vocal_metrics.get("acoustic_flags", vocal_metrics.get("red_flags", []))),
            "empty": False,
        }

    if hasattr(vocal_metrics, "speaking_rate_wpm"):
        return {
            "wpm": float(vocal_metrics.speaking_rate_wpm),
            "pause_ratio": float(vocal_metrics.pause_duration_ratio),
            "speech_clarity": float(vocal_metrics.speech_clarity_score),
            "flags": list(getattr(vocal_metrics, "acoustic_flags", [])),
            "empty": False,
        }

    if hasattr(vocal_metrics, "speech_rate_score"):
        # Legacy VocalMetrics dataclass
        speech_rate = float(vocal_metrics.speech_rate_score)
        wpm = speech_rate * 1.6 if speech_rate > 0 else 140.0
        return {
            "wpm": wpm,
            "pause_ratio": 0.18,
            "speech_clarity": float(getattr(vocal_metrics, "speech_clarity_score", 75.0)),
            "flags": list(getattr(vocal_metrics, "red_flags", [])),
            "empty": False,
        }

    return {"wpm": 140.0, "pause_ratio": 0.18, "speech_clarity": 75.0, "flags": [], "empty": True}


def _extract_cv_attributes(cv_metrics: Any) -> Dict[str, Any]:
    """Extract normalized computer vision metrics from diverse input representations."""
    if isinstance(cv_metrics, list):
        if not cv_metrics:
            return {
                "gaze": 75.0,
                "head": 75.0,
                "presence": 85.0,
                "dynamics": 70.0,
                "blink_cpm": 16.0,
                "flags": [],
                "empty": True,
            }
        g_vals, h_vals, p_vals, d_vals, b_vals, flags = [], [], [], [], [], []
        for cm in cv_metrics:
            attr = _extract_cv_attributes(cm)
            g_vals.append(attr["gaze"])
            h_vals.append(attr["head"])
            p_vals.append(attr["presence"])
            d_vals.append(attr["dynamics"])
            b_vals.append(attr["blink_cpm"])
            flags.extend(attr.get("flags", []))
        n = max(1, len(cv_metrics))
        return {
            "gaze": sum(g_vals) / n,
            "head": sum(h_vals) / n,
            "presence": sum(p_vals) / n,
            "dynamics": sum(d_vals) / n,
            "blink_cpm": sum(b_vals) / n,
            "flags": list(dict.fromkeys(flags)),
            "empty": False,
        }

    if isinstance(cv_metrics, dict):
        return {
            "gaze": float(cv_metrics.get("gaze_stability_ratio", cv_metrics.get("eye_contact", 75.0))),
            "head": float(cv_metrics.get("head_pose_variance", cv_metrics.get("head_stability", 75.0))),
            "presence": float(cv_metrics.get("frame_presence_ratio", cv_metrics.get("attention_span", 85.0))),
            "dynamics": float(cv_metrics.get("facial_movement_dynamics", cv_metrics.get("engagement", 70.0))),
            "blink_cpm": float(cv_metrics.get("blink_frequency_cpm", 16.0)),
            "flags": list(cv_metrics.get("observable_flags", cv_metrics.get("red_flags", []))),
            "empty": False,
        }

    if hasattr(cv_metrics, "gaze_stability_ratio"):
        return {
            "gaze": float(cv_metrics.gaze_stability_ratio),
            "head": float(cv_metrics.head_pose_variance),
            "presence": float(cv_metrics.frame_presence_ratio),
            "dynamics": float(cv_metrics.facial_movement_dynamics),
            "blink_cpm": float(getattr(cv_metrics, "blink_frequency_cpm", 16.0)),
            "flags": list(getattr(cv_metrics, "observable_flags", [])),
            "empty": False,
        }

    if hasattr(cv_metrics, "eye_contact_score"):
        # Legacy BehavioralMetrics dataclass
        return {
            "gaze": float(cv_metrics.eye_contact_score),
            "head": float(getattr(cv_metrics, "head_stability_score", 75.0)),
            "presence": float(getattr(cv_metrics, "attention_span_score", 85.0)),
            "dynamics": float(getattr(cv_metrics, "facial_engagement_score", 70.0)),
            "blink_cpm": 16.0,
            "flags": list(getattr(cv_metrics, "red_flags", [])),
            "empty": False,
        }

    return {
        "gaze": 75.0,
        "head": 75.0,
        "presence": 85.0,
        "dynamics": 70.0,
        "blink_cpm": 16.0,
        "flags": [],
        "empty": True,
    }


def _match_remediation_for_concept(concept: str) -> str:
    """Find specific technical remediation advice for a given concept or return structured guidance."""
    concept_lower = concept.lower()
    for key, advice in CONCEPT_REMEDIATION_MAP.items():
        if key in concept_lower:
            return advice
    return f"Study and implement hands-on exercises for '{concept}' to reinforce practical application and theoretical depth."


def generate_tailored_feedback(
    evaluations: Optional[List[AnswerEvaluation]] = None,
    coding_evaluation: Optional[Union[CodingChallengeEvaluation, Dict[str, Any]]] = None,
    role_competencies: Optional[List[CompetencyWeight]] = None,
    vocal_metrics: Optional[Union[ObservableVocalMetrics, Any]] = None,
    cv_metrics: Optional[Union[ObservableCVMetrics, Any]] = None,
) -> TailoredFeedback:
    """
    Generate evidence-anchored tailored candidate feedback across technical, coding, communication,
    and role competency gap dimensions.

    Parameters:
        evaluations: Per-question verbal answer evaluations.
        coding_evaluation: Results from sandboxed coding challenge execution.
        role_competencies: Weighted competency requirements for the target role.
        vocal_metrics: Acoustic vocal metrics (speaking rate WPM, pause ratio, clarity).
        cv_metrics: Observable computer vision metrics (gaze stability, head pose, blink CPM, presence).

    Returns:
        TailoredFeedback instance with all 7 fields populated.
    """
    evaluations = evaluations or []
    role_competencies = role_competencies or []

    # ---------------------------------------------------------
    # 1. Technical Strengths & Weaknesses (Question-Level Evidence)
    # ---------------------------------------------------------
    strongest_technical: List[str] = []
    weakest_technical: List[str] = []
    missed_concepts_all: List[str] = []
    covered_concepts_all: List[str] = []

    if evaluations:
        for idx, e in enumerate(evaluations):
            q_num = getattr(e, "question_index", idx) + 1
            q_text = getattr(e, "question_text", f"Question {q_num}")
            rel_score = float(getattr(e, "relevance_score", 0.0) or 0.0)
            depth_score = float(getattr(e, "depth_score", 0.0) or 0.0)
            acc_score = float(getattr(e, "accuracy_score", 0.0) or 0.0)
            is_correct = getattr(e, "is_correct", False)

            # Normalized rubric score for the question
            rel_norm = min(100.0, max(0.0, rel_score * 10.0 if rel_score <= 10.0 else rel_score))
            depth_norm = min(100.0, max(0.0, depth_score * 10.0 if depth_score <= 10.0 else depth_score))
            acc_norm = min(100.0, max(0.0, acc_score))
            q_rubric_score = (rel_norm * 0.30) + (depth_norm * 0.40) + (acc_norm * 0.30)

            covered = getattr(e, "key_points_covered", []) or []
            missed = getattr(e, "missed_points", []) or []

            covered_concepts_all.extend(covered)
            missed_concepts_all.extend(missed)

            short_q = (q_text[:70] + "...") if len(q_text) > 70 else q_text

            # Classify strengths
            if (q_rubric_score >= 70.0 or is_correct or acc_norm >= 75.0) and covered:
                concepts_str = ", ".join(covered[:3])
                strongest_technical.append(
                    f"Demonstrated solid grasp of {concepts_str} on Question {q_num} ('{short_q}') with {acc_norm:.0f}% accuracy."
                )
            elif q_rubric_score >= 80.0:
                strongest_technical.append(
                    f"Provided thorough explanation on Question {q_num} ('{short_q}') scoring {q_rubric_score:.1f}/100 on rubric depth."
                )

            # Classify weaknesses
            if missed:
                missed_str = ", ".join(missed[:3])
                weakest_technical.append(
                    f"Missed key concepts ({missed_str}) on Question {q_num} ('{short_q}')."
                )
            elif q_rubric_score < 60.0 or not is_correct:
                weakest_technical.append(
                    f"Superficial technical depth or partial inaccuracies on Question {q_num} ('{short_q}') scoring {q_rubric_score:.1f}/100."
                )

    # Fallbacks for technical areas if empty
    if not strongest_technical:
        if evaluations:
            strongest_technical.append("Candidate attempted interview questions and engaged with technical problem prompts.")
        else:
            strongest_technical.append("Candidate initiated the interview session.")

    if not weakest_technical:
        if evaluations:
            weakest_technical.append("No critical technical knowledge gaps identified during evaluated questions.")
        else:
            weakest_technical.append("Core technical competencies were not evaluated as no questions were completed.")

    # ---------------------------------------------------------
    # 2. Sandboxed Coding Assessment Summary
    # ---------------------------------------------------------
    if coding_evaluation:
        if isinstance(coding_evaluation, dict):
            compile_ok = coding_evaluation.get("compile_success", True)
            pub_passed = coding_evaluation.get("public_tests_passed", 0)
            pub_total = coding_evaluation.get("public_tests_total", 0)
            hid_passed = coding_evaluation.get("hidden_tests_passed", 0)
            hid_total = coding_evaluation.get("hidden_tests_total", 0)
            c_score = float(coding_evaluation.get("overall_coding_score", 0.0))
            lang = coding_evaluation.get("language", "code")
            exec_time = float(coding_evaluation.get("execution_time_total_ms", 0.0))
            mem = float(coding_evaluation.get("peak_memory_kb", 0.0))
        else:
            compile_ok = getattr(coding_evaluation, "compile_success", True)
            pub_passed = getattr(coding_evaluation, "public_tests_passed", 0)
            pub_total = getattr(coding_evaluation, "public_tests_total", 0)
            hid_passed = getattr(coding_evaluation, "hidden_tests_passed", 0)
            hid_total = getattr(coding_evaluation, "hidden_tests_total", 0)
            c_score = float(getattr(coding_evaluation, "overall_coding_score", 0.0))
            lang = getattr(coding_evaluation, "language", "code")
            exec_time = float(getattr(coding_evaluation, "execution_time_total_ms", 0.0))
            mem = float(getattr(coding_evaluation, "peak_memory_kb", 0.0))

        if not compile_ok:
            coding_summary = (
                f"Compilation failed for {lang.capitalize()} solution (Score: 0.0/100). "
                f"Candidate did not pass public (0/{pub_total}) or hidden (0/{hid_total}) test cases due to syntax or type errors."
            )
        elif hid_total > 0 and hid_passed < hid_total:
            coding_summary = (
                f"Candidate passed {pub_passed}/{pub_total} public test cases, but failed {hid_total - hid_passed}/{hid_total} hidden test cases "
                f"in {lang.capitalize()} (Overall Score: {c_score:.1f}/100, Runtime: {exec_time:.1f}ms). "
                f"Indicates missing boundary condition handling, unhandled edge cases, or algorithmic scale limitations."
            )
        elif pub_total + hid_total > 0 and (pub_passed + hid_passed == pub_total + hid_total):
            coding_summary = (
                f"Solution in {lang.capitalize()} successfully passed all {pub_total} public and {hid_total} hidden test cases "
                f"(Score: {c_score:.1f}/100, Runtime: {exec_time:.1f}ms, Peak Memory: {mem:.1f}KB). "
                f"Demonstrated strong algorithmic design, edge-case coverage, and clean implementation."
            )
        else:
            coding_summary = (
                f"Coding challenge completed in {lang.capitalize()} with an overall score of {c_score:.1f}/100 "
                f"({pub_passed}/{pub_total} public tests passed, {hid_passed}/{hid_total} hidden tests passed)."
            )
    else:
        coding_summary = (
            "No coding challenge was submitted or the coding section was skipped during this session. "
            "Practical algorithmic execution and code quality were not directly assessed."
        )

    # ---------------------------------------------------------
    # 3. Communication Observations (Objective Physical Signals)
    # ---------------------------------------------------------
    vocal = _extract_vocal_attributes(vocal_metrics)
    wpm = vocal["wpm"]
    pause_ratio = vocal["pause_ratio"]
    clarity = vocal["speech_clarity"]
    acoustic_flags = vocal["flags"]

    comm_obs: List[str] = []

    # Speaking Rate (Conversational norm: 120-160 WPM)
    if 120.0 <= wpm <= 160.0:
        comm_obs.append(f"Measured speaking rate of {wpm:.1f} WPM was within the optimal conversational range (120–160 WPM).")
    elif wpm < 120.0:
        comm_obs.append(f"Speaking rate of {wpm:.1f} WPM was below the conversational baseline (120–160 WPM), suggesting cautious or deliberate pacing.")
    else:
        comm_obs.append(f"Speaking rate of {wpm:.1f} WPM exceeded standard conversational pacing (120–160 WPM), which may impact listener absorption.")

    # Pause Duration Ratio (Conversational norm: 0.10 - 0.25)
    if 0.10 <= pause_ratio <= 0.25:
        comm_obs.append(f"Pause duration ratio of {pause_ratio:.1%} reflected natural conversational pauses and structured transitions.")
    elif pause_ratio > 0.25:
        comm_obs.append(f"Pause duration ratio of {pause_ratio:.1%} indicated extended silent intervals between sentence clauses.")
    else:
        comm_obs.append(f"Pause duration ratio of {pause_ratio:.1%} showed continuous speech delivery with minimal transition pauses.")

    # Speech Clarity
    if clarity >= 75.0:
        comm_obs.append(f"Speech clarity score of {clarity:.1f}/100 showed clear acoustic projection and phonetic distinctness.")
    else:
        comm_obs.append(f"Speech clarity score of {clarity:.1f}/100 suggested opportunities for clearer vocal projection and articulation.")

    # Acoustic Flags
    if acoustic_flags:
        flags_str = ", ".join(acoustic_flags)
        comm_obs.append(f"Acoustic flags noted during audio processing: {flags_str}.")

    # Verbal answers clarity
    if evaluations:
        comm_scores = [float(getattr(e, "communication_score", 0.0) or 0.0) for e in evaluations]
        avg_comm = (sum(comm_scores) / len(comm_scores)) * 10.0 if any(s <= 10.0 for s in comm_scores) else (sum(comm_scores) / len(comm_scores))
        comm_obs.append(f"Verbal response structure and articulation averaged {avg_comm:.1f}/100 across {len(evaluations)} answered questions.")

    # ---------------------------------------------------------
    # 4. Behavioral Observations (Objective Computer Vision Signals)
    # ---------------------------------------------------------
    cv = _extract_cv_attributes(cv_metrics)
    gaze = cv["gaze"]
    head = cv["head"]
    presence = cv["presence"]
    blink = cv["blink_cpm"]
    cv_flags = cv["flags"]

    beh_obs: List[str] = []

    # Camera presence
    if presence >= 85.0:
        beh_obs.append(f"Maintained steady camera presence with face detected in {presence:.1f}% of analyzed video frames.")
    else:
        beh_obs.append(f"Camera presence was {presence:.1f}%, indicating periodic movement outside the primary camera field of view.")

    # Gaze stability
    if gaze >= 70.0:
        beh_obs.append(f"Gaze stability ratio was {gaze:.1f}%, reflecting consistent eye orientation toward the central display area.")
    else:
        beh_obs.append(f"Gaze stability ratio was {gaze:.1f}%, indicating frequent shifts in eye orientation away from the screen center.")

    # Head pose variance
    if head >= 70.0:
        beh_obs.append(f"Head stability index of {head:.1f}% demonstrated balanced posture throughout question delivery.")
    else:
        beh_obs.append(f"Head pose stability index was {head:.1f}%, reflecting active head rotational variance during responses.")

    # Blink frequency
    if blink > 0:
        beh_obs.append(f"Blink rate averaged {blink:.1f} blinks per minute (conversational baseline: 12–20 CPM).")

    # Observable physical flags
    if cv_flags:
        flags_str = ", ".join(cv_flags)
        beh_obs.append(f"Physical camera observations flagged: {flags_str}.")

    # ---------------------------------------------------------
    # 5. Target Role Gap Analysis (Competencies with Score < 60%)
    # ---------------------------------------------------------
    missing_role_skills: List[str] = []

    if role_competencies:
        for comp in role_competencies:
            area_name = comp.competency_area
            req_concepts = comp.required_concepts or []
            weight = comp.importance_weight

            # Find matching evaluations for this competency area
            matching_evals = []
            for e in evaluations:
                q_text = getattr(e, "question_text", "")
                q_comp = getattr(e, "competency_area", "")
                q_covered = getattr(e, "key_points_covered", []) or []
                q_missed = getattr(e, "missed_points", []) or []

                if (
                    _concept_matches(area_name, q_text)
                    or (q_comp and _concept_matches(area_name, q_comp))
                    or any(_concept_matches(c, q_text) for c in req_concepts)
                    or any(_concept_matches(c, k) for c in req_concepts for k in q_covered)
                    or any(_concept_matches(c, m) for c in req_concepts for m in q_missed)
                ):
                    matching_evals.append(e)

            # Find missed concepts specific to this competency
            competency_missed = [
                c for c in req_concepts
                if any(_concept_matches(c, m) for m in missed_concepts_all)
            ]

            if matching_evals:
                scores = []
                for me in matching_evals:
                    rel = min(100.0, max(0.0, float(getattr(me, "relevance_score", 0.0) or 0.0) * 10.0 if float(getattr(me, "relevance_score", 0.0) or 0.0) <= 10.0 else float(getattr(me, "relevance_score", 0.0) or 0.0)))
                    dep = min(100.0, max(0.0, float(getattr(me, "depth_score", 0.0) or 0.0) * 10.0 if float(getattr(me, "depth_score", 0.0) or 0.0) <= 10.0 else float(getattr(me, "depth_score", 0.0) or 0.0)))
                    acc = min(100.0, max(0.0, float(getattr(me, "accuracy_score", 0.0) or 0.0)))
                    scores.append(rel * 0.30 + dep * 0.40 + acc * 0.30)
                avg_score = sum(scores) / len(scores)

                if avg_score < 60.0 or len(competency_missed) >= 1:
                    detail_str = f" (Score: {avg_score:.1f}% vs 60% threshold, Weight: {weight:.0%})"
                    if competency_missed:
                        detail_str += f" - Missed concepts: {', '.join(competency_missed[:2])}"
                    missing_role_skills.append(f"{area_name}{detail_str}")
            elif not evaluations:
                # No questions answered at all
                missing_role_skills.append(f"{area_name} (Role Weight: {weight:.0%}, required concepts: {', '.join(req_concepts[:2])})")
            elif competency_missed:
                missing_role_skills.append(f"{area_name} - Missed key concepts: {', '.join(competency_missed[:2])}")
    elif missed_concepts_all:
        # No role competencies provided, use direct missed concepts
        for mc in dict.fromkeys(missed_concepts_all):
            missing_role_skills.append(f"Demonstrated gap in '{mc}' during technical evaluation")

    if not missing_role_skills:
        if evaluations:
            missing_role_skills.append("All primary role competencies met or exceeded the 60% threshold during evaluation.")
        else:
            missing_role_skills.append("Target role competencies require initial technical calibration.")

    # ---------------------------------------------------------
    # 6. Actionable Improvement Recommendations
    # ---------------------------------------------------------
    recommendations: List[str] = []

    # 1. Technical concept remediation based on actual missed points
    seen_remediations = set()
    for mc in missed_concepts_all:
        advice = _match_remediation_for_concept(mc)
        if advice not in seen_remediations:
            seen_remediations.add(advice)
            recommendations.append(advice)

    # 2. Coding challenge remediation
    if coding_evaluation:
        if isinstance(coding_evaluation, dict):
            compile_ok = coding_evaluation.get("compile_success", True)
            hid_passed = coding_evaluation.get("hidden_tests_passed", 0)
            hid_total = coding_evaluation.get("hidden_tests_total", 0)
            c_score = float(coding_evaluation.get("overall_coding_score", 0.0))
        else:
            compile_ok = getattr(coding_evaluation, "compile_success", True)
            hid_passed = getattr(coding_evaluation, "hidden_tests_passed", 0)
            hid_total = getattr(coding_evaluation, "hidden_tests_total", 0)
            c_score = float(getattr(coding_evaluation, "overall_coding_score", 0.0))

        if not compile_ok:
            recommendations.append(
                "Focus on syntax accuracy, compiler error diagnostics, and local code compilation before test submission."
            )
        elif hid_total > 0 and hid_passed < hid_total:
            recommendations.append(
                "Incorporate rigorous edge-case testing into coding practice, focusing on boundary values (empty inputs, zero/negative bounds, off-by-one indices, and large scale inputs)."
            )
        elif c_score < 75.0:
            recommendations.append(
                "Practice data structures and algorithmic complexity optimization on platforms like LeetCode or HackerRank to improve runtime efficiency."
            )

    # 3. Communication / Speaking rate pacing remediation
    if wpm < 120.0 and not vocal["empty"]:
        recommendations.append(
            "Practice structured response frameworks (e.g., STAR method) with timed rehearsals to increase conversational speaking pace toward 130–150 WPM."
        )
    elif wpm > 160.0 and not vocal["empty"]:
        recommendations.append(
            "Incorporate deliberate micro-pauses at key concept transitions to moderate speaking pace below 160 WPM for enhanced clarity."
        )

    if pause_ratio > 0.25 and not vocal["empty"]:
        recommendations.append(
            "Prepare concise mental outlines before answering to reduce hesitation and silent pause intervals."
        )

    # 4. High-Performance Edge Case (100% on everything with evaluated questions)
    if evaluations and (not missed_concepts_all or len(missed_concepts_all) == 0) and (not recommendations or len(recommendations) < 2):
        recommendations.append(
            "Explore advanced distributed systems patterns, consensus algorithms (Raft/Paxos), and high-throughput stream processing."
        )
        recommendations.append(
            "Focus on technical leadership, architectural decision record (ADR) authoring, and mentoring engineering team members."
        )

    # 5. Empty evaluation edge case (Candidate answered zero questions)
    if not evaluations:
        recommendations.append(
            "Review foundational system design principles, API development workflows, and database indexing strategies."
        )
        recommendations.append(
            "Participate in mock technical interviews to build familiarity with live interactive questioning."
        )

    # Deduplicate while preserving order
    unique_recommendations = list(dict.fromkeys(recommendations))

    return TailoredFeedback(
        strongest_technical_areas=strongest_technical,
        weakest_technical_areas=weakest_technical,
        coding_analysis_summary=coding_summary,
        communication_observations=comm_obs,
        behavioral_observations=beh_obs,
        missing_role_skills=missing_role_skills,
        actionable_improvement_recommendations=unique_recommendations,
    )
