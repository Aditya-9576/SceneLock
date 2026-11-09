"""Local deployment workflow using a completely new, untrained screenplay.

The SDK is mocked because authenticated Gemini access is not configured.
This proves application wiring, not the Gemini model's ability to detect it.
"""

import csv
import io
import json
from pathlib import Path
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

import model_adapter
from exports import findings_csv_bytes, review_json_bytes
from model_adapter import GeminiSettings
from schemas import HumanDecision, LLMAnalysisPayload
from test_semantic_engine import fake_inference
from validators import validate_input_payload


APP = Path(__file__).resolve().parents[1] / "app.py"
NEW_SCREENPLAY = "Kavya slips a silver compass into a red backpack before crossing the bridge."
NEW_PROMPT = "Kavya tucks a silver compass into a blue backpack, then crosses the bridge. Golden backlight."
NEW_INTENT = "Show the compass being stowed in Kavya's red backpack before she crosses the bridge."


def test_fresh_review_round_trip_through_actual_streamlit_and_export_code(monkeypatch) -> None:
    response = LLMAnalysisPayload.model_validate({
        "facts": [
            {
                "fact_id": "F1", "category": "explicit_visual_attribute", "entity": "Kavya",
                "required_detail": "Kavya has a red backpack.", "source_evidence": "red backpack",
                "comparison_status": "Contradicted", "applicability_reason": "The backpack is clearly shown.",
            },
            {
                "fact_id": "F2", "category": "critical_action", "entity": "Kavya",
                "required_detail": "Kavya stows the compass before crossing.",
                "source_evidence": "Kavya slips a silver compass",
                "comparison_status": "Supported", "applicability_reason": "The prompt keeps the stowing action.",
            },
        ],
        "findings": [
            {
                "finding_id": "ISSUE1", "related_fact_id": "F1",
                "category": "explicit_visual_attribute", "comparison_status": "Contradicted",
                "severity": "Medium", "screenplay_evidence": "red backpack",
                "prompt_evidence": "blue backpack", "explanation": "Kavya's visible backpack color was changed.",
                "suggested_fix": "Change blue backpack to red backpack while preserving the light.",
            }
        ],
        "suggested_corrected_prompt": (
            "Kavya tucks a silver compass into a red backpack, then crosses the bridge. Golden backlight."
        ),
    })
    provider = Mock(return_value=fake_inference(response))
    monkeypatch.setattr(model_adapter, "load_gemini_settings", lambda **_: GeminiSettings(api_key="fake-unit-test-only"))
    monkeypatch.setattr(model_adapter.GeminiAdapter, "analyze", provider)

    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_area(key="screenplay_text").input(NEW_SCREENPLAY)
    app.text_area(key="video_prompt").input(NEW_PROMPT)
    app.text_area(key="shot_intent").input(NEW_INTENT)
    app.selectbox(key="shot_type").set_value("Action shot")
    next(button for button in app.button if button.label == "Analyse Prompt").click().run()

    assert not app.exception
    provider.assert_called_once()
    report = app.session_state["analysis_report"]
    assert report.summary.finding_count == 1
    assert report.findings[0].prompt_evidence == "blue backpack"
    assert report.summary.warning_count == 1
    analysis_id = report.metadata.analysis_id
    app.radio(key=f"decision_{analysis_id}_ISSUE1").set_value("Accept Suggestion").run()
    edited = "Kavya stows the compass in the red backpack, then walks across the bridge."
    app.text_area(key=f"edited_prompt_{analysis_id}").input(edited).run()

    request = validate_input_payload({
        "screenplay_text": NEW_SCREENPLAY, "video_prompt": NEW_PROMPT,
        "shot_type": "Action shot", "shot_intent": NEW_INTENT,
    })
    json_result = json.loads(review_json_bytes(request, report, app.session_state["review_decisions"], edited))
    csv_result = list(csv.DictReader(io.StringIO(
        findings_csv_bytes(request, report, app.session_state["review_decisions"]).decode("utf-8-sig")
    )))
    assert json_result["inputs"]["video_prompt"] == NEW_PROMPT
    assert json_result["reviewer_edited_prompt"] == edited
    assert json_result["analysis"]["findings"][0]["prompt_evidence"] == "blue backpack"
    assert csv_result[0]["human_decision"] == HumanDecision.ACCEPT.value
    assert csv_result[0]["status"] == "Contradicted"
    provider.assert_called_once()  # Human changes must not requery the model.
