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

## Synthetic Customer Product Pattern

Visa's kickoff slide linked Bain's synthetic-customer article as a clue for the desired product direction. The main implication is that the product should not look like a generic chatbot or a fixed A/B card tester. It should operate as a customer-perspective workbench for early innovation decisions: bring simulated customer viewpoints into proposition design earlier, keep the customer voice traceable, and make the path to real validation explicit.

Product decisions applied in this repo:

- Keep the survey, interview guide or value proposition as the input artifact.
- Make the core output a synthetic customer board, decision drivers, objections to probe, messages to test and real-customer validation bridge.
- Preserve persona-level evidence so consultants can inspect the synthetic "customer voice" behind each aggregate signal.
- Treat all outputs as directional learning, with benchmark alignment and consistency checks before any recommendation is used.

Useful source:

- Bain, "How Synthetic Customers Bring Companies Closer to the Real Ones": <https://www.bain.com/insights/how-synthetic-customers-bring-companies-closer-to-the-real-ones/>

## Product Design Implications From External Projects

The latest product layer borrows the useful pattern from persona-simulation projects without copying their scope:

- Stanford's Generative Agents paper motivates memory, reflection and consistency as core design patterns for believable agent behavior. In this repo, persona context plus prior answers gives each respondent a stable point of view across the survey.
- Product scope stays anchored to Visa's own brief: Swiss persona design, persona agents that answer survey/interview inputs, aggregated and persona-level output, and validation against public benchmarks. In this repo, that maps to the customer perspective board, need states, objections, message tests, decision drivers, time/cost advantage and real-customer bridge.
- Microsoft's TinyTroupe shows that LLM-powered persona simulation can be useful for business insight work, but also highlights the importance of empirical validation against real survey data. In this repo, that maps to benchmark alignment, realism review and the new real-customer validation plan.
- OASIS / Open Agentic Survey Interview System is a useful reference for structured survey protocols and searchable transcripts. In this repo, the equivalent product surface is uploaded survey ingestion, parsed question audit, persona-level response tables and exportable evidence.
- The 2026 reliability paper is the most important caveat: persona-conditioned LLMs can introduce subgroup distortion. That is why the product now includes a Consultant Quality Layer with evidence grade, decision risk, risk flags and survey repair recommendations instead of pretending every synthetic run is decision-ready.

Useful sources:

- Generative Agents, arXiv 2304.03442: <https://arxiv.org/abs/2304.03442>
- Microsoft TinyTroupe: <https://github.com/microsoft/TinyTroupe>
- OASIS, Open Agentic Survey Interview System: <https://oasis-surveys.github.io/>
- Assessing the Reliability of Persona-Conditioned LLMs as Synthetic Survey Respondents, arXiv 2602.18462: <https://arxiv.org/abs/2602.18462>
