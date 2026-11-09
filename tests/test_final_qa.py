"""Independent final-acceptance checks discovered during the submission audit.

The fake LLM below only tests the real Python/Streamlit contracts. These
results MUST NOT be presented as Gemini semantic performance.
"""

import csv
from datetime import datetime, timezone
import io
import json

import pytest

from analyzer import SceneLockAnalyzer
from exports import findings_csv_bytes, review_json_bytes
from model_adapter import InferenceMetadata, ModelInferenceResult, load_gemini_settings
from schemas import AnalysisInput, LLMAnalysisPayload, ReviewStatus
from validators import InputValidationError, ModelOutputValidationError, parse_model_response, validate_input_payload


@pytest.mark.parametrize(
    "field,value",
    [
        ("screenplay_text", "..."),
        ("video_prompt", "!!!"),
        ("screenplay_text", "--- ???"),
    ],
)
def test_punctuation_only_is_not_meaningful_required_input(field: str, value: str) -> None:
    payload = {
        "screenplay_text": "Saira gasps at the flashing lights.",
        "video_prompt": "Close-up of Saira gasping.",
        "shot_type": "Character close-up",
    }
    payload[field] = value
    with pytest.raises(InputValidationError):
        validate_input_payload(payload)


def test_custom_shot_punctuation_only_intent_does_not_count_as_description() -> None:
    with pytest.raises(InputValidationError):
        validate_input_payload({
            "screenplay_text": "Saira gasps at the flashing lights.",
            "video_prompt": "Close-up of Saira gasping.",
            "shot_type": "Custom / other",
            "shot_intent": "!!!",
        })


@pytest.mark.parametrize("placeholder", ["REPLACE_WITH_YOUR_REAL_KEY", "YOUR_REAL_GEMINI_API_KEY"])
def test_deployment_docs_placeholder_is_not_treated_as_real_api_key(placeholder: str) -> None:
    settings = load_gemini_settings(environ={"GEMINI_API_KEY": placeholder}, secrets={})
    assert not settings.is_configured


def test_punctuation_quote_cannot_support_an_ai_fact() -> None:
    screenplay = "Wait... Saira drops the ring."
    prompt = "Saira drops the ring in surprise."
    raw = json.dumps({
        "facts": [{
            "fact_id": "F1", "category": "critical_action", "entity": "Saira",
            "required_detail": "Saira drops the ring", "source_evidence": "...",
            "comparison_status": "Supported", "applicability_reason": "The action is shown.",
        }],
        "findings": [], "suggested_corrected_prompt": prompt,
    })
    with pytest.raises(ModelOutputValidationError):
        parse_model_response(raw, screenplay_text=screenplay, video_prompt=prompt)


class _UnseenCloseupAdapter:
    """Return fixed EXPECTED classifications, never real Gemini predictions."""

    def analyze(self, request: AnalysisInput) -> ModelInferenceResult:
        payload = LLMAnalysisPayload.model_validate({
            "facts": [
                {
                    "fact_id": "F1", "category": "critical_action", "entity": "Saira",
                    "required_detail": "Saira hides a brass locket earlier.",
                    "source_evidence": "Saira hides a brass locket in a blue trunk",
                    "comparison_status": "Not Applicable",
                    "applicability_reason": "The close-up starts later, after the trunk was closed.",
                },
                {
                    "fact_id": "F2", "category": "critical_action", "entity": "Saira",
                    "required_detail": "Saira gasps when the siren sounds.",
                    "source_evidence": "she gasps as a distant siren sounds",
                    "comparison_status": "Supported",
                    "applicability_reason": "The close-up is specifically on Saira's later reaction.",
                },
            ],
            "findings": [],
            "suggested_corrected_prompt": request.video_prompt,
        })
        return ModelInferenceResult(
            analysis=payload,
            raw_response_text=json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
            metadata=InferenceMetadata(
                provider="mock_final_qa_only", model="manually_authored_expected_result",
                interaction_id=None, completed_at_utc=datetime.now(timezone.utc),
                duration_ms=0, attempts=1,
            ),
        )


def test_new_closeup_scope_no_false_warning_and_no_issue_exports() -> None:
    request = AnalysisInput.model_validate({
        "screenplay_text": (
            "Before midnight, Saira hides a brass locket in a blue trunk. "
            "Later, she gasps as a distant siren sounds in the hallway."
        ),
        "video_prompt": "Tight close-up on Saira gasping at the distant siren; moody side lighting.",
        "shot_type": "Character close-up",
        "shot_intent": "Show only Saira's reaction after the trunk has already been closed.",
        "scene_id": "FRESH-2026",
    })
    result = SceneLockAnalyzer(_UnseenCloseupAdapter()).analyze_with_raw(request)
    report = result.report
    assert report.summary.overall_status == ReviewStatus.NO_SIGNIFICANT_ISSUES
    assert report.summary.extracted_fact_count == 2
    assert report.summary.relevant_fact_count == 1
    assert report.summary.verified_fact_count == 1
    assert report.summary.finding_count == 0
    assert report.summary.critical_issue_count == 0
    assert report.suggested_corrected_prompt == request.video_prompt

    document = json.loads(review_json_bytes(request, report, {}, request.video_prompt))
    assert document["analysis"]["findings"] == []
    assert document["analysis"]["facts"][0]["comparison_status"] == "Not Applicable"
    assert document["review_decisions"] == []
    rows = list(csv.DictReader(io.StringIO(findings_csv_bytes(request, report, {}).decode("utf-8-sig"))))
    assert rows == []  # Header-only CSV is valid for a clean shot.
