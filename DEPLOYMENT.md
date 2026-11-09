# SceneLock — Publish Online for Kuku Evaluators

This is the **click-by-click Phase 10 deployment guide**. No coding is needed
to complete the remaining account steps. The project is already organized for
GitHub and Streamlit Community Cloud.

**Important:** This guide describes steps to perform in **your own GitHub,
Streamlit and Google accounts**. The project ZIP is ready, but a public URL
does not exist until the GitHub upload and Streamlit deployment succeed.

## Part A — Put the project on GitHub

1. Download `SceneLock_Phase10_Deployment_Ready.zip` from the ChatGPT response.
2. On your Mac, double-click the ZIP. Open the extracted **SceneLock** folder.
   It must directly contain `app.py`, `requirements.txt` and `README.md`.
3. To display hidden configuration folders in Finder, press
   **Command + Shift + .** (period). You should now see `.streamlit` and
   `.github`. Both contain only safe public configuration and workflow files.
4. Open **https://github.com/new** and sign in to your GitHub account.
5. Under **Repository name**, type exactly `SceneLock`.
6. Select **Public** so Kuku evaluators can inspect the source if desired.
7. Leave **Add a README file**, **Add .gitignore**, and **Choose a license**
   unchecked. The project already includes its README and ignore rules;
   no license has been chosen without your decision.
8. Click **Create repository**.
9. On the empty repository page, click **uploading an existing file** (or use
   **Add file → Upload files**, if the repository page shows that menu).
10. From Finder, select the **contents inside the SceneLock folder**, including
    `.streamlit` and `.github`, and drag them to GitHub's upload area.
    **Do not upload the SceneLock folder as an extra nested directory.**
    The repository root must contain `app.py`.
11. In the **Commit changes** section, use a simple message such as
    `Initial SceneLock deployment-ready application`, then click
    **Commit changes** or **Propose changes** as shown by GitHub.
12. Reopen your repository's **Code** tab. Confirm these appear at the top
    level: `app.py`, `requirements.txt`, `offline_demo.py`, `.streamlit/`,
    `.github/`, `sample_exports/` and `README.md`.
13. Open **Actions** on GitHub. The included **SceneLock quality checks**
    workflow is intended to run on pushes; wait for its green check. A red
    run means check its log before deploying. GitHub may request you to
    enable workflows for a new repository.

**NEVER upload:** `.streamlit/secrets.toml`, `.env`, `.env.local`, an API
key, a `.venv/` folder, `raw_outputs/T01_response.json` or any private
screenplay. The provided ZIP excludes secrets, virtual environments, Git
internals, and real raw responses. It includes synthetic test cases only.

If you connect the authorized GitHub integration in ChatGPT later, the
assistant may be able to publish the same files without these manual uploads.

## Part B — Deploy on Streamlit Community Cloud

1. Open **https://share.streamlit.io**.
2. Click **Sign in** and use your **GitHub** account; authorize Streamlit's
   requested repository access if prompted.
3. In the Streamlit workspace, click **Create app**.
4. If asked whether you already have an app, choose **Yup, I have an app**
   (the option to deploy an existing GitHub repository).
5. Enter or select:
   - **Repository:** `<your-GitHub-username>/SceneLock`
   - **Branch:** `main`
   - **Main file path:** `app.py`
6. Optionally choose a memorable, available **App URL** subdomain; Streamlit
   shows whether your choice is free. Do not assume a subdomain is available.
7. Click **Advanced settings**.
8. Set **Python version** to **3.12** (the version used for local verification).
9. In the **Secrets** field, enter the following using your **real key in your
   own Streamlit account**. The text below is a placeholder, not a secret:

   ```toml
   GEMINI_API_KEY = "REPLACE_WITH_YOUR_REAL_KEY"
   GEMINI_MODEL = "gemini-3.6-flash"
   ```

   Get a key privately at **https://aistudio.google.com/api-keys**. Never
   paste it into ChatGPT, GitHub, screenshots, or the public README.
   Streamlit stores these values as deployment secrets; the key is not
   committed to the GitHub repository.
10. Click **Save** in Advanced settings, then **Deploy**.
11. Allow Streamlit to install the dependencies and start the app. When it
    finishes, copy the actual `https://...streamlit.app` address from your
    browser. **The deployment is not verified until this address loads.**

You can also deploy **without a key** to demonstrate the clearly labeled
offline fixture. The sidebar will say the key is not configured; real
**Analyse Prompt** calls will be unavailable until you add the key in the
app's **Settings → Secrets** and restart the app. Never put the key in code.

## Part C — Test the public app as a Kuku evaluator

1. Open the new Streamlit URL in an **Incognito/Private window** where you
   are not signed in. For a public app, it should load without software
   installation or sign-in. If it prompts for access, check the app's
   sharing/visibility settings in Streamlit Cloud.
2. Under **Screenplay**, enter this NEW fictional example:

   > Kavya slips a silver compass into a red backpack before crossing the bridge.

3. Under **Video-generation prompt**, enter:

   > Kavya tucks a silver compass into a blue backpack, then crosses the bridge. Golden backlight.

4. Select **Action shot**.
5. Set **Shot intent** to:

   > Show the compass being stowed in Kavya's red backpack before she crosses the bridge.

6. Click **Validate Inputs**. The app should report valid inputs without
   making an API request.
7. Click **Analyse Prompt**. With a configured key/quota, a real Gemini
   request should run. **Inspect the actual response**: the red/blue bag
   discrepancy should ideally be flagged, but do not claim detection if it
   is missing or rejected by evidence validation.
8. If an issue appears, review its exact screenplay and prompt quotations.
   Set **Accept Suggestion** (or another human-review decision).
9. Edit the suggested corrected prompt. Confirm your edit is independent
   from the original screenplay and AI findings.
10. Expand **Download reviewed report**. Click **Download JSON** and
    **Download CSV**. Open both files and confirm the source evidence,
    finding, human decision and revised text are correct.
11. A successful live analysis also offers **Download unedited AI response**.
    Keep that raw file private; it may contain submitted screenplay details.

Only mark the live smoke test **PASSED** after performing all of the above
on the **actual public URL**. Automated local tests alone do not prove public
availability, Gemini quality or Cloud secrets configuration.

## Part D — Offline fallback if Gemini quota fails

Even when Gemini is unavailable, evaluators can still inspect the UI:

1. Open the hosted SceneLock app (no key required for this fallback).
2. Click **Open Offline Demo (No Gemini)**.
3. The app displays a **prominent warning** explaining that this is a
   human-authored fixture, **not a Gemini prediction**.
4. Inspect the red-envelope actor reversal, change its human-review decision,
   edit the corrected prompt, and download both JSON and CSV files.
5. Explain honestly that this verifies the review and reporting workflow,
   while real model semantic accuracy remains untested if quota is blocked.

If Streamlit hosting itself is unavailable, use the bundled
`sample_exports/` reports and `docs/Phase9_Engineering_Evaluation_Report.md`
as a static fallback. You can also run the app locally using the main README
and screen-share the demonstration. **Do not claim a static report is a live
AI inference.**

## Useful official documentation

- [Streamlit: Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit: Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Streamlit: Share your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)
- [GitHub: Create a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
- [GitHub: Upload files and folders](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

## Deployment status checklist

- [x] Production dependencies pinned to locally installed and tested versions.
- [x] GitHub-ready root layout, safe secret example and ignore rules.
- [x] No real credentials or confidential screenplay outputs in deployment ZIP.
- [x] Honest no-key fallback demo, review and export controls.
- [x] Automated no-key UI, mocked end-to-end and regression checks.
- [ ] GitHub repository **created in an authorized account**.
- [ ] Streamlit Community Cloud app **deployed to an actual public URL**.
- [ ] Real Gemini response, human review, JSON and CSV **verified on that URL**.
- [ ] Incognito/unauthenticated public access **verified**.

**Never publish a guessed GitHub or Streamlit URL.** Record the true URL only
after the site is created and tested.
