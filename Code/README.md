# 🎯 HireSIGHT - AI-Powered Interview & Recruitment Platform

An intelligent interview platform that automatically evaluates candidates across multiple dimensions using AI, computer vision, and voice analysis.

---

## 📚 **[→ READ THE COMPLETE SYSTEM GUIDE ←](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)**

**Everything you need to know about HireSIGHT:**
- ✅ Complete pipeline from job posting to hiring decision
- ✅ How each evaluation module works (technical, voice, behavioral, coding)
- ✅ What gets scored during interviews and why
- ✅ How computer vision and voice analysis work in simple terms
- ✅ All technologies explained (MediaPipe, OpenSMILE, Vosk, etc.)
- ✅ Step-by-step flow with examples

👉 **[CLICK HERE TO READ THE COMPLETE GUIDE](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)** 👈

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB
- FFmpeg (for audio processing)

### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Download required AI models (Vosk for speech recognition)
python setup_enhanced_evaluation.py

# Start backend server
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000  
API Docs: http://localhost:8000/docs

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend runs at: http://localhost:3000

### MongoDB Setup
```bash
# Start MongoDB (if not already running)
mongod --dbpath /path/to/data
```

---

## 📊 What Does HireSIGHT Do?

HireSIGHT conducts AI-powered video interviews and evaluates candidates across **4 dimensions**:

### 1. **Technical Knowledge** (35% of score)
- Evaluates answer quality using LLM (AI)
- Measures depth of technical knowledge
- Asks follow-up questions for clarity

**Technologies**: Vosk (speech-to-text), LLM evaluation

### 2. **Communication Skills** (25% of score)
- Analyzes voice confidence, clarity, and tone
- Measures speech rate and pause patterns
- Detects pitch variance (not monotone)

**Technologies**: OpenSMILE (acoustic features), Librosa (audio processing)

### 3. **Behavioral Analysis** (20% of score)
- Tracks eye contact using iris detection
- Measures posture and head stability
- Detects fidgeting and attention span
- Analyzes facial engagement

**Technologies**: MediaPipe (468 facial landmarks), OpenCV (computer vision)

### 4. **Coding Assessment** (20% of score)
- Tests code with automated test cases
- Evaluates correctness and quality
- Measures problem-solving ability

**Technologies**: Code execution sandbox

---

## 🎯 Key Features

✅ **Automated Candidate Evaluation** - Multi-dimensional AI analysis  
✅ **Computer Vision** - 468-point facial landmark detection  
✅ **Voice Analysis** - Acoustic feature extraction (88 features)  
✅ **Speech Recognition** - Offline, real-time (Vosk)  
✅ **Coding Challenges** - Automated test case validation  
✅ **Comprehensive Reports** - Hidden from candidates, visible to admins  
✅ **Admin Dashboard** - Manage jobs, view candidates, access reports  
✅ **Resume Skill Matching** - AI-powered resume parsing  
✅ **Red Flag Detection** - 6 behavioral flags, vocal issues, technical gaps  

---

## 📁 Project Structure

```
├── backend/                           # Python/FastAPI backend
│   ├── app/
│   │   ├── interview/                 # Interview system
│   │   │   ├── services/
│   │   │   │   ├── behavioral_analysis.py    # Computer vision 👁️
│   │   │   │   ├── vocal_analysis.py         # Voice analysis 🎤
│   │   │   │   ├── stt_service.py            # Speech-to-text
│   │   │   │   ├── llm_service.py            # Answer evaluation
│   │   │   │   ├── code_execution.py         # Code runner
│   │   │   │   └── recruiter_report.py       # Report generation
│   │   │   ├── models.py              # Database models
│   │   │   └── routes.py              # API endpoints
│   │   ├── auth/                      # Authentication & job posts
│   │   ├── resume/                    # Resume parsing & skill extraction
│   │   ├── core/                      # Security & config
│   │   └── db/                        # MongoDB connection
│   ├── models/                        # AI models (Vosk)
│   ├── requirements.txt               # Python dependencies
│   └── setup_enhanced_evaluation.py   # Setup script
│
├── frontend/                          # Next.js/React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── admin-dashboard.jsx    # Admin control panel
│   │   │   └── user-dashboard.jsx     # Candidate interface
│   │   └── components/
│   │       ├── Admin/
│   │       │   └── JobCandidatesList.jsx      # Candidates list
│   │       └── Interview/
│   │           ├── RecruiterReportViewer.jsx  # Report viewer
│   │           └── MetricsDashboard.jsx       # Real-time metrics
│   └── package.json
│
└── HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md  # 📖 Complete documentation
```

---

## 🛠️ Technologies Used

### AI & Machine Learning
| Technology | Purpose |
|------------|---------|
| **MediaPipe** | 468-point facial landmark detection for behavioral analysis |
| **OpenSMILE** | Extract 88 acoustic features from voice |
| **Vosk** | Offline speech-to-text conversion (no internet needed) |
| **Librosa** | Audio signal processing and pitch analysis |
| **LLM** | Technical answer evaluation (OpenAI/Groq) |
| **BERT NER** | Resume skill extraction |

### Backend
- **FastAPI** - Modern web framework
- **MongoDB** - NoSQL database
- **Beanie** - MongoDB object-document mapper
- **JWT** - Authentication

### Frontend
- **Next.js** - React framework
- **Tailwind CSS** - Styling
- **Lucide Icons** - UI icons

---

## 📊 Interview Scoring Example

```
Example Candidate:

Technical:      85/100 × 35% = 29.75
Communication:  78/100 × 25% = 19.50
Behavioral:     82/100 × 20% = 16.40
Coding:         90/100 × 20% = 18.00
────────────────────────────────
Overall Score:  83.65/100

Recommendation: "Hire" ✅
Confidence: High
```

---

## 🚨 Red Flags Detected

### Behavioral (Computer Vision)
- Poor eye contact - looked away frequently
- Unstable posture - excessive head movements
- Low facial engagement - minimal expression
- High fidgeting - nervous behavior
- Attention issues - face not consistently visible

### Communication (Voice Analysis)
- Low vocal confidence - hesitant speech
- Poor speech clarity - mumbling detected
- Monotone delivery - no voice variation
- Rapid speech - possible anxiety

### Technical
- Unable to answer basic questions
- Excessive follow-ups needed
- Many questions skipped

---

## 🔒 Privacy & Security

**Reports are SECRET from candidates:**
- ❌ Candidates CANNOT see their scores
- ❌ Candidates CANNOT see reports
- ❌ Candidates CANNOT see hiring recommendations

**Only admins can access:**
- ✅ Full interview reports
- ✅ All scores and metrics
- ✅ Hiring recommendations
- ✅ Behavioral analysis results

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)** | 📖 Main guide - Everything explained simply |
| `backend/QUICK_START_ENHANCED.md` | Setup instructions for enhanced system |
| `backend/TESTING_CHECKLIST.md` | Testing guide and checklist |
| `COMPLETE_PIPELINE_FLOW.tex` | LaTeX pipeline documentation (30+ pages) |

---

## 🎓 How Computer Vision Works (Simple Explanation)

1. **Camera captures video** → Your face during interview
2. **MediaPipe finds 468 points** → On your face (eyes, nose, mouth, etc.)
3. **System tracks movements** → Where you look, how you move
4. **Scores calculated** → Based on professional behaviors

**What it detects:**
- Where you're looking (eye contact)
- How much you move (fidgeting)
- Your facial expressions (engagement)
- Your head position (posture)
- If you're paying attention (face visible)

---

## 🔗 API Endpoints

### Authentication & Jobs
```
POST   /auth/register                              # Register user
POST   /auth/login                                 # Login user
POST   /auth/admin/job-post                        # Create job post
GET    /auth/admin/job-posts                       # List all jobs
GET    /auth/admin/job-posts/{id}/candidates       # View candidates
GET    /auth/admin/job-posts/{id}/candidates/{session_id}/report  # View report
```

### Interview
```
POST   /interview/start                            # Start interview
POST   /interview/live/{session_id}/submit-answer  # Submit answer
POST   /interview/live/{session_id}/submit-coding-result  # Submit code
GET    /interview/{session_id}/report              # Get report (admin only)
```

### Resume
```
POST   /resume/parse                               # Upload & parse resume
POST   /resume/extract-skills                      # Extract skills
```

---

## ✅ System Status

**ALL FEATURES COMPLETE:**
- ✅ Job posting and management
- ✅ Resume upload and AI skill matching
- ✅ Live video interviews with camera
- ✅ Technical knowledge assessment (LLM)
- ✅ Voice and speech analysis (OpenSMILE, Vosk)
- ✅ Behavioral analysis (MediaPipe computer vision)
- ✅ Coding challenges with test cases
- ✅ Automatic report generation
- ✅ Admin dashboard with candidate management
- ✅ Complete privacy controls

**Ready for Production**: YES ✅

---

## 🎯 For Different Users

### **For Admins/Recruiters:**
1. Login to admin dashboard
2. Post job with requirements
3. Wait for candidates to apply
4. Review candidate reports
5. Make data-driven hiring decisions

### **For Candidates:**
1. Browse available jobs
2. Upload your resume
3. If qualified, take the interview
4. Perform your best across all dimensions
5. Get hired! 🎉

### **For Developers:**
1. Read [HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)
2. Check `backend/app/` for services
3. Check `frontend/src/` for UI components
4. Run `python setup_enhanced_evaluation.py` first

---

## 📞 Quick Reference

**Backend Port**: 8000  
**Frontend Port**: 3000  
**Database**: MongoDB on localhost:27017  
**API Docs**: http://localhost:8000/docs  

**Main Documentation**: [HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)

---

## 👥 Credits

Built with advanced AI technologies:
- Google MediaPipe for computer vision
- OpenSMILE for voice analysis
- Vosk for speech recognition
- FastAPI for high-performance backend
- Next.js for modern frontend

---

**🚀 Ready to revolutionize hiring with AI!**

*For complete system understanding, read: [HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md](HIRESIGHT_COMPLETE_SYSTEM_GUIDE.md)*
