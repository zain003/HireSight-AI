# Architecture Context - HireSIGHT

## Technology Stack

| Layer | Technology | Role / Responsibility |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js (React 18), Tailwind CSS, Lucide Icons | Responsive candidate interview interface, coding IDE, and admin dashboards |
| **Backend API** | FastAPI (Python 3.9+), Uvicorn, Pydantic v2 | High-performance asynchronous REST API, orchestration, and business logic |
| **Database** | MongoDB, Beanie ODM, Motor (Async driver) | Document storage for users, job posts, profiles, interview sessions, and reports |
| **Speech-to-Text** | Vosk (Offline Kaldi ASR), Whisper fallback | Local real-time audio transcription with zero external cloud dependency |
| **Text-to-Speech** | Edge-TTS (Neural voice synthesis) | Natural audio delivery of interview questions |
| **Computer Vision** | Google MediaPipe (468 Face Mesh), OpenCV | Observable facial landmark detection, normalized gaze tracking, 3D head pose |
| **Voice Analysis** | Librosa, OpenSMILE (GeMAPS feature set), SoundFile | Acoustic feature extraction (F0 pitch, RMS energy, speech rate WPM, pause ratio) |
| **LLM Reasoning** | xAI Grok / Groq (Llama 3.3 70B Versatile) | Structured question generation with rubrics, answer evaluation against rubrics |
| **Code Execution** | Python Subprocess sandbox with memory/time cgroups | Isolated execution of candidate code against public and hidden test cases |
| **Resume Extraction** | pdfplumber, python-docx, Tesseract OCR, BERT NER | Text extraction and entity recognition from PDF, Word, and image CVs |

---

## System Boundaries & Directory Ownership

- `backend/app/resume/` — Owns document upload parsing, OCR fallback, domain filtering (computing vs non-computing), and structured candidate profile generation.
- `backend/app/ai/` — Owns entity recognition (NER), skill taxonomy normalization, and skill extraction logic.
- `backend/app/auth/` — Owns user authentication (JWT), role management (Candidate vs Admin), job posting CRUD, and candidate-job application linking.
- `backend/app/interview/` — Owns live interview session orchestration, question planning with rubrics, STT/TTS routing, coding execution sandbox, CV & acoustic metric collation, 5-dimensional explainable scoring, and recruiter report generation.
- `backend/app/interview/services/` — Owns specialized sub-services:
  - `behavioral_analysis.py`: MediaPipe computer vision metrics.
  - `vocal_analysis.py`: Acoustic feature extraction and speech rate analysis.
  - `code_execution.py`: Multi-language code sandbox runner.
  - `llm_service.py`: LLM question planning, rubric generation, and answer scoring.
  - `recruiter_report.py`: 5-dimensional data aggregation and report builder.
- `frontend/src/pages/` — Owns client-side routing (Candidate login/dashboard/interview, Admin dashboard/reports/job management).
- `frontend/src/components/` — Reusable domain components (`Interview`, `Admin`, `Resume`, `Candidate`, `Auth`).

---

## Storage Model

- **MongoDB Collections (Beanie Documents)**:
  - `users`: User identity, hashed credentials, role (`candidate` or `admin`), timestamps.
  - `profiles`: Extracted candidate profiles, normalized skills, experience years, education, projects, certifications.
  - `job_posts`: Recruiter job postings, required skills, competency criteria, seniority level.
  - `interview_sessions`: Complete interview state, question list with reference rubrics, per-question evaluations, observable CV/acoustic frames, coding execution records, 5-dimensional aggregate scores, and final recruiter reports.
- **Local / File Storage (`/storage`, `/uploads`)**:
  - Raw resume binary files (PDF/DOCX/PNG).
  - Temporary audio recordings (`.webm`, `.wav`) during STT transcode (cleaned immediately after analysis).
  - Generated PDF recruiter reports.

---

## Auth and Access Control Model

- **JWT Authentication**: Bearer tokens issued upon login/register, verified via FastAPI dependencies (`get_current_active_user`, `get_current_admin`).
- **Role Separation**:
  - `Candidate`: Can upload resume, configure own interview, participate in live interview session, and execute code.
  - `Admin / Recruiter`: Can create job postings, view all candidate applications, view comprehensive 5-dimensional recruiter reports, and download PDF summaries.
- **Report Secrecy Invariant**: Candidate endpoints **MUST NEVER** return final hiring recommendations, recruiter notes, or behavioral red flag flags to candidate sessions. Recruiter reports are strictly accessible by admin roles.

---

## Core System Invariants

1. **Explainable Scoring**: Every score in the 5-dimensional model must be directly computable from recorded question evaluations, test results, and acoustic/CV measurements. No black-box magic numbers.
2. **Observable Physical Signals**: Computer vision and voice analysis must only measure objective, observable physical indicators (e.g. eye gaze stability, 3D head rotation angles, words-per-minute, pause ratios). The system must never make unsupported psychological or emotion-guessing claims.
3. **Question Reference Rubrics**: Every generated technical question must contain a pre-computed reference answer key, expected technical concepts, and grading rubric stored at question creation time.
4. **Isolated Code Execution**: Code execution must occur in a restricted sandbox with hard CPU timeout (max 5s per test case), memory caps, and zero access to the host filesystem outside the scratch directory.
5. **Session Resilience**: Live interview progress is persistently saved after every question. A page reload or network blip must allow resuming from the current question index without losing prior data.
6. **Hidden Test Privacy**: Hidden test inputs and expected outputs must never be transmitted to the frontend client.
