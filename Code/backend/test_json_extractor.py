import json, re

def extract_valid_json_objects(text: str) -> list:
    """Extract all complete JSON objects from text, even if the surrounding array was truncated."""
    text = re.sub(r"```json|```", "", text).strip()
    # Try direct parse first
    start_bracket = text.find("[")
    end_bracket = text.rfind("]")
    if start_bracket != -1 and end_bracket > start_bracket:
        try:
            parsed = json.loads(text[start_bracket:end_bracket + 1])
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # Extract individual objects by tracking balanced braces
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

# Test on truncated string
truncated_text = '''[
  {
    "question_text": "Q1 for Java?",
    "stage": "icebreaker",
    "competency_area": "Java",
    "difficulty": "mid",
    "rubric": {
      "reference_answer": "Answer 1",
      "key_concepts_expected": ["c1", "c2"],
      "depth_criteria": {"basic": "b", "intermediate": "i", "advanced": "a"},
      "scoring_guide": {"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0}
    }
  },
  {
    "question_text": "Q2 for Spring Boot?",
    "stage": "core_technical",
    "competency_area": "Spring",
    "difficulty": "mid",
    "rubric": {
      "reference_answer": "Answer 2",
      "key_concepts_expected": ["c3", "c4"],
      "depth_criteria": {"basic": "b", "intermediate": "i", "advanced": "a"},
      "scoring_guide": {"relevance_max": 30.0, "depth_max": 40.0, "accuracy_max": 30.0}
    }
  },
  {
    "question_text": "Q3 incomplete...",
    "stage": "deep_dive",
    "rubric": {
      "reference_answer": "'''

extracted = extract_valid_json_objects(truncated_text)
print(f"Extracted {len(extracted)} valid objects from truncated stream!")
for q in extracted:
    print(" -", q["question_text"])
