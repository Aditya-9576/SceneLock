"""A clearly labeled, manually authored fallback for public demonstrations.

This is never an LLM prediction or a substitute for an authenticated analysis.
The bundled example still passes the same Python evidence and export checks.
"""

from __future__ import annotations

import json
from pathlib import Path

from exports import review_json_bytes
from schemas import AnalysisInput, AnalysisResult


DEMO_PATH = (
    Path(__file__).resolve().parent / "sample_exports"
    / "scenelock_P5-03_human_authored_example.json"
)


def load_validated_offline_demo() -> tuple[AnalysisInput, AnalysisResult]:
    """Return a safe, reproducible fixture and independently validated report."""
    document = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
    request = AnalysisInput.model_validate(document["inputs"])
    report = AnalysisResult.model_validate(document["analysis"])
    if (
        report.metadata.analysis_engine != "synthetic_fixture"
        or report.metadata.provider != "human_authored_fixture"
        or report.metadata.model != "not_a_gemini_result"
    ):
        raise ValueError("Offline demonstration must never impersonate Gemini output.")
    # Recheck evidence, cross-references, scene scope and Python summary using
    # the exact same export boundary as a live analysis.
    review_json_bytes(request, report, {}, report.suggested_corrected_prompt)
    return request, report
