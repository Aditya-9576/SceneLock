# SceneLock — Phase 9 Engineering Testing and Evaluation

**Date:** 8 November 2026  
**Project:** Kuku AI Generalist Assignment, Problem Statement 3  
**Evaluation state:** Offline engineering QA complete; authenticated Gemini evaluation **BLOCKED** (no API key).

## Executive outcome

The actual SceneLock Python application, Gemini adapter, deterministic
validation, raw-response archiving, issue scorer and Streamlit interface were
retested. The complete automated suite passed **173 tests**. All **15 original
Phase 2 cases** and **25 human-authored fact labels** remain intact. A new
runner is ready to submit those exact inputs and three additional unseen
cases to Gemini when credentials become available.

**No authenticated Gemini inference occurred during Phase 9.** The honest
evaluation manifest contains **18 `not_run_no_credentials` records** and
`model_issue_metrics: null`. There are **no** `raw_outputs/T01_response.json`
through `T15_response.json` files, because no genuine responses exist.
Neither AI precision/recall, model latency nor a specific Gemini AI mistake
can be reported. Creating synthetic responses at those paths would be false
evidence and was intentionally prohibited.

## 1. Executed checks and real outcomes

| Test or diagnostic | Actual observed result | Interpretation |
|---|---|---|
| `python -m pytest -q` | **173 passed in 1.97 s** | Unit, adapter, UI and simulated end-to-end checks passed |
| `python evaluation/validate_dataset.py` | 15 cases, 25 facts, **0 errors** | Ground-truth integrity maintained |
| `python evaluation/keyword_baseline.py` | 2 TP, 3 FP, 5 TN, 5 FN | Real deterministic **case-level** keyword baseline only |
| `python evaluation/run_phase9.py` | Exit 2: `BLOCKED_NO_GEMINI_API_KEY` | **0 of 18 real Gemini requests**; no model metrics |
| `python evaluation/generate_failure_log.py` | 2 actual baseline misclassifications logged in detail | Not Gemini mistakes |
| `python -m pip check` | No broken requirements found | Local dependency consistency |
| `python -m compileall -q ...` | Exit 0 | All modified Python modules compile |
| Unseen case schema/evidence validation | **3 of 3** passed | Their manually authored fixtures are internally valid; no Gemini inference |
| Streamlit UI smoke tests | Passed inside the pytest suite | Input, review and downloads remain wired to the validated pipeline |

An additional mocked run exercised **all 18 cases** through the real
`SceneLockAnalyzer`, validators, scorer and raw archiver, producing all
expected raw filenames **inside a temporary test folder**. Another test used
the actual Gemini adapter with a simulated SDK to prove that one malformed
response and one rate-limit failure are counted separately; the malformed raw
text was retained, and no invalid analysis was accepted. These are **software
integration checks, not authenticated inference or model performance**.

## 2. Model issue-level metrics — correctly not measured

| Metric | Actual Gemini result | Why unavailable |
|---|---|---|
| T01–T15 processed by Gemini | **0 / 15** | No API key |
| Unseen U01–U03 processed by Gemini | **0 / 3** | No API key |
| Correct semantic matches | **Not measured** | No predictions |
| Issue-level precision | **Not measured (`null`)** | No validated predictions |
| Issue-level recall | **Not measured (`null`)** | No validated predictions |
| Model false positives / false negatives | **Not measured** | No predictions |
| Model shot-scope mistakes | **Not measured** | No predictions |
| Model evidence-validation failure rate | **Not measured** | No API responses |
| Real API failures / rate limits | **Not observed** | No API requests |
| Model inference latency | **Not measured** | No API requests |
| Actual Gemini mistake and retest | **Not observed / not run** | No predictions to inspect |

Do not confuse simulated API errors from automated tests with actual provider
failures. The manifest reports `api_failure_count: 0` simply because no
request was attempted; it explicitly lists unmeasured fields and does not
assert a 0% provider failure rate.

### How the scorer will calculate real metrics

The original annotations cover **25 facts** across 15 cases:

- Supported: **14**
- Contradicted: **6**
- Missing: **1**
- Ambiguous: **1**
- Not Applicable: **3**

There are **7 confirmed High/Medium Contradicted or Missing labeled facts**.
`evaluation/score_predictions.py` aligns a model fact and a gold fact when
their **category** is identical and their exact screenplay evidence spans
overlap by at least 60% of the shorter span. Alignment is **one-to-one**;
arbitrary model IDs are not treated as stable gold identifiers.

Issue-level confirmed positive = a matched High/Medium **Contradicted** or
**Missing** finding. The scorer reports:

\[
\mathrm{Precision} = \frac{TP}{TP + FP}, \qquad
\mathrm{Recall} = \frac{TP}{TP + FN}
\]

Both ratios are **`null` when their denominator is zero**. Missing predictions
for positively labeled facts are false negatives. Predictions of confirmed
issues for aligned Supported/Not Applicable/Ambiguous facts are false
positives. Additional model findings with no matching human annotation are
**unadjudicated**, not automatically false positives, because the existing
labels are partial. This limitation will be shown alongside any future
metrics. Scope mistakes, severity/status disagreements, ambiguity matches and
per-case latency are reported separately. Failed API calls or evidence-invalid
outputs are counted as failures, not silently converted into negative
predictions.

## 3. Actual observed baseline mistakes — not Gemini mistakes

The frozen Phase 2 **keyword-matching baseline** was re-executed on T01–T15.
Its real **case-level** confusion matrix was:

| TP | FP | TN | FN | Precision | Recall |
|---:|---:|---:|---:|---:|---:|
| 2 | 3 | 5 | 5 | **40.0%** | **28.57%** |

These are **case-level binary keyword metrics**, not model predictions and
not the issue-level metrics defined above. The baseline produced 8 errors,
including the following two whose actual inputs and outputs are stored in
`evaluation/phase9_failure_log.json`.

### Observed error A — T06: false positive from ignoring shot scope

**Screenplay:** “Nila tucks a brass key into her coat pocket and then turns
toward the sound of shattered glass, visibly frightened.”

**Video prompt:** “Tight close-up of Nila's frightened face as she turns toward
the sound of breaking glass.”

**Shot type and intent:** Character close-up; only Nila's frightened reaction
**after** hiding the key. The hiding action belongs to the earlier beat.

**Actual wrong baseline prediction:** `predicted_has_confirmed_issue = true`
with lexical recall **0.4167** (threshold 0.50). Human-authored expected status:
**No Significant Issues Detected**, because the hidden key action is **Not
Applicable** to this later reaction shot.

**Root cause:** The keyword baseline ignores shot type and temporal intent,
mistaking missing lexical tokens for an omitted visible action.

**Correction:** Updated `prompts.py` to version
`scenelock-semantic-v3-phase9`, requiring an explicit before/after and
off-frame applicability check **before** reporting Missing.

**Retest:** The new prompt-contract regression test passes. The intentionally
frozen keyword baseline still makes the same error, which preserves the
original comparison. **Whether Gemini improves is untested** without a key.

### Observed error B — T14: false negative from reversed roles

**Screenplay:** “Ritika hands the antidote vial to Dr. Karan, who is too weak
to reach for it.”

**Video prompt:** “Dr. Karan hands the antidote vial to Ritika as she reaches
out to receive it.”

**Shot intent:** Show Ritika delivering the antidote to Dr. Karan.

**Actual wrong baseline prediction:** `predicted_has_confirmed_issue = false`
with lexical recall **0.6667**. Human-authored expected status: **Review
Required** because the giver/recipient roles are explicitly reversed.

**Root cause:** Token overlap sees “Ritika”, “Karan”, “hands”, “antidote” but
cannot represent direction or role assignment.

**Correction:** The updated AI instruction template explicitly checks actor,
recipient and temporal direction even when most tokens match.

**Retest:** The instruction-contract test passes; the keyword baseline remains
an unchanged, reproducible failure. **No real Gemini retest was possible**.

## 4. Reproduced and fixed implementation defects

These are **actual code bugs**, not speculative AI predictions.

**CODE-01 — Invisible Unicode was accepted as nonempty content.** A failing
Phase 9 test demonstrated that screenplay text or shot intent consisting only
of U+200B/U+200C/U+200D passed input validation. Another failing test showed
an invisible-only source quote could count as evidence when it appeared
literally in a longer screenplay. Cause: Python's `str.strip()` does not
remove zero-width format characters. `schemas.py` now requires visible Unicode
content; `validators.py` enforces the same on evidence quotes. The three
regression tests now pass.

**CODE-02 — Rejected provider text could vanish before evaluation.** An
initially failing test demonstrated no mechanism to preserve the raw
structured output if evidence validation rejected it. A second failure
showed an incomplete interaction was rejected before its available raw text
could be observed. `GeminiAdapter` now accepts an optional evaluation-only
`raw_response_observer` called **before** response validation/status
rejection. The raw archiver can save exact text under the required stable
case filename and refuses overwrites. The Streamlit UI still does not
automatically save user content. Both regression tests now pass.

## 5. Edge-case and adversarial test matrix

| Scenario | How tested | Observed outcome |
|---|---|---|
| Invalid API key / 401 and 403 | Injected SDK error codes through actual adapter | Typed `AuthenticationFailure`, no fake report |
| Rate limit / 429 | Injected SDK error; retry boundary tested | Typed `RateLimitFailure` or recovered after bounded retry |
| Timeout | Injected HTTP timeout | Typed `ModelTimeoutFailure`, no fake report |
| Connection failure | Injected HTTP transport error | Typed connection error |
| Malformed and incomplete responses | Injected raw SDK payloads | Rejected; available raw text preserved by optional observer |
| Duplicate JSON keys | Injected ambiguous JSON | Rejected by parser |
| Fabricated screenplay evidence | Injected nonexistent screenplay quote | Rejected by evidence validator |
| Fabricated prompt evidence | Injected nonexistent prompt quote | Rejected by evidence validator |
| Empty / Unicode-invisible inputs | Input-validation boundary | Rejected after actual regression fix |
| Uncertain character identity | Manually labeled unfamiliar/human-authored fixtures | Ambiguous rather than proven contradiction in offline pipeline |
| Prompt injection | Simulated attacker directives in screenplay, prompt and shot intent | Strings remained **data** in JSON input, never became system instructions |
| Hindi, multiline, quotes and commas | Schema and export round-trips | Preserved in offline validated reports |

The injected provider errors and prompt-injection transport tests check the
implementation; they **do not** prove how the real Gemini model would respond
to adversarial text. Model semantic resilience is a remaining live test.

## 6. Three previously unseen scenes

The new `evaluation/unseen_phase9_cases.json` contains:

1. **U01:** Farah folds and launches a paper boat into a rain puddle;
   wording paraphrases the action (expected Supported).
2. **U02:** Dev closes a steel hatch before Nisha climbs; the video prompt
   reverses the actions (expected Contradicted, High).
3. **U03:** A Hindi screenplay names मीरा, but the English prompt only
   identifies “a woman” (expected Ambiguous, Medium).

All three inputs and expected fixture replies were validated through the
real Pydantic/evidence contracts. A mock-provider run exercised the full
analysis runner for each. **Actual Gemini runs: 0/3; semantic predictions
are still unknown.** These scenes remain separate from the original Phase 2
dataset and are not inserted into the system prompt as examples.

## 7. Provenance, raw files and reproducibility

The unchanged Phase 2 ground-truth file SHA-256 is:

`4fd9b3b5353d6c0c2510cfaf2ef1a1cb8d0108ab14c04a2c4bc8c3a183b4891c`

The frozen keyword baseline's actual predictions remain in
`evaluation/baseline_predictions.json` and its measured summary in
`evaluation/baseline_summary.json`. The two documented error examples and
their original source text are in `evaluation/phase9_failure_log.json`.
The actual no-key run state is saved in `evaluation/phase9_live_summary.json`.
No `raw_outputs/T##_response.json` files were produced from mock tests in the
distributable project; mocked raw data was contained to temporary test dirs.

The evaluation runner:

1. Verifies original labels and logs the source labels' SHA-256.
2. Checks private Gemini settings from environment or Streamlit secrets.
3. If absent, writes an honest blocked manifest **without API calls**.
4. If present, submits exactly T01–T15 and U01–U03 through the **real** Gemini
   adapter without sending expected labels to the model.
5. Captures any returned raw text unmodified and **exclusively** as
   `raw_outputs/T01_response.json` (and corresponding other IDs), even if its
   structured content later fails validation.
6. Counts actual API errors separately from rejected model content; scores
   only fully validated cases, labels unmatched facts as unadjudicated, and
   writes per-case and aggregate results.

To run it on a Mac (after installing dependencies and configuring a key
privately), execute `python evaluation/run_phase9.py` inside SceneLock.
Never paste API keys into chat or include local secrets/raw private screenplay
outputs in public repositories. Existing raw filenames are never overwritten.

## 8. Remaining limitations and delivery decision

- A Gemini API key and a permitted account quota are needed to achieve the
  requested **real 15-case model evaluation** and three new live tests.
- A real Gemini misprediction cannot be identified or corrected/retested
  without actual Gemini output. The documented T06/T14 mistakes belong to the
  deterministic baseline **only**.
- The strengthened v3 instructions have passed static tests but have **no
  measured model-quality improvement** yet.
- Partial manual labels mean any unmatched model finding needs later human
  adjudication. Evidence overlap alignment is not a semantic oracle.
- No public deployment, user data storage or independently adjudicated
  production-quality benchmark was attempted in Phase 9.

**Status:** Phase 9 implementation, regression repairs, non-API evaluation,
test artifacts and reproduction documentation are complete. Authenticated
model metrics and raw T01–T15 replies are explicitly **blocked**. Do not
represent this report as having completed a live model quality evaluation.
