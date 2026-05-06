# Slack Platform Findings

This note records the deployment and platform guidance extracted from the IBM Slack workspace, especially `#watsonx-agentic-ai-challenge-2026-general-guest`, after reviewing the visible channel history and the deployment-related threads on 2026-05-05.

## Scope Reviewed

- General channel history visible in Slack from 2026-02-24 through 2026-05-04.
- Deployment-related threads on Code Engine projects, resource groups, watsonx.ai projects and quotas, Container Registry permissions, Orchestrate plan expiry, custom Python tools, and HTTP/TCP limitations.
- Course labs under `D:\master\seminar\Labs`, especially Cloud setup, Code Engine, watsonx Orchestrate, watsonx.ai, and RAG/OpenAPI labs.

## Decisions For Group 28 / Visa

| Decision | Evidence from Slack/Labs | Impact on this repo |
| --- | --- | --- |
| Use the assigned Code Engine project. Do not create a new one. | Dimitri clarified on 2026-03-10 that students are not supposed to create Code Engine projects; each group already has a project where they can create applications and jobs. | The app is deployed to the existing Group 28 Code Engine project. Docs tell the team to select the assigned project rather than creating a new one. |
| Target `eu-de` and the correct resource group. | Slack thread on 2026-03-10 explains that CLI users must target the resource group UUID before selecting the Code Engine project. A later 2026-04-28 thread again emphasizes correct region `EU-DE` and resource group. | Docs keep `eu-de`, `group28`, and browser-first instructions. CLI commands are optional and include resource group targeting. |
| Code Engine Application is the main stakeholder demo path. | Code Engine lab says applications are ideal for presenting a proof of concept to stakeholders without managing servers. | Streamlit cockpit is the primary live demo and has a verified public Code Engine URL. |
| Code Engine apps should expose HTTP endpoints. | A 2026-04-23 thread reports raw TCP services such as PostgreSQL are not working as Code Engine applications; HTTP requests are the reliable path. | The project exposes Streamlit and FastAPI over HTTP. No raw TCP database is required for the final demo. |
| Do not make Container Registry source builds the only path. | 2026-04-20 and 2026-04-25 threads report registry storage quota failures. 2026-04-28 thread reports namespace/permission confusion; Dimitri says the namespace already exists and should not be manually created. | The repo keeps normal GitHub source-build docs, but also documents the verified runtime-clone fallback. Ask IBM to confirm source-build permissions or accept the current fallback. |
| Keep `MODEL_PROVIDER=mock` as a fallback, but use `MODEL_PROVIDER=watsonx` for the final real-model proof. | 2026-04-11, 2026-04-13, and 2026-05-04 messages show `token_quota_reached (403)` for watsonx.ai runtime calls; IBM can upgrade quotas but issues can still happen. On 2026-05-06 Lenny restored Group 28's runtime quota and the live Granite smoke test succeeded. | The app now surfaces whether watsonx is configured. The local and Code Engine paths are configured for IBM Granite; mock remains a rehearsal/quota fallback. |
| Create watsonx.ai project/API key inside the watsonx.ai instance, not generic IBM Cloud project creation. | 2026-03-18 thread says to navigate to the group watsonx.ai instance, create a project there, and then create the API key. | `.env.example` and docs use `WATSONX_PROJECT_ID` and `WATSONX_APIKEY`, but final demo can run without them. |
| Keep Orchestrate as integration/extension unless tool deployment is confirmed. | 2026-04-27 and 2026-05-02 thread shows custom Python tools with `requirements.txt` can block invocation and agent deployment with `uv install`/500 errors. | The critical path is Streamlit on Code Engine plus FastAPI/OpenAPI tool import. The ADK spec is architecture evidence, not the only runtime. |
| Orchestrate plan expiry needs no student action. | 2026-04-05/06 thread says free-plan expiry is expected and plans will be upgraded. 2026-04-07 confirms UC-account Orchestrate instances were upgraded to `Essentials Agentic MAU`. | No local migration is needed solely because the UI shows a plan expiry warning. |
| Ask platform questions in general Slack, use-case questions in Visa Slack, formal questions via Q&A form. | 2026-04-02 and 2026-04-29 messages say technical troubleshooting should be posted in Slack, while implementation/final-presentation questions can use the Q&A form. | `docs/partner_questions.md` separates IBM technical asks from Visa product asks. |

## Recommended Final Platform Story

1. Primary demo: Code Engine Streamlit application.
2. Integration proof: Code Engine FastAPI endpoint imported into watsonx Orchestrate or Agent Builder through OpenAPI.
3. IBM model proof: watsonx.ai provider with `ibm/granite-4-h-small`; verified live on 2026-05-06 after IBM restored the Group 28 runtime quota.
4. Cloud proof: Code Engine API `/health` now reports `watsonx_configured=true`, and a one-question `/run` call returned persona responses and validation under the watsonx configuration.
5. Reliability fallback: deterministic mock provider, retained for rehearsal or quota contingency.
6. Future extension: package the workflow into Orchestrate ADK or custom tools only after IBM confirms the dependency deployment issue is resolved.

## Current Verified Assets

```text
Streamlit app:
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

FastAPI / OpenAPI tool endpoint:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud
```

The deployed apps are enough to show that stakeholders do not need to run anything locally. They also align with the Code Engine lab guidance: deploy a proof-of-concept application for testing and stakeholder presentation. As of 2026-05-06, both apps reference the `watsonx-runtime-env` Code Engine secret for the real-model proof.

## Open Questions To Ask

Ask IBM technical questions in `#watsonx-agentic-ai-challenge-2026-general-guest`:

- Can IBM enable normal GitHub source-build / Container Registry policy assignment permissions for Group 28, or confirm that the current runtime-clone Code Engine deployment is acceptable for final demo?
- Is the Group 28 registry namespace already `group28`, and should we avoid creating any namespace manually?
- Given the reported Orchestrate custom Python dependency issue, is an OpenAPI tool calling our Code Engine API the recommended low-risk Orchestrate integration route?

Ask Visa use-case questions in `#watsonx-agentic-ai-challenge-2026-visa`:

- Can Visa share one representative card/product concept or marketing research survey/interview guide for the final demo?
- Should the final output emphasize persona-level responses, aggregate insights, or both?
- Which benchmark or validation evidence would be most convincing for VCA stakeholders?

Use the Q&A form mentioned in general Slack for formal session questions:

```text
ibm.biz/agenticaichallenge-qa
password: watsonxagents
```
