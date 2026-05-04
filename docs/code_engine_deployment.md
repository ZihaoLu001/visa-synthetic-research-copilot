# IBM Code Engine Deployment

The course labs describe IBM Code Engine as the easiest way to expose a working PoC to stakeholders as a managed application. This repo includes a minimal Dockerfile so the Streamlit cockpit can be deployed without changing the product code.

## Local Container Smoke Test

```bash
docker build -t visa-synthetic-research-copilot .
docker run --rm -p 8080:8080 visa-synthetic-research-copilot
```

Then open:

```text
http://localhost:8080
```

## IBM Cloud Code Engine Sketch

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
  --env MODEL_PROVIDER=mock
```

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

## Demo Positioning

- Local Streamlit is the reliable live-demo path.
- Code Engine is the stakeholder-sharing path if the team wants a public or partner-facing URL.
- Keep `MODEL_PROVIDER=mock` available for rehearsal and fallback.
