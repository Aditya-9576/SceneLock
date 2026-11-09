# SceneLock — Phase 7 Streamlit UI Verification

**Date:** 8 November 2026  
**Scope:** A simple, professional one-page artist interface over the existing validated SceneLock backend.

## Artist workflow implemented

1. **SceneLock introduction:** one clear heading, product explanation and scope disclaimer.
2. **Load Sample:** choose one of the original synthetic cases T01, T03, T05, T06, T09 or T15 and click Load Sample. The screenplay, prompt, shot type, intent and optional IDs populate the editable widgets. No model request or expected-label data is transmitted by the sample loader.
3. **Edit or enter a shot:** optional episode/scene/shot IDs, screenplay text area, candidate video-prompt text area, one of seven shot types, optional shot intent.
4. **Validate Inputs:** checks fields without contacting Gemini and shows friendly field-specific issues.
5. **Analyse Prompt:** invokes the existing single structured Gemini request only when an API key is configured, with a visible spinner and distinct failure messages.
6. **Read the result:** Python-owned overall status and issue metrics; one evidence-backed issue card per finding with category, status, severity, explanation, actual quotes and minimal fix.
7. **Human decision:** each card offers Needs Further Review (default), Accept Suggestion, or Dismiss as Intentional. Choices are stored by finding ID only in `st.session_state`, separate from original model facts/findings.
8. **Use the suggestion:** independently editable proposed prompt; the original video prompt and untouched AI recommendation remain preserved.
9. **Download on demand:** reviewed JSON and CSV from the current validated result (Phase 6 behavior retained). Failed, unauthenticated, and stale results have no report/download controls.

The layout uses Streamlit's native widgets, readable labels, responsive two-column inputs, restrained light-theme styling and collapsible optional sections. It adds no database, account system, video generation or heavyweight dashboard framework.

## Actual verification

| Check | Result |
|---|---|
| Automated suite | **121 passed** with `python -m pytest -q` on local Python 3.12 |
| Initial page and input widgets | Passed in Streamlit `AppTest`; no key needed to open the page |
| Load Sample | Passed: T03 populated screenplay, prompt, shot type and episode ID without any model result |
| Manual input validation | Passed: valid unknown text accepted; empty fields and missing Custom/other intent show errors |
| Analyze without a key | Passed: honest error, no fabricated findings/summary/download |
| Full analysis dashboard rendering | Passed with an injected **mock model response**, not an authenticated Gemini call |
| Human decisions | Passed with two independently reviewed findings; accepting one and dismissing another did not modify original AI findings |
| Reviewer-edited prompt | Passed: editing it did not modify original source prompt, model suggestion or trigger a new model call |
| Source edited after analysis | Passed: stale report and download section hidden immediately |
| Load another sample after analysis | Passed: previous findings/reviewer controls cleared, no extra Gemini request |
| Simulated provider quota failure | Passed: error shown and no `Insufficient Context` report produced |
| Original Phase 2 labels | 15 cases, 25 human-labeled facts, 0 validation errors; unchanged |
| Authenticated Gemini UI request | **NOT RUN:** no configured API key in this workspace |

The initial UI refactor changed input buttons from form submits to ordinary Streamlit buttons; old form-specific test selectors failed as expected and were updated to exercise the new immediate-feedback workflow. The final suite is green. Mocked model success is **not** evidence of Gemini's semantic accuracy.

## Beginner macOS use

Follow the root `README.md`. Install Python 3.11+, create/activate the project virtual environment, install `requirements.txt`, and run:

```bash
python -m streamlit run app.py
```

This opens the local app. Try **T01 — Costume contradiction**, **T05 — Missing critical action**, and **T06 — Reaction close-up scope** first. To run actual Gemini inference, privately configure an API key using the included `python scripts/setup_gemini_key.py` helper. Do **not** share the key in chat or include it in a ZIP.

## Genuine limitations

- The full page and interactions were tested in-process by Streamlit's AppTest; no claim is made that an authenticated Gemini interaction succeeded or that a deployed public app was tested.
- AI classifications still require human judgment; evidence validation proves exact textual provenance, not perfect semantic understanding.
- Reviewer decisions persist for the current browser session only. They are not stored in an external database or shared between users.
- Input examples are synthetic and deliberately do not include evaluation labels when sent to the model.
- The user's Phase 7 request prioritized UI implementation; the earlier roadmap's live T01–T15 benchmark evaluation remains a separate future task.
