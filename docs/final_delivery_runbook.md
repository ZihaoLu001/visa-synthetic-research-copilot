# Final Delivery Runbook

This is the practical checklist for Team 1 / Group 28.

## Confirmed Logistics

- Use case: Visa / Multi-Agent Synthetic Researcher
- Team: Team 1 / Group 28
- Date: 26 May 2026
- Slot: 19:15-19:40
- Room: 04404
- Venue: IBM Schweiz AG, Vulkanstrasse 106, 8048 Zurich

## Recommended Delivery Stack

| Layer | Status | Why |
| --- | --- | --- |
| Streamlit cockpit | Primary demo | Best for the 5-point working demo rubric: paste/upload survey, run agents, inspect insights, validation, and exports. |
| Mock provider | Required fallback | Protects the live demo from quota, network, or platform issues. |
| watsonx.ai provider | IBM model proof | Shows IBM ecosystem use when credentials and quota are available. |
| GitHub source / Code Engine | Deployment proof | Matches the Code Engine lab and lets stakeholders open the app without local setup. |
| FastAPI `/run` | Integration proof | Lets Orchestrate or another IBM workflow trigger a synthetic research run. |
| watsonx Orchestrate ADK | Extension proof | Useful for architecture and Q&A, but should not replace the reliable Streamlit demo unless deployment is confirmed. |

## Do Before The Next Q&A

1. Ask the questions in `docs/partner_questions.md`.
2. Confirm the exact Code Engine project name and whether Group 28 has Container Registry/build permissions.
3. Confirm whether Visa can provide one representative survey/interview guide.
4. Confirm whether they expect Orchestrate to be part of the live runtime or just the architecture story.

## Do Before The Final Rehearsal

1. Run local Streamlit:

   ```powershell
   streamlit run app.py
   ```

2. Run local API:

   ```powershell
   uvicorn api:app --host 0.0.0.0 --port 8080
   ```

3. Run tests:

   ```powershell
   python -m pytest -q
   ```

4. Practice this live sequence:

   - Paste a new survey question live.
   - Run 48 or 96 respondents.
   - Show Question Parser.
   - Show Consultant Summary.
   - Show Segment Explorer.
   - Show Persona Responses.
   - Show Validation and Scorecard.
   - Change fee or protection messaging, rerun, and explain the movement.

## Code Engine Execution

Preferred browser path:

1. Open IBM Cloud in the browser.
2. Go to Code Engine in region `eu-de`.
3. Select the Visa / Group 28 Code Engine project.
4. Create an application from GitHub source:

   ```text
   https://github.com/ZihaoLu001/visa-synthetic-research-copilot
   ```

5. Use branch `main`, port `8080`, and the included `Dockerfile`.
6. Set:

   ```text
   MODEL_PROVIDER=mock
   APP_MODE=streamlit
   ```

7. Open the generated application URL and run the demo.

CLI path, only if the IBM Cloud CLI is installed:

```powershell
ibmcloud login --sso
.\scripts\deploy_code_engine.ps1 -ProjectName <group-28-visa-project-name> -Mode streamlit
```

For Orchestrate/API integration:

```powershell
.\scripts\deploy_code_engine.ps1 -ProjectName <group-28-visa-project-name> -Mode api
```

Then replace the `servers[0].url` value in `orchestrate/openapi/visa_synthetic_research_api.yaml` with the Code Engine application URL before importing the OpenAPI tool into watsonx Orchestrate.

## Risk Controls

- Keep local Streamlit ready even if Code Engine fails.
- Keep `MODEL_PROVIDER=mock` ready even if watsonx.ai quota is exhausted.
- Do not commit `.env`, API keys, Slack codes, meeting passwords, or private Visa data.
- Treat synthetic output as directional and validation-ready, not as real customer evidence.
