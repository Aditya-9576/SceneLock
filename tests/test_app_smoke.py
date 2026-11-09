"""Streamlit UI smoke tests, run in-process without a web browser."""

import json
from pathlib import Path
from unittest.mock import Mock

import model_adapter
from streamlit.testing.v1 import AppTest

from model_adapter import GeminiSettings, RateLimitFailure
from schemas import HumanDecision, LLMAnalysisPayload
from test_semantic_engine import fake_inference


APP = Path(__file__).resolve().parents[1] / "app.py"


def click_button(app: AppTest, label: str) -> None:
    next(button for button in app.button if button.label == label).click().run()


def test_app_opens_without_api_key() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    assert any("SceneLock" in item.value for item in app.title)
    assert len(app.text_area) == 3  # screenplay, prompt, shot intent
    assert len(app.selectbox) == 2  # sample picker and shot type
    assert any(button.label == "Load Sample" for button in app.button)
    assert any(button.label == "Validate Inputs" and not button.disabled for button in app.button)
    assert any(button.label == "Analyse Prompt" and not button.disabled for button in app.button)


def test_ui_can_validate_an_unseen_input() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_area(key="screenplay_text").input("Mina opens a locked door and enters the study.")
    app.text_area(key="video_prompt").input("Mina opens the door and walks into the study.")
    app.selectbox(key="shot_type").set_value("Action shot")
    app.text_area(key="shot_intent").input("Show Mina entering the room.")
    click_button(app, "Validate Inputs")
    assert not app.exception
    assert any("inputs are valid" in item.proto.body.lower() for item in app.success)
    assert not any("finding" in item.proto.body.lower() for item in app.error)


def test_invalid_form_shows_error_not_fake_results() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    click_button(app, "Validate Inputs")
    assert not app.exception
    assert len(app.error) >= 1
    assert not any("inputs are valid" in item.proto.body.lower() for item in app.success)


def test_analysis_with_no_api_key_reports_failure_without_canned_findings() -> None:
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_area(key="screenplay_text").input("Meera secretly hides the key before turning toward Arjun.")
    app.text_area(key="video_prompt").input("Close-up of Meera's frightened face.")
    app.selectbox(key="shot_type").set_value("Character close-up")
    app.text_area(key="shot_intent").input("Show Meera's reaction after she hid the key.")
    click_button(app, "Analyse Prompt")
    assert not app.exception
    assert any("gemini api key locally" in item.proto.body.lower() for item in app.error)
    assert not any("analysis completed" in item.proto.body.lower() for item in app.success)
    assert len(app.metric) == 0
    assert not any("Download reviewed report" in exp.label for exp in app.expander)


def test_live_dashboard_and_independent_review_decision_with_mock_provider(monkeypatch) -> None:
    # This is a UI wiring test, NOT an authenticated model prediction.
    fixtures = json.loads(
        (APP.parent / "evaluation" / "phase5_contract_fixtures.json").read_text(encoding="utf-8")
    )
    case = next(row for row in fixtures["cases"] if row["id"] == "P5-03")
    payload = LLMAnalysisPayload.model_validate(case["expected"])
    mock_analyze = Mock(return_value=fake_inference(payload))
    monkeypatch.setattr(model_adapter, "load_gemini_settings", lambda **_: GeminiSettings(api_key="test-only"))
    monkeypatch.setattr(model_adapter.GeminiAdapter, "analyze", mock_analyze)

    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_area(key="screenplay_text").input(case["input"]["screenplay_text"])
    app.text_area(key="video_prompt").input(case["input"]["video_prompt"])
    app.text_area(key="shot_intent").input(case["input"]["shot_intent"])
    app.selectbox(key="shot_type").set_value(case["input"]["shot_type"])
    click_button(app, "Analyse Prompt")

    assert not app.exception
    mock_analyze.assert_called_once()
    assert any("analysis completed" in item.proto.body.lower() for item in app.success)
    assert any("Review Required" in item.proto.body for item in app.warning)
    assert {m.label: m.value for m in app.metric} == {
        "Critical issues": "1", "Warnings": "0", "Verified facts": "0", "Relevant facts": "1"
    }
    assert any("Download reviewed report" in exp.label for exp in app.expander)
    analysis_id = app.session_state["analysis_report"].metadata.analysis_id
    assert app.session_state["analysis_raw_response"] == payload.model_dump_json()
    assert any("Raw AI response" in item.value for item in app.caption)
    reviewer_key = f"decision_{analysis_id}_ISSUE1"
    app.radio(key=reviewer_key).set_value("Dismiss as Intentional").run()
    assert app.session_state["review_decisions"]["ISSUE1"] == HumanDecision.DISMISS.value
    mock_analyze.assert_called_once()  # UI review must not trigger another model call.

    # Source edits now hide old results immediately, without form submission.
    app.text_area(key="screenplay_text").input("The script has since changed.").run()
    assert len(app.metric) == 0
    assert any("inputs have changed" in item.proto.body.lower() for item in app.info)
    assert not any("Download reviewed report" in exp.label for exp in app.expander)
    # The previous raw model text is kept only until a new request/sample reset.
    # Merely editing form fields must not display it with stale findings.


def test_load_sample_populates_editable_fields_without_ai_request():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.selectbox(key="sample_choice").set_value("T03 · Handbag / purse synonym").run()
    click_button(app, "Load Sample")
    assert not app.exception
    assert "brown handbag" in app.text_area(key="screenplay_text").value
    assert "brown purse" in app.text_area(key="video_prompt").value
    assert app.selectbox(key="shot_type").value == "Character interaction"
    assert app.text_input(key="episode_id").value == "EP01"
    assert any("Sample loaded" in item.proto.body for item in app.success)
    assert len(app.metric) == 0


def test_custom_shot_requires_intent_in_visible_ui():
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    click_button(app, "Load Sample")
    app.selectbox(key="shot_type").set_value("Custom / other")
    app.text_area(key="shot_intent").input("")
    click_button(app, "Validate Inputs")
    assert not app.exception
    assert any("requires a short shot-intent" in warning.proto.body.lower() for warning in app.warning)
    assert len(app.metric) == 0


def test_live_provider_error_is_distinct_from_insufficient_context(monkeypatch):
    monkeypatch.setattr(model_adapter, "load_gemini_settings", lambda **_: GeminiSettings(api_key="test-only"))
    failed = Mock(side_effect=RateLimitFailure("Gemini rate limit reached."))
    monkeypatch.setattr(model_adapter.GeminiAdapter, "analyze", failed)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    click_button(app, "Load Sample")
    click_button(app, "Analyse Prompt")
    failed.assert_called_once()
    assert not app.exception
    assert any("rate limit" in error.proto.body.lower() for error in app.error)
    assert len(app.metric) == 0
    assert not any("Insufficient Context" in info.proto.body for info in app.info)
    assert not any("Download reviewed report" in exp.label for exp in app.expander)


def test_two_independent_review_decisions_and_prompt_edit_do_not_mutate_ai(monkeypatch):
    screenplay = "Arjun gives a red envelope to Meera. Meera wears a green scarf."
    video_prompt = "Meera gives a red envelope to Arjun. Meera wears a blue scarf."
    corrected = "Arjun gives a red envelope to Meera. Meera wears a green scarf."
    payload = LLMAnalysisPayload.model_validate({
        "facts": [
            {
                "fact_id": "F1", "category": "critical_action", "entity": "Arjun",
                "required_detail": "Arjun gives the envelope to Meera.",
                "source_evidence": "Arjun gives a red envelope to Meera",
                "comparison_status": "Contradicted", "applicability_reason": "The handover is central.",
            },
            {
                "fact_id": "F2", "category": "explicit_visual_attribute", "entity": "Meera",
                "required_detail": "Meera's scarf is green.",
                "source_evidence": "green scarf", "comparison_status": "Contradicted",
                "applicability_reason": "The scarf is visible in this shot.",
            },
        ],
        "findings": [
            {
                "finding_id": "ISSUE1", "related_fact_id": "F1", "category": "critical_action",
                "comparison_status": "Contradicted", "severity": "High",
                "screenplay_evidence": "Arjun gives a red envelope to Meera",
                "prompt_evidence": "Meera gives a red envelope to Arjun",
                "explanation": "The handover direction was reversed.",
                "suggested_fix": "Make Arjun the giver.",
            },
            {
                "finding_id": "ISSUE2", "related_fact_id": "F2",
                "category": "explicit_visual_attribute", "comparison_status": "Contradicted",
                "severity": "Medium", "screenplay_evidence": "green scarf",
                "prompt_evidence": "blue scarf", "explanation": "The scarf color changed.",
                "suggested_fix": "Use a green scarf.",
            },
        ],
        "suggested_corrected_prompt": corrected,
    })
    mock_analyze = Mock(return_value=fake_inference(payload))
    monkeypatch.setattr(model_adapter, "load_gemini_settings", lambda **_: GeminiSettings(api_key="test-only"))
    monkeypatch.setattr(model_adapter.GeminiAdapter, "analyze", mock_analyze)

    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.text_area(key="screenplay_text").input(screenplay)
    app.text_area(key="video_prompt").input(video_prompt)
    app.selectbox(key="shot_type").set_value("Character interaction")
    click_button(app, "Analyse Prompt")
    assert not app.exception
    assert len(app.radio) == 2
    report = app.session_state["analysis_report"]
    run_id = report.metadata.analysis_id
    app.radio(key=f"decision_{run_id}_ISSUE1").set_value("Accept Suggestion").run()
    app.radio(key=f"decision_{run_id}_ISSUE2").set_value("Dismiss as Intentional").run()
    assert app.session_state["review_decisions"] == {
        "ISSUE1": HumanDecision.ACCEPT.value,
        "ISSUE2": HumanDecision.DISMISS.value,
    }
    app.text_area(key=f"edited_prompt_{run_id}").input("Reviewer edits a separate prompt.").run()
    assert app.session_state["analysis_report"].findings == report.findings
    assert app.session_state["analysis_report"].suggested_corrected_prompt == corrected
    assert app.session_state["review_decisions"]["ISSUE1"] == HumanDecision.ACCEPT.value
    mock_analyze.assert_called_once()

    # Loading a different sample clears old findings and decisions with no new AI call.
    click_button(app, "Load Sample")
    assert not app.exception
    assert len(app.metric) == 0
    assert len(app.radio) == 0
    assert "analysis_raw_response" not in app.session_state
    mock_analyze.assert_called_once()
