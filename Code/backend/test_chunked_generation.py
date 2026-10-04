import asyncio, sys, traceback, json, re
sys.stdout.reconfigure(encoding='utf-8')
from app.interview.services.llm_service import _try_interview_llm_call

def extract_valid_json_objects(text: str) -> list:
    text = re.sub(r"```json|```", "", text).strip()
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket > start_bracket:
        try:
            parsed = json.loads(text[start_bracket:end_bracket + 1])
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    objects = []
    in_string = False
    escape_char = False
    brace_depth = 0
    obj_start = -1

    for idx, char in enumerate(text):
        if char == '"' and not escape_char:
            in_string = not in_string
        elif char == '\\' and in_string:
            escape_char = not escape_char
            continue

        if not in_string:
            if char == '{':
                if brace_depth == 0:
                    obj_start = idx
                brace_depth += 1
            elif char == '}':
                if brace_depth > 0:
                    brace_depth -= 1
                    if brace_depth == 0 and obj_start != -1:
                        obj_str = text[obj_start:idx + 1]
                        try:
                            obj = json.loads(obj_str)
                            if isinstance(obj, dict) and "question_text" in obj:
                                objects.append(obj)
                        except Exception:
                            pass
                        obj_start = -1
        escape_char = False

    return objects

async def run_chunked():
    # Chunk 1: Technical
    prompt1 = """Session Entropy: chunk1
You are a principal technical interviewer at a top technology firm.
Generate 10 technical questions for:
TARGET JOB ROLE: Java Developer
SENIORITY LEVEL: mid
SPECIALIZED STACK: Java, Spring Boot, Hibernate/JPA, Microservices, PostgreSQL

Generate 10 questions in JSON array:
- 2 'icebreaker' questions on Java Developer background & motivations
- 5 'core_technical' questions on Java 17+, JVM, Spring Boot, Hibernate/JPA, and PostgreSQL
- 3 'deep_dive' questions on microservices architecture, distributed transactions, and high-concurrency Java systems

OUTPUT: JSON array of objects with:
"question_text", "stage", "competency_area", "difficulty", "rubric" (reference_answer, key_concepts_expected, depth_criteria, scoring_guide).
No markdown, no commentary outside JSON array."""

    print("Requesting Chunk 1 (Technical)...")
    r1 = _try_interview_llm_call([{"role": "user", "content": prompt1}], max_tokens=2500)
    items1 = extract_valid_json_objects(r1 or "")
    print(f"Chunk 1 returned {len(items1)} questions:")
    for q in items1[:4]:
        print(" -", q.get("stage"), "|", q.get("question_text")[:80])

    # Chunk 2: Coding & Behavioral
    prompt2 = """Session Entropy: chunk2
You are a principal technical interviewer at a top technology firm.
Generate 10 questions for:
TARGET JOB ROLE: Java Developer
SENIORITY LEVEL: mid
SPECIALIZED STACK: Java, Spring Boot, Microservices

Generate 10 questions in JSON array:
- 3 'coding' algorithmic coding challenges suitable for Java (with problem_statement and test_cases)
- 4 'behavioral' questions using STAR methodology for Java engineers
- 3 'closing' questions on Java automated testing (JUnit 5, Mockito), security, and CI/CD

OUTPUT: JSON array of objects with:
"question_text", "stage", "competency_area", "difficulty", "rubric" (reference_answer, key_concepts_expected, depth_criteria, scoring_guide).
No markdown, no commentary outside JSON array."""

    print("\nRequesting Chunk 2 (Coding & Behavioral)...")
    r2 = _try_interview_llm_call([{"role": "user", "content": prompt2}], max_tokens=2500)
    items2 = extract_valid_json_objects(r2 or "")
    print(f"Chunk 2 returned {len(items2)} questions:")
    for q in items2[:4]:
        print(" -", q.get("stage"), "|", q.get("question_text")[:80])

    total_combined = items1 + items2
    print(f"\nTotal questions generated successfully: {len(total_combined)}/20!")

if __name__ == "__main__":
    asyncio.run(run_chunked())
