"""Configuration tests: no network or external API calls."""

import pytest
import streamlit as st

from model_adapter import (
    DEFAULT_GEMINI_MODEL,
    GeminiAdapter,
    GeminiConfigurationError,
    load_gemini_settings,
)


def test_missing_key_does_not_break_setup() -> None:
    settings = load_gemini_settings(environ={}, secrets={})
    assert not settings.is_configured
    assert settings.model == DEFAULT_GEMINI_MODEL


def test_key_can_come_from_streamlit_secrets() -> None:
    settings = load_gemini_settings(environ={}, secrets={"GEMINI_API_KEY": "secret-example"})
    assert settings.is_configured
    assert "secret-example" not in repr(settings)


def test_streamlit_managed_secrets_are_loaded_automatically(monkeypatch) -> None:
    monkeypatch.setattr(st, "secrets", {"GEMINI_API_KEY": "managed-test-key", "GEMINI_MODEL": "managed-test-model"})
    settings = load_gemini_settings(environ={})
    assert settings.api_key == "managed-test-key"
    assert settings.model == "managed-test-model"


def test_environment_takes_priority_and_model_is_configurable() -> None:
    settings = load_gemini_settings(
        environ={"GEMINI_API_KEY": "env-key", "GEMINI_MODEL": "custom-model"},
        secrets={"GEMINI_API_KEY": "secrets-key"},
    )
    assert settings.api_key == "env-key"
    assert settings.model == "custom-model"


def test_google_api_key_has_official_priority_over_gemini_env_key() -> None:
    settings = load_gemini_settings(
        environ={"GOOGLE_API_KEY": "google-key", "GEMINI_API_KEY": "gemini-key"},
        secrets={},
    )
    assert settings.api_key == "google-key"


def test_placeholder_is_not_a_valid_key() -> None:
    settings = load_gemini_settings(environ={}, secrets={"GEMINI_API_KEY": "YOUR_API_KEY_HERE"})
    assert not settings.is_configured


def test_client_fails_cleanly_without_key() -> None:
    adapter = GeminiAdapter(load_gemini_settings(environ={}, secrets={}))
    with pytest.raises(GeminiConfigurationError, match="GEMINI_API_KEY"):
        adapter.create_client()
