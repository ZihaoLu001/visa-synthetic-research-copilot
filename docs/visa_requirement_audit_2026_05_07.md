# Visa Requirement Audit - 2026-05-07

This audit checks the current product against the Visa Consulting & Analytics brief in
`20260316_IBM_watsonx_kickoff_slides.pdf`, especially slides 3-5 and 7.

## Executive Verdict

The current product satisfies the core Visa requirement: it is a multi-agent synthetic
survey researcher for early-stage product and value proposition decisions, not a fixed
question-answer demo.

The strongest evidence is that the deployed app can:

- accept uploaded or pasted survey, interview, or value proposition inputs;
- parse the input into structured questions;
- run independent Swiss synthetic consumer persona agents with a real IBM watsonx /
  Granite model path;
- produce both aggregated consultant insights and persona-level responses;
- benchmark and validate outputs using public Swiss payment anchors; and
- export a consultant-style PDF report and evidence pack.

Remaining work is product-hardening rather than scope correction.

## Requirement Fit

| Visa ask | Current status | Evidence |
| --- | --- | --- |
| Design a concept for a multi-agent synthetic survey researcher | Green | Streamlit consultant cockpit, FastAPI endpoint, orchestrator, parser, persona agents, analyst, validator, PDF export. |
| Represent different customer personas | Green | `data/swiss_archetypes.yaml` contains weighted Swiss archetypes with age, region, language, income, household, education, lifestyle, payment profile and attitudes. |
| Provide realistic, consistent feedback in surveys or interviews | Green | Persona prompts include persona context, benchmark context and prior answers; validation includes realism and repeated-run consistency. |
| Support arbitrary survey/interview input, not fixed questions | Green | Upload/paste support for TXT, MD, PDF, DOCX, CSV and XLSX; public input stress tests cover ECB, Federal Reserve and FCA survey artifacts. |
| Support high number of outputs | Green | UI supports 12-96 synthetic respondents; response count scales with parsed questions and proposition count. |
| Support both aggregate and persona-level output | Green | Consultant Summary, Segment Explorer, Persona Responses, Decision Brief, PDF report and CSV/JSON export. |
| Use public Swiss demographic and payment behavior data | Mostly green | Persona store and benchmark YAML use Swiss public anchors and SNB-style payment-method benchmark. More BFS/FSO calibration can strengthen this further. |
| Benchmark against comparable real-world studies | Green for pilot | Benchmark alignment, question coverage, internal consistency, realism rubric and public stress-test runs. Final Visa validation still needs Visa internal studies. |
| Demonstrate time, cost and insight advantage | Green | Runtime KPIs, response volume, output report, survey repair plan, and real-research bridge are visible in the app and PDF reports. |

## What Changed After Scope Recheck

Earlier versions over-emphasized example card concepts. Those have been removed from
the product default flow. The current product keeps only the Visa-required flow:

1. Upload or paste a survey/interview/value proposition input.
2. Review parsed questions.
3. Define the client value proposition being tested.
4. Run Swiss synthetic customer persona agents.
5. Read aggregated insights and individual persona evidence.
6. Inspect validation/confidence checks.
7. Export a PDF consultant report and evidence pack.

## Alignment With The Visa Varia Reference

Visa linked Bain's synthetic customer article as further inspiration. The current
product is aligned with that reference in the areas that matter for the brief:

- it treats synthetic customers as an augmentation layer for faster early-stage
  product and value proposition decisions, not as a replacement for real customers;
- it uses scenario design plus data-grounded personas rather than generic chatbot
  role-play;
- it supports value proposition, pricing, messaging, segmentation and survey/interview
  testing rather than only a pre-scripted card comparison; and
- it exposes limitations and validation evidence because synthetic outputs can be
  biased, overly agreeable, or inconsistent in longer surveys.

This reinforces the scope decision to remove fixed A/B card defaults from the main
experience and keep the product centered on flexible synthetic customer research.

## Real Model Status

The intended real-model path is active:

- Provider: IBM watsonx.ai
- Model: `ibm/granite-4-h-small`
- Region: `eu-de`
- Live API health reports `watsonx_configured=true`
- Local tests and public input stress tests have completed with real watsonx outputs

Mock mode remains only as an emergency fallback for classroom quota or network issues.

## Current Proof Points

| Proof | Result |
| --- | --- |
| Unit/regression tests | `22 passed` on 2026-05-07 |
| Live app load | Passed desktop and mobile smoke test |
| Live console health | No browser console errors in the checked load path |
| Stale off-scope wording | No visible `Premium Travel`, `Everyday Cashback`, `Product Concepts`, `Concept A/B`, or `decision matrix` wording in the checked app/docs paths |
| Public input stress tests | ECB SPACE, Federal Reserve mobile financial services and FCA Financial Lives inputs generated watsonx PDF reports |
| Live API health | `active_provider_if_auto=watsonx`, `watsonx_configured=true`, `watsonx_model_id=ibm/granite-4-h-small` |

## Remaining Product Gaps

These are not blockers for the final demo, but they are the next best improvements if
the team wants to move from pilot to production-grade client tool.

1. Better public-data calibration
   - Add more explicit BFS/FSO distributions for age, household, language region,
     income and education.
   - Show a calibration table in the UI comparing synthetic panel weights to public
     Swiss population anchors.

2. Stronger benchmark library
   - Add a benchmark registry for SNB, Swiss Payment Monitor, ECB SPACE and other
     public payment studies.
   - Let the user choose which benchmark is relevant for a run.

3. More robust document extraction
   - Current PDF/DOCX/CSV/XLSX extraction is adequate for clean inputs.
   - For scanned PDFs, long tables, or complex forms, add Docling/OCR-style extraction.

4. Better human-in-the-loop controls
   - Let consultants accept/reject parsed questions before running agents.
   - Let consultants flag weak persona responses and rerun only those responses.

5. Run history and comparison
   - Store previous runs.
   - Compare two proposition wordings or fee/message variants side by side without
     re-uploading everything manually.

6. Enterprise governance
   - Add authentication, project-level access control, no-secret logging policy,
     audit trail and data-retention settings before real Visa client use.

## Recommended Final Presentation Position

Do not claim this replaces real customers. The strongest positioning is:

> This is a fast, transparent, benchmark-grounded synthetic customer layer for VCA
> consultants. It helps stress-test early value propositions, surface weak assumptions,
> identify segment differences and design better real customer research.

That statement matches the Visa slides and avoids overclaiming synthetic validity.
