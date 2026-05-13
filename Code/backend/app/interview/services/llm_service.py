"""LLM service for interviews: Grok for question generation; Grok-then-Groq for scoring helpers."""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from typing import Dict, List, Optional

import httpx


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
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        messages=msg_list,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


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

    return AnswerEvaluation(
        question_index=0,
        question_text=question_text,
        question_type=question_type,
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
