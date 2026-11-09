# SceneLock — Phase 2 Evaluation Dataset

**Dataset ID:** `scenelock-original-eval-v1`  
**Version:** 1.0, 8 November 2026  
**Phase:** 2 — evaluation fixtures and deterministic baseline  
**Status:** Complete; no Gemini/LLM calls have been made

## What this package contains

This package supplies **15 original, synthetic** screenplay-to-video-prompt examples (T01 through T15), with deliberately authored reference labels and a weak but reproducible keyword-matching baseline. The scenes are fictional and are **not** copied from Kuku's confidential input pack. They are designed to test both true discrepancies and situations where an attentive reviewer should **not** raise an error.

These reference labels are a first-pass project gold standard, not independent expert adjudication. Phase 3 and later should preserve the labels as written for honest regression testing. If a later reviewer identifies a real labeling mistake, create a new version and document why the label changed; do not retroactively change it merely because a model disagreed.

## Files

```text
SceneLock_Phase2/
├── README.md
├── sample_inputs/
│   └── test_cases.json
└── evaluation/
    ├── expected_labels.json
    ├── validate_dataset.py
    ├── keyword_baseline.py
    ├── baseline_predictions.json
    └── baseline_summary.json
```

- `sample_inputs/test_cases.json`: exactly 15 screenplay/prompt pairs with shot type, shot intent, episode/scene/shot IDs, scenario metadata, and demo-candidate markers.
- `evaluation/expected_labels.json`: 25 expected screenplay facts, each with exact source evidence, category, expected comparison status, issue type (if any), severity (if any), matching prompt evidence when present, and an explanation. Also supplies the expected case-level review status.
- `evaluation/validate_dataset.py`: checks the 15-case ID set, required fields and enums, coverage, evidence substrings, severity/status compatibility, duplicate IDs, and consistency of case-level review status with fact labels.
- `evaluation/keyword_baseline.py`: a **binary case-level lexical-overlap baseline**, deliberately limited. It has no LLM or API dependency.
- `evaluation/baseline_predictions.json`: reproducible, actual baseline predictions for the 15 examples.
- `evaluation/baseline_summary.json`: genuine baseline-only confusion matrix, precision, recall, errors, and caveats.

## Case inventory

| Test | Challenge | Expected review status | Confirmed issue? | Demo? |
|---|---|---|---|---|
| T01 | Red vs blue dress, important visual identification signal | Review Required | Yes | Yes |
| T02 | Black vs white jacket | Review Required | Yes | No |
| T03 | Handbag vs purse synonyms | No Significant Issues Detected | No | Yes |
| T04 | Places vs slips key into bag | No Significant Issues Detected | No | No |
| T05 | Destruction of signed confession letter omitted | Review Required | Yes | Yes |
| T06 | Earlier key hiding excluded from a reaction close-up | No Significant Issues Detected | No | Yes |
| T07 | Interior wristwatch irrelevant to exterior establishing shot | No Significant Issues Detected | No | No |
| T08 | All important actions correctly represented | No Significant Issues Detected | No | No |
| T09 | Ambiguous man/woman identity vs named characters | Insufficient Context | No confirmed contradiction | Yes |
| T10 | Compatible cinematic lighting addition | No Significant Issues Detected | No | No |
| T11 | Doorway blocker relocated to sofa | Review Required | Yes | No |
| T12 | Plot-critical purple envelope changed to orange | Review Required | Yes | No |
| T13 | Locking and key handoff reversed | Review Required | Yes | No |
| T14 | Antidote giver and receiver swapped | Review Required | Yes | No |
| T15 | Hindi-English code switching and a later out-of-scope action | No Significant Issues Detected | No | Yes |

**Important label distinction:** `Ambiguous` is an unresolved review concern, not a confirmed screenplay mismatch. For binary baseline evaluation, a case is positive only when it contains at least one **High/Medium `Contradicted` or `Missing`** fact. Thus T09 is a negative case for *confirmed error detection* but its expected overall status is `Insufficient Context`.

## Required coverage and label policy

All four detection categories appear: `critical_action`, `important_prop`, `character_identity_position`, and `explicit_visual_attribute`.

All five comparison statuses appear: `Supported`, `Contradicted`, `Missing`, `Ambiguous`, and `Not Applicable`.

Facts with `Supported` or `Not Applicable` have no issue type and no severity. `Missing` facts must not invent prompt evidence. Every evidence quotation is required to be an exact substring of the relevant input. An irrelevant omission is `Not Applicable`, never `Missing`. A possible but unconfirmed identity mapping remains `Ambiguous`, never a definite contradiction.

## How to validate the data

With Python 3 installed, open a terminal in this package directory and run:

```bash
python3 evaluation/validate_dataset.py
```

The script exits with code 0 only when every consistency check passes. It prints counts and exact errors if something is wrong. There are no external Python dependencies.

## How the keyword baseline works

The baseline **only reads raw screenplay and prompt text when making a prediction**. It case-folds words, removes common English stopwords, compares the remaining unique words, and flags a potential issue when screenplay-word recall in the prompt is below a fixed **0.50** threshold.

It deliberately does **not** understand synonyms, shot scope, Hindi-English translation, identities, causal order, or the difference between a contradiction and a missing detail. It emits **only** a binary potential-issue flag, not five-way fact statuses. It is a fair end-to-end lexical comparator for *binary case-level error detection*, but **not** directly comparable to an LLM's fact-level status/severity performance.

To rerun:

```bash
python3 evaluation/keyword_baseline.py
```

This recreates `baseline_predictions.json` and `baseline_summary.json` from the actual algorithm and data; no metrics are typed in manually.

### Actual deterministic baseline results (not LLM results)

| Metric | Result |
|---|---:|
| Test cases | 15 |
| True positives | 2 |
| False positives | 3 |
| True negatives | 5 |
| False negatives | 5 |
| Precision | 40.00% |
| Recall | 28.57% |

This intentionally simple method often overlooks color, action-order and role conflicts because many surrounding words still match. It also generates false alarms for valid close-ups, interior props outside the shot, and Hindi-English wording. These outcomes are observations from the included deterministic run, **not** results from any Gemini model.

## Recommended final live-demo sequence

1. **T01:** Obvious visual contradiction; easy to explain within seconds.
2. **T05:** Crucial story action omitted; illustrates production impact.
3. **T03:** Equivalent wording should not produce a false alarm.
4. **T06:** Shot intent should prevent an invalid omission warning.
5. **T09:** Uncertain character identity must stay uncertain.
6. **T15:** Optional multilingual demonstration; treat reliability as unproven until the model is evaluated.

For the final interview, also run **one new, unseen input** entered live rather than relying only on these authored cases.

## How Phase 3 should use the package

1. Keep both original JSON files unchanged as the Phase 2 baseline dataset.
2. Feed the future LLM only the five input groups (`screenplay_text`, `video_prompt`, `shot_type`, `shot_intent`, IDs). Do **not** feed it `scenario`, `tags`, `demo_candidate`, or any expected labels.
3. Run the real analysis engine on each case and save unedited raw model responses separately.
4. Compare the LLM's fact-level classifications to `expected_facts` with a documented matching policy. Report genuine disagreement cases transparently.
5. Derive a binary confirmed-issue label from future LLM findings for a fair case-level comparison to this lexical baseline.
6. Do not claim the 15 cases establish production-wide accuracy; expand evaluation with independently reviewed, realistic data in later phases.

## Limitations

- Synthetic cases cannot by themselves prove that Kuku currently has this workflow gap.
- Labels were carefully specified and structurally checked but have not been adjudicated by an independent video-production expert.
- Baseline metrics are on this small dataset only and should not be extrapolated to production.
- There are no model calls, provider credentials, deployed apps, or model quality results in Phase 2.

