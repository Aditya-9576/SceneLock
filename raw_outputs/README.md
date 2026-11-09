# Raw model outputs

This folder is reserved for **unchanged responses from actual authenticated
Gemini semantic evaluation runs**. The opt-in
`python scripts/live_semantic_smoke.py --case P5-03` command archives its
response here **only after analysis and evidence validation succeed**.
Archives preserve the exact model text, use unique case and analysis IDs,
refuse overwrites, and have owner-only file permissions where supported.

Phase 9 adds `python evaluation/run_phase9.py`, which saves unmodified
provider replies as **T01_response.json through T15_response.json** and
**U01_response.json through U03_response.json**. The evaluation-only observer
runs *before* evidence validation, so a malformed or incomplete provider
reply can be retained for diagnosis even though SceneLock refuses to accept
it as a finding. In those cases the `.json` extension identifies intended
structured output, but the contents may not parse as JSON. Never edit them.

**No authenticated Gemini request succeeded in the Phase 9 development
workspace:** there was no configured key. Therefore no T01–T15 raw files are
present or fabricated. The files inside `sample_exports/`
are labeled *synthetic fixtures*, not raw Gemini predictions.

**Phase 11 submission check (8 November 2026):** The required Kuku raw-AI
output deliverable remains **incomplete**. There are **zero** genuine
`T01_response.json` to `T15_response.json` files here. The project ZIP
deliberately contains only this explanatory README in `raw_outputs/`.
Do not present `evaluation/baseline_predictions.json` or
`sample_exports/*human_authored_example*` as raw AI inference.

The Streamlit UI does **not** automatically save screenplay or raw output
to disk. For any successful live request, it offers a separate
**Download unedited AI response (JSON)** button that downloads the unmodified
structured response as-is from session memory.

Never fabricate or hand-edit raw outputs. Do not commit confidential
screenplays, API keys, or sensitive provider metadata. The `.gitignore`
ignores locally generated raw `.json`, `.jsonl`, and `.csv` files by default.
