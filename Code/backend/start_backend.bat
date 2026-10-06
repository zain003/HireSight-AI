@echo off
REM HireSIGHT AI Backend Startup Script
REM Always enforces backend/.venv (Python 3.10.11 ML environment)

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    SET "PYTHON_EXE=.venv\Scripts\python.exe"
) ELSE IF EXIST "venv\Scripts\python.exe" (
    SET "PYTHON_EXE=venv\Scripts\python.exe"
) ELSE (
    echo [ERROR] No virtual environment found at .venv\Scripts\python.exe!
    pause
    exit /b 1
)

echo [HireSIGHT] Starting Backend using Python: %PYTHON_EXE%
"%PYTHON_EXE%" -c "import cv2, mediapipe as mp; print('[OK] ML Engine Ready: OpenCV', cv2.__version__, '| MediaPipe', mp.__version__)"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Critical ML libraries (OpenCV / MediaPipe) failed to load! Check .venv.
    pause
    exit /b 1
)

echo [HireSIGHT] Launching FastAPI Dev Server on http://0.0.0.0:8000 ...
"%PYTHON_EXE%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
