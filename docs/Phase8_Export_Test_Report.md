# SceneLock — Phase 8 Export Implementation and Verification

Date: 8 November 2026

## Implemented scope

The existing working Phase 7 Streamlit UI now offers three separate downloads
after a successful, validated inference:

1. **Download JSON** — input fields and scene IDs, validated model facts and
   comparison statuses, evidence-backed findings and severities, computed
   summary counts, model metadata, an independent list of `review_decisions`
   and the separately editable `reviewer_edited_prompt`.
2. **Download CSV** — one row per finding, including the required `finding_id`,
   `category`, `status`, `severity`, `screenplay_evidence`, `prompt_evidence`,
   `explanation`, `suggested_fix`, and `human_decision` columns, plus scene
   identifiers, related fact ID, `comparison_status`, and uncertainty notes.
3. **Download unedited AI response (JSON)** — the original structured model
   response text, preserved separately from the Python report and human
   decisions. The UI does not save it to disk automatically.

An optional authenticated CLI smoke test saves the unaltered response under
`raw_outputs/` for later evaluation using exclusive file creation and
owner-only permissions (where supported). Raw outputs are ignored by Git and
excluded from the distributable ZIP.

## End-to-end verification

The workflow was exercised as:

`AnalysisInput → injected human-authored fixture provider → strict model JSON
and evidence verification → Python AnalysisResult → independent human review
→ JSON/CSV serialization → parse/read-back and field-level assertions`.

Streamlit smoke tests also exercised input validation, the Analyse Prompt
button calling the injected provider, rendered issue cards and metrics,
independent user decision changes, edited prompt persistence, report hiding
after input changes, and clearing raw state on sample reset.

No fixture provider test counts as an actual Gemini inference. Semantic model
quality, accuracy, and production robustness still require a real API key.

## Automated results (executed in this workspace)

| Check | Actual result |
|---|---|
| `python -m pytest -q` | **141 passed in 1.86 s** |
| `python evaluation/validate_dataset.py` | 15 cases, 25 facts, **0 errors** |
| `python -m pip check` | No broken requirements found |
| `python -m compileall -q ...` | Success, exit 0 |
| `python scripts/generate_sample_exports.py` | Produced four JSON/CSV pairs, exit 0 |
| `python scripts/live_semantic_smoke.py --case P5-03` | **NOT RUN**; no key configured, exit 2 |

## Examples actually created

Every example report states `analysis_engine: synthetic_fixture`,
`provider: human_authored_fixture`, and `model: not_a_gemini_result`.
Descriptions and severity labels come from authored expectations, **not** a
model or benchmark.

| Case | Expected outcome | Files |
|---|---|---|
| `P5-01` | No significant issues; 0 findings | JSON and header-only CSV |
| `P5-03` | Reversed envelope handover; High contradiction | JSON and one-row CSV |
| `P5-04` | Required burning action missing; prompt quote is null/blank | JSON and one-row CSV |
| `P8-UNICODE` | Hindi-English costume color mismatch; Medium contradiction | JSON and one-row CSV |

The Unicode case includes Hindi words, embedded quotes, commas and newline
characters. Tests read generated CSV using `utf-8-sig` and `csv.DictReader`,
and JSON using UTF-8 and `json.loads`; source text, evidence, explanation,
human decisions and edited prompt survive the round-trip exactly.

## Safeguards verified

- Model text is checked against its validated payload before constructing a
  report; a mismatch causes an error rather than a downloadable result.
- JSON/CSV construction rechecks evidence quotations and summary counts.
- Reviewer actions are a separate section and cannot mutate the model facts
  or original findings.
- CSV quotes all fields, includes an Excel-friendly Unicode BOM, and escapes
  formula-like leading characters so spreadsheet software will not evaluate
  text supplied by an LLM.
- Missing prompt requirements cannot invent prompt evidence; the CSV uses
  an empty field and JSON uses `null`.
- Zero findings produce an empty JSON `findings` list, empty `review_decisions`
  list and a valid header-only CSV.
- Unknown reviewer finding IDs, mismatched scene IDs and unrelated screenplays
  cause export errors.
- Raw response archives preserve bytes, refuse overwrites, and reject unsafe
  file identifiers.
- Unconfigured or failed API calls never show a successful report or exports.

## Honest limitations

The run proved software wiring and deterministic safeguards, not Gemini
semantic performance. Evidence substring checks establish the existence of
quoted passages, but cannot guarantee an AI's interpretation of the story.
The full **live** `INPUT → ANALYSIS → VALIDATION → HUMAN REVIEW → EXPORT`
workflow is implemented and UI-tested using injected fixtures; an authenticated
end-to-end Gemini run remains pending a privately configured key. There is no
automatic cloud storage, public deployment or model benchmark in Phase 8.
