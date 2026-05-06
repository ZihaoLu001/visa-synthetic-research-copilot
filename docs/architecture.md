# Architecture

## Product Intent

Visa Synthetic Research Copilot helps VCA consultants pressure-test early card, payment, or banking value propositions before commissioning real customer research. The core product is a synthetic customer lab: flexible survey/interview input is one artifact used to simulate customer perspectives, decision drivers and follow-up validation needs.

## Flow

```text
Consultant UI
  -> Research Brief / Decision Rule
  -> Survey File/Text Ingestion
  -> Survey Parser Agent
  -> Persona Builder / Selector
  -> Weighted Swiss Micro-Population
  -> Persona Respondent Agents
  -> Analytics Aggregator
  -> Benchmark / Consistency / Coverage / Realism Validator
  -> Synthetic Customer Lens
  -> Consultant Quality Layer
  -> VCA Decision Brief / PDF Report / Consultant Delivery Pack
```

## Components

`app.py`
: Streamlit cockpit for setting the research brief and decision rule, uploading or pasting survey questions, editing card concepts, selecting respondent count, choosing provider, and setting validation repetitions.

`consulting.py`
: Converts raw synthetic evidence into a VCA-style decision brief: executive answer, decision posture, concept matrix, "so what" implications, hypothesis readout, next real-research actions, methodology snapshot and limitations.

`ingestion.py`
: Converts pasted text plus TXT, MD, PDF, DOCX, CSV, and XLSX uploads into normalized survey text with extraction metadata. This lets Visa or IBM test the prototype with a real marketing research survey file instead of retyping every question.

`SyntheticResearchOrchestrator`
: Coordinates survey parsing, persona expansion, repeated synthetic survey runs, aggregation, and validation.

`SurveyParserAgent`
: Converts arbitrary survey or interview text into structured questions with type and measured construct. A deterministic construct-normalization pass cross-checks model output so adoption, price sensitivity, feature preference and barrier coverage remain stable for unfamiliar survey wording.

`PersonaAgent`
: Answers each question from one persona's point of view using persona context, concept details, public benchmark context, and prior answers.

`InsightAnalystAgent`
: Converts aggregate metrics into consultant-facing recommendation, watchouts, and next test suggestions.

`Decision Brief`
: Sits above the analyst summary. It answers the business question first, then links the recommendation to adoption, price, segment fit, validation score and the user's stated hypotheses. This is the layer that makes the prototype read like a consulting workbench instead of a generic synthetic respondent table.

`customer_lens.py`
: Reframes the run as a synthetic customer learning loop inspired by the Bain "synthetic customers" framing. It generates Bain-style use-case fit, scenario-design checks, the synthetic customer board, segment need states, likely best-fit concept, objections to probe, message tests, scenario-planning moves, decision drivers, time/cost advantage and real-customer bridge.

`insight_quality.py`
: Adds the consultant evidence lens: evidence grade, decision risk, lead-margin interpretation, segment differentiation, risk flags, survey repair plan, validation plan and calibration thresholds. This makes the output more defensible because VCA sees not only the answer, but also how strong the synthetic evidence is and what must be tested with real customers next.

`delivery.py`
: Packages the run into a partner-review ZIP containing the decision brief, PDF report, consultant report, persona-level CSV, validation JSON, full run JSON, input audit, methodology/governance notes, and a pilot readiness gate. This gives Visa a portable artifact they can inspect outside Streamlit.

`pdf_report.py`
: Renders a VCA-style PDF report from the exact run data: executive answer, KPI strip, research brief, consultant quality layer, concept decision matrix, signal/barrier tables, segment fit, persona-level evidence, validation confidence, methodology and limitations. This turns the demo into a concrete consultant artifact rather than only an on-screen dashboard.

`validation.py`
: Runs benchmark alignment, internal consistency, persona coverage, survey construct coverage, judge-style realism checks and an overall validation confidence score.

## Model Strategy

The system depends on a small `BaseLLM` interface:

```python
class BaseLLM:
    def generate_text(self, prompt: str) -> str: ...
    def generate_json(self, prompt: str) -> Any: ...
```

This keeps orchestration independent from any single model. `WatsonxLLM` calls IBM watsonx.ai with `ibm-watsonx-ai` when credentials are available. `MockLLM` remains a deterministic fallback for CI, rehearsals and quota failures.

Current default:

- `MODEL_PROVIDER=watsonx`: IBM watsonx.ai, default `WATSONX_MODEL_ID=ibm/granite-4-h-small`.
- `MODEL_PROVIDER=mock`: deterministic fallback, reproducible for CI and rehearsals.
- `MODEL_PROVIDER=auto`: selects watsonx when `WATSONX_URL`, `WATSONX_PROJECT_ID` and `WATSONX_APIKEY` are present; otherwise falls back to mock.

The production recommendation is to run pilot evidence generation through watsonx.ai, keep mock as a smoke-test fallback, and calibrate outputs against Visa internal studies when Visa can provide validation targets.

## Validation Layer

Benchmark alignment compares the synthetic panel's weighted payment-method mix to public Swiss payment benchmarks. It currently includes:

- SNB 2025 point-of-sale transactions
- Swiss Payment Monitor 1/2026 all transactions
- Swiss Payment Monitor 1/2026 in-store transactions

Internal consistency repeats the same run and measures Likert standard deviation per persona, concept, and question.

Coverage checks whether the synthetic panel spans the core Visa-requested dimensions: age, income, household, language region, and persona archetype count.

Question coverage checks whether the input survey includes the consultant constructs most relevant for card proposition testing: adoption, price sensitivity, feature preference and barriers.

The Synthetic Customer Lens answers the Bain-style product question: what customer perspectives did we simulate, what customer-learning use cases does this run support, what decision drivers emerged, what scenario moves should be tried next, where does this create time/cost advantage, and which assumptions still need real customer proof.

The Consultant Quality Layer converts validation output into an explicit actionability signal. A strong validation score can still be marked as medium decision risk if the concept lead is narrow, segment spread is weak or the survey lacks a key construct. Conversely, it can recommend a smaller real-customer validation plan when synthetic evidence is directionally strong.

The realism rubric checks for concise survey-style answers, model identity leakage, numeric range validity, rough persona/price alignment and obvious adoption-versus-price contradictions. It is intentionally transparent so a future watsonx judge or human reviewer can use the same rubric.

The app also records an input-source audit in every run: source type, uploaded file name, extracted character count, extraction notes, and whether the extracted text was edited before execution. This makes partner-side testing repeatable and reviewable.

## Extension Points

- Replace deterministic analyst with a watsonx.ai analyst prompt.
- Add authenticated project storage, run history, reviewer approval and audit logs for a true enterprise pilot.
- Add LangGraph or watsonx Orchestrate ADK for durable multi-agent orchestration.
- Add calibrated weights from more granular FSO tables.
- Add PowerPoint export if the final team wants a native deck artifact; the current app already exports a PDF report, portable consultant delivery pack and a PDF operation manual.
- Add human review loop for Visa benchmark calibration.
