"""
Domain models and curated catalog for coding challenges and test suites.

Includes public sample test cases and server-stored hidden test cases across
supported algorithmic paradigms and languages (Python, JavaScript, C, C++, Java).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CodingTestCase(BaseModel):
    """Single test case input and expected standard output."""
    test_id: int
    stdin: str = ""
    expected_stdout: str = ""
    is_hidden: bool = False
    description: Optional[str] = None


class CodingChallenge(BaseModel):
    """Full coding challenge specification with multi-language templates and test suites."""
    challenge_id: str
    title: str
    problem_statement: str
    difficulty: str = "mid"
    recommended_languages: List[str] = Field(
        default_factory=lambda: ["python", "javascript", "c", "cpp", "java"]
    )
    constraints: str = ""
    starter_code: str = ""
    starter_templates: Dict[str, str] = Field(default_factory=dict)
    public_test_cases: List[CodingTestCase] = Field(default_factory=list)
    hidden_test_cases: List[CodingTestCase] = Field(default_factory=list)
    reference_solutions: Dict[str, str] = Field(default_factory=dict)
    evaluation_notes: Optional[str] = None


# --- Curated Algorithmic Challenge Catalog ---

_CHALLENGE_CATALOG: Dict[str, CodingChallenge] = {
    "CHAL-001-TWO-SUM": CodingChallenge(
        challenge_id="CHAL-001-TWO-SUM",
        title="Duplicate Identifier Detection",
        problem_statement=(
            "Audit a batch of telemetry ticket IDs.\n"
            "Input format:\n"
            "Line 1: Integer n (2 ≤ n ≤ 2000).\n"
            "Line 2: n space-separated integers.\n"
            "Output format:\n"
            "Print 'YES' if any integer appears at least twice, otherwise print 'NO' with a trailing newline."
        ),
        difficulty="entry",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n) or O(n log n). Space Complexity: O(n). 32-bit signed integers.",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    n = int(data[0])\n"
            "    nums = [int(x) for x in data[1:n+1]]\n"
            "    # TODO: Detect duplicate integer\n"
            "    print('NO')\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    if not data:\n"
                "        return\n"
                "    n = int(data[0])\n"
                "    nums = [int(x) for x in data[1:n+1]]\n"
                "    seen = set()\n"
                "    for x in nums:\n"
                "        if x in seen:\n"
                "            print('YES')\n"
                "            return\n"
                "        seen.add(x)\n"
                "    print('NO')\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const n = parseInt(tokens[0], 10);\n"
                "    const nums = tokens.slice(1, n + 1).map(Number);\n"
                "    const seen = new Set();\n"
                "    for (const num of nums) {\n"
                "        if (seen.has(num)) {\n"
                "            console.log('YES');\n"
                "            return;\n"
                "        }\n"
                "        seen.add(num);\n"
                "    }\n"
                "    console.log('NO');\n"
                "}\n\n"
                "main();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <vector>\n"
                "#include <unordered_set>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    ios_base::sync_with_stdio(false);\n"
                "    cin.tie(NULL);\n"
                "    int n;\n"
                "    if (!(cin >> n)) return 0;\n"
                "    unordered_set<int> seen;\n"
                "    bool dup = false;\n"
                "    for (int i = 0; i < n; ++i) {\n"
                "        int val;\n"
                "        cin >> val;\n"
                "        if (seen.find(val) != seen.end()) dup = true;\n"
                "        seen.insert(val);\n"
                "    }\n"
                "    cout << (dup ? \"YES\" : \"NO\") << \"\\n\";\n"
                "    return 0;\n"
                "}\n"
            ),
            "c": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "int compare(const void *a, const void *b) {\n"
                "    int x = *(const int *)a;\n"
                "    int y = *(const int *)b;\n"
                "    return (x > y) - (x < y);\n"
                "}\n\n"
                "int main() {\n"
                "    int n;\n"
                "    if (scanf(\"%d\", &n) != 1) return 0;\n"
                "    int *arr = (int *)malloc(n * sizeof(int));\n"
                "    for (int i = 0; i < n; ++i) {\n"
                "        if (scanf(\"%d\", &arr[i]) != 1) { free(arr); return 0; }\n"
                "    }\n"
                "    qsort(arr, n, sizeof(int), compare);\n"
                "    int dup = 0;\n"
                "    for (int i = 1; i < n; ++i) {\n"
                "        if (arr[i] == arr[i - 1]) { dup = 1; break; }\n"
                "    }\n"
                "    printf(\"%s\\n\", dup ? \"YES\" : \"NO\");\n"
                "    free(arr);\n"
                "    return 0;\n"
                "}\n"
            ),
            "java": (
                "import java.util.*;\n\n"
                "public class Solution {\n"
                "    public static void main(String[] args) {\n"
                "        Scanner sc = new Scanner(System.in);\n"
                "        if (!sc.hasNextInt()) return;\n"
                "        int n = sc.nextInt();\n"
                "        Set<Integer> seen = new HashSet<>();\n"
                "        boolean dup = false;\n"
                "        for (int i = 0; i < n; i++) {\n"
                "            int val = sc.nextInt();\n"
                "            if (seen.contains(val)) dup = true;\n"
                "            seen.add(val);\n"
                "        }\n"
                "        System.out.println(dup ? \"YES\" : \"NO\");\n"
                "    }\n"
                "}\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="5\n4 2 7 2 1\n",
                expected_stdout="YES\n",
                is_hidden=False,
                description="Duplicate 2 present in small array",
            ),
            CodingTestCase(
                test_id=2,
                stdin="4\n1 2 3 4\n",
                expected_stdout="NO\n",
                is_hidden=False,
                description="All distinct elements",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="6\n10 20 30 40 50 10\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Duplicate at boundary (first and last)",
            ),
            CodingTestCase(
                test_id=4,
                stdin="5\n-1 -2 -3 -4 -5\n",
                expected_stdout="NO\n",
                is_hidden=True,
                description="All distinct negative numbers",
            ),
            CodingTestCase(
                test_id=5,
                stdin="7\n0 5 -5 10 -10 5 99\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Duplicate positive 5 with mixed signs",
            ),
            CodingTestCase(
                test_id=6,
                stdin="2\n1000000 1000000\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Minimum length array with twin large elements",
            ),
        ],
    ),
    "CHAL-002-VALID-PARENTHESES": CodingChallenge(
        challenge_id="CHAL-002-VALID-PARENTHESES",
        title="DSL Bracket Sequence Validation",
        problem_statement=(
            "Validate bracket syntax for a domain configuration DSL.\n"
            "Input format:\n"
            "Line 1: A single non-empty string containing only characters '(', ')', '{', '}', '[', ']'.\n"
            "Output format:\n"
            "Print 'YES' if the brackets are closed in valid LIFO order and matched by the same type, otherwise 'NO'."
        ),
        difficulty="mid",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="String length ≤ 2000. Contains only ()[]{}.",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    line = sys.stdin.readline().strip()\n"
            "    # TODO: Stack validation\n"
            "    print('YES')\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\n\n\ndef main():\n"
                "    s = sys.stdin.readline().strip()\n"
                "    mapping = {')': '(', '}': '{', ']': '['}\n"
                "    stack = []\n"
                "    for char in s:\n"
                "        if char in mapping.values():\n"
                "            stack.append(char)\n"
                "        elif char in mapping:\n"
                "            if not stack or stack.pop() != mapping[char]:\n"
                "                print('NO')\n"
                "                return\n"
                "    print('YES' if not stack else 'NO')\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const s = fs.readFileSync(0, 'utf-8').trim();\n"
                "    const map = { ')': '(', '}': '{', ']': '[' };\n"
                "    const stack = [];\n"
                "    for (let i = 0; i < s.length; i++) {\n"
                "        const ch = s[i];\n"
                "        if (ch === '(' || ch === '{' || ch === '[') {\n"
                "            stack.push(ch);\n"
                "        } else if (map[ch]) {\n"
                "            if (stack.length === 0 || stack.pop() !== map[ch]) {\n"
                "                console.log('NO');\n"
                "                return;\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "    console.log(stack.length === 0 ? 'YES' : 'NO');\n"
                "}\n\n"
                "main();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <string>\n"
                "#include <stack>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    string s;\n"
                "    if (!(cin >> s)) return 0;\n"
                "    stack<char> st;\n"
                "    bool ok = true;\n"
                "    for (char c : s) {\n"
                "        if (c == '(' || c == '{' || c == '[') st.push(c);\n"
                "        else {\n"
                "            if (st.empty()) { ok = false; break; }\n"
                "            char top = st.top(); st.pop();\n"
                "            if ((c == ')' && top != '(') || (c == '}' && top != '{') || (c == ']' && top != '[')) {\n"
                "                ok = false; break;\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "    if (!st.empty()) ok = false;\n"
                "    cout << (ok ? \"YES\" : \"NO\") << \"\\n\";\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="()[]{}\n",
                expected_stdout="YES\n",
                is_hidden=False,
                description="Valid mixed brackets in sequence",
            ),
            CodingTestCase(
                test_id=2,
                stdin="([)]\n",
                expected_stdout="NO\n",
                is_hidden=False,
                description="Invalid intertwined bracket nesting",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="{[()]}\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Properly nested multi-tier hierarchy",
            ),
            CodingTestCase(
                test_id=4,
                stdin="(((\n",
                expected_stdout="NO\n",
                is_hidden=True,
                description="Unclosed opening brackets",
            ),
            CodingTestCase(
                test_id=5,
                stdin="]\n",
                expected_stdout="NO\n",
                is_hidden=True,
                description="Immediate closing bracket on empty stack",
            ),
            CodingTestCase(
                test_id=6,
                stdin="{()}[{()}]\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Complex compound balanced structure",
            ),
        ],
    ),
    "CHAL-003-MAX-SUBARRAY": CodingChallenge(
        challenge_id="CHAL-003-MAX-SUBARRAY",
        title="Maximum Subarray Throughput (Kadane)",
        problem_statement=(
            "Calculate the maximum possible contiguous throughput sum from a stream of periodic deltas.\n"
            "Input format:\n"
            "Line 1: Integer n (1 ≤ n ≤ 5000).\n"
            "Line 2: n space-separated integers (can be negative).\n"
            "Output format:\n"
            "Print the maximum contiguous subarray sum followed by a newline."
        ),
        difficulty="senior",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n). Space Complexity: O(1). Output fits in 64-bit integer.",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    n = int(data[0])\n"
            "    nums = [int(x) for x in data[1:n+1]]\n"
            "    # TODO: Kadane's algorithm\n"
            "    print(0)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    if not data:\n"
                "        return\n"
                "    n = int(data[0])\n"
                "    nums = [int(x) for x in data[1:n+1]]\n"
                "    max_so_far = nums[0]\n"
                "    curr_max = nums[0]\n"
                "    for i in range(1, n):\n"
                "        curr_max = max(nums[i], curr_max + nums[i])\n"
                "        max_so_far = max(max_so_far, curr_max)\n"
                "    print(max_so_far)\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const n = parseInt(tokens[0], 10);\n"
                "    const nums = tokens.slice(1, n + 1).map(Number);\n"
                "    let maxSoFar = nums[0];\n"
                "    let currMax = nums[0];\n"
                "    for (let i = 1; i < n; i++) {\n"
                "        currMax = Math.max(nums[i], currMax + nums[i]);\n"
                "        maxSoFar = Math.max(maxSoFar, currMax);\n"
                "    }\n"
                "    console.log(maxSoFar);\n"
                "}\n\n"
                "main();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <vector>\n"
                "#include <algorithm>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    int n;\n"
                "    if (!(cin >> n)) return 0;\n"
                "    long long max_so_far, curr_max;\n"
                "    long long first;\n"
                "    cin >> first;\n"
                "    max_so_far = curr_max = first;\n"
                "    for (int i = 1; i < n; ++i) {\n"
                "        long long x;\n"
                "        cin >> x;\n"
                "        curr_max = max(x, curr_max + x);\n"
                "        max_so_far = max(max_so_far, curr_max);\n"
                "    }\n"
                "    cout << max_so_far << \"\\n\";\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="4\n1 -2 3 4\n",
                expected_stdout="7\n",
                is_hidden=False,
                description="Subarray [3, 4] yields max sum 7",
            ),
            CodingTestCase(
                test_id=2,
                stdin="1\n-5\n",
                expected_stdout="-5\n",
                is_hidden=False,
                description="Single negative element",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="9\n-2 1 -3 4 -1 2 1 -5 4\n",
                expected_stdout="6\n",
                is_hidden=True,
                description="Classic Kadane benchmark subarray [4, -1, 2, 1]",
            ),
            CodingTestCase(
                test_id=4,
                stdin="5\n-8 -3 -6 -2 -5\n",
                expected_stdout="-2\n",
                is_hidden=True,
                description="All negative numbers returns least negative",
            ),
            CodingTestCase(
                test_id=5,
                stdin="6\n10 20 30 40 50 60\n",
                expected_stdout="210\n",
                is_hidden=True,
                description="All positive numbers sum total",
            ),
        ],
    ),
    "CHAL-004-PALINDROME-CHECK": CodingChallenge(
        challenge_id="CHAL-004-PALINDROME-CHECK",
        title="Alphanumeric Palindrome Validator",
        problem_statement=(
            "Determine if an incoming text string is an alphanumeric palindrome (ignoring casing and punctuation).\n"
            "Input format:\n"
            "Line 1: Text string.\n"
            "Output format:\n"
            "Print 'YES' if it reads the same forward and backward after filtering non-alphanumerics, else 'NO'."
        ),
        difficulty="entry",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="String length ≤ 2000.",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    line = sys.stdin.readline().strip()\n"
            "    cleaned = [c.lower() for c in line if c.isalnum()]\n"
            "    print('YES' if cleaned == cleaned[::-1] else 'NO')\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="A man, a plan, a canal: Panama\n",
                expected_stdout="YES\n",
                is_hidden=False,
                description="Standard palindrome with punctuation",
            ),
            CodingTestCase(
                test_id=2,
                stdin="race a car\n",
                expected_stdout="NO\n",
                is_hidden=False,
                description="Non-palindrome string",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="0P\n",
                expected_stdout="NO\n",
                is_hidden=True,
                description="Short alphanumeric non-palindrome",
            ),
            CodingTestCase(
                test_id=4,
                stdin="ab_a\n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Palindrome with underscore symbol",
            ),
            CodingTestCase(
                test_id=5,
                stdin="   \n",
                expected_stdout="YES\n",
                is_hidden=True,
                description="Whitespace-only string is trivially empty palindrome",
            ),
        ],
    ),
    "CHAL-005-BINARY-SEARCH": CodingChallenge(
        challenge_id="CHAL-005-BINARY-SEARCH",
        title="Target Index Binary Search",
        problem_statement=(
            "Locate the index of a target value in a sorted array.\n"
            "Input format:\n"
            "Line 1: Two integers n (1 ≤ n ≤ 5000) and target.\n"
            "Line 2: n sorted space-separated integers.\n"
            "Output format:\n"
            "Print the 0-indexed position of target if found, otherwise -1."
        ),
        difficulty="mid",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(log n).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    n = int(data[0])\n"
            "    target = int(data[1])\n"
            "    nums = [int(x) for x in data[2:n+2]]\n"
            "    # TODO: Binary Search\n"
            "    left, right = 0, n - 1\n"
            "    res = -1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if nums[mid] == target:\n"
            "            res = mid\n"
            "            break\n"
            "        elif nums[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    print(res)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="6 9\n-1 0 3 5 9 12\n",
                expected_stdout="4\n",
                is_hidden=False,
                description="Target 9 found at index 4",
            ),
            CodingTestCase(
                test_id=2,
                stdin="6 2\n-1 0 3 5 9 12\n",
                expected_stdout="-1\n",
                is_hidden=False,
                description="Target 2 not present in list",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="1 5\n5\n",
                expected_stdout="0\n",
                is_hidden=True,
                description="Single element matching target",
            ),
            CodingTestCase(
                test_id=4,
                stdin="5 100\n10 20 30 40 50\n",
                expected_stdout="-1\n",
                is_hidden=True,
                description="Target out of right bounds",
            ),
            CodingTestCase(
                test_id=5,
                stdin="4 -10\n-10 -5 0 5\n",
                expected_stdout="0\n",
                is_hidden=True,
                description="Target at leftmost boundary",
            ),
        ],
    ),
}


# --- Domain Query Functions ---

def get_all_challenges() -> List[CodingChallenge]:
    """Return all available coding challenges in the repository."""
    return list(_CHALLENGE_CATALOG.values())


def get_challenge(challenge_id: str) -> Optional[CodingChallenge]:
    """Fetch challenge definition by unique challenge ID."""
    if not challenge_id:
        return None
    return _CHALLENGE_CATALOG.get(challenge_id.strip())


def get_challenges_by_difficulty(difficulty: str) -> List[CodingChallenge]:
    """Filter challenges by difficulty tier (entry, mid, senior, lead, easy, medium, hard)."""
    target = (difficulty or "").strip().lower()
    return [c for c in _CHALLENGE_CATALOG.values() if c.difficulty.lower() == target]


def get_public_challenge_dict(challenge: CodingChallenge) -> Dict[str, Any]:
    """
    Return candidate-safe dictionary representation of a challenge.
    Excludes server-side hidden test cases and internal reference solutions.
    """
    return {
        "challenge_id": challenge.challenge_id,
        "title": challenge.title,
        "problem_statement": challenge.problem_statement,
        "difficulty": challenge.difficulty,
        "recommended_languages": challenge.recommended_languages,
        "constraints": challenge.constraints,
        "starter_code": challenge.starter_code,
        "starter_templates": challenge.starter_templates,
        "public_test_cases": [
            {
                "test_id": tc.test_id,
                "stdin": tc.stdin,
                "expected_stdout": tc.expected_stdout,
                "is_hidden": False,
                "description": tc.description,
            }
            for tc in challenge.public_test_cases
        ],
    }
