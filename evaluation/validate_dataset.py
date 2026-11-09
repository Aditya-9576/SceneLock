"""Validate SceneLock Phase 2 synthetic inputs and manually authored labels.

Run from any directory:
    python evaluation/validate_dataset.py

No AI service or third-party library is required.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "sample_inputs" / "test_cases.json"
LABELS = ROOT / "evaluation" / "expected_labels.json"

SHOT_TYPES = {
    "Full dramatic beat",
    "Establishing / wide shot",
    "Character interaction",
    "Action shot",
    "Character close-up",
    "Prop close-up",
    "Custom / other",
}
CATEGORIES = {
    "critical_action",
    "important_prop",
    "character_identity_position",
    "explicit_visual_attribute",
}
STATUSES = {"Supported", "Contradicted", "Missing", "Ambiguous", "Not Applicable"}
SEVERITIES = {"High", "Medium", "Low"}
OUTCOMES = {
    "Review Required",
    "No Significant Issues Detected",
    "Insufficient Context",
}
EXPECTED_IDS = {f"T{i:02d}" for i in range(1, 16)}


def derive_status(facts: list[dict]) -> str:
    relevant = [f for f in facts if f["expected_status"] != "Not Applicable"]
    if not relevant or all(f["expected_status"] == "Ambiguous" for f in relevant):
        return "Insufficient Context"
    if any(
        f["expected_severity"] in {"High", "Medium"}
        for f in relevant
        if f["expected_status"] in {"Contradicted", "Missing", "Ambiguous"}
    ):
        return "Review Required"
    return "No Significant Issues Detected"


def has_confirmed_issue(facts: list[dict]) -> bool:
    """Binary gold label for comparing with the deliberately simple baseline."""
    return any(
        f["expected_status"] in {"Contradicted", "Missing"}
        and f["expected_severity"] in {"High", "Medium"}
        for f in facts
    )


def validate() -> dict:
    data = json.loads(INPUTS.read_text(encoding="utf-8"))
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    errors: list[str] = []

    if data.get("dataset_id") != labels.get("dataset_id"):
        errors.append("Inputs and labels have different dataset_id values")

    cases = data.get("cases", [])
    annotations = labels.get("labels", [])
    case_ids = [c.get("test_id") for c in cases]
    label_ids = [c.get("test_id") for c in annotations]
    if set(case_ids) != EXPECTED_IDS or len(case_ids) != 15 or len(set(case_ids)) != 15:
        errors.append("Inputs must contain exactly T01-T15 once each")
    if set(label_ids) != EXPECTED_IDS or len(label_ids) != 15 or len(set(label_ids)) != 15:
        errors.append("Labels must contain exactly T01-T15 once each")

    by_id = {c["test_id"]: c for c in cases if c.get("test_id")}
    statuses = Counter()
    categories = Counter()
    outcomes = Counter()
    demo_ids = []
    confirmed_issues = 0
    facts_count = 0

    for c in cases:
        test_id = c.get("test_id", "UNKNOWN")
        if c.get("shot_type") not in SHOT_TYPES:
            errors.append(f"{test_id}: invalid shot type")
        for field in ("screenplay_text", "video_prompt", "shot_intent"):
            if not isinstance(c.get(field), str) or not c[field].strip():
                errors.append(f"{test_id}: missing {field}")
        if len(c.get("screenplay_text", "")) > 8000:
            errors.append(f"{test_id}: screenplay exceeds MVP length limit")
        if len(c.get("video_prompt", "")) > 4000:
            errors.append(f"{test_id}: video prompt exceeds MVP length limit")
        if len(c.get("shot_intent", "")) > 500:
            errors.append(f"{test_id}: shot intent exceeds MVP length limit")
        if c.get("demo_candidate"):
            demo_ids.append(test_id)

    for annotation in annotations:
        test_id = annotation.get("test_id", "UNKNOWN")
        if test_id not in by_id:
            errors.append(f"{test_id}: missing matching input")
            continue
        case = by_id[test_id]
        facts = annotation.get("expected_facts", [])
        if not facts:
            errors.append(f"{test_id}: no manually labeled facts")
        if annotation.get("expected_overall_status") not in OUTCOMES:
            errors.append(f"{test_id}: invalid overall status")
        if annotation.get("expected_overall_status") != derive_status(facts):
            errors.append(f"{test_id}: expected overall status contradicts individual fact labels")

        local_fact_ids = set()
        evidence_status = {}
        for f in facts:
            facts_count += 1
            fact_id = f.get("fact_id", "")
            if not fact_id.startswith(test_id + "-F") or fact_id in local_fact_ids:
                errors.append(f"{test_id}: nonunique or malformed fact ID {fact_id}")
            local_fact_ids.add(fact_id)

            category = f.get("category")
            status = f.get("expected_status")
            severity = f.get("expected_severity")
            issue_type = f.get("issue_type")
            source = f.get("source_evidence")
            prompt = f.get("prompt_evidence")
            categories[category] += 1
            statuses[status] += 1

            if category not in CATEGORIES or status not in STATUSES:
                errors.append(f"{fact_id}: unrecognized category or status")
            if not isinstance(source, str) or not source or source not in case["screenplay_text"]:
                errors.append(f"{fact_id}: source evidence is not an exact screenplay substring")
            if prompt is not None and (not isinstance(prompt, str) or not prompt or prompt not in case["video_prompt"]):
                errors.append(f"{fact_id}: prompt evidence is not an exact prompt substring")

            if status in {"Supported", "Not Applicable"}:
                if severity is not None or issue_type is not None:
                    errors.append(f"{fact_id}: supported/not-applicable fact has issue metadata")
            else:
                if severity not in SEVERITIES or not isinstance(issue_type, str) or not issue_type:
                    errors.append(f"{fact_id}: issue/ambiguity lacks valid severity and issue type")

            if status in {"Contradicted", "Supported", "Ambiguous"} and prompt is None:
                errors.append(f"{fact_id}: {status} must identify matching or conflicting prompt wording")
            if status in {"Missing", "Not Applicable"} and prompt is not None:
                errors.append(f"{fact_id}: {status} must not claim corresponding prompt evidence")

            if not isinstance(f.get("explanation"), str) or len(f["explanation"].strip()) < 20:
                errors.append(f"{fact_id}: missing meaningful human explanation")

            key = (category, source)
            if key in evidence_status and evidence_status[key] != status:
                errors.append(f"{fact_id}: same screenplay fact has contradictory statuses")
            evidence_status[key] = status

        outcomes[annotation["expected_overall_status"]] += 1
        confirmed_issues += has_confirmed_issue(facts)

    if len(demo_ids) < 3:
        errors.append("At least three demo-ready cases must be identified")
    if set(categories) != CATEGORIES:
        errors.append("The four required detection categories are not all represented")
    if set(statuses) != STATUSES:
        errors.append("The five required statuses are not all represented")

    summary = {
        "dataset_id": data.get("dataset_id"),
        "case_count": len(cases),
        "labeled_fact_count": facts_count,
        "expected_status_counts": dict(sorted(statuses.items())),
        "expected_category_counts": dict(sorted(categories.items())),
        "expected_review_outcomes": dict(sorted(outcomes.items())),
        "confirmed_issue_cases": confirmed_issues,
        "non_confirmed_issue_cases": len(cases) - confirmed_issues,
        "demo_case_ids": demo_ids,
        "error_count": len(errors),
        "errors": errors,
    }
    return summary


if __name__ == "__main__":
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["error_count"] == 0 else 1)
