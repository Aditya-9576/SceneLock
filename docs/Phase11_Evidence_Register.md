# SceneLock - source and measurement register

## Provenance for the two-page solution

| PDF statement | Actual source / file | Evidence boundary |
|---|---|---|
| Kuku uses AI-generated microdrama | `Kuku - AI Generalist Assignment.pdf`, p. 1 | Assignment is direct context; not independent study of artist error rates |
| Problem 3 asks for a narrow prototype | Same PDF, pp. 3-5 | Assignment requirement, not a validation result |
| Video prompts include scene subjects/actions | Official Runway Text-to-Video Prompting Guide | General industry guidance only; does not measure errors at Kuku |
| SceneLock examines shot-level script/prompt alignment | `app.py`, `analyzer.py`, `prompts.py`, `validators.py` | Implementation verified using code and offline tests; Gemini predictions unverified |
| 15 labeled cases, 25 facts | `sample_inputs/test_cases.json`, `evaluation/expected_labels.json` | All human-authored fictional examples |
| Baseline precision 40%, recall 28.6% | `evaluation/baseline_summary.json` | 2 TP, 3 FP, 5 TN, 5 FN, **case-level keyword baseline only** |
| Observed T06 baseline false positive | `evaluation/phase9_failure_log.json` | Root cause shot-scope ignorance; frozen baseline still wrong |
| Corrected prompt instructions tested | `prompts.py`, `tests/test_phase9_adversarial.py` | Regression confirms instruction wording/contract; **not live Gemini improvement** |
| Software test count | Final re-execution `python -m pytest -q`: **187 passed on 2026-11-08** | Tests include mocks, not a model-accuracy benchmark |
| HTTP readiness | `scripts/local_deployment_smoke.py` returned HTTP 200 | Local health only; no public URL |
| Gemini predictions and latency | `evaluation/phase9_live_summary.json` | 18 attempts **not run** because no key; all model metrics null |
| Cost method | [Official Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) | Pricing changes; no measured input/output tokens or billing |
| Prototype delivery | Local Git repository, runnable ZIP; `DEPLOYMENT.md` | No authorized public GitHub/Streamlit deployment verified |

## Important distinction

The **actual code bugs** fixed in Phase 9 include invisible Unicode that
previously passed some input/evidence checks and an observer path needed to
retain rejected raw provider text. The **keyword baseline's** T06 and T14
mistakes are observed algorithm errors. They are **not authenticated Gemini
model errors**. No claim of improved live Gemini behavior can be made without
first running the model and scoring its answers against untouched labels.

The final independent QA newly found and fixed (a) punctuation-only screenplay,
prompt and supposed evidence being accepted as meaningful text, and (b) two
placeholder Gemini API key strings being misreported as configured credentials.
The corresponding new tests failed before the changes and passed afterward;
the full suite finished at **187 passed**. A new fictional Saira reaction
close-up was exercised with a **manually authored mock adapter**, demonstrating
the actual code's `Not Applicable` / header-only CSV pathway but **not**
Gemini's real-world shot-scope accuracy.

## Explicitly unmeasured

- Real production errors at Kuku, hours saved, video regeneration reduction,
  per-shot cost, weekly shot throughput.
- Gemini issue-level precision/recall, semantic accuracy, false positive rate,
  shot-scope error rate, real API latency, safety resilience.
- Actual public demo URL uptime, authenticated API success and external access.

For these claims, the proposed next experiment is a blinded artist review:
sample actual permitted shots, compare human adjudications with model findings,
measure review time and true prompt changes, and compare avoided regeneration
cost against token usage. No such pilot has been performed.
