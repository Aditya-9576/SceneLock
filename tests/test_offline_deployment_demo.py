"""Fallback demo must remain reviewable but unmistakably non-Gemini."""

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from exports import findings_csv_bytes, review_json_bytes
from offline_demo import load_validated_offline_demo
from schemas import HumanDecision


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_bundled_offline_example_is_evidence_validated_not_model_generated() -> None:
    request, report = load_validated_offline_demo()
    assert report.metadata.analysis_engine == "synthetic_fixture"
    assert report.metadata.provider == "human_authored_fixture"
    assert report.summary.finding_count == 1
    assert report.findings[0].comparison_status.value == "Contradicted"
    payload = json.loads(review_json_bytes(request, report, {}, report.suggested_corrected_prompt))
    assert payload["analysis"]["metadata"]["model"] == "not_a_gemini_result"
    assert len(findings_csv_bytes(request, report, {})) > 100


def test_no_key_offline_demo_supports_review_and_independent_prompt_edit(monkeypatch) -> None:
    import model_adapter
    from model_adapter import GeminiSettings

    monkeypatch.setattr(model_adapter, "load_gemini_settings", lambda **_: GeminiSettings(api_key=None))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    next(b for b in app.button if b.label == "Open Offline Demo (No Gemini)").click().run()

    assert not app.exception
    report = app.session_state["analysis_report"]
    assert report.metadata.analysis_engine == "synthetic_fixture"
    assert app.session_state["analysis_raw_response"] is None
    assert any("Offline demonstration" in warning.proto.body for warning in app.warning)
    assert any("NOT Gemini predictions" in info.proto.body for info in app.info)
    assert any("No raw Gemini response" in caption.value for caption in app.caption)
    assert any("Download reviewed report" in exp.label for exp in app.expander)
    decision_key = f"decision_{report.metadata.analysis_id}_ISSUE1"
    app.radio(key=decision_key).set_value("Accept Suggestion").run()
    assert app.session_state["review_decisions"]["ISSUE1"] == HumanDecision.ACCEPT.value
    edit_key = f"edited_prompt_{report.metadata.analysis_id}"
    app.text_area(key=edit_key).input("Human-edited demo prompt, camera pans right.").run()
    assert app.session_state[edit_key] == "Human-edited demo prompt, camera pans right."
    assert app.session_state["analysis_report"].findings == report.findings
