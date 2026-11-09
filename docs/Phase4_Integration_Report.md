# SceneLock — Phase 4 Gemini Integration and Verification Report

**Date:** 8 November 2026  
**Scope:** Genuine, replaceable Gemini interface; structured semantic output; safe authentication and failure handling. Streamlit review/results UI remains Phase 5.

## Implementation decisions

| Decision | Implemented choice |
|---|---|
| Provider/API | Google Gemini SDK `google-genai` v2, `client.interactions.create(...)` |
| Default model | `gemini-3.6-flash`, an officially documented stable Flash model with structured outputs and a free-tier route |
| Other models | Override `GEMINI_MODEL` in an environment variable or Streamlit secrets |
| Structured response | Pydantic JSON schema for `LLMAnalysisPayload` (facts, findings, corrected prompt) |
| Replaceable contract | `ModelAdapter` Protocol with `.analyze(AnalysisInput) -> ModelInferenceResult` |
| Public entry point | `analyze_with_model(screenplay, video_prompt, shot_scope, shot_intent)` |
| Credential sources | `GOOGLE_API_KEY`, `GEMINI_API_KEY`, or Streamlit-managed secrets; no hard-coded secrets |
| Time budget/retries | 45-second provider timeout, at most 2 attempts on transient errors |
| Returned metadata | Provider, requested/reported model, interaction ID, UTC completion, duration, attempts and available token counts |
| Server storage | `store=False`; SceneLock does not write the raw provider output or inputs to local files |
| Evidence checking | Facts must quote screenplay literally; findings link unique facts and quote supplied prompt literally when required |

## Failure handling

| Condition | SceneLock error behavior |
|---|---|
| Missing credentials | `GeminiConfigurationError`; no request started |
| HTTP 401 or 403 | `AuthenticationFailure`; do not retry |
| HTTP 429 | `RateLimitFailure`; bounded retry |
| HTTP 408/504 or HTTP-client timeout | `ModelTimeoutFailure`; bounded retry |
| Transport/connection failure | `ModelConnectionFailure`; bounded retry |
| HTTP 500/502/503 | `ProviderAPIError`; bounded retry |
| Non-retryable provider error | `ProviderAPIError` with HTTP status, without provider's unfiltered message |
| Empty, malformed, incomplete or unsupported evidence | `ModelResponseFailure`; reject result without accepting fabricated claims |

The typed exceptions are available for the Phase 5 user interface to display appropriate messages. A syntactically valid model response is **not** assumed to be a semantically accurate verdict.

## Commands and observed verification

| Check | Actual result |
|---|---|
| Install upgraded dependencies | `google-genai 2.34.0` and `socksio 1.0.0` installed into Python 3.12 virtual environment |
| SDK constructor and interface | Local `genai.Client` initialized with non-real dummy string; `interactions.create` exposed; **no network call** |
| Mocked adapter and regression tests | **46 passed** with `python -m pytest -q` (latest Phase 4 run) |
| Auth / rate-limit / timeout / transport / malformed JSON handling | Exercised using faked SDK interactions and errors, **not live provider errors** |
| Actual authenticated Gemini inference | **NOT RUN.** No `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or local Streamlit secrets were configured in this workspace |
| Phase 2 labeling and keyword baseline | Preserved; no LLM evaluation or accuracy metrics calculated in Phase 4 |

### Authenticated request pathway for the next local run

1. Visit [Google AI Studio API Keys](https://aistudio.google.com/api-keys) and create or select a personal Gemini API key.
2. Activate the project environment and run `python scripts/setup_gemini_key.py` on your own Mac. This obtains the key via a **hidden Terminal prompt** and stores it in an ignored, user-only `.streamlit/secrets.toml` file.
3. Run `python scripts/live_gemini_smoke.py` from the project root. The script sends exactly one synthetic red-dress/blue-dress example through `analyze_with_model` and prints safe metadata/counts, or prints a transparent failure/skip reason. It makes no claim about benchmark accuracy.
4. Keep keys out of chat, source files, Git history, screenshots and the distributed ZIP.

## Official references checked

- [Gemini models — 3.6 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash)
- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Interactions API overview](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [API key management](https://ai.google.dev/gemini-api/docs/api-key)
- [API errors and troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting)

## Explicit limits and Phase 5 handoff

- The **Streamlit input validation screen** remains operational, but its **Analyse Prompt** button is disabled. Hook the existing `SceneLockAnalyzer` and `ModelInferenceResult` to the UI in Phase 5.
- The API endpoint, access to `gemini-3.6-flash`, and provider acceptance of this exact schema **still require a real authenticated smoke run** in the user's account. The mock-based evidence is not a substitute.
- Human review workflow, computed summary counts, downloadable analysis exports and model-quality evaluation are intentionally out of Phase 4 scope.
- Preserve the original 15 T01–T15 screenplay/prompt test cases and 25 authored expected facts without changes for later evaluation.
