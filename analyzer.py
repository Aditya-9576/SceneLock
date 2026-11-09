"""Semantic analysis with distinct validated report and untouched raw output.

The LLM judges source meaning; Python verifies its evidence and owns all
counts, review statuses and report identity. No alternate canned inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from model_adapter import InferenceMetadata, ModelAdapter, ModelResponseFailure
from schemas import (
    AnalysisInput,
    AnalysisMetadata,
    AnalysisResult,
    AnalysisSummary,
    LLMAnalysisPayload,
    derive_summary,
)
from validators import ModelOutputValidationError, parse_model_response, validate_model_payload


def calculate_summary(result: LLMAnalysisPayload) -> AnalysisSummary:
    """Count *validated* semantic facts without asking Gemini for arithmetic.

    Accepts a model payload (facts and findings) and does not mutate it.
    """
    return derive_summary(result.facts, result.findings)


@dataclass(frozen=True)
class AnalysisRun:
    """Keep provider bytes separate from Python-normalized reviewed data."""

    report: AnalysisResult
    raw_response_text: str = field(repr=False)
    inference_metadata: InferenceMetadata


class SceneLockAnalyzer:
    """One provider request, verification, Python summary, and typed report."""

    def __init__(self, adapter: ModelAdapter, *, analysis_engine: str = "live_llm") -> None:
        self.adapter = adapter
        self.analysis_engine = analysis_engine

    def analyze(self, request: AnalysisInput) -> AnalysisResult:
        """Backward-compatible validated report API, without exposing raw text."""
        return self.analyze_with_raw(request).report

    def analyze_with_raw(self, request: AnalysisInput) -> AnalysisRun:
        """Run one inference, validate raw/payload agreement, preserve raw bytes."""
        if not isinstance(request, AnalysisInput):
            raise TypeError("A validated AnalysisInput object is required.")

        # Any conforming provider can replace Gemini. Verify again at this
        # boundary to catch a faulty third-party adapter, not just Gemini.
        inference = self.adapter.analyze(request)
        try:
            raw_payload = parse_model_response(
                inference.raw_response_text,
                screenplay_text=request.screenplay_text,
                video_prompt=request.video_prompt,
            )
            payload = validate_model_payload(
                inference.analysis,
                screenplay_text=request.screenplay_text,
                video_prompt=request.video_prompt,
            )
            if payload != raw_payload:
                raise ModelOutputValidationError(
                    "Returned model structure differs from the original raw output."
                )
        except (ModelOutputValidationError, ValueError):
            raise ModelResponseFailure("Model analysis failed evidence validation.") from None

        report = AnalysisResult(
            metadata=AnalysisMetadata(
                analysis_id=str(uuid4()),
                created_at_utc=inference.metadata.completed_at_utc,
                episode_id=request.episode_id,
                scene_id=request.scene_id,
                shot_id=request.shot_id,
                shot_type=request.shot_type,
                shot_intent=request.shot_intent,
                analysis_engine=self.analysis_engine,
                provider=inference.metadata.provider,
                model=inference.metadata.model,
                duration_ms=inference.metadata.duration_ms,
            ),
            facts=payload.facts,
            findings=payload.findings,
            summary=calculate_summary(payload),
            suggested_corrected_prompt=payload.suggested_corrected_prompt,
        )
        return AnalysisRun(
            report=report,
            raw_response_text=inference.raw_response_text,
            inference_metadata=inference.metadata,
        )
