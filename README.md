# 🎯 HireSIGHT AI - Interview Platform

AI-Powered Interview Preparation Platform with Resume Analysis and Personalized Question Generation

## 📁 Project Structure (Monorepo - Microservices Ready)

```
FYP-Project/
│
├── backend/                          # Backend API (FastAPI)
│   ├── app/
│   │   ├── auth/                     # Authentication Module
│   │   ├── resume/                   # Resume Parsing Module
│   │   ├── ai/                       # AI/ML Services (SBERT)
│   │   ├── core/                     # Shared Utilities
│   │   └── db/                       # Database Layer
│   ├── docker-compose.yml            # Backend-only compose
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                         # Frontend (Next.js + React)
│   ├── src/
│   │   ├── components/               # UI Components
│   │   │   ├── Auth/                 # Login, Register
│   │   │   ├── Resume/               # CV Upload, Profile
│   │   │   └── Interview/            # Interview UI (Module 2)
│   │   ├── pages/                    # Next.js Pages
│   │   ├── services/                 # API Services
│   │   ├── store/                    # State Management
│   │   └── utils/                    # Helper Functions
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml                # Root compose (All services)
└── README.md
```

---

## 🏗️ Architecture

### **Modular Monolith (Microservices Ready)**

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                │
│                    Port 3000                        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────┐
│              Backend API (FastAPI)                  │
│                    Port 8000                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │   Auth   │  │  Resume  │  │    AI    │         │
│  │  Module  │  │  Module  │  │  Module  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└──────────────────────┬──────────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────────┐
│            PostgreSQL Database                      │
│                    Port 5432                        │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### **Option 1: Run Everything with Docker (Recommended)**

```bash
# Clone repository
git clone https://github.com/zain003/Final-Year-Project.git
cd Final-Year-Project

# Start all services (backend + frontend + database)
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### **Option 2: Run Backend Only**

```bash
cd backend

# Using Docker
docker-compose up --build

# OR using Python directly
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Access:
# - API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
```

### **Option 3: Run Frontend Only (Development)**

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start development server
npm run dev

# Access: http://localhost:3000
```

---

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js React Application |
| Backend API | 8000 | FastAPI REST API |
| PostgreSQL | 5432 | Database |
| Swagger UI | 8000/docs | API Documentation |

---

## 🔧 Technology Stack

### **Backend**
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14
- **ORM**: SQLAlchemy
- **Authentication**: JWT (python-jose)
- **AI/ML**: 
  - Sentence-BERT (all-MiniLM-L6-v2)
  - spaCy NLP
  - PyTorch
- **Resume Parsing**: 
  - pdfplumber (PDF)
  - python-docx (DOCX)
  - pytesseract (OCR)

### **Frontend**
- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form

### **DevOps**
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Database Migrations**: Alembic

---

## 📚 API Endpoints

### **Authentication**
```
POST   /auth/register          # Register new user
POST   /auth/login             # Login user
GET    /auth/me                # Get current user
GET    /auth/profile           # Get user profile
POST   /auth/profile           # Update profile
POST   /auth/start-session     # Start interview session
GET    /auth/sessions          # Get user sessions
```

### **Resume**
```
POST   /resume/parse           # Upload & parse resume
POST   /resume/extract-skills  # Extract skills from text
```

### **Health**
```
GET    /                       # Health check
GET    /health                 # Detailed health
```

---

## 🎨 Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Home page |
| Login | `/login` | User login |
| Register | `/register` | User registration |
| Dashboard | `/dashboard` | Main dashboard |
| Profile | `/profile` | User profile settings |
| Interview | `/interview/[id]` | Interview session (Module 2) |

---

## 🔐 Environment Variables

### **Backend (.env)**
```env
DATABASE_URL=postgresql://interview_user:interview_pass@db:5432/interview_platform
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760
SBERT_MODEL=all-MiniLM-L6-v2
CORS_ORIGINS=http://localhost:3000
```

### **Frontend (.env)**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=HireSIGHT AI
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
```

---

## 🧪 Testing

### **Backend Tests**
```bash
cd backend

# Run all tests
python test_all.py

# Or run complete integration test
python complete_test.py
```

### **Frontend Tests**
```bash
cd frontend
npm test
```

---

## 📖 Module Documentation

### **Module 1: Resume Analysis (✅ Complete)**
- PDF/DOCX/Image parsing
- AI skill extraction (SBERT + keywords)
- Experience detection
- Domain classification
- Profile auto-creation

### **Module 2: Interview Generation (🚧 In Progress)**
- Personalized question generation
- Real-time interview sessions
- AI-powered feedback
- Performance analytics

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild services
docker-compose up --build

# Remove volumes (reset database)
docker-compose down -v
```

---

## 📝 Development Workflow

1. **Backend Development**
   ```bash
   cd backend
   # Make changes to app/
   # Backend auto-reloads with volume mount
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm run dev
   # Make changes to src/
   # Hot reload enabled
   ```

3. **Database Migrations**
   ```bash
   cd backend
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

---

## 🎯 Features

### **Current (Module 1)**
- ✅ User registration & authentication
- ✅ JWT-based security
- ✅ Resume upload (PDF/DOCX)
- ✅ AI skill extraction (SBERT)
- ✅ Experience detection
- ✅ Domain classification
- ✅ Profile management
- ✅ Responsive UI

### **Upcoming (Module 2)**
- 🚧 Interview question generation
- 🚧 Real-time interview sessions
- 🚧 AI answer evaluation
- 🚧 Performance analytics
- 🚧 Interview history

---

## 👥 Team

- **Zain Ali Khan** - Full Stack Development

---

## 📄 License

This project is part of a Final Year Project (FYP).

---

## 🔗 Links

- **GitHub**: https://github.com/zain003/Final-Year-Project
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

---

## 📞 Support

For issues or questions, please open an issue on GitHub.
