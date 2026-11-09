"""Real integration of fixture inputs -> analysis -> review -> JSON/CSV.

Test inference is explicitly stubbed with human-authored labels. No Gemini
success or semantic accuracy is implied by passing this suite.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from analyzer import SceneLockAnalyzer
from exports import CSV_FIELDS, findings_csv_bytes, review_json_bytes
from model_adapter import ModelResponseFailure
from schemas import AnalysisInput, AnalysisResult, HumanDecision, ReviewStatus
from scripts.generate_sample_exports import HumanAuthoredFixtureAdapter, selected_cases


PROJECT = Path(__file__).resolve().parents[1]
BY_CASE = {case["id"]: case for case in selected_cases()}


def analyze_fixture(case_id: str):
    case = BY_CASE[case_id]
    request = AnalysisInput.model_validate(case["input"])
    run = SceneLockAnalyzer(
        HumanAuthoredFixtureAdapter(case["expected"]), analysis_engine="synthetic_fixture"
    ).analyze_with_raw(request)
    return request, run


def csv_rows(binary: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(binary.decode("utf-8-sig"), newline="")))


def test_complete_review_pipeline_preserves_original_ai_finding() -> None:
    request, run = analyze_fixture("P5-03")
    original_finding = run.report.findings[0].model_dump(mode="json")
    original_raw = run.raw_response_text
    edited = "Arjun offers the red envelope to Meera. Film on a gentle dolly."
    decisions = {"ISSUE1": HumanDecision.DISMISS}

    exported_json = review_json_bytes(request, run.report, decisions, edited)
    exported_csv = findings_csv_bytes(request, run.report, decisions)
    result = json.loads(exported_json.decode("utf-8"))
    rows = csv_rows(exported_csv)

    assert AnalysisResult.model_validate(result["analysis"]) == run.report
    assert result["inputs"] == request.model_dump(mode="json")
    assert result["analysis"]["findings"][0] == original_finding
    assert result["analysis"]["findings"][0]["severity"] == "High"
    assert result["analysis"]["metadata"]["analysis_engine"] == "synthetic_fixture"
    assert result["review_decisions"] == [
        {"finding_id": "ISSUE1", "decision": HumanDecision.DISMISS.value}
    ]
    assert result["reviewer_edited_prompt"] == edited
    assert "review_decisions" not in result["analysis"]
    assert "reviewer_edited_prompt" not in result["analysis"]
    assert "raw_response_text" not in result  # Separate raw provider record.
    assert len(rows) == 1
    assert all(field in rows[0] for field in (
        "finding_id", "category", "status", "severity", "screenplay_evidence",
        "prompt_evidence", "explanation", "suggested_fix", "human_decision"
    ))
    assert rows[0]["status"] == "Contradicted"
    assert rows[0]["comparison_status"] == rows[0]["status"]
    assert rows[0]["human_decision"] == HumanDecision.DISMISS.value
    assert run.raw_response_text == original_raw
    assert run.report.findings[0].model_dump(mode="json") == original_finding


def test_missing_action_never_invents_prompt_evidence() -> None:
    request, run = analyze_fixture("P5-04")
    assert run.report.findings[0].comparison_status.value == "Missing"
    assert run.report.findings[0].prompt_evidence is None
    report = json.loads(review_json_bytes(request, run.report, {}, "Reviewer notes.").decode("utf-8"))
    assert report["analysis"]["findings"][0]["prompt_evidence"] is None
    rows = csv_rows(findings_csv_bytes(request, run.report, {}))
    assert rows[0]["prompt_evidence"] == ""


def test_no_findings_json_and_header_only_csv() -> None:
    request, run = analyze_fixture("P5-01")
    assert run.report.summary.overall_status == ReviewStatus.NO_SIGNIFICANT_ISSUES
    document = json.loads(review_json_bytes(request, run.report, {}, request.video_prompt))
    assert document["analysis"]["findings"] == []
    assert document["review_decisions"] == []
    assert document["analysis"]["summary"]["finding_count"] == 0
    csv_bytes = findings_csv_bytes(request, run.report, {})
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    csv_reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""))
    assert tuple(csv_reader.fieldnames) == CSV_FIELDS
    assert list(csv_reader) == []


def test_multiline_quotes_comma_hindi_roundtrip_and_separate_edit() -> None:
    request, run = analyze_fixture("P8-UNICODE")
    finding = run.report.findings[0]
    edited = 'रीमा कहती है, "रुको, अभी!"\nShe wears a red dupatta, camera close-up.'
    decisions = {finding.finding_id: HumanDecision.ACCEPT}
    json_bytes = review_json_bytes(request, run.report, decisions, edited)
    csv_bytes = findings_csv_bytes(request, run.report, decisions)

    document = json.loads(json_bytes.decode("utf-8"))
    row = csv_rows(csv_bytes)[0]
    assert document["inputs"]["screenplay_text"] == request.screenplay_text
    assert document["inputs"]["video_prompt"] == request.video_prompt
    assert document["reviewer_edited_prompt"] == edited
    assert document["analysis"]["findings"][0]["explanation"] == finding.explanation
    assert document["analysis"]["suggested_corrected_prompt"] == run.report.suggested_corrected_prompt
    assert "रुको, अभी!" in document["inputs"]["screenplay_text"]
    assert "\n" in document["inputs"]["screenplay_text"]
    assert row["explanation"] == finding.explanation
    assert "\n" in row["explanation"]
    assert "," in row["explanation"]
    assert '"रुको, अभी!"' in row["explanation"]
    assert row["screenplay_evidence"] == "लाल दुपट्टा"
    assert row["prompt_evidence"] == "blue dupatta"
    assert row["human_decision"] == HumanDecision.ACCEPT.value
    assert csv_bytes.startswith(b"\xef\xbb\xbf")


def test_default_human_decision_is_further_review() -> None:
    request, run = analyze_fixture("P5-03")
    doc = json.loads(review_json_bytes(request, run.report, {}, "User edit").decode("utf-8"))
    assert doc["review_decisions"] == [
        {"finding_id": "ISSUE1", "decision": HumanDecision.FURTHER_REVIEW.value}
    ]


def test_unknown_human_decision_cannot_tamper_with_report() -> None:
    request, run = analyze_fixture("P5-03")
    with pytest.raises(ValueError, match="outside this analysis"):
        review_json_bytes(request, run.report, {"OTHER": HumanDecision.ACCEPT}, "test")
    with pytest.raises(ValueError, match="outside this analysis"):
        findings_csv_bytes(request, run.report, {"OTHER": HumanDecision.ACCEPT})


def test_export_rejects_unrelated_screenplay_and_report() -> None:
    original_request, run = analyze_fixture("P5-03")
    wrong = original_request.model_copy(update={"screenplay_text": "A completely different story."})
    with pytest.raises(ValueError, match="not supplied"):
        review_json_bytes(wrong, run.report, {}, "test")


def test_export_rejects_mismatched_scene_identifiers() -> None:
    request, run = analyze_fixture("P8-UNICODE")
    wrong = request.model_copy(update={"episode_id": "EP-OTHER"})
    with pytest.raises(ValueError, match="metadata does not match"):
        findings_csv_bytes(wrong, run.report, {})


def test_raw_payload_mismatch_causes_failure_before_any_export() -> None:
    case = BY_CASE["P5-03"]
    request = AnalysisInput.model_validate(case["input"])
    adapter = HumanAuthoredFixtureAdapter(case["expected"])
    original = adapter.analyze

    def altered_response(submitted):
        from dataclasses import replace
        result = original(submitted)
        return replace(result, raw_response_text='{"facts": [], "findings": [], "suggested_corrected_prompt": "changed"}')

    adapter.analyze = altered_response
    with pytest.raises(ModelResponseFailure, match="evidence validation"):
        SceneLockAnalyzer(adapter).analyze_with_raw(request)


def test_generated_sample_exports_are_parseable_and_honestly_labeled() -> None:
    for case_id in BY_CASE:
        stem = f"scenelock_{case_id}_human_authored_example"
        json_path = PROJECT / "sample_exports" / f"{stem}.json"
        csv_path = PROJECT / "sample_exports" / f"{stem}.csv"
        assert json_path.exists() and csv_path.exists(), "Run scripts/generate_sample_exports.py first."
        doc = json.loads(json_path.read_text(encoding="utf-8"))
        report = AnalysisResult.model_validate(doc["analysis"])
        assert report.metadata.analysis_engine == "synthetic_fixture"
        assert report.metadata.provider == "human_authored_fixture"
        assert report.metadata.model == "not_a_gemini_result"
        assert len(csv_rows(csv_path.read_bytes())) == report.summary.finding_count


def test_csv_leading_formula_characters_are_escaped() -> None:
    request, run = analyze_fixture("P5-03")
    altered = run.report.model_copy(deep=True)
    altered.findings[0].explanation = '=HYPERLINK("https://example.invalid", "click")'
    altered.findings[0].suggested_fix = "  +SUM(1,2)"
    rows = csv_rows(findings_csv_bytes(request, altered, {}))
    assert rows[0]["explanation"].startswith("'=")
    assert rows[0]["suggested_fix"].startswith("'  +")

