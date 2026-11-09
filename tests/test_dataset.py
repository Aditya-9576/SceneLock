"""Preserve the Phase 2 data and label consistency during future work."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_15_original_cases_are_present() -> None:
    data = json.loads((ROOT / "sample_inputs" / "test_cases.json").read_text(encoding="utf-8"))
    assert [c["test_id"] for c in data["cases"]] == [f"T{i:02d}" for i in range(1, 16)]


def test_previous_labels_still_pass_validator() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "evaluation" / "validate_dataset.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["error_count"] == 0


def test_baseline_is_labelled_as_non_llm() -> None:
    summary = json.loads((ROOT / "evaluation" / "baseline_summary.json").read_text())
    assert summary["not_an_llm_result"] is True
    assert summary["case_count"] == 15
