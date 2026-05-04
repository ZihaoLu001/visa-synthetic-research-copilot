# Visa Synthetic Research Copilot

Running PoC for the IBM watsonx / Visa Consulting & Analytics **Multi-Agent Synthetic Researcher** case study.

The app accepts flexible survey, interview, or card value proposition test questions, runs a panel of public-data-grounded Swiss synthetic consumer personas, and returns:

- persona-level survey responses
- aggregated adoption, pricing, feature, and barrier signals
- segment-level fit by Swiss persona archetype
- benchmark alignment, internal consistency, and coverage checks
- judge-style realism rubric and overall validation confidence
- file ingestion audit for pasted text, TXT, MD, PDF, DOCX, CSV, and XLSX survey inputs
- downloadable CSV responses, Markdown consultant report, and full run JSON

This is an early-stage hypothesis and survey-design tool. It does **not** claim to replace real customer research or Visa's final validation.

## Why this matches the Visa brief

The kickoff deck asks for three layers:

1. **Persona design**: Swiss personas grounded in public demographic and payment behavior anchors.
2. **Multi-agent layer**: one respondent agent per persona, orchestrated across survey questions and card concepts.
3. **Validation & insight**: aggregated consultant output plus individual responses, with benchmark and consistency checks.

This repo implements that flow in a small, demo-friendly Streamlit application with a deterministic mock provider and optional watsonx.ai provider.

## Final Presentation Slot

Team 1 / Group 28 presents the Visa use case on **26 May 2026, 19:15-19:40** in **IBM Zurich Room 04404**. The final talk is 20 minutes plus 5 minutes partner feedback.

## Quick Start

```powershell
cd visa-synthetic-research-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_cli.py
streamlit run app.py
```

Optional API mode for IBM Code Engine or watsonx Orchestrate tool integration:

```powershell
uvicorn api:app --host 0.0.0.0 --port 8080
```

For macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_cli.py
streamlit run app.py
```

## Optional IBM Code Engine Deployment

The course labs highlight Code Engine as a lightweight stakeholder demo path. The recommended deployment path is browser-first: create a Code Engine application from the GitHub repository, use the included `Dockerfile`, set port `8080`, and set `APP_MODE=streamlit`. Local Docker and IBM Cloud CLI commands are optional; see `docs/code_engine_deployment.md`.

## Optional IBM watsonx.ai Setup

Copy `.env.example` to `.env` and set:

```bash
MODEL_PROVIDER=watsonx
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=...
WATSONX_APIKEY=...
WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
```

Keep `MODEL_PROVIDER=mock` available as the fallback for rehearsal and live demo reliability.

## Demo Flow

1. Paste a survey/interview guide or upload a TXT, MD, PDF, DOCX, CSV, or XLSX research file.
2. Tune the two default card concepts and fees.
3. Run 48 or 96 synthetic respondents.
4. Review adoption index, acceptable fee, feature and barrier signals.
5. Open the Question Parser tab to prove the survey is not hardcoded and inspect the input extraction audit.
6. Open segment and persona-level tables for traceability.
7. Open Validation and Scorecard for benchmark, consistency, coverage, realism and KPI evidence.
8. Download CSV, Markdown, or JSON outputs for partner review.
9. Change a fee or feature live, rerun, and compare the directional movement.

Suggested live stress test:

```text
Would you trust a card that automatically suggests the cheapest payment method at checkout?
What annual fee in CHF would you consider acceptable?
Which benefit would make you switch from your current card?
What is the main barrier that would stop you?
```

## Project Structure

```text
app.py                         Streamlit consultant cockpit
api.py                         FastAPI integration endpoint for Code Engine / Orchestrate
run_cli.py                     Offline CLI smoke demo
data/
  swiss_archetypes.yaml        Swiss synthetic persona archetypes
  benchmark_snb_2025.yaml      Public benchmark anchors and validation profiles
  sample_concepts.yaml         Card propositions for the demo
  sample_survey_card.yaml      Sample survey
synthetic_researcher/
  agents.py                    Survey parser, persona respondent, analyst
  analytics.py                 Aggregation and scoring
  ingestion.py                 TXT/MD/PDF/DOCX/CSV/XLSX survey extraction
  llm.py                       Mock + IBM watsonx providers
  orchestrator.py              End-to-end multi-agent run
  reporting.py                 Markdown consultant report
  sampler.py                   Weighted micro-population expansion
  schemas.py                   Typed dataclasses
  validation.py                Benchmark, consistency, coverage checks
tests/
  test_offline_run.py          Mock-mode regression tests
orchestrate/
  agents/                      Minimal watsonx Orchestrate ADK agent specification
  openapi/                     OpenAPI contract for importing the API as a tool
scripts/
  deploy_code_engine.ps1       IBM Code Engine deployment helper
docs/
  architecture.md              System design and extension notes
  demo_script.md               6-7 minute demo script
  code_engine_deployment.md     Optional IBM Code Engine deployment path
  evaluation_scorecard.md      Mapping to final presentation grading criteria
  final_delivery_runbook.md     Group 28 final delivery checklist
  final_presentation_plan.md   20-minute presentation structure
  partner_questions.md          Slack/Q&A messages for IBM and Visa alignment
  requirement_traceability.md  Email/lab/rubric/Visa requirement checklist
  research_notes.md            Framework and synthetic survey research notes
  sources.md                   Public data sources
```

## Full-Mark Scorecard Targets

- Running demo: paste survey -> parse -> simulate -> aggregate -> validate -> export.
- Flexible input demo: uploaded marketing research survey files can be converted to survey text before parsing.
- Architecture: UI, parser, persona store, orchestrator, respondent agents, validator, analytics/export.
- KPIs: time to insight, response count, JSON parse success, consistency, benchmark MAE, realism score.
- Business value: early-stage concept screening and better real survey design, not final market research replacement.
- Next steps: watsonx Orchestrate ADK, calibration, human/LLM judge, PPT/PDF export, Visa internal validation.

## Public Data Anchors

- Swiss Federal Statistical Office / FSO population 2024 key figures.
- Swiss National Bank Payment Methods Survey of Private Individuals in Switzerland 2025.
- Swiss Payment Monitor 1/2026 by ZHAW and University of St.Gallen.

See `docs/sources.md` and `data/benchmark_snb_2025.yaml` for links and values used in the validation layer.

## Guardrails

- No Visa internal, client-specific, or sensitive data is used.
- Persona weights and payment profiles are transparent and editable.
- Benchmark alignment is a grounding check, not a proof of accuracy.
- Final validation should compare outputs with real Visa/customer studies when available.
