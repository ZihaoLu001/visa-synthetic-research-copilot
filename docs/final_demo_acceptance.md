# Final Demo Acceptance Report

This is the final readiness checklist for the Visa Synthetic Research Copilot demo. It is written so the team can prove, quickly and calmly, that the project is deployed, testable, and aligned with the final rubric.

## Live URLs

```text
Streamlit consultant cockpit:
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

FastAPI / OpenAPI endpoint:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

API health:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud/health
```

## Verified On 2026-05-06

| Check | Result |
| --- | --- |
| Streamlit Code Engine app | HTTP 200 |
| API `/health` | HTTP 200, `status=ok`, `active_provider_if_auto=watsonx`, `watsonx_configured=true` |
| API `/run` synthetic survey | HTTP 200, parsed 5 flexible questions |
| API response volume | 24 respondents, 2 concepts, 5 questions, 2 consistency runs = 240 persona-question responses |
| Validation evidence | Overall validation score returned by API |
| Cloud watsonx.ai API proof | `POST /run` with a one-question card survey returned persona responses and validation under `MODEL_PROVIDER=watsonx` |
| External survey API stress tests | 3 public-example-inspired surveys returned synthetic responses, validation evidence, and 100.0 JSON parse success |
| Real watsonx.ai smoke test | `ibm/granite-4-h-small` returned a live response after IBM restored Group 28 quota |
| Real watsonx.ai mini-run | End-to-end parser/persona/validation flow completed with provider `watsonx` |
| Local regression tests | `19 passed` |
| GitHub Actions | CI and Docker publish workflows succeeded for latest pushed commit |

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
1. How likely would you be to adopt this card if it were offered by your bank?
2. What annual fee in CHF would feel acceptable for this card?
3. Which benefit or feature feels most valuable to you, and why?
4. Would you trust a card that automatically suggests the cheapest payment method at checkout?
5. What is the main barrier that would prevent you from using this card?
```

Demo sequence:

1. Open the Streamlit URL.
2. For the final real-model proof, set model provider to `watsonx` and confirm the sidebar shows `Real LLM ready`. Keep `mock` available only as a fallback for rehearsal or quota issues.
3. For a real-model proof, keep the default quick setting: `12` respondents, `1` consistency run, and `Quick real-model proof (first 2 questions)`. This conserves watsonx classroom quota while proving the live model path.
4. For the full-scale presentation run, switch to `Full survey`, move respondents to `96`, and use mock only if quota/time becomes a risk.
5. Use `Core Visa card survey`, upload the public sample PDF, or paste/upload a different survey if Visa wants to test from their side.
6. Run the synthetic survey and confirm the KPI cards show parsed questions, runtime, validation and response count.
7. Show `Consultant Summary`.
8. Show `Question Parser` to prove flexible survey input.
9. Show `Segment Explorer` for Swiss archetype differences.
10. Show `Persona Responses` for individual traceability.
11. Show `Validation` and `Scorecard` for benchmark, consistency, coverage, realism, pilot readiness, and grading evidence.
12. Download the Consultant Delivery Pack ZIP to show the partner-review artifact.
13. Switch the scenario to `Live sensitivity: lower Premium fee to CHF 60`, rerun, and explain directional movement.

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
