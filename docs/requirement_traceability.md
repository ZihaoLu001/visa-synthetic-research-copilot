# Requirement Traceability

This checklist maps the project to the course emails, labs, final grading PDF, and Visa kickoff materials.

## Email And Course Logistics

| Source | Requirement or signal | Project response |
| --- | --- | --- |
| `Agentic AI Challenge Next Steps`, 18 Feb 2026 | Check Slack regularly; form groups and choose use cases. | Communication is external to the app; repo includes a clear README and demo script for partner discussion. |
| `Kickoff IBM watsonx Agentic AI Challenge: UC VISA`, 12 Mar 2026 | Kickoff on 16 Mar; questions sent via Slack or email before the kickoff. | Project scope follows the clarified Visa questions: persona structure, output format, data sources, and validation. |
| `Agentic AI Challenge Mid-Term: Visa`, 24 Mar 2026 | Midterm/final criteria are in `Midterm and Final Presentation.pdf`. | `docs/evaluation_scorecard.md` and the app Scorecard tab map evidence to the grading criteria. |

## Final Presentation Rubric

| Final rubric item | Evidence in this repo |
| --- | --- |
| In time, not overtime, not undertime | `docs/final_presentation_plan.md` provides a 20-minute structure. |
| Problem statement and pain points | README, `docs/demo_script.md`, and the app opening screen describe VCA users, slow surveys/interviews, and unvalidated pricing/feature assumptions. |
| Working demo solving the use case | `app.py` runs paste/upload survey -> parse -> persona agents -> analytics -> validation -> export. |
| Business value and pain-point fit | Consultant Summary and report explain early concept screening, time-to-insight, and better real survey design. |
| KPIs and how they are met | Runtime, response count, JSON success, benchmark MAE, consistency, coverage, and realism scores appear in the app and report. |
| Architecture with visuals | Architecture tab, `docs/architecture.md`, and componentized Python modules show UI, parser, persona store, LLM provider, orchestrator, analytics, validation, and export. |
| Next steps and limitations | Scorecard, README guardrails, and `docs/final_presentation_plan.md` explain watsonx Orchestrate, calibration, PowerPoint/PDF export, and Visa internal validation. |
| Appealing presentation and all team members speak | Demo script and presentation plan split the talk into clear sections that can be assigned across team members. |

## Visa Case Requirements

| Visa requirement | Implementation |
| --- | --- |
| Multi-agent synthetic survey researcher | `SyntheticResearchOrchestrator` runs independent persona agents across concepts and questions. |
| Swiss persona design | `data/swiss_archetypes.yaml` defines weighted Swiss archetypes with age, region, language, income, household, education, lifestyle, payment profile, attitudes, and source notes. |
| Public-data grounding | `data/benchmark_snb_2025.yaml` uses public Swiss payment behavior and demographic anchors. |
| Flexible survey/interview input | `app.py` accepts pasted text and uploaded TXT, MD, PDF, DOCX, CSV, and XLSX files through `synthetic_researcher/ingestion.py`. |
| High number of outputs | Slider supports 12-96 synthetic respondents across all questions and concepts. |
| Aggregated and persona-level results | Consultant Summary, Segment Explorer, Persona Responses, CSV export, Markdown report, and JSON export. |
| Realism, benchmark, and consistency validation | `synthetic_researcher/validation.py` includes benchmark alignment, repeated-run consistency, coverage, question coverage, and realism rubric. |
| No Visa-internal data required | README and app guardrails state that only public or user-provided data is used. |

## Lab-Informed Engineering Choices

| Lab | Relevant guidance | Project response |
| --- | --- | --- |
| Cloud & Course Setup | Use IBM Cloud account and Python development environment. | Python/Streamlit app with reproducible `requirements.txt` and CI tests. |
| Code Engine | Stakeholder demos can be deployed as a managed Code Engine application. | `Dockerfile`, `.dockerignore`, and `docs/code_engine_deployment.md` provide a deployment path. |
| Design Thinking | Design around real users and pain points, not just technology. | VCA consultant cockpit and output tabs follow the consultant workflow. |
| watsonx Orchestrate | Agents should have roles, tools, orchestration, and deployment story. | Parser, persona, analyst, validator, and orchestrator are separated; watsonx Orchestrate ADK remains a next step. |
| Prompt Engineering | Structured outputs, model parameters, and prompt discipline matter. | Prompts require strict JSON, persona context, benchmark context, and consistency with prior answers. |
| RAG / Tools / Parameters | Grounding and evaluation improve reliability. | Public benchmark grounding and validation dashboard are implemented; future RAG could ingest partner research docs. |
| Open Source Technology | Consider Docling, BeeAI, LangChain/LangFlow for extraction, tools, and orchestration. | Current ingestion uses lightweight open-source parsers; future extension can replace PDF/DOCX parsing with Docling and orchestration with LangGraph/BeeAI. |

## Remaining Optional Enhancements

- Add a watsonx Orchestrate ADK deployment package for one or more agents.
- Add Docling-based document extraction for richer table/form parsing.
- Add PowerPoint/PDF report export for a consultant-grade deliverable.
- Add a calibration workflow where Visa can compare synthetic outputs against internal survey results.
