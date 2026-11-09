"""The orchestration boundary uses any provider and produces a real summary."""

from datetime import datetime, timezone
from types import SimpleNamespace

from analyzer import SceneLockAnalyzer
from model_adapter import InferenceMetadata, ModelInferenceResult
from schemas import AnalysisInput, LLMAnalysisPayload, ReviewStatus, ShotType


def test_analyzer_calls_injected_provider_without_gemini() -> None:
    request = AnalysisInput(
        screenplay_text="Mina places a key inside her purse.",
        video_prompt="Mina slips a key into her handbag.",
        shot_type=ShotType.ACTION_SHOT,
    )
    payload = LLMAnalysisPayload(
        facts=[], findings=[], suggested_corrected_prompt=request.video_prompt
    )
    result = ModelInferenceResult(
        analysis=payload,
        metadata=InferenceMetadata(
            provider="fake",
            model="unit-test",
            interaction_id="fake-id",
            completed_at_utc=datetime.now(timezone.utc),
            duration_ms=5,
            attempts=1,
        ),
        raw_response_text=payload.model_dump_json(),
    )
    provider = SimpleNamespace(analyze=lambda submitted: result)
    report = SceneLockAnalyzer(provider).analyze(request)
    assert report.metadata.provider == "fake"
    assert report.metadata.model == "unit-test"
    assert report.metadata.shot_type == ShotType.ACTION_SHOT
    assert report.summary.overall_status == ReviewStatus.INSUFFICIENT_CONTEXT
    assert report.summary.extracted_fact_count == 0
    assert report.summary.finding_count == 0
    assert report.suggested_corrected_prompt == request.video_prompt

    raw_run = SceneLockAnalyzer(provider, analysis_engine="synthetic_fixture").analyze_with_raw(request)
    assert raw_run.raw_response_text == result.raw_response_text
    assert raw_run.report.metadata.analysis_engine == "synthetic_fixture"
    assert raw_run.inference_metadata.interaction_id == "fake-id"
