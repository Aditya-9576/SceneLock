# SceneLock — Phase 3 Verification Report

**Date:** 8 November 2026  
**Scope:** Local project setup and Streamlit input/validation screen; **no model inference**.

## Environment actually used

- Operating environment: Linux-based project execution workspace (not a macOS machine).
- Interpreter: Python **3.12.14** (meets the project requirement of Python 3.11+).
- Virtual environment: `.venv` created successfully; intentionally excluded from the distributable ZIP.
- Installed and imported: Streamlit **1.67.0**, Pydantic **2.14.3**, google-genai **1.75.0**, pytest **9.2.0**.
- Dependency check: `python -m pip check` → **No broken requirements found**.

## Checks actually performed

| Check | Method | Observed result |
|---|---|---|
| Dependency installation | `.venv/bin/python -m pip install -r requirements.txt` | Success |
| Import smoke | Import `streamlit`, `pydantic`, `google.genai`, `pytest` | Success |
| Python syntax | `python3 -m compileall -q` on application, tests and evaluation files | Success |
| Automated tests | `.venv/bin/python -m pytest -q` | **24 passed** in 1.07 seconds |
| Dataset consistency | `.venv/bin/python evaluation/validate_dataset.py` | **15 cases, 25 facts, 0 errors** |
| Dependency conflicts | `.venv/bin/python -m pip check` | **No broken requirements** |
| Web-server process | Local `streamlit run app.py` headless startup | Reported startup successfully |
| HTTP live health | Same-process local request to `/_stcore/health` on temporary port 8513 | **HTTP 200** |
| UI smoke | `streamlit.testing.v1.AppTest` through pytest | Initial UI, valid user input and invalid form behavior passed |

The first pytest run had **4 failing test assertions** (20 passed): two assertions used an incorrect Streamlit test property (`message` rather than `proto.body`), and two attempted case-sensitive regex matches against capitalized error messages. The tests were corrected; the next run passed **24/24**. These were test-harness mistakes, not observed Gemini or semantic-analysis errors.

## Intentionally untested in Phase 3

- Actual Gemini model connectivity, provider quota, billing, or generation.
- Semantic fact extraction, comparison classification, corrected prompts and evidence validation of model outputs.
- Final JSON/CSV report export or human review of AI findings.
- macOS-specific local execution. The README includes beginner-friendly macOS commands, but the application was **verified here on Linux/Python 3.12**, not on the user's Mac.

## What this verifies

Phase 3 produces a real startup-ready application and a tested input-validation path. It does **not** yet satisfy the full assignment's requirement for live semantic analysis; that work explicitly begins in Phase 4. No model findings or LLM accuracy metrics have been fabricated.
