from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from synthetic_researcher.llm import LLMError, get_llm
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator, load_concepts
from synthetic_researcher.reporting import build_markdown_report
from synthetic_researcher.schemas import Concept, SurveyRun

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


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
              <h1 class="visa-title">Synthetic Research Copilot</h1>
              <div class="visa-subtitle">
                Multi-agent Swiss persona simulation for early-stage card value proposition research.
                Paste a survey, tune concepts, run synthetic respondents, then review persona-level
                answers, aggregate insights and validation checks.
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
        provider = st.selectbox("Model provider", ["mock", "watsonx"], index=0)
        micro_n = st.slider("Synthetic respondents", min_value=12, max_value=96, value=48, step=12)
        consistency_runs = st.slider("Repeated consistency runs", min_value=1, max_value=3, value=2, step=1)
        st.divider()
        st.subheader("Demo Guardrail")
        st.write("Directional early-stage research only. Final validation remains with Visa and real customer data.")

    with st.form("research_form", border=False):
        left, right = st.columns([1.05, 0.95], gap="large")
        with left:
            st.markdown("#### Survey / Interview Input")
            raw_survey = st.text_area(
                "Paste survey questions",
                value="""1. How likely would you be to adopt this card if it were offered by your bank?
2. What annual fee in CHF would feel acceptable for this card?
3. Which benefit or feature feels most valuable to you, and why?
4. What is the main barrier that would prevent you from using this card?""",
                height=224,
                label_visibility="collapsed",
            )
            st.markdown("#### Target Market")
            target_context = st.text_input(
                "Target market",
                value="Swiss consumers across age, income, household, language region and payment behavior segments",
                label_visibility="collapsed",
            )
        with right:
            st.markdown("#### Product Concepts")
            concepts = concept_editor(defaults, target_context)

        submitted = st.form_submit_button("Run synthetic survey", type="primary", use_container_width=True)

    if submitted:
        run_synthetic_survey(provider, raw_survey, concepts, micro_n, consistency_runs)

    run = st.session_state.get("last_run")
    if run:
        render_results(run)
    else:
        render_empty_state()


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


def run_synthetic_survey(
    provider: str,
    raw_survey: str,
    concepts: list[Concept],
    micro_n: int,
    consistency_runs: int,
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
            st.session_state["last_run"] = orchestrator.run(
                raw_survey=raw_survey,
                concepts=concepts,
                micro_population_n=micro_n,
                consistency_runs=consistency_runs,
            )
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
    summary_tab, segment_tab, persona_tab, validation_tab, architecture_tab = st.tabs(
        ["Consultant Summary", "Segment Explorer", "Persona Responses", "Validation", "Architecture"]
    )
    with summary_tab:
        render_summary(run)
    with segment_tab:
        render_segment_explorer(run)
    with persona_tab:
        render_persona_responses(run)
    with validation_tab:
        render_validation(run)
    with architecture_tab:
        render_architecture()


def render_kpis(run: SurveyRun) -> None:
    aggregate = run.aggregate
    benchmark = run.validation["benchmark_alignment"]
    concepts = aggregate.get("concept_summary", {})
    best_id = max(concepts, key=lambda k: concepts[k].get("adoption_index_0_100") or 0) if concepts else "-"
    best_score = concepts.get(best_id, {}).get("adoption_index_0_100", "-")
    c1, c2, c3, c4 = st.columns(4)
    card(c1, "Lead concept", str(best_id), f"Adoption index {best_score}/100.")
    card(c2, "Panel", str(aggregate.get("respondent_count", "-")), f"{aggregate.get('response_count', 0)} persona-question responses.")
    card(c3, "Confidence", str(aggregate.get("avg_confidence", "-")), "Mean response confidence from respondent agents.")
    card(c4, "Benchmark", str(benchmark.get("score", "-")), benchmark.get("primary_profile_label", "Public payment mix alignment."))


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
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

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
            st.dataframe(price_df, use_container_width=True, hide_index=True)
    with p2:
        st.markdown("#### Feature / Barrier Signals")
        labels = aggregate.get("top_answer_labels", [])
        label_df = pd.DataFrame(labels, columns=["signal", "count"]) if labels else pd.DataFrame()
        if label_df.empty:
            st.info("No labeled open-ended signal detected.")
        else:
            st.dataframe(label_df, use_container_width=True, hide_index=True)

    st.markdown("#### Consultant Next Test")
    for item in analyst.get("next_test", []):
        st.write(f"- {item}")

    report = build_markdown_report(run)
    st.download_button(
        "Download Markdown report",
        data=report.encode("utf-8"),
        file_name=f"visa_synthetic_report_{run.run_id}.md",
        mime="text/markdown",
    )


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
    st.dataframe(pivot.style.background_gradient(cmap="Blues", axis=None), use_container_width=True)
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
        use_container_width=True,
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
    c1, c2, c3 = st.columns(3)
    benchmark = validation["benchmark_alignment"]
    consistency = validation["internal_consistency"]
    coverage = validation["coverage"]
    c1.metric("Benchmark alignment", benchmark.get("score"), status_text(benchmark.get("score")))
    c2.metric("Internal consistency", consistency.get("score"), f"avg std {consistency.get('avg_likert_std')}")
    c3.metric("Persona coverage", coverage.get("score"), f"{coverage.get('archetype_count')} archetypes")

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
    st.dataframe(pd.DataFrame(profile_rows), use_container_width=True, hide_index=True)

    mix = benchmark.get("synthetic_mix", {})
    if mix:
        mix_df = pd.DataFrame([{"method": k, "synthetic_share": v} for k, v in mix.items()])
        st.bar_chart(mix_df, x="method", y="synthetic_share", color="#1434cb")

    with st.expander("Raw validation JSON"):
        st.json(validation)


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
  -> Consultant Report Export
        """.strip(),
        language="text",
    )
    st.markdown("#### Data Grounding")
    st.write(
        "Personas are grounded in public Swiss demographic and payment behavior anchors from FSO/BFS, "
        "Swiss Payment Monitor, and the SNB Payment Methods Survey. No Visa internal or client-sensitive data is used."
    )
    st.markdown("#### KPIs")
    st.write("- Time to first synthetic insight: target under 2 minutes in mock mode.")
    st.write("- Synthetic responses per run: up to 96 personas across all questions and concepts.")
    st.write("- JSON parse success rate: target above 95 percent with watsonx structured prompts.")
    st.write("- Internal consistency: repeated-run Likert standard deviation target below 0.5.")
    st.write("- Benchmark alignment: payment-method mix MAE target below 10 percentage points.")


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
