"""Optional Phase 5 end-to-end semantic smoke test (genuine Gemini request).

No key => clear NOT RUN / exit 2. Uses one original synthetic fixture per run.
Example: python scripts/live_semantic_smoke.py --case P5-03
No benchmark or model accuracy is claimed from this one-shot diagnostic.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from analyzer import SceneLockAnalyzer  # noqa: E402
from model_adapter import (  # noqa: E402
    GeminiAdapter,
    GeminiConfigurationError,
    ModelAdapterError,
    load_gemini_settings,
)
from schemas import AnalysisInput  # noqa: E402
from raw_archive import save_raw_evaluation_response  # noqa: E402


def local_secrets() -> dict:
    path = PROJECT / ".streamlit" / "secrets.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def main() -> int:
    cases = json.loads(
        (PROJECT / "evaluation" / "phase5_contract_fixtures.json").read_text(encoding="utf-8")
    )["cases"]
    by_id = {case["id"]: case for case in cases}
    parser = argparse.ArgumentParser(description="Run one genuine Gemini semantic SceneLock request")
    parser.add_argument("--case", choices=list(by_id), default="P5-01")
    args = parser.parse_args()

    settings = load_gemini_settings(secrets=local_secrets())
    if not settings.is_configured:
        print("PHASE 5 LIVE SEMANTIC TEST NOT RUN: no Gemini key configured; no authenticated request.")
        return 2

    case = by_id[args.case]
    try:
        run = SceneLockAnalyzer(GeminiAdapter(settings)).analyze_with_raw(
            AnalysisInput.model_validate(case["input"])
        )
    except (GeminiConfigurationError, ModelAdapterError) as exc:
        print(f"PHASE 5 LIVE SEMANTIC TEST FAILED: {type(exc).__name__}: {exc}")
        return 1

    report = run.report
    raw_path = save_raw_evaluation_response(
        run.raw_response_text, case_id=case["id"], analysis_id=report.metadata.analysis_id
    )
    print(json.dumps({
        "authenticated_live_model_request_succeeded": True,
        "case": case["id"],
        "model": report.metadata.model,
        "inference_duration_ms": report.metadata.duration_ms,
        "reported_review_status": report.summary.overall_status.value,
        "human_authored_expected_review_status": case["expected_overall_status"],
        "returned_fact_statuses": [f.comparison_status.value for f in report.facts],
        "finding_count": report.summary.finding_count,
        "raw_response_saved_privately_at": str(raw_path),
        "note": "One authenticated sample diagnostic, not benchmark precision or recall.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
