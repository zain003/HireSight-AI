---
name: hiresight-frontend
description: Best practices and operational instructions for HireSIGHT Next.js and React frontend development. Use this skill when developing or modifying UI pages, WebRTC video/audio capture, the coding IDE workspace, state orchestration hooks, Tailwind styling, or running frontend build checks.
---

# HireSIGHT Frontend Development & Operations

This skill provides guidelines, architectural patterns, and execution commands for the HireSIGHT Next.js / React frontend.

## 1. Architecture & Component Structure

All frontend source code resides in [`frontend/src/`](file:///d:/FYP/Code/frontend/src/):

- **Pages (`src/pages/`)**:
  - `index.js`: Landing page & candidate/admin portal access.
  - `candidate/`: Candidate profile, resume upload, interview setup, role selection.
  - `interview/`: Live multimodal interview room (WebRTC video feed, live question prompter, coding IDE, timer).
  - `admin/`: Recruiter job management, candidate pipeline, and comprehensive 5-dimensional recruiter report viewer.
- **Components (`src/components/`)**:
  - `Interview/`: `VideoFeed.jsx`, `QuestionPrompt.jsx`, `CodingWorkspace.jsx`, `Timer.jsx`, `AudioVisualizer.jsx`.
  - `Admin/`: `JobPostForm.jsx`, `CandidateList.jsx`, `RecruiterReportViewer.jsx`, `MetricBreakdown.jsx`.
  - `Common/`: `Modal.jsx`, `Navbar.jsx`, `Button.jsx`, `Badge.jsx`.
- **Services (`src/services/`)**:
  - `api.js`: Centralized Axios/fetch client consuming `NEXT_PUBLIC_API_URL`.

---

## 2. Frontend Development Standards

1. **Design System & UI Context Adherence**:
   - Strictly follow the technical dark-mode design system, color tokens, and layout blueprints defined in [`context/ui-context.md`](file:///d:/FYP/Code/context/ui-context.md).
   - Use standardized obsidian surfaces (`bg-slate-950`, `bg-slate-900/60`), glassmorphic panels (`backdrop-blur-md`, `border-white/10`), and neon accents (`indigo-500`, `emerald-400`, `sky-400`).
   - Use `lucide-react` exclusively for stroke-based iconography.
2. **Defensive Rendering**:
   Always guard against missing or nested metrics in responses:
   ```javascript
   const technicalScore = report?.recruiter_report?.aggregate_scores?.technical_score ?? 0;
   const gazeStability = session?.behavioral_metrics?.gaze_stability_ratio ?? 0.0;
   ```
2. **WebRTC Stream Handling**:
   - Always prompt for permissions with clear fallback UI if the camera/microphone is denied or unavailable.
   - Clean up media tracks (`track.stop()`) on component unmount to prevent camera indicator lock.
3. **Coding IDE Sandbox Integration**:
   - Provide explicit language selector (Python, JavaScript, Java, C++).
   - Display clear status badges (`Running`, `Accepted`, `Wrong Answer`, `Timeout`, `Runtime Error`).
   - Never display hidden test case inputs or expected outputs to candidate views.
4. **State Isolation**:
   - Manage live interview stage transitions with clean state machines or custom hooks (`useInterviewSession`).
   - Persist question progress to survive accidental page reloads.

---

## 3. Operational Commands & Build Checks

### Run Next.js Development Server
```powershell
cd d:\FYP\Code\frontend
npm run dev
```

### Validate Frontend Build & Lints
```powershell
cd d:\FYP\Code\frontend
npm run build
```
