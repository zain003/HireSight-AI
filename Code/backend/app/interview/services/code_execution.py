"""
Local code execution via subprocess (no Docker / Judge0).

Supports Python, JavaScript (Node), C, C++, Java with stdin/stdout test cases.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.config import settings
from app.interview.schemas import (
    CodingRunTestCaseIn,
    CodingRunTestResult,
    RunCodeResponse,
)

MAX_SOURCE_CHARS = 400_000
MAX_TEST_CASES = 24
DEFAULT_RUN_TIMEOUT_SEC = 10.0
DEFAULT_COMPILE_TIMEOUT_SEC = 20.0

LANG_ALIASES = {
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "c++": "cpp",
    "cplusplus": "cpp",
}


def normalize_language(lang: str) -> str:
    key = (lang or "").strip().lower()
    key = LANG_ALIASES.get(key, key)
    return key


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
            timeout=15,
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
            timeout=15,
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
        for sub in ("Python312", "Python311", "Python310", "Python39"):
            p = base / sub / "python.exe"
            if p.is_file():
                found.append(str(p))
    return found


def _python_argv(script: str) -> List[str]:
    """
    Build argv for running solution.py. On Windows, prefer `py -3` before bare `python`
    (avoids Microsoft Store aliases). Optional CODE_RUN_PYTHON / .env override wins.
    """
    override = _exe_file_setting("CODE_RUN_PYTHON", "CODE_RUN_PYTHON")
    if override:
        if not _verify_python3_exe(override):
            raise FileNotFoundError(
                f"CODE_RUN_PYTHON is set but is not a working Python 3.8+ executable: {override}"
            )
        return [override, script]

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
        "Python 3.8+ not found. On Windows: install from https://www.python.org/downloads/, "
        "enable 'Add python.exe to PATH', disable Settings → Apps → Advanced → App execution aliases "
        "for python.exe / python3.exe (they point to the Microsoft Store), or set CODE_RUN_PYTHON "
        "in backend/.env to the full path of python.exe."
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
    """LLVM winget installs to Program Files\\LLVM\\bin but often does not add PATH."""
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
    """
    Temurin/other JDK installers often omit JAVA_HOME and javac from PATH.
    Probe typical layout: Eclipse Adoptium\\jdk-*\\bin\\javac.exe
    """
    if os.name != "nt":
        return None
    jh = os.environ.get("JAVA_HOME", "").strip()
    if jh:
        home = Path(jh)
        if (home / "bin" / "javac.exe").is_file():
            return home
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env)
        if not base:
            continue
        adoptium = Path(base) / "Eclipse Adoptium"
        if adoptium.is_dir():
            for jdk in sorted(adoptium.glob("jdk-*"), reverse=True):
                if (jdk / "bin" / "javac.exe").is_file():
                    return jdk
        for leaf in ("Java", "Microsoft"):
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
    return "Main"


def _normalize_stdout(s: str) -> str:
    if s is None:
        return ""
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _outputs_match(actual: str, expected: str) -> bool:
    return _normalize_stdout(actual) == _normalize_stdout(expected)


def _run_process(
    cmd: Sequence[str],
    cwd: Path,
    stdin_text: str,
    timeout_sec: float,
) -> Tuple[str, str, int, Optional[str]]:
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
        out = r.stdout if r.stdout is not None else ""
        err = r.stderr if r.stderr is not None else ""
        return out, err, int(r.returncode), None
    except subprocess.TimeoutExpired:
        return "", "Execution timed out.", -1, "timeout"
    except Exception as exc:  # noqa: BLE001
        return "", str(exc), -1, "error"


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
        return r.returncode == 0, err.strip()
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
        return False, "javac not found on PATH (install a JDK) or set CODE_RUN_JAVAC / JAVA_HOME."
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
        return r.returncode == 0, err.strip()
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out."
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def execute_code(
    language: str,
    source_code: str,
    test_cases: List[CodingRunTestCaseIn],
    run_timeout_sec: float = DEFAULT_RUN_TIMEOUT_SEC,
    compile_timeout_sec: float = DEFAULT_COMPILE_TIMEOUT_SEC,
) -> RunCodeResponse:
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

    run_timeout_sec = max(1.0, min(run_timeout_sec, 60.0))
    compile_timeout_sec = max(1.0, min(compile_timeout_sec, 60.0))

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
            try:
                script_path = "solution.py"
                (work / script_path).write_text(source_code, encoding="utf-8")
                run_cmd = _python_argv(script_path)
            except FileNotFoundError as exc:
                missing.append(str(exc))

        elif lang == "javascript":
            node = _resolve_node()
            if not node:
                missing.append(
                    "Node.js not found. Install from https://nodejs.org/ or set CODE_RUN_NODE to node.exe."
                )
            else:
                js_file = "solution.js"
                (work / js_file).write_text(source_code, encoding="utf-8")
                run_cmd = [node, js_file]

        elif lang == "c":
            gcc = _resolve_gcc()
            if not gcc:
                missing.append(
                    "C compiler (gcc/clang) not found. Install MinGW/LLVM or set CODE_RUN_GCC."
                )
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
                missing.append(
                    "C++ compiler (g++/clang++) not found. Install MinGW/LLVM or set CODE_RUN_GPP."
                )
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
                    missing.append(
                        "java runtime not found. Install a JDK or set JAVA_HOME / CODE_RUN_JAVA."
                    )
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
                compile_output="Internal error: no run command.",
                missing_tools=[],
                results=[],
                all_passed=False,
            )

        results: List[CodingRunTestResult] = []
        all_passed = True

        for idx, tc in enumerate(test_cases):
            stdin_txt = tc.stdin if tc.stdin is not None else ""
            expected = tc.expected_stdout if tc.expected_stdout is not None else ""

            actual_out, stderr_txt, exit_code, err_kind = _run_process(
                run_cmd, work, stdin_txt, run_timeout_sec
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
                err_msg = "Time limit exceeded."
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


def supported_languages() -> List[str]:
    return ["python", "javascript", "c", "cpp", "java"]
