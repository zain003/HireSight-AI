# HireSIGHT - AI-Powered Technical Assessment & Interview Platform

## Overview

HireSIGHT is an intelligent, end-to-end technical recruitment and AI mock interview platform that systematically evaluates candidates across multiple objective dimensions. From the initial moment a candidate uploads their resume to the final generation of an explainable recruiter report, HireSIGHT automates candidate profile extraction, role-competency mapping, interactive interview configuration, dynamic question delivery with rubric-backed evaluation, observable computer vision analysis, acoustic voice evaluation, and sandboxed coding assessments.

The platform eliminates black-box hiring decisions by providing transparent, mathematically grounded scores across five core evaluation dimensions, accompanied by actionable feedback and verifiable audit trails.

---

## Goals

1. **End-to-End Automation**: Deliver a continuous, friction-free 13-stage pipeline from resume upload to final candidate fit report.
2. **5-Dimensional Assessment**: Measure candidates across Technical Knowledge (35%), Coding Ability (20%), Role Fit (15%), Communication (15%), and Behavioral Indicators (15%).
3. **Explainable & Transparent Scoring**: Ensure every numerical score is supported by question-by-question evidence, rubric comparisons, and mathematical formulas rather than opaque AI assertions.
4. **Observable, Bias-Resistant Analysis**: Evaluate computer vision (gaze ratio, head stability, facial dynamics) and vocal acoustics (speech rate, pitch variance, pauses) strictly on measurable physical signals without unsupported psychological claims.
5. **Secure Coding Verification**: Execute and evaluate code against visible and hidden test cases in an isolated sandbox with runtime and memory constraints.

---

## Complete 13-Stage End-to-End Pipeline Flow

```
1. Resume Upload (PDF/DOCX/Images + OCR Fallback)
   ↓
2. Resume Validation & Parsing (Domain filter, NER & profile structuring)
   ↓
3. Candidate Profile & Role Mapping (Extract skills, map to role taxonomy & seniority)
   ↓
4. Interview Configuration (Candidate role/difficulty confirmation, agenda generation)
   ↓
5. Question Selection & Rubric Generation (Technical, CV-based, Coding with reference keys)
   ↓
6. Live AI Interview (TTS question delivery, real-time webcam & audio capture)
   ↓
7. Answer Processing & STT (Vosk offline STT / Whisper fallback, transcript alignment)
   ↓
8. Technical Evaluation (LLM rubric comparison, concept coverage %, accuracy scoring)
   ↓
9. Observable Behavioral & Vocal Analysis (MediaPipe 468 landmarks + OpenSMILE/Librosa)
   ↓
10. Sandboxed Coding Assessment (Multi-language runner, public + hidden test cases)
    ↓
11. Data Aggregation & Normalization (5-dimensional metric collation)
    ↓
12. Explainable Final Scoring (Weighted 5-dim model, audit trail, Fit status)
    ↓
13. Feedback & Report Generation (Actionable gap remediation, JSON & PDF export)
```

---

## Core User Flows

### Candidate Flow
1. **Profile Setup & Upload**: Register/login, upload resume (PDF/DOCX/Image), and review parsed technical profile.
2. **Interview Configuration**: Select target job role, confirm inferred seniority level (Junior/Mid/Senior), choose coding language, and view the interview agenda.
3. **Live AI Interview**: Proceed through structured interview stages (Icebreaker → Technical Core → CV Deep Dive → Coding Challenge → Closing) using audio or text with live video feedback.
4. **Coding Challenge**: Solve role-aligned programming problem in the online editor, running code against public tests and submitting for hidden test evaluation.
5. **Interview Completion**: Complete session and view submission confirmation (scores and recruiter recommendations remain restricted to hiring teams).

### Admin / Recruiter Flow
1. **Job Post Creation**: Create job postings specifying required skills, domain concepts, and seniority requirements.
2. **Applicant Tracking**: Review candidate applications, match scores, and parsed skill profiles.
3. **Recruiter Report Review**: Access comprehensive 5-dimensional candidate reports with executive summaries, radar score breakdowns, question-by-question transcripts with rubric benchmarks, behavioral/acoustic metrics, and coding benchmark results.
4. **Export & Sharing**: Download publication-grade PDF and JSON reports with full mathematical audit logs to inform hiring committee decisions.

---

## Feature Scope

### In Scope
- Multi-format resume parsing (PDF, DOCX, PNG/JPG) with Tesseract OCR fallback and computing domain validation.
- Standardized Role & Seniority Taxonomy mapping candidate profiles to core technical competency clusters.
- Pre-interview configuration interface for candidate role confirmation, difficulty selection, and agenda preview.
- Dynamic question generation storing reference answer keys, key points expected, and grading rubrics.
- Live interview runner with offline Speech-to-Text (Vosk), Text-to-Speech (Edge TTS), and video stream capture.
- Observable computer vision analysis (MediaPipe Face Mesh 468 landmarks) for normalized eye gaze, 3D head pose stability, and facial movement dynamics.
- Acoustic speech analysis (Librosa / OpenSMILE) for speech rate (WPM), pitch variance, pause duration ratio, and vocal confidence.
- Sandboxed multi-language code runner (Python, JavaScript, C++, C, Java) with public and hidden test case evaluation.
- 5-Dimensional Explainable Scoring Model (Technical, Coding, Role Fit, Communication, Behavioral) with transparent weight calculations.
- Actionable feedback generation identifying specific concept gaps and targeted remediation steps.
- Recruiter report viewer and downloadable PDF report generator.

### Out of Scope
- Fully automated, definitive "Hire / No Hire" hiring decisions without human recruiter review.
- Pseudoscientific psychological profiling or emotion lie-detection claims.
- Live peer-to-peer human video streaming or multi-interviewer panel conferencing.
- Third-party applicant tracking system (ATS) bi-directional integrations in MVP.

---

## Success Criteria

1. **Parsing Reliability**: Accurate text extraction from native and scanned resumes (>90% extraction rate on standard tech CVs).
2. **Deterministic Evaluation**: Technical answers graded against explicit reference rubrics with zero arbitrary score variance.
3. **Observable CV Accuracy**: Eye gaze and head pose metrics normalized to camera resolution and face scale without frame-rate drop.
4. **Coding Security**: Isolated execution terminating infinite loops/crashes within timeout limits (max 5s per test) without leaking hidden test cases.
5. **Scoring Explainability**: 100% of final scores include a transparent formula breakdown linking directly to individual question evaluations.
