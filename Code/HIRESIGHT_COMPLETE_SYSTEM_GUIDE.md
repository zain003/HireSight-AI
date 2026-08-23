# HireSIGHT - Complete System Guide

## 📖 What is HireSIGHT?

HireSIGHT is an AI-powered interview and recruitment platform that automatically evaluates job candidates during video interviews. The system analyzes candidates across multiple dimensions and generates comprehensive reports to help companies make better hiring decisions.

---

## 🎯 Complete Pipeline Flow

### Step-by-Step Process

```
1. Admin Posts Job
   ↓
2. Candidate Sees Job & Uploads Resume
   ↓
3. System Matches Resume to Job Requirements
   ↓
4. If Match Score > Threshold → Interview Starts
   ↓
5. Live Interview with Real-Time Analysis
   ↓
6. Final Report Generated (Hidden from Candidate)
   ↓
7. Admin Reviews Report & Makes Hiring Decision
```

---

## 📋 Detailed Pipeline Explanation

### **PHASE 1: Job Posting**

**Who**: Admin/Recruiter  
**What Happens**:
- Admin logs into admin dashboard
- Creates a new job post with:
  - Job title (e.g., "Python Developer")
  - Job description
  - Required skills (e.g., "Python, Django, PostgreSQL")
  - Domain (e.g., "Software Development")
  - Status (Active/Draft/Closed)

**Files Involved**:
- `frontend/src/pages/admin-dashboard.jsx` - Admin dashboard UI
- `backend/app/auth/routes.py` - API endpoint: `POST /auth/admin/job-post`
- `backend/app/auth/job_post_model.py` - Database model

---

### **PHASE 2: Candidate Application**

**Who**: Job Candidate  
**What Happens**:
- Candidate browses available job postings
- Selects a job they're interested in
- Uploads their resume/CV (PDF or DOCX)

**Files Involved**:
- `frontend/src/pages/user-dashboard.jsx` - User dashboard
- `backend/app/resume/routes.py` - Resume upload endpoint
- `backend/app/storage/file_handler.py` - File storage

---

### **PHASE 3: Resume Matching**

**Who**: System (Automated)  
**What Happens**:

1. **Resume Parsing**:
   - Extracts text from PDF/DOCX
   - Uses NER (Named Entity Recognition) to identify:
     - Skills (Python, Java, AWS, etc.)
     - Experience years
     - Education
     - Previous roles

2. **Skill Matching**:
   - Compares candidate skills with job requirements
   - Calculates match percentage
   - Example:
     ```
     Job Requires: Python, Django, PostgreSQL, Docker
     Candidate Has: Python, Django, MySQL, Git
     Match: 50% (2 out of 4 skills)
     ```

3. **Decision**:
   - If match score ≥ threshold (e.g., 60%) → Proceed to interview
   - If match score < threshold → Candidate notified (not eligible)

**Files Involved**:
- `backend/app/resume/parser.py` - Resume text extraction
- `backend/app/ai/extraction.py` - NER skill extraction
- `backend/app/auth/skill_matcher.py` - Matching logic

---

### **PHASE 4: Live Interview** ⭐ MAIN PHASE

**Who**: Candidate (being interviewed)  
**Duration**: 20-45 minutes  
**What Happens**: Real-time multi-dimensional evaluation

#### **4A. Technical Knowledge Assessment (35% of score)**

**What We Evaluate**:
- Answer quality to technical questions
- Depth of technical knowledge
- Problem-solving approach

**How It Works**:
1. System generates questions based on job role (e.g., "Explain Python decorators")
2. Candidate answers verbally
3. Speech-to-text converts answer to text
4. LLM (AI) evaluates answer quality
5. System may ask follow-up questions if answer is unclear

**Technologies Used**:
- **Vosk**: Converts speech to text (offline, no internet needed)
- **LLM (OpenAI/Groq)**: Evaluates answer quality and relevance

**What Gets Scored**:
- Correctness of answer (0-100)
- Completeness of explanation
- Technical accuracy
- Ability to handle follow-up questions

**Files Involved**:
- `backend/app/interview/services/llm_service.py` - LLM evaluation
- `backend/app/interview/services/stt_service.py` - Speech-to-text

---

#### **4B. Communication Skills Assessment (25% of score)**

**What We Evaluate**:
- How clearly candidate speaks
- Voice confidence level
- Speech patterns and tone

**How It Works**:

**Voice Analysis** (Real-time audio processing):

1. **Vocal Confidence** (0-100):
   - Measures voice energy and steadiness
   - High energy = confident, Low energy = hesitant
   - Technology: OpenSMILE (acoustic feature extraction)

2. **Speech Clarity** (0-100):
   - How clearly words are pronounced
   - Measures articulation quality
   - Technology: Librosa (audio analysis)

3. **Pitch Variance** (0-100):
   - Variation in voice tone (not monotone)
   - Good variance = engaging speaker
   - Technology: Librosa (pitch tracking)

4. **Speech Rate** (0-100):
   - Words per minute
   - Too fast = nervous, Too slow = unprepared
   - Optimal: 120-150 words/minute

5. **Pause Patterns** (0-100):
   - Natural pauses vs. excessive "uh", "um"
   - Measures fluency

6. **Tone Consistency** (0-100):
   - Professional tone maintained throughout
   - No extreme emotional variations

**Technologies Used**:
- **OpenSMILE**: Extracts 88 acoustic features from voice
- **Librosa**: Audio signal processing
- **Vosk**: Real-time speech recognition

**What Gets Scored**:
```python
communication_score = (
    vocal_confidence × 25% +
    speech_clarity × 25% +
    pitch_variance × 15% +
    speech_rate × 15% +
    pause_pattern × 10% +
    tone_consistency × 10%
)
```

**Files Involved**:
- `backend/app/interview/services/vocal_analysis.py` - Voice analysis
- `backend/app/interview/services/stt_service.py` - Speech recognition

---

#### **4C. Behavioral Analysis (20% of score)** 👁️ COMPUTER VISION

**What We Evaluate**:
- Body language and facial expressions
- Eye contact with camera
- Posture and confidence
- Attention and engagement

**How It Works** (Real-time video analysis):

**Computer Vision Using MediaPipe**:
- Detects **468 facial landmarks** on candidate's face
- Tracks face position, eye movement, head angles
- Analyzes every video frame (30-60 frames per second)

**1. Eye Contact Detection** (0-100):
- **What**: Checks if candidate looks at camera
- **How**: Tracks iris position relative to eye center
  - Iris near center = looking at camera ✅
  - Iris far from center = looking away ❌
- **Technology**: MediaPipe iris landmarks (5 points per eye)
- **Score**: % of time maintaining eye contact

**2. Head Stability** (0-100):
- **What**: Measures how still candidate keeps their head
- **How**: Calculates head angles (yaw, pitch, roll)
  - Yaw: Left-right rotation
  - Pitch: Up-down rotation
  - Roll: Head tilt
- **Good**: Minimal movement (stable, attentive)
- **Bad**: Excessive movement (distracted, nervous)
- **Score**: % of frames with stable head position

**3. Facial Engagement** (0-100):
- **What**: Measures facial expressions and animation
- **How**: Tracks mouth movement, eyebrow raises, facial activity
- **Good**: Animated, expressive (engaged)
- **Bad**: Blank face (disengaged, uninterested)
- **Score**: Level of facial expression activity

**4. Fidgeting Detection** (0-100):
- **What**: Detects nervous movements
- **How**: Tracks rapid back-and-forth head movements
- **Example**: Turning head left, then right, then left quickly
- **Good**: Minimal fidgeting (calm, focused)
- **Bad**: High fidgeting (nervous, anxious)
- **Score**: 100 - (fidget_count / frames × 100)

**5. Confidence Posture** (0-100):
- **What**: Evaluates professional body language
- **How**: Analyzes head position and angles
- **Confident posture**:
  - Face forward (yaw < 20°)
  - Head upright (pitch between -10° and 20°)
  - Minimal tilt (roll < 15°)
- **Score**: % of time maintaining confident posture

**6. Attention Span** (0-100):
- **What**: Checks if candidate stays focused
- **How**: Tracks face presence in video frame
- **Good**: Face always visible (attentive)
- **Bad**: Frequently looks away or leaves frame (distracted)
- **Score**: % of time face is visible

**Technologies Used**:
- **MediaPipe Face Mesh**: Detects 468 facial landmarks
- **MediaPipe Face Detection**: Detects face presence
- **OpenCV**: Image processing and video analysis
- **NumPy**: Mathematical calculations

**What Gets Scored**:
```python
behavioral_score = (
    eye_contact × 25% +
    head_stability × 20% +
    facial_engagement × 20% +
    fidgeting × 15% +
    confidence_posture × 10% +
    attention_span × 10%
)
```

**Red Flags Detected**:
- ⚠️ Poor eye contact (score < 40)
- ⚠️ Unstable posture (excessive head movements)
- ⚠️ Low facial engagement (minimal expression)
- ⚠️ High fidgeting (nervousness detected)
- ⚠️ Attention issues (face not consistently visible)
- ⚠️ Frequent absence from frame (possible distractions)

**Files Involved**:
- `backend/app/interview/services/behavioral_analysis.py` - Complete behavioral analysis

---

#### **4D. Coding Assessment (20% of score)**

**What We Evaluate**:
- Ability to write working code
- Problem-solving skills
- Code quality

**How It Works**:
1. System presents coding challenge (e.g., "Write a function to reverse a string")
2. Candidate writes code in browser code editor
3. System executes code with test cases
4. Evaluates correctness

**Example**:
```
Challenge: "Write a function to check if a number is prime"
Test Cases:
  - Input: 7 → Expected: True
  - Input: 4 → Expected: False
  - Input: 1 → Expected: False

Candidate Code:
def is_prime(n):
    if n < 2: return False
    for i in range(2, n):
        if n % i == 0: return False
    return True

Result: 3/3 test cases passed ✅
Score: 100/100
```

**What Gets Scored**:
- Test cases passed (% of total)
- Correctness of logic
- Edge case handling
- Code quality

**Technologies Used**:
- **Code execution sandbox**: Runs code safely
- **Test case validation**: Automatic verification

**Files Involved**:
- `backend/app/interview/services/code_execution.py` - Code execution

---

### **PHASE 5: Report Generation** 📊

**Who**: System (Automated)  
**When**: Immediately after interview ends  
**What Happens**:

The system automatically generates a comprehensive hiring decision report that combines all evaluation data.

#### **Overall Score Calculation**:

```
Overall Score = (
    Technical Score × 35% +
    Communication Score × 25% +
    Behavioral Score × 20% +
    Coding Score × 20%
)
```

**Example**:
```
Technical: 85/100 × 0.35 = 29.75
Communication: 78/100 × 0.25 = 19.50
Behavioral: 82/100 × 0.20 = 16.40
Coding: 90/100 × 0.20 = 18.00
─────────────────────────────
Overall Score: 83.65/100
```

#### **Hiring Recommendation**:

Based on overall score:
- **85-100**: "Strong Hire" 🟢 (Highly recommended)
- **70-84**: "Hire" 🟢 (Recommended)
- **55-69**: "Maybe" 🟡 (Consider with reservations)
- **0-54**: "No Hire" 🔴 (Not recommended)

#### **Report Contents**:

1. **Executive Summary**: Brief overview of candidate performance
2. **Overall Score**: Final weighted score (0-100)
3. **Dimension Scores**:
   - Technical: 85/100
   - Communication: 78/100
   - Behavioral: 82/100
   - Coding: 90/100
4. **Strengths**: List of 5-10 strong points
   - Example: "Excellent technical knowledge in Python"
   - Example: "Strong problem-solving skills"
5. **Red Flags/Concerns**: Issues detected during interview
   - Example: "Poor eye contact during behavioral questions"
   - Example: "Hesitant speech patterns"
6. **Areas for Improvement**: Suggestions for candidate growth
7. **Detailed Analysis**: Deep dive into each dimension
8. **Question Performance**: How many questions answered/skipped
9. **Coding Results**: Test cases passed/failed
10. **Next Steps**: Recommended hiring actions

#### **Report Privacy** 🔒:

**IMPORTANT**: The detailed report is **completely hidden from the candidate**. Only the admin who posted the job can see it.

**Candidate sees**:
- ✅ "Interview completed" message
- ❌ NO scores
- ❌ NO report
- ❌ NO hiring recommendation

**Admin sees**:
- ✅ Complete report with all details
- ✅ All scores and metrics
- ✅ Hiring recommendation
- ✅ Strengths and weaknesses
- ✅ Red flags and concerns

**Files Involved**:
- `backend/app/interview/services/recruiter_report.py` - Report generation
- `backend/app/interview/models.py` - Report stored in `recruiter_report` field

---

### **PHASE 6: Admin Review**

**Who**: Admin/Recruiter  
**What Happens**:

1. **View Candidates List**:
   - Admin clicks "View Candidates" button on their job post
   - Sees list of all candidates who completed interviews
   - List shows:
     - Candidate name and email
     - Overall score
     - Hiring recommendation
     - Interview date
     - Status (Completed/In Progress)

2. **Filter & Sort**:
   - Filter by status: All, Completed, In Progress
   - Sort by: Score (high to low), Date, Name

3. **View Full Report**:
   - Admin clicks "View Full Report" on a candidate
   - Opens comprehensive report viewer with tabs:
     - **Summary**: Overall scores, strengths, concerns
     - **Scores**: Detailed breakdown of all metrics
     - **Analysis**: Deep analysis of each dimension
     - **Details**: Full recommendation and session info

4. **Make Decision**:
   - Based on report, admin decides:
     - Move to next round
     - Make job offer
     - Reject candidate
   - Can print/download report for records

**Files Involved**:
- `frontend/src/pages/admin-dashboard.jsx` - Admin dashboard
- `frontend/src/components/Admin/JobCandidatesList.jsx` - Candidates list
- `frontend/src/components/Interview/RecruiterReportViewer.jsx` - Report viewer
- `backend/app/auth/routes.py` - API endpoints:
  - `GET /auth/admin/job-posts/{id}/candidates`
  - `GET /auth/admin/job-posts/{id}/candidates/{session_id}/report`

---

## 🎯 What Gets Evaluated During Interview?

### Summary Table

| Dimension | Weight | What's Measured | Technologies |
|-----------|--------|-----------------|--------------|
| **Technical** | 35% | Answer quality, knowledge depth | Vosk (speech-to-text), LLM (evaluation) |
| **Communication** | 25% | Voice confidence, clarity, speech patterns | OpenSMILE, Librosa, Vosk |
| **Behavioral** | 20% | Eye contact, posture, engagement, attention | MediaPipe, OpenCV (computer vision) |
| **Coding** | 20% | Code correctness, test cases passed | Code execution sandbox |

---

## 🛠️ Technologies Used

### AI & Machine Learning
- **MediaPipe**: Facial landmark detection (468 points per face)
- **OpenSMILE**: Acoustic feature extraction (88 audio features)
- **Vosk**: Offline speech recognition
- **Librosa**: Audio signal processing
- **LLM (OpenAI/Groq)**: Answer evaluation
- **BERT NER**: Resume skill extraction

### Backend
- **Python 3.9+**: Programming language
- **FastAPI**: Web framework
- **MongoDB**: Database
- **Beanie**: MongoDB object-document mapper

### Frontend
- **Next.js**: React framework
- **React**: UI library
- **Tailwind CSS**: Styling

### Computer Vision Details
- **Face Detection**: Detects face presence in frame
- **Face Mesh**: 468 landmark points on face
- **Iris Tracking**: 5 points per eye for gaze detection
- **Head Pose Estimation**: 3D angles (yaw, pitch, roll)

---

## 📊 Score Calculation Examples

### Example 1: Strong Candidate

```
Technical: 92/100 (Excellent answers, deep knowledge)
Communication: 85/100 (Clear speech, confident voice)
Behavioral: 88/100 (Good eye contact, stable posture)
Coding: 95/100 (All test cases passed)

Overall = (92×0.35) + (85×0.25) + (88×0.20) + (95×0.20)
        = 32.2 + 21.25 + 17.6 + 19.0
        = 90.05/100

Recommendation: "Strong Hire" ✅
Confidence: High
```

### Example 2: Borderline Candidate

```
Technical: 65/100 (Decent answers, some gaps)
Communication: 58/100 (Hesitant speech, low confidence)
Behavioral: 52/100 (Poor eye contact, fidgeting)
Coding: 70/100 (Most test cases passed)

Overall = (65×0.35) + (58×0.25) + (52×0.20) + (70×0.20)
        = 22.75 + 14.5 + 10.4 + 14.0
        = 61.65/100

Recommendation: "Maybe" ⚠️
Confidence: Medium
Red Flags: Poor eye contact, Hesitant speech
```

---

## 🚨 Red Flags System

### Behavioral Red Flags
- Poor eye contact - looked away frequently
- Unstable posture - excessive head movements
- Low facial engagement - minimal expression
- High fidgeting - nervous behavior detected
- Attention issues - face not consistently visible
- Frequent absence from frame - distracted

### Communication Red Flags
- Low vocal confidence - hesitant speech
- Poor speech clarity - difficult to understand
- Monotone delivery - no voice variation
- Rapid speech - possible anxiety
- Excessive pauses - lack of fluency

### Technical Red Flags
- Unable to answer basic questions
- Excessive follow-ups needed
- Lack of technical depth
- Many questions skipped

### Coding Red Flags
- Failed basic test cases
- Did not complete challenges
- Poor code quality
- No edge case handling

---

## 📂 Key Files & Their Purpose

### Backend (Python)

**Interview Services**:
- `behavioral_analysis.py` - Face/eye tracking, posture analysis
- `vocal_analysis.py` - Voice analysis, speech patterns
- `stt_service.py` - Speech-to-text conversion
- `llm_service.py` - Answer evaluation
- `code_execution.py` - Run and test code
- `recruiter_report.py` - Generate final report

**Routes**:
- `interview/routes.py` - Interview API endpoints
- `auth/routes.py` - Admin, job posts, candidates API

**Models**:
- `interview/models.py` - InterviewSession database model
- `auth/job_post_model.py` - JobPost database model

### Frontend (React/Next.js)

**Pages**:
- `admin-dashboard.jsx` - Admin control panel
- `user-dashboard.jsx` - Candidate interface

**Components**:
- `JobCandidatesList.jsx` - List of candidates per job
- `RecruiterReportViewer.jsx` - Full report display
- `MetricsDashboard.jsx` - Real-time interview metrics

---

## 🎓 Simple Explanation of Computer Vision

**What is it?**  
Computer vision means the computer can "see" and understand what's in a video, just like humans can.

**How does it work in HireSIGHT?**

1. **Camera captures video** → Candidate's face during interview
2. **MediaPipe analyzes each frame** → Finds 468 points on the face
3. **System tracks movements** → Sees where eyes look, how head moves
4. **Scores are calculated** → Based on professional behaviors

**What does it detect?**
- Where you're looking (eye contact)
- How much you move (fidgeting)
- Your facial expressions (engagement)
- Your head position (posture)
- If you're paying attention (face visible)

**Why is this useful?**
- Removes human bias in evaluation
- Provides objective measurements
- Catches things humans might miss
- Consistent evaluation for all candidates

---

## ✅ System Status

**All Features Complete**:
- ✅ Job posting and management
- ✅ Resume upload and skill matching
- ✅ Live video interviews
- ✅ Technical knowledge assessment
- ✅ Voice and speech analysis
- ✅ Behavioral analysis (computer vision)
- ✅ Coding challenges
- ✅ Automatic report generation
- ✅ Admin dashboard for candidate review
- ✅ Complete privacy controls

**Ready for Use**: YES ✅

---

## 📞 Quick Reference

### For Admins:
1. Login to admin dashboard
2. Create job post with requirements
3. Wait for candidates to apply
4. Review candidate reports
5. Make hiring decision

### For Candidates:
1. Browse available jobs
2. Upload resume
3. If qualified, take interview
4. Wait for response
5. Get hired! 🎉

### For Developers:
- Backend: `backend/app/`
- Frontend: `frontend/src/`
- Database: MongoDB
- Start: `uvicorn app.main:app` (backend), `npm run dev` (frontend)

---

*This guide explains HireSIGHT in simple terms. The system uses advanced AI to make hiring fair, fast, and data-driven.*
