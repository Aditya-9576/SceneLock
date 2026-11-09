"""Generate actual, reviewable Phase 8 example files from authored labels.

NO Gemini API requests or fabricated model measurements are made. Each file's
analysis metadata explicitly identifies its source as a synthetic fixture.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from analyzer import SceneLockAnalyzer  # noqa: E402
from exports import findings_csv_bytes, review_json_bytes  # noqa: E402
from model_adapter import InferenceMetadata, ModelInferenceResult  # noqa: E402
from schemas import AnalysisInput, HumanDecision, LLMAnalysisPayload  # noqa: E402


class HumanAuthoredFixtureAdapter:
    """Exercise the genuine validation pipeline with declared manual labels."""

    def __init__(self, expected: dict) -> None:
        self.expected = expected

    def analyze(self, request: AnalysisInput) -> ModelInferenceResult:
        payload = LLMAnalysisPayload.model_validate(self.expected)
        return ModelInferenceResult(
            analysis=payload,
            metadata=InferenceMetadata(
                provider="human_authored_fixture",
                model="not_a_gemini_result",
                interaction_id=None,
                completed_at_utc=datetime.now(timezone.utc),
                duration_ms=0,
                attempts=0,
            ),
            raw_response_text=payload.model_dump_json(),
        )


def selected_cases() -> list[dict]:
    historical = json.loads(
        (PROJECT / "evaluation" / "phase5_contract_fixtures.json").read_text(encoding="utf-8")
    )["cases"]
    identifiers = {"P5-01", "P5-03", "P5-04"}
    picked = [row for row in historical if row["id"] in identifiers]
    picked.append(json.loads((PROJECT / "sample_inputs" / "export_unicode_case.json").read_text(encoding="utf-8")))
    return picked


def main() -> int:
    directory = PROJECT / "sample_exports"
    directory.mkdir(parents=True, exist_ok=True)
    for case in selected_cases():
        request = AnalysisInput.model_validate(case["input"])
        run = SceneLockAnalyzer(
            HumanAuthoredFixtureAdapter(case["expected"]), analysis_engine="synthetic_fixture"
        ).analyze_with_raw(request)
        report = run.report

        reviewer_choices = {}
        edited_prompt = report.suggested_corrected_prompt
        if case["id"] == "P5-03":
            reviewer_choices = {"ISSUE1": HumanDecision.ACCEPT}
            edited_prompt = "Arjun offers the red envelope to Meera. Camera pans slightly."
        elif case["id"] == "P8-UNICODE":
            reviewer_choices = {"ISSUE1": HumanDecision.FURTHER_REVIEW}
            edited_prompt = (
                'रीमा कहती है, "रुको, अभी!"\n'
                'She wears a red dupatta, soft light; note: re-check costume, framing.'
            )
        elif case["id"] == "P5-04":
            reviewer_choices = {"ISSUE1": HumanDecision.DISMISS}

        stem = f"scenelock_{case['id']}_human_authored_example"
        json_path = directory / f"{stem}.json"
        csv_path = directory / f"{stem}.csv"
        json_path.write_bytes(review_json_bytes(request, report, reviewer_choices, edited_prompt))
        csv_path.write_bytes(findings_csv_bytes(request, report, reviewer_choices))
        print(f"CREATED: {json_path.name} and {csv_path.name} ({len(report.findings)} findings)")
    print("Source: human-authored fixtures; no Gemini request or measured accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
