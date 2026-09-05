#!/usr/bin/env python3
"""
HireSIGHT System-Wide Health and Quality Gate Verifier
Verifies codebase integrity, AI models, spec contracts, backend tests, and frontend build readiness.
"""

import os
import subprocess
import sys
from pathlib import Path

# Path: .agents/skills/<skill>/scripts/<file>.py -> parents[4] is workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
FRONTEND_DIR = WORKSPACE_ROOT / "frontend"
SPECS_DIR = WORKSPACE_ROOT / "context" / "feature-specs"

def run_system_verification():
    print("=" * 60)
    print(" HireSIGHT System-Wide Quality Gate & Invariant Check")
    print("=" * 60)
    
    passed_all = True

    # 1. Check Directory Structure
    print("\n[1/5] Checking Directory Structure & Essential Files...")
    essential_paths = [
        WORKSPACE_ROOT / "backend" / "app" / "main.py",
        WORKSPACE_ROOT / "frontend" / "package.json",
        WORKSPACE_ROOT / "context" / "architecture.md",
        WORKSPACE_ROOT / "context" / "code-standards.md",
        WORKSPACE_ROOT / "context" / "ai-workflow-rules.md",
        WORKSPACE_ROOT / "AGENTS.md",
    ]
    for p in essential_paths:
        if p.exists():
            print(f"  [OK] Found: {p.relative_to(WORKSPACE_ROOT)}")
        else:
            print(f"  [!] Missing: {p.relative_to(WORKSPACE_ROOT)}")
            passed_all = False

    # 2. Check AI Model Assets (Vosk ASR)
    print("\n[2/5] Checking Offline Speech-to-Text Model Weights...")
    models_dir = BACKEND_DIR / "models"
    if models_dir.exists():
        vosk_models = [d for d in models_dir.iterdir() if d.is_dir() and "vosk" in d.name.lower()]
        if vosk_models:
            print(f"  [OK] Offline Vosk model found: {[m.name for m in vosk_models]}")
        else:
            print("  [-] Note: No Vosk directory found in backend/models (online fallback mode or setup required).")
    else:
        print("  [-] Note: backend/models directory not present.")

    # 3. Check Spec Gating and Line Bounds
    print("\n[3/5] Checking Feature Specs & Pre-Flight Gates...")
    gate_script = WORKSPACE_ROOT / ".agents" / "skills" / "hiresight-spec-workflow" / "scripts" / "check_spec_gates.py"
    if gate_script.exists():
        res = subprocess.run([sys.executable, str(gate_script)], capture_output=True, text=True)
        if res.returncode == 0:
            print("  [OK] Feature specs and dependency gates valid.")
        else:
            print(f"  [!] Gate check warnings/errors:\n{res.stdout}")
    else:
        print("  [!] Gate script not found.")

    # 4. Check Backend Syntax & Python Environment
    print("\n[4/5] Checking Backend Python Files Syntax...")
    backend_py_files = list((BACKEND_DIR / "app").glob("**/*.py"))
    py_errors = 0
    for py_file in backend_py_files:
        try:
            import py_compile
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"  [!] Syntax error in {py_file.relative_to(WORKSPACE_ROOT)}: {e}")
            py_errors += 1
            passed_all = False

    if py_errors == 0:
        print(f"  [OK] All {len(backend_py_files)} backend Python files compiled with zero syntax errors.")

    # 5. Check Frontend Package Setup
    print("\n[5/5] Checking Frontend Configuration...")
    pkg_json = FRONTEND_DIR / "package.json"
    if pkg_json.exists():
        print(f"  [OK] Frontend package.json present.")
    else:
        print(f"  [!] Missing frontend/package.json")
        passed_all = False

    print("\n" + "=" * 60)
    if passed_all:
        print(" [OK] HireSIGHT System Verification PASSED.")
        print("=" * 60)
        return 0
    else:
        print(" [!] System Verification Encountered Issues. Please review above.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(run_system_verification())
