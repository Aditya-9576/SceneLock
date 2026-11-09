"""SceneLock Phase 10 — public-ready Streamlit UI with honest offline fallback.

One shot, one validated structured Gemini request, evidence-backed review.
Samples never call the model, and decisions cannot overwrite AI findings.
"""

from __future__ import annotations

import streamlit as st

from analyzer import AnalysisRun, SceneLockAnalyzer
from exports import findings_csv_bytes, review_json_bytes
from model_adapter import (
    GeminiAdapter,
    GeminiConfigurationError,
    GeminiSettings,
    ModelAdapterError,
    load_gemini_settings,
)
from offline_demo import load_validated_offline_demo
from sample_loader import demo_samples
from schemas import AnalysisInput, AnalysisResult, HumanDecision, ReviewStatus, ShotType
from validators import InputValidationError, validate_input_payload


st.set_page_config(
    page_title="SceneLock | Microdrama Prompt QA",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

REVIEW_OPTIONS = {
    "Needs Further Review": HumanDecision.FURTHER_REVIEW.value,
    "Accept Suggestion": HumanDecision.ACCEPT.value,
    "Dismiss as Intentional": HumanDecision.DISMISS.value,
}


def apply_readable_style() -> None:
    """Minimal, static style layer; user text is never rendered as HTML."""
    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 2.0rem; padding-bottom: 3rem; }
        div[data-testid="stMetric"] {
            background-color: #F5F7FA;
            border: 1px solid #E4EAF0;
            border-radius: 0.65rem;
            padding: 0.85rem 1rem;
        }
        div[data-testid="stMetricLabel"] { color: #4D6272; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def available_streamlit_secrets() -> dict[str, str]:
    """Missing local/deployment secrets must not prevent the UI from loading."""
    try:
        return {
            name: st.secrets.get(name, "")
            for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GEMINI_MODEL")
        }
    except (FileNotFoundError, RuntimeError, KeyError):
        return {}


def analyze_request(request: AnalysisInput, settings: GeminiSettings) -> AnalysisRun:
    """One Gemini call, strict checks, Python report and unedited raw output."""
    return SceneLockAnalyzer(GeminiAdapter(settings)).analyze_with_raw(request)


def clear_previous_analysis() -> None:
    """Remove stale report and review widget state without touching inputs."""
    previous = st.session_state.get("analysis_report")
    if previous is not None:
        analysis_id = previous.metadata.analysis_id
        st.session_state.pop(f"edited_prompt_{analysis_id}", None)
        for finding in previous.findings:
            st.session_state.pop(f"decision_{analysis_id}_{finding.finding_id}", None)
    for name in ("analysis_report", "analysis_request", "review_decisions", "analysis_raw_response"):
        st.session_state.pop(name, None)


def load_selected_sample(samples: dict[str, dict[str, str]]) -> None:
    """Called by a button before widgets are instantiated on the new rerun."""
    selected = st.session_state.get("sample_choice", next(iter(samples)))
    for name, value in samples[selected].items():
        st.session_state[name] = value
    clear_previous_analysis()
    st.session_state["sample_notice"] = (
        "Sample loaded. You can edit it freely. No AI request has been made."
    )


def load_offline_demonstration() -> None:
    """Open a real review UI for manual test labels, without calling Gemini."""
    try:
        request, report = load_validated_offline_demo()
    except (OSError, ValueError, KeyError):
        st.session_state["offline_demo_error"] = (
            "The offline example could not be loaded. The live analysis is unaffected."
        )
        return
    clear_previous_analysis()
    for name, value in request.model_dump(mode="json").items():
        st.session_state[name] = value if value is not None else ""
    st.session_state["analysis_report"] = report
    st.session_state["analysis_request"] = request.model_dump(mode="json")
    st.session_state["analysis_raw_response"] = None
    st.session_state["review_decisions"] = {}
    st.session_state["offline_demo_notice"] = (
        "Offline example loaded from human-authored labels. "
        "These are NOT Gemini predictions. Human review and exports are interactive."
    )


def render_sample_picker() -> None:
    samples = demo_samples()
    with st.container(border=True):
        st.markdown("**Start with your own scene or try an example**")
        left, right = st.columns([4, 1], vertical_alignment="bottom")
        with left:
            st.selectbox(
                "Example scene",
                options=list(samples),
                key="sample_choice",
                help="These are fictional cases, not completed model analyses.",
            )
        with right:
            st.button(
                "Load Sample",
                on_click=load_selected_sample,
                args=(samples,),
                use_container_width=True,
            )
        st.caption(
            "Examples demonstrate common production risks: costumes, key actions, "
            "shot scope, identities and Hindi-English text."
        )
    if notice := st.session_state.pop("sample_notice", None):
        st.success(notice)


def render_input_area() -> dict[str, str | None]:
    """All seven input widgets live outside a form so source edits hide stale QA."""
    st.markdown("### Shot details")
    with st.expander("Episode, scene and shot IDs (optional)", expanded=False):
        episode_col, scene_col, shot_col = st.columns(3)
        with episode_col:
            episode_id = st.text_input(
                "Episode ID", max_chars=80, key="episode_id", placeholder="EP01"
            )
        with scene_col:
            scene_id = st.text_input(
                "Scene ID", max_chars=80, key="scene_id", placeholder="SC01"
            )
        with shot_col:
            shot_id = st.text_input(
                "Shot ID", max_chars=80, key="shot_id", placeholder="SH01"
            )

    screenplay_col, prompt_col = st.columns(2, gap="large")
    with screenplay_col:
        screenplay_text = st.text_area(
            "Screenplay *",
            placeholder="Paste the original screenplay excerpt or dramatic beat...",
            height=260,
            max_chars=8000,
            key="screenplay_text",
            help="The screenplay is the source of truth for explicit story requirements.",
        )
        st.caption("Original source · Maximum 8,000 characters")
    with prompt_col:
        video_prompt = st.text_area(
            "Video-generation prompt *",
            placeholder="Paste the exact prompt intended for the video generator...",
            height=260,
            max_chars=4000,
            key="video_prompt",
        )
        st.caption("Candidate shot prompt · Maximum 4,000 characters")

    scope_col, intent_col = st.columns([1, 2], gap="large")
    with scope_col:
        selected_shot = st.selectbox(
            "Shot type *",
            options=["Select a shot type", *[item.value for item in ShotType]],
            key="shot_type",
            help="Choose what this shot is actually intended to show.",
        )
    with intent_col:
        shot_intent = st.text_area(
            "Shot intent (optional unless Custom / other)",
            placeholder="Example: Tight close-up of Meera reacting after hiding the key.",
            height=115,
            max_chars=500,
            key="shot_intent",
        )
    st.caption(
        "* Required. One screenplay excerpt and one intended shot per analysis. "
        "A close-up need not include every action in the larger scene."
    )
    return {
        "screenplay_text": screenplay_text,
        "video_prompt": video_prompt,
        "shot_type": None if selected_shot == "Select a shot type" else selected_shot,
        "shot_intent": shot_intent,
        "episode_id": episode_id,
        "scene_id": scene_id,
        "shot_id": shot_id,
    }


def render_report(report: AnalysisResult, request: AnalysisInput, raw_response_text: str | None) -> None:
    """Human-readable analysis; all decisions remain outside the AI payload."""
    st.divider()
    st.markdown("## Analysis report")
    is_live = report.metadata.analysis_engine == "live_llm"
    if is_live:
        st.caption(
            f"Live LLM analysis · {report.metadata.provider} / {report.metadata.model} · "
            f"{report.metadata.duration_ms} ms · Analysis ID {report.metadata.analysis_id}"
        )
    else:
        st.warning(
            "Offline demonstration — HUMAN-AUTHORED expected labels, NOT a Gemini "
            "analysis or evidence of model accuracy."
        )
        st.caption(f"Fixture: {report.metadata.provider} · Analysis ID {report.metadata.analysis_id}")

    with st.container(border=True):
        status = report.summary.overall_status
        if status == ReviewStatus.REVIEW_REQUIRED:
            st.warning("Review Required — there are findings worth checking before generation.")
        elif status == ReviewStatus.INSUFFICIENT_CONTEXT:
            st.info("Insufficient Context — the available shot information cannot be assessed reliably.")
        else:
            st.success("No Significant Issues Detected — no major discrepancy was returned.")
        metrics = st.columns(4)
        metrics[0].metric("Critical issues", report.summary.critical_issue_count)
        metrics[1].metric("Warnings", report.summary.warning_count)
        metrics[2].metric("Verified facts", report.summary.verified_fact_count)
        metrics[3].metric("Relevant facts", report.summary.relevant_fact_count)
        st.caption(
            f"{report.summary.finding_count} finding(s) across "
            f"{report.summary.extracted_fact_count} extracted fact(s). "
            "Counts are deterministic classifications, not accuracy scores."
        )

    st.markdown("### Findings and human review")
    if not report.findings:
        st.success("No issue cards were returned for this specific shot.")
    else:
        for number, finding in enumerate(report.findings, start=1):
            with st.container(border=True):
                readable_category = finding.category.value.replace("_", " ").title()
                st.markdown(f"**{number}. {readable_category}**")
                st.caption(
                    f"{finding.comparison_status.value} · {finding.severity.value} severity "
                    f"· Finding {finding.finding_id}"
                )
                st.write(finding.explanation)
                evidence_col, prompt_col = st.columns(2, gap="large")
                with evidence_col:
                    st.markdown("**Screenplay evidence**")
                    st.code(finding.screenplay_evidence)
                with prompt_col:
                    st.markdown("**Prompt evidence**")
                    if finding.prompt_evidence is None:
                        st.caption(
                            "Not stated in this prompt. The issue is Missing, "
                            "not an explicit contradiction."
                        )
                    else:
                        st.code(finding.prompt_evidence)
                st.markdown("**Suggested minimal correction**")
                st.write(finding.suggested_fix)
                if finding.uncertainty_note:
                    st.caption(f"Uncertainty: {finding.uncertainty_note}")

                label = st.radio(
                    f"Reviewer decision · {finding.finding_id}",
                    options=list(REVIEW_OPTIONS),
                    key=f"decision_{report.metadata.analysis_id}_{finding.finding_id}",
                    horizontal=True,
                )
                st.session_state.setdefault("review_decisions", {})[
                    finding.finding_id
                ] = REVIEW_OPTIONS[label]

    with st.expander("All extracted facts and shot applicability", expanded=False):
        if not report.facts:
            st.caption("The model returned no verifiable screenplay facts.")
        for fact in report.facts:
            st.markdown(
                f"**{fact.fact_id} · {fact.category.value.replace('_', ' ').title()} "
                f"· {fact.comparison_status.value}**"
            )
            st.write(fact.required_detail)
            st.caption(f"Source quote: “{fact.source_evidence}”")
            st.caption(f"Shot applicability: {fact.applicability_reason}")
            if fact.uncertainty_note:
                st.caption(f"Uncertainty: {fact.uncertainty_note}")

    reviewed = sum(
        value != HumanDecision.FURTHER_REVIEW.value
        for value in st.session_state.get("review_decisions", {}).values()
    )
    st.caption(
        f"Reviewer decisions completed: {reviewed} / {len(report.findings)}. "
        "Choices do not alter the original AI findings or screenplay."
    )

    st.markdown("### Suggested corrected prompt")
    with st.container(border=True):
        edited_prompt = st.text_area(
            "Editable candidate prompt",
            value=report.suggested_corrected_prompt,
            key=f"edited_prompt_{report.metadata.analysis_id}",
            height=170,
            help="Your edits are separate from the original video prompt and model findings.",
        )
        st.caption(
            "Edit or copy this draft if useful. The original prompt and "
            "the unedited AI recommendation remain preserved in the report."
        )

    with st.expander("Download reviewed report", expanded=False):
        st.caption(
            "Exports contain the submitted screenplay. Keep files private "
            "and share only with authorized production teammates."
        )
        decisions = st.session_state.get("review_decisions", {})
        json_data = review_json_bytes(request, report, decisions, edited_prompt)
        csv_data = findings_csv_bytes(request, report, decisions)
        json_col, csv_col = st.columns(2)
        json_col.download_button(
            "Download JSON",
            data=json_data,
            file_name=f"scenelock_review_{report.metadata.analysis_id}.json",
            mime="application/json",
            use_container_width=True,
        )
        csv_col.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"scenelock_findings_{report.metadata.analysis_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.divider()
        if is_live and raw_response_text:
            st.caption(
                "Raw AI response — an unedited provider record for later evaluation. "
                "It is separate from the reviewed JSON/CSV and may contain screenplay details."
            )
            st.download_button(
                "Download unedited AI response (JSON)",
                data=raw_response_text.encode("utf-8"),
                file_name=f"scenelock_raw_{report.metadata.analysis_id}.json",
                mime="application/json",
            )
        else:
            st.caption(
                "No raw Gemini response exists for this manually authored offline example."
            )


def render_page() -> None:
    apply_readable_style()
    st.title("SceneLock")
    st.markdown(
        "**Pre-generation QA for microdrama shots.** Compare a screenplay beat "
        "with its proposed video prompt, spot meaningful differences, "
        "and review the smallest justified fixes before generating footage."
    )
    st.caption("Text-only check · One shot at a time · Human review remains final")

    settings = load_gemini_settings(secrets=available_streamlit_secrets())
    with st.sidebar:
        st.markdown("### AI connection")
        if settings.is_configured:
            st.success("Gemini API key configured")
            st.caption(f"Model: {settings.model}. Only Analyse Prompt sends content to Gemini.")
        else:
            st.warning("Gemini API key not configured")
            st.caption(
                "You can load samples and validate inputs without a key. "
                "To run a live analysis, follow the private key setup in README.md."
            )
            st.markdown("[Get a key in Google AI Studio](https://aistudio.google.com/api-keys)")
        st.divider()
        st.caption(
            "SceneLock checks prompt text only. It does not generate video "
            "or guarantee that a model's interpretation is correct."
        )

    with st.container(border=True):
        st.markdown("**Need a reliable fallback for your evaluator demo?**")
        st.caption(
            "Open a pre-labeled fictional scene to try issue cards, human review, "
            "and downloads without using your Gemini quota. This is NOT an AI prediction."
        )
        st.button("Open Offline Demo (No Gemini)", on_click=load_offline_demonstration)
    if notice := st.session_state.pop("offline_demo_notice", None):
        st.info(notice)
    if error := st.session_state.pop("offline_demo_error", None):
        st.error(error)

    render_sample_picker()
    payload = render_input_area()
    validate_col, analyze_col, spacer = st.columns([1, 1.35, 2.6])
    with validate_col:
        validate_clicked = st.button("Validate Inputs", use_container_width=True)
    with analyze_col:
        analyze_clicked = st.button(
            "Analyse Prompt",
            type="primary",
            use_container_width=True,
            help="Uses one genuine Gemini request when your key is configured.",
        )

    if validate_clicked or analyze_clicked:
        try:
            validated = validate_input_payload(payload)
        except InputValidationError as exc:
            st.error("Please correct the input fields before continuing.")
            for message in str(exc).splitlines():
                st.warning(message)
        else:
            if validate_clicked:
                st.success("Inputs are valid. No AI request was sent.")
            if analyze_clicked:
                clear_previous_analysis()
                if not settings.is_configured:
                    st.error(
                        "Live analysis unavailable: add your Gemini API key locally. "
                        "You can still load samples or validate inputs."
                    )
                else:
                    with st.spinner("Gemini is comparing the screenplay and shot prompt..."):
                        try:
                            run = analyze_request(validated, settings)
                        except (GeminiConfigurationError, ModelAdapterError) as exc:
                            st.error(f"Analysis failed — {exc}")
                        except Exception:
                            # Never expose unfiltered provider errors, user content or keys.
                            st.error("Analysis failed unexpectedly. No report was generated.")
                        else:
                            st.session_state["analysis_report"] = run.report
                            st.session_state["analysis_request"] = validated.model_dump(mode="json")
                            st.session_state["analysis_raw_response"] = run.raw_response_text
                            st.session_state["review_decisions"] = {}
                            st.success("Analysis completed. Evidence and references passed validation.")

    saved_report = st.session_state.get("analysis_report")
    if saved_report is not None:
        try:
            current_request = validate_input_payload(payload)
        except InputValidationError:
            current_request = None
        if (
            current_request is not None
            and current_request.model_dump(mode="json") == st.session_state.get("analysis_request")
        ):
            render_report(
                saved_report,
                current_request,
                st.session_state["analysis_raw_response"],
            )
        else:
            st.info(
                "Your shot inputs have changed since the last analysis. "
                "Run Analyse Prompt again to see a current report."
            )


if __name__ == "__main__":
    render_page()
