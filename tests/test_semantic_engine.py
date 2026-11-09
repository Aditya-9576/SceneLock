"""Phase 5 deterministic pipeline tests with human-authored scenario fixtures.

These tests intentionally MOCK the model output. They verify evidence,
classification plumbing and Python counts, NOT Gemini semantic accuracy.
"""

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from analyzer import SceneLockAnalyzer
from model_adapter import InferenceMetadata, ModelInferenceResult, ModelResponseFailure
from prompts import PROMPT_VERSION, SYSTEM_INSTRUCTIONS
from schemas import AnalysisInput, LLMAnalysisPayload, ReviewStatus


FIXTURES = json.loads(
    (Path(__file__).resolve().parents[1] / "evaluation" / "phase5_contract_fixtures.json")
    .read_text(encoding="utf-8")
)["cases"]


def fake_inference(payload: LLMAnalysisPayload) -> ModelInferenceResult:
    return ModelInferenceResult(
        analysis=payload,
        metadata=InferenceMetadata(
            provider="synthetic-test-only",
            model="fixture-no-network",
            interaction_id=None,
            completed_at_utc=datetime.now(timezone.utc),
            duration_ms=7,
            attempts=1,
        ),
        raw_response_text=payload.model_dump_json(),
    )


@pytest.mark.parametrize("case", FIXTURES, ids=[item["id"] for item in FIXTURES])
def test_expected_manual_case_is_valid_and_pipeline_counts_correct(case):
    request = AnalysisInput.model_validate(case["input"])
    payload = LLMAnalysisPayload.model_validate(case["expected"])
    model = Mock()
    model.analyze.return_value = fake_inference(payload)

    report = SceneLockAnalyzer(model).analyze(request)

    model.analyze.assert_called_once_with(request)
    assert report.metadata.provider == "synthetic-test-only"
    assert report.summary.overall_status.value == case["expected_overall_status"]
    assert report.summary.extracted_fact_count == len(payload.facts)
    assert report.summary.relevant_fact_count == sum(
        fact.comparison_status.value != "Not Applicable" for fact in payload.facts
    )
    assert report.summary.verified_fact_count == sum(
        fact.comparison_status.value == "Supported" for fact in payload.facts
    )
    assert report.summary.finding_count == len(payload.findings)
    assert report.summary.critical_issue_count == sum(
        f.severity.value == "High" for f in payload.findings
    )
    assert report.summary.warning_count == sum(
        f.severity.value in {"Medium", "Low"} for f in payload.findings
    )
    assert report.suggested_corrected_prompt == case["expected"]["suggested_corrected_prompt"]


def test_meera_arjun_reaction_case_does_not_flag_out_of_scope_key_hiding():
    expected = FIXTURES[0]["expected"]
    assert expected["facts"][0]["comparison_status"] == "Not Applicable"
    assert expected["facts"][1]["comparison_status"] == "Supported"
    assert expected["findings"] == []


def test_unfamiliar_semantic_scenarios_are_present_as_manual_contracts():
    by_id = {item["id"]: item for item in FIXTURES}
    assert len(by_id) == len(FIXTURES) == 9
    assert by_id["P5-02"]["expected"]["facts"][0]["comparison_status"] == "Supported"
    assert by_id["P5-03"]["expected"]["facts"][0]["comparison_status"] == "Contradicted"
    assert by_id["P5-04"]["expected"]["findings"][0]["prompt_evidence"] is None
    assert by_id["P5-05"]["expected"]["facts"][0]["comparison_status"] == "Ambiguous"
    assert by_id["P5-07"]["input"]["screenplay_text"].startswith("रीमा")


def test_stage_instructions_contain_all_three_stages_and_non_execution_rules():
    assert PROMPT_VERSION == "scenelock-semantic-v3-phase9"
    for required in (
        "STAGE A", "STAGE B", "STAGE C", "handbag", "purse", "shot_intent",
        "Not Applicable", "Contradicted", "Ambiguous", "untrusted", "EXACT"
    ):
        assert required in SYSTEM_INSTRUCTIONS


def test_alternative_adapter_cannot_forge_nonexistent_source_evidence():
    case = FIXTURES[2]
    bad_payload = deepcopy(case["expected"])
    bad_payload["facts"][0]["source_evidence"] = "invented screenplay quotation"
    provider = SimpleNamespace(
        analyze=lambda request: fake_inference(LLMAnalysisPayload.model_validate(bad_payload))
    )
    with pytest.raises(ModelResponseFailure, match="evidence validation"):
        SceneLockAnalyzer(provider).analyze(AnalysisInput.model_validate(case["input"]))


def test_ambiguous_high_severity_is_rejected():
    case = FIXTURES[4]
    bad_payload = deepcopy(case["expected"])
    bad_payload["findings"][0]["severity"] = "High"
    provider = SimpleNamespace(
        analyze=lambda request: fake_inference(LLMAnalysisPayload.model_validate(bad_payload))
    )
    with pytest.raises(ModelResponseFailure):
        SceneLockAnalyzer(provider).analyze(AnalysisInput.model_validate(case["input"]))


def test_ambiguous_only_output_cannot_silently_change_prompt():
    case = FIXTURES[4]
    bad_payload = deepcopy(case["expected"])
    bad_payload["suggested_corrected_prompt"] = "Arjun enters wearing a green jacket."
    provider = SimpleNamespace(
        analyze=lambda request: fake_inference(LLMAnalysisPayload.model_validate(bad_payload))
    )
    with pytest.raises(ModelResponseFailure):
        SceneLockAnalyzer(provider).analyze(AnalysisInput.model_validate(case["input"]))


def test_actionable_mismatch_must_include_actual_changed_prompt():
    case = FIXTURES[5]
    bad_payload = deepcopy(case["expected"])
    bad_payload["suggested_corrected_prompt"] = case["input"]["video_prompt"]
    provider = SimpleNamespace(
        analyze=lambda request: fake_inference(LLMAnalysisPayload.model_validate(bad_payload))
    )
    with pytest.raises(ModelResponseFailure):
        SceneLockAnalyzer(provider).analyze(AnalysisInput.model_validate(case["input"]))


def test_low_severity_ambiguity_with_supported_fact_is_not_forced_to_review():
    case = FIXTURES[4]
    data = deepcopy(case["expected"])
    data["facts"].append({
        "fact_id": "F2", "category": "explicit_visual_attribute", "entity": "Arjun",
        "required_detail": "Green jacket", "source_evidence": "green jacket",
        "comparison_status": "Supported", "applicability_reason": "Visible costume",
        "uncertainty_note": None,
    })
    data["findings"][0]["severity"] = "Low"
    provider = SimpleNamespace(
        analyze=lambda request: fake_inference(LLMAnalysisPayload.model_validate(data))
    )
    report = SceneLockAnalyzer(provider).analyze(AnalysisInput.model_validate(case["input"]))
    assert report.summary.overall_status == ReviewStatus.NO_SIGNIFICANT_ISSUES
    assert report.summary.warning_count == 1
    assert report.summary.verified_fact_count == 1
