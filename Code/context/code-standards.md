# Code Standards - HireSIGHT

## General Principles

- **Clean Architecture & Separation of Concerns**: Keep route handlers thin; orchestrate business logic in services (`app/*/service.py`), domain rules in domain models (`app/*/domain/`), and database persistence in Beanie models (`app/*/models.py`).
- **Fix Root Causes**: Address underlying edge cases at the source (e.g. normalizing eye coordinates relative to face dimensions) rather than patching with ad-hoc heuristics.
- **Fail Gracefully**: External AI services (LLMs, OCR, audio extractors) must have robust fallbacks (e.g. Grok → Groq → deterministic question bank; OpenSMILE → Librosa).

---

## Python / FastAPI Backend Standards

- **Strict Type Annotations**: All function signatures must declare explicit type annotations for parameters and return values.
- **Pydantic v2 Models**: All request bodies, response payloads, and configuration settings must be validated using Pydantic models.
- **Async by Default**: Use `async`/`await` for all I/O operations (database queries, network requests, file reading). Heavy CPU operations (e.g. OpenCV image processing, code execution subprocesses) must be offloaded via `asyncio.to_thread()`.
- **Exception Handling**: Use custom domain exceptions mapped to standard HTTP exceptions in `app.core.exceptions`. Never leak raw stack traces to client responses.
- **Temporary Resource Cleanup**: Always use `try...finally` or context managers when writing temporary files (audio/video frames) to ensure immediate disk cleanup.

```python
# Standard API Response Envelope Pattern
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None
```

---

## JavaScript / React / Next.js Standards

- **Strict UI Context Adherence**: All pages and components must strictly adhere to the technical dark-mode design system, color tokens, and layout standards defined in [`context/ui-context.md`](file:///d:/FYP/Code/context/ui-context.md). Never introduce unapproved ad-hoc light themes or arbitrary hex colors.
- **Component Modularity**: Keep components single-purpose. Break complex views (like the live interview screen) into dedicated subcomponents (`VideoFeed`, `QuestionPrompt`, `CodingWorkspace`, `Timer`, `AudioVisualizer`).
- **State Management**: Centralize session state in clean React hooks; avoid prop drilling across deep component trees.
- **Defensive Rendering**: Always guard against `undefined`/`null` nested metrics (e.g. `report?.recruiter_report?.aggregate_scores?.technical_score ?? 0`).
- **No Hardcoded API URLs**: Use `NEXT_PUBLIC_API_URL` configured in environment variables, consumed via `services/api.js`.

---

## Computer Vision & Audio Standards

- **Resolution Independence**: Never use absolute pixel distances for facial geometry. Always normalize landmark distances by inter-ocular distance (`dist(left_eye, right_eye)`) or face bounding box dimensions.
- **Standardized Head Pose**: Use 3D landmark correspondence with `cv2.solvePnP` against canonical 3D face models instead of 2D slope heuristics.
- **Observable Metrics Only**: Behavioral metrics must be named objectively:
  - ✅ `gaze_stability_ratio`, `head_pose_variance`, `speaking_rate_wpm`, `pause_duration_ratio`
  - ❌ `is_lying`, `is_nervous`, `psychological_confidence`

---

## Sandboxed Code Execution Standards

- **Timeout Enforcement**: Every code execution run must specify strict `compile_timeout` (max 5s) and `run_timeout` (max 3s per test case).
- **Process Isolation**: Subprocesses must run with non-root permissions, restricted scratch directories, and output buffer truncation (max 10KB stdout/stderr) to prevent memory flooding.
- **Hidden Test Case Secrecy**: Hidden test cases are evaluated entirely on the backend; the API response must return only `passed: bool`, `runtime_ms`, and `error_type` for hidden tests without exposing raw inputs/outputs.

---

## File Organization & Naming Conventions

- **Python Files**: `snake_case.py` (e.g., `behavioral_analysis.py`, `recruiter_report.py`).
- **React Components**: `PascalCase.jsx` (e.g., `CodingWorkspace.jsx`, `RecruiterReportViewer.jsx`).
- **React Pages**: `kebab-case.jsx` or lowercase (e.g., `admin-dashboard.jsx`, `interview.jsx`).
- **Feature Specs**: `FEAT-XXX-<LAYER>-<name>.md` where `<LAYER>` is `BE`, `FE`, `INT`, or `VERIFY`.
