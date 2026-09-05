---
name: hiresight-backend
description: Best practices and operational instructions for HireSIGHT FastAPI backend development. Use this skill when modifying or building backend services, Beanie ODM schemas, MediaPipe computer vision metrics, Librosa acoustic pipelines, LLM question rubrics, sandbox code execution, or running backend pytest suites.
---

# HireSIGHT Backend Development & Operations

This skill provides guidelines, architectural patterns, and execution commands for the HireSIGHT FastAPI Python backend.

## 1. Architecture & Service Map

All backend code lives in [`backend/app/`](file:///d:/FYP/Code/backend/app/):

- **Auth & Roles** (`backend/app/auth/`): JWT tokens, candidate/admin permissions, job CRUD.
- **Resume & AI NER** (`backend/app/resume/`, `backend/app/ai/`): PDF/DOCX parsing, OCR fallback, domain filtering, skill normalization.
- **Live Interview Engine** (`backend/app/interview/`): Session state machine, question sequencing, STT/TTS routing.
- **Analysis Services** (`backend/app/interview/services/`):
  - `behavioral_analysis.py`: MediaPipe 468-point Face Mesh, normalized gaze stability ratio, 3D head pose with `cv2.solvePnP`.
  - `vocal_analysis.py`: Librosa/OpenSMILE acoustic feature extraction (F0 pitch, RMS energy, speech rate WPM, pause ratio).
  - `code_execution.py`: Subprocess sandboxing with timeout (max 5s compile, max 3s run) and 10KB output buffer.
  - `llm_service.py`: Question generation with reference rubrics and rubric-anchored answer evaluations.
  - `recruiter_report.py`: 5-dimensional explainable scoring aggregation.

---

## 2. Backend Coding Standards

1. **Strict Type Annotations**: Every function must include explicit type hints.
2. **Pydantic v2 Schemas**: Request bodies and response payloads must use Pydantic v2 models.
3. **Async / Sync Separation**:
   - Use `async/await` for database (Motor/Beanie) and network I/O.
   - Heavy CPU operations (OpenCV frame processing, audio waveform slicing) must be executed in threads via `asyncio.to_thread()`.
4. **Standard API Envelope**:
   ```python
   from pydantic import BaseModel
   from typing import Generic, TypeVar, Optional

   T = TypeVar("T")

   class APIResponse(BaseModel, Generic[T]):
       success: bool = True
       data: Optional[T] = None
       message: Optional[str] = None
       error: Optional[str] = None
   ```
5. **Report Secrecy Enforcement**:
   - Ensure candidate endpoints never expose `final_hiring_decision`, `red_flags`, or recruiter notes.
   - Verify permissions with `get_current_admin` dependency for recruiter-only routes.

---

## 3. Computer Vision & Audio Invariants

- **Normalized Coordinates**: Always normalize facial landmarks by inter-ocular distance (`dist(left_eye, right_eye)`) or face bounding box dimensions. Never use raw pixel distances.
- **Observable Physical Indicators**:
  - ✅ `gaze_stability_ratio`, `head_pose_variance`, `speaking_rate_wpm`, `pause_duration_ratio`
  - ❌ `is_lying`, `is_nervous`, `confidence_level`

---

## 4. Operational Commands & Testing

### Run Development Server
```powershell
cd d:\FYP\Code\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Backend Tests & System Validation
Use the skill helper script to run the test suite:
```powershell
python .agents/skills/hiresight-backend/scripts/run_backend_tests.py
```

Or execute directly with pytest:
```powershell
cd d:\FYP\Code\backend
pytest -v
python validate_system.py
```
