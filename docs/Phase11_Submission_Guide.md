# SceneLock - Phase 11 submission guide

**Candidate:** Aditya Gautam  
**Roll number:** 230106003  
**Chosen problem:** Kuku AI Generalist Assignment - Problem Statement 3  
**Prepared:** 8 November 2026

## Read this first

The assignment asks for **(1) a PDF of at most two pages; (2) a link to an
openable prototype or runnable GitHub repository; and (3) a folder of genuine,
unedited outputs of the AI solution**, with an optional walkthrough video of
at most three minutes. Submission goes through the placement-cell form and
the links must be accessible to anyone who has them.

SceneLock's first two deliverables are prepared locally: a two-page PDF and a
complete Python/Streamlit repository. **The third mandatory deliverable is
currently incomplete:** no authenticated Gemini request was made, so there
are zero true Gemini outputs. Do **not** upload manually created fixtures as
if they were model outputs. A GitHub URL and a Streamlit URL also remain
unavailable until the account-side deployment is completed.

## Deliverables and current state

| Item | File or location | Truthful status |
|---|---|---|
| 1 - Solution document | `01_solution_document/SceneLock_Kuku_Solution_Two_Pages.pdf` | **Ready; exactly two A4 pages** |
| 2 - Working prototype | `02_working_prototype/SceneLock_Prototype_Complete.zip` | **Runnable local project; automated tests pass** |
| Public prototype link | GitHub / Streamlit Community Cloud | **Not created or verified**; see `DEPLOYMENT.md` in the project |
| 3 - Raw model responses | `03_raw_ai_outputs/README_RAW_OUTPUTS_STATUS.md` | **Blocked** - no Gemini key, no raw replies |
| Actual evaluation evidence | `05_evaluation_provenance/` | Genuine deterministic baseline, blocked model manifest and failure log; **not AI outputs** |
| 4 - Optional walkthrough | `04_optional_walkthrough/SceneLock_Walkthrough_Script_Storyboard.md` | Storyboard ready; **video not recorded** |

## Before you press Submit

1. **Publish the prototype** from the project ZIP following
   `DEPLOYMENT.md`. Confirm that the exact public URL works in an incognito
   browser, without installation or account access. If public hosting is not
   available, a GitHub repository with the clear README/run steps is
   acceptable according to the Kuku brief.
2. **Configure your Gemini API key privately** in Streamlit secrets or your
   local environment. Never send the key in chat or commit it to GitHub.
3. **Run real evaluation inputs**: the `evaluation/run_phase9.py` runner
   attempts all T01-T15 plus U01-U03 and records exact raw provider replies
   in `raw_outputs/` when authentication succeeds. The current blocked
   manifest proves no calls were made; it is **not** an AI-output substitute.
4. **Inspect every raw response** before sharing it. It must be the unedited
   original, clearly associated with its test ID. Do not rename a hand-authored
   `sample_exports/` fixture to `T01_response.json`.
5. Upload an accessible folder of the real raw outputs, with the test inputs
   and evaluation context, only when they exist. Do not disclose private
   Kuku screenplays, API keys, personally identifying information, or secrets.
6. Review the two-page PDF against the final live measurements. **Replace
   only factual claims that have newly become verified**; do not fill in
   imagined accuracy/latency or unverified website links.
7. In the official placement-cell form, enter your **name** (Aditya Gautam),
   **roll number** (230106003), **branch** (enter your actual branch; not
   inferred here), **Problem 3**, and the valid publicly accessible links for
   the solution PDF, prototype, and raw outputs. Include an optional video
   link only if you have actually recorded and shared the walkthrough.
8. Open each submitted link in a private/incognito window to check public
   accessibility. The PDF is two pages and the walkthrough, if made, must be
   at most three minutes.

## What the actual numbers mean

- **187 passing pytest tests**: software checks including mock-provider and
  Streamlit integration; not authenticated AI semantic accuracy.
- **15 labeled cases / 25 facts**: human-authored ground truth, validated
  without errors.
- **40.0% precision, 28.6% recall**: binary case-level metrics from the
  frozen **keyword-matching baseline**, not from Gemini.
- **0/15 Gemini-labeled and 0/3 unseen authenticated evaluations**: no key was
  available. Therefore Gemini precision, recall, latency and genuine
  model-specific failures are **unmeasured**.
- **Baseline failure T06**: a real false alarm on a later reaction close-up;
  instructions were improved and unit-checked. The model was not retested.

## What to tell Kuku about what is real

The Kuku brief establishes that AI-generated microdrama is an important
production setting; Runway's official video prompting guide documents the
importance of describing subjects and actions in video prompts. **Neither
source verifies a measured screenplay-to-video error rate at Kuku.** The
expected workflow gap and time saved remain hypotheses to test with video
artists. Tell evaluators that SceneLock is a pre-generation text QA assistant,
not a measured end-to-end video-quality guarantee.

## Sources

- Kuku - AI Generalist Assignment, pp. 1, 3-5 (user-provided).
- Runway, [Text-to-Video Prompting Guide](https://help.runwayml.com/hc/en-us/articles/42460036199443-Text-to-Video-Prompting-Guide) (reviewed 8 November 2026).
- Google, [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) (rates can change; use a token-based cost method).
- Streamlit, [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
