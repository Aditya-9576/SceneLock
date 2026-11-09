"""Opt-in archival of exact, validated model text for private evaluation.

The Streamlit UI never automatically saves user scripts or Gemini responses to
disk. A live evaluation command may explicitly call this function; every
archive is an independent, restricted-permission file and cannot be replaced.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


DEFAULT_RAW_DIR = Path(__file__).resolve().parent / "raw_outputs"
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")


def save_raw_evaluation_response(
    raw_text: str,
    *,
    case_id: str,
    analysis_id: str,
    output_dir: Path | None = None,
) -> Path:
    """Save the unaltered provider JSON as a private, exclusive file.

    Only call after normal evidence validation succeeded. `raw_text` is not
    parsed or reserialized here, so indentation, Unicode and line endings stay
    exactly as returned by the model.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("A nonempty raw model response is required.")
    for label, segment in (("case_id", case_id), ("analysis_id", analysis_id)):
        if not isinstance(segment, str) or not _SAFE_SEGMENT.fullmatch(segment):
            raise ValueError(f"Invalid {label}; only letters, numbers, underscores and hyphens.")

    directory = DEFAULT_RAW_DIR if output_dir is None else Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / f"{case_id}_{analysis_id}.json"
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(raw_text)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def save_raw_case_response(
    raw_text: str,
    *,
    case_id: str,
    output_dir: Path | None = None,
) -> Path:
    """Record untouched T01-T15/U01-U03 provider text under a stable name.

    Called *before* evidence parsing by the optional evaluation observer, so
    malformed provider JSON is still available for debugging. As a result a
    .json file is not guaranteed to parse successfully. Existing output is
    never overwritten, preventing accidental benchmark-history corruption.
    """
    if not isinstance(case_id, str) or not re.fullmatch(
        r"(?:T(?:0[1-9]|1[0-5])|U0[1-3])", case_id
    ):
        raise ValueError("Expected an evaluation ID T01-T15 or U01-U03.")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("A nonempty provider response is required.")
    directory = DEFAULT_RAW_DIR if output_dir is None else Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / f"{case_id}_response.json"
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(raw_text)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target
