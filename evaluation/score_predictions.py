"""Conservative, reproducible scoring of *actual* validated model reports.

Expected labels are partial annotations of 25 screenplay facts, not an
exhaustive list of every possible valid finding. Predictions with no safe
evidence/category alignment are therefore UNADJUDICATED, not automatically
counted as false positives. This avoids inflated or dishonest precision.
"""

from __future__ import annotations

from typing import Any

from schemas import AnalysisResult, ComparisonStatus, Severity


ISSUE_STATUSES = {ComparisonStatus.CONTRADICTED.value, ComparisonStatus.MISSING.value}
ISSUE_SEVERITIES = {Severity.HIGH.value, Severity.MEDIUM.value}


def _intervals(text: str, exact_quote: str) -> list[tuple[int, int]]:
    if not exact_quote:
        return []
    result = []
    start = 0
    while True:
        loc = text.find(exact_quote, start)
        if loc < 0:
            return result
        result.append((loc, loc + len(exact_quote)))
        start = loc + 1


def _evidence_overlap(source: str, left: str, right: str) -> float:
    """How strongly two exact source quotations share a source-text span.

    Use containment-normalized overlap because an LLM may quote a shorter
    exact phrase than a human label, even when both identify the same fact.
    A higher bar reduces accidental matches on generic repeated tokens.
    """
    if len(left.strip()) < 4 or len(right.strip()) < 4:
        return 0.0
    pairs = (
        (max(0, min(a[1], b[1]) - max(a[0], b[0])), a, b)
        for a in _intervals(source, left) for b in _intervals(source, right)
    )
    return max((overlap / min(len(left), len(right)) for overlap, _, _ in pairs), default=0.0)


def align_labeled_facts(
    source: str, labels: list[dict[str, Any]], report: AnalysisResult
) -> tuple[dict[int, int], list[int]]:
    """Align partial human labels and model facts one-to-one without using IDs.

    Model fact IDs (F1 etc.) are arbitrary. Match only the same category with
    at least 60% overlap of their verbatim screenplay quotations. Remaining
    model facts need human adjudication before being called false positives.
    """
    candidates = []
    for li, label in enumerate(labels):
        for pi, fact in enumerate(report.facts):
            if label["category"] != fact.category.value:
                continue
            score = _evidence_overlap(source, label["source_evidence"], fact.source_evidence)
            if score >= 0.60:
                candidates.append((score, li, pi))
    assigned_labels: dict[int, int] = {}
    assigned_predictions: set[int] = set()
    for score, li, pi in sorted(candidates, key=lambda row: (-row[0], row[1], row[2])):
        if li not in assigned_labels and pi not in assigned_predictions:
            assigned_labels[li] = pi
            assigned_predictions.add(pi)
    return assigned_labels, [i for i in range(len(report.facts)) if i not in assigned_predictions]


def score_case(
    case_id: str,
    screenplay: str,
    expected_label: dict[str, Any],
    report: AnalysisResult,
) -> dict[str, Any]:
    """Evaluate confirmed-issue detection only where a gold fact is aligned.

    `precision`/`recall` are micro-aggregated by the calling runner; do not
    count ambiguous labels as confirmed issues or invent a label for extra
    model findings. Severity and status errors are reported separately.
    """
    labels = expected_label["expected_facts"]
    matched, unmatched_predicted = align_labeled_facts(screenplay, labels, report)
    findings_by_fact = {finding.related_fact_id: finding for finding in report.findings}
    tp = fp = fn = scope = semantic_correct = semantic_total = ambiguous_correct = ambiguous_total = 0
    status_mismatches: list[dict[str, str]] = []
    severity_mismatches: list[dict[str, str]] = []
    for li, label in enumerate(labels):
        gold_status = label["expected_status"]
        if gold_status == ComparisonStatus.SUPPORTED.value:
            semantic_total += 1
        if gold_status == ComparisonStatus.AMBIGUOUS.value:
            ambiguous_total += 1
        pi = matched.get(li)
        fact = report.facts[pi] if pi is not None else None
        predicted_status = fact.comparison_status.value if fact else None
        predicted_finding = findings_by_fact.get(fact.fact_id) if fact else None
        predicted_positive = bool(
            predicted_finding
            and predicted_finding.comparison_status.value in ISSUE_STATUSES
            and predicted_finding.severity.value in ISSUE_SEVERITIES
        )
        gold_positive = bool(
            gold_status in ISSUE_STATUSES and label.get("expected_severity") in ISSUE_SEVERITIES
        )
        if gold_positive:
            if predicted_positive:
                tp += 1
            else:
                fn += 1
        elif predicted_positive:
            fp += 1

        if fact:
            if gold_status == predicted_status and gold_status == ComparisonStatus.SUPPORTED.value:
                semantic_correct += 1
            if gold_status == predicted_status and gold_status == ComparisonStatus.AMBIGUOUS.value:
                ambiguous_correct += 1
            if gold_status != predicted_status:
                status_mismatches.append({
                    "gold_fact_id": label["fact_id"],
                    "expected_status": gold_status,
                    "predicted_status": predicted_status,
                })
            if (gold_status == ComparisonStatus.NOT_APPLICABLE.value) != (
                predicted_status == ComparisonStatus.NOT_APPLICABLE.value
            ):
                scope += 1
            if predicted_finding and label.get("expected_severity") not in (
                None, predicted_finding.severity.value
            ):
                severity_mismatches.append({
                    "gold_fact_id": label["fact_id"],
                    "expected_severity": label["expected_severity"],
                    "predicted_severity": predicted_finding.severity.value,
                })

    unadjudicated = [
        finding.finding_id
        for finding in report.findings
        if any(report.facts[idx].fact_id == finding.related_fact_id for idx in unmatched_predicted)
    ]
    return {
        "test_id": case_id,
        "labeled_fact_count": len(labels),
        "aligned_fact_count": len(matched),
        "unmatched_labeled_fact_count": len(labels) - len(matched),
        "issue_confusion_on_adjudicable_facts": {"TP": tp, "FP": fp, "FN": fn},
        "correct_supported_matches": semantic_correct,
        "expected_supported_facts": semantic_total,
        "correct_ambiguous_matches": ambiguous_correct,
        "expected_ambiguous_facts": ambiguous_total,
        "shot_scope_mistakes": scope,
        "status_mismatches": status_mismatches,
        "severity_mismatches": severity_mismatches,
        "unadjudicated_predicted_finding_ids": unadjudicated,
        "model_overall_status": report.summary.overall_status.value,
        "expected_overall_status": expected_label["expected_overall_status"],
        "overall_status_correct": report.summary.overall_status.value == expected_label["expected_overall_status"],
        "latency_ms": report.metadata.duration_ms,
    }


def summarize_scored_cases(scored: list[dict], *, total_labeled_cases: int) -> dict:
    def add(key: str) -> int:
        return sum(int(item[key]) for item in scored)

    confusion = {label: sum(row["issue_confusion_on_adjudicable_facts"][label] for row in scored)
                 for label in ("TP", "FP", "FN")}
    tp, fp, fn = confusion["TP"], confusion["FP"], confusion["FN"]
    latencies = [row["latency_ms"] for row in scored if row["latency_ms"] is not None]
    latencies_sorted = sorted(latencies)
    return {
        "evaluation_type": "validated_live_model_partial_gold_issue_scoring",
        "total_labeled_cases": total_labeled_cases,
        "scored_case_count": len(scored),
        "coverage": len(scored) / total_labeled_cases if total_labeled_cases else None,
        "issue_confusion_on_adjudicable_facts": confusion,
        "issue_precision_on_adjudicable_facts": tp / (tp + fp) if tp + fp else None,
        "issue_recall_on_adjudicable_facts": tp / (tp + fn) if tp + fn else None,
        "correct_supported_matches": add("correct_supported_matches"),
        "expected_supported_facts": add("expected_supported_facts"),
        "shot_scope_mistakes": add("shot_scope_mistakes"),
        "correct_ambiguous_matches": add("correct_ambiguous_matches"),
        "expected_ambiguous_facts": add("expected_ambiguous_facts"),
        "unadjudicated_predicted_findings": sum(len(row["unadjudicated_predicted_finding_ids"]) for row in scored),
        "status_mismatch_count": sum(len(row["status_mismatches"]) for row in scored),
        "severity_mismatch_count": sum(len(row["severity_mismatches"]) for row in scored),
        "overall_status_matches": sum(row["overall_status_correct"] for row in scored),
        "latency_ms": {
            "sample_count": len(latencies_sorted),
            "mean": sum(latencies_sorted) / len(latencies_sorted) if latencies_sorted else None,
            "min": latencies_sorted[0] if latencies_sorted else None,
            "max": latencies_sorted[-1] if latencies_sorted else None,
        },
        "limitations": [
            "Ground labels are partial and human-authored, not independently adjudicated.",
            "Unmatched model findings are unadjudicated, not automatically false positives.",
            "Fact matching uses category and overlapping exact screenplay spans; different model decomposition can leave facts unmatched.",
            "Precision/recall cover confirmed High/Medium Missing/Contradicted facts from successfully validated cases only.",
            "API or evidence-validation failures are excluded from prediction scoring and reported separately.",
        ],
    }
