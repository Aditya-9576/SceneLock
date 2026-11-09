"""Optional genuine authenticated smoke test for SceneLock's Phase 4 backend.

Only runs when GEMINI_API_KEY/GOOGLE_API_KEY or local Streamlit secrets exist.
Never prints a key. No outputs are represented as LLM results if skipped.

Run from project root:
    python scripts/live_gemini_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from model_adapter import ModelAdapterError, analyze_with_model, load_gemini_settings  # noqa: E402


def read_optional_secrets() -> dict:
    path = PROJECT / ".streamlit" / "secrets.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def main() -> int:
    settings = load_gemini_settings(secrets=read_optional_secrets(), environ=os.environ)
    if not settings.is_configured:
        print("LIVE GEMINI TEST NOT RUN: no API key configured. No authenticated request was made.")
        return 2

    try:
        result = analyze_with_model(
            "Tara waits at the station wearing a red dress.",
            "Tara waits at the station wearing a blue dress.",
            "Character interaction",
            "Show Tara at the station in her scripted outfit.",
            secrets=read_optional_secrets(),
        )
    except ModelAdapterError as exc:
        print(f"LIVE GEMINI TEST FAILED: {type(exc).__name__}: {exc}")
        return 1

    print(json.dumps({
        "live_authenticated_request_succeeded": True,
        "model": result.metadata.model,
        "interaction_id": result.metadata.interaction_id,
        "duration_ms": result.metadata.duration_ms,
        "attempts": result.metadata.attempts,
        "fact_count": len(result.analysis.facts),
        "finding_count": len(result.analysis.findings),
        "total_tokens": result.metadata.total_tokens,
        "note": "Schema/evidence parsing succeeded; this is not an accuracy score.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
