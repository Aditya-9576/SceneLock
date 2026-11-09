"""Replaceable Gemini Interactions adapter with strict Phase 6 validation.

The module never logs keys, user text or raw model output to disk.
"""

from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

import httpx
from google import genai
from google.genai import errors as genai_errors

from prompts import SYSTEM_INSTRUCTIONS
from schemas import AnalysisInput, LLMAnalysisPayload, ShotType
from validators import ModelOutputValidationError, parse_model_response, validate_input_payload


# Officially documented stable Flash model with structured output and a free tier.
# Users with access to a different model may override GEMINI_MODEL.
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str | None = field(default=None, repr=False)
    model: str = DEFAULT_GEMINI_MODEL

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


class GeminiConfigurationError(RuntimeError):
    """A genuine model request cannot run without configured credentials."""


class ModelAdapterError(RuntimeError):
    """Base class for safe-to-display model inference failures."""


class AuthenticationFailure(ModelAdapterError):
    """Gemini rejected API credentials or access to the project/model."""


class RateLimitFailure(ModelAdapterError):
    """Gemini request/usage quota has been exceeded."""


class ModelTimeoutFailure(ModelAdapterError):
    """The provider did not complete within the configured budget."""


class ModelConnectionFailure(ModelAdapterError):
    """The provider could not be reached."""


class ModelResponseFailure(ModelAdapterError):
    """No complete, valid, evidence-grounded structured response was returned."""


class ProviderAPIError(ModelAdapterError):
    """Other provider error, without exposing potentially sensitive details."""


@dataclass(frozen=True)
class InferenceMetadata:
    provider: str
    model: str
    interaction_id: str | None
    completed_at_utc: datetime
    duration_ms: int
    attempts: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ModelInferenceResult:
    analysis: LLMAnalysisPayload
    metadata: InferenceMetadata
    raw_response_text: str = field(repr=False)


@runtime_checkable
class ModelAdapter(Protocol):
    """Replaceable semantic-model interface (no Gemini types in this API)."""

    def analyze(self, request: AnalysisInput) -> ModelInferenceResult: ...


def _non_placeholder(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.upper() in {
        "YOUR_API_KEY_HERE",
        "REPLACE_ME",
        "YOUR_KEY_HERE",
        "REPLACE_WITH_YOUR_REAL_KEY",  # Deployment guide example.
        "YOUR_REAL_GEMINI_API_KEY",  # Reviewer quickstart example.
    }:
        return None
    return cleaned


def load_gemini_settings(
    *,
    secrets: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GeminiSettings:
    """Read from environment, then optional Streamlit secrets.

    No credentials are printed, persisted, embedded in errors or committed.
    Google's SDK gives GOOGLE_API_KEY precedence when both env names are set.
    The Phase 3 input UI still does not require a key.
    """
    env = os.environ if environ is None else environ
    if secrets is not None:
        secret_source = secrets
    else:
        # Read Streamlit's managed secrets lazily. This supports both local
        # secrets.toml and Streamlit-hosted deployments, without requiring a
        # Streamlit runtime for command-line tests or alternative UIs.
        try:
            import streamlit as st
            from streamlit.errors import StreamlitSecretNotFoundError

            try:
                secret_source = dict(st.secrets)
            except (StreamlitSecretNotFoundError, FileNotFoundError):
                secret_source = {}
        except ImportError:
            secret_source = {}
    key = (
        _non_placeholder(env.get("GOOGLE_API_KEY"))
        or _non_placeholder(env.get("GEMINI_API_KEY"))
        or _non_placeholder(secret_source.get("GOOGLE_API_KEY"))
        or _non_placeholder(secret_source.get("GEMINI_API_KEY"))
    )
    model = _non_placeholder(env.get("GEMINI_MODEL")) or _non_placeholder(
        secret_source.get("GEMINI_MODEL")
    ) or DEFAULT_GEMINI_MODEL
    return GeminiSettings(api_key=key, model=model)


class GeminiAdapter:
    """One real structured Gemini request with bounded retries and clear errors.

    client_factory and sleep_fn are injectable for deterministic mock tests.
    Actual SDK clients are closed when owned by this adapter.
    """

    def __init__(
        self,
        settings: GeminiSettings,
        *,
        client_factory: Callable[[], Any] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        timeout_seconds: float = 45.0,
        max_attempts: int = 2,
        raw_response_observer: Callable[[str], None] | None = None,
    ) -> None:
        if timeout_seconds <= 0 or max_attempts < 1:
            raise ValueError("timeout_seconds must be positive and max_attempts at least one.")
        self.settings = settings
        self._client_factory = client_factory
        self._sleep = sleep_fn
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        # Phase 9 evaluation-only callback: receives exact provider text before
        # evidence validation. Never configured by the Streamlit interface.
        self.raw_response_observer = raw_response_observer

    def create_client(self) -> genai.Client:
        if not self.settings.is_configured:
            raise GeminiConfigurationError(
                "Gemini is not configured. Set GEMINI_API_KEY in the environment or Streamlit secrets."
            )
        return genai.Client(api_key=self.settings.api_key)

    @staticmethod
    def _api_error(exc: genai_errors.APIError) -> tuple[ModelAdapterError, bool]:
        code = getattr(exc, "code", None)
        if code in (401, 403):
            return AuthenticationFailure(
                "Gemini denied authentication or model access. Check the key and project permissions."
            ), False
        if code == 429:
            return RateLimitFailure(
                "Gemini rate limit or quota reached. Check your project's limits in Google AI Studio."
            ), True
        if code in (408, 504):
            return ModelTimeoutFailure("Gemini request timed out; you may retry."), True
        if code in (500, 502, 503):
            return ProviderAPIError("Gemini service is temporarily unavailable; try again later."), True
        return ProviderAPIError(f"Gemini request failed (HTTP status {code or 'unknown'})."), False

    @staticmethod
    def _usage_value(usage: Any, attr: str) -> int | None:
        value = getattr(usage, attr, None)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def analyze(self, request: AnalysisInput) -> ModelInferenceResult:
        if not isinstance(request, AnalysisInput):
            raise TypeError("GeminiAdapter requires a validated AnalysisInput object.")

        # Explicit JSON prevents accidental inclusion of evaluation labels or
        # metadata fields in the prompt; source data remains untrusted text.
        input_text = json.dumps(
            {
                "screenplay_text": request.screenplay_text,
                "video_prompt": request.video_prompt,
                "shot_scope": request.shot_type.value,
                "shot_intent": request.shot_intent or "",
            },
            ensure_ascii=False,
        )
        response_format = [
            {
                "type": "text",
                "mime_type": "application/json",
                "schema": LLMAnalysisPayload.model_json_schema(),
            }
        ]

        owned_client = self._client_factory is None
        try:
            client = self.create_client() if owned_client else self._client_factory()
        except GeminiConfigurationError:
            raise
        except (httpx.TransportError, OSError) as exc:
            raise ModelConnectionFailure("Could not initialize the Gemini HTTP client.") from None

        start = time.perf_counter()
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    interaction = client.interactions.create(
                        model=self.settings.model,
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        input=input_text,
                        response_format=response_format,
                        store=False,
                        timeout=self.timeout_seconds,
                    )
                except genai_errors.APIError as exc:
                    mapped, retryable = self._api_error(exc)
                    if retryable and attempt < self.max_attempts:
                        self._sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    raise mapped from None
                except (httpx.TimeoutException, TimeoutError):
                    if attempt < self.max_attempts:
                        self._sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    raise ModelTimeoutFailure("Gemini did not respond before the timeout.") from None
                except (httpx.TransportError, ConnectionError, OSError):
                    if attempt < self.max_attempts:
                        self._sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    raise ModelConnectionFailure("Unable to connect to Gemini; check your network.") from None
                except Exception:
                    raise ProviderAPIError("Unexpected Gemini SDK failure. No analysis was produced.") from None

                status = getattr(interaction, "status", None)
                status_value = getattr(status, "value", status)
                raw_text = getattr(interaction, "output_text", None)
                if isinstance(raw_text, str) and raw_text.strip() and self.raw_response_observer is not None:
                    try:
                        self.raw_response_observer(raw_text)
                    except Exception:
                        raise ModelResponseFailure(
                            "Raw-response capture failed; evaluation stopped without accepting a report."
                        ) from None
                if status_value not in (None, "completed"):
                    raise ModelResponseFailure("Gemini returned an incomplete or failed interaction.")
                if not isinstance(raw_text, str) or not raw_text.strip():
                    raise ModelResponseFailure("Gemini returned no structured text output.")
                try:
                    parsed = parse_model_response(
                        raw_text,
                        screenplay_text=request.screenplay_text,
                        video_prompt=request.video_prompt,
                    )
                except ModelOutputValidationError:
                    raise ModelResponseFailure(
                        "Gemini returned malformed or unsupported evidence. No result was accepted."
                    ) from None

                usage = getattr(interaction, "usage", None)
                elapsed_ms = round((time.perf_counter() - start) * 1000)
                reported_model = getattr(interaction, "model", None)
                metadata = InferenceMetadata(
                    provider="gemini",
                    model=reported_model if isinstance(reported_model, str) and reported_model else self.settings.model,
                    interaction_id=getattr(interaction, "id", None),
                    completed_at_utc=datetime.now(timezone.utc),
                    duration_ms=max(0, elapsed_ms),
                    attempts=attempt,
                    input_tokens=self._usage_value(usage, "total_input_tokens"),
                    output_tokens=self._usage_value(usage, "total_output_tokens"),
                    total_tokens=self._usage_value(usage, "total_tokens"),
                )
                return ModelInferenceResult(
                    analysis=parsed,
                    metadata=metadata,
                    raw_response_text=raw_text,
                )
        finally:
            if owned_client:
                close = getattr(client, "close", None)
                if callable(close):
                    close()

        raise ModelResponseFailure("Gemini produced no acceptable response.")


def analyze_with_model(
    screenplay: str,
    video_prompt: str,
    shot_scope: ShotType | str,
    shot_intent: str | None = None,
    *,
    adapter: ModelAdapter | None = None,
    secrets: Mapping[str, str] | None = None,
) -> ModelInferenceResult:
    """Public provider-neutral entry point for SceneLock semantic comparison.

    No API key is ever passed as a function argument or printed.
    Subsequent phases can inject any adapter that implements ModelAdapter.
    """
    request = validate_input_payload(
        {
            "screenplay_text": screenplay,
            "video_prompt": video_prompt,
            "shot_type": shot_scope,
            "shot_intent": shot_intent,
        }
    )
    selected_adapter = adapter or GeminiAdapter(load_gemini_settings(secrets=secrets))
    return selected_adapter.analyze(request)
