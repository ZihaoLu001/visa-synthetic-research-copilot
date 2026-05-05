# Partner Questions

Use this document to prepare messages for Slack or the Q&A submission form before the final presentation.

## Where To Ask

- Visa-specific product, use-case, persona, survey, or architecture questions: `#watsonx-agentic-ai-challenge-2026-visa`.
- General IBM technical questions, quota issues, Code Engine, watsonx.ai, or Orchestrate setup: `#watsonx-agentic-ai-challenge-2026-general-guest`.
- Formal Q&A sessions: use the Q&A submission form linked in the general Slack channel for the 5 May and 12 May sessions: `ibm.biz/agenticaichallenge-qa`, password `watsonxagents`.
- Urgent partner alignment: post in the Visa channel and mention the lab team contacts already active there.

## Recommended Slack Message

```text
Hi IBM/Visa team, we want to make sure our final delivery matches expectations.

We are Team 1 / Group 28 for the Visa use case. Our current prototype is a working Streamlit app for a Synthetic Research Copilot: consultants can paste or upload a flexible survey/interview guide, run benchmark-grounded Swiss synthetic persona agents, and receive persona-level responses, aggregated insights, and validation checks.

We have prepared three delivery paths:
1. Streamlit consultant cockpit as the primary live demo.
2. IBM Code Engine deployment for stakeholder access.
3. FastAPI/OpenAPI integration asset so watsonx Orchestrate can call the synthetic research run as a tool.

Current Code Engine demo URL:
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

Current API / OpenAPI tool URL:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

Could you confirm:
1. For the final demo, is a Code Engine deployment plus watsonx.ai model provider sufficient, or do you expect the main workflow itself to run inside watsonx Orchestrate?
2. Given the recent ADK/custom Python tool dependency deployment issues mentioned in Slack, is it acceptable to present Orchestrate as an OpenAPI integration layer/production extension rather than the critical-path runtime?
3. Could Visa share one example card/product concept or marketing research survey question set they would like us to test in the final demo?
4. IBM source build from GitHub is currently blocked by Container Registry/service ID policy assignment permissions for Group 28. Could IBM enable this permission or confirm that the current Code Engine runtime-clone deployment is acceptable?

Thank you!
```

## Short Q&A Form Version

```text
Team 1 / Group 28, Visa use case. We built and deployed a Streamlit Synthetic Research Copilot that accepts flexible survey/interview input, runs Swiss synthetic persona agents, and returns persona-level responses, aggregate insights, and validation checks. Current demo URL: https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud. Current API/OpenAPI URL: https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud. We also prepared Docker/GitHub source-build assets and a watsonx Orchestrate import contract.

Questions:
1. Is Code Engine + watsonx.ai sufficient for the final live demo, or should the core workflow run inside watsonx Orchestrate?
2. Is it acceptable to present Orchestrate as a production integration/extension because several teams are reporting ADK custom-tool dependency issues?
3. Can Visa provide one example card concept or survey/interview guide for our final demo?
4. Can IBM enable normal Code Engine GitHub source-build permissions for Group 28, or confirm that our current deployed fallback is acceptable?
```

## If They Ask For A Very Specific Technical Question

Ask this in the general channel:

```text
Hi IBM team, for Group 28 we want to deploy our GitHub repo directly through the IBM Cloud Code Engine console, without relying on a local Docker or CLI setup. The app can run in Streamlit mode for the demo or API mode for an OpenAPI tool imported into watsonx Orchestrate. Could you confirm the Code Engine project name we should use for Group 28 / Visa and whether the project has the required source-build / Container Registry permissions?
```

Updated after deployment attempt:

```text
Hi IBM team, Group 28 / Visa now has the Streamlit app running on Code Engine here:
https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

We also have the API endpoint for OpenAPI/Orchestrate integration running here:
https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud

The regular GitHub source-build path is still blocked for us by a Container Registry/service ID policy assignment error:
Trace ID: codeengine-cli-di8dq00g89

Could you either enable the required source-build / Container Registry permissions for the Group 28 Code Engine project in eu-de, or confirm that the current runtime-clone deployment is acceptable for the final demo?
```
