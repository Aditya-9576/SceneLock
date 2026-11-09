"""SceneLock's strict input, model-output, report and human-decision contracts.

Gemini proposes facts/findings; Python verifies evidence and owns summaries.
Validators here preserve the existing JSON-schema shape for Gemini while
rejecting blank or excessive content once the model has answered.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


def has_visible_text(value: str) -> bool:
    """Unicode format/zero-width characters are not visible evidence.

    `str.strip()` alone accepts zero-width spaces and joiners as "content".
    Letters, numbers, punctuation and symbols remain valid, including Hindi.
    """
    return isinstance(value, str) and any(
        unicodedata.category(ch)[0] not in {"C", "Z", "M"} for ch in value
    )


def has_semantic_text(value: str) -> bool:
    """Require at least one letter or number, not only visible punctuation.

    A screenplay like "..." or an alleged evidence quote of just "!" is
    syntactically visible but cannot establish a concrete character/action.
    Unicode letters/numbers in Hindi and other languages remain supported.
    """
    return has_visible_text(value) and any(
        unicodedata.category(ch)[0] in {"L", "N"} for ch in value
    )


class ShotType(str, Enum):
    FULL_DRAMATIC_BEAT = "Full dramatic beat"
    ESTABLISHING_WIDE = "Establishing / wide shot"
    CHARACTER_INTERACTION = "Character interaction"
    ACTION_SHOT = "Action shot"
    CHARACTER_CLOSE_UP = "Character close-up"
    PROP_CLOSE_UP = "Prop close-up"
    CUSTOM_OTHER = "Custom / other"


class DetectionCategory(str, Enum):
    CRITICAL_ACTION = "critical_action"
    IMPORTANT_PROP = "important_prop"
    CHARACTER_IDENTITY_POSITION = "character_identity_position"
    EXPLICIT_VISUAL_ATTRIBUTE = "explicit_visual_attribute"


class ComparisonStatus(str, Enum):
    SUPPORTED = "Supported"
    CONTRADICTED = "Contradicted"
    MISSING = "Missing"
    AMBIGUOUS = "Ambiguous"
    NOT_APPLICABLE = "Not Applicable"


class Severity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ReviewStatus(str, Enum):
    REVIEW_REQUIRED = "Review Required"
    NO_SIGNIFICANT_ISSUES = "No Significant Issues Detected"
    INSUFFICIENT_CONTEXT = "Insufficient Context"


class HumanDecision(str, Enum):
    ACCEPT = "Accept suggestion"
    DISMISS = "Dismiss / intentional creative choice"
    FURTHER_REVIEW = "Needs further review"


class AnalysisInput(BaseModel):
    """The five agreed input groups (scene identifiers are one group)."""

    model_config = ConfigDict(extra="forbid")

    screenplay_text: str = Field(max_length=8000, description="Source screenplay excerpt")
    video_prompt: str = Field(max_length=4000, description="Proposed video-generation prompt")
    shot_type: ShotType
    shot_intent: str | None = Field(default=None, max_length=500)
    episode_id: str | None = Field(default=None, max_length=80)
    scene_id: str | None = Field(default=None, max_length=80)
    shot_id: str | None = Field(default=None, max_length=80)

    @field_validator("screenplay_text", "video_prompt", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            if not has_semantic_text(cleaned):
                raise ValueError("This required text field must contain meaningful words or numbers.")
            return cleaned
        return value

    @field_validator("shot_intent", "episode_id", "scene_id", "shot_id", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object, info: ValidationInfo) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            check = has_semantic_text if info.field_name == "shot_intent" else has_visible_text
            return cleaned if check(cleaned) else None
        return value

    @model_validator(mode="after")
    def custom_shot_has_intent(self) -> "AnalysisInput":
        if self.shot_type == ShotType.CUSTOM_OTHER and not self.shot_intent:
            raise ValueError("Custom / other requires a short shot-intent description.")
        return self


class ScreenplayFact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fact_id: str
    category: DetectionCategory
    entity: str | None = None
    required_detail: str
    source_evidence: str
    comparison_status: ComparisonStatus
    applicability_reason: str
    uncertainty_note: str | None = None

    @model_validator(mode="after")
    def required_descriptions_must_be_meaningful(self) -> "ScreenplayFact":
        for name in ("fact_id", "required_detail", "source_evidence", "applicability_reason"):
            if not has_semantic_text(getattr(self, name)):
                raise ValueError(f"{name} must contain visible, non-whitespace text.")
        if self.entity is not None and not has_semantic_text(self.entity):
            raise ValueError("entity must be nonempty when supplied.")
        if self.uncertainty_note is not None and not has_visible_text(self.uncertainty_note):
            raise ValueError("uncertainty_note must be nonempty when supplied.")
        return self


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    related_fact_id: str
    category: DetectionCategory
    comparison_status: ComparisonStatus
    severity: Severity
    screenplay_evidence: str
    prompt_evidence: str | None = None
    explanation: str
    suggested_fix: str
    uncertainty_note: str | None = None

    @model_validator(mode="after")
    def findings_are_actual_concerns(self) -> "Finding":
        if self.comparison_status in {ComparisonStatus.SUPPORTED, ComparisonStatus.NOT_APPLICABLE}:
            raise ValueError("Supported or Not Applicable facts must not appear as findings.")
        for name in ("finding_id", "related_fact_id", "screenplay_evidence", "explanation", "suggested_fix"):
            if not has_semantic_text(getattr(self, name)):
                raise ValueError(f"{name} must contain visible, non-whitespace text.")
        if self.prompt_evidence is not None and not has_semantic_text(self.prompt_evidence):
            raise ValueError("prompt_evidence must be nonempty when supplied.")
        if self.uncertainty_note is not None and not has_visible_text(self.uncertainty_note):
            raise ValueError("uncertainty_note must be nonempty when supplied.")
        return self


class AnalysisMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    analysis_id: str
    created_at_utc: datetime
    episode_id: str | None = None
    scene_id: str | None = None
    shot_id: str | None = None
    shot_type: ShotType
    shot_intent: str | None = None
    analysis_engine: str = "live_llm"
    provider: str
    model: str
    duration_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def valid_provenance(self) -> "AnalysisMetadata":
        if not all(has_visible_text(s) for s in (self.analysis_id, self.provider, self.model)):
            raise ValueError("Analysis ID, provider and model must be nonempty.")
        if self.created_at_utc.tzinfo is None or self.created_at_utc.utcoffset() is None:
            raise ValueError("Model/report completion time must be timezone-aware.")
        if self.created_at_utc.utcoffset() != timezone.utc.utcoffset(self.created_at_utc):
            raise ValueError("Model/report completion time must be in UTC.")
        return self


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overall_status: ReviewStatus
    extracted_fact_count: int = Field(ge=0)
    relevant_fact_count: int = Field(ge=0)
    verified_fact_count: int = Field(ge=0)
    critical_issue_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    finding_count: int = Field(ge=0)


def derive_summary(facts: list[ScreenplayFact], findings: list[Finding]) -> AnalysisSummary:
    """The canonical Python-owned counting and status policy.

    This function has no dependency on model text, review decisions or Gemini.
    """
    relevant = [fact for fact in facts if fact.comparison_status != ComparisonStatus.NOT_APPLICABLE]
    verified = sum(fact.comparison_status == ComparisonStatus.SUPPORTED for fact in relevant)
    critical = sum(
        finding.severity == Severity.HIGH
        and finding.comparison_status in {ComparisonStatus.MISSING, ComparisonStatus.CONTRADICTED}
        for finding in findings
    )
    warning = sum(finding.severity in {Severity.MEDIUM, Severity.LOW} for finding in findings)
    if not relevant or all(fact.comparison_status == ComparisonStatus.AMBIGUOUS for fact in relevant):
        status = ReviewStatus.INSUFFICIENT_CONTEXT
    elif any(finding.severity in {Severity.HIGH, Severity.MEDIUM} for finding in findings):
        status = ReviewStatus.REVIEW_REQUIRED
    else:
        status = ReviewStatus.NO_SIGNIFICANT_ISSUES
    return AnalysisSummary(
        overall_status=status,
        extracted_fact_count=len(facts),
        relevant_fact_count=len(relevant),
        verified_fact_count=verified,
        critical_issue_count=critical,
        warning_count=warning,
        finding_count=len(findings),
    )


class AnalysisResult(BaseModel):
    """Validated analysis, assembled by Python rather than supplied by Gemini."""

    model_config = ConfigDict(extra="forbid")
    metadata: AnalysisMetadata
    facts: list[ScreenplayFact]
    findings: list[Finding]
    summary: AnalysisSummary
    suggested_corrected_prompt: str

    @model_validator(mode="after")
    def summary_must_match_the_facts(self) -> "AnalysisResult":
        if self.summary != derive_summary(self.facts, self.findings):
            raise ValueError("Summary counts/status do not match the returned facts and findings.")
        return self


class LLMAnalysisPayload(BaseModel):
    """Exactly the three data groups Gemini may propose in one structured call.

    The model is NOT allowed to decide final review status or summary counts.
    Neither successful JSON parsing nor a schema alone guarantees correctness;
    validators.py additionally checks quotations and fact relationships.
    """

    model_config = ConfigDict(extra="forbid")
    facts: list[ScreenplayFact] = Field(description="Atomic screenplay facts and shot-aware comparison")
    findings: list[Finding] = Field(description="Only Contradicted, Missing or Ambiguous concerns")
    suggested_corrected_prompt: str = Field(description="Minimal suggested revision preserving compatible details")

    @model_validator(mode="after")
    def bounded_nonempty_response(self) -> "LLMAnalysisPayload":
        if len(self.facts) > 80 or len(self.findings) > 80:
            raise ValueError("Model returned an excessive number of facts or findings.")
        if not has_semantic_text(self.suggested_corrected_prompt):
            raise ValueError("Corrected prompt must contain visible text.")
        if len(self.suggested_corrected_prompt) > 8000:
            raise ValueError("Model corrected prompt exceeds the accepted length.")
        return self


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    decision: HumanDecision = HumanDecision.FURTHER_REVIEW

    @field_validator("finding_id")
    @classmethod
    def reviewer_target_cannot_be_blank(cls, value: str) -> str:
        if not has_visible_text(value):
            raise ValueError("A reviewer decision must refer to an actual finding.")
        return value
