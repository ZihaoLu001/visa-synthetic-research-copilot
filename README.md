# Visa Synthetic Research Copilot

Running PoC for the IBM watsonx / Visa Consulting & Analytics **Multi-Agent Synthetic Researcher** case study.

The app accepts flexible survey, interview, or card value proposition test questions, runs a panel of public-data-grounded Swiss synthetic consumer personas, and returns:

- persona-level survey responses
- aggregated adoption, pricing, feature, and barrier signals
- segment-level fit by Swiss persona archetype
- benchmark alignment, internal consistency, and coverage checks
- downloadable CSV responses and Markdown consultant report

This is an early-stage hypothesis and survey-design tool. It does **not** claim to replace real customer research or Visa's final validation.

## Why this matches the Visa brief

The kickoff deck asks for three layers:

1. **Persona design**: Swiss personas grounded in public demographic and payment behavior anchors.
2. **Multi-agent layer**: one respondent agent per persona, orchestrated across survey questions and card concepts.
3. **Validation & insight**: aggregated consultant output plus individual responses, with benchmark and consistency checks.

This repo implements that flow in a small, demo-friendly Streamlit application with a deterministic mock provider and optional watsonx.ai provider.

## Quick Start

```powershell
cd visa-synthetic-research-copilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_cli.py
streamlit run app.py
```

For macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_cli.py
streamlit run app.py
```

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

1. Paste or edit a survey/interview guide.
2. Tune the two default card concepts and fees.
3. Run 48 or 96 synthetic respondents.
4. Review adoption index, acceptable fee, feature and barrier signals.
5. Open segment and persona-level tables for traceability.
6. Change a fee or feature live, rerun, and compare the directional movement.

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
run_cli.py                     Offline CLI smoke demo
data/
  swiss_archetypes.yaml        Swiss synthetic persona archetypes
  benchmark_snb_2025.yaml      Public benchmark anchors and validation profiles
  sample_concepts.yaml         Card propositions for the demo
  sample_survey_card.yaml      Sample survey
synthetic_researcher/
  agents.py                    Survey parser, persona respondent, analyst
  analytics.py                 Aggregation and scoring
  llm.py                       Mock + IBM watsonx providers
  orchestrator.py              End-to-end multi-agent run
  reporting.py                 Markdown consultant report
  sampler.py                   Weighted micro-population expansion
  schemas.py                   Typed dataclasses
  validation.py                Benchmark, consistency, coverage checks
tests/
  test_offline_run.py          Mock-mode regression tests
docs/
  architecture.md              System design and extension notes
  demo_script.md               6-7 minute demo script
  sources.md                   Public data sources
```

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
