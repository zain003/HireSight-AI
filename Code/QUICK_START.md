# 🚀 Quick Start Guide - HireSIGHT AI

## Prerequisites
- Docker Desktop installed and running
- Git (for cloning)

---

## 🎯 Start Everything (Recommended)

### Windows
```bash
# Double-click or run:
start_all.bat
```

### Linux/Mac
```bash
docker-compose up --build -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔧 Development Mode

### Backend Only
```bash
cd backend
docker-compose up --build
```

### Frontend Only
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

### Test Backend
```bash
cd backend
python test_all.py
```

### Test with Postman
1. Register: POST `http://localhost:8000/auth/register`
2. Login: POST `http://localhost:8000/auth/login`
3. Upload CV: POST `http://localhost:8000/resume/parse` (with Bearer token)

---

## 📦 What's Running?

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 8000 | http://localhost:8000 |
| Swagger | 8000 | http://localhost:8000/docs |
| Database | 5432 | localhost:5432 |

---

## 🛑 Stop Services

```bash
docker-compose down
```

---

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

---

## ⚡ Quick Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild everything
docker-compose up --build

# Stop and remove volumes (reset database)
docker-compose down -v
```

---

## 🎨 Frontend Features

- ✅ User Registration & Login
- ✅ Resume Upload (PDF/DOCX)
- ✅ AI Skill Extraction
- ✅ Profile Dashboard
- 🚧 Interview Module (Coming Soon)

---

## 🔐 Default Test User

After starting, register a new user or use:
- Create via: http://localhost:3000/register
- Login via: http://localhost:3000/login

---

## 🐛 Troubleshooting

### Docker not running?
```bash
# Check Docker status
docker --version
docker ps
```

### Port already in use?
```bash
# Stop conflicting services
docker-compose down
```

### Database issues?
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

---

## 📞 Need Help?

- Check [README.md](README.md)
- Check [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)
- Open issue on GitHub
