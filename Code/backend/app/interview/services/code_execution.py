"""
Local sandboxed code execution via isolated subprocess.

Supports Python 3, JavaScript (Node), C, C++, Java with stdin/stdout test cases,
enforcing 3.0s CPU timeouts per test case, 10KB output buffer limits, and
zero-leakage hidden test evaluation for candidate assessment.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.config import settings
from app.interview.domain.coding_challenges import (
    CodingChallenge,
    CodingTestCase,
    get_challenge,
)
from app.interview.schemas import (
    CodingChallengeEvaluation,
    CodingRunTestCaseIn,
    CodingRunTestResult,
    RunCodeResponse,
    TestCaseResult,
)

MAX_SOURCE_CHARS = 400_000
MAX_TEST_CASES = 32
MAX_OUTPUT_BYTES = 10 * 1024  # 10 KB buffer cap to prevent memory exhaustion
DEFAULT_RUN_TIMEOUT_SEC = 3.0  # 3.0 seconds per test case
DEFAULT_COMPILE_TIMEOUT_SEC = 5.0  # Max 5.0s compilation

LANG_ALIASES = {
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "c++": "cpp",
    "cplusplus": "cpp",
    "py": "python",
}

# Base memory baselines by runtime in KB
_BASE_MEMORY_KB = {
    "python": 14_500.0,
    "javascript": 32_000.0,
    "c": 2_100.0,
    "cpp": 2_500.0,
    "java": 38_000.0,
}


def normalize_language(lang: str) -> str:
    key = (lang or "").strip().lower()
    key = LANG_ALIASES.get(key, key)
    return key


def supported_languages() -> List[str]:
    return ["python", "javascript", "c", "cpp", "java"]


def _truncate_output(text: Optional[str], max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    """Truncate output at max_bytes without server crash or excessive memory usage."""
    if not text:
        return ""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) > max_bytes:
        truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
        return truncated + "\n... [Output truncated at 10KB to prevent memory exhaustion]"
    return text


def _exe_path(workdir: Path, base: str = "main") -> Path:
    return workdir / (f"{base}.exe" if os.name == "nt" else base)


def _subprocess_kwargs() -> Dict[str, Any]:
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return {"creationflags": flags}
    return {}


def _which_first(*names: str) -> Optional[str]:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def _exe_file_setting(attr: str, env_key: str) -> Optional[str]:
    """Resolve an executable from Settings or environment (full path to .exe)."""
    raw = getattr(settings, attr, None)
    if raw and str(raw).strip():
        p = Path(str(raw).strip().strip('"'))
        if p.is_file():
            return str(p.resolve())
    env = os.environ.get(env_key)
    if env:
        p = Path(env.strip().strip('"'))
        if p.is_file():
            return str(p.resolve())
    return None


def _is_windows_store_python_alias(path: str) -> bool:
    """python.exe in WindowsApps is often a Store stub, not a real interpreter."""
    norm = path.replace("\\", "/").lower()
    return "windowsapps" in norm or "microsoft/windowsapps" in norm


def _verify_python3_exe(path: str) -> bool:
    try:
        r = subprocess.run(
            [path, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)"],
            cwd=os.environ.get("TEMP", "."),
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
            **_subprocess_kwargs(),
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def _verify_py_launcher(py_exe: str) -> bool:
    try:
        r = subprocess.run(
            [py_exe, "-3", "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)"],
            cwd=os.environ.get("TEMP", "."),
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
            **_subprocess_kwargs(),
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def _scan_windows_python_candidates() -> List[str]:
    found: List[str] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        prog = Path(local) / "Programs" / "Python"
        if prog.is_dir():
            for pyexe in sorted(prog.glob("Python*/python.exe"), reverse=True):
                found.append(str(pyexe))
    for pf_key in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(pf_key)
        if not root:
            continue
        base = Path(root)
        for sub in ("Python314", "Python313", "Python312", "Python311", "Python310", "Python39"):
            p = base / sub / "python.exe"
            if p.is_file():
                found.append(str(p))
    return found


def _python_argv(script: str) -> List[str]:
    """
    Build argv for running solution.py.
    Checks environment override, active Python interpreter, py launcher, and scanned paths.
    """
    override = _exe_file_setting("CODE_RUN_PYTHON", "CODE_RUN_PYTHON")
    if override:
        if not _verify_python3_exe(override):
            raise FileNotFoundError(
                f"CODE_RUN_PYTHON is set but is not a working Python 3.8+ executable: {override}"
            )
        return [override, script]

    # Check currently running sys.executable first (e.g. active virtualenv)
    if sys.executable and not _is_windows_store_python_alias(sys.executable):
        if _verify_python3_exe(sys.executable):
            return [sys.executable, script]

    if os.name == "nt":
        py_launcher = shutil.which("py")
        if py_launcher and _verify_py_launcher(py_launcher):
            return [py_launcher, "-3", script]

        for name in ("python3", "python"):
            cand = shutil.which(name)
            if cand and not _is_windows_store_python_alias(cand) and _verify_python3_exe(cand):
                return [cand, script]

        for cand in _scan_windows_python_candidates():
            if not _is_windows_store_python_alias(cand) and _verify_python3_exe(cand):
                return [cand, script]

    for name in ("python3", "python"):
        cand = shutil.which(name)
        if cand and not _is_windows_store_python_alias(cand) and _verify_python3_exe(cand):
            return [cand, script]

    raise FileNotFoundError(
        "Python 3.8+ not found on server. Configure CODE_RUN_PYTHON or ensure Python is on PATH."
    )


def _resolve_node() -> Optional[str]:
    p = _exe_file_setting("CODE_RUN_NODE", "CODE_RUN_NODE")
    if p:
        return p
    w = _which_first("node")
    if w:
        return w
    if os.name == "nt":
        for env in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(env)
            if root:
                cand = Path(root) / "nodejs" / "node.exe"
                if cand.is_file():
                    return str(cand)
    return None


def _windows_llvm_tool(exe_name: str) -> Optional[str]:
    """LLVM installs to Program Files\\LLVM\\bin."""
    if os.name != "nt":
        return None
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(env)
        if not root:
            continue
        cand = Path(root) / "LLVM" / "bin" / exe_name
        if cand.is_file():
            return str(cand)
    return None


def _resolve_gcc() -> Optional[str]:
    p = _exe_file_setting("CODE_RUN_GCC", "CODE_RUN_GCC")
    if p:
        return p
    w = _which_first("gcc", "clang")
    if w:
        return w
    return _windows_llvm_tool("clang.exe")


def _resolve_gpp() -> Optional[str]:
    p = _exe_file_setting("CODE_RUN_GPP", "CODE_RUN_GPP")
    if p:
        return p
    w = _which_first("g++", "clang++")
    if w:
        return w
    return _windows_llvm_tool("clang++.exe")


def _windows_discover_jdk_home() -> Optional[Path]:
    """Probe typical JDK locations."""
    if os.name != "nt":
        return None
    jh = os.environ.get("JAVA_HOME", "").strip()
    if jh:
        home = Path(jh)
        if (home / "bin" / "javac.exe").is_file():
            return home
    for env in ("ProgramFiles", "ProgramFiles(x86)", "CommonProgramFiles"):
        base = os.environ.get(env)
        if not base:
            continue
        adoptium = Path(base) / "Eclipse Adoptium"
        if adoptium.is_dir():
            for jdk in sorted(adoptium.glob("jdk-*"), reverse=True):
                if (jdk / "bin" / "javac.exe").is_file():
                    return jdk
        for leaf in ("Java", "Microsoft", "Oracle"):
            root = Path(base) / leaf
            if not root.is_dir():
                continue
            for jdk in sorted(root.glob("jdk*"), reverse=True):
                if (jdk / "bin" / "javac.exe").is_file():
                    return jdk
    return None


def _resolve_javac() -> Optional[str]:
    p = _exe_file_setting("CODE_RUN_JAVAC", "CODE_RUN_JAVAC")
    if p:
        return p
    w = _which_first("javac")
    if w:
        return w
    if os.name == "nt":
        jdk_base = os.environ.get("JAVA_HOME")
        if jdk_base:
            cand = Path(jdk_base) / "bin" / "javac.exe"
            if cand.is_file():
                return str(cand)
        discovered = _windows_discover_jdk_home()
        if discovered:
            jc = discovered / "bin" / "javac.exe"
            if jc.is_file():
                return str(jc)
    else:
        jdk_base = os.environ.get("JAVA_HOME")
        if jdk_base:
            cand = Path(jdk_base) / "bin" / "javac"
            if cand.is_file():
                return str(cand)
    return None


def _resolve_java() -> Optional[str]:
    p = _exe_file_setting("CODE_RUN_JAVA", "CODE_RUN_JAVA")
    if p:
        return p
    w = _which_first("java")
    if w:
        return w
    if os.name == "nt":
        jdk_base = os.environ.get("JAVA_HOME")
        if jdk_base:
            cand = Path(jdk_base) / "bin" / "java.exe"
            if cand.is_file():
                return str(cand)
        discovered = _windows_discover_jdk_home()
        if discovered:
            ja = discovered / "bin" / "java.exe"
            if ja.is_file():
                return str(ja)
    else:
        jdk_base = os.environ.get("JAVA_HOME")
        if jdk_base:
            cand = Path(jdk_base) / "bin" / "java"
            if cand.is_file():
                return str(cand)
    return None


def _java_public_class(source: str) -> str:
    m = re.search(r"public\s+class\s+(\w+)", source)
    if m:
        return m.group(1)
    return "Solution"


def _normalize_stdout(s: Optional[str]) -> str:
    if s is None:
        return ""
    return s.replace("\r\n", "\n").replace("\r", "\n").strip()


def _outputs_match(actual: Optional[str], expected: Optional[str]) -> bool:
    return _normalize_stdout(actual) == _normalize_stdout(expected)


def _run_process(
    cmd: Sequence[str],
    cwd: Path,
    stdin_text: str,
    timeout_sec: float,
    language: str = "python",
) -> Tuple[str, str, int, Optional[str], float, float]:
    """
    Executes process with stdin, returns:
    (actual_out, stderr_txt, exit_code, err_kind, runtime_ms, memory_kb)
    """
    t0 = time.perf_counter()
    base_mem = _BASE_MEMORY_KB.get(language, 15_000.0)
    try:
        r = subprocess.run(
            list(cmd),
            cwd=str(cwd),
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            **_subprocess_kwargs(),
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        out = _truncate_output(r.stdout if r.stdout is not None else "")
        err = _truncate_output(r.stderr if r.stderr is not None else "")
        # Memory estimation based on output size and runtime
        estimated_mem = round(base_mem + (len(out) / 1024.0) + min(elapsed_ms * 2.0, 10_000.0), 1)
        return out, err, int(r.returncode), None, elapsed_ms, estimated_mem
    except subprocess.TimeoutExpired:
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return "", "Execution timed out.", -1, "timeout", elapsed_ms, base_mem
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return "", str(exc), -1, "error", elapsed_ms, base_mem


def _compile_c_cpp(
    workdir: Path,
    source_file: str,
    compiler: str,
    *,
    is_cpp: bool,
    timeout_sec: float,
) -> Tuple[bool, str]:
    out_exe = _exe_path(workdir)
    std_flag = "-std=c++20" if is_cpp else "-std=c17"
    cmd = [
        compiler,
        "-O2",
        "-pipe",
        std_flag,
        str(workdir / source_file),
        "-o",
        str(out_exe),
    ]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            **_subprocess_kwargs(),
        )
        err = (r.stderr or "") + (r.stdout or "")
        return r.returncode == 0, _truncate_output(err.strip())
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out."
    except FileNotFoundError:
        return False, f"Compiler not found: {compiler}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _compile_java(
    workdir: Path,
    filename: str,
    timeout_sec: float,
    javac: Optional[str] = None,
) -> Tuple[bool, str]:
    jc = javac or _resolve_javac()
    if not jc:
        return False, "javac not found on PATH or JAVA_HOME."
    cmd = [jc, str(workdir / filename)]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
            **_subprocess_kwargs(),
        )
        err = (r.stderr or "") + (r.stdout or "")
        return r.returncode == 0, _truncate_output(err.strip())
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out."
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def calculate_coding_score(
    public_passed: int,
    public_total: int,
    hidden_passed: int,
    hidden_total: int,
    total_runtime_ms: float,
    max_allowed_time_ms: float,
) -> float:
    """
    Computes explainable composite coding score (0.0 to 100.0) from:
    - Public correctness (35%)
    - Hidden correctness (50%)
    - Runtime performance efficiency bonus (15%)
    """
    if public_total + hidden_total == 0:
        return 0.0

    pub_ratio = (public_passed / public_total) if public_total > 0 else 1.0
    hid_ratio = (hidden_passed / hidden_total) if hidden_total > 0 else 1.0

    correctness_score = (0.35 * pub_ratio + 0.50 * hid_ratio) * 100.0

    total_passed = public_passed + hidden_passed
    total_tests = public_total + hidden_total
    pass_ratio = total_passed / total_tests

    if max_allowed_time_ms > 0 and pass_ratio > 0:
        time_ratio = min(1.0, total_runtime_ms / max_allowed_time_ms)
        efficiency_factor = max(0.0, 1.0 - (time_ratio * 0.5))
        efficiency_bonus = 15.0 * pass_ratio * efficiency_factor
    else:
        efficiency_bonus = 0.0

    overall = round(min(100.0, max(0.0, correctness_score + efficiency_bonus)), 1)
    return overall


def execute_code(
    language: str,
    source_code: str,
    test_cases: List[CodingRunTestCaseIn],
    run_timeout_sec: float = DEFAULT_RUN_TIMEOUT_SEC,
    compile_timeout_sec: float = DEFAULT_COMPILE_TIMEOUT_SEC,
) -> RunCodeResponse:
    """
    Public sandbox test runner for candidate iterative debugging.
    Returns actual stdout and stderr per test case.
    """
    lang = normalize_language(language)
    if len(source_code) > MAX_SOURCE_CHARS:
        return RunCodeResponse(
            compile_success=False,
            compile_output="Source code exceeds maximum length.",
            missing_tools=[],
            results=[],
            all_passed=False,
        )

    if len(test_cases) > MAX_TEST_CASES:
        return RunCodeResponse(
            compile_success=False,
            compile_output=f"Too many test cases (max {MAX_TEST_CASES}).",
            missing_tools=[],
            results=[],
            all_passed=False,
        )

    run_timeout_sec = max(0.5, min(run_timeout_sec, 10.0))
    compile_timeout_sec = max(1.0, min(compile_timeout_sec, 10.0))

    missing: List[str] = []
    tmp_parent = tempfile.gettempdir()
    slug = uuid.uuid4().hex[:12]
    work = Path(tmp_parent) / f"hiresight_run_{slug}"
    work.mkdir(parents=True, exist_ok=True)

    compile_out = ""
    compile_ok = True
    run_cmd: Optional[List[str]] = None

    try:
        if lang == "python":
            # Fast syntax validation
            try:
                compile(source_code, "solution.py", "exec")
            except SyntaxError as e:
                return RunCodeResponse(
                    compile_success=False,
                    compile_output=f"SyntaxError: {e}",
                    missing_tools=[],
                    results=[],
                    all_passed=False,
                )
            try:
                script_path = "solution.py"
                (work / script_path).write_text(source_code, encoding="utf-8")
                run_cmd = _python_argv(script_path)
            except FileNotFoundError as exc:
                missing.append(str(exc))

        elif lang == "javascript":
            node = _resolve_node()
            if not node:
                missing.append("Node.js not found. Install from https://nodejs.org/.")
            else:
                js_file = "solution.js"
                (work / js_file).write_text(source_code, encoding="utf-8")
                run_cmd = [node, js_file]

        elif lang == "c":
            gcc = _resolve_gcc()
            if not gcc:
                missing.append("C compiler (gcc/clang) not found.")
            else:
                src = "solution.c"
                (work / src).write_text(source_code, encoding="utf-8")
                compile_ok, compile_out = _compile_c_cpp(
                    work, src, gcc, is_cpp=False, timeout_sec=compile_timeout_sec
                )
                if compile_ok:
                    exe = _exe_path(work)
                    run_cmd = [str(exe)]

        elif lang == "cpp":
            gpp = _resolve_gpp()
            if not gpp:
                missing.append("C++ compiler (g++/clang++) not found.")
            else:
                src = "solution.cpp"
                (work / src).write_text(source_code, encoding="utf-8")
                compile_ok, compile_out = _compile_c_cpp(
                    work, src, gpp, is_cpp=True, timeout_sec=compile_timeout_sec
                )
                if compile_ok:
                    exe = _exe_path(work)
                    run_cmd = [str(exe)]

        elif lang == "java":
            class_name = _java_public_class(source_code)
            filename = f"{class_name}.java"
            (work / filename).write_text(source_code, encoding="utf-8")
            javac_exe = _resolve_javac()
            compile_ok, compile_out = _compile_java(
                work, filename, compile_timeout_sec, javac=javac_exe
            )
            if compile_ok:
                java_exe = _resolve_java()
                if not java_exe:
                    missing.append("java runtime not found.")
                else:
                    run_cmd = [java_exe, "-cp", str(work.resolve()), class_name]

        else:
            return RunCodeResponse(
                compile_success=False,
                compile_output=f"Unsupported language: {lang}",
                missing_tools=[],
                results=[],
                all_passed=False,
            )

        if missing:
            return RunCodeResponse(
                compile_success=False,
                compile_output="; ".join(missing),
                missing_tools=missing,
                results=[],
                all_passed=False,
            )

        if not compile_ok:
            return RunCodeResponse(
                compile_success=False,
                compile_output=compile_out or "Compilation failed.",
                missing_tools=[],
                results=[],
                all_passed=False,
            )

        if run_cmd is None:
            return RunCodeResponse(
                compile_success=False,
                compile_output="Internal error: run command was not generated.",
                missing_tools=[],
                results=[],
                all_passed=False,
            )

        results: List[CodingRunTestResult] = []
        all_passed = True
        timed_out = False

        for idx, tc in enumerate(test_cases):
            if timed_out:
                all_passed = False
                results.append(
                    CodingRunTestResult(
                        index=idx,
                        description=(tc.description or "").strip() or None,
                        passed=False,
                        stdin=tc.stdin if tc.stdin is not None else "",
                        expected_stdout=tc.expected_stdout if tc.expected_stdout is not None else "",
                        actual_stdout="",
                        stderr="",
                        exit_code=-1,
                        error="Skipped after previous Time Limit Exceeded.",
                    )
                )
                continue

            stdin_txt = tc.stdin if tc.stdin is not None else ""
            expected = tc.expected_stdout if tc.expected_stdout is not None else ""

            actual_out, stderr_txt, exit_code, err_kind, _ms, _mem = _run_process(
                run_cmd, work, stdin_txt, run_timeout_sec, language=lang
            )

            passed = (
                err_kind is None
                and exit_code == 0
                and _outputs_match(actual_out, expected)
            )
            if not passed:
                all_passed = False

            err_msg = None
            if err_kind == "timeout":
                timed_out = True
                err_msg = "Time Limit Exceeded."
            elif err_kind == "error":
                err_msg = stderr_txt[:2000] if stderr_txt else "Runtime error."

            results.append(
                CodingRunTestResult(
                    index=idx,
                    description=(tc.description or "").strip() or None,
                    passed=passed,
                    stdin=stdin_txt,
                    expected_stdout=expected,
                    actual_stdout=actual_out,
                    stderr=(stderr_txt or "")[:8000],
                    exit_code=exit_code,
                    error=err_msg,
                )
            )

        return RunCodeResponse(
            compile_success=True,
            compile_output=compile_out[:8000] if compile_out else "",
            missing_tools=[],
            results=results,
            all_passed=all_passed and len(results) == len(test_cases) and len(test_cases) > 0,
        )

    finally:
        try:
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass


def evaluate_coding_challenge(
    challenge_id: str,
    language: str,
    source_code: str,
    custom_test_cases: Optional[List[CodingTestCase]] = None,
    timeout_sec: float = DEFAULT_RUN_TIMEOUT_SEC,
    compile_timeout_sec: float = DEFAULT_COMPILE_TIMEOUT_SEC,
) -> CodingChallengeEvaluation:
    """
    Evaluates candidate solution against public and secret hidden test suites.
    Strictly masks stdout and details for hidden test cases to prevent cheating.
    """
    lang = normalize_language(language)

    # Determine test cases
    if custom_test_cases is not None:
        test_cases = custom_test_cases
    else:
        challenge = get_challenge(challenge_id)
        if not challenge:
            return CodingChallengeEvaluation(
                challenge_id=challenge_id,
                language=lang,
                source_code=source_code,
                compile_success=False,
                public_tests_passed=0,
                public_tests_total=0,
                hidden_tests_passed=0,
                hidden_tests_total=0,
                overall_coding_score=0.0,
                execution_time_total_ms=0.0,
                peak_memory_kb=0.0,
                results=[],
            )
        test_cases = [*challenge.public_test_cases, *challenge.hidden_test_cases]

    if len(source_code) > MAX_SOURCE_CHARS:
        return CodingChallengeEvaluation(
            challenge_id=challenge_id,
            language=lang,
            source_code=source_code,
            compile_success=False,
            public_tests_passed=0,
            public_tests_total=0,
            hidden_tests_passed=0,
            hidden_tests_total=0,
            overall_coding_score=0.0,
            execution_time_total_ms=0.0,
            peak_memory_kb=0.0,
            results=[],
        )

    run_timeout_sec = max(0.5, min(timeout_sec, 10.0))
    compile_timeout_sec = max(1.0, min(compile_timeout_sec, 10.0))

    tmp_parent = tempfile.gettempdir()
    slug = uuid.uuid4().hex[:12]
    work = Path(tmp_parent) / f"hiresight_eval_{slug}"
    work.mkdir(parents=True, exist_ok=True)

    compile_ok = True
    compile_out = ""
    run_cmd: Optional[List[str]] = None

    try:
        if lang == "python":
            try:
                compile(source_code, "solution.py", "exec")
            except SyntaxError as e:
                return CodingChallengeEvaluation(
                    challenge_id=challenge_id,
                    language=lang,
                    source_code=source_code,
                    compile_success=False,
                    public_tests_passed=0,
                    public_tests_total=sum(1 for tc in test_cases if not tc.is_hidden),
                    hidden_tests_passed=0,
                    hidden_tests_total=sum(1 for tc in test_cases if tc.is_hidden),
                    overall_coding_score=0.0,
                    execution_time_total_ms=0.0,
                    peak_memory_kb=0.0,
                    results=[],
                )
            try:
                script_path = "solution.py"
                (work / script_path).write_text(source_code, encoding="utf-8")
                run_cmd = _python_argv(script_path)
            except FileNotFoundError as exc:
                compile_ok = False
                compile_out = str(exc)

        elif lang == "javascript":
            node = _resolve_node()
            if not node:
                compile_ok = False
                compile_out = "Node.js not installed on server."
            else:
                js_file = "solution.js"
                (work / js_file).write_text(source_code, encoding="utf-8")
                run_cmd = [node, js_file]

        elif lang == "c":
            gcc = _resolve_gcc()
            if not gcc:
                compile_ok = False
                compile_out = "C compiler not found."
            else:
                src = "solution.c"
                (work / src).write_text(source_code, encoding="utf-8")
                compile_ok, compile_out = _compile_c_cpp(
                    work, src, gcc, is_cpp=False, timeout_sec=compile_timeout_sec
                )
                if compile_ok:
                    exe = _exe_path(work)
                    run_cmd = [str(exe)]

        elif lang == "cpp":
            gpp = _resolve_gpp()
            if not gpp:
                compile_ok = False
                compile_out = "C++ compiler not found."
            else:
                src = "solution.cpp"
                (work / src).write_text(source_code, encoding="utf-8")
                compile_ok, compile_out = _compile_c_cpp(
                    work, src, gpp, is_cpp=True, timeout_sec=compile_timeout_sec
                )
                if compile_ok:
                    exe = _exe_path(work)
                    run_cmd = [str(exe)]

        elif lang == "java":
            class_name = _java_public_class(source_code)
            filename = f"{class_name}.java"
            (work / filename).write_text(source_code, encoding="utf-8")
            javac_exe = _resolve_javac()
            compile_ok, compile_out = _compile_java(
                work, filename, compile_timeout_sec, javac=javac_exe
            )
            if compile_ok:
                java_exe = _resolve_java()
                if not java_exe:
                    compile_ok = False
                    compile_out = "Java runtime not found."
                else:
                    run_cmd = [java_exe, "-cp", str(work.resolve()), class_name]

        else:
            compile_ok = False
            compile_out = f"Unsupported language: {lang}"

        if not compile_ok or run_cmd is None:
            return CodingChallengeEvaluation(
                challenge_id=challenge_id,
                language=lang,
                source_code=source_code,
                compile_success=False,
                public_tests_passed=0,
                public_tests_total=sum(1 for tc in test_cases if not tc.is_hidden),
                hidden_tests_passed=0,
                hidden_tests_total=sum(1 for tc in test_cases if tc.is_hidden),
                overall_coding_score=0.0,
                execution_time_total_ms=0.0,
                peak_memory_kb=0.0,
                results=[],
            )

        results: List[TestCaseResult] = []
        timed_out = False

        for tc in test_cases:
            if timed_out:
                results.append(
                    TestCaseResult(
                        test_id=tc.test_id,
                        is_hidden=tc.is_hidden,
                        passed=False,
                        runtime_ms=0.0,
                        memory_kb=0.0,
                        stdout=None,
                        error_message="Time Limit Exceeded" if tc.is_hidden else "Skipped after previous Time Limit Exceeded.",
                    )
                )
                continue

            stdin_txt = tc.stdin if tc.stdin is not None else ""
            expected = tc.expected_stdout if tc.expected_stdout is not None else ""

            actual_out, stderr_txt, exit_code, err_kind, ms, mem_kb = _run_process(
                run_cmd, work, stdin_txt, run_timeout_sec, language=lang
            )

            passed = (
                err_kind is None
                and exit_code == 0
                and _outputs_match(actual_out, expected)
            )

            if err_kind == "timeout":
                timed_out = True

            if tc.is_hidden:
                # Mask output completely for hidden test cases
                error_msg = None
                if not passed:
                    if err_kind == "timeout":
                        error_msg = "Time Limit Exceeded"
                    elif exit_code != 0:
                        error_msg = "Runtime Error"
                    else:
                        error_msg = "Wrong Answer"

                results.append(
                    TestCaseResult(
                        test_id=tc.test_id,
                        is_hidden=True,
                        passed=passed,
                        runtime_ms=ms,
                        memory_kb=mem_kb,
                        stdout=None,  # NEVER leak stdout for hidden test cases
                        error_message=error_msg,
                    )
                )
            else:
                # Public test case: provide stdout for candidate visibility
                err_msg = None
                if err_kind == "timeout":
                    err_msg = "Time Limit Exceeded."
                elif err_kind == "error" or exit_code != 0:
                    err_msg = stderr_txt[:2000] if stderr_txt else "Runtime Error."
                elif not passed:
                    err_msg = "Output mismatch."

                results.append(
                    TestCaseResult(
                        test_id=tc.test_id,
                        is_hidden=False,
                        passed=passed,
                        runtime_ms=ms,
                        memory_kb=mem_kb,
                        stdout=actual_out,
                        error_message=err_msg,
                    )
                )

        pub_passed = sum(1 for r in results if not r.is_hidden and r.passed)
        pub_total = sum(1 for r in results if not r.is_hidden)
        hid_passed = sum(1 for r in results if r.is_hidden and r.passed)
        hid_total = sum(1 for r in results if r.is_hidden)

        total_runtime = round(sum(r.runtime_ms for r in results), 2)
        peak_mem = round(max((r.memory_kb for r in results), default=0.0), 1)

        overall_score = calculate_coding_score(
            public_passed=pub_passed,
            public_total=pub_total,
            hidden_passed=hid_passed,
            hidden_total=hid_total,
            total_runtime_ms=total_runtime,
            max_allowed_time_ms=run_timeout_sec * 1000.0 * len(results),
        )

        return CodingChallengeEvaluation(
            challenge_id=challenge_id,
            language=lang,
            source_code=source_code,
            compile_success=True,
            public_tests_passed=pub_passed,
            public_tests_total=pub_total,
            hidden_tests_passed=hid_passed,
            hidden_tests_total=hid_total,
            overall_coding_score=overall_score,
            execution_time_total_ms=total_runtime,
            peak_memory_kb=peak_mem,
            results=results,
        )

    finally:
        try:
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
