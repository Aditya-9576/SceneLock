"""Phase 9 runner never silently swaps a synthetic provider for Gemini."""

from __future__ import annotations

import json

from evaluation import run_phase9
from model_adapter import GeminiSettings


def test_without_credentials_writes_a_honest_not_run_manifest(tmp_path, monkeypatch) -> None:
    destination = tmp_path / "evaluation.json"
    monkeypatch.setattr(run_phase9, "OUTPUT_PATH", destination)
    monkeypatch.setattr(run_phase9, "_load_secrets", lambda: {})
    monkeypatch.setattr(
        run_phase9, "load_gemini_settings", lambda **_: GeminiSettings(api_key=None)
    )
    monkeypatch.setattr(
        run_phase9, "GeminiAdapter", lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("No model adapter should be constructed without credentials")
        )
    )

    assert run_phase9.main() == 2
    output = json.loads(destination.read_text(encoding="utf-8"))
    assert output["run_status"] == "BLOCKED_NO_GEMINI_API_KEY"
    assert output["authenticated_successful_requests"] == 0
    assert output["raw_response_files_saved"] == 0
    assert output["model_issue_metrics"] is None
    assert output["unseen_holdout_metrics"] is None
    assert len(output["cases"]) == 18
    assert all(item["status"] == "not_run_no_credentials" for item in output["cases"])


def test_unmodified_phase2_labels_and_case_order_remain_intact() -> None:
    original, labels, unseen, unseen_labels, digest = run_phase9.load_cases()
    assert [row["test_id"] for row in original] == [f"T{i:02d}" for i in range(1, 16)]
    assert set(labels) == {f"T{i:02d}" for i in range(1, 16)}
    assert [row["test_id"] for row in unseen] == ["U01", "U02", "U03"]
    assert len(unseen_labels) == 3
    assert len(digest) == 64


def test_complete_18_case_runner_wiring_with_explicit_mock_not_live_gemini(tmp_path, monkeypatch) -> None:
    """Exercises the *real* analyzer/validators/score/archive orchestration.

    No network request: provider return values here are neutral mock payloads
    specifically to verify that the runner does not accidentally skip a case.
    The test artifacts live only under pytest's temporary directory.
    """
    from datetime import datetime, timezone

    from model_adapter import InferenceMetadata, ModelInferenceResult
    from raw_archive import save_raw_case_response
    from schemas import LLMAnalysisPayload

    class ExplicitlyMockedAdapter:
        def __init__(self, settings, *, raw_response_observer):
            self.observe = raw_response_observer

        def analyze(self, request):
            payload = LLMAnalysisPayload(
                facts=[], findings=[], suggested_corrected_prompt=request.video_prompt
            )
            raw = payload.model_dump_json()
            self.observe(raw)
            return ModelInferenceResult(
                analysis=payload,
                metadata=InferenceMetadata(
                    provider="mock_test_only", model="not_gemini",
                    interaction_id=None, completed_at_utc=datetime.now(timezone.utc),
                    duration_ms=2, attempts=1,
                ),
                raw_response_text=raw,
            )

    monkeypatch.setattr(run_phase9, "PROJECT", tmp_path)
    monkeypatch.setattr(run_phase9, "OUTPUT_PATH", tmp_path / "summary.json")
    monkeypatch.setattr(run_phase9, "_load_secrets", lambda: {})
    monkeypatch.setattr(
        run_phase9, "load_gemini_settings", lambda **_: GeminiSettings(api_key="mock-only")
    )
    monkeypatch.setattr(run_phase9, "GeminiAdapter", ExplicitlyMockedAdapter)
    monkeypatch.setattr(
        run_phase9, "save_raw_case_response",
        lambda raw, *, case_id: save_raw_case_response(
            raw, case_id=case_id, output_dir=tmp_path / "raw_outputs"
        ),
    )

    assert run_phase9.main() == 0
    result = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert result["run_status"] == "ALL_18_VALIDATED"
    assert result["raw_response_files_saved"] == 18
    assert len(result["cases"]) == 18
    assert result["model_issue_metrics"]["scored_case_count"] == 15
    assert result["unseen_holdout_metrics"]["scored_case_count"] == 3
    for cid in [*[f"T{i:02d}" for i in range(1, 16)], "U01", "U02", "U03"]:
        assert (tmp_path / "raw_outputs" / f"{cid}_response.json").is_file()


def test_failure_log_is_derived_from_actual_baseline_files_not_model_fiction(tmp_path, monkeypatch) -> None:
    from evaluation import generate_failure_log

    destination = tmp_path / "failures.json"
    monkeypatch.setattr(generate_failure_log, "OUTPUT", destination)
    generate_failure_log.main()
    result = json.loads(destination.read_text(encoding="utf-8"))
    assert result["model_mistake_observed"] is False
    assert result["model_fix_retest_completed"] is False
    assert [(row["case_id"], row["observed_error"]) for row in result["observed_baseline_errors"]] == [
        ("T06", "false_positive"), ("T14", "false_negative")
    ]
    assert all(row["actual_predictor"] == "keyword_overlap_v1_not_an_LLM" for row in result["observed_baseline_errors"])


def test_real_adapter_runner_distinguishes_mock_api_and_validation_failures(tmp_path, monkeypatch) -> None:
    """Actual GeminiAdapter code, injected SDK fake. Still NOT authenticated."""
    from types import SimpleNamespace

    from google.genai import errors as genai_errors

    from model_adapter import GeminiAdapter
    from raw_archive import save_raw_case_response

    calls = 0

    def sdk_create(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return SimpleNamespace(status="completed", output_text="{broken json", id="mock-first", usage=None)
        if calls == 2:
            raise genai_errors.APIError(429, {"error": {"message": "rate limited in fake"}})
        data = json.loads(kwargs["input"])
        return SimpleNamespace(
            status="completed", id=f"mock-{calls}", model="not-gemini",
            output_text=json.dumps({
                "facts": [], "findings": [], "suggested_corrected_prompt": data["video_prompt"],
            }, ensure_ascii=False),
            usage=None,
        )

    sdk_client = SimpleNamespace(interactions=SimpleNamespace(create=sdk_create))

    def adapter_with_fake_sdk(settings, *, raw_response_observer):
        return GeminiAdapter(
            settings, client_factory=lambda: sdk_client,
            raw_response_observer=raw_response_observer, max_attempts=1,
        )

    monkeypatch.setattr(run_phase9, "PROJECT", tmp_path)
    monkeypatch.setattr(run_phase9, "OUTPUT_PATH", tmp_path / "summary.json")
    monkeypatch.setattr(run_phase9, "_load_secrets", lambda: {})
    monkeypatch.setattr(run_phase9, "load_gemini_settings", lambda **_: GeminiSettings(api_key="fake-key"))
    monkeypatch.setattr(run_phase9, "GeminiAdapter", adapter_with_fake_sdk)
    monkeypatch.setattr(
        run_phase9, "save_raw_case_response",
        lambda raw, *, case_id: save_raw_case_response(raw, case_id=case_id, output_dir=tmp_path / "raw_outputs"),
    )

    assert run_phase9.main() == 1  # Partial, accurately not a complete run.
    result = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert calls == 18
    assert result["run_status"] == "PARTIAL_OR_FAILED_GEMINI_RUN"
    assert result["validation_failure_count"] == 1
    assert result["api_failure_count"] == 1
    assert result["authenticated_successful_requests"] == 16
    assert result["raw_response_files_saved"] == 17
    assert (tmp_path / "raw_outputs" / "T01_response.json").read_text() == "{broken json"
    assert not (tmp_path / "raw_outputs" / "T02_response.json").exists()
    assert len(result["cases"]) == 18
    assert result["cases"][0]["status"] == "evidence_or_model_response_failure"
    assert result["cases"][1]["status"] == "api_failure"
    assert result["model_issue_metrics"]["scored_case_count"] == 13
    assert result["unseen_holdout_metrics"]["scored_case_count"] == 3
