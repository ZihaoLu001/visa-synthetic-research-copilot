# Architecture

## Product Intent

Visa Synthetic Research Copilot helps VCA consultants pressure-test early card, payment, or banking value propositions before commissioning real customer research. It accepts flexible survey/interview input instead of a fixed question list.

## Flow

```text
Consultant UI
  -> Survey Parser Agent
  -> Persona Builder / Selector
  -> Weighted Swiss Micro-Population
  -> Persona Respondent Agents
  -> Analytics Aggregator
  -> Benchmark / Consistency / Coverage Validator
  -> Consultant Report Export
```

## Components

`app.py`
: Streamlit cockpit for editing survey questions, card concepts, respondent count, provider, and validation repetitions.

`SyntheticResearchOrchestrator`
: Coordinates survey parsing, persona expansion, repeated synthetic survey runs, aggregation, and validation.

`SurveyParserAgent`
: Converts arbitrary survey or interview text into structured questions with type and measured construct.

`PersonaAgent`
: Answers each question from one persona's point of view using persona context, concept details, public benchmark context, and prior answers.

`InsightAnalystAgent`
: Converts aggregate metrics into consultant-facing recommendation, watchouts, and next test suggestions.

`validation.py`
: Runs benchmark alignment, internal consistency, and persona coverage checks.

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

## Extension Points

- Replace deterministic analyst with a watsonx.ai analyst prompt.
- Add LangGraph or watsonx Orchestrate ADK for durable multi-agent orchestration.
- Add calibrated weights from more granular FSO tables.
- Add export to PowerPoint/PDF for final consultant deliverables.
- Add human review loop for Visa benchmark calibration.
