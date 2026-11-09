"""Phase 6 validated, in-memory JSON/CSV review exports.

Only explicitly requested downloads are built; no automatic storage of user
screenplays, model outputs or secrets. CSV text is formula-injection-safe.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Mapping

from analyzer import calculate_summary
from schemas import AnalysisInput, AnalysisResult, HumanDecision, LLMAnalysisPayload, ReviewDecision
from validators import validate_model_payload


CSV_FIELDS = (
    "analysis_id", "episode_id", "scene_id", "shot_id", "finding_id", "related_fact_id",
    "category", "status", "comparison_status", "severity", "screenplay_evidence", "prompt_evidence",
    "explanation", "suggested_fix", "uncertainty_note", "human_decision",
)


def validated_review_decisions(
    report: AnalysisResult, supplied: Mapping[str, str | HumanDecision]
) -> list[ReviewDecision]:
    """Verify every independent human decision refers to this actual report."""
    expected_ids = {finding.finding_id for finding in report.findings}
    if set(supplied) - expected_ids:
        raise ValueError("Reviewer decision refers to a finding outside this analysis.")
    return [
        ReviewDecision(
            finding_id=finding.finding_id,
            decision=supplied.get(finding.finding_id, HumanDecision.FURTHER_REVIEW),
        )
        for finding in report.findings
    ]


def _verify_report_for_request(request: AnalysisInput, report: AnalysisResult) -> None:
    """Never pair a report with different source text or fabricated summary."""
    if not isinstance(request, AnalysisInput) or not isinstance(report, AnalysisResult):
        raise TypeError("Only a validated input/report pair can be exported.")
    if (
        report.metadata.shot_type != request.shot_type
        or report.metadata.shot_intent != request.shot_intent
        or report.metadata.episode_id != request.episode_id
        or report.metadata.scene_id != request.scene_id
        or report.metadata.shot_id != request.shot_id
    ):
        raise ValueError("Report metadata does not match the selected input.")
    payload = validate_model_payload(
        LLMAnalysisPayload(
            facts=report.facts,
            findings=report.findings,
            suggested_corrected_prompt=report.suggested_corrected_prompt,
        ),
        screenplay_text=request.screenplay_text,
        video_prompt=request.video_prompt,
    )
    if calculate_summary(payload) != report.summary:
        raise ValueError("Report summary does not match the validated evidence.")


def review_json_bytes(
    request: AnalysisInput,
    report: AnalysisResult,
    decisions: Mapping[str, str | HumanDecision],
    edited_prompt: str,
) -> bytes:
    """Include supplied source inputs, exact evidence and separate reviewer choices."""
    _verify_report_for_request(request, report)
    resolved = validated_review_decisions(report, decisions)
    document = {
        "schema_version": report.metadata.schema_version,
        "inputs": request.model_dump(mode="json"),
        "analysis": report.model_dump(mode="json"),
        "review_decisions": [choice.model_dump(mode="json") for choice in resolved],
        "reviewer_edited_prompt": edited_prompt,
    }
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _csv_safe(value: object) -> str:
    """Prevent spreadsheet apps from executing prompt-injected CSV formulas."""
    if value is None:
        return ""
    text = str(value)
    if text.lstrip("\ufeff \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def findings_csv_bytes(
    request: AnalysisInput, report: AnalysisResult, decisions: Mapping[str, str | HumanDecision]
) -> bytes:
    """One row per finding, with headers even if no findings were returned."""
    _verify_report_for_request(request, report)
    resolved = {d.finding_id: d.decision.value for d in validated_review_decisions(report, decisions)}
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writeheader()
    for finding in report.findings:
        row = {
            "analysis_id": report.metadata.analysis_id,
            "episode_id": report.metadata.episode_id,
            "scene_id": report.metadata.scene_id,
            "shot_id": report.metadata.shot_id,
            "finding_id": finding.finding_id,
            "related_fact_id": finding.related_fact_id,
            "category": finding.category.value,
            "status": finding.comparison_status.value,
            "comparison_status": finding.comparison_status.value,
            "severity": finding.severity.value,
            "screenplay_evidence": finding.screenplay_evidence,
            "prompt_evidence": finding.prompt_evidence,
            "explanation": finding.explanation,
            "suggested_fix": finding.suggested_fix,
            "uncertainty_note": finding.uncertainty_note,
            "human_decision": resolved[finding.finding_id],
        }
        writer.writerow({name: _csv_safe(value) for name, value in row.items()})
    return buffer.getvalue().encode("utf-8-sig")  # Excel-friendly UTF-8 including Hindi.
