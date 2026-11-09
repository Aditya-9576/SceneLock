# SceneLock — Phase 1 Project Specification

**Document ID:** SCENELOCK-SPEC-001  
**Version:** 1.0 (requirements baseline)  
**Date:** 8 November 2026  
**Project:** SceneLock — AI Pre-Generation Quality Assurance for Microdrama Production  
**Assignment:** Kuku AI Generalist Assignment, Problem Statement 3  
**Owner:** Aditya Gautam  
**Status:** Phase 1 complete; application implementation not started

> **Instruction for subsequent phases:** This document is the agreed requirements baseline. Implement and test against its acceptance criteria. Avoid adding features without a specific demonstrated need. If an implementation constraint makes a requirement impractical, document the deviation and reason before changing behavior.

## 1. Product decision and problem framing

### 1.1 Problem

During the proposed screenplay-to-AI-video workflow, an artist may write a generation prompt that changes, omits, or ambiguously represents important scripted actions, props, character identities, positions, or explicitly required visual attributes. Detecting such errors *after* footage is generated may require additional human review or regeneration. SceneLock performs a **text-only, pre-generation check** of one intended shot prompt against its screenplay excerpt and shot intent.

This is a product hypothesis for microdrama workflows, **not a verified claim that Kuku lacks such a tool or has a particular internal process**. Later evaluation must independently establish evidence for the pain point and actual tool performance.

### 1.2 User and job-to-be-done

- **Primary user:** AI video artist / shot-prompt engineer.
- **Secondary user:** AI content producer or pre-production QA reviewer.
- **Job:** “Before I spend time or compute on a shot, help me find important prompt discrepancies, show why they matter, and propose only the smallest justified correction.”
- **Unit of work:** One screenplay excerpt or dramatic beat + one video prompt + intended shot type.
- **Human authority:** Every AI finding and correction remains advisory. The reviewer makes the final creative decision.

### 1.3 MVP success definition

An unfamiliar user can paste a **previously unseen** screenplay and video prompt, identify the shot, run a real language-model comparison, receive validated and evidence-backed findings, distinguish genuine problems from permissible filming choices, review suggestions, and download the result. The application must report model/API/validation failure honestly instead of displaying canned “success.”

### 1.4 Scope assumptions

1. The supplied screenplay excerpt is the approved source of truth for story facts; the shot intent determines which of those facts are relevant.
2. The video prompt may describe **less than the full scene**. Omission is not automatically an error.
3. No reference images, video frames, audio, previous shots, or independent director's notes are provided in MVP. Facts conveyed *only* by such external materials cannot be verified.
4. The original prompt can include compatible cinematic choices (lighting, camera angle, mood, background detail). The checker must preserve legitimate choices.
5. Character coreference may be uncertain, especially when prompts use generic labels (“a man,” “the woman”). Uncertain identities must not be asserted as fact.
6. The initial language path accepts Unicode Hindi and English text. Robust multilingual accuracy remains an evaluation question, not an assumed guarantee.
7. No actual video generation, actual regeneration savings, or provider-independent correctness guarantee is in scope.

## 2. Frozen input contract (five input groups)

| Input group | UI field and type | Required? | Validation and processing rule |
|---|---|---|---|
| **I1 — Screenplay** | Multiline text area, `screenplay_text: str` | **Yes** | Trim surrounding whitespace; reject blank input; preserve original text for evidence matching; maximum **8,000 characters**. Include dialogue and action descriptions. |
| **I2 — Video-generation prompt** | Multiline text area, `video_prompt: str` | **Yes** | Trim surrounding whitespace; reject blank input; preserve original text; maximum **4,000 characters**. |
| **I3 — Shot type** | Required dropdown, `shot_type: enum` | **Yes** | User must select one of the seven defined options; no hidden default that assumes full-scene coverage. |
| **I4 — Shot intent** | Single/multiline short text, `shot_intent: str | null` | No | Maximum **500 characters**. Describes the specific action/beat/subject intended to appear. A narrower clear intent takes precedence over broad shot-type assumptions. |
| **I5 — Scene identifiers** | Group of text fields: `episode_id`, `scene_id`, `shot_id` | No | Each may be blank; maximum **80 characters**. Used only for metadata/tracking; never as evidence of screenplay meaning. |

**Shot-type enum (`I3`):**

1. `Full dramatic beat`
2. `Establishing / wide shot`
3. `Character interaction`
4. `Action shot`
5. `Character close-up`
6. `Prop close-up`
7. `Custom / other`

If `Custom / other` is chosen, require a nonblank `shot_intent`. All other types allow an optional intent. The UI may show helper examples, but no examples will be silently submitted as actual user inputs.

**Other input rules:** Do not make a minimum word count a rigid requirement: short but meaningful microdrama beats exist. If text is nonblank but semantically too sparse, analysis may return **Insufficient Context**. Input limits are practical MVP caps, not model limits; display a user-friendly warning when exceeded. Preserve Unicode. Treat screenplay/prompt content as **untrusted data** rather than instructions that can override the system prompt.

**Deferred metadata:** An optional show title can be added later, but is not required by the five-group MVP contract.

## 3. Detection taxonomy (exactly four categories)

| Category code | Category | Detect | Guardrail |
|---|---|---|---|
| `critical_action` | Critical actions | Missing, altered, reversed, or reassigned actions essential to the intended beat (hiding evidence, burning a letter, handing over a key). | Do not demand an action already completed before a reaction close-up. |
| `important_prop` | Important props | Necessary objects and explicitly required state, material, color, or placement. | Do not flag ordinary off-frame/background props merely because the screenplay mentions them. |
| `character_identity_position` | Character identity and position | Wrong actor assigned to an action; incompatible posture/location/spatial relation; missing character when the intended shot needs them. | Generic references with unresolved identity are `Ambiguous`, not definite contradictions. No face recognition. |
| `explicit_visual_attribute` | Explicit visual attributes | Required clothing colors, costume state, physical appearance or scene attributes that the shot actually shows. | Do not impose unstated styling or treat compatible lighting/camera choices as errors. |

Classification always depends on **the source evidence plus shot scope**, not a bare list of screenplay nouns.

## 4. Comparison statuses (exactly five)

| Status | Definition | Example |
|---|---|---|
| **Supported** | Prompt conveys the relevant fact faithfully, including semantic paraphrases. | “Places a key in her handbag” vs “slips a key into her purse.” |
| **Contradicted** | Prompt explicitly conveys an incompatible fact about the *same resolved entity or action*. | Script says red dress; prompt says blue dress for the identified character. |
| **Missing** | A required fact for the **selected shot** has no corresponding prompt content. Absence alone is never an explicit contradiction. | The intended full action shot must show burning the letter; the prompt stops at holding it. |
| **Ambiguous** | Meaning, entity matching, temporal sequence, or shot applicability is not sufficiently clear for a reliable judgment. | “A man watches a woman,” without evidence that this is Arjun and Meera. |
| **Not Applicable** | A screenplay fact is legitimately outside the specified shot's visible/time scope. | Key hiding omitted from a later face-reaction close-up. |

**Decision order for each fact:** Determine shot applicability → resolve entity/action references when supported → check explicit contradiction → check semantic support → identify a relevant missing requirement → otherwise assign ambiguity. `Not Applicable` facts must not contribute to error counts.

## 5. Severity and status business rules

### 5.1 Severity (`High | Medium | Low`)

- **High:** Clear contradiction or omission that changes a critical action, identity, or outcome of the intended shot.
- **Medium:** Meaningful likely problem or unresolved ambiguity that warrants a human decision; the impact is not certain.
- **Low:** Minor ambiguity or optional clarification unlikely to change the dramatic beat.

Assign severity only to **findings**, not to every `Supported` or `Not Applicable` fact. A `High` issue requires strong evidence; ambiguous identity by itself should not be called a confirmed High contradiction.

### 5.2 Deterministic summary counts

The **Python analyzer**, not the LLM, computes:

- `extracted_fact_count`: All valid facts extracted from the screenplay.
- `relevant_fact_count`: Facts whose comparison status is not `Not Applicable`.
- `verified_fact_count`: Relevant facts with status `Supported`.
- `critical_issue_count`: Findings with status `Missing` or `Contradicted` **and** severity `High`.
- `warning_count`: Findings with severity `Medium` or `Low` (including applicable ambiguities).
- `finding_count`: Total validated findings, regardless of severity.

Counts represent classifications, **not a percentage-accuracy score**.

### 5.3 Overall review status (`Review Required | No Significant Issues Detected | Insufficient Context`)

Precedence, after a **successful** validated model response:

1. **Insufficient Context** when there are zero relevant facts or none of the relevant facts can be assessed beyond `Ambiguous`.
2. **Review Required** when any validated finding is High/Medium and is relevant to the shot. A medium ambiguity can require clarification without being labeled a proven mistake.
3. **No Significant Issues Detected** otherwise. Low-severity warnings may still be shown with this status.

An API error, quota error, invalid JSON, failed schema validation, or fabricated quote is **`Analysis Failed` at the application level**, not one of the three successful review statuses. The app must show a clear failure message and provide retry where appropriate; no fake or canned report is substituted.

## 6. Exact output contract

### 6.1 Successful analysis object

`AnalysisResult` will contain the following top-level groups:

1. **`metadata`** — `schema_version`, unique `analysis_id`, UTC timestamp, episode/scene/shot IDs, selected shot type/intent, `analysis_engine` (`live_llm`), configured provider/model identifier, and optional duration metrics if available.
2. **`facts[]`** — `fact_id`, category (one of four), entity/actor if known, `required_detail`, `source_evidence` (exact screenplay substring), `comparison_status` (one of five), `applicability_reason`, and optional uncertainty note.
3. **`findings[]`** — `finding_id`, `related_fact_id`, category, `comparison_status` (`Contradicted`, `Missing`, or `Ambiguous`), severity, `screenplay_evidence`, nullable `prompt_evidence`, concise explanation, minimal `suggested_fix`, and optional uncertainty note.
4. **`summary`** — computed overall review status and six defined counts (Section 5.2).
5. **`suggested_corrected_prompt`** — an editable copy of the video prompt with only justified minimal changes. If no actionable changes exist, preserve the original prompt unchanged.

`ReviewDecision` records are **not part of the model's raw judgment**. Maintain a separate `review_decisions` map keyed by `finding_id`, with values `Accept suggestion`, `Dismiss / intentional creative choice`, or `Needs further review`. Initial decision is `Needs further review`. Include these only as a separate section in the exported **review report**.

### 6.2 Evidence and correction rules

- Every finding links to an existing fact ID and uses that fact's actual screenplay evidence.
- Every non-null evidence quotation must be a verbatim substring of the original source text. A `Missing` finding uses `prompt_evidence: null` rather than inventing a quotation.
- The LLM may reason about synonyms, but Python checks evidence substring integrity and IDs.
- Do not fabricate unseen characters, motivations, costume details, or actions.
- Do not convert `Ambiguous` into a definite correction without an explicit reviewer decision.
- Do not delete compatible camera, lighting, pacing, or visual-style instructions.
- Never silently overwrite the original screenplay or the original video prompt.
- UI shows full evidence, clear explanatory reason, and proposed minimal fix for each finding.

### 6.3 UI outputs

- One status badge: `Review Required`, `No Significant Issues Detected`, or `Insufficient Context`.
- Summary cards: critical issues, warnings, verified relevant facts, relevant fact count.
- Findings table/cards with category, status, severity, both evidence fields, explanation, suggestion, and independent human-decision control.
- Separate editable suggested revised prompt, retaining original prompt in the input view.
- Model/provider label (`Live LLM analysis`) and clear failure status when applicable.
- Download buttons for JSON and CSV; copyable revised prompt (native Streamlit text/code display or a similarly simple mechanism).

### 6.4 Exports

**JSON review report** includes: original inputs and shot metadata, validated analysis, summary, suggested prompt, review decisions, schema version and analysis ID. Download must be generated from the current session's actual result, not example data.

**CSV findings report** includes one row per finding with: `analysis_id`, IDs, `finding_id`, `related_fact_id`, category, status, severity, screenplay evidence, prompt evidence (blank if none), explanation, suggested fix, uncertainty note, human decision. An analysis with zero findings must still generate a CSV with headers.

**Raw evaluation output (future Phase 2+)** is the original unedited model response captured by test runs, stored separately from validated or human-edited exports. Do not create or claim raw outputs until actual model calls occur.

## 7. Architecture baseline (approved)

```text
Single-page Streamlit UI
        |
        v
Input validation and shot-scope context (Python)
        |
        v
Analyzer orchestration (Python)
        |
        v
Replaceable Gemini adapter (google-genai SDK)
        |
        v
One structured LLM request:
  extract facts -> interpret prompt -> compare within shot scope
        |
        v
Pydantic schema validation + deterministic evidence checks
        |
        v
Python counts, severity consistency and overall review status
        |
        v
Streamlit display + independent human decisions + JSON/CSV
```

### 7.1 Stack

- **Python:** Python 3.11 or newer.
- **Frontend / app runtime:** Streamlit.
- **AI:** Gemini, configured via the currently supported `google-genai` Python SDK. Exact available structured-output-capable model identifier is configurable rather than hardcoded in unrelated modules.
- **Schemas:** Pydantic v2-style models.
- **Processing:** Standard Python; Pandas only if useful for CSV tables.
- **Testing:** pytest and original labelled examples (created in Phase 2, not now).
- **Secrets:** Environment variables locally and Streamlit Community Cloud secrets in deployment; never commit keys.
- **Hosting:** Streamlit Community Cloud when deployment phase begins; a reproducible GitHub repository is the fallback.

### 7.2 Explicit separation of responsibility

| Component | What it owns | What it must not own |
|---|---|---|
| Streamlit | Inputs, display, review controls, downloads, session state | Semantic reasoning rules or API-specific JSON parsing |
| Model adapter | Provider request, response retrieval, timeout/rate-limit handling | UI elements or business-status calculations |
| LLM | Extract, interpret and semantically compare facts | Invented evidence, numerical accuracy scores, final status/count arithmetic |
| Pydantic / validators | Types, allowed values, cross-references, actual source quotation integrity | Creative interpretation beyond deterministic checks |
| Analyzer | Pipeline orchestration, safe error propagation, Python summaries | Silent prompt replacement or fake fallback success |
| Human | Accept, dismiss, or defer suggestions | Mutation of the original raw model record |

### 7.3 One-call MVP decision

Use **one** structured model call implementing three logical stages to minimize cost, latency, and development time. If Phase 2 evaluation shows omissions or self-inconsistent outputs, introduce a second independent verification call later as a documented change. Do not build agent frameworks, embeddings, vector search, databases, or background queues for MVP.

### 7.4 Future file responsibilities (not created in Phase 1)

| Planned file | Responsibility |
|---|---|
| `app.py` | Streamlit UI and session-based reviewer workflow |
| `analyzer.py` | Orchestrate request → model → validation → summary |
| `model_adapter.py` | Replaceable Gemini model integration |
| `prompts.py` | Conservative system prompt and analysis instructions |
| `schemas.py` | Exact Pydantic models and enums |
| `validators.py` | Evidence and cross-reference validation; status/count calculations if separated |
| `requirements.txt` | Minimal dependencies |
| `tests/` | Test harness and regression tests |
| `sample_inputs/` | Original or properly licensed sample cases |
| `raw_outputs/` | Real, unmodified responses after later evaluations |
| `README.md` | Setup, run, config, limits and transparency |

## 8. MVP non-goals and deferred features

**Out of scope for the first working prototype:** video generation; processing output frames; face recognition; speech/lip-sync checks; series-wide continuity; full-scene story rewriting; virality prediction; authentication; multiple accounts; team collaboration; databases; automatic approval; automatic edits to source screenplay; batch processing; multi-step agents; paid inference dependency; advanced UI styling; mandatory offline NLP fallback.

If no API key is available, show **live analysis unavailable** and clear configuration guidance. A later limited, deterministic rule mode may be considered, but it must be labeled as limited and must never use canned results or claim full semantic comparison.

## 9. Safety, privacy, failures and limits

1. Do not log or publish confidential Kuku-provided scripts in public repositories or raw-output folders.
2. Test with invented or properly licensed scene/prompt pairs unless permission is established for other material.
3. Never expose API keys in source, downloads, logs, or error messages.
4. Clearly surface provider outage, quota exhaustion, rate limiting, timeouts, blocked requests, malformed responses, or failed evidence validation.
5. A bounded retry for transient transport/JSON failure is permitted; never change the user's input or fabricate results to hide a failure.
6. Keep review decisions in Streamlit session state for MVP. Persistence across browser sessions is not promised.
7. No claim of accuracy, cost savings, production time reduction, or fewer regenerations without measured data.
8. Validate the precise availability and free-tier quota of the selected model during implementation; no fixed model ID, pricing or quota is guaranteed by this specification.

## 10. Acceptance criteria (implementation test IDs)

Each future acceptance criterion is **defined**, not yet implemented or passed.

| ID | Acceptance requirement | Passing evidence expected later |
|---|---|---|
| AC-01 | Required screenplay, prompt and shot type are collected; optional fields work. | UI input tests. |
| AC-02 | Blank/over-limit inputs are rejected with useful errors. | Validation tests. |
| AC-03 | Unseen screenplay and prompt trigger a real model request. | Actual new-input run and raw response. |
| AC-04 | Extracted facts are grounded in exact screenplay excerpts. | Evidence substring assertions. |
| AC-05 | Critical actions and props are checked when shot-relevant. | Labelled action/prop cases. |
| AC-06 | Character identity/position and explicit attributes can be checked. | Labelled identity/attribute cases. |
| AC-07 | The five comparison statuses are implemented and used correctly. | Status unit and integration tests. |
| AC-08 | Synonyms/paraphrases do not create automatic false contradictions. | Handbag/purse and action-paraphrase cases. |
| AC-09 | Shot type and shot intent prevent irrelevant omission alarms. | Reaction close-up test. |
| AC-10 | Ambiguous identity is not presented as certain contradiction. | Unnamed-character case. |
| AC-11 | Each finding has proper linked evidence, severity, explanation and minimally scoped fix. | Schema, evidence and reviewer inspection. |
| AC-12 | Status and summary counts come from Python deterministic rules. | Unit tests for all branches and zero findings. |
| AC-13 | Original prompt is preserved; suggested correction avoids unnecessary stylistic changes. | Before/after tests and review. |
| AC-14 | Human accept/dismiss/review choices do not mutate AI findings. | Streamlit session and export tests. |
| AC-15 | JSON and CSV exports work, including zero-findings case. | Parse downloaded JSON/CSV. |
| AC-16 | Model/API/schema/evidence failures are clearly surfaced, with no fake result. | Fault-injection tests. |
| AC-17 | The app can be rerun on unfamiliar examples, not canned outputs. | Fresh end-to-end run. |
| AC-18 | The complete deliverable has tests, actual raw outputs, a documented error, limitations and run instructions. | Submission checklist and repository review. |

**Minimum MVP release gate:** AC-01 through AC-17 pass on representative cases. **Assignment submission gate:** AC-18 also passes; the Kuku brief additionally requires a solution PDF (max two pages), a working prototype/repository link, and raw real-run outputs; a ≤3-minute walkthrough is optional but recommended. All shared links must be accessible to their intended evaluators.

## 11. Approved implementation order (future phases only)

These are the next actions, **not Phase 1 work**:

1. **Phase 2 — Evaluation fixtures:** Create 15 original labelled screenplay/prompt pairs and expected outcomes *before* final model tuning; include contradictions, omissions, valid paraphrases, close-ups, ambiguity and creative additions.
2. **Phase 3 — Scaffold:** Create Python environment, minimal Streamlit inputs, exact schemas, and a real Gemini adapter.
3. **Phase 4 — Analysis:** Implement the conservative single-call extraction/comparison prompt and validation pipeline.
4. **Phase 5 — Rules and UI:** Compute deterministic counts/status; display evidence, minimal correction and independent reviewer decisions.
5. **Phase 6 — Exports:** Enable actual JSON/CSV downloads, preserving raw response separately in tests.
6. **Phase 7 — Evaluation/debugging:** Run all labelled cases and at least three unseen ones; record false positives, false negatives, latency, raw outputs and one genuine failure.
7. **Phase 8 — Reproducibility/deployment:** README, public app or repository, real smoke test from a fresh session.
8. **Phase 9 — Submission:** Two-page PDF, accessible links, raw output folder and optional ≤3-minute own-voice walkthrough.

**Priority order:** live functionality → trustworthy evidence → shot-scope logic → understandable output → real evaluations → deployment/documentation → polish.

## 12. Phase 1 completion checklist

- [x] Narrow MVP problem, user, one-shot scope and assumptions finalized.
- [x] Five input groups defined with types, required fields, shot enum and validation rules.
- [x] Exactly four detection categories defined.
- [x] Exactly five comparison statuses defined with conservative handling.
- [x] Evidence, severity, Python summary, minimal correction and export contracts defined.
- [x] Python + Streamlit + Gemini + Pydantic architecture and responsibility boundaries finalized.
- [x] Concrete implementation acceptance IDs AC-01 through AC-18 established.
- [x] Next-phase implementation order and release gates defined.
- [x] Versioned reusable Phase 1 specification created.
- [x] Phase 2 test cases and application source code intentionally **not** created.

### Genuine blockers at Phase 1

**None for requirements/specification.** Actual live Gemini access and model availability will only be verified in the implementation phase; deployment requires an API key configured outside the repository. Evidence that the proposed workflow is a substantial real-world pain point still needs collection before final submission. These are future validation tasks, not blockers to completing Phase 1.

