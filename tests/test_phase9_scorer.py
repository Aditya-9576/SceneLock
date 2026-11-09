"""Honest partial-label evaluation, using fixtures solely to test scoring."""

from __future__ import annotations

import json
from pathlib import Path

from analyzer import SceneLockAnalyzer
from evaluation.run_phase9 import _unseen_label
from evaluation.score_predictions import align_labeled_facts, score_case, summarize_scored_cases
from schemas import AnalysisInput, ComparisonStatus
from scripts.generate_sample_exports import HumanAuthoredFixtureAdapter


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    row["id"]: row for row in json.loads(
        (ROOT / "evaluation" / "phase5_contract_fixtures.json").read_text(encoding="utf-8")
    )["cases"]
}


def fixture_report(case_id: str):
    case = FIXTURES[case_id]
    request = AnalysisInput.model_validate(case["input"])
    report = SceneLockAnalyzer(
        HumanAuthoredFixtureAdapter(case["expected"]), analysis_engine="synthetic_fixture"
    ).analyze(request)
    return request, report


def fixture_label(case_id: str) -> dict:
    case = FIXTURES[case_id]
    issues = {f["related_fact_id"]: f for f in case["expected"]["findings"]}
    return {
        "test_id": case_id,
        "expected_overall_status": case["expected_overall_status"],
        "expected_facts": [
            {
                "fact_id": f["fact_id"], "category": f["category"],
                "source_evidence": f["source_evidence"],
                "expected_status": f["comparison_status"],
                "expected_severity": issues.get(f["fact_id"], {}).get("severity"),
            }
            for f in case["expected"]["facts"]
        ],
    }


def test_adjudicable_confirmed_issue_detected_by_aligned_evidence() -> None:
    request, report = fixture_report("P5-03")
    result = score_case("P5-03", request.screenplay_text, fixture_label("P5-03"), report)
    assert result["issue_confusion_on_adjudicable_facts"] == {"TP": 1, "FP": 0, "FN": 0}
    assert result["status_mismatches"] == []
    assert result["shot_scope_mistakes"] == 0
    aggregate = summarize_scored_cases([result], total_labeled_cases=15)
    assert aggregate["issue_precision_on_adjudicable_facts"] == 1
    assert aggregate["issue_recall_on_adjudicable_facts"] == 1
    assert aggregate["coverage"] == 1 / 15


def test_supported_and_not_applicable_are_not_false_positives() -> None:
    request, report = fixture_report("P5-01")
    result = score_case("P5-01", request.screenplay_text, fixture_label("P5-01"), report)
    assert result["issue_confusion_on_adjudicable_facts"] == {"TP": 0, "FP": 0, "FN": 0}
    assert result["correct_supported_matches"] == 1
    assert result["shot_scope_mistakes"] == 0


def test_ambiguous_character_is_not_counted_as_proven_issue() -> None:
    request, report = fixture_report("P5-05")
    result = score_case("P5-05", request.screenplay_text, fixture_label("P5-05"), report)
    assert result["issue_confusion_on_adjudicable_facts"] == {"TP": 0, "FP": 0, "FN": 0}
    assert result["correct_ambiguous_matches"] == 1
    assert result["expected_ambiguous_facts"] == 1


def test_missing_predicted_issue_is_false_negative_even_without_fact_alignment() -> None:
    request, report = fixture_report("P5-01")
    gold = fixture_label("P5-03")
    result = score_case("P5-03", "Arjun offers the red envelope to Meera.", gold, report)
    assert result["issue_confusion_on_adjudicable_facts"] == {"TP": 0, "FP": 0, "FN": 1}


def test_unlabeled_model_finding_remains_unadjudicated_not_automatic_fp() -> None:
    request, report = fixture_report("P5-03")
    gold = fixture_label("P5-03")
    gold["expected_facts"] = []  # A deliberately incomplete annotation file.
    result = score_case("P5-03", request.screenplay_text, gold, report)
    assert result["issue_confusion_on_adjudicable_facts"]["FP"] == 0
    assert result["unadjudicated_predicted_finding_ids"] == ["ISSUE1"]


def test_missing_credential_scoring_has_null_precision_and_recall() -> None:
    result = summarize_scored_cases([], total_labeled_cases=15)
    assert result["scored_case_count"] == 0
    assert result["coverage"] == 0
    assert result["issue_precision_on_adjudicable_facts"] is None
    assert result["issue_recall_on_adjudicable_facts"] is None
    assert result["latency_ms"]["mean"] is None


def test_unseen_manual_labels_match_input_evidence_and_are_separate() -> None:
    from validators import validate_model_payload
    from schemas import LLMAnalysisPayload

    unseen = json.loads((ROOT / "evaluation" / "unseen_phase9_cases.json").read_text(encoding="utf-8"))
    assert [item["test_id"] for item in unseen["cases"]] == ["U01", "U02", "U03"]
    for case in unseen["cases"]:
        request = AnalysisInput.model_validate(case["input"])
        model_payload = validate_model_payload(
            LLMAnalysisPayload.model_validate(case["expected"]),
            screenplay_text=request.screenplay_text,
            video_prompt=request.video_prompt,
        )
        assert model_payload.facts
        assert _unseen_label(case)["expected_facts"]
    assert unseen["cases"][2]["expected"]["facts"][0]["comparison_status"] == ComparisonStatus.AMBIGUOUS.value


def test_evidence_alignment_respects_category_and_source_positions() -> None:
    request, report = fixture_report("P5-03")
    labels = fixture_label("P5-03")["expected_facts"]
    matching, leftover = align_labeled_facts(request.screenplay_text, labels, report)
    assert matching == {0: 0}
    assert leftover == []
    labels[0]["category"] = "important_prop"
    matching, leftover = align_labeled_facts(request.screenplay_text, labels, report)
    assert matching == {}
    assert leftover == [0]

