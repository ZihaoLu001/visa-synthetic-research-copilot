# VCA Multi-Agent Synthetic Researcher

Running PoC for the IBM watsonx / Visa Consulting & Analytics **Multi-Agent Synthetic Researcher** case study.

The app accepts a client payment or banking value proposition plus flexible survey, interview, or proposition-test questions, runs a panel of public-data-grounded Swiss synthetic customers, and returns:

- a consultant research brief with objective, decision rule, hypotheses and expected stakeholder output
- a Visa-focused customer perspective board with segment needs, objections, message tests, time/cost advantage and real-customer validation bridge
- a decision brief that translates synthetic evidence into VCA-style recommendation, action, caveats and next real-research steps
- persona-level survey responses
- aggregated adoption, pricing, feature, and barrier signals
- segment-level fit by Swiss persona archetype
- benchmark alignment, internal consistency, and coverage checks
- judge-style realism rubric and overall validation confidence
- consultant quality layer with evidence grade, decision risk, lead-margin interpretation, survey repair plan and real-customer validation plan
- file ingestion audit for pasted text, TXT, MD, PDF, DOCX, CSV, and XLSX survey inputs
- downloadable VCA-style PDF report generated from the exact run evidence
- downloadable consultant delivery pack with decision brief, PDF report, Markdown report, persona CSV, validation JSON, full run JSON, source audit and governance notes
- external survey stress-test set inspired by public proposition-testing and payment-survey examples

This is an early-stage hypothesis and survey-design tool. It does **not** claim to replace real customer research or Visa's final validation.

## Why this matches the Visa brief

The kickoff deck asks for three layers:

1. **Persona design**: Swiss personas grounded in public demographic and payment behavior anchors.
2. **Multi-agent layer**: one respondent agent per persona, orchestrated across survey questions and the client value proposition.
3. **Validation & insight**: aggregated consultant output plus individual responses, with benchmark and consistency checks.

This repo implements that flow in a focused Streamlit workbench with a deterministic fallback provider and an IBM watsonx.ai provider.

The product is intentionally framed as a **consultant-grade multi-agent synthetic research workbench**, not a generic chatbot and not a fixed A/B demo. A user starts with the business decision and hypotheses, uploads or pastes a survey/interview artifact, defines the client value proposition, then reviews synthetic customer perspectives, decision drivers, evidence quality and the real-customer validation plan.

## Algorithm and Model Stack

Current runtime has two interchangeable provider modes and an `auto` default:

- `MODEL_PROVIDER=watsonx` uses IBM watsonx.ai through `ibm-watsonx-ai` `ModelInference`, with default model `ibm/granite-4-h-small`. Set `WATSONX_URL`, `WATSONX_PROJECT_ID`, `WATSONX_APIKEY`, and optionally `WATSONX_MODEL_ID`.
- `MODEL_PROVIDER=mock` uses a deterministic `MockLLM` for rehearsals, CI and quota-failure fallback.
- `MODEL_PROVIDER=auto` uses watsonx when all credentials are present and falls back to mock only when they are missing.

The main algorithms are transparent and replaceable:

- File ingestion extracts text from PDF, DOCX, XLSX, CSV, TXT or pasted survey content and stores an audit trail.
- Survey parsing turns arbitrary research questions into structured question objects: Likert, choice, price or open text.
- Deterministic construct normalization cross-checks model output so adoption, price, feature and barrier signals remain stable even when an uploaded survey uses unfamiliar wording.
- Persona sampling expands Swiss public-data-grounded archetypes into a weighted synthetic micro-population.
- Persona response generation asks one persona agent at a time, using value-proposition context, public benchmark context and prior answers for consistency.
- Aggregation computes weighted adoption index, acceptable-fee signals, feature/barrier labels, segment fit and persona quotes.
- Validation computes benchmark alignment MAE, repeated-run Likert variance, persona coverage, question construct coverage and judge-style realism flags.
- Synthetic customer synthesis builds a customer board with need states, proposition fit, objections to probe, message tests, decision drivers, time/cost advantage and real-customer bridge for each Swiss segment.
- Consulting synthesis builds a VCA Decision Brief: proposition signal, evidence quality, decision posture, hypothesis readout, next tests and governance caveats.
- Consultant quality scoring adds an explicit evidence grade, decision risk, risk flags, survey repair plan and real-customer validation plan so VCA can decide what is strong enough to use and what still needs real customer proof.
- PDF reporting renders a consultant-style report with executive answer, decision matrix, segment fit, persona evidence, validation confidence, methodology and limitations.
- Delivery packaging exports a partner-review ZIP so Visa can inspect the recommendation, PDF report, persona rows, validation evidence and source audit outside the app.

The `mock` provider is not presented as a real customer model. It is a reliability fallback. The final partner proof should run the same workflow with watsonx credentials and then calibrate persona weights/prompts against Visa internal research.

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

The course labs highlight Code Engine as a lightweight stakeholder demo path. A Group 28 cloud deployment was verified on 2026-05-04:

```text
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud
```

The verified deployment runs the Streamlit cockpit and successfully completed a 96-persona synthetic survey run in the browser. It is now configured with `MODEL_PROVIDER=watsonx` and a Code Engine secret for the final real-model proof; `MODEL_PROVIDER=mock` remains available only as a rehearsal/quota fallback. The preferred long-term deployment path remains GitHub source build with the included `Dockerfile`, port `8080`, and `APP_MODE=streamlit`; the current IBM account still needs Container Registry/source-build permissions enabled for Group 28. See `docs/code_engine_deployment.md`.

The API integration endpoint for watsonx Orchestrate/OpenAPI tool import is also deployed:

```text
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud
```

Slack and lab review confirmed that the safest final platform story is **Code Engine as the primary stakeholder demo** plus **OpenAPI/FastAPI as the Orchestrate integration proof**. Several teams reported watsonx.ai quota, Container Registry, and Orchestrate custom Python dependency issues in Slack, so the deterministic mock provider and the deployed HTTP API remain intentional risk controls. IBM restored the Group 28 watsonx.ai text-generation quota on 2026-05-06; the live Granite smoke test, a small end-to-end run, and the Code Engine API health/run proof now succeed with watsonx configured. See `docs/slack_platform_findings.md`.

## Real IBM watsonx.ai Setup

Copy `.env.example` to `.env` and set:

```bash
MODEL_PROVIDER=watsonx
WATSONX_URL=https://eu-de.ml.cloud.ibm.com
WATSONX_PROJECT_ID=...
WATSONX_APIKEY=...
WATSONX_MODEL_ID=ibm/granite-4-h-small
```

Then verify a real IBM Granite call:

```powershell
python scripts/watsonx_smoke_test.py
```

For a tiny end-to-end LLM-backed run, use:

```powershell
python scripts/watsonx_smoke_test.py --mini-run
```

Keep `MODEL_PROVIDER=mock` available only as a fallback for rehearsal, CI, and quota issues. In the Streamlit app, select **watsonx** for the final real-model proof. The app defaults to a quota-safe **Quick real-model proof** scope when watsonx credentials are present; switch to **Full survey** and 96 respondents when quota/time allows.

## Operating Flow

1. Edit the Research Brief: objective, client decision, hypotheses, decision rule and desired stakeholder output.
2. Upload a PDF survey/interview guide, or use TXT, MD, DOCX, CSV, or XLSX when that is what the client has.
3. Review the extracted survey text and adjust questions if needed.
4. Set the Swiss target market and paste the client value proposition to test.
5. Run a quick live watsonx proof with 12 respondents and the first 2 uploaded questions, or switch to a full survey run with up to 96 respondents.
6. Open Decision Brief for the proposition readout, customer perspective board, decision posture, Consultant Quality Layer, hypothesis readout, caveats and recommended real research.
7. Review adoption index, acceptable fee, feature and barrier signals.
8. Open the Question Parser tab to prove the survey is not hardcoded and inspect the PDF extraction audit.
9. Open segment and persona-level tables for traceability.
10. Open Validation and Scorecard for benchmark, consistency, coverage, realism and KPI evidence.
11. Download the polished PDF Report, Consultant Delivery Pack ZIP, CSV, Markdown Decision Brief, full Markdown report, or JSON outputs for partner review.
12. Change a price, benefit, or message live, rerun, and compare the directional movement.

The Slack-ready PDF operation manual is in `demo/manuals/visa_synthetic_research_copilot_operation_manual.pdf`. It shows the full workflow with a public Federal Reserve mobile-payments survey excerpt uploaded as a PDF attachment, the real IBM watsonx.ai / Granite model path, screenshots from a live quick run, and reviewer instructions. The real-run video is retained in `demo/videos/visa_synthetic_research_copilot_real_upload_demo.mp4`.

Slack-ready example attachments are also included:

```text
demo/partner_examples/visa_example_input_public_mobile_payments_survey.pdf
demo/partner_examples/visa_example_output_consultant_report_watsonx.pdf
```

The output report was generated from the input PDF flow with `MODEL_PROVIDER=watsonx`, `ibm/granite-4-h-small`, Swiss synthetic respondents, payment/value-proposition survey questions, persona-level responses, validation checks and a generated consultant PDF report. It is intentionally positioned as directional evidence for deciding what to test with real Swiss customers next.

Suggested live stress test:

```text
Would you trust a payment assistant that suggests the most suitable payment method at checkout?
What annual fee in CHF would you consider acceptable?
Which benefit would make you try this proposition instead of your current payment habit?
What is the main barrier that would stop you?
```

## Project Structure

```text
app.py                         Streamlit consultant cockpit
api.py                         FastAPI integration endpoint for Code Engine / Orchestrate
run_cli.py                     Offline CLI smoke demo
demo/
  final_demo_survey.txt        Live-paste survey for the final demo
  api_smoke_payload.json       Cloud API smoke-test payload
  public_survey_uploads/       Public survey excerpt in TXT and PDF upload formats
  manuals/                     PDF operation manual, HTML source, screenshots and Slack draft
  partner_examples/            Slack-ready input PDF survey and output watsonx PDF report
  videos/                      Slack-ready real-run demo video and post draft
data/
  swiss_archetypes.yaml        Swiss synthetic persona archetypes
  benchmark_snb_2025.yaml      Public benchmark anchors and validation profiles
  sample_value_proposition.yaml
                               Generic client value proposition sample for CLI/tests
  sample_survey_proposition.yaml
                               Generic proposition survey sample
synthetic_researcher/
  agents.py                    Survey parser, persona respondent, analyst
  analytics.py                 Aggregation and scoring
  ingestion.py                 TXT/MD/PDF/DOCX/CSV/XLSX survey extraction
  consulting.py                VCA-style research brief and decision brief synthesis
  delivery.py                  Consultant delivery pack and pilot readiness gate
  customer_lens.py             Visa-focused customer board, decision drivers and real-customer bridge
  insight_quality.py           Evidence grade, decision risk, survey repair plan and validation plan
  llm.py                       Mock + IBM watsonx providers
  orchestrator.py              End-to-end multi-agent run
  pdf_report.py                VCA-style PDF report renderer
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
  build_operation_manual.py    Rebuilds the PDF operation manual from screenshots
  deploy_code_engine.ps1       IBM Code Engine deployment helper
  smoke_deployment.ps1         Verifies the deployed Streamlit and API apps
  run_external_survey_tests.ps1 Posts public-example-inspired surveys to the deployed API
  watsonx_smoke_test.py        Verifies a live IBM watsonx.ai / Granite call
docs/
  architecture.md              System design and extension notes
  demo_script.md               6-7 minute demo script
  code_engine_deployment.md     Optional IBM Code Engine deployment path
  evaluation_scorecard.md      Mapping to final presentation grading criteria
  final_demo_acceptance.md     Final deployed-demo acceptance checklist
  final_delivery_runbook.md     Group 28 final delivery checklist
  external_survey_testing.md    Public-survey-inspired acceptance-test evidence
  final_presentation_plan.md   20-minute presentation structure
  partner_questions.md          Slack/Q&A messages for IBM and Visa alignment
  real_watsonx_runbook.md       Checklist for the final real-model proof
  requirement_traceability.md  Email/lab/rubric/Visa requirement checklist
  research_notes.md            Framework and synthetic survey research notes
  slack_platform_findings.md   Slack-derived IBM platform and deployment decisions
  sources.md                   Public data sources
  visa_requirement_audit_2026_05_06.md Current requirement and real-model readiness audit
```

## Full-Mark Scorecard Targets

- Running demo: paste survey -> parse -> simulate -> aggregate -> validate -> export.
- Flexible input demo: uploaded marketing research survey files can be converted to survey text before parsing.
- External survey proof: proposition-test, payment-behavior, and pricing/message surveys in `demo/external_survey_tests/` run through the same pipeline.
- Architecture: UI, parser, persona store, orchestrator, respondent agents, validator, analytics/export.
- KPIs: time to insight, response count, JSON parse success, consistency, benchmark MAE, realism score.
- Business value: early-stage proposition screening and better real survey design, not final market research replacement.
- Next steps: watsonx Orchestrate ADK, calibration, human/LLM judge, PPT export, Visa internal validation.

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
