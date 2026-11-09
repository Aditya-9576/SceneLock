# SceneLock — Phase 6 Structured Output and Reliability Report

**Date:** 8 November 2026  
**Scope:** Schema hardening, strict response decoding, evidence verification, severity consistency, deterministic report validation, clear provider-failure separation, and reviewed JSON/CSV exports.

## Completed implementation

| Layer | Verification policy |
|---|---|
| Gemini response decoding | Exactly one UTF-8 JSON object; reject empty/trailing JSON, duplicate keys, NaN/Infinity, invalid Unicode, oversized response and unknown fields |
| Pydantic output contracts | Required typed fields for `ScreenplayFact`, `Finding`, `AnalysisMetadata`, `LLMAnalysisPayload`, `AnalysisResult`, `ReviewDecision`; exact status/category/severity enums |
| Required prose | Reject blank IDs, factual descriptions, evidence, applicability explanations and fixes; model facts/findings capped at 80 each |
| Reference integrity | Unique fact IDs and finding IDs, no duplicated identical atomic facts, findings link existing fact IDs, one finding per concern, category/status match |
| Evidence integrity | Exact nonblank screenplay quotations; non-missing prompt evidence must occur verbatim in original video prompt; `Missing` cannot invent prompt evidence |
| Severity logic | High only for proven Missing/Contradicted findings (High Ambiguous rejected); Medium and Low warnings remain separate |
| Deterministic summary | All fact/issue counts and three successful review statuses calculated in Python; Pydantic `AnalysisResult` independently rejects contradictory counts/status |
| API errors | Auth, quota, timeout, transport, malformed and service failures remain typed exceptions, not valid reports or `Insufficient Context` |
| Safe exports | JSON includes actual input, analysis, summary, editable reviewer prompt and independent review decisions; CSV includes one row per finding or just headers if empty; spreadsheet formula injection escaped |
| UI behavior | Downloads shown only for the current successful report, hidden after source edits or failures; no automatic raw-output persistence |

## Actual verification performed

- **Automated tests:** `python -m pytest -q` — **115 passed** on local Python 3.12 environment, including adversarial malformed-response/quote/reference tests and Streamlit mocked-result smoke tests.
- **Original Phase 2 dataset validation:** 15 cases, 25 expected facts, **0 errors**. Original expected labels were not modified.
- **Python compilation:** `python -m compileall` on application, scripts, tests and evaluation — passed.
- **Dependency check:** `python -m pip check` — no broken requirements.
- **Live Gemini semantic test:** `python scripts/live_semantic_smoke.py` — **NOT RUN**, no API key configured; no authenticated call or model accuracy is claimed.
- **Streamlit UI:** In-process AppTest exercised successful mocked report rendering, human decision changes, stale-report protection and absence of success/downloads without credentials. Streamlit process itself started, but a separate-shell local HTTP probe could not connect in this workspace; no HTTP health-check success is claimed.

### Adversarial classes covered

1. Missing required fields; empty/whitespace fact IDs, evidence, explanations and suggested fixes.
2. Unknown comparison statuses, detection categories and severities.
3. Malformed JSON, duplicate object keys (including nested objects), non-finite values, unexpected fields, oversized response, non-object payloads.
4. Invented screenplay and prompt quotations; invented prompt evidence for a Missing fact.
5. Unknown fact references, duplicate IDs, duplicate atomic facts, repeated finding for one fact, category/status disagreements and missing required findings.
6. High-severity ambiguity, ambiguous-only corrected prompt changes, actionable mismatch with no correction.
7. Invalid metadata timestamps or provenance and mismatched/fabricated summary counts or overall status.
8. Auth/quota/provider failures versus a valid `Insufficient Context` report.
9. Unknown reviewer decision IDs, invalid decision values, report/input mismatch, zero-issue CSV headers, malicious spreadsheet formula-looking strings.

The first expanded test run exposed an assertion that provided whitespace-only data rather than an oversized nonblank payload. The assertion was corrected to target the response-size limit. A separate UI test had assumed Streamlit's testing library would expose download buttons as ordinary buttons; it was corrected to test rendered download sections and separately verify the actual produced JSON/CSV bytes. The **final suite is green**.

## Explicit limitations and next phase

These checks prevent **unverified quotations, malformed structures, invalid references and inconsistent count/status arithmetic** from being accepted. They cannot prove that a quoted sentence was **interpreted correctly**: synonymous wording, causal relations and shot intent still depend on Gemini and human review. No real-model benchmark or guaranteed accuracy claim is made.

Phase 7 should perform authenticated Gemini runs on the unchanged T01–T15 cases, capture genuine raw model results safely, compare against human ground truth, and report precision/recall with limitations. Keep API keys out of chat, source files, exports and ZIPs.
