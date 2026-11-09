"""Phase 6 adversarial structured-output, severity, error and export tests.

All model responses here are deliberately fabricated *test fixtures* and are
not presented as real Gemini inferences or performance measurements.
"""

from __future__ import annotations

import csv
import io
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from analyzer import SceneLockAnalyzer
from exports import CSV_FIELDS, _csv_safe, findings_csv_bytes, review_json_bytes
from model_adapter import (
    AuthenticationFailure,
    ModelResponseFailure,
    ProviderAPIError,
    RateLimitFailure,
)
from schemas import (
    AnalysisInput, AnalysisMetadata, AnalysisResult, HumanDecision, LLMAnalysisPayload,
    ReviewDecision, ReviewStatus,
)
from validators import ModelOutputValidationError, parse_model_response, validate_model_payload
from test_semantic_engine import fake_inference


DATA = json.loads(
    (Path(__file__).resolve().parents[1] / "evaluation" / "phase5_contract_fixtures.json")
    .read_text(encoding="utf-8")
)
CASES = {c["id"]: c for c in DATA["cases"]}


def checked(case_id: str, payload: dict | None = None):
    case = CASES[case_id]
    return validate_model_payload(
        payload or deepcopy(case["expected"]),
        screenplay_text=case["input"]["screenplay_text"],
        video_prompt=case["input"]["video_prompt"],
    )


def run_fixture(case_id: str) -> tuple[AnalysisInput, AnalysisResult]:
    case = CASES[case_id]
    request = AnalysisInput.model_validate(case["input"])
    payload = LLMAnalysisPayload.model_validate(case["expected"])
    provider = SimpleNamespace(analyze=lambda _: fake_inference(payload))
    return request, SceneLockAnalyzer(provider).analyze(request)


@pytest.mark.parametrize(
    "field,value",
    [
        ("fact_id", " "),
        ("source_evidence", " \n "),
        ("required_detail", ""),
        ("applicability_reason", " \t "),
        ("comparison_status", "Invented Status"),
        ("category", "unknown_category"),
    ],
)
def test_invalid_or_missing_fact_fields_fail_pydantic(field, value):
    payload = deepcopy(CASES["P5-03"]["expected"])
    payload["facts"][0][field] = value
    with pytest.raises(ValidationError):
        LLMAnalysisPayload.model_validate(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("severity", "Critical"),
        ("explanation", "  "),
        ("suggested_fix", ""),
        ("prompt_evidence", "  "),
        ("finding_id", " "),
        ("comparison_status", "Not Applicable"),
    ],
)
def test_invalid_finding_fields_fail_pydantic(field, value):
    payload = deepcopy(CASES["P5-03"]["expected"])
    payload["findings"][0][field] = value
    with pytest.raises(ValidationError):
        LLMAnalysisPayload.model_validate(payload)


def test_missing_required_fields_and_unexpected_fields_are_rejected():
    payload = deepcopy(CASES["P5-03"]["expected"])
    del payload["findings"][0]["screenplay_evidence"]
    with pytest.raises(ValidationError):
        LLMAnalysisPayload.model_validate(payload)


def test_metadata_and_final_report_require_valid_provenance_and_summary_types():
    request, report = run_fixture("P5-03")
    assert AnalysisResult.model_validate(report.model_dump()) == report
    assert report.metadata.created_at_utc.tzinfo is not None
    base_metadata = report.metadata.model_dump()
    for bad in (
        {"created_at_utc": datetime(2026, 11, 8)},
        {"duration_ms": -1},
        {"provider": " "},
        {"shot_type": "Unlisted angle"},
    ):
        with pytest.raises(ValidationError):
            AnalysisMetadata.model_validate({**base_metadata, **bad})
    report_json = report.model_dump(mode="json")
    del report_json["summary"]["critical_issue_count"]
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(report_json)
    report_json = report.model_dump(mode="json")
    report_json["summary"]["critical_issue_count"] = 25
    with pytest.raises(ValidationError, match="Summary counts/status"):
        AnalysisResult.model_validate(report_json)
    report_json = report.model_dump(mode="json")
    report_json["summary"]["overall_status"] = ReviewStatus.INSUFFICIENT_CONTEXT.value
    with pytest.raises(ValidationError, match="Summary counts/status"):
        AnalysisResult.model_validate(report_json)
    payload = deepcopy(CASES["P5-03"]["expected"])
    payload["invented_status_count"] = 99
    with pytest.raises(ValidationError):
        LLMAnalysisPayload.model_validate(payload)


@pytest.mark.parametrize(
    "bad_json",
    [
        "", "[]", "{}", "{", "null", "true", '{"facts": [], "findings": []}',
        "{} trailing text", '{"facts": NaN}', '{"facts": Infinity}',
        '{"facts": [], "facts": [], "findings": [], "suggested_corrected_prompt": "x"}',
    ],
)
def test_bad_json_never_returns_a_report(bad_json):
    case = CASES["P5-03"]
    with pytest.raises(ModelOutputValidationError):
        parse_model_response(
            bad_json,
            screenplay_text=case["input"]["screenplay_text"],
            video_prompt=case["input"]["video_prompt"],
        )


def test_nested_duplicate_json_key_is_rejected():
    raw = json.dumps(CASES["P5-03"]["expected"])
    raw = raw.replace('"fact_id": "F1"', '"fact_id": "OTHER", "fact_id": "F1"', 1)
    case = CASES["P5-03"]
    with pytest.raises(ModelOutputValidationError):
        parse_model_response(
            raw,
            screenplay_text=case["input"]["screenplay_text"],
            video_prompt=case["input"]["video_prompt"],
        )


def test_excessive_model_output_is_rejected():
    case = CASES["P5-03"]
    with pytest.raises(ModelOutputValidationError, match="size"):
        parse_model_response(
            "x" * 1_000_001,
            screenplay_text=case["input"]["screenplay_text"],
            video_prompt=case["input"]["video_prompt"],
        )
    oversized = deepcopy(case["expected"])
    oversized["facts"] = [
        {**case["expected"]["facts"][0], "fact_id": f"F{i}"} for i in range(81)
    ]
    with pytest.raises(ValidationError):
        LLMAnalysisPayload.model_validate(oversized)


@pytest.mark.parametrize(
    "mutation",
    [
        "invented_screenplay_evidence", "invented_prompt_evidence", "invented_missing_evidence",
        "invalid_related_fact", "duplicate_fact_id", "duplicate_finding_id",
        "duplicate_atomic_fact", "two_findings_for_fact", "finding_status_mismatch",
        "finding_category_mismatch", "missing_required_finding", "finding_quote_mismatch",
    ],
)
def test_relationship_and_quote_forgery_are_rejected(mutation):
    case_id = "P5-04" if mutation == "invented_missing_evidence" else "P5-03"
    payload = deepcopy(CASES[case_id]["expected"])
    fact = payload["facts"][0]
    finding = payload["findings"][0]
    if mutation == "invented_screenplay_evidence":
        fact["source_evidence"] = "an action which does not appear"
    elif mutation == "invented_prompt_evidence":
        finding["prompt_evidence"] = "an invented video-prompt quote"
    elif mutation == "invented_missing_evidence":
        finding["prompt_evidence"] = "holds the letter"
    elif mutation == "invalid_related_fact":
        finding["related_fact_id"] = "F_DOES_NOT_EXIST"
    elif mutation == "duplicate_fact_id":
        payload["facts"].append(deepcopy(fact))
    elif mutation == "duplicate_finding_id":
        payload["facts"].append({**fact, "fact_id": "F2", "required_detail": "Second independent assertion"})
        payload["findings"].append({**finding, "related_fact_id": "F2"})
    elif mutation == "duplicate_atomic_fact":
        payload["facts"].append({**fact, "fact_id": "F2"})
    elif mutation == "two_findings_for_fact":
        payload["findings"].append({**finding, "finding_id": "ISSUE2"})
    elif mutation == "finding_status_mismatch":
        finding["comparison_status"] = "Missing"
    elif mutation == "finding_category_mismatch":
        finding["category"] = "important_prop"
    elif mutation == "missing_required_finding":
        payload["findings"] = []
    elif mutation == "finding_quote_mismatch":
        finding["screenplay_evidence"] = "red envelope"
    with pytest.raises(ModelOutputValidationError):
        checked(case_id, payload)


def test_not_applicable_and_supported_cases_have_no_invented_findings():
    assert checked("P5-01").findings == []
    assert checked("P5-02").findings == []


def test_api_failures_never_become_insufficient_context():
    request = AnalysisInput.model_validate(CASES["P5-05"]["input"])
    for error in (
        AuthenticationFailure("no access"), RateLimitFailure("quota"),
        ProviderAPIError("provider down"), ModelResponseFailure("invalid JSON"),
    ):
        class FailingProvider:
            def analyze(self, request):
                raise error

        with pytest.raises(type(error)):
            SceneLockAnalyzer(FailingProvider()).analyze(request)
    _, valid_uncertain_report = run_fixture("P5-05")
    assert valid_uncertain_report.summary.overall_status == ReviewStatus.INSUFFICIENT_CONTEXT


def test_review_decision_contract_and_report_export_integrity():
    request, report = run_fixture("P5-03")
    choices = {"ISSUE1": HumanDecision.DISMISS.value}
    decoded = json.loads(review_json_bytes(request, report, choices, "Edited by reviewer").decode("utf-8"))
    assert decoded["inputs"]["screenplay_text"] == request.screenplay_text
    assert decoded["analysis"]["findings"][0]["screenplay_evidence"] == "Arjun offers the red envelope to Meera"
    assert decoded["analysis"]["summary"]["critical_issue_count"] == 1
    assert decoded["review_decisions"][0]["decision"] == HumanDecision.DISMISS.value
    assert decoded["reviewer_edited_prompt"] == "Edited by reviewer"
    assert report.suggested_corrected_prompt == "Arjun offers the red envelope to Meera."
    csv_text = findings_csv_bytes(request, report, choices).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 1
    assert rows[0]["human_decision"] == HumanDecision.DISMISS.value
    assert rows[0]["prompt_evidence"] == "Meera offers the red envelope to Arjun"


def test_empty_findings_csv_is_still_valid_and_defaults_review_are_typed():
    request, report = run_fixture("P5-01")
    assert not report.findings
    csv_text = findings_csv_bytes(request, report, {}).decode("utf-8-sig")
    assert list(csv.DictReader(io.StringIO(csv_text))) == []
    assert tuple(next(csv.reader(io.StringIO(csv_text)))) == CSV_FIELDS
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate({"finding_id": "ISSUE1", "decision": "Unapproved"})
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate({"finding_id": "ISSUE1", "unexpected": True})


def test_tampered_review_decision_summary_or_input_blocks_export():
    request, report = run_fixture("P5-03")
    with pytest.raises(ValueError, match="outside this analysis"):
        findings_csv_bytes(request, report, {"UNKNOWN_ISSUE": HumanDecision.ACCEPT.value})

    tampered_report = report.model_copy(deep=True)
    tampered_report.summary.verified_fact_count = 99
    with pytest.raises(ValueError, match="summary"):
        review_json_bytes(request, tampered_report, {}, "anything")

    different_request = request.model_copy(update={"screenplay_text": "An entirely different scene."})
    with pytest.raises(ModelOutputValidationError):
        findings_csv_bytes(different_request, report, {})


@pytest.mark.parametrize("danger", ["=1+1", "+SUM(A1)", "-2+3", "@FETCH", "\t =HYPERLINK('x')"])
def test_csv_formula_injection_is_escaped(danger):
    assert _csv_safe(danger).startswith("'")
    assert _csv_safe("कहानी और सीन") == "कहानी और सीन"
