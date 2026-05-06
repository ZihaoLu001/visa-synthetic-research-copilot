# Real watsonx.ai Model Runbook

Use this checklist when the team wants to prove that the system is calling a real IBM foundation model rather than the deterministic fallback.

## Required Configuration

Create a local `.env` file from `.env.example` or configure the same values as Code Engine environment variables/secrets:

```bash
MODEL_PROVIDER=watsonx
WATSONX_URL=https://eu-de.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<watsonx.ai-project-id>
WATSONX_APIKEY=<ibm-cloud-api-key>
WATSONX_MODEL_ID=ibm/granite-4-h-small
```

Do not commit `.env` or any API key. The repository `.gitignore` already excludes `.env` and `.streamlit/secrets.toml`.

## Local Smoke Test

Run:

```powershell
python scripts/watsonx_smoke_test.py
```

Expected result:

- `configured: true`
- `model_id: ibm/granite-4-h-small`
- A short live response from watsonx.ai

For a tiny end-to-end LLM-backed run:

```powershell
python scripts/watsonx_smoke_test.py --mini-run
```

This uses the same survey parser and persona respondent stack as the app, but with only a small panel to avoid unnecessary quota usage.

Verified Group 28 status on 2026-05-06:

- `python scripts/watsonx_smoke_test.py` returned a live IBM Granite response.
- `python scripts/watsonx_smoke_test.py --mini-run` completed an end-to-end run with `provider: watsonx`, 2 parsed questions, 12 synthetic responses, aggregate concept summary, and validation output.

## Streamlit App Proof

Start:

```powershell
streamlit run app.py
```

In the sidebar:

1. Select `watsonx`.
2. Confirm the sidebar says `Real LLM ready: ibm/granite-4-h-small`.
3. Run a small panel first, then increase respondents for the final demo.

If the sidebar reports missing credentials, the app is not using the real IBM model yet.

## Quota Troubleshooting

If the smoke test returns `403 token_quota_reached`, the credentials and Project ID are valid but the IBM watsonx.ai Runtime quota for text generation is exhausted or set to zero. This is a platform/account issue, not an application bug. Ask the IBM course team to restore quota for the Group 28 Runtime, or confirm another supported runtime/model for the final real-model proof.

Group 28 hit this issue on 2026-05-06. IBM restored/upgraded the runtime quota, after which the same configuration succeeded without code or credential changes.

## Code Engine Proof

Set normal environment variables for non-secret values and store the API key as a Code Engine secret.

The public `/health` endpoint returns a safe status object:

```json
{
  "watsonx_configured": true,
  "watsonx_model_id": "ibm/granite-4-h-small"
}
```

Never expose `WATSONX_APIKEY` in screenshots, Slack messages, docs, or logs.

## Talk Track

Use this exact wording:

> The production path uses IBM watsonx.ai with Granite through the same provider abstraction. Mock mode exists only as a deterministic fallback for CI and quota failures. For this proof, the sidebar and smoke-test output confirm that watsonx is configured and the run is using the real model provider.
