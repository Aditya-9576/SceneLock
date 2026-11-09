# SceneLock - Independent Engineering QA and Submission Decision

**Review date:** 8 November 2026  
**Candidate:** Aditya Gautam, roll 230106003  
**Reference:** Kuku AI Generalist Assignment, Problem Statement 3  
**Decision:** **Locally runnable and verified; not yet a complete Kuku submission.**

## Scope and independence

I inspected the six-page Kuku assignment, the user's SceneLock roadmap,
the final Python/Streamlit modules, data, labels, automated tests, deployment
rules and two-page PDF. I ran the actual checks listed below and added
independent, previously unseen regression inputs. Source text and labels
remained unchanged. No authenticated Gemini key, remote GitHub repository,
or public Streamlit app was available for end-to-end cloud validation.

## Final requirement checklist

Status definitions: **Complete** = directly inspected and executed/verified
where possible; **Partially Complete** = implemented but some critical
unverified assumption remains; **Blocked** = missing external access or
required real evidence.

| Requirement | Status | Verified evidence and qualification |
|---|---|---|
| Problem 3: narrow, relevant user/problem/solution | **Partially Complete** | Kuku's brief validates AI-microdrama setting and Runway validates prompt-centric process. A particular Kuku QA error rate and interviews are **not** documented; workflow pain is a hypothesis. |
| Complete source architecture | **Complete** | Reviewed `app.py`, `analyzer.py`, `model_adapter.py`, `schemas.py`, `prompts.py`, `validators.py`, `exports.py`, `raw_archive.py`, and runnable tests. |
| Accept completely new input | **Complete** | New Saira reaction close-up passed actual request, analyzer, schema, JSON and header-only CSV checks using a clearly mocked adapter. Earlier Kavya case covered Streamlit form and human decisions. |
| Real replaceable Gemini API implementation | **Partially Complete** | Official Google documentation confirms Interactions structured JSON support for stable `gemini-3.6-flash`; installed SDK signature accepts used arguments. Mocked errors tested. No authenticated request succeeded. |
| Screenplay extraction and semantic matching | **Partially Complete** | Stages A/B/C and conservative synonyms/roles are in `prompts.py`. No verified model semantic performance or live output. |
| Evidence and relationship verification | **Complete** | Python rejects invented/nonliteral quotations, invalid references, empty facts, malformed JSON, duplicate IDs/keys and new punctuation-only fake evidence. |
| Severity, counts and overall status | **Complete** | Pydantic enums and deterministic `derive_summary` verified in tests, independent of model arithmetic. Semantic severity assignments remain model proposals requiring review. |
| Ignore irrelevant shot-scope omissions | **Partially Complete** | Intent/timing instructions, Not Applicable rule and mock-provider scope tests pass; real Gemini false-positive rate unmeasured. |
| Human review without overwriting AI findings | **Complete** | Session decisions and independently editable prompt verified; JSON decision section remains separate. Browser session state is intentionally not long-term storage. |
| JSON/CSV and Unicode exports | **Complete** | Actual functions tested, including commas/newlines/Hindi, safe CSV quoting, reviewer decisions and no-finding headers. |
| Validated automated tests | **Complete** | Latest run: **187 passed in 2.32 s** on local Python environment. |
| Genuine AI evaluations and unedited outputs | **Blocked** | 0/15 original and 0/3 unseen Gemini requests; no key; `raw_outputs/` contains README only. Keyword baseline data must not be mislabeled AI output. |
| Accessible public application/repository | **Blocked** | Local Git repo exists with no remote; Streamlit localhost health HTTP 200, but no publicly verified GitHub/Streamlit link. |
| Professional solution PDF, max 2 pages | **Complete** | `docs/SceneLock_Kuku_Solution_Two_Pages.pdf` confirmed **exactly 2 A4 pages**, rendered and visually inspected. |
| Mandatory Kuku solution PDF | **Complete** | Real file exists, but a public anyone-with-link upload still needed for the form. |
| Mandatory prototype link | **Blocked** | Runnable repository ZIP is ready; public URL not created. |
| Mandatory raw AI output folder | **Blocked** | Cannot provide genuine model replies without credentials; explanatory README only. |
| Optional 3-minute walkthrough | **Partially Complete** | Final 2:50 script/storyboard ready. Video not recorded or shared. |
| Safe submission package | **Complete** | ZIP built from Git-tracked files, with dedicated honest raw-output status and separate measured baseline evidence; no secrets included. |

## Executed checks - actual results

| Command/check | Observed result |
|---|---|
| `.venv/bin/python -m pytest -q` | **187 passed in 2.29 seconds** in the final verification run |
| `.venv/bin/python evaluation/validate_dataset.py` | **15 cases, 25 facts, 0 errors** |
| `.venv/bin/python evaluation/keyword_baseline.py` | **TP 2, FP 3, TN 5, FN 5; precision 0.4; recall 0.2857**, binary case-level keyword algorithm only |
| `.venv/bin/python -m pip check` | No broken requirements found |
| `.venv/bin/python -m compileall -q ...` | Exit 0 |
| `.venv/bin/python scripts/local_deployment_smoke.py` | Actual localhost `/_stcore/health`: HTTP 200 OK; **not public** |
| `.venv/bin/python scripts/release_audit.py` | No detected credentials/raw model output among publishable candidates; manual audit remains wise |
| `pdfinfo` + rendered page inspection | Exactly two A4 PDF pages; text and tables readable |
| Gemini auth credentials present | **No** (`GEMINI_API_KEY` and `GOOGLE_API_KEY` unset; no private secrets file) |
| Online Git/Streamlit availability | No `git remote`; no authorized GitHub deployment connection; **no public URL verified** |

### New independently observed bugs and corrections

**QA-01 - punctuation-only content was accepted.** Original reproduction:
`screenplay_text='...'`, `video_prompt='!!!'` passed field validation.
Even a source-evidence quote of `'...'` could pass if that substring was
in the screenplay. Five newly written regression checks initially failed.
Root cause: checking Unicode-visible punctuation alone, instead of at least
one letter or number. Fix: `schemas.has_semantic_text` now protects required
screenplay/prompt, shot intent, fact descriptions, evidence and corrected
prompt. Exact quote validation uses the same rule. All five checks passed
after the change; Hindi and other language tests still pass.

**QA-02 - documentation placeholders were treated as credentials.**
`REPLACE_WITH_YOUR_REAL_KEY` and `YOUR_REAL_GEMINI_API_KEY` incorrectly set
`GeminiSettings.is_configured=True`. Both new regression cases failed first.
Fix: recognize these exact placeholder strings as unset. Both pass now;
real key values remain private and were not inspected.

**QA-03 - independent new-input/scope acceptance.** Fictional screenplay:
Saira hides a brass locket in a trunk *before* a later reaction shot.
Mocked structured analysis labels the earlier action **Not Applicable** and
the in-shot gasp **Supported**. Actual Python analyzer computes
`No Significant Issues Detected`, relevant=1, verified=1, findings=0,
and JSON/CSV export passes. The mock is manually authored; this **does not
prove Gemini would make the same classification**.

## AI quality evidence and failures

The *real executed* deterministic keyword baseline made 8 binary case-level
errors. **T06** incorrectly flagged a past off-frame key-hiding action in
a later face close-up; **T14** missed reversed antidote giver/receiver roles
despite shared words. Prompt instructions were improved in Phase 9 and
regression contracts pass. These are **algorithm errors, not Gemini errors**.
The earlier implementation also fixed invisible Unicode evidence and raw
response archiving of rejected model text. **No real Gemini mistake or
successful model retest can be asserted** without an authenticated run.

No actual model issue-level precision, recall, latency, shot-scope false
positive rate, evidence-failure rate, throughput, cost per shot, or production
savings is measured. The API adapter is prepared but never successfully used
with an authenticated key in this workspace.

## Remaining operational steps - minimum beginner actions

1. **Create/open a public GitHub repo:** [github.com/new](https://github.com/new).
   Name it **SceneLock**, select Public, then upload the **contents** of the
   supplied project ZIP's SceneLock folder. Confirm `app.py` is at the root.
   If a GitHub integration becomes authorized, an assistant could publish it;
   none is authorized right now.
2. **Create a private API key:** [Google AI Studio API Keys](https://aistudio.google.com/api-keys).
   Keep it in your Google/Streamlit account, never the chat or repository.
3. **Deploy Streamlit (recommended):** [share.streamlit.io](https://share.streamlit.io),
   connect GitHub repo `SceneLock`, branch `main`, entry point `app.py`,
   Python 3.12. Use Advanced Settings -> Secrets to enter
   `GEMINI_API_KEY = "...your private key..."` yourself.
4. **Run actual Gemini cases** before treating the raw output requirement as
   complete. The project documents one command in `README.md`:
   `python evaluation/run_phase9.py`. Real unedited text will appear under
   `raw_outputs/T01_response.json` etc **only when provider responses arrive**.
5. **Verify external access:** open the real deployed URL in a private window,
   run a completely fresh screenplay/prompt, inspect evidence and human review,
   download JSON and CSV. If no app can be hosted, Kuku accepts a publicly
   viewable GitHub repo with clear run instructions; it still requires actual
   raw output files.
6. **Upload all deliverable links:** solution PDF (<=2 pages), public prototype
   or repo, and authentic raw-output folder; optional <=3-minute recording.
   Check every link as an anonymous reader. Enter your actual degree branch
   into Kuku's form; the branch was not guessed from course history.

**Integrity advice:** Never upload Kuku's private input pack, unapproved
third-party scripts, credentials, private screenplay text, or human-created
fixtures relabeled as Gemini responses.
