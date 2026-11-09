"""Run SceneLock's genuine adapter over T01–T15 and three unseen pairs.

Without credentials: save an honest, machine-readable NOT RUN manifest with
all model measures null. With credentials: preserve each unedited provider
response *before* semantic validation, score only actually validated reports,
and keep manual ground truth unchanged. Never silently substitute fixtures.

Run from project root: python evaluation/run_phase9.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from analyzer import SceneLockAnalyzer  # noqa: E402
from model_adapter import GeminiAdapter, GeminiConfigurationError, ModelAdapterError, load_gemini_settings  # noqa: E402
from raw_archive import save_raw_case_response  # noqa: E402
from prompts import PROMPT_VERSION  # noqa: E402
from schemas import AnalysisInput  # noqa: E402
from evaluation.score_predictions import score_case, summarize_scored_cases  # noqa: E402
from evaluation.validate_dataset import validate as validate_original_dataset  # noqa: E402


LABEL_PATH = PROJECT / "evaluation" / "expected_labels.json"
INPUT_PATH = PROJECT / "sample_inputs" / "test_cases.json"
UNSEEN_PATH = PROJECT / "evaluation" / "unseen_phase9_cases.json"
OUTPUT_PATH = PROJECT / "evaluation" / "phase9_live_summary.json"


def _load_secrets() -> dict:
    path = PROJECT / ".streamlit" / "secrets.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _unseen_label(case: dict) -> dict:
    expected = case["expected"]
    indexed_findings = {finding["related_fact_id"]: finding for finding in expected["findings"]}
    from schemas import LLMAnalysisPayload, derive_summary

    payload = LLMAnalysisPayload.model_validate(expected)
    return {
        "test_id": case["test_id"],
        "expected_overall_status": derive_summary(payload.facts, payload.findings).overall_status.value,
        "expected_facts": [
            {
                "fact_id": fact["fact_id"],
                "category": fact["category"],
                "source_evidence": fact["source_evidence"],
                "expected_status": fact["comparison_status"],
                "expected_severity": indexed_findings.get(fact["fact_id"], {}).get("severity"),
            }
            for fact in expected["facts"]
        ],
    }


def load_cases() -> tuple[list[dict], dict[str, dict], list[dict], dict[str, dict], str]:
    quality = validate_original_dataset()
    if quality["error_count"]:
        raise ValueError("Original Phase 2 labels failed validation; no model requests may run.")
    original = json.loads(INPUT_PATH.read_text(encoding="utf-8"))["cases"]
    label_bytes = LABEL_PATH.read_bytes()
    labels = json.loads(label_bytes)["labels"]
    unseen = json.loads(UNSEEN_PATH.read_text(encoding="utf-8"))["cases"]
    expected_original_ids = [f"T{i:02d}" for i in range(1, 16)]
    ids = [case["test_id"] for case in original]
    if ids != expected_original_ids or [case["test_id"] for case in unseen] != ["U01", "U02", "U03"]:
        raise ValueError("Expected exactly the unchanged T01-T15 dataset plus three unseen cases.")
    by_label = {label["test_id"]: label for label in labels}
    if set(by_label) != set(ids):
        raise ValueError("Original labels and inputs disagree; evaluation stopped.")
    return original, by_label, unseen, {
        case["test_id"]: _unseen_label(case) for case in unseen
    }, hashlib.sha256(label_bytes).hexdigest()


def _write_result(document: dict) -> None:
    OUTPUT_PATH.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    originals, labels, unseen, unseen_labels, label_digest = load_cases()
    settings = load_gemini_settings(secrets=_load_secrets())
    total_cases = [*originals, *unseen]
    summary = {
        "evaluation_type": "phase9_actual_gemini_evaluation_only_if_authenticated",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "ground_truth_sha256": label_digest,
        "original_case_count": len(originals),
        "unseen_case_count": len(unseen),
        "model": settings.model,
        "prompt_version": PROMPT_VERSION,
        "key_configured": settings.is_configured,
        "authenticated_successful_requests": 0,
        "api_failure_count": 0,
        "validation_failure_count": 0,
        "raw_response_files_saved": 0,
        "model_issue_metrics": None,
        "unseen_holdout_metrics": None,
        "cases": [],
    }
    if not settings.is_configured:
        summary["run_status"] = "BLOCKED_NO_GEMINI_API_KEY"
        summary["cases"] = [{"test_id": case["test_id"], "status": "not_run_no_credentials"}
                            for case in total_cases]
        summary["explicitly_not_measured"] = [
            "Gemini issue-level precision and recall", "Gemini semantic equivalence accuracy",
            "Gemini false-positive rate", "Gemini shot-scope error rate",
            "Gemini evidence failures and API failures", "Gemini inference latency",
            "Any Gemini AI mistake or a model fix/retest",
        ]
        _write_result(summary)
        print("BLOCKED: No Gemini API key configured. 0/18 authenticated requests; no fabricated metrics.")
        return 2

    scored_labeled = []
    scored_unseen = []
    for case in total_cases:
        cid = case["test_id"]
        is_unseen = cid.startswith("U")
        input_fields = case["input"] if is_unseen else {
            name: case.get(name) for name in (
                "screenplay_text", "video_prompt", "shot_type", "shot_intent",
                "episode_id", "scene_id", "shot_id",
            )
        }
        request = AnalysisInput.model_validate(input_fields)
        archive_path: Path | None = None
        destination = PROJECT / "raw_outputs" / f"{cid}_response.json"
        if destination.exists():
            summary["cases"].append({
                "test_id": cid, "status": "blocked_existing_raw_output",
                "note": "Existing raw response is preserved; no duplicate request was issued.",
            })
            continue

        def capture_exact_response(raw_text: str) -> None:
            nonlocal archive_path
            archive_path = save_raw_case_response(raw_text, case_id=cid)

        analyzer = SceneLockAnalyzer(GeminiAdapter(settings, raw_response_observer=capture_exact_response))
        start = time.perf_counter()
        try:
            report = analyzer.analyze(request)
        except GeminiConfigurationError as exc:
            category = "configuration_failure"
            safe_error = str(exc)
        except ModelAdapterError as exc:
            category = "evidence_or_model_response_failure" if type(exc).__name__ == "ModelResponseFailure" else "api_failure"
            safe_error = str(exc)
        else:
            summary["authenticated_successful_requests"] += 1
            expected = unseen_labels[cid] if is_unseen else labels[cid]
            result = score_case(cid, request.screenplay_text, expected, report)
            (scored_unseen if is_unseen else scored_labeled).append(result)
            summary["cases"].append({
                "test_id": cid,
                "status": "validated_live_result",
                "observed_total_duration_ms": round((time.perf_counter() - start) * 1000),
                "raw_saved": archive_path is not None,
                "raw_file": str(archive_path.relative_to(PROJECT)) if archive_path else None,
                "score": result,
            })
            summary["raw_response_files_saved"] += int(archive_path is not None)
            continue

        if category == "evidence_or_model_response_failure":
            summary["validation_failure_count"] += 1
        else:
            summary["api_failure_count"] += 1
        summary["raw_response_files_saved"] += int(archive_path is not None)
        summary["cases"].append({
            "test_id": cid,
            "status": category,
            "error_type": category,
            "safe_error": safe_error,
            "observed_total_duration_ms": round((time.perf_counter() - start) * 1000),
            "raw_saved": archive_path is not None,
            "raw_file": str(archive_path.relative_to(PROJECT)) if archive_path else None,
        })

    summary["run_status"] = (
        "ALL_18_VALIDATED" if len(scored_labeled) == 15 and len(scored_unseen) == 3
        else "PARTIAL_OR_FAILED_GEMINI_RUN"
    )
    summary["model_issue_metrics"] = summarize_scored_cases(scored_labeled, total_labeled_cases=15)
    summary["unseen_holdout_metrics"] = summarize_scored_cases(scored_unseen, total_labeled_cases=3)
    _write_result(summary)
    print(json.dumps({
        "run_status": summary["run_status"],
        "authenticated_successful_requests": summary["authenticated_successful_requests"],
        "api_failures": summary["api_failure_count"],
        "model_validation_failures": summary["validation_failure_count"],
        "raw_responses_saved": summary["raw_response_files_saved"],
        "labeled_cases_scored": len(scored_labeled),
        "unseen_cases_scored": len(scored_unseen),
        "summary_file": str(OUTPUT_PATH.relative_to(PROJECT)),
    }, ensure_ascii=False, indent=2))
    return 0 if summary["run_status"] == "ALL_18_VALIDATED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
