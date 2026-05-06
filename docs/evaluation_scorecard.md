# Evaluation Scorecard

This document maps the PoC directly to the final presentation scoring areas.

## Demo - 5 Points

Evidence:

- `streamlit run app.py` launches a working consultant cockpit.
- Survey input is editable and supports uploaded `.txt`, `.md`, `.pdf`, `.docx`, `.csv`, and `.xlsx` guides.
- The Question Parser tab shows parsed question type, construct and input-source audit.
- The app runs a weighted Swiss micro-population and returns persona-level responses.
- Decision Brief, Consultant Summary, Segment Explorer, Persona Responses, Validation, Scorecard and Architecture tabs are all live.
- The sidebar exposes the real IBM watsonx.ai / Granite provider and a quota-safe quick proof scope.
- CSV, Markdown report, full JSON and Consultant Delivery Pack downloads make the result testable from the partner side.
- Sidebar demo scenarios support live fee/protection sensitivity reruns.

## Architecture - 3 Points

Evidence:

- `docs/architecture.md` documents the flow.
- `synthetic_researcher/orchestrator.py` owns the end-to-end workflow.
- `synthetic_researcher/ingestion.py` normalizes survey files into text before agent parsing.
- `synthetic_researcher/llm.py` isolates model provider choice behind `BaseLLM`.
- `synthetic_researcher/validation.py` separates benchmark, consistency, coverage and realism validation.
- `synthetic_researcher/reporting.py` exports consultant-readable Markdown.
- `synthetic_researcher/delivery.py` exports a partner-review ZIP and readiness gate.

## KPIs - 2 Points

Implemented metrics:

- Time to first synthetic insight: `aggregate.runtime.elapsed_seconds`
- Number of synthetic responses: `aggregate.response_count`
- JSON parse success: `aggregate.runtime.json_parse_success_rate`
- Internal consistency: `validation.internal_consistency.avg_likert_std`
- Benchmark alignment: `validation.benchmark_alignment.primary_mae_percentage_points`
- Realism rubric: `validation.realism_rubric.score`

Presentation targets:

- time to first insight under 2 minutes
- up to 96 synthetic respondents per run
- JSON parse success above 95 percent
- repeated-run Likert standard deviation below 0.5
- benchmark alignment MAE below 10 percentage points
- Visa feedback rating at least 4/5 after partner review

## Business Value - 2 Points

Evidence:

- The app positions output as early-stage hypothesis screening.
- It does not claim to replace final real customer validation.
- It highlights segment-specific barriers, pricing signals and next tests.
- It helps consultants decide which weak assumptions deserve real customer research.

## Next Steps - 2 Points

Roadmap:

- extend the current watsonx.ai provider proof into watsonx Orchestrate ADK or Agent Builder when dependency deployment is stable
- add more granular FSO / Swiss Payment Monitor calibration
- add LLM-as-judge or human review on top of the transparent realism rubric
- export final reports to native PowerPoint if needed; the current repository already includes a consultant delivery pack and a PDF operation manual with screenshots
- validate against Visa internal survey/customer insight data when available

## Presentation Quality - 3 Points

Evidence:

- Visa-style cockpit design, clean tabs and scorecards
- polished README and GitHub repository
- clear demo script and final presentation plan
- transparent source notes and guardrails
- traceability from aggregate insight down to persona response rows
