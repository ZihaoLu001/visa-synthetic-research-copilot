from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from synthetic_researcher.calibration import build_panel_calibration
from synthetic_researcher.consulting import (
    build_decision_brief,
    default_research_brief,
    format_decision_brief_markdown,
    methodology_snapshot,
)
from synthetic_researcher.delivery import (
    build_consultant_delivery_pack,
    build_pilot_readiness_gate,
    readiness_status_counts,
)
from synthetic_researcher.ingestion import SurveyExtractionError, extract_survey_text, supported_upload_types
from synthetic_researcher.llm import LLMError, get_llm, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.pdf_report import build_consultant_pdf_report
from synthetic_researcher.reporting import build_markdown_report
from synthetic_researcher.sampler import load_benchmark_data, load_personas
from synthetic_researcher.schemas import Concept, SurveyRun
from synthetic_researcher.survey_scope import limit_survey_questions

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEMO_SURVEYS = ROOT / "demo" / "external_survey_tests"
PUBLIC_UPLOADS = ROOT / "demo" / "public_survey_uploads"
LIVE_APP_URL = "https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud/"
FEDERAL_RESERVE_SURVEY_SOURCE = (
    "https://www.federalreserve.gov/econresdata/mobile-devices/"
    "2015-appendix-2-survey-of-consumers-use-of-mobile-financial-services-2014-questionnaire.htm"
)


st.set_page_config(page_title="VCA Multi-Agent Synthetic Researcher", layout="wide", page_icon="V")

st.markdown(
    """
    <style>
    :root {
      --visa-blue: #1a1f71;
      --visa-electric: #1434cb;
      --visa-gold: #f7b600;
      --ink: #111827;
      --muted: #64748b;
      --line: #dbe3ef;
      --surface: #ffffff;
      --wash: #f5f7fb;
    }
    .stApp {
      background: linear-gradient(180deg, #ffffff 0%, #f5f7fb 58%, #eef3fb 100%);
      color: var(--ink);
    }
    .block-container {
      padding-top: 1.4rem;
      padding-bottom: 2rem;
      max-width: 1380px;
    }
    [data-testid="stSidebar"] {
      background: #f8fafc;
      border-right: 1px solid var(--line);
    }
    .visa-shell {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.92);
      padding: 22px 24px;
      border-radius: 8px;
      box-shadow: 0 18px 48px rgba(26,31,113,0.08);
      margin-bottom: 18px;
    }
    .visa-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
    }
    .visa-title {
      font-size: 34px;
      line-height: 1.05;
      font-weight: 760;
      letter-spacing: 0;
      color: var(--visa-blue);
      margin: 0 0 8px;
    }
    .visa-subtitle {
      color: var(--muted);
      font-size: 15px;
      line-height: 1.5;
      max-width: 850px;
    }
    .visa-logo {
      font-weight: 900;
      font-style: italic;
      letter-spacing: -1px;
      color: var(--visa-electric);
      font-size: 42px;
      line-height: 1;
      white-space: nowrap;
    }
    .mini-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 700;
      margin-bottom: 2px;
    }
    .metric-card {
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 8px;
      padding: 15px 16px;
      min-height: 116px;
    }
    .metric-value {
      color: var(--visa-blue);
      font-size: 30px;
      font-weight: 780;
      line-height: 1;
      margin-top: 6px;
    }
    .metric-caption {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      margin-top: 8px;
    }
    .status-green { color: #0f7a45; font-weight: 760; }
    .status-amber { color: #a16207; font-weight: 760; }
    .status-red { color: #b42318; font-weight: 760; }
    .section-note {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin-top: -6px;
      margin-bottom: 10px;
    }
    div[data-testid="stMetric"] {
      border: 1px solid var(--line);
      background: white;
      border-radius: 8px;
      padding: 14px 16px;
    }
    div[data-testid="stMetric"] label {
      color: var(--muted);
      font-size: 13px;
    }
    div[data-testid="stMetricValue"] {
      color: var(--visa-blue);
      font-size: 26px;
    }
    .stButton > button {
      border-radius: 6px;
      font-weight: 700;
    }
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
      background: var(--visa-electric) !important;
      border-color: var(--visa-electric) !important;
      color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
      background: var(--visa-blue) !important;
      border-color: var(--visa-blue) !important;
      color: white !important;
    }
    .stDownloadButton > button {
      border-radius: 6px;
      font-weight: 700;
    }
    .workflow-step {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.94);
      border-radius: 8px;
      padding: 16px 18px;
      margin: 12px 0;
    }
    .workflow-step-head {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 4px;
    }
    .step-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 30px;
      height: 30px;
      border-radius: 999px;
      background: var(--visa-electric);
      color: white;
      font-weight: 780;
      font-size: 14px;
    }
    .workflow-step-title {
      color: var(--visa-blue);
      font-size: 18px;
      line-height: 1.2;
      font-weight: 760;
      margin: 0;
    }
    .workflow-step-copy {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin-left: 40px;
    }
    .upload-proof {
      border: 1px solid #bfe3cf;
      background: #effaf3;
      border-radius: 8px;
      padding: 12px 14px;
      color: #14532d;
      font-size: 14px;
      line-height: 1.45;
    }
    .decision-callout {
      border-left: 5px solid var(--visa-electric);
      background: #ffffff;
      border-radius: 8px;
      padding: 18px 20px;
      box-shadow: 0 12px 32px rgba(26,31,113,0.08);
      margin-bottom: 16px;
    }
    .decision-headline {
      color: var(--visa-blue);
      font-size: 21px;
      font-weight: 780;
      line-height: 1.35;
      margin-bottom: 8px;
    }
    .decision-copy {
      color: var(--ink);
      font-size: 15px;
      line-height: 1.5;
    }
    .proof-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .proof-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.94);
      border-radius: 8px;
      padding: 14px 15px;
      min-height: 112px;
    }
    .proof-card strong {
      display: block;
      color: var(--visa-blue);
      font-size: 15px;
      margin-bottom: 6px;
    }
    .proof-card span {
      color: var(--muted);
      font-size: 12.5px;
      line-height: 1.4;
    }
    .proof-card.green {
      border-color: #bfe3cf;
      background: #f4fbf7;
    }
    .proof-card.amber {
      border-color: #f1d38a;
      background: #fffaf0;
    }
    @media (max-width: 900px) {
      .proof-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .visa-head { flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    st.markdown(
        """
        <div class="visa-shell">
          <div class="visa-head">
            <div>
              <h1 class="visa-title">VCA Multi-Agent Synthetic Researcher</h1>
              <div class="visa-subtitle">
                A consultant-grade copilot for early-stage value proposition screening. Upload a survey,
                interview guide or proposition test, run Swiss synthetic customer agents, and export
                persona-level evidence, aggregate insights, validation checks and a VCA decision brief.
              </div>
            </div>
            <div class="visa-logo">VISA</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Run Settings")
        wx_status = watsonx_config_status()
        provider_options = ["watsonx", "mock"]
        provider_default = 0 if wx_status["configured"] else 1
        provider = st.selectbox(
            "Model provider",
            provider_options,
            index=provider_default,
            help="Use watsonx for the real IBM Granite model run. Mock is only a deterministic fallback.",
        )
        if provider == "watsonx" and wx_status["configured"]:
            st.success(f"Real LLM ready: {wx_status['model_id']}")
        elif provider == "watsonx":
            st.error("watsonx selected but credentials are missing: " + ", ".join(wx_status["missing"]))
        else:
            st.warning("Mock fallback selected. Use watsonx for the final real-model proof.")
        micro_n = st.slider(
            "Synthetic respondents",
            min_value=12,
            max_value=96,
            value=12 if wx_status["configured"] else 96,
            step=12,
            help="Use 12 for a quick live Granite proof; move to 96 for the full presentation run.",
        )
        consistency_runs = st.slider(
            "Repeated consistency runs",
            min_value=1,
            max_value=3,
            value=1 if wx_status["configured"] else 2,
            step=1,
            help="Use 1 for a fast live-model proof; use 2-3 when presenting internal-consistency evidence.",
        )
        run_scope = st.selectbox(
            "Run scope",
            [
                "Quick real-model proof (first 2 questions)",
                "Focused consultant test (first 4 questions)",
                "Full survey",
            ],
            index=0 if wx_status["configured"] else 2,
            help=(
                "Use a smaller scoped run when proving the live watsonx model to conserve classroom quota. "
                "Full survey remains available for the complete synthetic-research run."
            ),
        )
        st.divider()
        st.subheader("Research Guardrail")
        st.write("Directional early-stage research only. Final validation remains with Visa and real customer data.")

    render_model_and_delivery_proof(wx_status, provider, run_scope)
    render_partner_review_panel()
    research_brief = render_research_brief()
    render_calibration_preview()

    default_survey = """1. How relevant is this value proposition for your everyday payment or banking needs?
2. What annual fee or monthly price in CHF would feel acceptable, if any?
3. Which benefit, service or message feels most valuable to you, and why?
4. What is the main barrier or concern that would stop you from using it?"""
    survey_presets = load_survey_presets(default_survey)
    if "survey_text_value" not in st.session_state:
        st.session_state["survey_text_value"] = default_survey

    render_workflow_step(
        1,
        "Upload a survey file",
        "PDF is the recommended partner-review format. TXT, DOCX, CSV and XLSX also work.",
    )
    upload_col, sample_col = st.columns([0.62, 0.38], gap="large")
    with upload_col:
        uploaded_survey = st.file_uploader(
            "Upload PDF, DOCX, XLSX or text survey",
            type=supported_upload_types(),
            help="Upload a survey, interview guide or proposition test. The system extracts text before running the agents.",
            key="survey_file_upload",
        )
    with sample_col:
        st.markdown("**Need a realistic test file?**")
        st.caption("Use the public mobile-payments survey excerpt for a reviewer-friendly PDF upload test.")
        sample_pdf = PUBLIC_UPLOADS / "federal_reserve_mobile_payments_excerpt.pdf"
        if sample_pdf.exists():
            st.download_button(
                "Download sample PDF survey",
                data=sample_pdf.read_bytes(),
                file_name=sample_pdf.name,
                mime="application/pdf",
                width="stretch",
            )
        st.link_button("Open public source", FEDERAL_RESERVE_SURVEY_SOURCE, width="stretch")

    preset_name = "Core Visa synthetic survey"
    input_metadata: dict[str, object] = {
        "source": "preset",
        "file_name": preset_name,
        "file_type": "text",
        "char_count": len(st.session_state["survey_text_value"]),
        "extraction_notes": [f"Using app preset: {preset_name}."],
    }
    extracted_text: str | None = None
    if uploaded_survey is not None:
        try:
            extracted = extract_survey_text(uploaded_survey.name, uploaded_survey.getvalue())
            upload_key = f"{uploaded_survey.name}:{uploaded_survey.size}"
            if st.session_state.get("last_uploaded_survey_key") != upload_key:
                st.session_state["survey_text_value"] = extracted.text
                st.session_state["last_uploaded_survey_key"] = upload_key
            default_survey = st.session_state["survey_text_value"]
            extracted_text = extracted.text
            input_metadata = extracted.metadata()
            st.markdown(
                f"""
                <div class="upload-proof">
                  <strong>File loaded:</strong> {uploaded_survey.name}<br/>
                  <strong>Type:</strong> {extracted.file_type.upper()} &nbsp; 
                  <strong>Characters extracted:</strong> {extracted.char_count:,}<br/>
                  The extracted text is ready to review in Step 2.
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("View extraction audit and text preview", expanded=False):
                st.write("\n".join(f"- {note}" for note in extracted.extraction_notes))
                st.code(extracted.text[:2200], language="text")
        except SurveyExtractionError as exc:
            st.error(str(exc))
            input_metadata = {
                "source": "direct_text_after_failed_upload",
                "file_name": uploaded_survey.name,
                "file_type": uploaded_survey.name.rsplit(".", 1)[-1].lower(),
                "char_count": len(st.session_state["survey_text_value"]),
                "extraction_notes": [f"Upload extraction failed: {exc}"],
            }
    else:
        preset_name = st.selectbox(
            "Or start from an example survey",
            list(survey_presets.keys()),
            help="Use a public-example-inspired stress test, or paste your own survey in Step 2.",
            key="question_preset_select",
        )
        if st.session_state.get("last_question_preset") != preset_name:
            st.session_state["survey_text_value"] = survey_presets[preset_name]
            st.session_state["last_question_preset"] = preset_name
        default_survey = st.session_state["survey_text_value"]
        input_metadata = {
            "source": "preset",
            "file_name": preset_name,
            "file_type": "text",
            "char_count": len(default_survey),
            "extraction_notes": [f"Using app preset: {preset_name}."],
        }

    render_workflow_step(
        2,
        "Review or adjust questions",
        "The survey text below is what the parser agent receives. Reviewers can edit it before running.",
    )
    with st.form("research_form", border=False):
        left, right = st.columns([1.05, 0.95], gap="large")
        with left:
            raw_survey = st.text_area(
                "Survey text for the agents",
                key="survey_text_value",
                height=260,
                help="You can keep the extracted PDF text as-is or edit it before running the synthetic respondents.",
            )
            review_confirmed = st.checkbox(
                "I reviewed the extracted survey text and removed irrelevant pages, disclaimers or instructions.",
                value=True,
                help="This records a lightweight human review step before the agents run.",
            )
            input_metadata = {**input_metadata, "char_count": len(raw_survey)}
            input_metadata["human_review_confirmed"] = review_confirmed
            if extracted_text is not None:
                input_metadata["edited_after_extraction"] = raw_survey.strip() != extracted_text.strip()
                if input_metadata["edited_after_extraction"]:
                    input_metadata["source"] = "uploaded_file_edited_text"
            elif raw_survey.strip() != default_survey.strip():
                input_metadata["source"] = "edited_preset_or_direct_text"
                input_metadata["edited_after_extraction"] = True
            survey_to_run = scoped_survey_for_run(raw_survey, input_metadata, run_scope)
            st.markdown("#### Target Market")
            target_context = st.text_input(
                "Target market",
                value="Swiss consumers across age, income, household, language region and payment behavior segments",
                label_visibility="collapsed",
            )
        with right:
            render_workflow_step(
                3,
                "Define the value proposition",
                "Paste the client payment or banking value proposition that the synthetic customers should react to.",
            )
            st.markdown("#### Client Value Proposition")
            concepts = concept_editor(default_value_proposition(target_context), target_context)

        render_workflow_step(
            4,
            "Run and review results",
            "Launch the parser, persona respondent agents, aggregation and validation layers.",
        )
        submitted = st.form_submit_button("Run synthetic survey and generate insights", type="primary", width="stretch")

    if submitted:
        run_synthetic_survey(provider, survey_to_run, concepts, micro_n, consistency_runs, input_metadata, research_brief)

    run = st.session_state.get("last_run")
    if run:
        render_results(run)
    else:
        render_empty_state()


def render_research_brief() -> dict[str, str]:
    defaults = default_research_brief()
    st.markdown(
        """
        <div class="visa-shell">
          <div class="mini-label">Consulting setup</div>
          <div class="visa-title" style="font-size:24px;margin-bottom:8px;">Research Brief</div>
          <div class="visa-subtitle">
            Start with the business decision, not the model. These fields make the output read like a
            VCA decision brief and help reviewers see that the tool is built for consulting work, not
            free-form chatbot answers.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Edit research objective, hypotheses and decision rule", expanded=True):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            project_objective = st.text_area(
                "Project objective",
                value=defaults["project_objective"],
                height=96,
                help="What should this synthetic research run help the consultant learn?",
            )
            client_decision = st.text_area(
                "Client decision to support",
                value=defaults["client_decision"],
                height=96,
                help="Which decision should the partner/client make after reading the brief?",
            )
        with c2:
            hypotheses = st.text_area(
                "Hypotheses to test",
                value=defaults["hypotheses"],
                height=130,
                help="One hypothesis per line. The app will map the output back to these hypotheses.",
            )
            decision_rule = st.text_area(
                "Decision rule",
                value=defaults["decision_rule"],
                height=72,
                help="Define what would make a synthetic finding worth advancing to real validation.",
            )
        stakeholder_output = st.text_input(
            "Expected stakeholder output",
            value=defaults["stakeholder_output"],
            help="This is used in the downloadable decision brief.",
        )
    return {
        "project_objective": project_objective,
        "client_decision": client_decision,
        "hypotheses": hypotheses,
        "decision_rule": decision_rule,
        "stakeholder_output": stakeholder_output,
    }


def render_model_and_delivery_proof(wx_status: dict[str, object], provider: str, run_scope: str) -> None:
    if provider == "watsonx" and wx_status.get("configured"):
        model_class = "green"
        model_text = f"Real IBM watsonx.ai / Granite ready: {wx_status.get('model_id')}"
    elif provider == "watsonx":
        model_class = "amber"
        model_text = "watsonx selected but credentials are incomplete; add the missing values before final proof."
    else:
        model_class = "amber"
        model_text = "Deterministic mock fallback selected for rehearsal, CI or quota contingency."
    st.markdown(
        f"""
        <div class="proof-grid">
          <div class="proof-card {model_class}">
            <strong>1. Model Proof</strong>
            <span>{model_text}</span>
          </div>
          <div class="proof-card">
            <strong>2. Persona Agent Loop</strong>
            <span>Client proposition -> survey/interview artifact -> synthetic customers -> validation -> real research plan.</span>
          </div>
          <div class="proof-card">
            <strong>3. Run Scope</strong>
            <span>{run_scope}. This lets reviewers upload a full survey while controlling live-model quota.</span>
          </div>
          <div class="proof-card">
            <strong>4. Governance</strong>
            <span>Designed to move closer to customer intuition early; final decisions still require real validation.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_partner_review_panel() -> None:
    with st.expander("Partner review checklist and Slack-ready invitation", expanded=False):
        st.markdown("#### What Visa reviewers can test")
        st.write("- Upload a real survey, interview guide, or value proposition test as PDF/DOCX/XLSX/CSV/TXT.")
        st.write("- Replace the value proposition with one from a Visa/VCA engagement scenario.")
        st.write("- Run a quick watsonx proof first, then switch to full survey/96 respondents if quota allows.")
        st.write("- Inspect the Decision Brief, persona-level responses, validation checks, and PDF report export.")
        st.write("- Tell us where the output is useful or not useful for a VCA consultant workflow.")

        st.markdown("#### Suggested Slack message")
        st.code(build_partner_slack_message(), language="text")
        st.download_button(
            "Download Slack message draft",
            data=build_partner_slack_message().encode("utf-8"),
            file_name="visa_partner_review_slack_message.txt",
            mime="text/plain",
        )


def build_partner_slack_message() -> str:
    return f"""Hi Visa team,

We have a working prototype for the Visa use case: a VCA Multi-Agent Synthetic Researcher.

App link:
{LIVE_APP_URL}

What it does:
- Upload or paste a survey, interview guide, or value proposition test.
- Run Swiss synthetic customer persona agents using the IBM watsonx / Granite path.
- Review aggregated insights, persona-level responses, validation checks, and a downloadable PDF report.

If you have time, feel free to try it with any survey or value proposition input you think is realistic for VCA. We would especially appreciate feedback on:
- whether the input flow matches how a VCA consultant would actually test early product/value proposition ideas;
- whether the persona-level and aggregated outputs are the right level of detail;
- whether the validation checks are useful and credible enough;
- what you would remove, add, or change before the final presentation.

This is intended as directional early-stage research support, not a replacement for real customer validation.

Thank you very much!"""


def render_calibration_preview() -> None:
    snapshot = calibration_snapshot()
    with st.expander("Swiss synthetic customer panel calibration", expanded=False):
        st.caption(snapshot["interpretation"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Swiss archetypes", snapshot["archetype_count"])
        c2.metric("Synthetic panel size", snapshot["micro_population_count"])
        c3.metric("Public anchors", len(snapshot["public_anchors"]))

        tab_weights, tab_demographics, tab_payment, tab_sources = st.tabs(
            ["Persona weights", "Demographics", "Payment benchmarks", "Sources"]
        )
        with tab_weights:
            st.dataframe(pd.DataFrame(snapshot["persona_weights"]), width="stretch", hide_index=True)
        with tab_demographics:
            field = st.selectbox(
                "Calibration dimension",
                list(snapshot["demographic_distributions"].keys()),
                format_func=lambda value: value.replace("_", " ").title(),
            )
            distribution = pd.DataFrame(snapshot["demographic_distributions"][field])
            st.dataframe(distribution, width="stretch", hide_index=True)
            if not distribution.empty:
                st.bar_chart(distribution, x="segment", y="share_pct", color="#1434cb")
        with tab_payment:
            st.dataframe(pd.DataFrame(snapshot["payment_comparison"]), width="stretch", hide_index=True)
            st.caption("The synthetic panel is calibrated directionally. Visa internal benchmarks should override public anchors in production.")
        with tab_sources:
            source_rows = [
                {
                    "anchor": anchor.get("name"),
                    "value": anchor.get("value"),
                    "source": anchor.get("source"),
                    "url": anchor.get("url"),
                }
                for anchor in snapshot["public_anchors"]
            ]
            st.dataframe(pd.DataFrame(source_rows), width="stretch", hide_index=True)


@st.cache_data(show_spinner=False)
def calibration_snapshot() -> dict[str, object]:
    personas = load_personas(DATA / "swiss_archetypes.yaml")
    benchmark_data = load_benchmark_data(DATA / "benchmark_snb_2025.yaml")
    return build_panel_calibration(personas, benchmark_data, target_n=96)


def scoped_survey_for_run(raw_survey: str, metadata: dict[str, object], run_scope: str) -> str:
    scope_limits = {
        "Quick real-model proof (first 2 questions)": 2,
        "Focused consultant test (first 4 questions)": 4,
        "Full survey": None,
    }
    limit = scope_limits.get(run_scope)
    scoped = limit_survey_questions(raw_survey, limit)
    metadata["run_scope"] = run_scope
    metadata["question_limit"] = limit or "all"
    metadata["original_char_count"] = len(raw_survey)
    metadata["char_count"] = len(scoped)
    if scoped != raw_survey:
        notes = list(metadata.get("extraction_notes", []))
        notes.append(
            f"Run scope applied: first {limit} numbered questions were sent to the parser to conserve live-model quota."
        )
        metadata["extraction_notes"] = notes
        metadata["source"] = f"{metadata.get('source', 'survey')}_scoped"
    return scoped


def render_workflow_step(number: int, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="workflow-step">
          <div class="workflow-step-head">
            <span class="step-badge">{number}</span>
            <h2 class="workflow-step-title">{title}</h2>
          </div>
          <div class="workflow-step-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def default_value_proposition(target_context: str) -> Concept:
    return Concept(
        id="P1",
        name="Client value proposition",
        description=(
            "Paste the client proposition here. Include the customer promise, product or service context, "
            "pricing or fee if known, benefits to test, and any message or assumption the consultant wants "
            "synthetic Swiss customers to react to."
        ),
        annual_fee_chf=0.0,
        features=[
            "replace with the main customer benefit",
            "replace with a proof point or service feature",
            "replace with a message, risk or barrier to test",
        ],
        target_context=target_context or "Swiss consumer value proposition",
    )


def concept_editor(default: Concept, target_context: str) -> list[Concept]:
    name = st.text_input("Proposition name", value=default.name, key="name_primary")
    annual_fee = st.number_input(
        "Price or annual fee CHF",
        min_value=0,
        max_value=500,
        value=int(default.annual_fee_chf),
        step=5,
        help="Use 0 if no fee or price has been defined yet.",
        key="fee_primary",
    )
    description = st.text_area(
        "Proposition description",
        value=default.description,
        height=132,
        help="This is sent to each synthetic customer agent as the proposition context.",
        key="description_primary",
    )
    features_text = st.text_area(
        "Benefits, messages or assumptions to test",
        value="\n".join(default.features),
        height=118,
        help="One item per line. These can be benefits, claims, proof points or barriers to validate.",
        key="features_primary",
    )
    return [
        Concept(
            id="P1",
            name=name,
            description=description,
            annual_fee_chf=float(annual_fee),
            features=[line.strip() for line in features_text.splitlines() if line.strip()],
            target_context=target_context or default.target_context,
        )
    ]


def load_survey_presets(default_survey: str) -> dict[str, str]:
    presets = {"Core Visa synthetic survey": default_survey}
    if DEMO_SURVEYS.exists():
        label_map = {
            "concept_test_qualtrics_surveymonkey_style.txt": "External stress test: proposition testing",
            "payment_behavior_federal_reserve_style.txt": "External stress test: payment behavior",
            "pricing_message_value_proposition_test.txt": "External stress test: pricing and message",
        }
        for path in sorted(DEMO_SURVEYS.glob("*.txt")):
            label = label_map.get(path.name, f"External stress test: {path.stem.replace('_', ' ')}")
            presets[label] = path.read_text(encoding="utf-8")
    return presets


def run_synthetic_survey(
    provider: str,
    raw_survey: str,
    concepts: list[Concept],
    micro_n: int,
    consistency_runs: int,
    input_metadata: dict[str, object],
    research_brief: dict[str, str],
) -> None:
    try:
        with st.status("Running parser, persona agents, analytics and validation...", expanded=False):
            llm = get_llm(provider)
            orchestrator = SyntheticResearchOrchestrator(
                llm=llm,
                persona_path=DATA / "swiss_archetypes.yaml",
                benchmark_path=DATA / "benchmark_snb_2025.yaml",
            )
            st.write("Survey Parser Agent")
            st.write("Persona Respondent Agents")
            st.write("Insight Analyst and Validator")
            run = orchestrator.run(
                raw_survey=raw_survey,
                concepts=concepts,
                micro_population_n=micro_n,
                consistency_runs=consistency_runs,
                input_source=input_metadata,
            )
            run.aggregate["provider"] = provider
            run.aggregate["model_id"] = watsonx_config_status()["model_id"] if provider == "watsonx" else "MockLLM"
            run.aggregate["research_brief"] = research_brief
            run.aggregate["decision_brief"] = build_decision_brief(run, research_brief, provider=provider)
            st.session_state["last_run"] = run
            record_run_history(run)
    except LLMError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.exception(exc)


def record_run_history(run: SurveyRun) -> None:
    validation_score = run.validation.get("overall", {}).get("score")
    benchmark = run.validation.get("benchmark_alignment", {})
    history_entry = {
        "run_id": run.run_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "provider": run.aggregate.get("provider", "unknown"),
        "model": run.aggregate.get("model_id", "unknown"),
        "questions": len(run.questions),
        "responses": run.aggregate.get("response_count", len(run.responses)),
        "validation": validation_score,
        "benchmark_mae_pp": benchmark.get("primary_mae_percentage_points"),
        "source": run.aggregate.get("input_source", {}).get("file_name", "text input"),
    }
    history = [entry for entry in st.session_state.get("run_history", []) if entry.get("run_id") != run.run_id]
    st.session_state["run_history"] = [history_entry, *history][:6]


def render_empty_state() -> None:
    st.markdown("#### Operating Flow")
    c1, c2, c3, c4 = st.columns(4)
    card(c1, "1", "Parse", "Turn arbitrary survey text into structured questions.")
    card(c2, "2", "Simulate", "Run weighted Swiss persona agents independently.")
    card(c3, "3", "Aggregate", "Compare adoption, pricing, features and barriers.")
    card(c4, "4", "Validate", "Check benchmark alignment, coverage and consistency.")


def render_results(run: SurveyRun) -> None:
    st.success(f"Run complete: {run.run_id}")
    render_kpis(run)
    (
        decision_tab,
        summary_tab,
        questions_tab,
        segment_tab,
        persona_tab,
        validation_tab,
        partner_tab,
        scorecard_tab,
        architecture_tab,
    ) = st.tabs(
        [
            "Decision Brief",
            "Consultant Summary",
            "Question Parser",
            "Segment Explorer",
            "Persona Responses",
            "Validation",
            "Partner Review",
            "Scorecard",
            "Architecture",
        ]
    )
    with decision_tab:
        render_decision_brief(run)
    with summary_tab:
        render_summary(run)
    with questions_tab:
        render_question_parser(run)
    with segment_tab:
        render_segment_explorer(run)
    with persona_tab:
        render_persona_responses(run)
    with validation_tab:
        render_validation(run)
    with partner_tab:
        render_partner_review(run)
    with scorecard_tab:
        render_scorecard(run)
    with architecture_tab:
        render_architecture()


def render_kpis(run: SurveyRun) -> None:
    aggregate = run.aggregate
    validation = run.validation
    benchmark = validation["benchmark_alignment"]
    runtime = aggregate.get("runtime", {})
    concepts = aggregate.get("concept_summary", {})
    best_id = max(concepts, key=lambda k: concepts[k].get("adoption_index_0_100") or 0) if concepts else "-"
    best_score = concepts.get(best_id, {}).get("adoption_index_0_100", "-")
    c1, c2, c3, c4, c5 = st.columns(5)
    card(c1, "Proposition", str(best_id), f"Adoption index {best_score}/100.")
    card(c2, "Panel", str(aggregate.get("respondent_count", "-")), f"{aggregate.get('response_count', 0)} persona-question responses.")
    card(c3, "Validation", str(validation.get("overall", {}).get("score", "-")), "Weighted confidence scorecard.")
    card(c4, "Benchmark", str(benchmark.get("score", "-")), benchmark.get("primary_profile_label", "Public payment mix alignment."))
    card(c5, "Runtime", f"{runtime.get('elapsed_seconds', '-')}s", f"{runtime.get('questions_parsed', '-')} parsed questions.")


def render_decision_brief(run: SurveyRun) -> None:
    aggregate = run.aggregate
    research = aggregate.get("research_brief") or default_research_brief()
    decision = aggregate.get("decision_brief") or build_decision_brief(
        run,
        research,
        provider=str(aggregate.get("provider", "mock")),
    )
    st.markdown(
        f"""
        <div class="decision-callout">
          <div class="mini-label">Executive answer</div>
          <div class="decision-headline">{decision.get('decision_posture', 'Decision posture unavailable')}</div>
          <div class="decision-copy">{decision.get('executive_answer', 'No decision brief generated.')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proposition", decision.get("lead_concept_name") or decision.get("lead_concept_id") or "-")
    gap = decision.get("adoption_gap_vs_next")
    c2.metric("Survey evidence", f"{run.aggregate.get('response_count', 0)} responses", "persona-question records")
    c3.metric("Validation", decision.get("validation_score", "-"), decision.get("validation_band", ""))
    c4.metric("Evidence mode", str(aggregate.get("provider", "mock")), str(aggregate.get("model_id", "provider abstraction")))

    with st.expander("Research brief used for this run", expanded=True):
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.markdown("**Project objective**")
            st.write(research.get("project_objective", "n/a"))
            st.markdown("**Client decision**")
            st.write(research.get("client_decision", "n/a"))
        with r2:
            st.markdown("**Decision rule**")
            st.write(research.get("decision_rule", "n/a"))
            st.markdown("**Expected output**")
            st.write(research.get("stakeholder_output", "n/a"))

    st.markdown("#### Proposition Evidence Readout")
    matrix = pd.DataFrame(decision.get("concept_matrix", []))
    if not matrix.empty:
        display_cols = [
            "concept_id",
            "concept_name",
            "adoption_index",
            "mean_likert",
            "price_signal",
            "strongest_segments",
            "weakest_segments",
            "top_signals",
            "recommended_action",
        ]
        matrix = matrix.rename(
            columns={
                "concept_id": "proposition_id",
                "concept_name": "proposition_name",
            }
        )
        display_cols = [
            "proposition_id",
            "proposition_name",
            "adoption_index",
            "mean_likert",
            "price_signal",
            "strongest_segments",
            "weakest_segments",
            "top_signals",
            "recommended_action",
        ]
        st.dataframe(matrix[[col for col in display_cols if col in matrix.columns]], width="stretch", hide_index=True)
    else:
        st.info("No quantified relevance or adoption signal was parsed. Add a relevance, likelihood or appeal question if a numeric readout is needed.")

    s1, s2 = st.columns(2, gap="large")
    with s1:
        st.markdown("#### So What for VCA")
        for item in decision.get("so_what", []):
            st.write(f"- {item}")
    with s2:
        st.markdown("#### Recommended Real Research")
        for item in decision.get("recommended_real_research", []):
            st.write(f"- {item}")

    st.markdown("#### Hypothesis Readout")
    hypotheses = pd.DataFrame(decision.get("hypothesis_readout", []))
    if not hypotheses.empty:
        st.dataframe(hypotheses, width="stretch", hide_index=True)
    else:
        st.info("No hypotheses were provided.")

    lens = decision.get("synthetic_customer_lens", {})
    if lens:
        st.markdown("#### Customer Perspective Board")
        st.caption(lens.get("positioning", "Synthetic customers provide directional early-stage customer intuition."))
        st.markdown("**Value proposition questions this run can inform**")
        for item in lens.get("value_proposition_questions", []):
            st.write(f"- {item}")
        r1, r2, r3 = st.columns(3, gap="large")
        with r1:
            st.markdown("**Decision drivers**")
            drivers = pd.DataFrame(lens.get("decision_drivers", []))
            if not drivers.empty:
                st.dataframe(drivers, width="stretch", hide_index=True)
        with r2:
            st.markdown("**Time/cost advantage**")
            for _, item in (lens.get("time_cost_advantage") or {}).items():
                st.write(f"- {item}")
        with r3:
            st.markdown("**Real-customer bridge**")
            for item in lens.get("real_customer_bridge", []):
                st.write(f"- **{item.get('stage')}**: {item.get('purpose')}")

        board = pd.DataFrame(lens.get("synthetic_customer_board", []))
        if not board.empty:
            st.markdown("**Synthetic customer board**")
            st.dataframe(board, width="stretch", hide_index=True)

    quality = decision.get("consultant_quality_layer", {})
    if quality:
        st.markdown("#### Consultant Quality Layer")
        decision_risk = str(quality.get("decision_risk", "-"))
        lead_margin = str(quality.get("lead_margin_interpretation", "-"))
        risk_headline = decision_risk.split(":", 1)[0]
        lead_headline = "Tie" if "narrow" in lead_margin.lower() else ("Moderate" if "moderate" in lead_margin.lower() else "Clear")
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Evidence grade", quality.get("evidence_grade", "-"), f"{quality.get('evidence_score', '-')}/100")
        q2.metric("Decision risk", risk_headline)
        q3.metric("Lead margin", lead_headline)
        segment = quality.get("segment_differentiation", {})
        segment_interpretation = str(segment.get("interpretation", ""))
        segment_headline = "Low" if "low" in segment_interpretation.lower() else ("Moderate" if "moderate" in segment_interpretation.lower() else "Strong")
        q4.metric("Segment spread", segment.get("spread", "-"), segment_headline)
        st.caption(f"Decision interpretation: {decision_risk} {lead_margin} Segment read: {segment_interpretation}")

        r1, r2 = st.columns([0.48, 0.52], gap="large")
        with r1:
            st.markdown("**Evidence risks to mention**")
            for flag in quality.get("risk_flags", []):
                st.write(f"- **{flag.get('title')}** ({flag.get('severity')}): {flag.get('detail')}")
        with r2:
            st.markdown("**Top consultant actions**")
            for item in quality.get("top_consultant_actions", []):
                st.write(f"- {item}")

        repair = pd.DataFrame(quality.get("survey_repair_plan", []))
        if not repair.empty:
            st.markdown("**Survey repair plan for the next real customer test**")
            st.dataframe(repair, width="stretch", hide_index=True)

        with st.expander("Real-customer validation and calibration plan", expanded=False):
            for item in quality.get("recommended_validation_plan", []):
                st.write(f"- {item}")
            st.markdown("**Calibration thresholds**")
            for item in quality.get("calibration_thresholds", []):
                st.write(f"- {item}")

    st.markdown("#### Methodology and Model Transparency")
    for item in decision.get("methodology", methodology_snapshot(str(aggregate.get("provider", "mock")))):
        st.write(f"- {item}")

    with st.expander("Limitations and governance guardrails", expanded=True):
        for item in decision.get("limitations", []):
            st.write(f"- {item}")

    decision_report = format_decision_brief_markdown(run)
    pdf_report = build_consultant_pdf_report(run)
    pack = build_consultant_delivery_pack(run)
    d1, d2, d3 = st.columns([0.32, 0.34, 0.34])
    with d1:
        st.download_button(
            "Download Decision Brief",
            data=decision_report.encode("utf-8"),
            file_name=f"vca_decision_brief_{run.run_id}.md",
            mime="text/markdown",
        )
    with d2:
        st.download_button(
            "Download PDF Report",
            data=pdf_report,
            file_name=f"vca_synthetic_research_report_{run.run_id}.pdf",
            mime="application/pdf",
            help="Polished consultant-style PDF report generated from this run's synthetic responses, aggregation and validation evidence.",
        )
    with d3:
        st.download_button(
            "Download Consultant Delivery Pack",
            data=pack,
            file_name=f"vca_synthetic_research_delivery_pack_{run.run_id}.zip",
            mime="application/zip",
            help="ZIP with decision brief, consultant report, persona CSV, validation JSON, full run JSON, source audit and governance notes.",
        )


def render_summary(run: SurveyRun) -> None:
    aggregate = run.aggregate
    analyst = aggregate.get("analyst", {})
    st.markdown("#### Recommendation")
    st.write(analyst.get("recommendation", "No recommendation generated."))
    st.caption(analyst.get("why", ""))

    summary_df = pd.DataFrame([
        {
            "proposition": concept_id,
            "adoption_index": values.get("adoption_index_0_100"),
            "mean_likert": values.get("mean_likert"),
            "respondents": values.get("respondents"),
        }
        for concept_id, values in aggregate.get("concept_summary", {}).items()
    ])
    if not summary_df.empty:
        st.bar_chart(summary_df.set_index("proposition")["adoption_index"], color="#1434cb")
        st.dataframe(summary_df, width="stretch", hide_index=True)

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Pricing Signal")
        price_df = pd.DataFrame([
            {
                "proposition": concept_id,
                "mean_acceptable_fee_chf": values.get("weighted_mean_chf"),
                "min_chf": values.get("min_chf"),
                "max_chf": values.get("max_chf"),
            }
            for concept_id, values in aggregate.get("price_summary", {}).items()
        ])
        if price_df.empty:
            st.info("No price question detected.")
        else:
            st.dataframe(price_df, width="stretch", hide_index=True)
    with p2:
        st.markdown("#### Feature / Barrier Signals")
        labels = aggregate.get("top_answer_labels", [])
        label_df = pd.DataFrame(labels, columns=["signal", "count"]) if labels else pd.DataFrame()
        if label_df.empty:
            st.info("No labeled open-ended signal detected.")
        else:
            st.dataframe(label_df, width="stretch", hide_index=True)

    st.markdown("#### Consultant Next Test")
    for item in analyst.get("next_test", []):
        st.write(f"- {item}")

    st.markdown("#### Business Value Snapshot")
    runtime = aggregate.get("runtime", {})
    b1, b2, b3 = st.columns(3)
    b1.metric("Time to first synthetic insight", f"{runtime.get('elapsed_seconds', '-')}s", "Target < 2 min")
    b2.metric("Synthetic responses", aggregate.get("response_count", "-"), "Scales to 96 personas")
    b3.metric("JSON parse success", f"{runtime.get('json_parse_success_rate', '-')}%", "Target > 95%")

    report = build_markdown_report(run)
    st.download_button(
        "Download Markdown report",
        data=report.encode("utf-8"),
        file_name=f"visa_synthetic_report_{run.run_id}.md",
        mime="text/markdown",
    )
    st.download_button(
        "Download full run JSON",
        data=json.dumps(run.asdict(), indent=2).encode("utf-8"),
        file_name=f"visa_synthetic_run_{run.run_id}.json",
        mime="application/json",
    )


def render_question_parser(run: SurveyRun) -> None:
    input_source = run.aggregate.get("input_source", {})
    with st.expander("Input Source Audit", expanded=True):
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Source", input_source.get("source", "unknown"))
        s2.metric("File type", input_source.get("file_type", "text"))
        s3.metric("Run characters", input_source.get("char_count", 0))
        s4.metric("Edited after extraction", str(input_source.get("edited_after_extraction", False)))
        s5.metric("Run scope", input_source.get("question_limit", "all"))
        if input_source.get("original_char_count") and input_source.get("original_char_count") != input_source.get("char_count"):
            st.caption(f"Original extracted characters: {input_source.get('original_char_count')}")
        notes = input_source.get("extraction_notes", [])
        if notes:
            st.write("Extraction notes: " + " ".join(str(note) for note in notes))

    st.markdown("#### Parsed Survey Structure")
    st.caption("This is the live proof that the system is not limited to a fixed question set.")
    questions_df = pd.DataFrame([
        {
            "id": question.id,
            "type": question.type,
            "measures": question.measures,
            "question": question.text,
            "options": ", ".join(question.options),
        }
        for question in run.questions
    ])
    st.dataframe(questions_df, width="stretch", hide_index=True)

    st.markdown("#### Construct Coverage")
    coverage = run.validation.get("question_coverage", {})
    c1, c2 = st.columns([0.35, 0.65])
    c1.metric("Coverage score", coverage.get("score"))
    c2.write("Detected constructs: " + ", ".join(coverage.get("detected_constructs", [])))
    missing = coverage.get("missing_constructs", [])
    if missing:
        st.warning("Missing constructs for a richer value proposition test: " + ", ".join(missing))
    else:
        st.success("Survey covers adoption, pricing, feature preference and barriers.")


def render_segment_explorer(run: SurveyRun) -> None:
    rows = []
    for key, value in run.aggregate.get("segment_fit", {}).items():
        concept_id, segment = key.split(":", 1)
        rows.append({"proposition": concept_id, "segment": segment, "mean_likert": value})
    segment_df = pd.DataFrame(rows)
    if segment_df.empty:
        st.info("No Likert adoption question detected.")
        return
    pivot = segment_df.pivot(index="segment", columns="proposition", values="mean_likert").sort_index()
    st.dataframe(pivot, width="stretch")
    st.bar_chart(segment_df, x="segment", y="mean_likert", color="proposition")

    st.markdown("#### Sample Persona Quotes")
    quote_cols = st.columns(max(1, len(run.aggregate.get("sample_quotes", {}))))
    for idx, (concept_id, quotes) in enumerate(run.aggregate.get("sample_quotes", {}).items()):
        with quote_cols[idx % len(quote_cols)]:
            st.markdown(f"**Proposition {concept_id}**")
            for quote in quotes[:4]:
                st.write(f"- {quote}")


def render_persona_responses(run: SurveyRun) -> None:
    question_lookup = {q.id: q.text for q in run.questions}
    concept_lookup = {c.id: c.name for c in run.concepts}
    rows = []
    for response in run.responses:
        row = response.asdict()
        row["question"] = question_lookup.get(response.question_id, response.question_id)
        row["proposition"] = concept_lookup.get(response.concept_id, response.concept_id)
        row["archetype"] = response.persona_id.split("_")[0]
        rows.append(row)
    df = pd.DataFrame(rows)
    c1, c2, c3 = st.columns(3)
    concept_filter = c1.multiselect("Proposition", sorted(df["concept_id"].unique()), default=sorted(df["concept_id"].unique()))
    archetype_filter = c2.multiselect("Archetype", sorted(df["archetype"].unique()), default=sorted(df["archetype"].unique()))
    question_filter = c3.multiselect("Question", sorted(df["question_id"].unique()), default=sorted(df["question_id"].unique()))
    filtered = df[
        df["concept_id"].isin(concept_filter)
        & df["archetype"].isin(archetype_filter)
        & df["question_id"].isin(question_filter)
    ]
    st.dataframe(
        filtered[
            [
                "persona_id",
                "persona_name",
                "proposition",
                "question_id",
                "question",
                "answer_value",
                "answer_label",
                "answer_text",
                "rationale",
                "confidence",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
    st.download_button(
        "Download responses as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"visa_synthetic_responses_{run.run_id}.csv",
        mime="text/csv",
    )


def render_validation(run: SurveyRun) -> None:
    validation = run.validation
    c1, c2, c3, c4, c5 = st.columns(5)
    benchmark = validation["benchmark_alignment"]
    consistency = validation["internal_consistency"]
    coverage = validation["coverage"]
    question_coverage = validation["question_coverage"]
    realism = validation["realism_rubric"]
    c1.metric("Overall confidence", validation.get("overall", {}).get("score"), "weighted")
    c2.metric("Benchmark", benchmark.get("score"), status_text(benchmark.get("score")))
    c3.metric("Consistency", consistency.get("score"), f"avg std {consistency.get('avg_likert_std')}")
    c4.metric("Coverage", coverage.get("score"), f"{coverage.get('archetype_count')} archetypes")
    c5.metric("Realism rubric", realism.get("score"), f"{realism.get('flag_count')} flags")

    st.markdown("#### Benchmark Profiles")
    profile_rows = []
    for profile_id, profile in benchmark.get("profiles", {}).items():
        profile_rows.append({
            "profile": profile_id,
            "label": profile.get("label"),
            "score": profile.get("score"),
            "mae_pp": profile.get("mae_percentage_points"),
            "context": profile.get("context"),
            "source": profile.get("source"),
        })
    st.dataframe(pd.DataFrame(profile_rows), width="stretch", hide_index=True)

    mix = benchmark.get("synthetic_mix", {})
    if mix:
        mix_df = pd.DataFrame([{"method": k, "synthetic_share": v} for k, v in mix.items()])
        st.bar_chart(mix_df, x="method", y="synthetic_share", color="#1434cb")

    st.markdown("#### Judge-Style Realism Rubric")
    r1, r2 = st.columns([0.35, 0.65])
    r1.metric("Realism score", realism.get("score"), f"{realism.get('sampled_items')} responses checked")
    r2.write("Rubric checks: " + "; ".join(realism.get("rubric", [])))
    if realism.get("sample_flags"):
        st.dataframe(pd.DataFrame(realism["sample_flags"]), width="stretch", hide_index=True)
    else:
        st.success("No realism flags found in the primary synthetic run.")

    with st.expander("Raw validation JSON"):
        st.json(validation)


def render_partner_review(run: SurveyRun) -> None:
    st.markdown("#### Partner Review Pack")
    st.write(
        "Use this tab when sharing the prototype with Visa. It keeps the ask focused on product fit, "
        "output usefulness, and validation credibility rather than asking them to inspect implementation details."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current run", run.run_id)
    c2.metric("Provider", run.aggregate.get("provider", "unknown"))
    c3.metric("Responses", run.aggregate.get("response_count", len(run.responses)))
    c4.metric("Validation", run.validation.get("overall", {}).get("score", "-"))

    st.markdown("#### Suggested Feedback Questions")
    feedback_rows = [
        {
            "area": "Input workflow",
            "question": "Would a VCA consultant naturally start with this survey/interview/proposition input flow?",
        },
        {
            "area": "Synthetic customer output",
            "question": "Are persona-level responses and segment summaries detailed enough to be useful?",
        },
        {
            "area": "Consultant insight",
            "question": "Does the Decision Brief help decide what to validate with real customers next?",
        },
        {
            "area": "Validation",
            "question": "Are benchmark, consistency, coverage and realism checks credible enough for early-stage use?",
        },
        {
            "area": "Scope",
            "question": "What should be removed because it is not needed by Visa/VCA?",
        },
    ]
    st.dataframe(pd.DataFrame(feedback_rows), width="stretch", hide_index=True)

    st.markdown("#### Slack Message")
    st.code(build_partner_slack_message(), language="text")
    st.download_button(
        "Download Slack message draft",
        data=build_partner_slack_message().encode("utf-8"),
        file_name="visa_partner_review_slack_message.txt",
        mime="text/plain",
        key="download_partner_slack_message_after_run",
    )

    history = st.session_state.get("run_history", [])
    if history:
        st.markdown("#### This-session run history")
        st.dataframe(pd.DataFrame(history), width="stretch", hide_index=True)
        st.caption("Session history is intentionally lightweight. Production use should persist run history with access control and data-retention rules.")


def render_scorecard(run: SurveyRun) -> None:
    readiness = build_pilot_readiness_gate(run)
    status_counts = readiness_status_counts(readiness)
    st.markdown("#### Pilot Readiness Gate")
    r1, r2, r3 = st.columns(3)
    r1.metric("Ready checks", status_counts.get("Ready", 0), "Partner-facing evidence")
    r2.metric("Needs attention", status_counts.get("Needs attention", 0), "Resolve before final sign-off")
    provider = str(run.aggregate.get("provider", "mock"))
    provider_label = "Real IBM watsonx.ai" if provider == "watsonx" else "Fallback MockLLM"
    r3.metric("Evidence mode", provider_label, str(run.aggregate.get("model_id", "n/a")))
    st.dataframe(pd.DataFrame(readiness), width="stretch", hide_index=True)

    st.markdown("#### Final Evaluation Scorecard")
    runtime = run.aggregate.get("runtime", {})
    validation = run.validation
    rows = [
        {
            "rubric area": "Live product proof (5)",
            "evidence in product": "Running Streamlit app: paste survey -> run persona agents -> aggregate -> validate -> export.",
            "status": "Ready",
        },
        {
            "rubric area": "Architecture (3)",
            "evidence in product": "Architecture tab and docs show UI, parser, persona store, orchestrator, respondent agents, validator, analytics/export.",
            "status": "Ready",
        },
        {
            "rubric area": "KPIs (2)",
            "evidence in product": f"{runtime.get('elapsed_seconds', '-')}s time-to-insight, {run.aggregate.get('response_count', '-')} responses, {validation['internal_consistency'].get('avg_likert_std')} Likert std, {validation['benchmark_alignment'].get('primary_mae_percentage_points')}pp benchmark MAE.",
            "status": "Ready",
        },
        {
            "rubric area": "Business value (2)",
            "evidence in product": "Positions synthetic output as early proposition screening and survey design acceleration, not final customer truth.",
            "status": "Ready",
        },
        {
            "rubric area": "Next steps (2)",
            "evidence in product": "Consultant next-test recommendations, downloadable delivery pack, and docs roadmap: watsonx Orchestrate, calibration, PPT export, Visa internal validation.",
            "status": "Ready",
        },
        {
            "rubric area": "Presentation quality (3)",
            "evidence in product": "Visa-style cockpit, presenter runbook, source notes, validation guardrails and traceable persona response table.",
            "status": "Ready",
        },
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.markdown("#### Talk Track Anchor")
    st.info(
        "We do not claim to replace real customers. We give VCA consultants a fast, transparent, "
        "benchmark-grounded synthetic research layer to stress-test early propositions, identify weak "
        "assumptions and design better real customer research."
    )


def render_architecture() -> None:
    st.markdown("#### Architecture")
    st.code(
        """
UI (Streamlit consultant cockpit)
  -> Survey Parser Agent
  -> Persona Builder / Weighted Micro-Population
  -> Persona Respondent Agents
  -> Analytics Aggregator
  -> Benchmark / Consistency / Coverage Validator
  -> VCA Decision Brief / Consultant Delivery Pack
        """.strip(),
        language="text",
    )
    st.markdown("#### Data Grounding")
    st.write(
        "Personas are grounded in public Swiss demographic and payment behavior anchors from FSO/BFS, "
        "Swiss Payment Monitor, and the SNB Payment Methods Survey. No Visa internal or client-sensitive data is used."
    )
    st.markdown("#### Model and Algorithm Stack")
    st.write("- Real-model path: IBM watsonx.ai through `ibm-watsonx-ai` `ModelInference`, default `ibm/granite-4-h-small` in `eu-de`.")
    st.write("- Fallback path: deterministic `MockLLM` for CI, rehearsal and classroom quota contingency only.")
    st.write("- Algorithms: PDF/DOCX/XLSX/CSV/TXT extraction, survey parsing, weighted Swiss micro-persona sampling, persona-conditioned agent responses, weighted analytics, benchmark/consistency/coverage/realism validation and VCA decision synthesis.")
    st.write("- PDF report and delivery pack: polished PDF report plus ZIP export with decision brief, consultant report, persona CSV, validation JSON, full run JSON, input audit and governance notes.")
    st.markdown("#### KPIs")
    st.write("- Time to first synthetic insight: target under 2 minutes for quick real-model proof or full mock rehearsal.")
    st.write("- Synthetic responses per run: up to 96 personas across uploaded survey/interview questions and the client value proposition.")
    st.write("- JSON parse success rate: target above 95 percent with watsonx structured prompts.")
    st.write("- Internal consistency: repeated-run Likert standard deviation target below 0.5.")
    st.write("- Benchmark alignment: payment-method mix MAE target below 10 percentage points.")
    st.write("- Realism rubric: response/persona alignment score target above 85.")


def card(column, label: str, value: str, caption: str) -> None:
    column.markdown(
        f"""
        <div class="metric-card">
          <div class="mini-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_text(score: float | None) -> str:
    if score is None:
        return "not available"
    if score >= 85:
        return "green"
    if score >= 70:
        return "amber"
    return "red"


if __name__ == "__main__":
    main()
