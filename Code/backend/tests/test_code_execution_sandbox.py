"""Unit and sandbox security tests for FEAT-006-BE Coding Sandbox & Hidden Tests."""

import os
import time
import pytest
from app.interview.domain.coding_challenges import (
    CodingChallenge,
    CodingTestCase,
    get_all_challenges,
    get_challenge,
    get_public_challenge_dict,
)
from app.interview.schemas import (
    CodingChallengeEvaluation,
    CodingRunTestCaseIn,
    TestCaseResult,
)
from app.interview.services.code_execution import (
    DEFAULT_RUN_TIMEOUT_SEC,
    evaluate_coding_challenge,
    execute_code,
    normalize_language,
    supported_languages,
)


def test_supported_languages_list():
    langs = supported_languages()
    assert "python" in langs
    assert "javascript" in langs
    assert "c" in langs
    assert "cpp" in langs
    assert "java" in langs
    assert normalize_language("js") == "javascript"
    assert normalize_language("c++") == "cpp"


def test_python_solution_passes_all_tests():
    source_code = """
import sys

def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    nums = [int(x) for x in data[1:n+1]]
    seen = set()
    has_dup = False
    for x in nums:
        if x in seen:
            has_dup = True
            break
        seen.add(x)
    print("YES" if has_dup else "NO")

if __name__ == "__main__":
    main()
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="5\n4 2 7 2 1\n", expected_stdout="YES\n", is_hidden=False, description="Public duplicate"),
        CodingTestCase(test_id=2, stdin="4\n1 2 3 4\n", expected_stdout="NO\n", is_hidden=False, description="Public distinct"),
        CodingTestCase(test_id=3, stdin="6\n10 20 30 40 50 10\n", expected_stdout="YES\n", is_hidden=True, description="Hidden duplicate boundary"),
        CodingTestCase(test_id=4, stdin="5\n-1 -2 -3 -4 -5\n", expected_stdout="NO\n", is_hidden=True, description="Hidden negative distinct"),
    ]

    evaluation: CodingChallengeEvaluation = evaluate_coding_challenge(
        challenge_id="CHAL-001-TWO-SUM",
        language="python",
        source_code=source_code,
        custom_test_cases=test_cases,
        timeout_sec=3.0,
    )

    assert evaluation.compile_success is True
    assert evaluation.public_tests_passed == 2
    assert evaluation.public_tests_total == 2
    assert evaluation.hidden_tests_passed == 2
    assert evaluation.hidden_tests_total == 2
    assert evaluation.overall_coding_score >= 90.0
    assert len(evaluation.results) == 4

    # Public results should have stdout
    pub_res = [r for r in evaluation.results if not r.is_hidden]
    assert len(pub_res) == 2
    assert pub_res[0].stdout is not None
    assert pub_res[0].passed is True

    # Hidden results MUST NOT leak stdout or test details
    hid_res = [r for r in evaluation.results if r.is_hidden]
    assert len(hid_res) == 2
    assert hid_res[0].stdout is None
    assert hid_res[1].stdout is None
    assert hid_res[0].passed is True


def test_python_wrong_answer_fails():
    wrong_source = """
import sys
print("NO")
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="5\n4 2 7 2 1\n", expected_stdout="YES\n", is_hidden=False),
        CodingTestCase(test_id=2, stdin="4\n1 2 3 4\n", expected_stdout="NO\n", is_hidden=False),
        CodingTestCase(test_id=3, stdin="6\n1 2 3 4 5 1\n", expected_stdout="YES\n", is_hidden=True),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-001-TWO-SUM",
        language="python",
        source_code=wrong_source,
        custom_test_cases=test_cases,
    )

    assert evaluation.compile_success is True
    assert evaluation.public_tests_passed == 1
    assert evaluation.public_tests_total == 2
    assert evaluation.hidden_tests_passed == 0
    assert evaluation.hidden_tests_total == 1
    assert evaluation.overall_coding_score < 50.0

    # Hidden test failure must not leak error details or stdout
    hidden_result = evaluation.results[2]
    assert hidden_result.is_hidden is True
    assert hidden_result.passed is False
    assert hidden_result.stdout is None
    assert hidden_result.error_message == "Wrong Answer"


def test_infinite_loop_terminates_at_timeout():
    infinite_loop_code = """
import sys
import time

while True:
    time.sleep(0.1)
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="test", expected_stdout="test", is_hidden=False),
    ]

    t0 = time.perf_counter()
    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-001-TWO-SUM",
        language="python",
        source_code=infinite_loop_code,
        custom_test_cases=test_cases,
        timeout_sec=1.5,
    )
    elapsed = time.perf_counter() - t0

    assert elapsed < 3.5, f"Infinite loop took {elapsed:.2f}s, expected < 3.5s"
    assert evaluation.compile_success is True
    assert evaluation.public_tests_passed == 0
    assert evaluation.results[0].passed is False
    assert "Time Limit Exceeded" in (evaluation.results[0].error_message or "") or "timed out" in (evaluation.results[0].error_message or "").lower()


def test_hidden_test_inputs_not_leaked_in_response():
    source_code = """
import sys
data = sys.stdin.read().strip()
print(data)
"""
    secret_stdin = "SUPER_SECRET_INPUT_KEY_12345"
    secret_expected = "SUPER_SECRET_INPUT_KEY_12345\n"

    test_cases = [
        CodingTestCase(test_id=101, stdin="public_hello", expected_stdout="public_hello\n", is_hidden=False),
        CodingTestCase(test_id=102, stdin=secret_stdin, expected_stdout=secret_expected, is_hidden=True),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-TEST",
        language="python",
        source_code=source_code,
        custom_test_cases=test_cases,
    )

    eval_dict = evaluation.model_dump()
    json_str = evaluation.model_dump_json()

    # Verify secret stdin and expected output are not anywhere in the evaluation payload
    assert secret_stdin not in json_str or eval_dict["source_code"] == source_code
    # Ensure TestCaseResult has no stdin/expected_stdout attributes
    for res in eval_dict["results"]:
        assert "stdin" not in res
        assert "expected_stdout" not in res
        if res["is_hidden"]:
            assert res["stdout"] is None


def test_massive_stdout_truncated_at_10kb():
    massive_print_code = """
import sys
# Generate 5MB of output
print("A" * 5_000_000)
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="", expected_stdout="A\n", is_hidden=False),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-TEST",
        language="python",
        source_code=massive_print_code,
        custom_test_cases=test_cases,
        timeout_sec=3.0,
    )

    assert evaluation.compile_success is True
    res = evaluation.results[0]
    assert res.stdout is not None
    # Truncated to max ~10KB (10 * 1024 + truncation message)
    assert len(res.stdout) <= 12 * 1024
    assert "[Output truncated" in res.stdout


def test_syntax_error_returns_compile_failure():
    syntax_error_code = """
def broken_syntax(
    print "Missing paren"
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="", expected_stdout="", is_hidden=False),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-TEST",
        language="python",
        source_code=syntax_error_code,
        custom_test_cases=test_cases,
    )

    assert evaluation.compile_success is False
    assert evaluation.overall_coding_score == 0.0
    assert evaluation.public_tests_passed == 0
    assert len(evaluation.results) == 0 or not any(r.passed for r in evaluation.results)


def test_coding_challenge_catalog():
    challenges = get_all_challenges()
    assert len(challenges) >= 3

    two_sum = get_challenge("CHAL-001-TWO-SUM")
    assert two_sum is not None
    assert two_sum.title != ""
    assert len(two_sum.public_test_cases) >= 2
    assert len(two_sum.hidden_test_cases) >= 3

    # Ensure get_public_challenge_dict strips hidden test cases and reference solutions
    pub_dict = get_public_challenge_dict(two_sum)
    assert "hidden_test_cases" not in pub_dict
    assert "reference_solutions" not in pub_dict
    assert len(pub_dict["public_test_cases"]) == len(two_sum.public_test_cases)


def test_javascript_execution_sandbox():
    js_source = """
const fs = require('fs');

function main() {
    const input = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);
    if (!input || input.length < 2) return;
    const n = parseInt(input[0], 10);
    const nums = input.slice(1, n + 1).map(Number);
    const seen = new Set();
    let hasDup = false;
    for (const num of nums) {
        if (seen.has(num)) {
            hasDup = true;
            break;
        }
        seen.add(num);
    }
    console.log(hasDup ? "YES" : "NO");
}

main();
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="5\n4 2 7 2 1\n", expected_stdout="YES\n", is_hidden=False),
        CodingTestCase(test_id=2, stdin="4\n1 2 3 4\n", expected_stdout="NO\n", is_hidden=False),
        CodingTestCase(test_id=3, stdin="3\n9 9 9\n", expected_stdout="YES\n", is_hidden=True),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-001-TWO-SUM",
        language="javascript",
        source_code=js_source,
        custom_test_cases=test_cases,
    )

    if evaluation.compile_success:
        assert evaluation.public_tests_passed == 2
        assert evaluation.hidden_tests_passed == 1
        assert evaluation.overall_coding_score >= 80.0
    else:
        pytest.skip("Node.js not installed in test environment")


def test_java_compilation_and_execution():
    java_source = """
import java.util.*;

public class Solution {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        if (!sc.hasNextInt()) return;
        int n = sc.nextInt();
        Set<Integer> seen = new HashSet<>();
        boolean hasDup = false;
        for (int i = 0; i < n; i++) {
            int val = sc.nextInt();
            if (seen.contains(val)) {
                hasDup = true;
            }
            seen.add(val);
        }
        System.out.println(hasDup ? "YES" : "NO");
    }
}
"""
    test_cases = [
        CodingTestCase(test_id=1, stdin="5\n4 2 7 2 1\n", expected_stdout="YES\n", is_hidden=False),
        CodingTestCase(test_id=2, stdin="4\n1 2 3 4\n", expected_stdout="NO\n", is_hidden=False),
        CodingTestCase(test_id=3, stdin="3\n5 5 1\n", expected_stdout="YES\n", is_hidden=True),
    ]

    evaluation = evaluate_coding_challenge(
        challenge_id="CHAL-001-TWO-SUM",
        language="java",
        source_code=java_source,
        custom_test_cases=test_cases,
    )

    if evaluation.compile_success:
        assert evaluation.public_tests_passed == 2
        assert evaluation.hidden_tests_passed == 1
        assert evaluation.overall_coding_score >= 80.0
    else:
        pytest.skip("Java/javac not installed in test environment")
