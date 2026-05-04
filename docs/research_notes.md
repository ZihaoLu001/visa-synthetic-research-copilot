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
