# SceneLock — Phase 5 Semantic Analysis Verification

**Date:** 8 November 2026  
**Scope:** Three-stage instruction template, one-call orchestration, evidence verification, Python-calculated review status, Streamlit results/reviewer screen.

## Implementation completed

1. **Stage A — Screenplay facts:** Prompt instructs Gemini to extract atomic, quote-grounded critical actions, important props, character identities/positions and explicit visible attributes.
2. **Stage B — Video prompt meaning:** Prompt instructs it to consider faithful paraphrases and Hindi-English terms (e.g., handbag/purse), while preserving actor/action/direction semantics.
3. **Stage C — Shot-aware comparison:** Prompt instructs it to decide applicability first, then choose Supported, Contradicted, Missing, Ambiguous or Not Applicable. A key hidden *before* a reaction close-up is not automatically required in that close-up.
4. **One structured Gemini request:** Kept the Phase 4 `GeminiAdapter` (not a new orchestration framework). `SceneLockAnalyzer` verifies the returned payload and builds an `AnalysisResult` with new UUID, source IDs, provider/model metadata and deterministically calculated counts/status.
5. **Validation protections:** Literal quote containment, ID consistency, one linked finding per concern, no High-severity ambiguity, Missing has null prompt evidence, and no silent prompt rewrite if all findings are Ambiguous/Not Applicable/Supported. Actionable discrepancies must yield a changed suggested prompt.
6. **UI connection:** Enabled the form's Analyse Prompt button. Valid inputs with credentials invoke the provider; failures return an honest error. Verified reports show status, facts, evidence, severity, editable proposed prompt, and independent reviewer decisions. Stale reports are hidden after a changed form is submitted.

**Deliberately postponed to Phase 6:** JSON/CSV export generation. Phase 7 remains responsible for actual Gemini benchmark predictions and precision/recall on the unchanged T01–T15 cases.

## What was actually tested

| Check | Execution | Observed result |
|---|---|---|
| Automated suite | `.venv/bin/python -m pytest -q` | **65 passed** on Python 3.12 local workspace |
| Phase 5 scenario contract tests | Human-authored expected structured outputs injected through fake `ModelAdapter` | **9 of 9 fixture contract validations passed** — not actual Gemini predictions |
| Meera/Arjun reaction close-up | Fixture P5-01 with ignored earlier key hiding, supported facial reaction | **Offline contract pass**; live semantic classification not measured |
| Handbag/purse synonym | Fixture P5-02 | **Offline contract pass**; live semantic classification not measured |
| Reversed Arjun/Meera envelope transfer | Fixture P5-03 | **Offline contract pass**; live semantic classification not measured |
| Missing letter-burning action | Fixture P5-04 | **Offline contract pass**; live semantic classification not measured |
| Generic man/Arjun ambiguity | Fixture P5-05 | **Offline contract pass**; live semantic classification not measured |
| Zoya's conflicting raincoat color | Fixture P5-06 | **Offline contract pass**; live semantic classification not measured |
| Hindi-English red dupatta equivalence | Fixture P5-07 | **Offline contract pass**; live semantic classification not measured |
| Kabir's irrelevant earlier gate action | Fixture P5-08 | **Offline contract pass**; live semantic classification not measured |
| Arjun/Meera reversed positions | Fixture P5-09 | **Offline contract pass**; live semantic classification not measured |
| Streamlit mock result screen | Simulated provider returned P5-03 | Rendered critical count, finding, decision; decision changed without another model request; stale result hidden |
| Actual Gemini inference | `python scripts/live_semantic_smoke.py` | **NOT RUN — no configured key.** No authenticated result or accuracy score exists |

The fixture tests exercise the *real Python pipeline* against human-authored expected classifications. They do **not** test whether Gemini independently identifies these facts or statuses. Since no authenticated call ran, the number of actual semantic model successes and failures is **unknown**, not 9/9.

## Expected status policy exercised

- `Insufficient Context` when zero relevant facts exist or every relevant fact is Ambiguous.
- `Review Required` when a relevant finding is High or Medium, including a meaningful Medium ambiguity.
- `No Significant Issues Detected` when no High/Medium finding exists; Low warnings can remain visible.
- Critical issue count includes only High Missing/Contradicted; warning count includes Medium/Low findings; Not Applicable facts never inflate relevant counts.
- API errors and invalid evidence are **analysis failures**, not successful reports or fabricated zero-issue summaries.

## How to test the live engine on the user's Mac

After the private key setup from the root README:

```bash
python scripts/live_semantic_smoke.py
python scripts/live_semantic_smoke.py --case P5-03
python scripts/live_semantic_smoke.py --case P5-06
```

Each invocation sends **one** synthetic input pair to Gemini and reports model and actual returned review classification without claiming a benchmark score. The script refuses to report success if no key is available or schema/evidence validation fails. Do **not** paste keys into chat.

## Remaining limitations

- No authenticated call could be made here because the environment lacks `GEMINI_API_KEY`, `GOOGLE_API_KEY` and `.streamlit/secrets.toml`.
- Model adherence to all three stages, synonym accuracy, Hindi-English accuracy and correction quality remain unmeasured until the live run.
- Substring/cross-reference validation verifies quotation integrity, **not semantic truth**. Gemini could still make plausible but mistaken classifications; human review remains essential.
- Evidence and prompt data are deliberately not logged to disk automatically; raw model evaluation outputs remain empty.
