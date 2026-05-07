# Final Demo Acceptance Report

This is the final readiness checklist for the VCA Multi-Agent Synthetic Researcher demo. It is written so the team can prove, quickly and calmly, that the project is deployed, testable, and aligned with the final rubric.

## Live URLs

```text
Streamlit consultant cockpit:
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

FastAPI / OpenAPI endpoint:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

API health:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud/health
```

## Verified On 2026-05-07

| Check | Result |
| --- | --- |
| Streamlit Code Engine app | HTTP 200 |
| API `/health` | HTTP 200, `status=ok`, `active_provider_if_auto=watsonx`, `watsonx_configured=true` |
| API `/run` synthetic survey | HTTP 200, parsed 5 flexible questions |
| API response volume | Respondent count x parsed questions x consistency runs; defaults now use one client proposition so the output is easy for Visa reviewers to trace. |
| Validation evidence | Overall validation score returned by API |
| Cloud watsonx.ai API proof | `POST /run` with a one-question proposition survey returned persona responses and validation under `MODEL_PROVIDER=watsonx` |
| External survey API stress tests | 3 public-example-inspired surveys returned synthetic responses, validation evidence, and 100.0 JSON parse success |
| Real watsonx.ai smoke test | `ibm/granite-4-h-small` returned a live response after IBM restored Group 28 quota |
| Real watsonx.ai mini-run | End-to-end parser/persona/validation flow completed with provider `watsonx` |
| Local regression tests | `22 passed` |
| GitHub Actions | CI and Docker publish workflows succeeded for latest pushed commit |
| Slack-ready PDF report example | Public PDF survey input generates a watsonx/Granite consultant PDF report with persona-level responses, aggregate insights, validation checks and a real-customer validation plan |

## One-Command Smoke Test

From the repo root:

```powershell
.\scripts\smoke_deployment.ps1
```

Expected output:

```text
Streamlit cockpit OK: HTTP 200
API health OK: visa-synthetic-research-copilot
API run OK: run_id=<id>, responses=240, validation=<score>
```

If the first request takes longer than expected, wait and rerun. The Code Engine apps may scale down to zero and need a cold start.

## Final Demo Script

Use `demo/final_demo_survey.txt` as the live paste input:

```text
1. How relevant is this value proposition for your everyday payment or banking needs?
2. What annual fee or monthly price in CHF would feel acceptable, if any?
3. Which benefit or feature feels most valuable to you, and why?
4. Would you trust a payment assistant that suggests the most suitable payment method at checkout?
5. What is the main barrier or concern that would stop you from using it?
```

Demo sequence:

1. Open the Streamlit URL.
2. For the final real-model proof, set model provider to `watsonx` and confirm the sidebar shows `Real LLM ready`. Keep `mock` available only as a fallback for rehearsal or quota issues.
3. For a real-model proof, keep the default quick setting: `12` respondents, `1` consistency run, and `Quick real-model proof (first 2 questions)`. This conserves watsonx classroom quota while proving the live model path.
4. For the full-scale presentation run, switch to `Full survey`, move respondents to `96`, and keep mock only as an emergency fallback if IBM quota/time becomes a risk.
5. Use `Core Visa synthetic survey`, upload the public sample PDF, or paste/upload a different survey if Visa wants to test from their side.
6. Run the synthetic survey and confirm the KPI cards show parsed questions, runtime, validation and response count.
7. Show `Decision Brief`, especially the Consultant Quality Layer: evidence grade, decision risk, risk flags, survey repair plan and real-customer validation plan.
8. Show `Consultant Summary`.
9. Show `Question Parser` to prove flexible survey input.
10. Show `Segment Explorer` for Swiss archetype differences.
11. Show `Persona Responses` for individual traceability.
12. Show `Validation` and `Scorecard` for benchmark, consistency, coverage, realism, pilot readiness, and grading evidence.
13. Download the PDF Report and Consultant Delivery Pack ZIP to show the partner-review artifact.
14. Edit the proposition price, benefit wording or trust/control message, rerun, and explain directional movement.

## Partner Feedback Attachments

If asking Visa whether the output format meets their expectation, attach both files:

```text
demo/partner_examples/visa_example_input_public_mobile_payments_survey.pdf
demo/partner_examples/visa_example_output_consultant_report_watsonx.pdf
```

The first file is the uploaded survey artifact. The second file is the generated consultant report from the same flow with real `watsonx / ibm/granite-4-h-small`, including executive answer, Consultant Quality Layer, proposition evidence readout, segment fit, persona evidence, validation and governance caveats.

## What To Say

Use this as the anchor sentence:

```text
We do not claim to replace real customers. We give VCA consultants a fast, transparent, benchmark-grounded synthetic research layer to stress-test early propositions, identify weak assumptions, and design better real customer research.
```

## Platform Position

The final platform story is:

- Code Engine hosts the stakeholder-facing Streamlit app.
- Code Engine also hosts the FastAPI endpoint for OpenAPI import into watsonx Orchestrate or Agent Builder.
- watsonx.ai is the real-model provider for the final proof when credentials and quota are available.
- Mock mode is retained as a live-demo fallback because Slack reports show token-quota and Orchestrate custom Python dependency issues across several groups, but the current Code Engine apps are now configured with the watsonx secret for the final real-model proof.

This is the strongest low-risk route for the final: impressive live demo first, IBM-platform integration proof second, and clear governance/limitations throughout.
