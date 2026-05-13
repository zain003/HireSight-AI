# Install languages used by /interview/coding/run (Windows + winget).
# Run PowerShell as Administrator if winget refuses installs.
# After install, restart the terminal and the FastAPI server so PATH updates.

$ErrorActionPreference = "Stop"

function Install-WingetId {
    param([string]$Id, [string]$Label)
    Write-Host "Installing $Label ($Id)..."
    winget install --id $Id --accept-package-agreements --accept-source-agreements -e --silent
}

try {
    Install-WingetId "Python.Python.3.12" "Python 3.12"
} catch {
    Write-Warning "Python install failed: $_"
}

try {
    Install-WingetId "OpenJS.NodeJS.LTS" "Node.js LTS"
} catch {
    Write-Warning "Node.js install failed: $_"
}

try {
    Install-WingetId "EclipseAdoptium.Temurin.17.JDK" "JDK 17 (Temurin)"
} catch {
    Write-Warning "JDK install failed: $_"
}

try {
    Install-WingetId "LLVM.LLVM" "LLVM (clang/clang++ for C/C++)"
} catch {
    Write-Warning "LLVM install failed: $_"
}

Write-Host ""
Write-Host "Done. If Python still fails with 'Microsoft Store', disable App execution aliases:"
Write-Host "  Settings -> Apps -> Advanced app settings -> App execution aliases -> turn OFF python.exe"
Write-Host "Optionally set in backend/.env:"
Write-Host "  CODE_RUN_PYTHON=C:\Path\to\python.exe"
Write-Host "Restart your IDE/terminal so PATH changes apply."
