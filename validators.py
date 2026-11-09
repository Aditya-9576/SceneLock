"""Strict validation boundary for untrusted Gemini JSON and final reports.

These deterministic rules establish provenance and internal consistency, not
the semantic correctness of every model interpretation.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from schemas import AnalysisInput, ComparisonStatus, LLMAnalysisPayload, has_semantic_text


class InputValidationError(ValueError):
    """Readable validation message safe to display in Streamlit."""


def format_validation_errors(exc: ValidationError) -> list[str]:
    """Convert technical Pydantic issues into field-specific user messages."""
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "shot intent"
        description = error["msg"].removeprefix("Value error, ")
        messages.append(f"{location.replace('_', ' ').capitalize()}: {description}")
    return messages


def validate_input_payload(payload: dict[str, Any]) -> AnalysisInput:
    """Validate the input without contacting Gemini or writing files."""
    try:
        return AnalysisInput.model_validate(payload)
    except ValidationError as exc:
        raise InputValidationError("\n".join(format_validation_errors(exc))) from exc


def evidence_is_exact_substring(evidence: str, original_text: str) -> bool:
    """Quotes must contain visible text and occur verbatim in the supplied input."""
    return isinstance(evidence, str) and has_semantic_text(evidence) and evidence in original_text


class ModelOutputValidationError(ValueError):
    """A structured model response violated semantic evidence invariants."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys rather than silently accepting the last value."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ModelOutputValidationError("Model JSON contained duplicate object keys.")
        result[key] = value
    return result


def _reject_nonfinite_json_constant(_: str) -> None:
    raise ModelOutputValidationError("Model JSON contained a non-finite numeric value.")


def parse_model_response(
    raw_response_text: str, *, screenplay_text: str, video_prompt: str
) -> LLMAnalysisPayload:
    """Decode exactly one valid JSON object and then validate all its evidence.

    Unlike permissive JSON readers, this rejects duplicate keys, NaN,
    Infinity, trailing text and unexpectedly large model responses.
    """
    if not isinstance(raw_response_text, str) or not raw_response_text.strip():
        raise ModelOutputValidationError("Model returned no JSON text.")
    try:
        byte_count = len(raw_response_text.encode("utf-8"))
    except UnicodeError:
        raise ModelOutputValidationError("Model response contains invalid Unicode.") from None
    if byte_count > 1_000_000:
        raise ModelOutputValidationError("Model response exceeds the supported size limit.")
    try:
        decoded = json.loads(
            raw_response_text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except (json.JSONDecodeError, UnicodeError, TypeError, ValueError) as exc:
        raise ModelOutputValidationError("Model returned invalid or ambiguous JSON.") from None
    if not isinstance(decoded, dict):
        raise ModelOutputValidationError("Model response must be one JSON object.")
    return validate_model_payload(decoded, screenplay_text=screenplay_text, video_prompt=video_prompt)


def validate_model_payload(
    payload: LLMAnalysisPayload | dict[str, Any], *, screenplay_text: str, video_prompt: str
) -> LLMAnalysisPayload:
    """Check evidence and cross-references without inventing new AI findings.

    Numerical counts and review status remain exclusively Python-owned.
    """
    try:
        payload = LLMAnalysisPayload.model_validate(payload)
    except ValidationError:
        raise ModelOutputValidationError("Model response did not match the required schema.") from None

    fact_by_id = {}
    unique_atomic_facts = set()
    for fact in payload.facts:
        if fact.fact_id in fact_by_id:
            raise ModelOutputValidationError("The model produced duplicate fact IDs.")
        if not evidence_is_exact_substring(fact.source_evidence, screenplay_text):
            raise ModelOutputValidationError("A fact quoted screenplay text that was not supplied.")
        fact_key = (
            fact.category,
            (fact.entity or "").strip().casefold(),
            fact.required_detail.strip().casefold(),
            fact.source_evidence,
        )
        if fact_key in unique_atomic_facts:
            raise ModelOutputValidationError("The model repeated an identical atomic fact.")
        unique_atomic_facts.add(fact_key)
        fact_by_id[fact.fact_id] = fact

    finding_ids = set()
    finding_by_fact = set()
    for finding in payload.findings:
        if finding.finding_id in finding_ids:
            raise ModelOutputValidationError("The model produced duplicate finding IDs.")
        finding_ids.add(finding.finding_id)
        fact = fact_by_id.get(finding.related_fact_id)
        if fact is None:
            raise ModelOutputValidationError("A finding refers to a nonexistent screenplay fact.")
        if finding.related_fact_id in finding_by_fact:
            raise ModelOutputValidationError("The model reported the same fact more than once.")
        finding_by_fact.add(finding.related_fact_id)
        if finding.category != fact.category or finding.comparison_status != fact.comparison_status:
            raise ModelOutputValidationError("A finding disagrees with its linked fact.")
        if finding.screenplay_evidence != fact.source_evidence:
            raise ModelOutputValidationError("A finding's screenplay quotation differs from its fact.")
        if finding.comparison_status == ComparisonStatus.AMBIGUOUS and finding.severity.value == "High":
            raise ModelOutputValidationError("Uncertain facts cannot be labeled proven High-severity issues.")
        if finding.comparison_status == ComparisonStatus.MISSING:
            if finding.prompt_evidence is not None:
                raise ModelOutputValidationError("A missing requirement must not invent prompt evidence.")
        elif not evidence_is_exact_substring(finding.prompt_evidence or "", video_prompt):
            raise ModelOutputValidationError("A finding's prompt quotation is not in the input.")

    for fact in payload.facts:
        if fact.comparison_status in {
            ComparisonStatus.CONTRADICTED,
            ComparisonStatus.MISSING,
            ComparisonStatus.AMBIGUOUS,
        } and fact.fact_id not in finding_by_fact:
            raise ModelOutputValidationError("A reported problem lacks its required finding.")

    if not payload.suggested_corrected_prompt.strip():
        raise ModelOutputValidationError("The proposed prompt cannot be empty.")
    has_actionable_issue = any(
        finding.comparison_status in {ComparisonStatus.MISSING, ComparisonStatus.CONTRADICTED}
        for finding in payload.findings
    )
    if not has_actionable_issue and payload.suggested_corrected_prompt != video_prompt:
        raise ModelOutputValidationError("A prompt with no actionable issue must remain unchanged.")
    if has_actionable_issue and payload.suggested_corrected_prompt == video_prompt:
        raise ModelOutputValidationError("An actionable correction cannot leave the prompt unchanged.")
    return payload
