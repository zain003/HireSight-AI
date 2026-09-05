#!/usr/bin/env python3
"""
HireSIGHT Backend Test Runner
Discovers and executes backend unit tests, evaluation tests, and validation scripts.
"""

import os
import subprocess
import sys
from pathlib import Path

# Path: .agents/skills/<skill>/scripts/<file>.py -> parents[4] is workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = WORKSPACE_ROOT / "backend"

def run_tests():
    print(f"[*] Backend Directory: {BACKEND_DIR}")
    if not BACKEND_DIR.exists():
        print(f"[!] Error: Backend directory not found: {BACKEND_DIR}")
        return 1

    # Check for virtual environment python
    venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    
    python_exe = str(venv_python) if venv_python.exists() else sys.executable
    print(f"[*] Using Python: {python_exe}")

    test_scripts = [
        "test_role_mapping.py",
        "validate_system.py",
        "test_enhanced_evaluation.py",
        "test_resume_validation.py",
        "test_skill_classification.py",
    ]

    all_passed = True
    for test_script in test_scripts:
        script_path = BACKEND_DIR / test_script
        if script_path.exists():
            print(f"\n[>] Running: {test_script} ...")
            result = subprocess.run([python_exe, str(script_path)], cwd=str(BACKEND_DIR))
            if result.returncode != 0:
                print(f"[!] {test_script} failed with return code {result.returncode}")
                all_passed = False
            else:
                print(f"[OK] {test_script} passed.")
        else:
            print(f"[-] Skipping {test_script} (not found).")

    print("\n--- Backend Test Execution Complete ---")
    if all_passed:
        print("[OK] All executed test suites passed successfully.")
        return 0
    else:
        print("[!] One or more backend tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
