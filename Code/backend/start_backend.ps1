# HireSIGHT AI Backend Startup Script (PowerShell)
# Always enforces backend/.venv (Python 3.10.11 ML environment)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = Join-Path $ScriptDir "venv\Scripts\python.exe"
}

if (-not (Test-Path $PythonExe)) {
    Write-Error "[HireSIGHT] Cannot find Python virtual environment at .venv or venv!"
    exit 1
}

Write-Host "[HireSIGHT] Verifying ML dependencies using: $PythonExe" -ForegroundColor Cyan
& $PythonExe -c "import cv2, mediapipe as mp; print('[OK] ML Engine Ready: OpenCV', cv2.__version__, '| MediaPipe', mp.__version__)"

if ($LASTEXITCODE -ne 0) {
    Write-Error "[HireSIGHT] OpenCV or MediaPipe is missing in the virtual environment!"
    exit 1
}

Write-Host "[HireSIGHT] Launching FastAPI Dev Server on http://0.0.0.0:8000 ..." -ForegroundColor Green
& $PythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
