import asyncio, sys, traceback
sys.stdout.reconfigure(encoding='utf-8')
from app.interview.services.llm_service import _try_interview_llm_call, _parse_json_array

prompt = """Session Entropy: test1234
You are a principal technical interviewer at a top technology firm.
Generate a customized, stage-paced interview question plan specifically tailored for:
TARGET JOB ROLE: Java Developer
STANDARDIZED DOMAIN: backend_engineer
SENIORITY LEVEL: mid (Focus on application design patterns, state management, REST/query optimization, caching, error boundaries, and integration best practices.)
SPECIALIZED STACK HINTS: Java, Spring Boot, Hibernate/JPA, Microservices, PostgreSQL, REST APIs
JOB DESCRIPTION: Standard software engineering position
CANDIDATE PROJECTS:
- Candidate has not provided project portfolio details.

MANDATORY INSTRUCTIONS:
1. Questions MUST specifically test the technologies and frameworks relevant to 'Java Developer' (e.g. if MERN stack, ask about MongoDB, Express, React, Node.js; if Django, ask about Python/Django; if Flutter, ask about Flutter/Dart).
2. Calibrate question difficulty strictly to the mid level.
3. Generate exactly 20 questions matching the STAGE ALLOCATION below in sequential order:
- Stage 'icebreaker': exactly 2 question(s)
- Stage 'core_technical': exactly 7 question(s)
- Stage 'deep_dive': exactly 3 question(s)
- Stage 'coding': exactly 3 question(s)
- Stage 'behavioral': exactly 3 question(s)
- Stage 'closing': exactly 2 question(s)

MANDATORY RUBRIC REQUIREMENTS FOR EVERY SINGLE QUESTION:
- Every question MUST include a 'rubric' object.
- 'reference_answer': A comprehensive 2-4 sentence explanation of an exemplary answer.
- 'key_concepts_expected': A JSON list with AT LEAST 2 technical keywords/concepts.
- 'depth_criteria': Object with keys 'basic', 'intermediate', and 'advanced'.
- 'scoring_guide': Object with 'relevance_max' (30.0), 'depth_max' (40.0), 'accuracy_max' (30.0).

OUTPUT FORMAT: Return ONLY a valid JSON array of question objects matching this schema:
[
  {
    "question_text": "...",
    "stage": "icebreaker|core_technical|deep_dive|coding|behavioral|closing",
    "competency_area": "...",
    "difficulty": "entry|mid|senior|lead",
    "rubric": {
      "reference_answer": "...",
      "key_concepts_expected": ["concept1", "concept2"],
      "depth_criteria": {"basic": "...", "intermediate": "...", "advanced": "..."},
      "scoring_guide": {"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0}
    }
  }
]
No markdown, no backticks, no commentary outside the JSON array."""

print('Sending prompt to LLM...')
resp = _try_interview_llm_call([{'role': 'user', 'content': prompt}], max_tokens=4500)
print('Response length:', len(resp) if resp else 'None')
if resp:
    print('Raw response snippet:\n', resp[:250])
    try:
        parsed = _parse_json_array(resp)
        print('Parsed successfully! Total question count:', len(parsed))
    except Exception as e:
        print('Parsing ERROR:', e)
        print('End of response was:\n', repr(resp[-250:]))
