# Final Presentation Plan

Target: 20 minutes presentation + 5 minutes partner feedback.

Logistics for Team 1 / Group 28:

- Date: 26 May 2026
- Time: 19:15-19:40
- Location: IBM Schweiz AG, Vulkanstrasse 106, 8048 Zurich, Room 04404
- Arrival block: Block B starts at 18:00; official apero starts after the presentation block.

## 0:00-1:30 Problem and User

VCA consultants and product teams need early customer input when designing card and payment value propositions. Real surveys and interviews are still needed, but they are slower and more expensive than the early ideation cycle. This leaves assumptions about price sensitivity, benefits, needs and messaging under-tested.

## 1:30-3:00 Use-Case Understanding

The PoC is not a fixed FAQ bot. It is a flexible synthetic survey researcher:

- consultant pastes a survey, interview guide or proposition test
- the system parses the questions at runtime
- Swiss synthetic persona agents answer independently
- the output includes both persona-level traces and aggregate consultant insights

Positioning sentence:

> We do not claim to replace real customers. We give VCA consultants a fast, transparent, benchmark-grounded synthetic research layer to stress-test early value propositions, identify weak assumptions and design better real customer research.

## 3:00-5:00 Solution Overview

Show the architecture:

```text
Survey / concept input
  -> Survey Parser Agent
  -> Persona Builder / Weighted Micro-Population
  -> Persona Respondent Agents
  -> Analytics Aggregator
  -> Benchmark + Consistency + Realism Validator
  -> VCA Decision Brief / Consultant Delivery Pack
```

Explain that the orchestration is model-provider independent. The final real-model proof runs with watsonx.ai via `WatsonxLLM`; `MockLLM` stays available only as a reliability fallback for rehearsal, CI or quota issues.

IBM platform positioning:

- Primary final demo: Streamlit consultant cockpit, because the rubric rewards a working solution.
- IBM deployment proof: Code Engine is already running the Streamlit cockpit for Group 28.
- Integration proof: a second Code Engine app exposes FastAPI `/health` and `/run`; the OpenAPI contract points to that deployed API and can be imported as a watsonx Orchestrate tool.
- IBM model proof: Group 28's watsonx.ai / Granite path was verified after quota restoration on 2026-05-06.
- Orchestrate narrative: Orchestrate is the production coordinator for intake, tool calls, analyst review, and follow-up workflows, while the current repo remains the reliable demo runtime.

## 5:00-11:00 Live Demo

1. Confirm the sidebar shows `watsonx` and `Real LLM ready: ibm/granite-4-h-small`.
2. Upload the public sample PDF survey or paste the default card survey.
3. Run the quick real-model proof with 12 respondents and the first 2 questions.
4. Open Decision Brief for lead concept, decision posture, hypothesis readout and next real research.
5. Open the Question Parser tab to prove the survey is parsed dynamically from the uploaded file.
6. Open Consultant Summary for adoption index, acceptable fee and signals.
7. Open Segment Explorer for persona differences.
8. Open Persona Responses for traceability.
9. Open Validation for benchmark alignment, consistency, coverage and realism rubric.
10. If quota/time allows, switch to Full survey and 96 respondents; otherwise explain this as the full-scale mode already supported by the same workflow.

## 11:00-14:00 Architecture

Cover:

- Streamlit consultant cockpit
- data files for Swiss archetypes and benchmarks
- typed schemas and provider-independent `BaseLLM`
- orchestrator loop across personas, concepts and questions
- validation layer
- Consultant Delivery Pack, CSV and Markdown export
- FastAPI integration endpoint for Code Engine / watsonx Orchestrate
- OpenAPI and ADK assets under `orchestrate/`

Call out extension points:

- watsonx Orchestrate ADK for deployable agents
- LangGraph for durable graph orchestration
- more granular FSO calibration
- Native PowerPoint export as an optional next step; current repo already includes Markdown/CSV/JSON exports, a Consultant Delivery Pack and a PDF operation manual
- Visa internal validation once data is available

## 14:00-16:00 KPIs and Value

Use the app Scorecard tab:

- Time to first synthetic insight: target under 2 minutes
- Synthetic responses per run: 96 personas across concepts and questions
- JSON parse success rate: target above 95 percent
- Internal consistency: repeated-run Likert std below 0.5
- Benchmark alignment: payment-method mix MAE below 10 percentage points
- Consultant usefulness: target Visa feedback rating at least 4/5

Business value:

- screens weak propositions earlier
- finds segment-specific barriers before real survey spend
- improves interview guides and survey questions
- creates a transparent hypothesis log for consultants

## 16:00-18:00 Limitations and Governance

Be explicit:

- synthetic respondents are directional
- persona prompting can distort subgroups
- public benchmarks are limited
- final decisions require real customer validation
- no Visa internal or client-sensitive data is used

The strength of the PoC is not pretending to be perfect. The strength is showing the validation surface and the calibration path.

## 18:00-20:00 Next Steps

1. Connect selected agents to watsonx.ai / watsonx Orchestrate ADK.
2. Ask IBM to enable normal GitHub source-build / Container Registry permissions so the current runtime-clone Code Engine deployment can be replaced with a cleaner source-build deployment.
3. Import the deployed API OpenAPI tool into watsonx Orchestrate if the team wants a live IBM-platform proof during Q&A.
4. Calibrate persona weights with more FSO and payment benchmark slices.
5. Add native PowerPoint export if Visa wants a slide-ready artifact generated directly from each run.
6. Compare synthetic results to Visa internal studies when available.
