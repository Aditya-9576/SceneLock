# SceneLock — Kuku Problem 3 Final Runnable Prototype

**SceneLock** helps AI microdrama video artists check screenplay scenes against shot-generation prompts *before* generating footage. This repository is the working foundation for the Kuku AI Generalist Assignment, Problem Statement 3.

> **Current state:** SceneLock is **prepared for GitHub and Streamlit Community Cloud**. All original review/export features remain, with an explicitly labeled human-authored **offline demo** when Gemini quota is unavailable. Runtime dependency versions are pinned and independent automated tests are available through GitHub Actions. **No GitHub repository or public Streamlit URL has been created or verified in an authorized account yet.** Follow the beginner-friendly **[DEPLOYMENT.md](DEPLOYMENT.md)** for exact account-side clicks. The authenticated Gemini benchmark still needs a private key; synthetic fixture tests must not be described as model accuracy.

## Kuku Phase 11 submission material

- The official **[two-page solution PDF](docs/SceneLock_Kuku_Solution_Two_Pages.pdf)** is also supplied as a separate download in the submission bundle.
- See [Phase 11 submission checklist](docs/Phase11_Submission_Guide.md) for the exact Kuku form deliverables, what is ready and what remains blocked.
- See the [2:50-minute video storyboard](docs/Phase11_Walkthrough_Script_Storyboard.md) for an optional screen recording in your own voice.
- See the [evidence register](docs/Phase11_Evidence_Register.md) to distinguish real tests from assumptions and unmeasured AI accuracy.
- The public GitHub/Streamlit links are **not yet available**. No authenticated Gemini responses were generated, so `raw_outputs/` contains an honest status README, not invented T01-T15 results. This means the mandatory raw-output submission item is **not yet complete**.

**Final independent QA, 8 November 2026:** `187 passed` in pytest; `15` fictional cases and `25` labels validated with zero errors; local Streamlit health returned `HTTP 200`; the publishable-file secret audit passed. The keyword baseline alone yielded case-level precision `40.0%` and recall `28.6%` (2 TP / 3 FP / 5 TN / 5 FN). **No Gemini model quality metric exists without live calls.** See the [Final Independent QA Report](docs/Final_Independent_QA_Report.md) and [machine-readable checklist](evaluation/final_qa_checklist.json).

## The easiest way to run it on your Mac (no coding knowledge needed)

You only need to copy and paste the following commands. You do **not** need Homebrew or Conda. The input-validation screen requires no Gemini key; the optional live AI test does.

### Step A — Download and unzip

1. Download the complete SceneLock ZIP supplied in ChatGPT.
2. Double-click it on your Mac to unzip.
3. Open the extracted **SceneLock** folder (the one with `app.py` inside).

### Step B — Open Terminal in that folder

1. Press **Command + Space**, type **Terminal**, and press Return.
2. Type `cd ` (the letters `cd` followed by one space) but do not press Return yet.
3. Drag the **SceneLock** folder from Finder into the Terminal window. macOS will insert its full path.
4. Press Return.

### Step C — Check Python

```bash
python3 --version
```

The version must be **3.11 or newer**. If `python3` is missing or too old, install a recent Python 3 release for macOS from [python.org/downloads/macos/](https://www.python.org/downloads/macos/) and reopen Terminal. Python 3.12 is also supported.

### Step D — Create an isolated project environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Your Terminal prompt may now show `(.venv)`. This keeps SceneLock packages separate from other software on your Mac.

### Step E — Install the required packages

```bash
python -m pip install -r requirements.txt
```

This installs the tested versions of Streamlit, Pydantic and Google's GenAI SDK. It may take a few minutes the first time and needs an internet connection. Automated tests additionally require `requirements-dev.txt`.

### Step F — Run the app

```bash
python -m streamlit run app.py
```

Streamlit normally opens a browser tab. If it does not, paste this address into your browser:

**http://localhost:8501**

Start by choosing an example from the **Example scene** dropdown and clicking **Load Sample**, or paste your own screenplay and video prompt. The optional IDs are under **Episode, scene and shot IDs**. Select the shot type and optionally describe its intent. **Validate Inputs** checks the fields without contacting Gemini. With a private API key configured, **Analyse Prompt** performs one genuine Gemini review while showing a loading indicator. Results include counts, evidence-backed issue cards, separate reviewer choices, an editable corrected prompt, and **three downloads** under **Download reviewed report**: reviewed JSON, finding-level CSV and raw AI JSON. Editing screenplay/prompt fields immediately hides outdated results without another model request.

### Phase 8: Download your report

1. Run **Analyse Prompt** with a privately configured key, or inspect the generated examples inside `sample_exports/` when working without one.
2. For each issue card, select **Accept Suggestion**, **Dismiss as Intentional** or **Needs Further Review**. Decisions remain separate from the AI output.
3. Review and edit **Editable candidate prompt**. This text does not overwrite the original screenplay, video prompt or AI recommendation.
4. Expand **Download reviewed report** and choose:
   - **Download JSON** — original inputs and scene IDs, full extracted screenplay facts and comparison statuses, all findings and severity/evidence/explanations/suggestions, Python-calculated counts, model metadata, **separate** reviewer decisions, and the independently edited prompt.
   - **Download CSV** — one row per issue, with `finding_id`, `category`, `status`, `severity`, `screenplay_evidence`, `prompt_evidence`, `explanation`, `suggested_fix`, `human_decision`, and extra traceability columns. If zero issues exist, CSV still contains its header and JSON explicitly contains `[]` findings.
   - **Download unedited AI response (JSON)** — exactly the text returned by Gemini's structured-output response, before any human decisions or prompt editing. It is **not** merged into the reviewed JSON. This raw text lives only in your current browser session until you choose to download it; it is never automatically written to local disk by the UI.

CSV is Excel-compatible UTF-8 with a BOM and proper quoting of commas, double quotes and newlines. Formula-like text is escaped to protect spreadsheet viewers. Both formats preserve Hindi/English Unicode. **These reports may contain confidential screenplay content; keep them private.**

### Phase 10: Public demo and fallback

- For deployment to GitHub/Streamlit, follow **[DEPLOYMENT.md](DEPLOYMENT.md)**. It explains the exact buttons, where to paste a secret privately, what public URL to verify and how to test on a completely new screenplay.
- Without a key or when Gemini quota is exhausted, click **Open Offline Demo (No Gemini)** inside the app. It shows manually authored findings, human-review controls and functioning reviewed JSON/CSV exports. A prominent warning marks them as **NOT Gemini predictions**, and no fake raw AI output is offered.
- If hosting is unavailable, use the static `sample_exports/` examples and the Phase 9 engineering evaluation report. These are honest labeled fixtures, not a substitute for live inference.

### Step G — Stop the app safely

Return to Terminal and press **Control + C**. When done with the project environment, you may type:

```bash
deactivate
```

The next time you run SceneLock, open Terminal in the folder, execute `source .venv/bin/activate`, then `python -m streamlit run app.py` again.

## Try a real existing test case

You no longer need to copy JSON fields manually. Choose from six fictional sample shots in the app and press **Load Sample**:

- **T01** — Costume contradiction (red versus blue dress).
- **T03** — Handbag/purse wording that should be considered equivalent.
- **T05** — Missing critical action.
- **T06** — A reaction close-up that should not demand an earlier off-screen action.
- **T09** — Ambiguous character identities.
- **T15** — Hindi-English mixed text.

Pressing **Validate Inputs** validates fields only; pressing **Analyse Prompt** sends them to Gemini if a key is available. To verify the whole Phase 5 analysis path before trying the UI, use the dedicated live semantic smoke script below. T01–T15 are original synthetic evaluation cases and are **never silently sent to the model as labeled examples**.

## What works right now

- A runnable single-page Streamlit UI, with optional episode/scene/shot IDs.
- Required screenplay text (up to 8,000 characters) and video prompt (up to 4,000 characters).
- Seven shot types, including `Custom / other` that requires an explicit shot intent.
- Unicode Hindi and English inputs (without implying the future model's accuracy).
- User-friendly Pydantic validation for blank, over-limit, or invalid fields.
- Secure optional Gemini settings loaded from environment variables or Streamlit secrets.
- A **real Gemini Interactions API adapter** with Pydantic JSON schema output, bounded retries, typed failures and token/latency metadata.
- A replaceable `ModelAdapter` protocol; another LLM can be integrated without changing the app's input schema.
- One-call reasoning instructions in `prompts.py` implementing Stage A extraction, Stage B semantic prompt interpretation and Stage C shot-aware classification.
- An analyzer that verifies every model-backed source quote, linked finding and corrected-prompt invariant, then computes counts and overall review status deterministically.
- Strict response parsing that rejects duplicate JSON keys, non-finite numbers, malformed/empty or oversized data, blank facts, unknown enums and invented quotations.
- Pydantic report and metadata validation, with final summary consistency checked again when a report is constructed or exported.
- A live Streamlit results dashboard for findings, original evidence, scope reasoning, suggested minimal correction and individual human decisions.
- A focused sample picker with **Load Sample** that fills all seven input widgets from the original test dataset without triggering an AI request.
- Readable two-column screenplay/prompt inputs, optional scene identifiers, shot-intent help, clear progress and error messages, and evidence-backed issue cards.
- Individual **Accept Suggestion / Dismiss as Intentional / Needs Further Review** controls that persist for the current browser session and do not change model facts/findings.
- Reviewed JSON and CSV exports built only from the currently validated result; CSV protects spreadsheet users against formula injection.
- An unedited raw-model-response download held separately in session memory, with an opt-in private evaluation archive for authenticated command-line test runs.
- A generated sample-export collection exercising a High contradiction, High missing action, Hindi-English Medium contradiction, and zero-finding shot.
- An expressly labeled offline demonstration that exercises review and JSON/CSV exports without API quota or pretending to run Gemini.
- Pinned production dependencies, separate test-only dependencies, public-repository safety rules and a GitHub Actions workflow for no-key regression checks.
- Phase 9 evaluation runner for exactly **T01–T15 plus three unseen U01–U03 cases**, using the same real Gemini adapter and Python evidence validation when authorized credentials exist.
- Optional pre-validation raw-response observer. A malformed or incomplete response can be archived for later diagnosis while the invalid report is still rejected.
- Strict case-named raw archives (`raw_outputs/T01_response.json` through `T15_response.json`) with restricted file permissions and no overwrites, only for actual API replies.
- Conservative fact-aligned partial-label issue precision/recall, semantic matches, scope errors and latency measurements; extra model facts are marked unadjudicated instead of assumed false positives.
- Actual regression repairs for invisible Unicode input/evidence and for lost raw provider text. All changes have automated tests.
- Stale-result protection: when form inputs change, the previous result no longer appears as the new analysis.
- A private key-setup helper and an optional authenticated live-smoke script.
- Deterministic checks that source quotes and finding references correspond to the actual inputs.
- Retained Phase 2 data and deterministic baseline results.
- Automated unit tests, dataset consistency checks, and Streamlit UI smoke tests.

## What is intentionally not built until later

| Feature | Planned phase |
|---|---|
| Real Gemini request adapter and schema/evidence parsing | Phase 4 — implemented; live credentials pending |
| Web dashboard with validated issue reports and deterministic status counts | Phase 5 — implemented |
| Minimal AI-corrected prompt and human accept/dismiss workflow | Phase 5 — implemented; live credentials pending |
| Strict output models, adversarial validation | Phase 6 — implemented |
| Professional one-page Streamlit artist interface and sample loader | Phase 7 — implemented |
| Reviewed JSON/CSV export with separate human decisions and unedited raw download | Phase 8 — implemented |
| Evaluation runner, error tests and reproducible issue-scoring rules | Phase 9 — implemented |
| Actual authenticated LLM runs on T01–T15 and three unseen scenes | Phase 9 — **blocked by missing key**; no model metrics claimed |
| GitHub/Streamlit deployment preparation and offline fallback | Phase 10 — implemented |
| GitHub push, public Streamlit URL and live URL verification | Phase 10 — **requires connected/authorized accounts** |

**No model evaluation results are claimed by this repository.** The nine `evaluation/phase5_contract_fixtures.json` examples are human-authored expected inputs/labels used for offline pipeline and UI tests. Their passing tests **do not establish Gemini semantic accuracy**. The files under `evaluation/baseline_*.json` contain real results from a simple **keyword-matching algorithm**, not from Gemini.

## Phase 9 — run the complete model evaluation

Once your private Gemini key is configured (instructions below), open Terminal in the SceneLock folder and run:

```bash
python evaluation/run_phase9.py
```

This runner attempts all **15 original labeled cases** and **three independent unseen cases** using one structured Gemini analysis per case. It keeps the original labels unchanged and saves raw provider text **before** evidence validation, so validation failures are not erased. On a successful authenticated run, it writes:

- `raw_outputs/T01_response.json` through `T15_response.json`, plus `U01_response.json` through `U03_response.json` when each provider response exists. These are the **literal text returned by Gemini**, not reconstructed predictions. A rejected/malformed response may not itself be valid JSON; it is still stored unmodified.
- `evaluation/phase9_live_summary.json`: per-case outcome, API/validation error type, actual latency, match details, precision and recall **only for validated predictions that can be compared with labeled facts**.

If no key is configured, the command prints **BLOCKED**, creates only a `phase9_live_summary.json` with **18 `not_run_no_credentials` entries**, and records model metrics as `null`. It does **not** fabricate raw responses or inference numbers. If raw files already exist, the runner preserves them and explicitly skips those case IDs to prevent accidental overwrite.

For real baseline errors and reproducible backend repairs, inspect `evaluation/phase9_failure_log.json`. The keyword baseline's false positives/negatives are **not Gemini mistakes**. Details and limitations are in the Phase 9 engineering report.

## Project file guide

```text
SceneLock/
├── app.py                 # Input form, live QA dashboard and reviewer controls
├── analyzer.py            # Provider-neutral orchestrator and deterministic summary
├── model_adapter.py       # Real Gemini Interactions API adapter + error handling
├── schemas.py             # Pydantic input, structured-model and report schemas
├── prompts.py             # Three-stage, shot-aware semantic-review instructions
├── validators.py          # Input, evidence, cross-reference and correction checks
├── exports.py             # Validated in-memory JSON/CSV review reports
├── raw_archive.py         # Optional private raw response preservation for live CLI tests
├── offline_demo.py         # Non-Gemini human-authored fallback, validated before display
├── sample_loader.py       # Original fictional UI examples, no expected labels
├── requirements.txt       # Exact verified production dependency versions
├── requirements-dev.txt   # Separate pytest/testing dependencies
├── README.md              # These instructions
├── DEPLOYMENT.md          # Zero-coding GitHub and Streamlit deployment guide
├── .gitignore             # Protect secrets and local runtime files
├── .python-version        # Recommended local Python version
├── .github/workflows/tests.yml # Automated no-secret GitHub checks
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── sample_inputs/
│   ├── test_cases.json    # Fifteen original test pairs, unchanged from Phase 2
│   └── export_unicode_case.json # Manual multilingual export test input
├── sample_exports/        # Four generated JSON/CSV pairs; clearly labeled manual fixtures
│   ├── README.md
│   └── scenelock_*_human_authored_example.json / .csv
├── evaluation/
│   ├── expected_labels.json
│   ├── validate_dataset.py
│   ├── keyword_baseline.py
│   ├── baseline_predictions.json
│   ├── baseline_summary.json
│   ├── phase5_contract_fixtures.json # 9 manual fixtures; NOT Gemini predictions
│   ├── unseen_phase9_cases.json      # 3 fresh manual holdout scenes
│   ├── score_predictions.py          # Conservative issue-level scoring on aligned facts
│   ├── run_phase9.py                 # Genuine 18-case Gemini runner, key required
│   ├── phase9_live_summary.json      # Actual BLOCKED manifest until live access
│   ├── final_qa_checklist.json       # Independent final audit status; no invented model metrics
│   ├── generate_failure_log.py
│   └── phase9_failure_log.json       # Real keyword-baseline errors and code regressions
├── tests/
│   ├── test_validation.py
│   ├── test_model_adapter.py
│   ├── test_analyzer.py
│   ├── test_gemini_integration.py
│   ├── test_setup_key.py
│   ├── test_dataset.py
│   ├── test_app_smoke.py
│   ├── test_semantic_engine.py
│   ├── test_output_validation.py
│   ├── test_sample_loader.py
│   ├── test_full_export_workflow.py
│   ├── test_raw_archive.py
│   ├── test_phase9_runner.py
│   ├── test_phase9_scorer.py
│   ├── test_phase9_adversarial.py
│   ├── test_offline_deployment_demo.py
│   ├── test_deployment_workflow.py
│   ├── test_final_qa.py             # New unseen close-up and input/credential regressions
│   └── test_release_audit.py
├── scripts/
│   ├── live_gemini_smoke.py      # Genuine one-case request; key required
│   ├── live_semantic_smoke.py    # Full live pipeline and private raw archive; key required
│   ├── generate_sample_exports.py # Offline; no Gemini call; 4 JSON/CSV pairs
│   ├── release_audit.py            # Check public candidates for secrets/raw data
│   ├── local_deployment_smoke.py   # Start HTTP server and probe local health
│   └── setup_gemini_key.py       # Private, hidden-input local key setup
├── raw_outputs/
│   └── README.md          # Actual live raw responses excluded from ZIP/Git
└── docs/
    ├── SceneLock_Phase1_Project_Specification.md
    ├── SceneLock_Phase2_Dataset_README.md
    ├── Phase3_Test_Report.md
    ├── Phase4_Integration_Report.md
    ├── Phase5_Test_Report.md
    ├── Phase6_Verification_Report.md
    ├── Phase7_UI_Test_Report.md
    ├── Phase8_Export_Test_Report.md
    ├── Phase9_Engineering_Evaluation_Report.md
    ├── Phase10_Deployment_Test_Report.md
    ├── SceneLock_Kuku_Solution_Two_Pages.pdf
    ├── Phase11_Submission_Guide.md
    ├── Phase11_Walkthrough_Script_Storyboard.md
    ├── Phase11_Evidence_Register.md
    └── Final_Independent_QA_Report.md
```

## Run the automated tests

With the `.venv` environment activated and Terminal open in the SceneLock folder:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

To recheck the Phase 2 labels:

```bash
python evaluation/validate_dataset.py
```

To regenerate the Phase 8 example reports **without** a Gemini key:

```bash
python scripts/generate_sample_exports.py
```

The eight example files are in `sample_exports/`. Their `analysis_engine` and
`provider` explicitly identify the hand-authored labels; **they are not Gemini
outputs**. Four review cases exercise the full deterministic pipeline,
including evidence validation and human decisions.

To rerun the **deterministic keyword baseline only**:

```bash
python evaluation/keyword_baseline.py
```

The baseline's measured results are **2 TP, 3 FP, 5 TN, 5 FN** on the 15 authored cases (40.0% precision; 28.6% recall). They are not predictions from any LLM.

To reproduce the Phase 9 error examples from those actual baseline predictions:

```bash
python evaluation/generate_failure_log.py
```

## Gemini API key — one-time setup for your first real AI test

The official Gemini API key page is **[Google AI Studio — API Keys](https://aistudio.google.com/api-keys)**.

1. Open that link in your browser and sign in to your Google account.
2. Open **API Keys** in AI Studio, then choose **Create API key** (or the existing key for your project). Google may ask you to choose or create a Cloud project.
3. Copy the new key privately. **Never paste it into ChatGPT, GitHub, screenshots or a shared document.** New AI Studio keys are authorization keys, as described in Google's [API-key guide](https://ai.google.dev/gemini-api/docs/api-key).
4. With Terminal inside the SceneLock folder and the environment activated, run this one command:

   ```bash
   python scripts/setup_gemini_key.py
   ```

5. When prompted, paste the key into **your own Terminal**. The characters will be hidden. The helper securely creates `.streamlit/secrets.toml`, which is excluded from Git and the downloadable project ZIP.
6. To make one real, small Gemini request using a fictional screenplay, run:

   ```bash
   python scripts/live_gemini_smoke.py
   ```

   To test the **full Phase 5 semantic engine** on the Meera/Arjun close-up, run:

   ```bash
   python scripts/live_semantic_smoke.py
   ```

   For an unfamiliar costume contradiction, run:

   ```bash
   python scripts/live_semantic_smoke.py --case P5-06
   ```

   To run the full **Phase 9 T01–T15 benchmark and three unseen scenes**, run:

   ```bash
   python evaluation/run_phase9.py
   ```

If a request really succeeds, the script prints a success flag, model name, inference duration and numbers of facts/findings. The `live_semantic_smoke.py` script also privately saves the **exact** raw response under `raw_outputs/` with restricted file permissions and a unique analysis ID; Git excludes it. It does not print the key or a full screenplay. If no key is configured, it clearly reports **NOT RUN**; a mock test is not an authenticated success.

**Alternative for technical users:** Configure `GEMINI_API_KEY` or `GOOGLE_API_KEY` as an environment variable, or supply Streamlit deployment secrets. Google's SDK gives `GOOGLE_API_KEY` precedence if both environment names exist.

The default model is `gemini-3.6-flash`, an officially documented stable Flash model that supports structured output and has a free-tier path, subject to your account's quota. You can override it with `GEMINI_MODEL` if your API project has access to another supported Flash model. The implementation follows Google's newer [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), using [structured JSON output](https://ai.google.dev/gemini-api/docs/structured-output).

## Phase 9 handoff notes

Read `docs/SceneLock_Phase1_Project_Specification.md` before changing the input/output contract. Preserve `sample_inputs/test_cases.json` and `evaluation/expected_labels.json` unchanged. Phase 9 code, tests and reproducible offline baseline measurements are completed; **authenticated LLM benchmark evaluation remains blocked** until the user privately configures a key. Do not claim improved Gemini accuracy from the new v3 prompt without a real retest. Human decisions stay in `st.session_state`, separate from untouched model findings, and are copied only into user-requested exports. **Literal quote matching proves provenance, not semantic truth**: the human reviewer retains final authority.

## Troubleshooting

- **`command not found: python3`** — install Python 3.11+ using the Python website above; restart Terminal.
- **`No module named streamlit`** — make sure `source .venv/bin/activate` ran and rerun `python -m pip install -r requirements.txt`.
- **Browser does not open** — visit `http://localhost:8501` while the terminal process is running.
- **Port 8501 already in use** — stop any other Streamlit process (Control + C) or run `python -m streamlit run app.py --server.port 8502`.
- **Gemini key not configured** — expected and harmless for the UI. Create a key only when ready for a real API test.
- **401/403 error** — verify your key and the project's access to the selected model in AI Studio; don't share the key in chat.
- **429 error** — free-tier rate limit or quota reached; check your project usage and try later.
- **Timeout/connection error** — check network access and try again; the adapter performs at most one retry by default.
- **Malformed model response** — the adapter rejects it and clearly reports failure instead of inventing a successful result. A provider error is **not** "Insufficient Context"; that review status is reserved for valid model analyses with insufficient relevant evidence.
- **Download missing** — run an actual successful analysis first; downloads never appear for failed, unauthenticated, or stale results. Exports contain screenplay text, so handle them as confidential files.

