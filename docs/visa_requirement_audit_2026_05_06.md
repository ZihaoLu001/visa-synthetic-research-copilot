# Visa Requirement Audit - 2026-05-06

This audit maps the current product against `20260316_IBM_watsonx_kickoff_slides.pdf` and the later Slack clarification that the prototype should handle flexible survey questions rather than a fixed question list.

## Bottom Line

The current repository is no longer a toy demo. It is a consultant-grade pilot workbench that can be handed to IBM/Visa for testing through Code Engine, with a real IBM watsonx.ai / Granite path configured and a deterministic fallback for rehearsal.

The strongest recent addition is the Consultant Quality Layer. It gives every run an evidence grade, decision-risk rating, lead-margin interpretation, risk flags, survey repair plan and real-customer validation plan. This makes the system more VCA-like because it does not merely generate synthetic answers; it tells consultants how much to trust the evidence and what to test next.

It is still a pilot, not a production Visa system. Production use would require Visa-owned authentication, run storage, internal benchmark calibration, legal review and operating controls.

## Real Model Status

| Check | Status |
| --- | --- |
| Local watsonx.ai smoke test | Passed on 2026-05-06 with `ibm/granite-4-h-small`. |
| Local watsonx.ai mini synthetic run | Passed on 2026-05-06 with provider `watsonx`, parsed survey questions, persona responses and validation. |
| Code Engine API health | Passed on 2026-05-06 with `active_provider_if_auto=watsonx` and `watsonx_configured=true`. |
| Code Engine `/run` proof | Passed on 2026-05-06 with a one-question survey, 6 persona responses and validation output. |
| Slack-ready watsonx PDF report | Passed on 2026-05-06 with 72 persona-question responses, validation score 89.5, question coverage 100.0 and Consultant Quality evidence grade C because the concept lead is narrow. |
| CI and regression tests | Mock-backed by design so automated tests do not burn course quota or require secrets. |

## Requirement Trace

| Visa ask | Evidence in product | Status |
| --- | --- | --- |
| Design a concept for a multi-agent synthetic survey researcher | Streamlit VCA workbench, `SyntheticResearchOrchestrator`, parser, persona agents, analyst and validator. | Met |
| Represent different customer personas | `data/swiss_archetypes.yaml` includes Swiss archetypes with demographics, household, income, language region, lifestyle, payment profile and attitudes. | Met |
| Use public Swiss data and payment behavior | `data/benchmark_snb_2025.yaml`, sources notes and validation profiles reference BFS/FSO, Swiss Payment Monitor and SNB anchors. | Met |
| Answer flexible survey/interview questions | File ingestion accepts pasted text, PDF, DOCX, XLSX, CSV, TXT and Markdown; parser tests cover unseen survey phrasing and options. | Met |
| Multiple agents answer independently | Each persona answers each parsed question and concept with persona context, benchmark context and prior answers. | Met |
| Support high output volume | UI supports up to 96 synthetic respondents across all questions and concepts. | Met |
| Return both aggregated results and individual persona responses | Decision Brief, Consultant Summary, Segment Explorer, Persona Responses table, CSV export and JSON export. | Met |
| Include price sensitivity, feature preferences, barriers and card proposition outputs | Default research brief and analytics compute adoption, acceptable fee, feature/barrier labels and segment fit. | Met |
| Validate realism, benchmark alignment and internal consistency | Validation tab includes benchmark MAE, repeated-run Likert variance, coverage, question coverage and realism rubric. | Met |
| Make the output decision-grade for consultants | Consultant Quality Layer adds evidence grade, decision risk, lead-margin interpretation, survey repair plan and real-customer validation plan. | Met |
| Demonstrate time, cost and insight advantages | KPI cards and Scorecard tab show time-to-insight, response count, JSON success, benchmark and consistency evidence. | Met |
| Make it useful for consultants | Research Brief, Decision Brief, VCA "so what", hypothesis readout, recommended real research and Consultant Delivery Pack. | Met |

## Pilot Readiness

Ready for:

- final presentation live demo;
- IBM/Visa partner review through the public Code Engine URL;
- real-model proof using watsonx.ai / Granite;
- flexible survey/interview upload testing;
- export of a portable consultant delivery pack.

Not yet production-ready for:

- Visa SSO/user permissions;
- persistent run history and workspace governance;
- Visa internal customer insight calibration;
- legal/compliance approval for operational use;
- native PowerPoint report generation.

## Recommended Partner Framing

Say:

> This is a pilot workbench for early-stage VCA concept screening. It is benchmark-grounded, traceable to persona-level responses, and uses IBM watsonx.ai / Granite for the real-model proof. It is not a replacement for final customer research; it helps consultants decide what to test with real customers next.

Do not say:

> This predicts real Visa customer demand or replaces market research.
