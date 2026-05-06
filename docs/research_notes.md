# Research and Framework Notes

These sources are useful for the architecture and limitations slides.

## IBM watsonx.ai

The PoC uses a provider abstraction so the same workflow can run with the deterministic mock model or IBM watsonx.ai. IBM's Python SDK exposes `ModelInference` for foundation model text generation, which maps to the `WatsonxLLM` implementation in `synthetic_researcher/llm.py`.

Useful source:

- IBM watsonx.ai Python SDK `ModelInference`: <https://ibm.github.io/watsonx-ai-python-sdk/v1.5.4/fm_model_inference.html>

## IBM watsonx Orchestrate ADK

For a production-style next step, each current Python agent can be exposed as a watsonx Orchestrate agent or tool. The official ADK is designed for building and deploying agents in watsonx Orchestrate.

Useful sources:

- IBM watsonx Orchestrate Developers: <https://www.ibm.com/products/watsonx-orchestrate/developers>
- IBM watsonx Orchestrate ADK GitHub: <https://github.com/IBM/ibm-watsonx-orchestrate-adk>

## LangGraph

LangGraph is a good fit if the team wants durable graph orchestration with explicit nodes for parser, persona respondent, validator, analyst and human review.

Useful source:

- LangGraph repository: <https://github.com/langchain-ai/langgraph>

## Synthetic Survey Research Literature

Synthetic respondents should be presented as directional and benchmarked, not as a drop-in replacement for real humans.

Useful sources:

- Cao et al., "Specializing Large Language Models to Simulate Survey Response Distributions for Global Populations", NAACL 2025: <https://aclanthology.org/2025.naacl-long.162/>
- "Assessing the Reliability of Persona-Conditioned LLMs as Synthetic Survey Respondents", arXiv 2602.18462: <https://arxiv.org/abs/2602.18462>

Slide takeaway:

> Synthetic survey simulation is promising, but reliability depends on calibration, transparency and validation. That is why this PoC includes benchmark alignment, repeated-run consistency, construct coverage and a realism rubric.

## Product Design Implications From External Projects

The latest product layer borrows the useful pattern from persona-simulation projects without copying their scope:

- Stanford's Generative Agents paper motivates memory, reflection and consistency as core design patterns for believable agent behavior. In this repo, persona context plus prior answers gives each respondent a stable point of view across the survey.
- Bain's synthetic-customer framing is the closest business reference for the Visa brief: the aim is not to automate a questionnaire for its own sake, but to move product teams closer to real customer perspectives earlier in proposition design. In this repo, that maps to the Synthetic Customer Lens, Bain-style use-case fit, scenario-design checks, customer board, need states, objections, message tests, scenario moves, time/cost advantage and real-customer bridge.
- Microsoft's TinyTroupe shows that LLM-powered persona simulation can be useful for business insight work, but also highlights the importance of empirical validation against real survey data. In this repo, that maps to benchmark alignment, realism review and the new real-customer validation plan.
- OASIS / Open Agentic Survey Interview System is a useful reference for structured survey protocols and searchable transcripts. In this repo, the equivalent product surface is uploaded survey ingestion, parsed question audit, persona-level response tables and exportable evidence.
- The 2026 reliability paper is the most important caveat: persona-conditioned LLMs can introduce subgroup distortion. That is why the product now includes a Consultant Quality Layer with evidence grade, decision risk, risk flags and survey repair recommendations instead of pretending every synthetic run is decision-ready.

Useful sources:

- Generative Agents, arXiv 2304.03442: <https://arxiv.org/abs/2304.03442>
- Bain, "How Synthetic Customers Bring Companies Closer to the Real Ones": <https://www.bain.com/insights/how-synthetic-customers-bring-companies-closer-to-the-real-ones/>
- Microsoft TinyTroupe: <https://github.com/microsoft/TinyTroupe>
- OASIS, Open Agentic Survey Interview System: <https://oasis-surveys.github.io/>
- Assessing the Reliability of Persona-Conditioned LLMs as Synthetic Survey Respondents, arXiv 2602.18462: <https://arxiv.org/abs/2602.18462>
