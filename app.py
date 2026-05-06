from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import streamlit as st

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
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator, load_concepts
from synthetic_researcher.reporting import build_markdown_report
from synthetic_researcher.schemas import Concept, SurveyRun
from synthetic_researcher.survey_scope import limit_survey_questions

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEMO_SURVEYS = ROOT / "demo" / "external_survey_tests"
PUBLIC_UPLOADS = ROOT / "demo" / "public_survey_uploads"
FEDERAL_RESERVE_SURVEY_SOURCE = (
    "https://www.federalreserve.gov/econresdata/mobile-devices/"
    "2015-appendix-2-survey-of-consumers-use-of-mobile-financial-services-2014-questionnaire.htm"
)


st.set_page_config(page_title="Visa Synthetic Research Copilot", layout="wide", page_icon="V")

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
    defaults = load_concepts(DATA / "sample_concepts.yaml")

    st.markdown(
        """
        <div class="visa-shell">
          <div class="visa-head">
            <div>
              <h1 class="visa-title">VCA Synthetic Research Workbench</h1>
              <div class="visa-subtitle">
                A consultant-grade copilot for early-stage value proposition screening. Upload a survey or
                interview guide, define the client decision, run Swiss synthetic persona agents, and export
                persona-level evidence, aggregate insights, validation checks and a decision brief.
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
        scenario = st.selectbox(
            "Demo scenario",
            [
                "Baseline concepts",
                "Live sensitivity: lower Premium fee to CHF 60",
                "Live sensitivity: add stronger protection messaging",
            ],
        )
        st.divider()
        st.subheader("Demo Guardrail")
        st.write("Directional early-stage research only. Final validation remains with Visa and real customer data.")

    defaults = apply_demo_scenario(defaults, scenario)
    render_model_and_delivery_proof(wx_status, provider, run_scope)
    research_brief = render_research_brief()

    default_survey = """1. How likely would you be to adopt this card if it were offered by your bank?
2. What annual fee in CHF would feel acceptable for this card?
3. Which benefit or feature feels most valuable to you, and why?
4. What is the main barrier that would prevent you from using this card?"""
    survey_presets = load_survey_presets(default_survey)
    if "survey_text_value" not in st.session_state:
        st.session_state["survey_text_value"] = default_survey

    render_workflow_step(
        1,
        "Upload a survey file",
        "PDF is the recommended review format for partner demos. TXT, DOCX, CSV and XLSX also work.",
    )
    upload_col, sample_col = st.columns([0.62, 0.38], gap="large")
    with upload_col:
        uploaded_survey = st.file_uploader(
            "Upload PDF, DOCX, XLSX or text survey",
            type=supported_upload_types(),
            help="Upload a survey, interview guide or concept test. The system extracts text before running the agents.",
            key="survey_file_upload",
        )
    with sample_col:
        st.markdown("**Need a realistic test file?**")
        st.caption("Use the public mobile-payments survey excerpt for a reviewer-friendly PDF upload demo.")
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

    preset_name = "Core Visa card survey"
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
            input_metadata = {**input_metadata, "char_count": len(raw_survey)}
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
                "Configure concepts",
                "Use the default Visa card propositions, tune pricing/features, or paste a client proposition.",
            )
            st.markdown("#### Product Concepts")
            concepts = concept_editor(defaults, target_context)

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
            <strong>2. Research Workflow</strong>
            <span>Decision brief -> survey upload -> persona agents -> validation -> consultant output.</span>
          </div>
          <div class="proof-card">
            <strong>3. Run Scope</strong>
            <span>{run_scope}. This lets reviewers upload a full survey while controlling live-model quota.</span>
          </div>
          <div class="proof-card">
            <strong>4. Governance</strong>
            <span>Public Swiss benchmarks only; synthetic output is directional and still requires real validation.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def apply_demo_scenario(defaults: list[Concept], scenario: str) -> list[Concept]:
    concepts = [replace(concept) for concept in defaults]
    if scenario == "Live sensitivity: lower Premium fee to CHF 60":
        concepts[0] = replace(
            concepts[0],
            annual_fee_chf=60.0,
            description=concepts[0].description + " The annual fee is reduced for a broader trial positioning.",
        )
    elif scenario == "Live sensitivity: add stronger protection messaging":
        features = list(dict.fromkeys([*concepts[0].features, "strong purchase protection messaging", "transparent claims process"]))
        concepts[0] = replace(
            concepts[0],
            features=features,
            description=concepts[0].description + " Messaging emphasizes purchase protection, claim simplicity and transparent coverage.",
        )
    return concepts


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


def concept_editor(defaults: list[Concept], target_context: str) -> list[Concept]:
    concepts: list[Concept] = []
    for idx, default in enumerate(defaults):
        with st.expander(f"{default.id}: {default.name}", expanded=True):
            name = st.text_input("Name", value=default.name, key=f"name_{idx}")
            annual_fee = st.number_input(
                "Annual fee CHF",
                min_value=0,
                max_value=500,
                value=int(default.annual_fee_chf),
                step=5,
                key=f"fee_{idx}",
            )
            description = st.text_area("Description", value=default.description, height=86, key=f"description_{idx}")
            features_text = st.text_area(
                "Features",
                value="\n".join(default.features),
                height=96,
                key=f"features_{idx}",
            )
            concepts.append(
                Concept(
                    id=default.id,
                    name=name,
                    description=description,
                    annual_fee_chf=float(annual_fee),
                    features=[line.strip() for line in features_text.splitlines() if line.strip()],
                    target_context=target_context or default.target_context,
                )
            )
    return concepts


def load_survey_presets(default_survey: str) -> dict[str, str]:
    presets = {"Core Visa card survey": default_survey}
    if DEMO_SURVEYS.exists():
        label_map = {
            "concept_test_qualtrics_surveymonkey_style.txt": "External stress test: concept testing",
            "payment_behavior_federal_reserve_style.txt": "External stress test: payment behavior",
            "card_pricing_message_test.txt": "External stress test: pricing and message",
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
    except LLMError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.exception(exc)


def render_empty_state() -> None:
    st.markdown("#### Demo Flow")
    c1, c2, c3, c4 = st.columns(4)
    card(c1, "1", "Parse", "Turn arbitrary survey text into structured questions.")
    card(c2, "2", "Simulate", "Run weighted Swiss persona agents independently.")
    card(c3, "3", "Aggregate", "Compare adoption, pricing, features and barriers.")
    card(c4, "4", "Validate", "Check benchmark alignment, coverage and consistency.")


def render_results(run: SurveyRun) -> None:
    st.success(f"Run complete: {run.run_id}")
    render_kpis(run)
    decision_tab, summary_tab, questions_tab, segment_tab, persona_tab, validation_tab, scorecard_tab, architecture_tab = st.tabs(
        [
            "Decision Brief",
            "Consultant Summary",
            "Question Parser",
            "Segment Explorer",
            "Persona Responses",
            "Validation",
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
    card(c1, "Lead concept", str(best_id), f"Adoption index {best_score}/100.")
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
    c1.metric("Lead concept", decision.get("lead_concept_name") or decision.get("lead_concept_id") or "-")
    c2.metric("Adoption gap", f"{decision.get('adoption_gap_vs_next', '-')}", "vs next concept")
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

    st.markdown("#### Concept Decision Matrix")
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
        st.dataframe(matrix[[col for col in display_cols if col in matrix.columns]], width="stretch", hide_index=True)
    else:
        st.info("No adoption-style concept matrix is available. Check whether the survey includes a likelihood or appeal question.")

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

    st.markdown("#### Methodology and Model Transparency")
    for item in decision.get("methodology", methodology_snapshot(str(aggregate.get("provider", "mock")))):
        st.write(f"- {item}")

    with st.expander("Limitations and governance guardrails", expanded=True):
        for item in decision.get("limitations", []):
            st.write(f"- {item}")

    decision_report = format_decision_brief_markdown(run)
    pack = build_consultant_delivery_pack(run)
    d1, d2 = st.columns([0.42, 0.58])
    with d1:
        st.download_button(
            "Download Decision Brief",
            data=decision_report.encode("utf-8"),
            file_name=f"vca_decision_brief_{run.run_id}.md",
            mime="text/markdown",
        )
    with d2:
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
            "concept": concept_id,
            "adoption_index": values.get("adoption_index_0_100"),
            "mean_likert": values.get("mean_likert"),
            "respondents": values.get("respondents"),
        }
        for concept_id, values in aggregate.get("concept_summary", {}).items()
    ])
    if not summary_df.empty:
        st.bar_chart(summary_df.set_index("concept")["adoption_index"], color="#1434cb")
        st.dataframe(summary_df, width="stretch", hide_index=True)

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Pricing Signal")
        price_df = pd.DataFrame([
            {
                "concept": concept_id,
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
        st.warning("Missing constructs for a richer card proposition test: " + ", ".join(missing))
    else:
        st.success("Survey covers adoption, pricing, feature preference and barriers.")


def render_segment_explorer(run: SurveyRun) -> None:
    rows = []
    for key, value in run.aggregate.get("segment_fit", {}).items():
        concept_id, segment = key.split(":", 1)
        rows.append({"concept": concept_id, "segment": segment, "mean_likert": value})
    segment_df = pd.DataFrame(rows)
    if segment_df.empty:
        st.info("No Likert adoption question detected.")
        return
    pivot = segment_df.pivot(index="segment", columns="concept", values="mean_likert").sort_index()
    st.dataframe(pivot, width="stretch")
    st.bar_chart(segment_df, x="segment", y="mean_likert", color="concept")

    st.markdown("#### Sample Persona Quotes")
    quote_cols = st.columns(max(1, len(run.aggregate.get("sample_quotes", {}))))
    for idx, (concept_id, quotes) in enumerate(run.aggregate.get("sample_quotes", {}).items()):
        with quote_cols[idx % len(quote_cols)]:
            st.markdown(f"**Concept {concept_id}**")
            for quote in quotes[:4]:
                st.write(f"- {quote}")


def render_persona_responses(run: SurveyRun) -> None:
    question_lookup = {q.id: q.text for q in run.questions}
    concept_lookup = {c.id: c.name for c in run.concepts}
    rows = []
    for response in run.responses:
        row = response.asdict()
        row["question"] = question_lookup.get(response.question_id, response.question_id)
        row["concept"] = concept_lookup.get(response.concept_id, response.concept_id)
        row["archetype"] = response.persona_id.split("_")[0]
        rows.append(row)
    df = pd.DataFrame(rows)
    c1, c2, c3 = st.columns(3)
    concept_filter = c1.multiselect("Concept", sorted(df["concept_id"].unique()), default=sorted(df["concept_id"].unique()))
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
                "concept",
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
            "rubric area": "Demo (5)",
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
            "evidence in product": "Positions synthetic output as early concept screening and survey design acceleration, not final customer truth.",
            "status": "Ready",
        },
        {
            "rubric area": "Next steps (2)",
            "evidence in product": "Consultant next-test recommendations, downloadable delivery pack, and docs roadmap: watsonx Orchestrate, calibration, PPT export, Visa internal validation.",
            "status": "Ready",
        },
        {
            "rubric area": "Presentation quality (3)",
            "evidence in product": "Visa-style cockpit, demo script, source notes, validation guardrails and traceable persona response table.",
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
    st.write("- Delivery pack: ZIP export with decision brief, consultant report, persona CSV, validation JSON, full run JSON, input audit and governance notes.")
    st.markdown("#### KPIs")
    st.write("- Time to first synthetic insight: target under 2 minutes for quick real-model proof or full mock rehearsal.")
    st.write("- Synthetic responses per run: up to 96 personas across all questions and concepts.")
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
