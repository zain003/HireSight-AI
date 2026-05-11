"""Groq LLM service for both MCQ and live interview modules."""

from __future__ import annotations

import json
import os
import re
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
You are an expert AI HR Interviewer conducting a fully automated voice interview.
Be professional, warm, and unbiased.
RULES:
- Ask ONE question at a time - short and clear (max 2 sentences for TTS)
- Never chain multiple questions
- Be encouraging - never make the candidate feel judged mid-interview
- Adapt based on previous answers
QUESTION STRUCTURE (verbal interview phases, in order):
1. Introduction — candidate introduces themselves
2. Technical — role-specific depth
3. Behavioral — STAR-style past behavior
4. CV-based — tied to resume projects and experience
5. Coding — separate batch: programming tasks with public test cases (for a future online judge).
OUTPUT must be valid JSON only. No extra text. No markdown.
"""


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


def _coding_challenge_count(total_questions: int) -> int:
    """Use 3 coding tasks for longer interviews, otherwise 2."""
    t = int(total_questions)
    return 3 if t >= 11 else 2


def _verbal_question_budget(total_questions: int, coding_n: int) -> int:
    """Questions for intro + technical + behavioral + cv (coding appended separately)."""
    return max(4, min(12, int(total_questions) - coding_n))


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
        difficulty = "easy" if idx < 2 else ("medium" if idx < 4 else "hard")
        technical_questions.append(
            {
                "question_text": f"For a {job_role} role, explain how you would apply {skill} in a production scenario and what tradeoffs you would consider.",
                "question_type": "technical",
                "stage": "technical",
                "difficulty": difficulty,
            }
        )
    while len(technical_questions) < 6:
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
        if len(cv_questions) >= 6:
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
    cv_questions = cv_questions[:6]

    introduction_q = [
        {
            "question_text": f"Please introduce yourself: your background, education, and why you are interested in this {job_role} role.",
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
        *introduction_q,
        *technical_questions[:6],
        *behavioral_q,
        *cv_questions[:6],
    ]


def _fallback_coding_challenges(job_role: str, n: int) -> List[dict]:
    """Deterministic coding tasks when the LLM fails (stdin/stdout, Python)."""
    role_hint = (job_role or "software").strip()
    pool = [
        {
            "title": f"Warm-up — sums ({role_hint})",
            "problem_statement": (
                "Read from stdin: first line contains an integer n (1 ≤ n ≤ 100). "
                "Second line contains n integers separated by spaces. "
                "Print the sum of all integers followed by a newline."
            ),
            "difficulty": "easy",
            "recommended_languages": ["python"],
            "constraints": "Use 64-bit arithmetic; inputs fit in typical int range.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    # TODO: parse n and the list, print sum + newline\n"
                "    pass\n\n\n"
                'if __name__ == \"__main__\":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "mixed signs",
                    "stdin": "4\n10 -3 5 2\n",
                    "expected_stdout": "14\n",
                },
                {
                    "description": "single value",
                    "stdin": "1\n42\n",
                    "expected_stdout": "42\n",
                },
            ],
        },
        {
            "title": "Reverse words",
            "problem_statement": (
                "Read one line from stdin (may contain spaces). "
                "Print the words in reverse order, preserving a single space between words. "
                "Trailing newline at end of output."
            ),
            "difficulty": "medium",
            "recommended_languages": ["python"],
            "constraints": "Line length ≤ 500 characters.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    line = sys.stdin.readline()\n"
                "    # TODO: reverse word order, print result\n"
                "    pass\n\n\n"
                'if __name__ == \"__main__\":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "three words",
                    "stdin": "data pipelines rock\n",
                    "expected_stdout": "rock pipelines data\n",
                },
                {
                    "description": "single word",
                    "stdin": "kafka\n",
                    "expected_stdout": "kafka\n",
                },
            ],
        },
        {
            "title": "First duplicate index",
            "problem_statement": (
                "Read from stdin: first line integer n (2 ≤ n ≤ 2000). "
                "Second line: n integers. Print the 0-based index of the first value "
                "that appears more than once. If every value is unique, print -1. "
                "End with newline."
            ),
            "difficulty": "medium",
            "recommended_languages": ["python"],
            "constraints": "O(n) time expected.",
            "starter_code": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    # TODO: implement duplicate detection\n"
                "    pass\n\n\n"
                'if __name__ == \"__main__\":\n'
                "    main()\n"
            ),
            "public_test_cases": [
                {
                    "description": "duplicate exists",
                    "stdin": "5\n1 3 3 2 4\n",
                    "expected_stdout": "2\n",
                },
                {
                    "description": "all unique",
                    "stdin": "3\n1 2 3\n",
                    "expected_stdout": "-1\n",
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
    starter = str(obj.get("starter_code", "") or "").strip()
    if not starter:
        starter = (
            "import sys\n\n\ndef main():\n"
            "    # Read stdin, write answer to stdout\n"
            "    pass\n\n\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
        )
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
        f"You generate {num_problems} small programming exercises for an interview for: {job_role}.\n"
        f"Job context: {(job_description or '')[:1200]}\n"
        f"Role-required skills (themes): {skill_ctx}\n"
        f"Candidate skills (hints): {cand_ctx}\n\n"
        "Requirements:\n"
        "- Problems must be solvable in under 15 minutes each.\n"
        "- Prefer stdin/stdout in Python 3 (clear formats).\n"
        "- Include exactly 2 public_test_cases per problem with precise stdin and expected_stdout "
        "(include trailing newline in expected_stdout when printing lines).\n"
        "- starter_code must be valid Python with a main() or solve() entry reading stdin.\n"
        "- Difficulty spread: first easier, later slightly harder.\n\n"
        "Return ONLY a JSON array (no markdown) of objects:\n"
        "[{\n"
        '  "title": "...",\n'
        '  "problem_statement": "...",\n'
        '  "difficulty": "easy|medium|hard",\n'
        '  "recommended_languages": ["python"],\n'
        '  "constraints": "optional string",\n'
        '  "starter_code": "...",\n'
        '  "public_test_cases": [\n'
        '    {"description": "...", "stdin": "...", "expected_stdout": "..."}\n'
        "  ],\n"
        '  "evaluation_notes": "one line"\n'
        "}]\n"
    )
    raw = _sdk_call(
        [{"role": "user", "content": prompt}],
        system=_INTERVIEWER_SYSTEM,
        temperature=0.55,
        max_tokens=3200,
    )
    try:
        arr = _parse_json_array(raw)
    except Exception:
        arr = []
    normalized = []
    for item in arr:
        ch = _coding_challenge_dict_from_llm(item if isinstance(item, dict) else {})
        if ch:
            normalized.append(ch)
        if len(normalized) >= num_problems:
            break
    if len(normalized) < num_problems:
        normalized.extend(
            _fallback_coding_challenges(job_role, num_problems - len(normalized))
        )
    return normalized[:num_problems]


def _question_entries_from_coding_challenges(challenges: List[dict]) -> List[dict]:
    rows = []
    for ch in challenges:
        stmt = ch.get("problem_statement") or ch.get("title") or ""
        teaser = stmt[:320] + ("…" if len(stmt) > 320 else "")
        voice_intro = (
            f"This is a coding exercise: {ch.get('title')}. "
            "Use the on-screen instructions and starter code. "
            "When your workspace is ready, briefly outline your approach, then implement."
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
    total_questions: int = 8,
) -> List[dict]:
    coding_count = _coding_challenge_count(total_questions)
    verbal_budget = _verbal_question_budget(total_questions, coding_count)
    intro_count, technical_count, behavioral_count, cv_based_count = _allocate_four_phase_counts(
        verbal_budget
    )
    target_verbal_total = intro_count + technical_count + behavioral_count + cv_based_count

    asked_questions = asked_questions or []
    asked_norm = {
        _normalize_question_text(q) for q in asked_questions if _normalize_question_text(q)
    }
    project_ctx = _project_summary(candidate_projects or [])

    prompt = (
        "You are an AI Interviewer. Conduct a structured VERBAL interview in 4 PHASES (this exact order). "
        f"A separate coding segment after these phases will add {coding_count} programming exercises — "
        "do NOT output coding tasks here.\n\n"
        "VERBAL PHASES:\n"
        f"1) introduction: exactly {intro_count} question(s) — welcome the candidate and ask them to introduce themselves (background, education, motivation for this role). No STAR behavioral prompts here.\n"
        f"2) technical: exactly {technical_count} questions — role-specific; progressive difficulty easy→medium→hard; cover ALL required job skills.\n"
        f"3) behavioral: exactly {behavioral_count} questions — STAR-style past behavior (teamwork, conflict, priorities, learning).\n"
        f"4) cv_based: exactly {cv_based_count} questions — must reference the candidate's CV (projects, roles, companies, skills, certifications).\n\n"
        f"JOB ROLE: {job_role}\n\n"
        f"JOB DESCRIPTION: {job_description or 'Standard role'}\n\n"
        f"REQUIRED JOB SKILLS (COVER ALL IN TECHNICAL PHASE): {', '.join(required_job_skills or []) or 'Not provided'}\n\n"
        f"CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Not provided'}\n\n"
        f"CANDIDATE EXPERIENCE (YEARS): {experience_years if experience_years is not None else 'Not provided'}\n\n"
        f"CANDIDATE PROJECTS:\n{project_ctx}\n\n"
        f"CANDIDATE JOB TITLES: {candidate_job_titles or []}\n"
        f"CANDIDATE CERTIFICATIONS: {candidate_certifications or []}\n"
        f"CANDIDATE COMPANIES/INTERNSHIPS: {candidate_companies or []}\n\n"
        f"ALREADY ASKED QUESTIONS (DO NOT REPEAT): {asked_questions}\n\n"
        "RULES:\n"
        "- Every question must be NEW and UNIQUE\n"
        "- Do not repeat/near-repeat any question from asked_questions\n"
        "- Keep each question max 2 sentences\n"
        f"- Technical phase must cover ALL required job skills at least once across its {technical_count} questions\n"
        "- CV phase must reference CV content (projects, employment, skills), not generic trivia\n"
        "- Return strictly in phase order: all introduction, then all technical, then all behavioral, then all cv_based\n\n"
        f"Return a JSON array of exactly {target_verbal_total} objects:\n"
        "[\n"
        "  {\"question_text\": \"...\", \"question_type\": \"introduction|technical|behavioral|cv_based\", "
        "\"stage\": \"introduction|technical|behavioral|cv_based\", \"difficulty\": \"easy|medium|hard\"}\n"
        "]\n\n"
        "Return ONLY the JSON array."
    )

    raw = _sdk_call(
        [{"role": "user", "content": prompt}],
        system=_INTERVIEWER_SYSTEM,
        max_tokens=1500,
    )
    try:
        generated = _parse_json_array(raw)
    except Exception:
        generated = []

    clean_questions: List[dict] = []
    seen_norm = set(asked_norm)

    for q in generated:
        text = str((q or {}).get("question_text", "")).strip()
        q_type = str((q or {}).get("question_type", "")).strip().lower()
        stage = str((q or {}).get("stage", "")).strip().lower() or q_type
        difficulty = str((q or {}).get("difficulty", "")).strip().lower() or "medium"

        if not text:
            continue
        if q_type not in {"introduction", "behavioral", "technical", "cv_based"}:
            continue
        if stage not in {"introduction", "behavioral", "technical", "cv_based"}:
            stage = q_type
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

    # If model output is incomplete, fill with deterministic fallback questions
    fallback = _build_fallback_question_bank(
        job_role=job_role,
        required_job_skills=required_job_skills or [],
        candidate_skills=candidate_skills,
        candidate_projects=candidate_projects or [],
        candidate_job_titles=candidate_job_titles or [],
        candidate_certifications=candidate_certifications or [],
        candidate_companies=candidate_companies or [],
        experience_years=experience_years,
    )
    for fq in fallback:
        if len(clean_questions) >= target_verbal_total:
            break
        key = _normalize_question_text(fq["question_text"])
        if key in seen_norm:
            continue
        seen_norm.add(key)
        clean_questions.append(fq)

    # Enforce strict stage distribution (phase order: intro → technical → behavioral → cv)
    introduction = [q for q in clean_questions if q["stage"] == "introduction"][:intro_count]
    technical = [q for q in clean_questions if q["stage"] == "technical"][:technical_count]
    behavioral = [q for q in clean_questions if q["stage"] == "behavioral"][:behavioral_count]
    cv_based = [q for q in clean_questions if q["stage"] == "cv_based"][:cv_based_count]

    # Ensure technical stage covers all required job skills.
    required_skills = required_job_skills or []
    if required_skills:
        technical_text_blob = " ".join(q.get("question_text", "").lower() for q in technical)
        missing_required = [s for s in required_skills if s and s.lower() not in technical_text_blob]
        for skill in missing_required:
            replacement = {
                "question_text": f"How would you apply {skill} in this {job_role} role, and what implementation tradeoffs would you evaluate?",
                "question_type": "technical",
                "stage": "technical",
                "difficulty": "medium",
            }
            if len(technical) < technical_count:
                technical.append(replacement)
            else:
                technical[-1] = replacement
            technical_text_blob = " ".join(q.get("question_text", "").lower() for q in technical)
            if all(rs.lower() in technical_text_blob for rs in required_skills if rs):
                break

    # Ensure introduction phase has at least one question
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

    # Ensure CV stage covers projects + skills + experience.
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

    technical = technical[:technical_count]
    behavioral = behavioral[:behavioral_count]
    cv_based = cv_based[:cv_based_count]

    # If any stage is still short, pull from fallback by stage
    if (
        len(introduction) < intro_count
        or len(behavioral) < behavioral_count
        or len(technical) < technical_count
        or len(cv_based) < cv_based_count
    ):
        for fq in fallback:
            key = _normalize_question_text(fq["question_text"])
            combined = introduction + technical + behavioral + cv_based
            if key in {_normalize_question_text(x["question_text"]) for x in combined}:
                continue
            if fq["stage"] == "introduction" and len(introduction) < intro_count:
                introduction.append(fq)
            elif fq["stage"] == "behavioral" and len(behavioral) < behavioral_count:
                behavioral.append(fq)
            elif fq["stage"] == "technical" and len(technical) < technical_count:
                technical.append(fq)
            elif fq["stage"] == "cv_based" and len(cv_based) < cv_based_count:
                cv_based.append(fq)

    ordered_verbal = (introduction + technical + behavioral + cv_based)[:target_verbal_total]

    try:
        coding_chunks = await _generate_coding_challenges_llm(
            job_role=job_role,
            job_description=job_description or "",
            required_job_skills=required_job_skills or [],
            candidate_skills=candidate_skills or [],
            num_problems=coding_count,
        )
        coding_questions = _question_entries_from_coding_challenges(coding_chunks)
    except Exception:
        coding_questions = _question_entries_from_coding_challenges(
            _fallback_coding_challenges(job_role, coding_count)
        )

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
    raw = _sdk_call(history + [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=200)
    parsed = _parse_json(raw)
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

    raw = _sdk_call(
        [{"role": "user", "content": prompt}],
        system=_EVALUATOR_SYSTEM
        + "\n- coaching_detected: Detect if the transcript shows someone else giving the candidate the answer."
        + " Set to true if coaching is detected.",
        temperature=0.3,
        max_tokens=600,
    )

    data = _parse_json(raw)
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

    raw = _sdk_call(
        [{"role": "user", "content": prompt}],
        system="You are an expert HR analyst. Be objective and professional. Return only valid JSON.",
        temperature=0.4,
        max_tokens=800,
    )
    return _parse_json(raw)
