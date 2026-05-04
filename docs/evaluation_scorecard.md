# Evaluation Scorecard

This document maps the PoC directly to the final presentation scoring areas.

## Demo - 5 Points

Evidence:

- `streamlit run app.py` launches a working consultant cockpit.
- Survey input is editable and supports uploaded `.txt` / `.md` guides.
- The Question Parser tab shows parsed question type and construct.
- The app runs a weighted Swiss micro-population and returns persona-level responses.
- Consultant Summary, Segment Explorer, Validation and Export tabs are all live.
- Sidebar demo scenarios support live fee/protection sensitivity reruns.

## Architecture - 3 Points

Evidence:

- `docs/architecture.md` documents the flow.
- `synthetic_researcher/orchestrator.py` owns the end-to-end workflow.
- `synthetic_researcher/llm.py` isolates model provider choice behind `BaseLLM`.
- `synthetic_researcher/validation.py` separates benchmark, consistency, coverage and realism validation.
- `synthetic_researcher/reporting.py` exports consultant-readable Markdown.

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

- connect selected agents to watsonx.ai and watsonx Orchestrate ADK
- add more granular FSO / Swiss Payment Monitor calibration
- add LLM-as-judge or human review on top of the transparent realism rubric
- export final reports to PowerPoint/PDF
- validate against Visa internal survey/customer insight data when available

## Presentation Quality - 3 Points

Evidence:

- Visa-style cockpit design, clean tabs and scorecards
- polished README and GitHub repository
- clear demo script and final presentation plan
- transparent source notes and guardrails
- traceability from aggregate insight down to persona response rows
