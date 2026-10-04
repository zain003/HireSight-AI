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
    "CHAL-006-LRU-CACHE": CodingChallenge(
        challenge_id="CHAL-006-LRU-CACHE",
        title="Least Recently Used (LRU) Page Fault Simulator",
        problem_statement=(
            "Simulate a Least Recently Used (LRU) page replacement algorithm for a virtual memory system.\n"
            "Input format:\n"
            "Line 1: Two space-separated integers: physical frame capacity C (1 ≤ C ≤ 100) and reference count n (1 ≤ n ≤ 2000).\n"
            "Line 2: n space-separated integers representing sequential page reference requests.\n"
            "Output format:\n"
            "Print the total number of page faults followed by a newline."
        ),
        difficulty="mid",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n * C) or O(n). Memory: O(C).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    capacity = int(data[0])\n"
            "    n = int(data[1])\n"
            "    pages = [int(x) for x in data[2:2+n]]\n"
            "    # TODO: Simulate LRU cache and count page faults\n"
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
                "    capacity = int(data[0])\n"
                "    n = int(data[1])\n"
                "    pages = [int(x) for x in data[2:2+n]]\n"
                "    cache = []\n"
                "    faults = 0\n"
                "    for p in pages:\n"
                "        if p in cache:\n"
                "            cache.remove(p)\n"
                "            cache.append(p)\n"
                "        else:\n"
                "            faults += 1\n"
                "            if len(cache) >= capacity:\n"
                "                cache.pop(0)\n"
                "            cache.append(p)\n"
                "    print(faults)\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const capacity = parseInt(tokens[0], 10);\n"
                "    const n = parseInt(tokens[1], 10);\n"
                "    const pages = tokens.slice(2, 2 + n).map(Number);\n"
                "    const cache = [];\n"
                "    let faults = 0;\n"
                "    for (const p of pages) {\n"
                "        const idx = cache.indexOf(p);\n"
                "        if (idx !== -1) {\n"
                "            cache.splice(idx, 1);\n"
                "            cache.push(p);\n"
                "        } else {\n"
                "            faults++;\n"
                "            if (cache.length >= capacity) cache.shift();\n"
                "            cache.push(p);\n"
                "        }\n"
                "    }\n"
                "    console.log(faults);\n"
                "}\n\n"
                "main();\n"
            ),
            "cpp": (
                "#include <iostream>\n"
                "#include <vector>\n"
                "#include <list>\n"
                "#include <unordered_map>\n"
                "using namespace std;\n\n"
                "int main() {\n"
                "    int capacity, n;\n"
                "    if (!(cin >> capacity >> n)) return 0;\n"
                "    list<int> lru;\n"
                "    unordered_map<int, list<int>::iterator> pos;\n"
                "    int faults = 0;\n"
                "    for (int i = 0; i < n; ++i) {\n"
                "        int p;\n"
                "        cin >> p;\n"
                "        if (pos.find(p) != pos.end()) {\n"
                "            lru.erase(pos[p]);\n"
                "            lru.push_back(p);\n"
                "            pos[p] = --lru.end();\n"
                "        } else {\n"
                "            faults++;\n"
                "            if ((int)lru.size() >= capacity) {\n"
                "                int evict = lru.front();\n"
                "                lru.pop_front();\n"
                "                pos.erase(evict);\n"
                "            }\n"
                "            lru.push_back(p);\n"
                "            pos[p] = --lru.end();\n"
                "        }\n"
                "    }\n"
                "    cout << faults << \"\\n\";\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="3 13\n7 0 1 2 0 3 0 4 2 3 0 3 2\n",
                expected_stdout="10\n",
                is_hidden=False,
                description="3 frames with classic reference string yields 10 page faults",
            ),
            CodingTestCase(
                test_id=2,
                stdin="2 5\n1 2 1 3 1\n",
                expected_stdout="4\n",
                is_hidden=False,
                description="2 frames with repetitive sequence yields 4 faults",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="4 8\n1 2 3 4 1 2 3 4\n",
                expected_stdout="4\n",
                is_hidden=True,
                description="Capacity 4 holds all 4 unique pages with no eviction",
            ),
            CodingTestCase(
                test_id=4,
                stdin="1 6\n1 2 1 2 1 2\n",
                expected_stdout="6\n",
                is_hidden=True,
                description="Capacity 1 evicts on every alternating page",
            ),
        ],
    ),
    "CHAL-007-MERGE-INTERVALS": CodingChallenge(
        challenge_id="CHAL-007-MERGE-INTERVALS",
        title="Overlapping Interval Scheduler",
        problem_statement=(
            "Given n time intervals [start, end], merge all overlapping intervals and print the total merged count followed by each merged range in ascending order.\n"
            "Input format:\n"
            "Line 1: Integer n (1 ≤ n ≤ 2000).\n"
            "Next n lines: Two space-separated integers start and end.\n"
            "Output format:\n"
            "Line 1: Total number of non-overlapping merged intervals k.\n"
            "Next k lines: start end in ascending order."
        ),
        difficulty="mid",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n log n). Space Complexity: O(n).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    lines = sys.stdin.read().strip().splitlines()\n"
            "    if not lines:\n"
            "        return\n"
            "    n = int(lines[0].strip())\n"
            "    # TODO: Merge overlapping intervals\n"
            "    print(0)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\n\n\ndef main():\n"
                "    tokens = sys.stdin.read().strip().split()\n"
                "    if not tokens:\n"
                "        return\n"
                "    n = int(tokens[0])\n"
                "    intervals = []\n"
                "    idx = 1\n"
                "    for _ in range(n):\n"
                "        intervals.append([int(tokens[idx]), int(tokens[idx+1])])\n"
                "        idx += 2\n"
                "    intervals.sort(key=lambda x: x[0])\n"
                "    merged = []\n"
                "    for iv in intervals:\n"
                "        if not merged or merged[-1][1] < iv[0]:\n"
                "            merged.append(iv)\n"
                "        else:\n"
                "            merged[-1][1] = max(merged[-1][1], iv[1])\n"
                "    print(len(merged))\n"
                "    for s, e in merged:\n"
                "        print(f'{s} {e}')\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 1) return;\n"
                "    const n = parseInt(tokens[0], 10);\n"
                "    const intervals = [];\n"
                "    let idx = 1;\n"
                "    for (let i = 0; i < n; i++) {\n"
                "        intervals.push([parseInt(tokens[idx], 10), parseInt(tokens[idx+1], 10)]);\n"
                "        idx += 2;\n"
                "    }\n"
                "    intervals.sort((a, b) => a[0] - b[0]);\n"
                "    const merged = [];\n"
                "    for (const iv of intervals) {\n"
                "        if (merged.length === 0 || merged[merged.length - 1][1] < iv[0]) {\n"
                "            merged.push(iv);\n"
                "        } else {\n"
                "            merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], iv[1]);\n"
                "        }\n"
                "    }\n"
                "    console.log(merged.length);\n"
                "    for (const [s, e] of merged) {\n"
                "        console.log(`${s} ${e}`);\n"
                "    }\n"
                "}\n\n"
                "main();\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="4\n1 3\n2 6\n8 10\n15 18\n",
                expected_stdout="3\n1 6\n8 10\n15 18\n",
                is_hidden=False,
                description="Merge [1,3] and [2,6] into [1,6]",
            ),
            CodingTestCase(
                test_id=2,
                stdin="2\n1 4\n4 5\n",
                expected_stdout="1\n1 5\n",
                is_hidden=False,
                description="Touching intervals merge into single [1,5]",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="3\n1 4\n0 4\n3 5\n",
                expected_stdout="1\n0 5\n",
                is_hidden=True,
                description="Unordered nested intervals merge to [0,5]",
            ),
        ],
    ),
    "CHAL-008-GROUP-ANAGRAMS": CodingChallenge(
        challenge_id="CHAL-008-GROUP-ANAGRAMS",
        title="Anagram Signature Grouping",
        problem_statement=(
            "Given an array of lowercase strings, group the anagrams together and print the total number of distinct anagram groups.\n"
            "Input format:\n"
            "Line 1: Integer n (1 ≤ n ≤ 1000).\n"
            "Line 2: n space-separated lowercase words.\n"
            "Output format:\n"
            "Print the number of distinct anagram groups followed by a newline."
        ),
        difficulty="entry",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n * k log k).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    n = int(data[0])\n"
            "    words = data[1:1+n]\n"
            "    # TODO: Group anagrams\n"
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
                "    words = data[1:1+n]\n"
                "    groups = {}\n"
                "    for w in words:\n"
                "        key = ''.join(sorted(w))\n"
                "        groups.setdefault(key, []).append(w)\n"
                "    print(len(groups))\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const n = parseInt(tokens[0], 10);\n"
                "    const words = tokens.slice(1, 1 + n);\n"
                "    const groups = new Set();\n"
                "    for (const w of words) {\n"
                "        groups.add(w.split('').sort().join(''));\n"
                "    }\n"
                "    console.log(groups.size);\n"
                "}\n\n"
                "main();\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="6\neat tea tan ate nat bat\n",
                expected_stdout="3\n",
                is_hidden=False,
                description="6 words grouped into 3 anagram sets",
            ),
            CodingTestCase(
                test_id=2,
                stdin="1\na\n",
                expected_stdout="1\n",
                is_hidden=False,
                description="Single letter word",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="4\nab ba cd dc\n",
                expected_stdout="2\n",
                is_hidden=True,
                description="Two pairs of two anagrams",
            ),
        ],
    ),
    "CHAL-009-TOP-K-FREQUENT": CodingChallenge(
        challenge_id="CHAL-009-TOP-K-FREQUENT",
        title="Top K Frequent Metric Aggregator",
        problem_statement=(
            "Given an array of integer metric values, find the sum of the k most frequently occurring elements.\n"
            "Input format:\n"
            "Line 1: Two space-separated integers: n (1 ≤ n ≤ 5000) and k (1 ≤ k ≤ n).\n"
            "Line 2: n space-separated integers.\n"
            "Output format:\n"
            "Print the sum of the k most frequent element values followed by a newline."
        ),
        difficulty="mid",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n log n).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    n = int(data[0])\n"
            "    k = int(data[1])\n"
            "    nums = [int(x) for x in data[2:2+n]]\n"
            "    # TODO: Calculate sum of top k frequent elements\n"
            "    print(0)\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\nfrom collections import Counter\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    if not data:\n"
                "        return\n"
                "    n = int(data[0])\n"
                "    k = int(data[1])\n"
                "    nums = [int(x) for x in data[2:2+n]]\n"
                "    counts = Counter(nums)\n"
                "    top_k = [val for val, _ in counts.most_common(k)]\n"
                "    print(sum(top_k))\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const n = parseInt(tokens[0], 10);\n"
                "    const k = parseInt(tokens[1], 10);\n"
                "    const nums = tokens.slice(2, 2 + n).map(Number);\n"
                "    const freq = new Map();\n"
                "    for (const x of nums) freq.set(x, (freq.get(x) || 0) + 1);\n"
                "    const sorted = Array.from(freq.entries()).sort((a, b) => b[1] - a[1]);\n"
                "    let sum = 0;\n"
                "    for (let i = 0; i < Math.min(k, sorted.length); i++) sum += sorted[i][0];\n"
                "    console.log(sum);\n"
                "}\n\n"
                "main();\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="6 2\n1 1 1 2 2 3\n",
                expected_stdout="3\n",
                is_hidden=False,
                description="Top 2 frequent elements 1 and 2 sum to 3",
            ),
            CodingTestCase(
                test_id=2,
                stdin="1 1\n100\n",
                expected_stdout="100\n",
                is_hidden=False,
                description="Single element",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="7 3\n4 4 4 5 5 6 7\n",
                expected_stdout="15\n",
                is_hidden=True,
                description="Top 3 frequent 4, 5, 6 sum to 15",
            ),
        ],
    ),
    "CHAL-010-TOKEN-BUCKET": CodingChallenge(
        challenge_id="CHAL-010-TOKEN-BUCKET",
        title="Token Bucket Rate Limiter Simulator",
        problem_statement=(
            "Simulate a token bucket rate limiter. Given capacity C and a sequence of arrival timestamps in seconds, where 1 token is refilled per second (up to capacity C), count how many requests are accepted and how many are rejected (dropped).\n"
            "Input format:\n"
            "Line 1: Two space-separated integers: capacity C (1 ≤ C ≤ 100) and request count n (1 ≤ n ≤ 2000).\n"
            "Line 2: n space-separated non-decreasing integers representing request timestamps in seconds.\n"
            "Output format:\n"
            "Two space-separated integers: accepted_count rejected_count followed by a newline."
        ),
        difficulty="senior",
        recommended_languages=["python", "javascript", "c", "cpp", "java"],
        constraints="Time Complexity: O(n). Space Complexity: O(1).",
        starter_code=(
            "import sys\n\n\ndef main():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data:\n"
            "        return\n"
            "    capacity = int(data[0])\n"
            "    n = int(data[1])\n"
            "    timestamps = [int(x) for x in data[2:2+n]]\n"
            "    # TODO: Token bucket simulation\n"
            "    print(f'{n} 0')\n\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
        starter_templates={
            "python": (
                "import sys\n\n\ndef main():\n"
                "    data = sys.stdin.read().strip().split()\n"
                "    if not data:\n"
                "        return\n"
                "    capacity = int(data[0])\n"
                "    n = int(data[1])\n"
                "    timestamps = [int(x) for x in data[2:2+n]]\n"
                "    tokens = capacity\n"
                "    last_time = timestamps[0]\n"
                "    accepted = 0\n"
                "    dropped = 0\n"
                "    for t in timestamps:\n"
                "        elapsed = t - last_time\n"
                "        tokens = min(capacity, tokens + elapsed)\n"
                "        last_time = t\n"
                "        if tokens >= 1:\n"
                "            tokens -= 1\n"
                "            accepted += 1\n"
                "        else:\n"
                "            dropped += 1\n"
                "    print(f'{accepted} {dropped}')\n\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "javascript": (
                "const fs = require('fs');\n\n"
                "function main() {\n"
                "    const tokens = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n"
                "    if (!tokens || tokens.length < 2) return;\n"
                "    const capacity = parseInt(tokens[0], 10);\n"
                "    const n = parseInt(tokens[1], 10);\n"
                "    const timestamps = tokens.slice(2, 2 + n).map(Number);\n"
                "    let tokenCount = capacity;\n"
                "    let lastTime = timestamps[0];\n"
                "    let accepted = 0;\n"
                "    let dropped = 0;\n"
                "    for (const t of timestamps) {\n"
                "        const elapsed = t - lastTime;\n"
                "        tokenCount = Math.min(capacity, tokenCount + elapsed);\n"
                "        lastTime = t;\n"
                "        if (tokenCount >= 1) {\n"
                "            tokenCount -= 1;\n"
                "            accepted++;\n"
                "        } else {\n"
                "            dropped++;\n"
                "        }\n"
                "    }\n"
                "    console.log(`${accepted} ${dropped}`);\n"
                "}\n\n"
                "main();\n"
            ),
        },
        public_test_cases=[
            CodingTestCase(
                test_id=1,
                stdin="3 5\n1 1 1 1 2\n",
                expected_stdout="4 1\n",
                is_hidden=False,
                description="4 bursts at t=1 drops 1 request, recovery at t=2 accepts 5th",
            ),
            CodingTestCase(
                test_id=2,
                stdin="2 3\n0 10 20\n",
                expected_stdout="3 0\n",
                is_hidden=False,
                description="Spaced requests all accepted",
            ),
        ],
        hidden_test_cases=[
            CodingTestCase(
                test_id=3,
                stdin="1 5\n0 0 0 0 0\n",
                expected_stdout="1 4\n",
                is_hidden=True,
                description="Capacity 1 with 5 simultaneous requests drops 4",
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


get_coding_challenge_by_id = get_challenge


def get_role_challenges(job_role: str = "") -> List[CodingChallenge]:
    """Return the curated challenge pool for a given job role."""
    r_lower = (job_role or "").lower()
    if any(k in r_lower for k in ["mern", "react", "frontend", "javascript", "node"]):
        keys = ["CHAL-002-VALID-PARENTHESES", "CHAL-006-LRU-CACHE", "CHAL-007-MERGE-INTERVALS", "CHAL-009-TOP-K-FREQUENT", "CHAL-010-TOKEN-BUCKET", "CHAL-003-MAX-SUBARRAY"]
    elif any(k in r_lower for k in ["python", "django", "fastapi", "backend"]):
        keys = ["CHAL-006-LRU-CACHE", "CHAL-010-TOKEN-BUCKET", "CHAL-007-MERGE-INTERVALS", "CHAL-003-MAX-SUBARRAY", "CHAL-002-VALID-PARENTHESES", "CHAL-009-TOP-K-FREQUENT"]
    elif any(k in r_lower for k in ["java", "spring"]):
        keys = ["CHAL-005-BINARY-SEARCH", "CHAL-006-LRU-CACHE", "CHAL-007-MERGE-INTERVALS", "CHAL-002-VALID-PARENTHESES", "CHAL-003-MAX-SUBARRAY", "CHAL-010-TOKEN-BUCKET"]
    elif any(k in r_lower for k in ["flutter", "mobile", "android", "ios", "react native"]):
        keys = ["CHAL-006-LRU-CACHE", "CHAL-002-VALID-PARENTHESES", "CHAL-003-MAX-SUBARRAY", "CHAL-007-MERGE-INTERVALS", "CHAL-010-TOKEN-BUCKET"]
    elif any(k in r_lower for k in ["data", "ml", "ai", "machine learning", "pipeline"]):
        keys = ["CHAL-009-TOP-K-FREQUENT", "CHAL-007-MERGE-INTERVALS", "CHAL-010-TOKEN-BUCKET", "CHAL-003-MAX-SUBARRAY", "CHAL-005-BINARY-SEARCH"]
    else:
        keys = ["CHAL-006-LRU-CACHE", "CHAL-002-VALID-PARENTHESES", "CHAL-007-MERGE-INTERVALS", "CHAL-010-TOKEN-BUCKET", "CHAL-003-MAX-SUBARRAY", "CHAL-009-TOP-K-FREQUENT"]
    return [_CHALLENGE_CATALOG[k] for k in keys if k in _CHALLENGE_CATALOG]


def get_challenges_by_difficulty(difficulty: str) -> List[CodingChallenge]:
    """Filter challenges by difficulty tier (entry, mid, senior, lead, easy, medium, hard)."""
    target = (difficulty or "").strip().lower()
    return [c for c in _CHALLENGE_CATALOG.values() if c.difficulty.lower() == target]


def match_or_select_coding_challenge(job_role: str = "", query_text: str = "", idx: int = 0) -> CodingChallenge:
    """
    Intelligently select or match the best coding challenge based on:
    1. Keyword matching from question_text (e.g. 'LRU', 'bracket', 'kadane', 'interval', 'palindrome')
    2. Role & stack specialization (e.g. MERN, Python, Java, Mobile, Data)
    """
    if not isinstance(idx, int):
        try:
            idx = int(idx)
        except (ValueError, TypeError):
            idx = 0

    q_lower = (query_text or "").lower()
    r_lower = (job_role or "").lower()

    # 1. Direct keyword match
    if any(k in q_lower for k in ["lru", "cache", "virtual memory", "page replacement", "page fault"]):
        return _CHALLENGE_CATALOG["CHAL-006-LRU-CACHE"]
    if any(k in q_lower for k in ["bracket", "parenthes", "valid syntax", "stack", "dsl"]):
        return _CHALLENGE_CATALOG["CHAL-002-VALID-PARENTHESES"]
    if any(k in q_lower for k in ["interval", "overlap", "schedule", "merge"]):
        return _CHALLENGE_CATALOG["CHAL-007-MERGE-INTERVALS"]
    if any(k in q_lower for k in ["anagram", "word group", "string grouping"]):
        return _CHALLENGE_CATALOG["CHAL-008-GROUP-ANAGRAMS"]
    if any(k in q_lower for k in ["top k", "frequent", "frequency", "metric aggregator"]):
        return _CHALLENGE_CATALOG["CHAL-009-TOP-K-FREQUENT"]
    if any(k in q_lower for k in ["token bucket", "rate limit", "throttle"]):
        return _CHALLENGE_CATALOG["CHAL-010-TOKEN-BUCKET"]
    if any(k in q_lower for k in ["subarray", "kadane", "contiguous", "throughput", "max sum"]):
        return _CHALLENGE_CATALOG["CHAL-003-MAX-SUBARRAY"]
    if any(k in q_lower for k in ["palindrome", "alphanumeric"]):
        return _CHALLENGE_CATALOG["CHAL-004-PALINDROME-CHECK"]
    if any(k in q_lower for k in ["binary search", "sorted array", "target index", "search"]):
        return _CHALLENGE_CATALOG["CHAL-005-BINARY-SEARCH"]
    if any(k in q_lower for k in ["two sum", "duplicate", "seen set", "ticket id"]):
        return _CHALLENGE_CATALOG["CHAL-001-TWO-SUM"]

    # 2. Role-specific catalog cycling
    if any(k in r_lower for k in ["mern", "react", "frontend", "javascript", "node"]):
        role_pool = [
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-006-LRU-CACHE",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-009-TOP-K-FREQUENT",
            "CHAL-010-TOKEN-BUCKET",
            "CHAL-003-MAX-SUBARRAY",
        ]
    elif any(k in r_lower for k in ["python", "django", "fastapi", "backend"]):
        role_pool = [
            "CHAL-006-LRU-CACHE",
            "CHAL-010-TOKEN-BUCKET",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-003-MAX-SUBARRAY",
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-009-TOP-K-FREQUENT",
        ]
    elif any(k in r_lower for k in ["java", "spring"]):
        role_pool = [
            "CHAL-005-BINARY-SEARCH",
            "CHAL-006-LRU-CACHE",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-003-MAX-SUBARRAY",
            "CHAL-010-TOKEN-BUCKET",
        ]
    elif any(k in r_lower for k in ["devops", "cloud", "sre", "infrastructure", "k8s", "kubernetes", "docker", "terraform"]):
        role_pool = [
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-009-TOP-K-FREQUENT",
            "CHAL-005-BINARY-SEARCH",
            "CHAL-006-LRU-CACHE",
            "CHAL-010-TOKEN-BUCKET",
        ]
    elif any(k in r_lower for k in ["qa", "test", "automation", "sdet"]):
        role_pool = [
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-004-PALINDROME-CHECK",
            "CHAL-005-BINARY-SEARCH",
            "CHAL-009-TOP-K-FREQUENT",
            "CHAL-007-MERGE-INTERVALS",
        ]
    elif any(k in r_lower for k in ["flutter", "mobile", "android", "ios", "react native"]):
        role_pool = [
            "CHAL-006-LRU-CACHE",
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-003-MAX-SUBARRAY",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-010-TOKEN-BUCKET",
        ]
    elif any(k in r_lower for k in ["data", "ml", "ai", "machine learning", "pipeline"]):
        role_pool = [
            "CHAL-009-TOP-K-FREQUENT",
            "CHAL-003-MAX-SUBARRAY",
            "CHAL-005-BINARY-SEARCH",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-010-TOKEN-BUCKET",
        ]
    else:
        role_pool = [
            "CHAL-006-LRU-CACHE",
            "CHAL-002-VALID-PARENTHESES",
            "CHAL-007-MERGE-INTERVALS",
            "CHAL-003-MAX-SUBARRAY",
            "CHAL-010-TOKEN-BUCKET",
            "CHAL-005-BINARY-SEARCH",
            "CHAL-009-TOP-K-FREQUENT",
        ]

    selected_id = role_pool[idx % len(role_pool)]
    return _CHALLENGE_CATALOG[selected_id]


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
