"""AI Interview Platform - Modular Monolith Architecture"""

# HuggingFace Transformers defaults USE_TF=USE_TORCH=AUTO and will import TensorFlow if the
# package exists. A broken TF install then breaks `from transformers import pipeline` even for
# PyTorch-only NER. We only need Torch for resume NER; DeepFace loads TF lazily inside its calls.
import os

os.environ.setdefault("USE_TF", "0")

import pathlib


def _canonicalize_win_path(abs_path: str) -> str:
    """Match each path segment to on-disk casing (NTFS is case-insensitive, Python is not)."""
    if os.name != "nt":
        return os.path.normpath(abs_path)
    p = os.path.normpath(abs_path)
    parts = pathlib.PureWindowsPath(p).parts
    if not parts:
        return p
    cur = parts[0]
    for segment in parts[1:]:
        if segment in (".", ".."):
            cur = os.path.normpath(os.path.join(cur, segment))
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return p
        hit = next((n for n in names if n.casefold() == segment.casefold()), None)
        if hit is None:
            return p
        cur = os.path.join(cur, hit)
    return cur


def _ensure_canonical_cwd() -> None:
    """
    If the shell uses `...\\code\\...` while the repo folder on disk is `...\\Code\\...`, PyO3-based
    wheels (cryptography, pydantic-core) can be loaded twice →
    ImportError: PyO3 modules ... may only be initialized once per interpreter process.

    `chdir` to the canonical backend directory only (do not rewrite sys.path).
    """
    here = os.path.dirname(os.path.abspath(__file__))  # .../app
    backend = os.path.dirname(here)
    root = _canonicalize_win_path(backend)
    try:
        os.chdir(root)
    except OSError:
        pass


_ensure_canonical_cwd()
