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
QUESTION STRUCTURE (for a full interview):
1. Icebreaker ("Tell me about yourself")
2-3. Behavioral (STAR method)
4-6. Technical (role-specific)
7. Situational / problem-solving
8. Closing ("Do you have questions for us?")
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


async def generate_question_plan(
    job_role: str,
    job_description: str,
    candidate_skills: List[str],
    total_questions: int = 8,
) -> List[dict]:
    prompt = (
        f"Generate exactly {total_questions} interview questions.\n\n"
        f"JOB ROLE: {job_role}\n\n"
        f"JOB DESCRIPTION: {job_description or 'Standard role'}\n\n"
        f"CANDIDATE SKILLS: {', '.join(candidate_skills) if candidate_skills else 'Not provided'}\n\n"
        f"Return a JSON array of exactly {total_questions} objects:\n"
        "[\n"
        "  {\"question_text\": \"...\", \"question_type\": \"behavioral|technical|follow_up|closing\"}\n"
        "]\n\n"
        "Structure:\n"
        "- Index 0: Warm icebreaker\n"
        "- Index 1-2: Behavioral\n"
        "- Index 3-5: Technical\n"
        "- Index 6: Situational\n"
        "- Index 7: Closing\n\n"
        "Keep each question max 2 sentences.\n"
        "Return ONLY the JSON array."
    )

    raw = _sdk_call(
        [{"role": "user", "content": prompt}],
        system=_INTERVIEWER_SYSTEM,
        max_tokens=1500,
    )
    questions = _parse_json_array(raw)
    return questions[:total_questions]


async def generate_followup_question(
    job_role: str,
    original_question: str,
    candidate_answer: str,
    conversation_history: List[dict],
) -> dict:
    prompt = (
        "The candidate gave a shallow answer. Generate ONE follow-up question.\n\n"
        f"ORIGINAL QUESTION: {original_question}\n\n"
        f"CANDIDATE'S ANSWER: {candidate_answer}\n\n"
        f"JOB ROLE: {job_role}\n\n"
        "Return ONLY this JSON:\n"
        "{\"question_text\": \"...\", \"question_type\": \"follow_up\"}"
    )

    history = conversation_history[-6:]
    raw = _sdk_call(history + [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=200)
    return _parse_json(raw)


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
