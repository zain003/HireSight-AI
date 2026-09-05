# UI Context & Design System — HireSIGHT

## 1. Visual Language & Theme Philosophy

HireSIGHT uses a **Technical AI Workspace** aesthetic:
- **Dark-First Technical Workspace**: Deep obsidian, slate, and navy backgrounds with layered translucency. Zero plain or glaring white backgrounds in the main application flow.
- **Glassmorphism & Depth**: Surfaces utilize semi-transparent backdrops (`bg-slate-900/60`, `bg-white/5`, `backdrop-blur-md`) bordered with subtle 1px translucent strokes (`border-white/10`, `border-indigo-400/20`).
- **Curated Neon Accents**: Atmospheric indigo, violet, sky-blue, and emerald accents provide clear focal points for interactive elements, status badges, and active session controls.
- **Clarity Under Pressure**: The candidate live interview UI is intentionally minimal and distraction-free, prioritizing clear question prompts, live transcription feedback, and an integrated coding sandbox.

---

## 2. Color System & Design Tokens

All UI components must adhere to the standardized color palette and semantic tokens:

### Palette & Tokens

| Token Role | Tailwind Class / CSS Variable | Hex / RGBA Equivalent | Semantic Usage |
| :--- | :--- | :--- | :--- |
| **Base Background** | `bg-slate-950` / `--deep-night` | `#020617` / `#0b1220` | Root canvas and full-screen layout backgrounds |
| **Layered Surface** | `bg-slate-900/60` / `bg-white/5` | `rgba(15, 23, 42, 0.60)` | Primary cards, panels, control surfaces, and dialogs |
| **Subtle Sub-Surface** | `bg-slate-950/50` / `bg-white/10` | `rgba(2, 6, 23, 0.50)` | Nested stat tiles, editor containers, input backgrounds |
| **Primary Accent** | `bg-indigo-500` / `text-indigo-400` | `#6366f1` / `#4f46e5` | Primary buttons, active tabs, selected states, hero highlights |
| **Secondary Accent** | `bg-violet-600` / `text-violet-400` | `#7c3aed` / `#8b5cf6` | Button gradients (`from-indigo-500 to-violet-600`), AI badges |
| **Information / Tech** | `text-sky-400` / `bg-sky-500/10` | `#38bdf8` | Stage indicators, informational badges, technical tags |
| **Success / Passing** | `text-emerald-400` / `bg-emerald-500/10` | `#34d399` / `#10b981` | Passed tests, strong scores (≥80%), live webcam active |
| **Warning / Review** | `text-amber-400` / `bg-amber-500/10` | `#fbbf24` / `#f59e0b` | Mid scores (60–79%), missing profile skills, timer alerts |
| **Error / Critical** | `text-red-400` / `bg-red-500/10` | `#f87171` / `#ef4444` | Failed tests, critical red flags, network disconnect banners |
| **Primary Text** | `text-white` / `text-slate-100` | `#ffffff` / `#f1f5f9` | Page titles, card headers, active labels, primary content |
| **Secondary Text** | `text-slate-300` / `text-slate-200` | `#cbd5e1` / `#e2e8f0` | Body copy, descriptions, question prompts, instructions |
| **Muted Text** | `text-slate-400` / `text-slate-500` | `#94a3b8` / `#64748b` | Timestamps, metadata labels, keyboard shortcuts |
| **Default Border** | `border-white/10` | `rgba(255, 255, 255, 0.10)` | Card dividers, panel outlines, structural borders |
| **Highlight Border** | `border-indigo-400/30` / `border-neon` | `rgba(99, 102, 241, 0.30)` | Active selections, focus rings, interactive card hovers |

---

## 3. Typography & Hierarchy

HireSIGHT uses **Inter** for all UI typography and monospace fonts for technical code blocks:

| Hierarchy Level | Tailwind Classes | Font Weight | Usage Context |
| :--- | :--- | :--- | :--- |
| **Display / H1** | `text-3xl font-black text-white sm:text-4xl` | Black (900) / Bold (700) | Landing hero, major module headers |
| **Page Title / H2** | `text-2xl font-bold text-white sm:text-3xl` | Bold (700) | Page titles, setup headers, report candidate titles |
| **Section / H3** | `text-lg font-bold text-white` | Bold (700) / Semibold (600) | Panel titles, config step headers, question numbers |
| **Card Title / H4** | `text-sm font-semibold text-white` | Semibold (600) | Sub-cards, agenda stages, metric labels |
| **Body Standard** | `text-sm leading-relaxed text-slate-300` | Regular (400) / Medium (500) | Question prompts, candidate feedback, guidelines |
| **Micro / Metadata** | `text-xs uppercase tracking-wider text-slate-400` | Medium (500) / Semibold (600) | Metric tags, stage badges, input labels |
| **Code / Execution** | `font-mono text-xs text-slate-200` | Medium (500) | Monaco editor, compiler stdout/stderr, durations |

---

## 4. Border Radius & Structural Geometry

Consistent rounded geometries are enforced across all components:

| Component Type | Radius Standard | Example Tailwind Classes |
| :--- | :--- | :--- |
| **Root Panels & Hero Cards** | 16px | `rounded-2xl border border-white/10 bg-slate-900/60 p-6 shadow-xl` |
| **Interactive Selection Cards** | 12px | `rounded-xl border border-white/10 bg-slate-950/40 p-4` |
| **Primary Buttons & CTAs** | 12px | `rounded-xl px-6 py-3.5 text-sm font-semibold shadow-lg` |
| **Status Badges & Tags** | 8px or Full Pill | `rounded-lg px-2.5 py-1 text-xs` or `rounded-full px-3 py-1 text-xs` |
| **Form Inputs & Selects** | 10px | `rounded-lg border border-white/15 bg-slate-950/60 px-3 py-2 text-sm` |

---

## 5. Iconography Standard

All visual icons are strictly sourced from **`lucide-react`**:
- **Stroke-based Only**: Consistent stroke weights (`strokeWidth={2}` or default 1.5–2.0).
- **Standard Sizing**:
  - `h-3.5 w-3.5` / `h-4 w-4`: Inline badges, timestamp icons, sub-metric icons.
  - `h-5 w-5`: Card header icons, navigation links, button action indicators.
  - `h-6 w-6` to `h-8 w-8`: Status banners, large metric highlights, stage icons.

---

## 6. Key Screen & Layout Patterns

### A. Candidate Portal Shell (`CandidateHeader` + Responsive Body)
- **Top Navigation Bar**: Sticky, semi-transparent (`bg-slate-950/90 backdrop-blur border-b border-white/10`).
- **Brand Emblem**: `Hire` in pure white with `SIGHT` in `text-indigo-300 font-extrabold`.
- **Navigation Tabs**: Rounded pills with active background highlight (`bg-indigo-500 text-white`).
- **User Avatar Pill**: First letter avatar with username pill and clear logout button.

### B. Pre-Interview Setup & Calibration (`interview-setup.jsx`)
- **Profile Context Card**: Displays resume status, detected skill count with pill badges, and seniority inference.
- **Interactive Role Grid (`InterviewConfigCard.jsx`)**: 7 standard engineering roles with competency tags and live match indicators.
- **Seniority Tier Selector**: Radio cards (`Entry`, `Mid`, `Senior`, `Lead`) updating assessment depth.
- **Sandbox Language Selector**: Quick toggle for Python, JavaScript, Java, C++, C.
- **Dynamic Agenda Preview**: 4 visual stage cards showing duration and question count adapting to selected seniority.
- **Sticky Bottom Action Bar**: Elevated blur bar displaying chosen configuration with primary launch button.

### C. Live Multimodal Interview Room (`interview.jsx`)
- **Header Control Bar**: Elapsed interview timer, live question stage counter (`Question X of 20`), camera/mic status indicators.
- **Split Workspace Layout**:
  - **Left Pane**: Live candidate WebRTC video feed with facial landmark overlay bounding box, AI interviewer speech status indicator, and real-time speech-to-text transcript.
  - **Right Pane**: Question prompt card, reference rubric context (when in review), and mode-switching workspace:
    - *Verbal Mode*: Visual audio waveform, speech recognition feedback, STAR structure hints.
    - *Coding Mode (`CodingWorkspace.jsx`)*: Full Monaco editor with dark theme (`#1a1b26`), language switch, run test cases button, and public/hidden test output terminal.
- **Footer Control Bar**: Action buttons for Submit Answer, Skip Question, Text/Voice Input Toggle, and End Interview.

### D. Admin & Recruiter Dashboard (`admin-dashboard.jsx`)
- **Multi-Tab Navigation**: Active Job Posts, Candidate Applications, Evaluated Sessions, System Config.
- **Job Posting CRUD Drawer / Form**: Standard role selector, required skill multi-select, description, seniority target.
- **Recruiter Report Viewer (`RecruiterReportViewer.jsx`)**:
  - Radial SVG score gauges for overall hiring readiness.
  - 5-Dimensional score breakdown table (Technical, Coding, Role Fit, Communication, Behavioral).
  - Question-by-question transcript and rubric audit drawer.
  - PDF & JSON report export actions.

---

## 7. Interactive States & Micro-Animations

- **Hover States**: Cards subtly elevate and brighten border on hover (`hover:border-white/20 hover:bg-white/5 transition-all duration-200`).
- **Active / Focused States**: 2px ring with semi-transparent indigo or emerald glow (`ring-2 ring-indigo-400/40`).
- **Loading States**: Spinners with transparent top border (`animate-spin rounded-full border-2 border-indigo-400 border-t-transparent`).
- **Speech & Webcam Indicators**: Subtle pulse animations (`animate-pulse`) for active recording states.
- **Graceful Error Banners**: Prominent red/amber alert banners with specific retry actions on network or API failures.

---

## 8. Invariant: Strict Adherence for All Changes

1. **No Ad-Hoc Styling**: All new UI components and page modifications **MUST** use these predefined color tokens, radius classes, and layout structures.
2. **Responsive by Default**: Every screen must render cleanly across mobile (`sm: 640px`), tablet (`md: 768px`), and desktop (`lg: 1024px`, `xl: 1280px`).
3. **Secrecy in Candidate UI**: The candidate UI must **NEVER** expose recruiter-only scoring rubrics, psychological labels, or final hiring decision recommendations.
