# SceneLock — Phase 10 Deployment Readiness Report

**Date:** 8 November 2026  
**Scope:** Repository preparation, Streamlit Community Cloud compatibility,
secret protection, local HTTP/UI tests, reviewer fallback and honest blockers.

## Deployment state

**Ready to upload, NOT publicly deployed.** The GitHub integration was not
connected to an authorized account in this session, and there was no
Streamlit Community Cloud deployment connection. A public repository URL
and live Streamlit URL therefore **do not exist as verified deliverables**.
No real Gemini key was available, so neither a public live Gemini request nor
an incognito-access public site check could be performed.

The repository is prepared locally on the `main` branch. For a beginner,
`DEPLOYMENT.md` gives the exact steps to create `SceneLock` on GitHub, upload
the project root, configure Streamlit Community Cloud and test the generated
site without guessing a URL.

## Changes made

1. **Reproducible runtime:** `requirements.txt` now pins the exact locally
   verified versions: Streamlit 1.67.0, Pydantic 2.14.3, Google GenAI 2.34.0
   and HTTPX 0.28.1. Test-only pytest 9.2.0 is in `requirements-dev.txt`.
   The Cloud guide explicitly selects Python **3.12**.
2. **Safe public layout:** `app.py` and `requirements.txt` are at the
   repository root, with `.streamlit/config.toml`. API keys load only from
   environment variables or private Streamlit secrets. A placeholder
   `.streamlit/secrets.toml.example` is safe to commit; the real
   `secrets.toml` and `.env*` files are ignored.
3. **Publish safeguards:** `.gitignore` excludes raw model responses,
   virtual environments, key/certificate files, local secrets and caches.
   `scripts/release_audit.py` scans publish candidates for accidentally
   included key files, sensitive provider outputs and recognizable token
   patterns without revealing their values.
4. **Automated GitHub quality gate:** `.github/workflows/tests.yml` runs
   dataset validation, release audit, pytest and an actual local Streamlit
   HTTP health request on Python 3.12. The workflow itself cannot be tested
   on GitHub until the repository is uploaded.
5. **Offline fallback:** A clearly marked **Open Offline Demo (No Gemini)**
   button loads the existing human-authored envelope reversal fixture. It
   revalidates report evidence, exposes all human-review controls and allows
   independent JSON/CSV downloads without making a model request. It never
   claims to be Gemini output and does not provide a fake raw AI response.
6. **New production-style input test:** A fictional Kavya compass/red vs
   blue backpack scene was entered through the real Streamlit application
   using an injected test provider. The UI showed the structured issue,
   human decisions remained separate, and JSON/CSV generation preserved the
   actual source and reviewer edit. This validates wiring, **not Gemini
   correctness**.
7. **Step-by-step deployment and fallback guide:** `DEPLOYMENT.md` covers
   GitHub repository creation, hidden folder upload, Streamlit app setup,
   private Gemini secrets, incognito review, fresh-prompt test and static
   backup if quota/hosting is unavailable.

## Executed engineering checks

| Check | Observed result |
|---|---|
| `python -m pytest -q` | **179 passed in 2.48 s** |
| `python -m pip check` | No broken requirements found |
| Python `compileall` on source, scripts and tests | Exit 0 |
| `python scripts/release_audit.py` | Passed; no detected credentials or raw model output in publishable files |
| `python scripts/local_deployment_smoke.py` | **Passed: actual loopback HTTP `/_stcore/health` returned 200 OK** |
| New Kavya screenplay UI/analyzer/export integration test | Passed with explicitly mocked provider |
| Offline human-authored demo UI and review tests | Passed; no Gemini key required |
| Phase 2 original dataset and baseline | Preserved unchanged; earlier 0 dataset errors |

The first attempt to query a Streamlit server started in a different local
execution session did not connect across those isolated runtime sessions.
The reusable `local_deployment_smoke.py` runs the server and HTTP probe in the
**same** process environment and succeeded; it terminates its own child
process. This is an actual local HTTP smoke test but is **not** a public
deployment or external accessibility check.

## What remains account-side

- Create the public **SceneLock** repository inside the user's authenticated
  GitHub account and upload the provided repository-root files; or connect an
  authorized GitHub integration and publish the same content.
- In Streamlit Community Cloud, create an app from `main` → `app.py`, select
  Python 3.12 and privately configure `GEMINI_API_KEY` in deployment secrets.
- Verify the actual generated `.streamlit.app` URL in a logged-out private
  browser window and confirm the page requires **no installation**.
- Run the new Kavya screenplay/prompt through **the real hosted Gemini
  request**, inspect evidence-backed issue detection, make a human review
  choice, edit the corrected prompt and download JSON/CSV.
- If the key/quota is unavailable, use the clearly labeled offline example
  for a truthful interface demonstration, and provide the static synthetic
  sample reports as a hosting-outage backup.

**No external account was modified and no fabricated GitHub or Streamlit
link is included.** Do not mark Phase 10 public deployment complete until
the four remaining account-side checks are genuinely observed.
