# Architecture

## Product Intent

Visa Synthetic Research Copilot helps VCA consultants pressure-test early card, payment, or banking value propositions before commissioning real customer research. It accepts flexible survey/interview input instead of a fixed question list.

## Flow

```text
Consultant UI
  -> Survey File/Text Ingestion
  -> Survey Parser Agent
  -> Persona Builder / Selector
  -> Weighted Swiss Micro-Population
  -> Persona Respondent Agents
  -> Analytics Aggregator
  -> Benchmark / Consistency / Coverage / Realism Validator
  -> Consultant Report Export
```

## Components

`app.py`
: Streamlit cockpit for uploading or pasting survey questions, editing card concepts, selecting respondent count, choosing provider, and setting validation repetitions.

`ingestion.py`
: Converts pasted text plus TXT, MD, PDF, DOCX, CSV, and XLSX uploads into normalized survey text with extraction metadata. This lets Visa or IBM test the prototype with a real marketing research survey file instead of retyping every question.

`SyntheticResearchOrchestrator`
: Coordinates survey parsing, persona expansion, repeated synthetic survey runs, aggregation, and validation.

`SurveyParserAgent`
: Converts arbitrary survey or interview text into structured questions with type and measured construct.

`PersonaAgent`
: Answers each question from one persona's point of view using persona context, concept details, public benchmark context, and prior answers.

`InsightAnalystAgent`
: Converts aggregate metrics into consultant-facing recommendation, watchouts, and next test suggestions.

`validation.py`
: Runs benchmark alignment, internal consistency, persona coverage, survey construct coverage, judge-style realism checks and an overall validation confidence score.

## Model Strategy

The system depends on a small `BaseLLM` interface:

```python
class BaseLLM:
    def generate_text(self, prompt: str) -> str: ...
    def generate_json(self, prompt: str) -> Any: ...
```

This keeps orchestration independent from any single model. `MockLLM` provides deterministic offline behavior for demo reliability. `WatsonxLLM` can call IBM watsonx.ai with `ibm-watsonx-ai` when credentials are available.

## Validation Layer

Benchmark alignment compares the synthetic panel's weighted payment-method mix to public Swiss payment benchmarks. It currently includes:

- SNB 2025 point-of-sale transactions
- Swiss Payment Monitor 1/2026 all transactions
- Swiss Payment Monitor 1/2026 in-store transactions

Internal consistency repeats the same run and measures Likert standard deviation per persona, concept, and question.

Coverage checks whether the synthetic panel spans the core Visa-requested dimensions: age, income, household, language region, and persona archetype count.

Question coverage checks whether the input survey includes the consultant constructs most relevant for card proposition testing: adoption, price sensitivity, feature preference and barriers.

The realism rubric checks for concise survey-style answers, model identity leakage, numeric range validity, rough persona/price alignment and obvious adoption-versus-price contradictions. It is intentionally transparent so a future watsonx judge or human reviewer can use the same rubric.

The app also records an input-source audit in every run: source type, uploaded file name, extracted character count, extraction notes, and whether the extracted text was edited before execution. This makes partner-side testing repeatable and reviewable.

## Extension Points

- Replace deterministic analyst with a watsonx.ai analyst prompt.
- Add LangGraph or watsonx Orchestrate ADK for durable multi-agent orchestration.
- Add calibrated weights from more granular FSO tables.
- Add PowerPoint/PDF report export for final consultant deliverables.
- Add human review loop for Visa benchmark calibration.
