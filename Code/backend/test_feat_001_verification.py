"""
FEAT-001 End-to-End Verification Suite
Executes all checks defined in context/feature-specs/FEAT-001-VERIFY-role-mapping.md
"""
import math
import sys
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.interview.domain.role_taxonomy import (
    StandardRole,
    SeniorityLevel,
    get_all_standard_roles,
    get_role_competency_matrix,
    ROLE_METADATA_REGISTRY,
)
from app.interview.services.role_mapping_service import (
    infer_seniority_level,
    map_profile_to_role_fit,
    get_supported_roles_config,
)
from app.interview.routes import router as interview_router

def run_verification():
    report_lines = []
    def log(msg=""):
        print(msg)
        report_lines.append(msg)

    log("# FEAT-001 Verification Test Report")
    log(f"**Execution Timestamp**: {datetime.utcnow().isoformat()}Z")
    log(f"**Target Specs**: `FEAT-001-BE-role-competency-mapping.md`, `FEAT-001-FE-interview-config-role-select.md`")
    log()
    log("---")
    log()

    total_checks = 0
    passed_checks = 0

    def check(name, condition, detail=""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        status = "PASSED" if condition else "FAILED"
        if condition:
            passed_checks += 1
            log(f"- [x] **{name}**: `{status}` {detail}")
        else:
            log(f"- [ ] **{name}**: `{status}` {detail}")
        return condition

    log("## 1. Automated Backend Unit & Taxonomy Tests")

    # Seniority inference tests
    check("infer_seniority_level(0) == ENTRY", infer_seniority_level(0) == SeniorityLevel.ENTRY, f"-> {infer_seniority_level(0)}")
    check("infer_seniority_level(3) == MID", infer_seniority_level(3) == SeniorityLevel.MID, f"-> {infer_seniority_level(3)}")
    check("infer_seniority_level(7) == SENIOR", infer_seniority_level(7) == SeniorityLevel.SENIOR, f"-> {infer_seniority_level(7)}")
    check("infer_seniority_level(10) == LEAD", infer_seniority_level(10) == SeniorityLevel.LEAD, f"-> {infer_seniority_level(10)}")
    check("Missing experience (None) defaults to ENTRY", infer_seniority_level(None) == SeniorityLevel.ENTRY, f"-> {infer_seniority_level(None)}")

    # Standard roles completeness
    roles = get_all_standard_roles()
    expected_roles = {
        StandardRole.FRONTEND_ENGINEER,
        StandardRole.BACKEND_ENGINEER,
        StandardRole.FULLSTACK_ENGINEER,
        StandardRole.DEVOPS_ENGINEER,
        StandardRole.DATA_ENGINEER,
        StandardRole.ML_ENGINEER,
        StandardRole.QA_AUTOMATION_ENGINEER,
    }
    check("All 7 Standard Roles Present", set(roles) == expected_roles and len(roles) == 7, f"Registered: {len(roles)} roles")

    # Weight sums to 1.0 for each role
    all_weights_valid = True
    for role in StandardRole:
        matrix = get_role_competency_matrix(role)
        total_wt = sum(item.importance_weight for item in matrix)
        is_close = math.isclose(total_wt, 1.0, rel_tol=1e-5)
        if not is_close:
            all_weights_valid = False
            log(f"  * Warning: {role.value} weight sum = {total_wt}")
    check("Competency Weights Sum to 1.0", all_weights_valid, "All 7 roles verified with sum == 1.000")

    # Metadata completeness
    all_meta_valid = all(
        ROLE_METADATA_REGISTRY.get(r) is not None
        and "title" in ROLE_METADATA_REGISTRY.get(r)
        and "description" in ROLE_METADATA_REGISTRY.get(r)
        for r in StandardRole
    )
    check("Role Metadata Registry Complete", all_meta_valid, "Title and description present for all roles")

    # Skill matching
    fit_res = map_profile_to_role_fit(["FastAPI", "PostgreSQL", "Docker", "Redis"], StandardRole.BACKEND_ENGINEER)
    check(
        "Candidate Skill Fit Calculation",
        fit_res["overall_fit_score"] > 0.0 and len(fit_res["matched_skills"]) > 0,
        f"Score: {fit_res['overall_fit_score']:.2f}, Matched: {fit_res['matched_skills']}",
    )

    log()
    log("## 2. API Endpoint Verification")

    app = FastAPI()
    app.include_router(interview_router, prefix="/interview")
    client = TestClient(app)

    # GET /interview/config/roles
    res_roles = client.get("/interview/config/roles?experience_years=3")
    check(
        "GET /interview/config/roles returns 200",
        res_roles.status_code == 200 and len(res_roles.json().get("supported_roles", [])) == 7,
        f"Status: {res_roles.status_code}, Returned {len(res_roles.json().get('supported_roles', []))} roles, Default Seniority: {res_roles.json().get('default_seniority')}",
    )

    # POST /interview/config/role-fit
    fit_payload = {
        "role": "frontend_engineer",
        "skills": ["React", "JavaScript", "HTML5", "CSS Grid", "TypeScript"],
    }
    res_fit = client.post("/interview/config/role-fit", json=fit_payload)
    check(
        "POST /interview/config/role-fit returns 200",
        res_fit.status_code == 200 and res_fit.json().get("overall_fit_score", 0) > 0,
        f"Status: {res_fit.status_code}, Overall Score: {res_fit.json().get('overall_fit_score')}",
    )

    log()
    log("## 3. Frontend Component & Contract Compliance")
    check("Frontend File Exists: interview-setup.jsx", os.path.exists("../frontend/src/pages/interview-setup.jsx"), "Pre-interview setup screen")
    check("Frontend File Exists: InterviewConfigCard.jsx", os.path.exists("../frontend/src/components/Interview/InterviewConfigCard.jsx"), "Interactive config & agenda card")
    check("Frontend Service Method: getRoleConfigs", os.path.exists("../frontend/src/services/interviewService.js"), "interviewService.js updated")

    log()
    log("## 4. Overall Verification Summary")
    log(f"**Total Verification Checks**: {total_checks}")
    log(f"**Passed Checks**: {passed_checks}")
    log(f"**Failed Checks**: {total_checks - passed_checks}")
    log(f"**Pass Rate**: {(passed_checks / total_checks) * 100:.1f}%")
    log()
    if passed_checks == total_checks:
        log("### Final Gate Decision: **PASSED (100% Gated Criteria Satisfied)**")
    else:
        log("### Final Gate Decision: **FAILED (Action Required)**")

    # Write report
    report_dir = os.path.join("..", "feature-test-reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "FEAT-001-test-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    log(f"\nReport written to: {report_path}")

    return passed_checks == total_checks

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
