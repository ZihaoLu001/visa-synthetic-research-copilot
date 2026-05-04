# IBM Code Engine Deployment

The course labs describe IBM Code Engine as the easiest way to expose a working PoC to stakeholders as a managed application. This repo includes a minimal Dockerfile so the Streamlit cockpit can be deployed without changing the product code.

## Recommended Path: IBM Cloud Console

The Cloud setup lab marks the IBM Cloud CLI as optional. You do **not** need to run Docker locally to deploy this project if the IBM Cloud Console has access to the GitHub repository and the assigned Code Engine project.

Use this path first:

1. Open IBM Cloud in the browser.
2. Select region `Frankfurt (eu-de)`.
3. Open Code Engine.
4. Select the Code Engine project assigned to the Visa use case or Group 28.
5. Create an **Application**.
6. Choose **Source code** or GitHub source.
7. Use repository `https://github.com/ZihaoLu001/visa-synthetic-research-copilot`.
8. Use branch `main`.
9. Keep the repo root as the build context; the included `Dockerfile` provides the runtime.
10. Set listening port `8080`.
11. Set environment variables:

```text
MODEL_PROVIDER=mock
APP_MODE=streamlit
```

After deployment, open the generated Code Engine application URL. This should load the Streamlit consultant cockpit.

For API/Orchestrate integration mode, create or update the application with:

```text
MODEL_PROVIDER=mock
APP_MODE=api
```

Then test:

```text
https://<code-engine-url>/health
```

## Optional Local Container Smoke Test

```bash
docker build -t visa-synthetic-research-copilot .
docker run --rm -p 8080:8080 visa-synthetic-research-copilot
```

Then open:

```text
http://localhost:8080
```

API mode smoke test:

```bash
docker run --rm -p 8080:8080 -e APP_MODE=api visa-synthetic-research-copilot
```

Then open:

```text
http://localhost:8080/health
```

or run a synthetic research call against `POST /run`.

## Optional IBM Cloud CLI Sketch

Use the Frankfurt region (`eu-de`) as recommended in the Code Engine lab.

```bash
ibmcloud login --sso
ibmcloud target -r eu-de
ibmcloud target -g watsonx_Challenge_2026_Students

ibmcloud ce project select --name <group-use-case-project>
ibmcloud ce application create \
  --name visa-synthetic-research-copilot \
  --build-source . \
  --port 8080 \
  --env MODEL_PROVIDER=mock \
  --env APP_MODE=streamlit
```

For the Group 28 deployment helper:

```powershell
.\scripts\deploy_code_engine.ps1 -ProjectName <group-28-visa-code-engine-project> -Mode streamlit
```

Use `-Mode api` if the deployment is meant to be imported into watsonx Orchestrate as an OpenAPI tool.

This helper is optional. It exists for repeatable deployment once the IBM Cloud CLI is installed, but the browser console path above is enough for the course workflow.

For watsonx.ai-backed runs, configure the same environment variables used locally:

```bash
ibmcloud ce application update \
  --name visa-synthetic-research-copilot \
  --env MODEL_PROVIDER=watsonx \
  --env WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env WATSONX_PROJECT_ID=<project-id> \
  --env WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
```

Store `WATSONX_APIKEY` as a Code Engine secret rather than committing it to the repository.

## watsonx Orchestrate Integration Asset

This repo includes two lightweight assets for the IBM platform story:

- `orchestrate/agents/visa_synthetic_research_copilot.yaml`: minimal ADK agent specification for explaining the coordinator-agent role.
- `orchestrate/openapi/visa_synthetic_research_api.yaml`: OpenAPI contract for calling the `/run` API from Orchestrate or Agent Builder.

Recommended final-demo stance:

1. Use Streamlit on Code Engine for the primary visual demo.
2. Use the API/OpenAPI asset as the integration proof for Orchestrate.
3. Avoid making Orchestrate custom Python tool deployment the critical path, because Slack reports show several teams hitting dependency and permission issues.

## Demo Positioning

- Local Streamlit is the reliable live-demo path.
- Code Engine is the stakeholder-sharing path if the team wants a public or partner-facing URL.
- API mode is the Orchestrate-tool path.
- Keep `MODEL_PROVIDER=mock` available for rehearsal and fallback.
