# IBM Code Engine Deployment

The course labs describe IBM Code Engine as the easiest way to expose a working PoC to stakeholders as a managed application. This repo includes a minimal Dockerfile so the Streamlit cockpit can be deployed without changing the product code.

## Current Verified Deployment

As of 2026-05-04, the Streamlit cockpit is deployed in the assigned Group 28 Code Engine project:

```text
Application: visa-synthetic-research-copilot
Region: eu-de
Resource group: group28
Code Engine project: group28
Public URL: https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud
Mode: APP_MODE=streamlit; MODEL_PROVIDER=watsonx with watsonx-runtime-env secret configured.
Verification: HTTP 200 and an in-browser 96-respondent run completed successfully; real-model path is now configured for final proof.
```

The real IBM watsonx.ai / Granite provider was verified locally on 2026-05-06 after IBM restored Group 28's text-generation quota. On the same day the Code Engine apps were updated with `MODEL_PROVIDER=watsonx` and a `watsonx-runtime-env` secret, so the cloud health check now reports `watsonx_configured: true`.

The FastAPI integration endpoint is also deployed for watsonx Orchestrate/OpenAPI import:

```text
Application: visa-synthetic-research-api
Public URL: https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud
Verification: /health returned HTTP 200 with `active_provider_if_auto=watsonx`, and POST /run returned HTTP 200 with synthetic research JSON from the real-model configuration.
```

The deployment uses a temporary runtime-clone fallback from the public GitHub repository because the official Code Engine source-build path is currently blocked by IBM Container Registry policy assignment permissions in the course account. This is good enough for stakeholder demo access, but the cleaner final path is still a normal GitHub source build or a prebuilt image once IBM enables the required permissions.

## Recommended Path: IBM Cloud Console

The Cloud setup lab marks the IBM Cloud CLI as optional. You do **not** need to run Docker locally to deploy this project if the IBM Cloud Console has access to the GitHub repository and the assigned Code Engine project.

Slack clarification from the general channel matters here:

- Do not create a new Code Engine project. Select the project already assigned to Group 28 / Visa.
- Use region `eu-de`.
- If using the CLI, target the right resource group first. The course threads show this can be the missing step before `ibmcloud ce project select`.
- Do not manually create a Container Registry namespace. IBM indicated in Slack that group namespaces already exist for the course groups.
- Code Engine Applications are the right fit for HTTP apps. Avoid making raw TCP services, such as a self-hosted PostgreSQL port, part of the final critical path.

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
11. Set environment variables for the final real-model proof:

```text
MODEL_PROVIDER=watsonx
APP_MODE=streamlit
WATSONX_URL=https://eu-de.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<project-id>
WATSONX_MODEL_ID=ibm/granite-4-h-small
```

Store `WATSONX_APIKEY` as a Code Engine secret. Use `MODEL_PROVIDER=mock` only for rehearsal or quota-failure fallback.

After deployment, open the generated Code Engine application URL. This should load the Streamlit consultant cockpit.

For API/Orchestrate integration mode, create or update the application with:

```text
MODEL_PROVIDER=watsonx
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
ibmcloud target -g group28

ibmcloud ce project select --name <group-use-case-project>
ibmcloud ce application create \
  --name visa-synthetic-research-copilot \
  --build-source . \
  --port 8080 \
  --env MODEL_PROVIDER=watsonx \
  --env APP_MODE=streamlit \
  --env WATSONX_URL=https://eu-de.ml.cloud.ibm.com \
  --env WATSONX_PROJECT_ID=<project-id> \
  --env WATSONX_MODEL_ID=ibm/granite-4-h-small
```

For the Group 28 deployment helper:

```powershell
.\scripts\deploy_code_engine.ps1 -ProjectName <group-28-visa-code-engine-project> -Mode streamlit
```

Use `-Mode api` if the deployment is meant to be imported into watsonx Orchestrate as an OpenAPI tool.

This helper is optional. It exists for repeatable deployment once the IBM Cloud CLI is installed, but the browser console path above is enough for the course workflow.

For watsonx.ai-backed runs, configure the same environment variables used locally. This is the recommended setting for the final real-model proof:

```bash
ibmcloud ce secret create \
  --name watsonx-runtime-env \
  --format generic \
  --from-env-file watsonx_code_engine.env

ibmcloud ce application update \
  --name visa-synthetic-research-copilot \
  --env MODEL_PROVIDER=watsonx \
  --env-from-secret watsonx-runtime-env
```

Store `WATSONX_APIKEY` as a Code Engine secret rather than committing it to the repository.

Before presenting, open the app sidebar and confirm it shows `Real LLM ready: ibm/granite-4-h-small` rather than the mock fallback warning. The `/health` endpoint also exposes `watsonx_configured: true` without leaking secrets.

## Verified Runtime-Clone Fallback

If GitHub source build fails because Code Engine cannot assign the required Container Registry policies, the following fallback can still expose the Streamlit demo from the cloud. It starts from the public `python:3.12-slim` image, downloads the public GitHub repo at container start, installs dependencies, and launches Streamlit.

Do not set an environment variable named `PORT`; Code Engine reserves it.
The Dockerfile uses `APP_PORT` internally for this reason.

```bash
ibmcloud target -r eu-de -g group28
ibmcloud ce project select --name group28

APP_SCRIPT="python -c \"import urllib.request,zipfile,os,shutil; urllib.request.urlretrieve('https://github.com/ZihaoLu001/visa-synthetic-research-copilot/archive/refs/heads/main.zip','/tmp/app.zip'); zipfile.ZipFile('/tmp/app.zip').extractall('/tmp'); shutil.rmtree('/app', ignore_errors=True); os.rename('/tmp/visa-synthetic-research-copilot-main','/app')\" && cd /app && pip install --no-cache-dir -r requirements.txt && streamlit run app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true"

ibmcloud ce app create \
  --name visa-synthetic-research-copilot \
  --image python:3.12-slim \
  --port 8080 \
  --command /bin/sh \
  --argument=-c \
  --argument "$APP_SCRIPT" \
  --env MODEL_PROVIDER=watsonx \
  --env-from-secret watsonx-runtime-env \
  --env APP_MODE=streamlit \
  --cpu 1 \
  --memory 4G \
  --ephemeral-storage 2G \
  --min-scale 0 \
  --max-scale 1 \
  --visibility public \
  --wait \
  --wait-timeout 900
```

Known source-build blocker observed on 2026-05-04:

```text
FAILED The permission to assign required policies to the service ID, which is used to access the requested IBM Container Registry location, is insufficient.
Trace ID: codeengine-cli-di8dq00g89
```

Ask IBM to grant the Group 28 Code Engine project the needed Container Registry/service ID policy assignment permission, or to provide a preconfigured build output / registry secret for `group28`.

For a separate API app, use the same fallback pattern but start `uvicorn` instead of Streamlit:

```bash
APP_SCRIPT="python -c \"import urllib.request,zipfile,os,shutil; urllib.request.urlretrieve('https://github.com/ZihaoLu001/visa-synthetic-research-copilot/archive/refs/heads/main.zip','/tmp/app.zip'); zipfile.ZipFile('/tmp/app.zip').extractall('/tmp'); shutil.rmtree('/app', ignore_errors=True); os.rename('/tmp/visa-synthetic-research-copilot-main','/app')\" && cd /app && pip install --no-cache-dir -r requirements.txt && uvicorn api:app --host 0.0.0.0 --port 8080"

ibmcloud ce app create \
  --name visa-synthetic-research-api \
  --image python:3.12-slim \
  --port 8080 \
  --command /bin/sh \
  --argument=-c \
  --argument "$APP_SCRIPT" \
  --env MODEL_PROVIDER=watsonx \
  --env-from-secret watsonx-runtime-env \
  --env APP_MODE=api \
  --cpu 1 \
  --memory 4G \
  --ephemeral-storage 2G \
  --min-scale 0 \
  --max-scale 1 \
  --visibility public \
  --wait \
  --wait-timeout 900
```

## watsonx Orchestrate Integration Asset

This repo includes two lightweight assets for the IBM platform story:

- `orchestrate/agents/visa_synthetic_research_copilot.yaml`: minimal ADK agent specification for explaining the coordinator-agent role.
- `orchestrate/openapi/visa_synthetic_research_api.yaml`: OpenAPI contract for calling the deployed `/run` API from Orchestrate or Agent Builder.

Recommended final-demo stance:

1. Use Streamlit on Code Engine for the primary visual demo.
2. Use the API/OpenAPI asset as the integration proof for Orchestrate.
3. Avoid making Orchestrate custom Python tool deployment the critical path, because Slack reports show several teams hitting dependency and permission issues.

The 2026-04-27 and 2026-05-02 Slack thread is the key risk signal: standalone Orchestrate agents can deploy, but agents that attach custom Python tools with dependencies can fail during tool deployment. Calling this repo's deployed FastAPI endpoint as an OpenAPI tool is therefore the lower-risk IBM-platform integration route for final delivery.

## Demo Positioning

- The verified Code Engine URL is the primary stakeholder-sharing path.
- Local Streamlit remains the fallback if the course account hits quota or network issues.
- The verified API Code Engine URL is the Orchestrate-tool path.
- Keep `MODEL_PROVIDER=mock` available for rehearsal and fallback, but the current cloud apps are configured for `MODEL_PROVIDER=watsonx`.
