"""Direct test runner for Role & Competency Mapping (FEAT-001-BE)."""

import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_role_mapping import (
    test_infer_seniority_entry,
    test_infer_seniority_mid,
    test_infer_seniority_senior,
    test_infer_seniority_lead,
    test_all_seven_standard_roles_present,
    test_role_competency_weights_sum_to_one,
    test_role_metadata_complete,
    test_map_profile_to_role_fit_empty,
    test_map_profile_to_role_fit_matching,
    test_get_roles_config_structure,
    test_get_roles_endpoint_returns_200,
    test_post_role_fit_endpoint,
)

def run_all():
    print("[*] Running Role & Competency Mapping Tests (FEAT-001-BE)...")
    tests = [
        ("test_infer_seniority_entry", test_infer_seniority_entry),
        ("test_infer_seniority_mid", test_infer_seniority_mid),
        ("test_infer_seniority_senior", test_infer_seniority_senior),
        ("test_infer_seniority_lead", test_infer_seniority_lead),
        ("test_all_seven_standard_roles_present", test_all_seven_standard_roles_present),
        ("test_role_competency_weights_sum_to_one", test_role_competency_weights_sum_to_one),
        ("test_role_metadata_complete", test_role_metadata_complete),
        ("test_map_profile_to_role_fit_empty", test_map_profile_to_role_fit_empty),
        ("test_map_profile_to_role_fit_matching", test_map_profile_to_role_fit_matching),
        ("test_get_roles_config_structure", test_get_roles_config_structure),
        ("test_get_roles_endpoint_returns_200", test_get_roles_endpoint_returns_200),
        ("test_post_role_fit_endpoint", test_post_role_fit_endpoint),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [OK] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    print(f"\n[*] Results: {passed}/{len(tests)} tests passed.")
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(run_all())
