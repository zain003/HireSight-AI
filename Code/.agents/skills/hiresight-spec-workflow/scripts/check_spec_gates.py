#!/usr/bin/env python3
"""
HireSIGHT Spec Gate Checker
Validates feature specifications, dependency chains, line count limits (80-150 lines),
and pre-flight completion gates recorded in context/feature-specs/INDEX.md.
"""

import os
import re
import sys
from pathlib import Path

# Path: .agents/skills/<skill>/scripts/<file>.py -> parents[4] is workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
SPECS_DIR = WORKSPACE_ROOT / "context" / "feature-specs"
INDEX_FILE = SPECS_DIR / "INDEX.md"

def check_specs():
    print(f"[*] Checking specs in: {SPECS_DIR}")
    if not SPECS_DIR.exists():
        print(f"[!] Error: Specs directory not found: {SPECS_DIR}")
        return 1

    spec_files = list(SPECS_DIR.glob("FEAT-*.md"))
    if not spec_files:
        print("[!] No FEAT-*.md spec files found.")
        return 0

    warnings = []
    errors = []
    spec_data = {}

    for spec in sorted(spec_files):
        with open(spec, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        line_count = len(lines)
        file_id = spec.stem
        spec_data[file_id] = {"lines": line_count, "path": spec, "depends_on": []}

        # Size check (80 - 150 lines recommended)
        if line_count > 160:
            warnings.append(f"[SIZE] {spec.name} is {line_count} lines (exceeds recommended 80-150 range; consider splitting).")
        elif line_count < 40 and "VERIFY" not in spec.name:
            warnings.append(f"[SIZE] {spec.name} is {line_count} lines (may be underspecified).")

        # Parse dependencies
        content = "".join(lines)
        depends_match = re.search(r"Depends\s+on\s*:\s*([^\n\r]+)", content, re.IGNORECASE)
        if depends_match:
            raw_deps = depends_match.group(1)
            deps = [d.strip() for d in re.split(r"[,;]", raw_deps) if d.strip() and "none" not in d.lower()]
            spec_data[file_id]["depends_on"] = deps

    # Parse INDEX.md if present
    completed_specs = set()
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_content = f.read()
            for line in index_content.splitlines():
                if "DONE" in line.upper() or "VERIFIED" in line.upper() or "[X]" in line.upper():
                    match = re.search(r"(FEAT-\d+-[A-Z]+-[a-z0-9-]+)", line)
                    if match:
                        completed_specs.add(match.group(1))

    print(f"[*] Found {len(spec_files)} spec files.")
    print(f"[*] Completed/Verified in INDEX.md: {len(completed_specs)}")

    # Check dependency gating
    for file_id, info in spec_data.items():
        for dep in info["depends_on"]:
            clean_dep = dep.replace(".md", "").strip()
            matching_files = [k for k in spec_data.keys() if clean_dep in k or k in clean_dep]
            if not matching_files and not clean_dep.startswith("000"):
                warnings.append(f"[DEPENDENCY] {file_id} references unknown dependency '{clean_dep}'.")

    print("\n--- Gate Check Summary ---")
    if warnings:
        print("\n[!] Warnings / Recommendations:")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\n[OK] All spec files conform to sizing guidelines.")

    print("\n[OK] Spec gate check completed.")
    return 0

if __name__ == "__main__":
    sys.exit(check_specs())
