"""LLM service for interviews: Grok for question generation; Grok-then-Groq for scoring helpers."""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from typing import Any, Dict, List, Optional

import httpx

from app.interview.domain.interview_models import (
    InterviewQuestion,
    QuestionRubric,
    QuestionStage,
)
from app.interview.domain.role_taxonomy import (
    ROLE_COMPETENCY_MATRICES,
    SeniorityLevel,
    StandardRole,
    get_role_competency_matrix,
)


def _strip_fences(text: str) -> str:
    return re.sub(r"```json|```", "", text).strip()


def _parse_json(text: str) -> dict:
    text = _strip_fences(text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


def _parse_json_array(text: str) -> list:
    text = _strip_fences(text)
    start = text.find("[")
    end = text.rfind("]") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)


_groq_client = None

try:
    from groq import RateLimitError as _GroqRateLimitError
except ImportError:
    _GroqRateLimitError = None


def _is_groq_rate_limited(exc: BaseException) -> bool:
    """TPM/TPD or other quota exhaustion should degrade gracefully, not 500 the API."""
    if _GroqRateLimitError is not None and isinstance(exc, _GroqRateLimitError):
        return True
    code = getattr(exc, "status_code", None)
    if code == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "tokens per day" in msg


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        from app.core.config import settings

        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Add to backend/.env: GROQ_API_KEY=gsk_xxxx"
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _sdk_call(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    client = _get_groq_client()
    msg_list = []
    if system:
        msg_list.append({"role": "system", "content": system})
    msg_list.extend(messages)
    
    preferred_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    fallback_models = [
        preferred_model,
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b",
        "groq/compound",
    ]
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in fallback_models if not (m in seen or seen.add(m))]
    
    last_exc = None
    for model in models_to_try:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=msg_list,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as exc:
            last_exc = exc
            continue
            
    raise last_exc or RuntimeError("All Groq model attempts failed")


def _try_sdk_call(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> Optional[str]:
    """Like _sdk_call but returns None when Groq quota / rate limits block the request."""
    try:
        return _sdk_call(
            messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        if _is_groq_rate_limited(exc):
            return None
        raise


def _grok_api_key() -> str:
    """
    Resolve xAI Grok API key. GROQ_API_KEY is a different provider (Groq, usually `gsk_...`).
    Grok keys are typically `xai-...` and must be set as GROK_API_KEY or XAI_API_KEY.
    """
    from app.core.config import settings

    for key in (
        getattr(settings, "GROK_API_KEY", None),
        getattr(settings, "XAI_API_KEY", None),
        os.getenv("GROK_API_KEY"),
        os.getenv("XAI_API_KEY"),
    ):
        if key and str(key).strip():
            return str(key).strip()
    # Common mistake: xAI key pasted into GROQ_API_KEY (similar name)
    groq_slot = getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
    if groq_slot and str(groq_slot).strip().lower().startswith("xai-"):
        return str(groq_slot).strip()
    return ""


def _grok_chat(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    *,
    required: bool = False,
) -> Optional[str]:
    """
    xAI Grok OpenAI-compatible chat.
    Retries transient HTTP errors (including 429). Does not silently drop on 429.
    If `required` is True and no API key or all retries fail, raises RuntimeError.
    If `required` is False, returns None when no key or after failed retries (for non-question paths).
    """
    api_key = _grok_api_key()
    if not api_key:
        if required:
            raise RuntimeError(
                "GROK_API_KEY or XAI_API_KEY is not set. Interview question generation is configured to use Grok only."
            )
        return None
    from app.core.config import settings

    base = (getattr(settings, "GROK_API_BASE", None) or "https://api.x.ai/v1").rstrip("/")
    model = getattr(settings, "GROK_MODEL", None) or os.getenv("GROK_MODEL", "grok-2-latest")
    url = f"{base}/chat/completions"
    msg_list: list = []
    if system:
        msg_list.append({"role": "system", "content": system})
    msg_list.extend(messages)
    payload = {
        "model": model,
        "messages": msg_list,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    last_err = ""
    for attempt in range(3):
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
            last_err = (r.text or "")[:1500]
            if attempt < 2 and r.status_code in (429, 500, 502, 503, 529):
                time.sleep(1.8 * (attempt + 1))
                continue
            if required:
                raise RuntimeError(f"Grok API HTTP {r.status_code}: {last_err}")
            return None
        except RuntimeError:
            raise
        except Exception as exc:
            last_err = str(exc)
            if attempt < 2:
                time.sleep(1.8 * (attempt + 1))
                continue
            if required:
                raise RuntimeError(f"Grok request failed: {last_err}") from exc
    if required:
        raise RuntimeError(f"Grok failed after retries: {last_err}")
    return None


def _interview_question_llm(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Interview *question generation* (plan + coding): Grok when GROK_API_KEY/XAI_API_KEY is set; else Groq.
    Raises with actionable errors (no silent empty plan).
    """
    if _grok_api_key():
        out = _grok_chat(
            messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            required=True,
        )
        if not (out or "").strip():
            raise RuntimeError("Grok returned an empty response for interview question generation.")
        return out
    try:
        out = _sdk_call(
            messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        if _is_groq_rate_limited(exc):
            raise RuntimeError(
                "Groq returned a rate limit or quota error while generating interview questions. "
                "For Grok, add a separate line in backend/.env: GROK_API_KEY=xai-... "
                "(from https://console.x.ai). GROQ_API_KEY is only for Groq and does not call Grok."
            ) from exc
        raise RuntimeError(
            f"Interview questions use Groq because GROK_API_KEY is not set, and Groq failed: {exc!r}. "
            "Set GROK_API_KEY (xAI Grok) or fix GROQ_API_KEY / LLM_MODEL for Groq."
        ) from exc
    if not (out or "").strip():
        raise RuntimeError(
            "Groq returned an empty response. Check GROQ_API_KEY and LLM_MODEL, or set GROK_API_KEY "
            "for xAI Grok (GROQ_API_KEY is a different provider — it does not activate Grok)."
        )
    return out


def _try_grok_chat(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> Optional[str]:
    """Backward-compatible optional Grok call (evaluator / follow-ups): same retries, no raise."""
    return _grok_chat(
        messages,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        required=False,
    )


def _try_interview_llm_call(
    messages: list,
    system: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> Optional[str]:
    """Prefer Grok when `GROK_API_KEY` or `XAI_API_KEY` is set; otherwise use Groq."""
    grok = _try_grok_chat(
        messages,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if grok is not None:
        return grok
    return _try_sdk_call(
        messages,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _fallback_answer_evaluation(
    question_text: str,
    question_type,
    candidate_transcript: str,
    frame_analysis,
):
    """When the LLM cannot run (e.g. daily token cap), still return a valid AnswerEvaluation."""
    from app.interview.domain.interview_models import AnswerEvaluation, QuestionType

    qt = question_type
    if not isinstance(qt, QuestionType):
        try:
            qt = QuestionType(str(qt).lower())
        except ValueError:
            qt = QuestionType.TECHNICAL

    text = (candidate_transcript or "").strip()
    short = len(text) < 20 or len(text.split()) < 6
    if short:
        rel, depth, comm, acc = 3.5, 3.0, 4.0, 30.0
        notes = (
            "Automated AI scoring unavailable (LLM quota or API error). "
            "This answer looks very short — consider elaboration."
        )
    else:
        rel, depth, comm, acc = 6.0, 5.5, 6.0, 55.0
        notes = (
            "Automated AI scoring unavailable (LLM quota or API error). "
            "Placeholder scores — review the transcript manually."
        )

    return AnswerEvaluation(
        question_index=0,
        question_text=question_text,
        question_type=qt,
        candidate_transcript=candidate_transcript or "",
        relevance_score=rel,
        depth_score=depth,
        communication_score=comm,
        key_points_covered=[],
        missed_points=["Full rubric unavailable while LLM quota is exceeded."],
        is_correct=False,
        accuracy_score=acc,
        follow_up_triggered=short,
        coaching_detected=False,
        frame_analysis=frame_analysis,
        evaluator_notes=notes,
    )


class LLMService:
    """Legacy MCQ/assessment service (kept for backward compatibility)."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

    async def generate_questions(
        self,
        job_title: str,
        job_description: str,
        num_questions: int = 5,
        difficulty: str = "medium",
    ) -> List[Dict]:
        prompt = self._build_question_prompt(
            job_title, job_description, num_questions, difficulty
        )
        response = await self._call_llm(prompt)
        questions = self._parse_questions_response(response, num_questions)
        return questions

    def _build_question_prompt(
        self,
        job_title: str,
        job_description: str,
        num_questions: int,
        difficulty: str,
    ) -> str:
        return (
            "You are an AI interviewer. "
            f"Generate {num_questions} {difficulty}-level interview questions for the following job position.\n\n"
            f"Job Title: {job_title}\n\n"
            f"Job Description: {job_description}\n\n"
            f"Generate exactly {num_questions} questions that:\n"
            "1. Test technical skills relevant to the job\n"
            "2. Assess problem-solving abilities\n"
            "3. Evaluate communication skills\n"
            f"4. Are appropriate for a {difficulty} difficulty level\n\n"
            "Return the response as a JSON array with objects containing:\n"
            "- 'question': The interview question text\n"
            "- 'category': One of 'technical', 'behavioral', 'problem_solving', 'communication'\n"
            "- 'expected_duration': Estimated time to answer in seconds\n\n"
            "Format your response as a valid JSON array only, without any additional text."
        )

    async def _call_llm(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"Groq LLM API error: {response.text}")
            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _parse_questions_response(self, response: str, expected_count: int) -> List[Dict]:
        try:
            questions = json.loads(response)
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            for q in questions:
                if "question" not in q:
                    q["question"] = q.get("text", "")
                if "category" not in q:
                    q["category"] = "technical"
                if "expected_duration" not in q:
                    q["expected_duration"] = 60
            return questions[:expected_count]
        except json.JSONDecodeError:
            return self._fallback_parse(response, expected_count)

    def _fallback_parse(self, response: str, expected_count: int) -> List[Dict]:
        questions = []
        lines = response.strip().split("\n")
        for line in lines[:expected_count]:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                question = line.lstrip("0123456789.-•) ").strip()
                if question:
                    questions.append(
                        {
                            "question": question,
                            "category": "technical",
                            "expected_duration": 60,
                        }
                    )
        return questions

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        job_title: Optional[str] = None,
    ) -> Dict:
        prompt = self._build_evaluation_prompt(question, answer, job_title)
        response = await self._call_llm(prompt)
        return self._parse_evaluation_response(response)

    def _build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        job_title: Optional[str],
    ) -> str:
        context = f" for a {job_title} position" if job_title else ""
        return (
            f"You are an AI interviewer evaluating a candidate's answer{context}.\n\n"
            f"Question: {question}\n\n"
            f"Candidate's Answer: {answer}\n\n"
            "Evaluate this answer on the following criteria (score 0-100 for each):\n"
            "1. Relevance - How well does it address the question?\n"
            "2. Depth - Does it show thorough understanding?\n"
            "3. Clarity - Is it well-organized and easy to understand?\n"
            "4. Examples - Does it include relevant concrete examples?\n\n"
            "Also provide:\n"
            "- Overall score (weighted average)\n"
            "- Strengths (list of 2-3 key strengths)\n"
            "- Areas for improvement (list of 2-3 areas)\n"
            "- Brief feedback (2-3 sentences)\n\n"
            "Return as JSON with keys: relevance, depth, clarity, examples, overall_score, strengths, improvements, feedback"
        )

    def _parse_evaluation_response(self, response: str) -> Dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse evaluation", "raw_response": response[:500]}

    async def generate_interview_question(
        self,
        job_role: str,
        question_type: str,
        previous_questions: List[Dict],
        previous_answers: List[str],
    ) -> Dict[str, str]:
        context = ""
        if previous_questions and previous_answers:
            context = "\nPrevious Q&A:\n"
            for q, a in zip(previous_questions[-3:], previous_answers[-3:]):
                context += f"Q: {q}\nA: {a}\n\n"

        prompt = (
            f"You are an AI interviewer for a {job_role} position.\n\n"
            f"{context}"
            f"Generate a {question_type} question to ask the candidate.\n\n"
            "Return a JSON object with:\n"
            "- 'question': The interview question\n"
            "- 'question_type': The type of question\n"
            "- 'category': One of 'technical', 'behavioral', 'problem_solving', 'culture_fit', 'introduction'\n"
            "- 'difficulty': 'easy', 'medium', or 'hard'\n"
            "- 'expected_duration': Time to answer in seconds"
        )

        response = await self._call_llm(prompt)
        try:
            return json.loads(response)
        except Exception:
            return {
                "question": f"Tell me about your experience with {job_role}",
                "question_type": question_type,
                "category": "introduction",
                "difficulty": "easy",
                "expected_duration": 60,
            }


async def generate_interview_question(
    job_role: str,
    question_type: str,
    previous_questions: List[Dict],
    previous_answers: List[str],
) -> Dict[str, str]:
    service = LLMService()
    return await service.generate_interview_question(
        job_role, question_type, previous_questions, previous_answers
    )


async def evaluate_answer(question: str, answer: str, job_title: Optional[str] = None) -> Dict:
    service = LLMService()
    return await service.evaluate_answer(question, answer, job_title)


_INTERVIEWER_SYSTEM = """
You are a senior hiring manager at a technology company running a structured live interview.
You are rigorous, fair, and focused on signal: judgment and evidence — not buzzwords.

SCOPE (mandatory):
- You generate ONLY introduction, behavioral, and cv_based questions in this response.
- NEVER output technical or coding questions — they are produced by a separate Grok call.

TONE:
- Professional and direct; warm but not chatty.

VERBAL RULES:
- Ask ONE clear prompt per JSON object.
- At most 2 short sentences each (voice / TTS friendly).

OUTPUT must be valid JSON only. No extra text. No markdown.
"""


_CODING_GENERATOR_SYSTEM = """
You generate interview coding challenges for an automated judge.
STYLE: LeetCode / HackerRank — scenario-led algorithm tasks (clear I/O), NOT trivia or HR prompts.
OUTPUT: valid JSON array ONLY. No markdown. No commentary outside JSON.
Each problem must have unambiguous stdin/stdout and exactly 2 public_test_cases with precise expected_stdout (use \\n where line endings matter).
Do NOT include full solutions in starter_code — omit starter_code or use only empty def main(): pass skeleton.
"""


_MINIMAL_PYTHON_STDIO_STARTER = (
    "import sys\n\n\n"
    "def main():\n"
    "    # TODO: read stdin, solve, print to stdout.\n"
    "    pass\n\n\n"
    'if __name__ == "__main__":\n'
    "    main()\n"
)


_EVALUATOR_SYSTEM = """
You are an expert HR evaluator. Evaluate interview answers objectively.
SCORING (each 0-10):
- relevance_score: How directly did the answer address the question?
- depth_score: Did they give specific examples, metrics, details?
- communication_score: Clarity, structure, conciseness
CORRECTNESS / ACCURACY:
- is_correct: true/false (answer sufficiently correct for the question's expectations)
- accuracy_score: 0-100 (percentage match to expected content inferred from the question)
OUTPUT must be valid JSON only. No extra text. No markdown fences.
"""


def _normalize_question_text(text: str) -> str:
    cleaned = (text or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


# Fixed live interview: 2 + 7 + 4 + 4 verbal + 3 coding = 20 (must match API schema default).
LIVE_INTERVIEW_INTRO_COUNT = 2
LIVE_INTERVIEW_TECHNICAL_COUNT = 7
LIVE_INTERVIEW_BEHAVIORAL_COUNT = 4
LIVE_INTERVIEW_CV_COUNT = 4
LIVE_INTERVIEW_CODING_COUNT = 3
LIVE_INTERVIEW_TOTAL_QUESTIONS = (
    LIVE_INTERVIEW_INTRO_COUNT
    + LIVE_INTERVIEW_TECHNICAL_COUNT
    + LIVE_INTERVIEW_BEHAVIORAL_COUNT
    + LIVE_INTERVIEW_CV_COUNT
    + LIVE_INTERVIEW_CODING_COUNT
)


def _coding_challenge_count(total_questions: int) -> int:
    """Always three LeetCode-style rounds: easy → medium → hard."""
    return 3


def _verbal_question_budget(total_questions: int, coding_n: int) -> int:
    """Verbal slots = total interview length minus coding rounds."""
    return int(total_questions) - int(coding_n)


def _allocate_four_phase_counts(total_questions: int) -> tuple[int, int, int, int]:
    """
    Split total into: introduction, technical, behavioral, cv_based.
    Phase order in the interview: introduction → technical → behavioral → cv_based.
    Always exactly 1 introduction when total >= 4.
    """
    t = max(4, min(12, int(total_questions)))
    intro = 1
    r = t - intro  # questions left after introduction
    # Explicit splits so counts always sum to t (r ranges 3..11)
    splits = {
        3: (1, 1, 1),
        4: (2, 1, 1),
        5: (2, 2, 1),
        6: (2, 2, 2),
        7: (3, 2, 2),
        8: (3, 2, 3),
        9: (4, 3, 2),
        10: (4, 3, 3),
        11: (5, 3, 3),
    }
    tech, beh, cv = splits[r]
    return intro, tech, beh, cv


def _project_summary(candidate_projects: List[dict]) -> str:
    if not candidate_projects:
        return "No project details available."
    lines = []
    for idx, p in enumerate(candidate_projects[:5], start=1):
        name = str((p or {}).get("name", "")).strip() or f"Project {idx}"
        desc = str((p or {}).get("description", "")).strip()
        lines.append(f"- {name}: {desc}" if desc else f"- {name}")
    return "\n".join(lines)


_TECHNICAL_BLOCK_SYSTEM = """
You output ONLY a JSON array (no markdown) of TECHNICAL interview questions for a live voice interview.

SCOPE (strict — violations are unacceptable):
- Every question MUST be answerable using ONLY: the JOB ROLE title, the JOB DESCRIPTION text, and the
  REQUIRED JOB SKILLS list supplied in the user message.
- Do NOT invent topics from the candidate's CV, hobbies, or unrelated stacks. Do NOT pivot to languages,
  frameworks, or platforms that are not named in REQUIRED JOB SKILLS or clearly required by the JOB DESCRIPTION.
- If a skill is ambiguous, tie it to how that role would use it per the JD.

DEPTH & STYLE (concept exam, not behavioral):
- Senior interviewer tone: precise, textbook-plus depth — mechanisms, definitions, classifications, trade-offs.
- Prefer question families such as: \"What is … and what problem does it solve?\", \"How does … differ from …
  for this role?\", \"What are the main types / modes / variants of … and when would you pick each?\",
  \"Explain how … works internally at a level you could whiteboard.\", \"What invariants or contracts does …
  assume?\", \"What breaks first when … misconfigured or under load?\", \"Compare correctness vs performance
  trade-offs for … in this role.\"
- Each question must feel like a different *conceptual lens* (definition vs comparison vs types vs internals
  vs failure mode vs trade-off vs boundary conditions).

DIVERSITY:
- No two questions may share the same opening six words.
- Do NOT use generic behavioral or STAR framing (\"tell me about a time\", \"describe a project\").
- Do NOT use boilerplate: \"production scenario\", \"walk me through how you would apply\", \"your experience with\".

SKILL COVERAGE:
- Each question MUST explicitly name at least one REQUIRED JOB SKILL (exact spelling) when the list is non-empty.
- Across the full set of N questions, every REQUIRED skill must appear in at least one question.
- If REQUIRED list is empty, anchor every question to concrete nouns from the JOB DESCRIPTION + JOB ROLE only.

FORMAT:
- Each object: question_text (string), question_type (\"technical\"), stage (\"technical\"), difficulty (easy|medium|hard).

OUTPUT: JSON array only, length exactly N (given in user message).
"""


_TECH_CONCEPT_LENSES = [
    "Definition — What is it, what problem does it solve, and what are the non-negotiable terms?",
    "Difference — Contrast two related concepts, tools, or approaches within the SAME required skill or JD scope.",
    "Types / modes — Main variants or categories; when would you pick each for this job role?",
    "Internals — How does it work under the hood at a whiteboard depth (still scoped to role + required skills)?",
    "Correctness — Invariants, contracts, edge cases, or validation logic tied to the skill/JD.",
    "Trade-offs — e.g. latency vs consistency, memory vs speed, safety vs velocity — grounded in this role.",
    "Failure & debugging — What typically breaks, what symptoms you see, how you narrow root cause.",
]


def _technical_concept_lens_lines(start_index: int, count: int) -> str:
    """Ordered conceptual lenses so each slot is definition / diff / types / etc."""
    lines = []
    for i in range(max(0, count)):
        lens = _TECH_CONCEPT_LENSES[(start_index + i) % len(_TECH_CONCEPT_LENSES)]
        lines.append(f"  — Slot {i + 1}: {lens}")
    return "\n".join(lines) if lines else "(no slots)"


def _skill_mentioned_in_blob(skill: str, blob: str) -> bool:
    s = (skill or "").strip().lower()
    if not s:
        return True
    if s in blob:
        return True
    compact = re.sub(r"[^a-z0-9]+", "", s)
    blob_c = re.sub(r"[^a-z0-9]+", "", blob)
    if len(compact) >= 3 and compact in blob_c:
        return True
    tokens = [t for t in re.split(r"[\s/,.|+_-]+", s) if len(t) >= 3]
    if len(tokens) >= 2 and all(t in blob for t in tokens[:2]):
        return True
    if len(tokens) == 1 and tokens[0] in blob:
        return True
    return False


def _parse_technical_llm_items(raw: str, max_items: int, seen_norm: set) -> List[dict]:
    if not raw or max_items <= 0:
        return []
    try:
        arr = _parse_json_array(raw)
    except Exception:
        return []
    out: List[dict] = []
    for item in arr:
        if len(out) >= max_items:
            break
        if not isinstance(item, dict):
            continue
        text = str(item.get("question_text", "")).strip()
        if len(text) < 20:
            continue
        low = text.lower()
        if "production scenario" in low or "walk me through how you would apply" in low:
            continue
        if "tell me about a time" in low or "describe a time when" in low or "give me an example of when you" in low:
            continue
        q_type = str(item.get("question_type", "technical")).strip().lower()
        stage = str(item.get("stage", "technical")).strip().lower()
        if q_type != "technical" or stage != "technical":
            continue
        diff = str(item.get("difficulty", "medium")).strip().lower()
        if diff not in {"easy", "medium", "hard"}:
            diff = "medium"
        key = _normalize_question_text(text)
        if not key or key in seen_norm:
            continue
        seen_norm.add(key)
        out.append(
            {
                "question_text": text,
                "question_type": "technical",
                "stage": "technical",
                "difficulty": diff,
            }
        )
    return out


def _generate_technical_block_llm(
    job_role: str,
    job_description: str,
    required_job_skills: List[str],
    _candidate_skills: List[str],
    _experience_years: Optional[int],
    num_questions: int,
    seen_norm: set,
) -> List[dict]:
    """Dedicated Grok/Groq pass for technical-only questions (role + required skills + JD)."""
    n = max(0, int(num_questions))
    if n == 0:
        return []

    req = ", ".join(str(s).strip() for s in (required_job_skills or []) if str(s).strip())
    jd = (job_description or "").strip() or "Not provided."
    if len(jd) > 2800:
        jd = jd[:2800] + "…"

    merged: List[dict] = []
    seen_local = set(seen_norm)
    for _round_idx in range(3):
        need = n - len(merged)
        if need <= 0:
            break
        variation = secrets.token_hex(5)
        offset = len(merged)
        lens_lines = _technical_concept_lens_lines(offset, need)
        avoid = ""
        if merged:
            avoid = (
                "ALREADY GENERATED (do not repeat or paraphrase closely; write completely new questions):\n"
                + "\n".join(f"- {q['question_text'][:220]}" for q in merged[:12])
            )
        prompt = (
            f"N = {need}. Generate exactly {need} technical interview questions as a JSON array.\n"
            f"Round id: {variation}\n\n"
            f"PRIMARY ANCHORS (use these alone for topic selection): JOB ROLE, JOB DESCRIPTION, REQUIRED JOB SKILLS.\n"
            "Do NOT introduce technologies or domains that are not in REQUIRED JOB SKILLS or plainly implied by the "
            "JOB DESCRIPTION for this JOB ROLE. Ignore candidate CV skills unless they exactly duplicate a required "
            "skill string.\n\n"
            f"JOB ROLE: {job_role}\n\nJOB DESCRIPTION:\n{jd}\n\n"
            f"REQUIRED JOB SKILLS: {req or '(none — derive concrete technical nouns only from JD + role title)'}\n\n"
            "CONCEPTUAL LENS — apply one lens per question in slot order (each question a different style):\n"
            f"{lens_lines}\n\n"
            f"{avoid}\n\n"
            "Return ONLY the JSON array.\n"
        )
        raw = _interview_question_llm(
            [{"role": "user", "content": prompt}],
            system=_TECHNICAL_BLOCK_SYSTEM,
            temperature=0.88,
            max_tokens=min(7000, 620 * need),
        )
        batch = _parse_technical_llm_items(raw, need, seen_local)
        merged.extend(batch)
        merged = merged[:n]

    # Ensure required skills appear by name (one extra focused Grok pass if needed)
    blob = " ".join(q.get("question_text", "").lower() for q in merged)
    missing = [s for s in (required_job_skills or []) if str(s).strip() and not _skill_mentioned_in_blob(s, blob)]
    if missing and len(merged) < n:
        need = min(len(missing), n - len(merged))
        spec = ", ".join(str(s).strip() for s in missing[:6])
        lens2 = _technical_concept_lens_lines(len(merged), need)
        jd_excerpt = jd[:1400] if len(jd) > 1400 else jd
        raw2 = _interview_question_llm(
            [
                {
                    "role": "user",
                    "content": (
                        f"Generate exactly {need} NEW technical JSON objects (same schema as before).\n"
                        f"JOB ROLE: {job_role}\n"
                        f"JOB DESCRIPTION (excerpt): {jd_excerpt}\n\n"
                        f"Each question_text MUST visibly include one of these REQUIRED skill names "
                        f"(verbatim substring): {spec}.\n"
                        "Scope: only this role, this JD, and those skills — no CV topics or unrelated stacks.\n"
                        "CONCEPTUAL LENS — one per question in slot order (definition / compare / types / internals / "
                        "correctness / trade-offs / failure):\n"
                        f"{lens2}\n\n"
                        "No behavioral or STAR framing. Return ONLY the JSON array."
                    ),
                }
            ],
            system=_TECHNICAL_BLOCK_SYSTEM,
            temperature=0.82,
            max_tokens=2800,
        )
        merged.extend(_parse_technical_llm_items(raw2, need, seen_local))
        merged = merged[:n]

    return merged[:n]


def _finalize_technical_length(technical: List[dict], technical_count: int) -> List[dict]:
    """Trim to count; caller must have produced enough via Grok rounds."""
    return technical[:technical_count]


def _build_fallback_question_bank(
    job_role: str,
    required_job_skills: List[str],
    candidate_skills: List[str],
    candidate_projects: List[dict],
    candidate_job_titles: List[str],
    candidate_certifications: List[str],
    candidate_companies: List[str],
    experience_years: Optional[int],
) -> List[dict]:
    all_skills = list(dict.fromkeys((required_job_skills or []) + (candidate_skills or [])))
    top_skills = all_skills[:6]
    projects = candidate_projects or []
    exp_ctx = f"{experience_years} years of experience" if experience_years is not None else "your experience"

    technical_questions = []
    for idx, skill in enumerate(top_skills):
        difficulty = "easy" if idx < 2 else ("medium" if idx < 5 else "hard")
        technical_questions.append(
            {
                "question_text": f"For a {job_role} role, explain how you would apply {skill} in a production scenario and what tradeoffs you would consider.",
                "question_type": "technical",
                "stage": "technical",
                "difficulty": difficulty,
            }
        )
    while len(technical_questions) < 7:
        technical_questions.append(
            {
                "question_text": f"Design an end-to-end {job_role} solution using {', '.join(top_skills[:3]) if top_skills else 'your stack'} and explain reliability, scalability, and observability decisions.",
                "question_type": "technical",
                "stage": "technical",
                "difficulty": "hard",
            }
        )

    cv_questions = []

    # Work experience / roles / responsibilities / collaboration
    if candidate_job_titles:
        cv_questions.append(
            {
                "question_text": f"In your role as {candidate_job_titles[0]}, what were your top responsibilities and how did you collaborate with your team?",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "medium",
            }
        )
    if candidate_companies:
        cv_questions.append(
            {
                "question_text": f"At {candidate_companies[0]}, describe one difficult problem you solved and the concrete result of your solution.",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "medium",
            }
        )
    for p in projects[:4]:
        name = str((p or {}).get("name", "")).strip()
        desc = str((p or {}).get("description", "")).strip()
        if name:
            cv_questions.append(
                {
                    "question_text": f"In your project '{name}', what was your specific contribution, the hardest challenge, and the measurable impact?",
                    "question_type": "cv_based",
                    "stage": "cv_based",
                    "difficulty": "medium",
                }
            )
            if desc:
                cv_questions.append(
                    {
                        "question_text": f"Based on '{name}', explain one technical decision you made and why that choice was better than alternatives.",
                        "question_type": "cv_based",
                        "stage": "cv_based",
                        "difficulty": "hard",
                    }
                )
        if len(cv_questions) >= 10:
            break

    if candidate_certifications:
        cv_questions.append(
            {
                "question_text": f"You listed {candidate_certifications[0]}. What did you learn from it and where did you apply that knowledge in practice?",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "medium",
            }
        )

    if candidate_skills:
        cv_questions.append(
            {
                "question_text": f"You mentioned {candidate_skills[0]} in your CV. Give a real scenario where you used it, including architecture, APIs, and database decisions.",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "hard",
            }
        )

    cv_questions.extend(
        [
            {
                "question_text": f"Across {exp_ctx}, which skill on your CV do you consider strongest, and what evidence supports that?",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "medium",
            },
            {
                "question_text": "Describe one project from your CV that did not go as planned and explain what you changed afterward.",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "medium",
            },
            {
                "question_text": "If you had to improve one CV project today, what would you redesign first and why?",
                "question_type": "cv_based",
                "stage": "cv_based",
                "difficulty": "hard",
            },
        ]
    )
    cv_questions = cv_questions[:4]

    introduction_q = [
        {
            "question_text": f"Please introduce yourself: your background, education, and why you are interested in this {job_role} role.",
            "question_type": "introduction",
            "stage": "introduction",
            "difficulty": "easy",
        },
        {
            "question_text": f"In one minute, what should we know about your trajectory that is not obvious from your CV alone for this {job_role} role?",
            "question_type": "introduction",
            "stage": "introduction",
            "difficulty": "easy",
        },
    ]

    behavioral_q = [
        {"question_text": "Describe a time you handled a difficult stakeholder or teammate. What did you do and what was the outcome?", "question_type": "behavioral", "stage": "behavioral", "difficulty": "easy"},
        {"question_text": "Share an example where you made a mistake in a project. How did you recover and what did you learn?", "question_type": "behavioral", "stage": "behavioral", "difficulty": "medium"},
        {"question_text": "Tell me about a time you had competing priorities. How did you decide what to do first?", "question_type": "behavioral", "stage": "behavioral", "difficulty": "medium"},
        {"question_text": "Describe a situation where you had to learn a new technology quickly to deliver results.", "question_type": "behavioral", "stage": "behavioral", "difficulty": "medium"},
        {"question_text": "Tell me about a time you helped resolve conflict or disagreements within a team.", "question_type": "behavioral", "stage": "behavioral", "difficulty": "medium"},
    ]

    # Order: introduction → technical → behavioral → CV-based (matches interview phases)
    return [
        *introduction_q[:2],
        *technical_questions[:7],
        *behavioral_q[:4],
        *cv_questions[:4],
    ]


def _fallback_coding_challenges(job_role: str, n: int) -> List[dict]:
    """Deterministic LeetCode-style tasks when the LLM fails (stdin/stdout, Python)."""
    role_hint = (job_role or "software").strip()
    pool = [
        {
            "title": f"Easy — duplicate IDs ({role_hint})",
            "problem_statement": (
                "Scenario: You audit a batch of ticket IDs. "
                "Read stdin: first line integer n (2 ≤ n ≤ 2000), second line n integers. "
                "Print YES if any integer appears at least twice, otherwise print NO. "
                "Single line output with newline."
            ),
            "difficulty": "easy",
            "recommended_languages": ["python", "javascript", "cpp", "java"],
            "constraints": "O(n) time; values fit in 32-bit signed range.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    # TODO: detect duplicate\n"
                "    pass\n\n\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "duplicate present",
                    "stdin": "5\n4 2 7 2 1\n",
                    "expected_stdout": "YES\n",
                },
                {
                    "description": "all distinct",
                    "stdin": "4\n1 2 3 4\n",
                    "expected_stdout": "NO\n",
                },
            ],
        },
        {
            "title": f"Medium — valid bracket sequence ({role_hint})",
            "problem_statement": (
                "Scenario: Validate a string of brackets for a config DSL. "
                "Read one line from stdin containing only characters ( ) [ ] { }. "
                "Print YES if the brackets are properly nested and closed in order (LeetCode-style validity), "
                "otherwise NO. Output one word plus newline."
            ),
            "difficulty": "medium",
            "recommended_languages": ["python", "javascript", "cpp", "java"],
            "constraints": "Line length ≤ 2000.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    line = sys.stdin.readline().strip()\n"
                "    # TODO: stack-based validation\n"
                "    pass\n\n\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "valid mixed",
                    "stdin": "()[]{}\n",
                    "expected_stdout": "YES\n",
                },
                {
                    "description": "invalid nesting",
                    "stdin": "([)]\n",
                    "expected_stdout": "NO\n",
                },
            ],
        },
        {
            "title": f"Hard — maximum subarray throughput ({role_hint})",
            "problem_statement": (
                "Scenario: Hourly metrics can be negative (downtime). "
                "Read stdin: first line integer n (1 ≤ n ≤ 5000), second line n integers (may be negative). "
                "Print the maximum possible sum of a contiguous subarray (Kadane's algorithm). "
                "Print one integer followed by newline."
            ),
            "difficulty": "hard",
            "recommended_languages": ["python", "javascript", "cpp", "java"],
            "constraints": "O(n) required; answer fits 64-bit signed.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    # TODO: Kadane max subarray sum\n"
                "    pass\n\n\n"
                'if __name__ == "__main__":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "mixed values",
                    "stdin": "4\n1 -2 3 4\n",
                    "expected_stdout": "7\n",
                },
                {
                    "description": "single element",
                    "stdin": "1\n-5\n",
                    "expected_stdout": "-5\n",
                },
            ],
        },
    ]
    out = []
    for i in range(min(n, len(pool))):
        item = dict(pool[i])
        item.setdefault("evaluation_notes", "Future runner will execute stdin/stdout against hidden suites.")
        out.append(item)
    while len(out) < n:
        extra = dict(pool[len(out) % len(pool)])
        extra["title"] = extra["title"] + f" (variant {len(out) + 1})"
        out.append(extra)
    return out[:n]


def _normalize_public_cases(raw_cases: List) -> List[Dict]:
    out = []
    for c in raw_cases or []:
        if not isinstance(c, dict):
            continue
        stdin = str(c.get("stdin", "") or "")
        exp = str(c.get("expected_stdout", c.get("expected_output", "")) or "")
        desc = str(c.get("description", c.get("explanation", "")) or "").strip()
        if stdin or exp:
            out.append(
                {
                    "description": desc or "sample case",
                    "stdin": stdin,
                    "expected_stdout": exp if exp.endswith("\n") or not exp else exp + "\n",
                }
            )
    return out


def _coding_challenge_dict_from_llm(obj: dict) -> Optional[dict]:
    if not isinstance(obj, dict):
        return None
    title = str(obj.get("title", "")).strip()
    stmt = str(obj.get("problem_statement", obj.get("description", ""))).strip()
    if not title and not stmt:
        return None
    if not title:
        title = "Coding challenge"
    langs = obj.get("recommended_languages") or obj.get("allowed_languages") or ["python"]
    if isinstance(langs, str):
        langs = [langs]
    langs = [str(x).strip().lower() for x in langs if str(x).strip()]
    if not langs:
        langs = ["python"]
    starter = _MINIMAL_PYTHON_STDIO_STARTER
    cases = _normalize_public_cases(obj.get("public_test_cases") or [])
    if len(cases) < 1:
        return None
    return {
        "title": title,
        "problem_statement": stmt or title,
        "difficulty": str(obj.get("difficulty", "medium")).lower()
        if str(obj.get("difficulty", "")).lower() in {"easy", "medium", "hard"}
        else "medium",
        "recommended_languages": langs,
        "constraints": str(obj.get("constraints", "") or "").strip(),
        "starter_code": starter,
        "public_test_cases": cases,
        "evaluation_notes": str(
            obj.get(
                "evaluation_notes",
                "Automated execution and hidden tests will be added by the coding module.",
            )
        ),
    }


def _assign_coding_ladder_difficulties(challenges: List[dict]) -> None:
    """Force interview order: easy → medium → hard (three rounds)."""
    ladder = ("easy", "medium", "hard")
    for i, ch in enumerate(challenges):
        ch["difficulty"] = ladder[i] if i < len(ladder) else ladder[-1]


async def _generate_coding_challenges_llm(
    job_role: str,
    job_description: str,
    required_job_skills: List[str],
    candidate_skills: List[str],
    num_problems: int,
) -> List[dict]:
    skill_ctx = ", ".join((required_job_skills or [])[:12]) or "general CS"
    cand_ctx = ", ".join((candidate_skills or [])[:12]) or "not specified"
    prompt = (
        f"Entropy: {secrets.token_hex(4)}\n"
        f"Generate exactly {num_problems} DISTINCT programming problems for a '{job_role}' interview.\n"
        f"Company/job context (flavor only): {(job_description or '')[:1200]}\n"
        f"Topics to reflect where sensible: {skill_ctx}\n"
        f"Candidate skill hints: {cand_ctx}\n\n"
        "STYLE (mandatory):\n"
        "- LeetCode / competitive-programming style: scenario hook + precise I/O spec + constraints.\n"
        "- Each problem must feel different (vary patterns: hashing, two pointers, stack/queues, greedy, "
        "binary search on answer, sliding window, trees/graphs on SMALL inputs, classic DP, union-find, etc.).\n"
        "- Do NOT reuse the same core trick twice across the three problems.\n"
        "- FORBIDDEN as standalone tasks: trivial 'reverse this string', plain palindrome check only, "
        "classroom-only FizzBuzz, or duplicate warm-ups.\n\n"
        "DIFFICULTY LADDER — output array order MUST be:\n"
        "  [0] EASY — ~LeetCode easy (15–20 min): arrays/strings, hash counts, simple traversal.\n"
        "  [1] MEDIUM — ~LeetCode medium: greedy/stack/BFS/DFS on bounded input, two-pointer non-trivial, "
        "intervals, or heaps.\n"
        "  [2] HARD — ~LeetCode hard (still bounded by constraints): DP, harder greedy, graphs/trees with "
        "clear limits, or tricky sliding window.\n\n"
        "TECHNICAL RULES:\n"
        "- stdin/stdout only; describe formats exactly (line breaks matter).\n"
        "- Exactly 2 public_test_cases per problem with precise stdin and expected_stdout "
        "(include trailing \\n on stdout lines where applicable).\n"
        "- Omit starter_code from JSON (the platform injects a minimal Python stdin/stdout stub).\n"
        '- recommended_languages: ["python","javascript","cpp","java"] unless problem demands otherwise.\n'
        "- Numbers fit standard 64-bit signed unless you state otherwise.\n\n"
        "Return ONLY a JSON array (no markdown) of exactly "
        f"{num_problems} objects in easy→medium→hard order. Fields per object: title, problem_statement, "
        "difficulty, recommended_languages, constraints, public_test_cases (2 items), evaluation_notes. "
        "Do NOT include starter_code.\n"
        "[{\n"
        '  "title": "...",\n'
        '  "problem_statement": "...",\n'
        '  "difficulty": "easy|medium|hard",\n'
        '  "recommended_languages": ["python","javascript","cpp","java"],\n'
        '  "constraints": "time/space bounds",\n'
        '  "public_test_cases": [\n'
        '    {"description": "...", "stdin": "...", "expected_stdout": "..."}\n'
        "  ],\n"
        '  "evaluation_notes": "pattern name e.g. Kadane, monotonic stack"\n'
        "}]\n"
    )
    normalized: List[dict] = []
    for attempt in range(2):
        raw = _interview_question_llm(
            [{"role": "user", "content": prompt}],
            system=_CODING_GENERATOR_SYSTEM,
            temperature=0.62 if attempt == 0 else 0.78,
            max_tokens=7200,
        )
        try:
            arr = _parse_json_array(raw)
        except Exception:
            arr = []
        for item in arr:
            ch = _coding_challenge_dict_from_llm(item if isinstance(item, dict) else {})
            if ch:
                normalized.append(ch)
            if len(normalized) >= num_problems:
                break
        if len(normalized) >= num_problems:
            break
    if len(normalized) < num_problems:
        raise RuntimeError(
            f"Grok returned only {len(normalized)}/{num_problems} valid coding challenges after retry. "
            "Check API key and response format."
        )
    out = normalized[:num_problems]
    _assign_coding_ladder_difficulties(out)
    return out


def _question_entries_from_coding_challenges(challenges: List[dict]) -> List[dict]:
    rows = []
    total_c = len(challenges)
    for idx, ch in enumerate(challenges):
        stmt = ch.get("problem_statement") or ch.get("title") or ""
        teaser = stmt[:320] + ("…" if len(stmt) > 320 else "")
        tier = str(ch.get("difficulty") or "medium").lower()
        voice_intro = (
            f"This is coding problem {idx + 1} of {total_c}, {tier} difficulty: {ch.get('title')}. "
            "Follow the on-screen specification and starter code. "
            "Outline your approach briefly, then implement."
        )
        rows.append(
            {
                "question_text": voice_intro + " Problem summary: " + teaser,
                "question_type": "coding",
                "stage": "coding",
                "difficulty": ch.get("difficulty", "medium"),
                "coding_challenge": ch,
            }
        )
    return rows


async def generate_question_plan(
    job_role: str,
    job_description: str,
    candidate_skills: List[str],
    required_job_skills: Optional[List[str]] = None,
    candidate_projects: Optional[List[dict]] = None,
    candidate_job_titles: Optional[List[str]] = None,
    candidate_certifications: Optional[List[str]] = None,
    candidate_companies: Optional[List[str]] = None,
    experience_years: Optional[int] = None,
    asked_questions: Optional[List[str]] = None,
    total_questions: int = LIVE_INTERVIEW_TOTAL_QUESTIONS,
) -> List[dict]:
    _ = total_questions  # fixed product: 20 questions (see LIVE_INTERVIEW_* constants)
    coding_count = LIVE_INTERVIEW_CODING_COUNT
    intro_count = LIVE_INTERVIEW_INTRO_COUNT
    technical_count = LIVE_INTERVIEW_TECHNICAL_COUNT
    behavioral_count = LIVE_INTERVIEW_BEHAVIORAL_COUNT
    cv_based_count = LIVE_INTERVIEW_CV_COUNT
    non_technical_total = intro_count + behavioral_count + cv_based_count
    target_verbal_total = (
        intro_count + technical_count + behavioral_count + cv_based_count
    )

    asked_questions = asked_questions or []
    asked_norm = {
        _normalize_question_text(q) for q in asked_questions if _normalize_question_text(q)
    }
    project_ctx = _project_summary(candidate_projects or [])

    prompt = (
        f"Session entropy: {secrets.token_hex(4)}\n"
        "You are a senior hiring manager. Generate ONLY non-technical verbal interview questions.\n"
        f"A separate Grok call will add {technical_count} technical questions and {coding_count} coding exercises — "
        "do NOT output technical or coding here.\n\n"
        "PHASES for this response (strict order in the JSON array):\n"
        f"1) introduction: exactly {intro_count} question(s) — background and motivation for this role. "
        "No STAR behavioral prompts.\n"
        f"2) behavioral: exactly {behavioral_count} questions — STAR-style past behavior.\n"
        f"3) cv_based: exactly {cv_based_count} questions — reference CV context below.\n\n"
        f"JOB ROLE: {job_role}\n\nJOB DESCRIPTION: {job_description or 'Standard role'}\n\n"
        f"REQUIRED JOB SKILLS (tone context only): {', '.join(required_job_skills or []) or 'Not provided'}\n\n"
        f"CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Not provided'}\n\n"
        f"CANDIDATE EXPERIENCE (YEARS): {experience_years if experience_years is not None else 'Not provided'}\n\n"
        f"CANDIDATE PROJECTS:\n{project_ctx}\n\n"
        f"CANDIDATE JOB TITLES: {candidate_job_titles or []}\n"
        f"CANDIDATE CERTIFICATIONS: {candidate_certifications or []}\n"
        f"CANDIDATE COMPANIES/INTERNSHIPS: {candidate_companies or []}\n\n"
        f"ALREADY ASKED (DO NOT REPEAT): {asked_questions}\n\n"
        "RULES: unique questions; phase order = introduction, then behavioral, then cv_based.\n\n"
        f"Return ONLY a JSON array of exactly {non_technical_total} objects with keys "
        "question_text, question_type, stage, difficulty.\n"
    )

    raw = _interview_question_llm(
        [{"role": "user", "content": prompt}],
        system=_INTERVIEWER_SYSTEM,
        temperature=0.78,
        max_tokens=4200,
    )
    try:
        generated = _parse_json_array(raw)
    except Exception as exc:
        raise RuntimeError("Grok returned invalid JSON for non-technical interview questions.") from exc

    clean_questions: List[dict] = []
    seen_norm = set(asked_norm)

    for q in generated:
        text = str((q or {}).get("question_text", "")).strip()
        q_type = str((q or {}).get("question_type", "")).strip().lower()
        stage = str((q or {}).get("stage", "")).strip().lower() or q_type
        difficulty = str((q or {}).get("difficulty", "")).strip().lower() or "medium"

        if not text:
            continue
        if q_type not in {"introduction", "behavioral", "cv_based"}:
            continue
        if stage not in {"introduction", "behavioral", "cv_based"}:
            stage = q_type
        if stage not in {"introduction", "behavioral", "cv_based"}:
            continue
        key = _normalize_question_text(text)
        if not key or key in seen_norm:
            continue
        seen_norm.add(key)
        clean_questions.append(
            {
                "question_text": text,
                "question_type": q_type,
                "stage": stage,
                "difficulty": difficulty if difficulty in {"easy", "medium", "hard"} else "medium",
            }
        )

    introduction = [q for q in clean_questions if q["stage"] == "introduction"][:intro_count]
    behavioral = [q for q in clean_questions if q["stage"] == "behavioral"][:behavioral_count]
    cv_based = [q for q in clean_questions if q["stage"] == "cv_based"][:cv_based_count]

    if intro_count >= 1 and len(introduction) < intro_count:
        introduction.append(
            {
                "question_text": f"Please introduce yourself: your background, education, and why this {job_role} role interests you.",
                "question_type": "introduction",
                "stage": "introduction",
                "difficulty": "easy",
            }
        )
        introduction = introduction[:intro_count]

    cv_text_blob = " ".join(q.get("question_text", "").lower() for q in cv_based)
    needs_projects = bool(candidate_projects) and not any(
        str((p or {}).get("name", "")).strip().lower() in cv_text_blob
        for p in (candidate_projects or [])
        if str((p or {}).get("name", "")).strip()
    )
    needs_skills = bool(candidate_skills) and not any(s.lower() in cv_text_blob for s in candidate_skills[:8])
    needs_experience = "experience" not in cv_text_blob and "years" not in cv_text_blob

    if needs_projects:
        p_name = str(((candidate_projects or [])[0] or {}).get("name", "")).strip() or "a project from your CV"
        cv_q = {
            "question_text": f"In '{p_name}', what was your exact role, technical approach, and measurable impact?",
            "question_type": "cv_based",
            "stage": "cv_based",
            "difficulty": "medium",
        }
        if len(cv_based) < cv_based_count:
            cv_based.append(cv_q)
        else:
            cv_based[-1] = cv_q

    if needs_skills:
        top_cv_skill = (candidate_skills or ["your strongest skill"])[0]
        cv_q = {
            "question_text": f"Which CV skill best represents your strengths, and where did you apply {top_cv_skill} in real work?",
            "question_type": "cv_based",
            "stage": "cv_based",
            "difficulty": "medium",
        }
        if len(cv_based) < cv_based_count:
            cv_based.append(cv_q)
        else:
            cv_based[-1] = cv_q

    if needs_experience:
        cv_q = {
            "question_text": "Looking at your overall experience, what pattern of growth do you see and how has it changed your engineering decisions?",
            "question_type": "cv_based",
            "stage": "cv_based",
            "difficulty": "hard",
        }
        if len(cv_based) < cv_based_count:
            cv_based.append(cv_q)
        else:
            cv_based[-1] = cv_q

    behavioral = behavioral[:behavioral_count]
    cv_based = cv_based[:cv_based_count]

    if len(introduction) < intro_count or len(behavioral) < behavioral_count or len(cv_based) < cv_based_count:
        need_i = intro_count - len(introduction)
        need_b = behavioral_count - len(behavioral)
        need_c = cv_based_count - len(cv_based)
        top = (
            f"Return ONLY a JSON array of exactly {need_i + need_b + need_c} objects in this order:\n"
            f"- First {need_i} objects: stage introduction\n"
            f"- Next {need_b} objects: stage behavioral\n"
            f"- Last {need_c} objects: stage cv_based\n"
            "Each object: question_text, question_type, stage, difficulty. Job role and CV context as before.\n"
            f"JOB ROLE: {job_role}\nPROJECTS:\n{project_ctx}\n"
        )
        raw_top = _interview_question_llm(
            [{"role": "user", "content": top}],
            system=_INTERVIEWER_SYSTEM,
            temperature=0.82,
            max_tokens=3200,
        )
        try:
            extra = _parse_json_array(raw_top)
        except Exception:
            extra = []
        for q in extra:
            text = str((q or {}).get("question_text", "")).strip()
            st = str((q or {}).get("stage", "")).strip().lower()
            diff = str((q or {}).get("difficulty", "medium")).strip().lower() or "medium"
            if diff not in {"easy", "medium", "hard"}:
                diff = "medium"
            if not text or st not in {"introduction", "behavioral", "cv_based"}:
                continue
            key = _normalize_question_text(text)
            if not key or key in seen_norm:
                continue
            seen_norm.add(key)
            row = {"question_text": text, "question_type": st, "stage": st, "difficulty": diff}
            if st == "introduction" and len(introduction) < intro_count:
                introduction.append(row)
            elif st == "behavioral" and len(behavioral) < behavioral_count:
                behavioral.append(row)
            elif st == "cv_based" and len(cv_based) < cv_based_count:
                cv_based.append(row)

    if len(introduction) < intro_count or len(behavioral) < behavioral_count or len(cv_based) < cv_based_count:
        raise RuntimeError(
            "Grok did not return enough non-technical questions after top-up. "
            "Verify GROK_API_KEY and try again."
        )

    seen_for_tech = set(seen_norm)
    for q in introduction + behavioral + cv_based:
        k = _normalize_question_text(q.get("question_text", ""))
        if k:
            seen_for_tech.add(k)

    technical = _generate_technical_block_llm(
        job_role,
        job_description or "",
        required_job_skills or [],
        candidate_skills or [],
        experience_years,
        technical_count,
        seen_for_tech,
    )
    technical = _finalize_technical_length(technical, technical_count)
    if len(technical) < technical_count:
        raise RuntimeError(
            f"Grok returned only {len(technical)}/{technical_count} technical questions after retries. "
            "Try again or shorten job description / skill lists."
        )

    ordered_verbal = (introduction + technical + behavioral + cv_based)[:target_verbal_total]

    coding_chunks = await _generate_coding_challenges_llm(
        job_role=job_role,
        job_description=job_description or "",
        required_job_skills=required_job_skills or [],
        candidate_skills=candidate_skills or [],
        num_problems=coding_count,
    )
    coding_questions = _question_entries_from_coding_challenges(coding_chunks)

    return ordered_verbal + coding_questions


async def generate_followup_question(
    job_role: str,
    original_question: str,
    candidate_answer: str,
    conversation_history: List[dict],
    asked_questions: Optional[List[str]] = None,
    stage: Optional[str] = None,
) -> dict:
    asked_questions = asked_questions or []
    stage = (stage or "behavioral").strip().lower()
    if stage not in {"introduction", "behavioral", "technical", "cv_based"}:
        stage = "behavioral"

    prompt = (
        "The candidate gave a shallow answer. Generate ONE follow-up question.\n\n"
        f"ORIGINAL QUESTION: {original_question}\n\n"
        f"CANDIDATE'S ANSWER: {candidate_answer}\n\n"
        f"JOB ROLE: {job_role}\n\n"
        f"CURRENT STAGE: {stage}\n\n"
        f"ALREADY ASKED QUESTIONS (DO NOT REPEAT): {asked_questions}\n\n"
        "Rules:\n"
        "- Keep it to one question only\n"
        "- Must be different from all asked questions\n"
        "- Follow up directly on missing specifics from candidate answer\n\n"
        "Return ONLY this JSON:\n"
        "{\"question_text\": \"...\", \"question_type\": \"follow_up\", "
        "\"stage\": \"introduction|behavioral|technical|cv_based\", \"difficulty\": \"easy|medium|hard\"}"
    )

    history = conversation_history[-6:]
    raw = _try_interview_llm_call(history + [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=200)
    try:
        parsed = _parse_json(raw) if raw is not None else {}
    except Exception:
        parsed = {}
    text = str((parsed or {}).get("question_text", "")).strip()
    norm = _normalize_question_text(text)
    asked_norm = {_normalize_question_text(q) for q in asked_questions if _normalize_question_text(q)}

    if not text or norm in asked_norm:
        if stage == "introduction":
            text = "Could you add a bit more detail on your most relevant experience or education for this role?"
        elif stage in {"behavioral", "cv_based"}:
            text = "Could you give a specific real example with measurable impact and explain exactly what your contribution was?"
        else:
            text = "Please walk through your exact approach step by step, including tradeoffs and why you chose that design."

    return {
        "question_text": text,
        "question_type": "follow_up",
        "stage": stage,
        "difficulty": "medium",
    }


async def evaluate_answer_interview(
    question_text: str,
    question_type,
    candidate_transcript: str,
    job_role: str,
    frame_analysis=None,
):
    from app.interview.domain.interview_models import AnswerEvaluation

    frame_ctx = ""
    if frame_analysis:
        frame_ctx = (
            "\nVIDEO SIGNALS:\n"
            f"- Emotion: {frame_analysis.dominant_emotion}\n"
            f"- Gaze: {frame_analysis.gaze_direction}\n"
            f"- Looking away: {frame_analysis.looking_away_ratio:.0%}\n"
            f"- Flags: {', '.join(frame_analysis.suspicious_flags) or 'None'}\n"
        )

    prompt = (
        "Evaluate this interview answer:\n\n"
        f"JOB ROLE: {job_role}\n\n"
        f"QUESTION TYPE: {question_type}\n\n"
        f"QUESTION: {question_text}\n\n"
        "CANDIDATE ANSWER: "
        f"{candidate_transcript if candidate_transcript.strip() else '[No answer provided]'}\n\n"
        f"{frame_ctx}\n"
        "Return ONLY this JSON:\n"
        "{\n"
        "  \"relevance_score\": 0-10,\n"
        "  \"depth_score\": 0-10,\n"
        "  \"communication_score\": 0-10,\n"
        "  \"key_points_covered\": [\"point1\", \"point2\"],\n"
        "  \"missed_points\": [\"what was expected but missing\"],\n"
        "  \"is_correct\": true or false,\n"
        "  \"accuracy_score\": 0-100,\n"
        "  \"follow_up_needed\": true or false,\n"
        "  \"coaching_detected\": true or false,\n"
        "  \"evaluator_notes\": \"2-3 sentence professional assessment\"\n"
        "}\n"
    )

    raw = _try_interview_llm_call(
        [{"role": "user", "content": prompt}],
        system=_EVALUATOR_SYSTEM
        + "\n- coaching_detected: Detect if the transcript shows someone else giving the candidate the answer."
        + " Set to true if coaching is detected.",
        temperature=0.3,
        max_tokens=600,
    )
    if raw is None:
        return _fallback_answer_evaluation(
            question_text=question_text,
            question_type=question_type,
            candidate_transcript=candidate_transcript,
            frame_analysis=frame_analysis,
        )

    try:
        data = _parse_json(raw)
    except Exception:
        return _fallback_answer_evaluation(
            question_text=question_text,
            question_type=question_type,
            candidate_transcript=candidate_transcript,
            frame_analysis=frame_analysis,
        )
    raw_is_correct = data.get("is_correct", False)
    if isinstance(raw_is_correct, str):
        is_correct = raw_is_correct.strip().lower() in ("true", "1", "yes", "correct")
    else:
        is_correct = bool(raw_is_correct)

    from app.interview.domain.interview_models import QuestionType
    qt = question_type
    if not isinstance(qt, QuestionType):
        try:
            qt = QuestionType(str(qt).lower().strip())
        except ValueError:
            norm_qt = str(qt or "").lower().strip()
            if "tech" in norm_qt or "core" in norm_qt:
                qt = QuestionType.TECHNICAL
            elif "deep" in norm_qt or "dive" in norm_qt or "cv" in norm_qt:
                qt = QuestionType.DEEP_DIVE
            elif "ice" in norm_qt or "intro" in norm_qt:
                qt = QuestionType.ICEBREAKER
            elif "code" in norm_qt:
                qt = QuestionType.CODING
            elif "behav" in norm_qt:
                qt = QuestionType.BEHAVIORAL
            elif "close" in norm_qt or "closing" in norm_qt:
                qt = QuestionType.CLOSING
            else:
                qt = QuestionType.TECHNICAL

    return AnswerEvaluation(
        question_index=0,
        question_text=question_text,
        question_type=qt,
        candidate_transcript=candidate_transcript,
        relevance_score=float(data.get("relevance_score", 5)),
        depth_score=float(data.get("depth_score", 5)),
        communication_score=float(data.get("communication_score", 5)),
        key_points_covered=data.get("key_points_covered", []),
        missed_points=data.get("missed_points", []),
        is_correct=is_correct,
        accuracy_score=float(data.get("accuracy_score", 0.0)),
        follow_up_triggered=bool(data.get("follow_up_needed", False)),
        coaching_detected=bool(data.get("coaching_detected", False)),
        frame_analysis=frame_analysis,
        evaluator_notes=data.get("evaluator_notes", ""),
    )


async def generate_report_summary(
    candidate_name: str,
    job_role: str,
    evaluations: list,
    overall_score: float,
    video_integrity_score: float,
) -> dict:
    eval_lines = "\n".join(
        [
            f"Q{e.question_index + 1} ({e.question_type}): "
            f"R={e.relevance_score} D={e.depth_score} C={e.communication_score} | {e.evaluator_notes}"
            for e in evaluations
        ]
    )

    prompt = (
        "Generate a final interview report for:\n\n"
        f"CANDIDATE: {candidate_name}\n\n"
        f"ROLE: {job_role}\n\n"
        f"OVERALL SCORE: {overall_score:.1f}/100\n\n"
        f"VIDEO INTEGRITY: {video_integrity_score:.1f}/100\n\n"
        "PER-QUESTION EVALUATIONS:\n\n"
        f"{eval_lines}\n\n"
        "Return ONLY this JSON:\n"
        "{\n"
        "  \"behavioral_summary\": \"2-3 sentence summary of behavioral traits\",\n"
        "  \"strengths\": [\"strength1\", \"strength2\", \"strength3\"],\n"
        "  \"weaknesses\": [\"weakness1\", \"weakness2\"],\n"
        "  \"recommendation\": \"Strongly Recommend|Recommend|Borderline|Not Recommend\",\n"
        "  \"red_flags\": [],\n"
        "  \"hiring_decision_notes\": \"2-3 sentences for the HR manager\"\n"
        "}\n"
    )

    raw = _try_interview_llm_call(
        [{"role": "user", "content": prompt}],
        system="You are an expert HR analyst. Be objective and professional. Return only valid JSON.",
        temperature=0.4,
        max_tokens=800,
    )
    if raw is None:
        return {
            "behavioral_summary": (
                "Summary unavailable: Groq daily token quota exceeded. "
                "Use per-question evaluations and scores below."
            ),
            "strengths": ["See session evaluations"],
            "weaknesses": ["Manual review recommended when AI summary is unavailable"],
            "recommendation": "Borderline",
            "red_flags": [],
            "hiring_decision_notes": (
                "Automated narrative skipped due to LLM provider limits; rely on structured scores and transcripts."
            ),
        }
    try:
        return _parse_json(raw)
    except Exception:
        return {
            "behavioral_summary": "Report JSON could not be parsed.",
            "strengths": [],
            "weaknesses": [],
            "recommendation": "Borderline",
            "red_flags": [],
            "hiring_decision_notes": "Review evaluations manually.",
        }


# ============================================================================
# FEAT-002-BE: Rubric-Backed Question Generation Engine
# ============================================================================

def _normalize_role_and_seniority(
    job_role: StandardRole | str,
    seniority: SeniorityLevel | str = SeniorityLevel.MID,
) -> tuple[StandardRole, SeniorityLevel]:
    """Normalize input role and seniority into canonical domain enums."""
    # Match role
    role_out = StandardRole.BACKEND_ENGINEER
    if isinstance(job_role, StandardRole):
        role_out = job_role
    elif isinstance(job_role, str):
        normalized = job_role.strip().lower().replace(" ", "_").replace("-", "_")
        for r in StandardRole:
            if r.value == normalized or r.value in normalized or normalized in r.value:
                role_out = r
                break
        else:
            if "front" in normalized:
                role_out = StandardRole.FRONTEND_ENGINEER
            elif "full" in normalized:
                role_out = StandardRole.FULLSTACK_ENGINEER
            elif "devops" in normalized or "sre" in normalized or "cloud" in normalized:
                role_out = StandardRole.DEVOPS_ENGINEER
            elif "data" in normalized or "etl" in normalized or "analytics" in normalized:
                role_out = StandardRole.DATA_ENGINEER
            elif "ml" in normalized or "machine" in normalized or "ai" in normalized or "learning" in normalized:
                role_out = StandardRole.ML_ENGINEER
            elif "qa" in normalized or "test" in normalized or "quality" in normalized:
                role_out = StandardRole.QA_AUTOMATION_ENGINEER
            else:
                role_out = StandardRole.BACKEND_ENGINEER

    # Match seniority
    sen_out = SeniorityLevel.MID
    if isinstance(seniority, SeniorityLevel):
        sen_out = seniority
    elif isinstance(seniority, str):
        sen_norm = seniority.strip().lower()
        if "lead" in sen_norm or "principal" in sen_norm or "staff" in sen_norm:
            sen_out = SeniorityLevel.LEAD
        elif "senior" in sen_norm or "sr" in sen_norm:
            sen_out = SeniorityLevel.SENIOR
        elif "entry" in sen_norm or "junior" in sen_norm or "intern" in sen_norm or "assoc" in sen_norm:
            sen_out = SeniorityLevel.ENTRY
        else:
            sen_out = SeniorityLevel.MID

    return role_out, sen_out


_OFFLINE_RUBRIC_QUESTION_BANK: Dict[StandardRole, List[Dict[str, Any]]] = {
    StandardRole.FRONTEND_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Core Web Technologies & Frameworks",
            "question_text": "Please introduce your background in web development: what UI frameworks (React, Next.js, Vue) you specialize in, and what core architectural principles guide your frontend work?",
            "rubric": QuestionRubric(
                reference_answer="Candidate provides clear overview of frontend experience, discusses React/Vue/Next.js frameworks, component architectures, modularity, and user-centric engineering.",
                key_concepts_expected=["Component-Based Architecture", "State Management", "Modern JavaScript (ES6+)", "Responsive Design"],
                depth_criteria={
                    "basic": "Mentions basic HTML/CSS/JS syntax without framework depth.",
                    "intermediate": "Explains component lifecycles, hooks, and responsive layouts.",
                    "advanced": "Articulates performance implications, state synchronization, and scalable architecture.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Modern UI Frameworks (React/Vue/Next.js)",
            "question_text": "How does React's Virtual DOM diffing algorithm and reconciliation process work, and how does key prop usage prevent unnecessary re-renders?",
            "rubric": QuestionRubric(
                reference_answer="React maintains a virtual representation of the DOM. During state changes, it generates a new virtual tree, runs a heuristic O(N) diffing algorithm comparing element types and keys, and batches minimal mutation patches to the real DOM via Fiber reconciliation.",
                key_concepts_expected=["Virtual DOM", "Reconciliation Heuristics", "Key Prop Identity", "Fiber Architecture", "DOM Batching"],
                depth_criteria={
                    "basic": "States that virtual DOM is faster than real DOM without explaining diffing.",
                    "intermediate": "Explains tree comparison, element type checks, and why keys are necessary for lists.",
                    "advanced": "Explains Fiber work loop, time slicing, batching, and DOM mutation minimizing.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Web Performance & Core Vitals",
            "question_text": "What are Core Web Vitals (LCP, INP/FID, CLS), how do bundle size and render-blocking scripts impact them, and what optimization techniques do you apply?",
            "rubric": QuestionRubric(
                reference_answer="LCP measures largest contentful paint (loading), INP/FID measures interaction responsiveness, and CLS measures visual stability. Mitigations include code splitting via dynamic imports, critical CSS inlining, asset compression/CDN caching, image optimization (Next.js Image), and SSR/SSG.",
                key_concepts_expected=["Core Web Vitals (LCP/INP/CLS)", "Code Splitting & Lazy Loading", "SSR vs SSG vs Client Rendering", "Resource Prioritization & CDN Caching"],
                depth_criteria={
                    "basic": "Mentions image compression and minification.",
                    "intermediate": "Explains specific Core Web Vital thresholds and code-splitting with React.lazy/dynamic imports.",
                    "advanced": "Deep dives into critical rendering path, hydration bottlenecks, layout thrashing, and server components.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Client-Side Architecture & State",
            "question_text": "In your frontend work{project_clause}, how did you design client-side state management, handle caching/invalidation, and maintain consistent UI state under network latency?",
            "rubric": QuestionRubric(
                reference_answer="Candidate describes structured state architecture (Zustand/Redux/React Query), optimistic UI updates, normalized cache schemas, mutation invalidations, and error boundary fallbacks.",
                key_concepts_expected=["Global vs Server State", "Optimistic Updates", "Cache Invalidation (SWR/React Query)", "Error Boundaries & Fallbacks"],
                depth_criteria={
                    "basic": "Relies strictly on local useState or prop drilling.",
                    "intermediate": "Uses structured global store or data-fetching hooks with standard cache policies.",
                    "advanced": "Implements optimistic mutations, offline rollback, normalized caching, and performance memoization.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Algorithm Design & Sliding Window",
            "question_text": "Implement a function `length_of_longest_substring(s: str) -> int` that returns the length of the longest substring without repeating characters.",
            "rubric": QuestionRubric(
                reference_answer="Use sliding window approach with two pointers and a hash map/set to track character occurrences and indices in O(N) time and O(min(N, M)) space.",
                key_concepts_expected=["Sliding Window Technique", "Hash Map / Set Index Tracking", "O(N) Time Complexity", "Edge Case Handling (empty string, all identical characters)"],
                depth_criteria={
                    "basic": "O(N^2) brute force nested loops.",
                    "intermediate": "O(N) sliding window with set/map tracking.",
                    "advanced": "Optimized single-pass window jump with direct index mapping and zero allocation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Longest Substring Without Repeating Characters",
                "problem_statement": "Given a string s, find the length of the longest substring without repeating characters.",
                "starter_code": "def length_of_longest_substring(s: str) -> int:\n    # TODO: Implement sliding window\n    pass\n",
                "test_cases": [
                    {"input": "abcabcbb", "expected_output": "3", "is_hidden": False},
                    {"input": "bbbbb", "expected_output": "1", "is_hidden": False},
                    {"input": "pwwkew", "expected_output": "3", "is_hidden": True},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Testing & Web Security",
            "question_text": "How do you protect frontend applications from XSS and CSRF attacks, enforce Content Security Policies (CSP), and structure automated frontend testing?",
            "rubric": QuestionRubric(
                reference_answer="XSS prevention includes contextual output encoding, avoiding dangerouslySetInnerHTML, sanitizing user inputs, and strict CSP headers. CSRF protection utilizes SameSite cookie attributes and anti-CSRF tokens. Testing integrates Jest/RTL unit tests and Playwright E2E suites.",
                key_concepts_expected=["XSS Mitigation & Sanitization", "Content Security Policy (CSP)", "SameSite Cookies & CSRF", "Component & E2E Testing (Playwright/Jest)"],
                depth_criteria={
                    "basic": "Mentions avoiding dangerous HTML and running simple unit tests.",
                    "intermediate": "Explains CSP directives, HTTP-only cookies, and React Testing Library user-event simulations.",
                    "advanced": "Covers DOM-based XSS vectors, nonce-based CSP, iframe sandboxing, and automated visual regression.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.BACKEND_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Backend Systems & Architecture",
            "question_text": "Please introduce your backend engineering background: preferred languages/frameworks (FastAPI, Django, Node, Go), database technologies, and your approach to building reliable server architectures.",
            "rubric": QuestionRubric(
                reference_answer="Candidate summarizes server-side experience, API frameworks (FastAPI/Node/Go/Django), database designs, and architectural principles (modularity, reliability, testability).",
                key_concepts_expected=["RESTful API Conventions", "Relational & NoSQL Databases", "Async I/O & Microservices", "System Reliability"],
                depth_criteria={
                    "basic": "Mentions basic CRUD endpoints and standard database connections.",
                    "intermediate": "Describes clean layering (routes, services, repositories) and async request lifecycles.",
                    "advanced": "Articulates architectural trade-offs, scalability patterns, and operational telemetry.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Database Architecture & Query Optimization",
            "question_text": "Explain database indexing internals (B-Trees vs Hash indexes), composite index column ordering rules, and how you diagnose slow queries using execution plans (EXPLAIN ANALYZE).",
            "rubric": QuestionRubric(
                reference_answer="B-Trees store sorted data for range and equality queries with O(log N) operations. Composite indexes follow leftmost prefix matching. EXPLAIN ANALYZE reveals sequential scans, index scans, cost estimates, and buffer hits, allowing targeted index creation.",
                key_concepts_expected=["B-Tree Index Structure", "Leftmost Prefix Rule", "Sequential Scan vs Index Scan", "EXPLAIN ANALYZE Query Plans", "Index Selectivity"],
                depth_criteria={
                    "basic": "States that indexes make SELECT queries faster but slow down writes.",
                    "intermediate": "Explains B-Tree traversal, composite index ordering, and how to read basic execution plans.",
                    "advanced": "Analyzes index selectivity, covering indexes (INDEX INCLUDE), vacuum/page fragmentation, and locking overhead.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Concurrency, Async & Performance",
            "question_text": "Compare asynchronous non-blocking event loops (like Python Asyncio or Node.js) with multithreading / multiprocessing. How do you prevent event loop starvation and manage shared resources?",
            "rubric": QuestionRubric(
                reference_answer="Async event loops use cooperative multitasking over a single thread to handle high I/O concurrency via non-blocking sockets. CPU-bound tasks block the loop and must be delegated to process/thread worker pools. Shared state synchronization requires mutexes, locks, or atomic operations.",
                key_concepts_expected=["Event Loop & Non-Blocking I/O", "CPU-Bound vs I/O-Bound Workloads", "Thread/Process Worker Pools", "Race Conditions & Mutexes", "Connection Pooling"],
                depth_criteria={
                    "basic": "Distinguishes async from sync by saying async doesn't wait for requests.",
                    "intermediate": "Explains event loop polling (epoll/kqueue), await suspension points, and offloading heavy tasks.",
                    "advanced": "Details GIL implications in Python, thread pool sizing, coroutine starvation detection, and backpressure mechanisms.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Distributed Systems & Messaging",
            "question_text": "In your system architecture work{project_clause}, how do you ensure message ordering, idempotency, and fault tolerance when building event-driven services with message brokers like Kafka or RabbitMQ?",
            "rubric": QuestionRubric(
                reference_answer="Partition keys ensure per-entity ordering in Kafka. Idempotency is enforced using unique idempotency keys stored in database transactions (Transactional Outbox Pattern). Dead-letter queues and exponential backoff retries manage fault tolerance.",
                key_concepts_expected=["Message Broker Partitioning / Topics", "Idempotency Keys & Deduplication", "Transactional Outbox Pattern", "Dead Letter Queues (DLQ) & Retries", "Eventual Consistency"],
                depth_criteria={
                    "basic": "Mentions publishing messages to a queue and consuming them.",
                    "intermediate": "Explains partition keys, consumer group offset commits, and at-least-once delivery handling.",
                    "advanced": "Designs end-to-end transactional outbox pattern, dual-write mitigation, exactly-once processing guarantees, and poison-pill recovery.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Data Structures & LRU Cache",
            "question_text": "Design and implement a Least Recently Used (LRU) Cache supporting get(key) and put(key, value) operations in O(1) time complexity.",
            "rubric": QuestionRubric(
                reference_answer="Combine a hash map for O(1) key lookups with a doubly linked list to track node access order, moving accessed items to the head and evicting the tail on capacity overflow.",
                key_concepts_expected=["Hash Map + Doubly Linked List", "O(1) Time Complexity for Get and Put", "Capacity Eviction Policy (Tail Node)", "Node Pointer Manipulation (Head/Tail Sentinel Nodes)"],
                depth_criteria={
                    "basic": "Uses an array or list with O(N) search and shift operations.",
                    "intermediate": "Implements hash map + doubly linked list with correct pointer updates and eviction.",
                    "advanced": "Utilizes sentinel dummy nodes for clean boundary conditions, thread-safe locks, and unit tests.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "LRU Cache Implementation",
                "problem_statement": "Design a data structure that follows the constraints of a Least Recently Used (LRU) cache with O(1) get and put operations.",
                "starter_code": "class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n    def get(self, key: int) -> int:\n        pass\n    def put(self, key: int, value: int) -> None:\n        pass\n",
                "test_cases": [
                    {"input": "capacity=2, put(1,1), put(2,2), get(1)", "expected_output": "1", "is_hidden": False},
                    {"input": "put(3,3), get(2)", "expected_output": "-1", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Backend Security & Reliability",
            "question_text": "How do you build backend resilience against cascading outages using circuit breakers, rate limiting, and structured logging/telemetry?",
            "rubric": QuestionRubric(
                reference_answer="Circuit breakers (closed/open/half-open states) trip upon consecutive downstream failures to prevent thread exhaustion. Token bucket rate limiters prevent API abuse. Structured JSON logging with correlation IDs enables distributed request tracing.",
                key_concepts_expected=["Circuit Breaker Pattern (Open/Closed/Half-Open)", "Rate Limiting (Token Bucket / Leaky Bucket)", "Correlation IDs & Distributed Tracing", "Graceful Degradation & Fallbacks"],
                depth_criteria={
                    "basic": "Mentions try-catch blocks and basic logging.",
                    "intermediate": "Explains circuit breaker state transitions, rate limiter HTTP 429 responses, and centralized logs.",
                    "advanced": "Designs adaptive rate limiters, fallback cache degradation, OpenTelemetry span propagation, and health check probes.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.FULLSTACK_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Fullstack Architecture",
            "question_text": "Please introduce your fullstack background: how you bridge frontend user interfaces with backend API services, and your experience across the entire delivery lifecycle.",
            "rubric": QuestionRubric(
                reference_answer="Candidate outlines experience with React/Next.js on frontend, FastAPI/Node on backend, database modeling, and deployment practices.",
                key_concepts_expected=["End-to-End Development", "API Client & Server Contracts", "Database Modeling", "Containerized Deployment"],
                depth_criteria={
                    "basic": "Mentions basic UI and endpoint creation.",
                    "intermediate": "Explains full stack data flows, state synchronization, and schema validations.",
                    "advanced": "Articulates full architectural trade-offs, SSR vs CSR, caching layers, and CI/CD pipelines.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Backend Systems & REST/GraphQL APIs",
            "question_text": "How do you design and secure RESTful / GraphQL API contracts between frontend and backend, including JWT authentication, refresh tokens, and CORS configuration?",
            "rubric": QuestionRubric(
                reference_answer="APIs use consistent REST schemas or GraphQL types. Authentication uses short-lived access JWTs and HTTP-only Secure SameSite refresh tokens. CORS headers restrict origin, methods, and credentials.",
                key_concepts_expected=["JWT Access & Refresh Token Lifecycle", "HTTP-Only Secure Cookies", "CORS Configuration (Allowed Origins)", "Input Validation & Pydantic/Zod Schemas"],
                depth_criteria={
                    "basic": "Mentions storing JWT in localStorage without security analysis.",
                    "intermediate": "Explains token refresh rotation, HTTP-only cookie security, and CORS headers.",
                    "advanced": "Designs silent authentication refresh, CSRF protection alongside JWT, and automated OpenAPI contract sync.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Database Design & ORM/ODM Integration",
            "question_text": "Explain how ORMs/ODMs (like SQLAlchemy, Prisma, or Beanie) map object models to databases, how the N+1 query problem happens, and how you resolve it.",
            "rubric": QuestionRubric(
                reference_answer="ORMs translate domain objects to SQL/NoSQL queries. The N+1 problem occurs when fetching a parent record triggers N individual queries for child associations. Resolution uses joined load (eager loading), selectinload, or database aggregation pipelines.",
                key_concepts_expected=["ORM/ODM Mapping", "N+1 Query Problem", "Eager vs Lazy Loading", "Join Optimization & Aggregation Pipelines", "Database Indexing"],
                depth_criteria={
                    "basic": "Defines what an ORM does.",
                    "intermediate": "Explains why N+1 queries degrade performance and demonstrates eager loading solutions.",
                    "advanced": "Analyzes memory vs network trade-offs of large joins, batch querying strategies, and raw query fallbacks.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "DevOps, CI/CD & Deployment",
            "question_text": "In your fullstack work{project_clause}, how do you structure Docker multi-stage builds, manage environment secrets across environments, and set up automated CI/CD deployment pipelines?",
            "rubric": QuestionRubric(
                reference_answer="Multi-stage Docker builds separate build toolchains from minimal runtime images to minimize surface area and size. CI/CD runs automated linting, unit/E2E tests, and deploys container images with securely injected runtime secrets.",
                key_concepts_expected=["Docker Multi-Stage Builds", "CI/CD Pipeline Stages", "Environment Secret Management", "Zero-Downtime Deployment"],
                depth_criteria={
                    "basic": "Writes basic single-stage Dockerfile and pushes code.",
                    "intermediate": "Structures multi-stage Docker builds, separates dev/prod configs, and automates test pipelines.",
                    "advanced": "Implements immutable container tagging, vulnerability scanning in CI, non-root container users, and rollback automation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Data Aggregation & Algorithm Design",
            "question_text": "Write a function `aggregate_user_sessions(events: List[dict]) -> Dict[str, dict]` that groups logs by user_id and computes total duration and most frequent action.",
            "rubric": QuestionRubric(
                reference_answer="Iterate through logs in O(N) time, populating a dictionary indexed by user_id. Track session timestamps and action frequencies using hash counters.",
                key_concepts_expected=["Hash Map Grouping", "Time Complexity O(N)", "Frequency Counting", "Edge Case Handling (empty logs, malformed records)"],
                depth_criteria={
                    "basic": "Uses nested loops with poor efficiency.",
                    "intermediate": "O(N) dictionary aggregation with clean data output.",
                    "advanced": "Handles out-of-order timestamps, edge cases, and memory-efficient streaming generators.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Log Aggregation & User Session Metrics",
                "problem_statement": "Given a list of event dictionaries with keys 'user_id', 'timestamp', and 'action', aggregate total session time and top action per user.",
                "starter_code": "def aggregate_user_sessions(events: list) -> dict:\n    # TODO: Implement aggregation logic\n    pass\n",
                "test_cases": [
                    {"input": "[{'user_id': 'u1', 'timestamp': 100, 'action': 'click'}, {'user_id': 'u1', 'timestamp': 150, 'action': 'click'}]", "expected_output": "{'u1': {'total_duration': 50, 'top_action': 'click'}}", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Fullstack Security & Testing",
            "question_text": "What OWASP Top 10 vulnerabilities are most critical in fullstack web applications, and how do you enforce automated security scans and integration tests?",
            "rubric": QuestionRubric(
                reference_answer="Critical vulnerabilities include SQL/NoSQL injection, broken access control, XSS, and CSRF. Enforce input sanitization, role-based authorization middleware, secure headers, and automated security scanning (SAST/DAST) in CI.",
                key_concepts_expected=["OWASP Top 10 Vulnerabilities", "Broken Access Control / RBAC", "SQL/NoSQL Injection Mitigation", "Automated Security Scanners (SAST/DAST)", "Integration Test Suites"],
                depth_criteria={
                    "basic": "Lists common vulnerabilities without prevention details.",
                    "intermediate": "Explains RBAC checks, parameterized queries, and unit/integration testing strategies.",
                    "advanced": "Designs defense-in-depth architecture, JWT replay protection, automated dependency vulnerability alerts, and regression test suites.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.DEVOPS_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Infrastructure as Code & Cloud Platforms",
            "question_text": "Could you introduce your DevOps and Site Reliability Engineering background, your experience with Infrastructure as Code (Terraform/CloudFormation), and your philosophy on automation?",
            "rubric": QuestionRubric(
                reference_answer="Candidate summarizes cloud infrastructure experience (AWS/GCP/Azure), Terraform IaC, Kubernetes container orchestration, and CI/CD automation.",
                key_concepts_expected=["Infrastructure as Code (Terraform)", "Cloud Architecture & Networking (VPC/Subnets)", "Container Orchestration", "CI/CD Pipeline Automation"],
                depth_criteria={
                    "basic": "Mentions configuring cloud resources via GUI console.",
                    "intermediate": "Explains modular Terraform code, state locking with S3/DynamoDB, and automated deployment.",
                    "advanced": "Articulates multi-region redundancy, least-privilege IAM policies, and immutable infrastructure patterns.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Containerization & Orchestration",
            "question_text": "Explain Kubernetes architecture: what are the roles of the Control Plane (API Server, etcd, Scheduler, Controller Manager) vs Worker Nodes (Kubelet, Kube-proxy), and how does a Deployment roll out updates?",
            "rubric": QuestionRubric(
                reference_answer="API Server validates manifests and stores cluster state in etcd. Scheduler assigns Pods to nodes; Controller Manager reconciles desired state. Kubelet executes containers via CRI, and Kube-proxy manages network routing. Deployments manage ReplicaSets for rolling updates with readiness probes.",
                key_concepts_expected=["Kubernetes Control Plane (API Server, etcd, Scheduler)", "Worker Node Components (Kubelet, Kube-proxy)", "ReplicaSets & Rolling Update Strategy", "Liveness & Readiness Probes"],
                depth_criteria={
                    "basic": "Defines what a Pod and Container are.",
                    "intermediate": "Explains Control plane component responsibilities, rolling update parameters (maxSurge, maxUnavailable), and health probes.",
                    "advanced": "Analyzes etcd consensus/raft, CNI networking plugins, ingress controller routing, and custom resource definitions (CRDs).",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "CI/CD Automation & Release Engineering",
            "question_text": "Compare Blue-Green, Canary, and Rolling deployment strategies. How do you automate canary analysis and execute automated rollbacks based on error budget or metric thresholds?",
            "rubric": QuestionRubric(
                reference_answer="Blue-Green switches 100% traffic between identical environments. Canary routes a small traffic percentage (e.g. 5%) to new versions while monitoring Prometheus metrics (HTTP 5xx error rate, latency). If thresholds exceed error budgets, deployment automatically rolls back.",
                key_concepts_expected=["Blue-Green vs Canary vs Rolling Deployments", "Traffic Shifting & Ingress Routing", "Automated Canary Analysis (Argo Rollouts / Flagger)", "Prometheus Metric Gates & Auto-Rollback"],
                depth_criteria={
                    "basic": "Defines blue-green and canary at a high level.",
                    "intermediate": "Explains traffic shifting mechanisms and health check monitoring during release.",
                    "advanced": "Designs progressive delivery with Argo Rollouts, webhook integrations, error budget depletion tracking, and automated rollback.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Observability, Monitoring & Alerting",
            "question_text": "In your observability work{project_clause}, how do you implement the Three Pillars of Observability (Metrics, Logs, Traces) using Prometheus, Loki/ELK, and OpenTelemetry, and how do you calculate SLOs and Error Budgets?",
            "rubric": QuestionRubric(
                reference_answer="Prometheus scrapes numeric metrics; Loki/ELK aggregates indexed structured logs; OpenTelemetry traces requests across microservices. SLOs define target reliability (e.g. 99.9% success rate), and the Error Budget (0.1%) governs release velocity and alerting urgency.",
                key_concepts_expected=["Metrics, Structured Logs & Distributed Traces", "Prometheus Scraping & PromQL", "Distributed Tracing Spans (OpenTelemetry)", "SLI, SLO & Error Budget Formulas"],
                depth_criteria={
                    "basic": "Mentions setting up simple CPU/Memory alerts.",
                    "intermediate": "Explains PromQL queries, trace context propagation, and standard log aggregation.",
                    "advanced": "Calculates multi-window burn rate alerts for error budgets, distributed tracing sampling strategies, and high-cardinality metric management.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Log Parsing & Top-K Algorithm",
            "question_text": "Write a function `top_error_ips(log_lines: List[str], k: int) -> List[tuple]` that parses HTTP server access logs and returns the top K IP addresses generating HTTP 5xx errors.",
            "rubric": QuestionRubric(
                reference_answer="Parse log lines using regular expressions or structured splits, filter for 5xx status codes, accumulate IP frequencies in a hash map, and extract top K using a heap or sorted order.",
                key_concepts_expected=["Log Line Parsing / Regex", "HTTP 5xx Status Code Filtering", "Hash Map Frequency Counting", "Top-K Extraction (Heap / Sorting)", "Time & Space Complexity"],
                depth_criteria={
                    "basic": "Reads file and performs simple split without error handling.",
                    "intermediate": "Parses accurately, counts occurrences in dictionary, and outputs top K correctly.",
                    "advanced": "Uses min-heap for O(N log K) time efficiency, handles corrupt log lines gracefully, and optimizes for streaming memory.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Top Offending Error IPs",
                "problem_statement": "Given a list of access log lines in Common Log Format, return the top k IP addresses with HTTP status >= 500 sorted by error count descending.",
                "starter_code": "def top_error_ips(log_lines: list, k: int) -> list:\n    # TODO: Implement log parser and top-k counter\n    pass\n",
                "test_cases": [
                    {"input": "['192.168.1.1 - - [01/Jan/2026] \"GET /api\" 500 120', '192.168.1.2 - - [01/Jan/2026] \"GET /api\" 200 120', '192.168.1.1 - - [01/Jan/2026] \"POST /api\" 503 120'], k=1", "expected_output": "[('192.168.1.1', 2)]", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "DevSecOps & Site Reliability (SRE)",
            "question_text": "How do you implement secrets management (HashiCorp Vault / AWS KMS), container image vulnerability scanning, and disaster recovery / backup automation in production?",
            "rubric": QuestionRubric(
                reference_answer="Secrets are encrypted at rest and in transit via Vault/KMS with dynamic short-lived credentials. CI pipelines scan container images (Trivy/Grype) for CVEs. Automated snapshots and cross-region replication ensure RPO and RTO disaster recovery targets.",
                key_concepts_expected=["Secrets Management (Vault / KMS)", "Dynamic Short-Lived Secrets", "Container CVE Scanning (Trivy/Grype)", "RPO / RTO & Disaster Recovery Replication"],
                depth_criteria={
                    "basic": "Mentions using .env files and manual backups.",
                    "intermediate": "Explains Vault integration, least-privilege IAM, and scheduled automated backup cron jobs.",
                    "advanced": "Implements mutual TLS (mTLS), automated certificate rotation, immutable audit logging, and chaos engineering disaster simulations.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.DATA_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Data Pipeline Engineering (ETL/ELT)",
            "question_text": "Please introduce your data engineering background, the scale of data pipelines you've built, and your experience with batch vs streaming data architectures.",
            "rubric": QuestionRubric(
                reference_answer="Candidate summarizes ETL/ELT pipelines, distributed processing engines (Spark/Flink), messaging systems (Kafka), and cloud data warehouses.",
                key_concepts_expected=["Batch vs Streaming Architectures", "ETL/ELT Pipelines", "Distributed Data Engines (Spark/Kafka)", "Data Warehousing"],
                depth_criteria={
                    "basic": "Mentions writing simple SQL queries and CSV exports.",
                    "intermediate": "Explains pipeline orchestration (Airflow) and schema management.",
                    "advanced": "Articulates trade-offs between Lambda and Kappa architectures, data lakehouses, and scaling bottlenecks.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Big Data & Distributed Computing",
            "question_text": "Explain Apache Spark internals: what is the difference between transformations (narrow vs wide dependencies) and actions, and how do you optimize data shuffles and avoid skewed partitions?",
            "rubric": QuestionRubric(
                reference_answer="Transformations define a lazy DAG; narrow dependencies (map/filter) execute within partitions without shuffling, while wide dependencies (groupBy/join) trigger network shuffles. Mitigate skew via salting keys, broadcast joins for small tables, and adaptive query execution (AQE).",
                key_concepts_expected=["Spark Lazy DAG & RDDs/DataFrames", "Narrow vs Wide Dependencies", "Shuffle Spill & Network Overhead", "Broadcast Joins & Salting Keys for Data Skew", "Adaptive Query Execution (AQE)"],
                depth_criteria={
                    "basic": "Mentions running PySpark queries without understanding executors.",
                    "intermediate": "Explains transformations vs actions and why wide dependencies trigger expensive shuffles.",
                    "advanced": "Diagnoses skew in Spark UI, tunes shuffle partition counts, applies broadcast hash joins, and manages off-heap memory.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Data Warehousing & Modeling",
            "question_text": "How do you design dimensional models in cloud data warehouses (Snowflake, BigQuery, Databricks)? Compare Star vs Snowflake schemas, and explain how columnar storage (Parquet/ORC) improves analytical query speeds.",
            "rubric": QuestionRubric(
                reference_answer="Star schemas use denormalized dimension tables around a central fact table for fast joins; Snowflake schemas normalize dimensions to reduce redundancy. Columnar storage reads only requested columns and utilizes dictionary encoding and run-length compression for high scan throughput.",
                key_concepts_expected=["Star vs Snowflake Schema", "Fact vs Dimension Tables (SCD Type 1/2)", "Columnar Storage (Parquet / ORC)", "Partitioning, Clustering & File Pruning"],
                depth_criteria={
                    "basic": "Defines relational tables without dimensional concepts.",
                    "intermediate": "Explains fact/dimension relationships and how columnar file formats reduce I/O.",
                    "advanced": "Designs Slowly Changing Dimensions (SCD Type 2), cluster keys for micro-partition pruning, and lakehouse Delta Lake ACID transactions.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Stream Processing & Messaging",
            "question_text": "In your stream processing work{project_clause}, how do you handle event-time vs processing-time, manage late-arriving data with watermarks in Kafka/Flink, and guarantee exactly-once processing?",
            "rubric": QuestionRubric(
                reference_answer="Event-time reflects when an event occurred; processing-time is when the engine receives it. Watermarks track event-time progress to trigger window computations and handle bounded late data with side outputs. Two-phase commit protocol ensures end-to-end exactly-once semantics.",
                key_concepts_expected=["Event-Time vs Processing-Time", "Watermarking & Late Data Handling", "Sliding/Tumbling Window Computations", "Exactly-Once Semantics (2PC / Idempotency)"],
                depth_criteria={
                    "basic": "Treats all data as incoming timestamps without event-time concepts.",
                    "intermediate": "Explains window aggregation, watermark generation, and dead-letter queues for late data.",
                    "advanced": "Designs end-to-end transactional sinks, stateful checkpointing in Flink, and out-of-order event reconciliation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Streaming Sliding Window Algorithm",
            "question_text": "Write a function `detect_high_frequency_users(transactions: List[tuple], window_sec: int = 60, threshold: int = 3) -> List[str]` that detects users with more than `threshold` transactions within any `window_sec` interval.",
            "rubric": QuestionRubric(
                reference_answer="Sort transactions or maintain a deque of recent timestamps per user within the window, popping stale timestamps and checking queue length in O(N) amortized time.",
                key_concepts_expected=["Sliding Window / Queue Mechanism", "Per-User Deque of Timestamps", "Amortized O(N) Time Complexity", "Edge Cases (simultaneous timestamps, empty inputs)"],
                depth_criteria={
                    "basic": "O(N^2) pairwise comparisons of all transactions.",
                    "intermediate": "Uses deque or sliding window per user with accurate 60-second bounds.",
                    "advanced": "Optimizes memory footprint, handles unsorted streams, and supports streaming iterator generation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Sliding Window Transaction Rate Limiter / Detector",
                "problem_statement": "Given tuples of (user_id, timestamp_sec, amount), return unique user_ids with more than 3 transactions in any 60 second window.",
                "starter_code": "def detect_high_frequency_users(transactions: list, window_sec: int = 60, threshold: int = 3) -> list:\n    # TODO: Implement sliding window detector\n    pass\n",
                "test_cases": [
                    {"input": "[('u1', 10, 100), ('u1', 20, 50), ('u1', 40, 25), ('u1', 50, 10)]", "expected_output": "['u1']", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Data Governance & Quality",
            "question_text": "How do you enforce automated data quality testing (Great Expectations), data lineage tracking, and schema evolution (Avro/Protobuf) in enterprise data platforms?",
            "rubric": QuestionRubric(
                reference_answer="Data quality checks validate null constraints, value distributions, and uniqueness before table writes. Schema registries enforce backward/forward compatibility for Avro/Protobuf models. Data lineage tracking catalogs upstream/downstream impact.",
                key_concepts_expected=["Automated Data Quality Checks (Great Expectations)", "Schema Evolution (Backward/Forward Compatibility)", "Data Lineage & Metadata Catalogs", "Data Governance & Privacy (GDPR)"],
                depth_criteria={
                    "basic": "Manual spot-checking and basic SQL null checks.",
                    "intermediate": "Integrates automated quality assertions into Airflow DAGs and explains schema registry compatibility modes.",
                    "advanced": "Architects automated CI/CD schema validation, automated data quarantine for bad records, and column-level lineage governance.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.ML_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Machine Learning Fundamentals & Algorithms",
            "question_text": "Please introduce your Machine Learning and AI engineering background, the models you have trained or deployed to production, and your experience with MLOps workflows.",
            "rubric": QuestionRubric(
                reference_answer="Candidate summarizes ML experience (classical models, deep learning, PyTorch/TensorFlow, LLMs), model serving, and experiment tracking.",
                key_concepts_expected=["Model Training & Evaluation Lifecycle", "PyTorch / TensorFlow Frameworks", "MLOps & Model Serving", "Feature Engineering"],
                depth_criteria={
                    "basic": "Mentions running scikit-learn tutorial models.",
                    "intermediate": "Explains loss functions, overfitting prevention, and standard deployment with FastAPI.",
                    "advanced": "Articulates end-to-end model governance, distributed training architectures, and production inference optimization.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Deep Learning & Neural Architectures",
            "question_text": "Explain Transformer architecture internals: how does Multi-Head Self-Attention compute query, key, and value matrices, why is scaling by sqrt(d_k) necessary, and how do positional encodings work?",
            "rubric": QuestionRubric(
                reference_answer="Self-attention computes Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V. Scaling by sqrt(d_k) prevents dot-product values from growing large and vanishing softmax gradients. Positional encodings (sinusoidal or learned/RoPE) inject sequence order.",
                key_concepts_expected=["Query, Key, Value Matrices (Q, K, V)", "Scaled Dot-Product Formula", "Softmax Gradient Vanishing Mitigation", "Multi-Head Projection & Concatenation", "Positional Encodings (RoPE / Sinusoidal)"],
                depth_criteria={
                    "basic": "States that Transformers use attention to look at words.",
                    "intermediate": "Explains matrix operations (Q, K, V), softmax role, and multi-head benefits.",
                    "advanced": "Details computational complexity O(N^2), FlashAttention memory optimizations, and RoPE rotary embeddings.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "MLOps & Model Deployment Pipelines",
            "question_text": "How do you optimize deep learning model inference latency and throughput in production using techniques like ONNX Runtime, TensorRT, model quantization (INT8/FP8), and dynamic batching?",
            "rubric": QuestionRubric(
                reference_answer="ONNX Runtime and TensorRT perform graph optimizations, layer fusion, and kernel auto-tuning. Quantization converts FP32/FP16 weights to INT8/FP8 to reduce memory bandwidth and accelerate computation. Dynamic batching bundles concurrent inference requests.",
                key_concepts_expected=["Model Graph Optimization & Layer Fusion", "Quantization (Post-Training / QAT / INT8)", "Inference Servers (Triton / TorchServe / ONNX)", "Dynamic Batching & GPU Memory Bandwidth"],
                depth_criteria={
                    "basic": "Mentions loading model weights in a Python script.",
                    "intermediate": "Explains ONNX graph export, quantization precision trade-offs, and batching.",
                    "advanced": "Analyzes memory-bound vs compute-bound kernels, KV cache optimization in LLM serving (vLLM / PagedAttention), and latency profiling.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Large Language Models & Generative AI",
            "question_text": "In your Generative AI / LLM work{project_clause}, how do you architect a production Retrieval-Augmented Generation (RAG) system with hybrid search, vector embeddings, re-ranking, and hallucination guardrails?",
            "rubric": QuestionRubric(
                reference_answer="Chunk documents with semantic overlap, embed into vector databases (Qdrant/Milvus), and execute hybrid search (BM25 keyword + dense vector). Use cross-encoder re-ranking to select top context, inject into prompt with system constraints, and validate output with guardrails.",
                key_concepts_expected=["Semantic Chunking & Overlap", "Dense Embeddings vs Sparse BM25 (Hybrid Search)", "Cross-Encoder Re-ranking", "Vector Database Indexing (HNSW)", "Hallucination Mitigation & Output Guardrails"],
                depth_criteria={
                    "basic": "Uses naive text split and single vector search call.",
                    "intermediate": "Implements hybrid retrieval, re-ranking, and structured prompt template context injection.",
                    "advanced": "Designs self-corrective RAG (CRAG/GraphRAG), embedding fine-tuning, latency caching, and automated LLM-as-a-judge evaluation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Vector Operations & Numerical Stability",
            "question_text": "Write a function `cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float` that computes the cosine similarity between two vectors, with numerical zero-division guards.",
            "rubric": QuestionRubric(
                reference_answer="Compute dot product divided by the product of Euclidean norms: dot(u, v) / (norm(u) * norm(v)). Guard against zero division using epsilon and handle dimension mismatches.",
                key_concepts_expected=["Dot Product & Euclidean L2 Norm", "Cosine Similarity Mathematical Formula", "Zero Division Protection (Epsilon / Checks)", "Numerical Stability & Vector Dimension Validation"],
                depth_criteria={
                    "basic": "Simple formula without zero-magnitude checking.",
                    "intermediate": "Accurate math calculation with zero-vector handling.",
                    "advanced": "Vectorized numpy/list implementation with high precision stability and dimension assertion.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Cosine Similarity with Numerical Guardrails",
                "problem_statement": "Compute the cosine similarity between two float vectors u and v. Return 0.0 if either vector has zero magnitude.",
                "starter_code": "def cosine_similarity(vec_a: list, vec_b: list) -> float:\n    # TODO: Implement robust cosine similarity\n    pass\n",
                "test_cases": [
                    {"input": "vec_a=[1.0, 0.0], vec_b=[1.0, 0.0]", "expected_output": "1.0", "is_hidden": False},
                    {"input": "vec_a=[1.0, 0.0], vec_b=[0.0, 1.0]", "expected_output": "0.0", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Data Processing & Model Evaluation",
            "question_text": "How do you detect and monitor data drift and concept drift in production ML models, evaluate fairness/bias, and execute automated retraining pipelines?",
            "rubric": QuestionRubric(
                reference_answer="Data drift compares input feature distributions over time (using KS-test, PSI, or Wasserstein distance); concept drift detects degradation in target relationship. Set alerts on drift metrics and trigger automated retraining pipelines with validation gates.",
                key_concepts_expected=["Data Drift vs Concept Drift", "Statistical Drift Metrics (PSI / KS-Test / Wasserstein)", "Fairness & Demographic Bias Audits", "Automated Retraining Gates & Shadow Deployments"],
                depth_criteria={
                    "basic": "Mentions checking model accuracy periodically.",
                    "intermediate": "Explains Population Stability Index (PSI), distribution shift monitoring, and shadow testing.",
                    "advanced": "Architects continuous learning pipelines with rollback triggers, bias mitigation techniques, and automated feature store integration.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
    StandardRole.QA_AUTOMATION_ENGINEER: [
        {
            "stage": QuestionStage.ICEBREAKER,
            "competency_area": "Test Automation Frameworks & Strategy",
            "question_text": "Please introduce your Quality Engineering and Test Automation background, the test frameworks you specialize in (Playwright, Cypress, PyTest), and how you design scalable automated test suites.",
            "rubric": QuestionRubric(
                reference_answer="Candidate summarizes test automation experience (Playwright/Cypress/Selenium/PyTest), the testing pyramid (unit, integration, E2E), and CI/CD quality gate integration.",
                key_concepts_expected=["Testing Pyramid Architecture", "Page Object Model (POM)", "Modern Test Frameworks (Playwright/PyTest)", "CI/CD Quality Gates"],
                depth_criteria={
                    "basic": "Mentions manual testing and basic recorded scripts.",
                    "intermediate": "Explains Page Object Model design, test data management, and parallel test execution.",
                    "advanced": "Architects comprehensive enterprise test automation frameworks with dynamic reporting and automated regression gates.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "Modern E2E Testing Frameworks",
            "question_text": "How does Playwright/Cypress improve upon legacy Selenium architecture? How do you handle asynchronous waiting, dynamic DOM rendering, and flaky test elimination in modern SPAs?",
            "rubric": QuestionRubric(
                reference_answer="Playwright uses direct browser protocol (CDP) for fast execution, isolated browser contexts, and built-in auto-waiting for actionability (attached, visible, stable, enabled) without arbitrary sleep calls, eliminating timing flakiness.",
                key_concepts_expected=["Auto-Waiting & Actionability Checks", "Browser Context Isolation", "CDP Protocol vs WebDriver", "Flaky Test Root Cause Elimination (No Hardcoded Sleeps)", "Dynamic Locators (Role, Text, TestId)"],
                depth_criteria={
                    "basic": "Suggests using time.sleep() to wait for elements.",
                    "intermediate": "Explains explicit waits, auto-waiting locators, and isolated test contexts.",
                    "advanced": "Details network interception for mocking, trace viewer debugging, retry policies, and worker parallelism.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CORE_TECHNICAL,
            "competency_area": "API & Backend Testing",
            "question_text": "Explain how to design an API automated test framework (REST/GraphQL): how do you validate status codes, JSON schema compliance, response headers, and mock external dependencies using tools like Pact or WireMock?",
            "rubric": QuestionRubric(
                reference_answer="Framework structures test cases around API endpoints, validates HTTP status codes, deserializes responses against JSON Schemas (Pydantic/JSON Schema), asserts payload contracts, and mocks flaky third-party services via contract testing (Pact) or service virtualization.",
                key_concepts_expected=["API Status Code & Contract Verification", "JSON Schema Validation", "Consumer-Driven Contract Testing (Pact)", "Service Virtualization & Mocking", "Data-Driven Test Parameterization"],
                depth_criteria={
                    "basic": "Checks status code 200 using requests/Postman.",
                    "intermediate": "Validates JSON response schemas, headers, and parameterizes test fixtures.",
                    "advanced": "Implements consumer-driven contract testing, dynamic payload generators, and automated OpenAPI spec diff validation.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.DEEP_DIVE,
            "competency_area": "Performance, Load & Stress Testing",
            "question_text": "In your performance testing work{project_clause}, how do you design load and stress test scenarios with k6 or JMeter? How do you measure latency percentiles (p95, p99), throughput (RPS), and diagnose system bottlenecks?",
            "rubric": QuestionRubric(
                reference_answer="Define virtual user profiles, ramp-up schedules, and realistic think-times. Measure p95/p99 latency percentiles, request error rates, and RPS under load. Diagnose CPU/memory saturation, database lock contention, and connection pool exhaustion.",
                key_concepts_expected=["Load vs Stress vs Soak Testing", "Latency Percentiles (p95 / p99)", "Throughput (RPS) & Concurrency", "Bottleneck Isolation (DB Locks, Connection Pools, Memory Leaks)"],
                depth_criteria={
                    "basic": "Runs a basic script sending concurrent requests without metrics.",
                    "intermediate": "Explains latency distribution percentiles vs averages and ramp-up stages.",
                    "advanced": "Analyzes coordinated omission in load generators, database connection starvation, and CI performance regression budgets.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
        {
            "stage": QuestionStage.CODING,
            "competency_area": "Test Results Processing & Reporting",
            "question_text": "Write a function `generate_test_summary(results: List[dict]) -> dict` that parses test outcome records and returns total count, passed count, failed count, pass rate percentage, and names of failed tests.",
            "rubric": QuestionRubric(
                reference_answer="Iterate through test results, count pass/fail statuses, calculate percentage safely handling zero division, and aggregate failure names in O(N) time.",
                key_concepts_expected=["List & Dictionary Processing", "Zero Division Protection", "Accurate Percentage Calculation", "O(N) Time Complexity", "Edge Case Handling (empty results)"],
                depth_criteria={
                    "basic": "Simple loops without empty list handling.",
                    "intermediate": "Clean dictionary aggregation with accurate calculations.",
                    "advanced": "Handles edge cases, structures formatted output report, and supports categorized failure groupings.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
            "coding_challenge": {
                "title": "Test Results Summary Reporter",
                "problem_statement": "Given a list of dicts with keys 'test_name' and 'status' ('PASSED'/'FAILED'), return a dict summary with totals and pass rate percentage.",
                "starter_code": "def generate_test_summary(results: list) -> dict:\n    # TODO: Implement test summary generator\n    pass\n",
                "test_cases": [
                    {"input": "[{'test_name': 'test_login', 'status': 'PASSED'}, {'test_name': 'test_payment', 'status': 'FAILED'}]", "expected_output": "{'total': 2, 'passed': 1, 'failed': 1, 'pass_rate': 50.0, 'failed_tests': ['test_payment']}", "is_hidden": False},
                ],
            },
        },
        {
            "stage": QuestionStage.CLOSING,
            "competency_area": "Quality Engineering, Test Strategy & Bug Triage",
            "question_text": "How do you manage the defect lifecycle, conduct Root Cause Analysis (RCA) on production escapes, and integrate automated regression suites into CI/CD release gates?",
            "rubric": QuestionRubric(
                reference_answer="Track defects through triage, severity/priority assignment, investigation, verification, and closure. For production escapes, conduct 5-Whys RCA and write automated regression tests. CI/CD gates block merges on test suite failures.",
                key_concepts_expected=["Defect Lifecycle (Triage, Severity, RCA)", "5-Whys Root Cause Analysis", "Automated Regression Gates in CI/CD", "Risk-Based Test Prioritization"],
                depth_criteria={
                    "basic": "Describes reporting bugs in Jira.",
                    "intermediate": "Explains severity vs priority, RCA practices, and automated smoke test gating.",
                    "advanced": "Designs automated release gating with flaky test quarantining, risk-based test selection, and metric-driven quality dashboards.",
                },
                scoring_guide={"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0},
            ),
        },
    ],
}


def _normalize_coding_challenge(coding_ch: Optional[Dict[str, Any]], role_value: str, idx: int) -> Optional[Dict[str, Any]]:
    """Guarantees a complete candidate-facing coding challenge payload with public test cases."""
    if not coding_ch or not isinstance(coding_ch, dict):
        pool = _fallback_coding_challenges(role_value, 1)
        if pool:
            coding_ch = dict(pool[0])
        else:
            return None

    ch = dict(coding_ch)
    if "challenge_id" not in ch:
        ch["challenge_id"] = f"code_{role_value}_{idx + 1}"
    if "title" not in ch:
        ch["title"] = f"Coding Challenge ({role_value.replace('_', ' ').title()})"
    if "problem_statement" not in ch:
        ch["problem_statement"] = "Implement the requested algorithm according to standard input/output specifications."
    if "starter_code" not in ch:
        ch["starter_code"] = "import sys\n\ndef main():\n    # TODO: Implement solution\n    pass\n\nif __name__ == '__main__':\n    main()\n"
    if "starter_templates" not in ch or not ch["starter_templates"]:
        ch["starter_templates"] = {
            "python": ch.get("starter_code", ""),
            "javascript": "const fs = require('fs');\n\nfunction main() {\n    // TODO: Implement solution\n}\nmain();\n",
            "cpp": "#include <iostream>\nusing namespace std;\nint main() {\n    // TODO: Implement solution\n    return 0;\n}\n",
            "c": "#include <stdio.h>\nint main() {\n    // TODO: Implement solution\n    return 0;\n}\n",
            "java": "import java.util.*;\npublic class Solution {\n    public static void main(String[] args) {\n        // TODO: Implement solution\n    }\n}\n",
        }
    if "recommended_languages" not in ch:
        ch["recommended_languages"] = ["python", "javascript", "cpp", "c", "java"]

    # Normalize public test cases
    if "public_test_cases" not in ch or not ch["public_test_cases"]:
        if "test_cases" in ch and isinstance(ch["test_cases"], list):
            public_cases = []
            for i, tc in enumerate(ch["test_cases"]):
                if isinstance(tc, dict) and not tc.get("is_hidden", False):
                    inp = str(tc.get("input", "")).strip()
                    out = str(tc.get("expected_output", "")).strip()
                    public_cases.append({
                        "test_id": i + 1,
                        "description": tc.get("description", f"Sample Test {i + 1}"),
                        "stdin": inp + "\n" if not inp.endswith("\n") else inp,
                        "expected_stdout": out + "\n" if not out.endswith("\n") else out,
                        "is_hidden": False,
                    })
            ch["public_test_cases"] = public_cases if public_cases else [
                {
                    "test_id": 1,
                    "description": "Sample test",
                    "stdin": "5\n4 2 7 2 1\n",
                    "expected_stdout": "YES\n",
                    "is_hidden": False,
                }
            ]
        else:
            ch["public_test_cases"] = [
                {
                    "test_id": 1,
                    "description": "Sample test",
                    "stdin": "5\n4 2 7 2 1\n",
                    "expected_stdout": "YES\n",
                    "is_hidden": False,
                }
            ]
    return ch


def _generate_fallback_rubric_plan(
    job_role: StandardRole,
    seniority: SeniorityLevel,
    candidate_skills: List[str],
    candidate_projects: Optional[List[Dict]] = None,
    total_questions: int = 6,
) -> List[InterviewQuestion]:
    """
    Generate deterministic, stage-paced interview questions with complete grading rubrics.
    Guaranteed to execute in < 50ms (in-memory lookup) with ZERO repeated questions.
    """
    role_bank = _OFFLINE_RUBRIC_QUESTION_BANK.get(
        job_role, _OFFLINE_RUBRIC_QUESTION_BANK[StandardRole.BACKEND_ENGINEER]
    )

    # Resolve candidate project context
    project_clause = ""
    if candidate_projects and len(candidate_projects) > 0:
        first_proj = candidate_projects[0]
        p_name = str((first_proj or {}).get("name", "")).strip()
        if p_name:
            project_clause = f" on '{p_name}'"

    allocated_questions: List[InterviewQuestion] = []
    
    # Strictly select unique templates from role_bank without repeating
    target_count = min(len(role_bank), max(4, int(total_questions or 6)))
    for idx in range(target_count):
        tmpl = role_bank[idx]
        
        stage = tmpl["stage"]
        comp_area = tmpl["competency_area"]
        raw_text = tmpl["question_text"]
        
        # Format project clause if applicable
        if "{project_clause}" in raw_text:
            question_text = raw_text.replace("{project_clause}", project_clause)
        else:
            question_text = raw_text

        # Base rubric
        base_rubric: QuestionRubric = tmpl["rubric"]
        rubric_copy = QuestionRubric(
            reference_answer=base_rubric.reference_answer,
            key_concepts_expected=list(base_rubric.key_concepts_expected),
            depth_criteria=dict(base_rubric.depth_criteria),
            scoring_guide=dict(base_rubric.scoring_guide),
        )

        q_id = f"q_{idx + 1}"
        coding_ch = _normalize_coding_challenge(tmpl.get("coding_challenge"), job_role.value, idx) if stage == QuestionStage.CODING else None
        coding_id = f"code_{job_role.value}_{idx + 1}" if stage == QuestionStage.CODING else None

        allocated_questions.append(
            InterviewQuestion(
                question_id=q_id,
                question_index=idx,
                stage=stage,
                competency_area=comp_area,
                difficulty=seniority,
                question_text=question_text,
                rubric=rubric_copy,
                coding_challenge_id=coding_id,
                coding_challenge=coding_ch,
            )
        )

    return allocated_questions


async def generate_rubric_backed_plan(
    job_role: StandardRole | str,
    seniority: SeniorityLevel | str = SeniorityLevel.MID,
    candidate_skills: Optional[List[str]] = None,
    candidate_projects: Optional[List[Dict]] = None,
    total_questions: int = 6,
    job_description: Optional[str] = None,
    required_job_skills: Optional[List[str]] = None,
) -> List[InterviewQuestion]:
    """
    Generate personalized, stage-paced interview questions with pre-computed reference
    answers, expected concepts, and grading rubrics.
    Guarantees strict deduplication and zero question repetition.
    """
    norm_role, norm_seniority = _normalize_role_and_seniority(job_role, seniority)
    candidate_skills = list(candidate_skills or [])
    candidate_projects = list(candidate_projects or [])
    required_job_skills = list(required_job_skills or [])
    total_q = min(6, max(4, int(total_questions or 6)))

    project_summary = _project_summary(candidate_projects)
    
    prompt = (
        f"You are a technical interview committee lead at a top technology firm.\n"
        f"Generate a deterministic, stage-paced interview question plan for a candidate applying as:\n"
        f"JOB ROLE: {norm_role.value}\n"
        f"SENIORITY: {norm_seniority.value}\n"
        f"JOB DESCRIPTION: {job_description or 'Standard software engineering role'}\n"
        f"REQUIRED JOB SKILLS: {', '.join(required_job_skills) if required_job_skills else 'Standard role skills'}\n"
        f"CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Standard tech skills'}\n"
        f"CANDIDATE PROJECTS:\n{project_summary}\n\n"
        f"STAGE ALLOCATION (Must generate exactly {total_q} questions in this sequential order):\n"
        f"1. Stage 'icebreaker' (Question 1): Candidate intro, role motivations, stack background.\n"
        f"2. Stage 'core_technical' (Questions 2..{total_q - 3}): Core engineering concepts and fundamentals from role competency matrix.\n"
        f"3. Stage 'deep_dive' (Question {total_q - 2}): Project or complex architectural deep dive on trade-offs and bottlenecks.\n"
        f"4. Stage 'coding' (Question {total_q - 1}): Algorithmic problem with clear problem_statement and test_cases.\n"
        f"5. Stage 'closing' (Question {total_q}): Web security, testing, reliability, and engineering leadership.\n\n"
        "MANDATORY RUBRIC REQUIREMENTS FOR EVERY SINGLE QUESTION:\n"
        "- Every question MUST include a 'rubric' object.\n"
        "- 'reference_answer': A comprehensive 2-4 sentence explanation of an exemplary answer.\n"
        "- 'key_concepts_expected': A JSON list with AT LEAST 2 technical keywords/concepts.\n"
        "- 'depth_criteria': Object with keys 'basic', 'intermediate', and 'advanced'.\n"
        "- 'scoring_guide': Object with 'relevance_max' (30.0), 'depth_max' (40.0), 'accuracy_max' (30.0).\n\n"
        "OUTPUT FORMAT: Return ONLY a valid JSON array of question objects matching this schema:\n"
        "[\n"
        "  {\n"
        "    \"question_text\": \"...\",\n"
        "    \"stage\": \"icebreaker|core_technical|deep_dive|coding|closing\",\n"
        "    \"competency_area\": \"...\",\n"
        "    \"difficulty\": \"entry|mid|senior|lead\",\n"
        "    \"rubric\": {\n"
        "      \"reference_answer\": \"...\",\n"
        "      \"key_concepts_expected\": [\"concept1\", \"concept2\"],\n"
        "      \"depth_criteria\": {\"basic\": \"...\", \"intermediate\": \"...\", \"advanced\": \"...\"},\n"
        "      \"scoring_guide\": {\"relevance_max\": 30.0, \"depth_max\": 40.0, \"accuracy_max\": 30.0}\n"
        "    }\n"
        "  }\n"
        "]\n"
        "No markdown, no backticks, no commentary outside the JSON array."
    )

    try:
        raw_resp = _try_interview_llm_call(
            messages=[{"role": "user", "content": prompt}],
            system="You are an expert technical interviewer. Return only a valid JSON array of interview questions with complete rubrics.",
            temperature=0.7,
            max_tokens=4000,
        )
        if not raw_resp:
            return _generate_fallback_rubric_plan(
                norm_role, norm_seniority, candidate_skills, candidate_projects, total_q
            )

        parsed_items = _parse_json_array(raw_resp)
        if not isinstance(parsed_items, list) or len(parsed_items) == 0:
            return _generate_fallback_rubric_plan(
                norm_role, norm_seniority, candidate_skills, candidate_projects, total_q
            )

        seen_normalized_texts = set()
        validated_questions: List[InterviewQuestion] = []
        for idx, item in enumerate(parsed_items):
            if len(validated_questions) >= total_q:
                break
            if not isinstance(item, dict):
                continue
            text = str(item.get("question_text", "")).strip()
            if not text:
                continue

            # Deduplicate by normalized text key
            norm_key = re.sub(r"[^\w\s]", "", text.lower())[:80]
            if norm_key in seen_normalized_texts:
                continue
            seen_normalized_texts.add(norm_key)

            stage_str = str(item.get("stage", "core_technical")).strip().lower()
            try:
                stage_enum = QuestionStage(stage_str)
            except ValueError:
                stage_enum = QuestionStage.CORE_TECHNICAL

            diff_str = str(item.get("difficulty", norm_seniority.value)).strip().lower()
            try:
                diff_enum = SeniorityLevel(diff_str)
            except ValueError:
                diff_enum = norm_seniority

            comp_area = str(item.get("competency_area", "Technical Competency")).strip()

            raw_rubric = item.get("rubric") or {}
            ref_ans = str(raw_rubric.get("reference_answer", "")).strip()
            expected_concepts = raw_rubric.get("key_concepts_expected", [])
            if not isinstance(expected_concepts, list) or len(expected_concepts) < 2:
                # Fill default concepts if missing
                expected_concepts = [comp_area, f"{norm_role.value} best practices"]

            if not ref_ans:
                ref_ans = f"Candidate is expected to explain {comp_area} principles, implementation steps, and trade-offs."

            depth_crit = raw_rubric.get("depth_criteria")
            if not isinstance(depth_crit, dict) or not all(k in depth_crit for k in ["basic", "intermediate", "advanced"]):
                depth_crit = {
                    "basic": "Candidate demonstrates superficial understanding with partial concepts.",
                    "intermediate": "Candidate explains standard working principles and typical use cases.",
                    "advanced": "Candidate explains deep internal mechanics, performance trade-offs, and edge cases.",
                }

            scoring_guide = raw_rubric.get("scoring_guide")
            if not isinstance(scoring_guide, dict):
                scoring_guide = {"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0}

            rubric = QuestionRubric(
                reference_answer=ref_ans,
                key_concepts_expected=[str(c).strip() for c in expected_concepts if str(c).strip()],
                depth_criteria={k: str(v) for k, v in depth_crit.items()},
                scoring_guide={k: float(v) for k, v in scoring_guide.items()},
            )

            q_out_idx = len(validated_questions)
            coding_ch = _normalize_coding_challenge(item.get("coding_challenge"), norm_role.value, q_out_idx) if stage_enum == QuestionStage.CODING else None
            coding_id = f"code_{norm_role.value}_{q_out_idx + 1}" if stage_enum == QuestionStage.CODING else None

            validated_questions.append(
                InterviewQuestion(
                    question_id=f"q_{q_out_idx + 1}",
                    question_index=q_out_idx,
                    stage=stage_enum,
                    competency_area=comp_area,
                    difficulty=diff_enum,
                    question_text=text,
                    rubric=rubric,
                    coding_challenge_id=coding_id,
                    coding_challenge=coding_ch,
                )
            )

        if len(validated_questions) < total_q:
            # Fallback if insufficient valid questions generated
            return _generate_fallback_rubric_plan(
                norm_role, norm_seniority, candidate_skills, candidate_projects, total_q
            )

        return validated_questions

    except Exception:
        return _generate_fallback_rubric_plan(
            norm_role, norm_seniority, candidate_skills, candidate_projects, total_q
        )
