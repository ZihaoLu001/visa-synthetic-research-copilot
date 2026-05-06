from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from synthetic_researcher.consulting import build_decision_brief, default_research_brief
from synthetic_researcher.llm import get_llm, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.schemas import Concept


class ConceptPayload(BaseModel):
    id: str = Field(..., examples=["concept_a"])
    name: str = Field(..., examples=["Everyday Cashback Card"])
    description: str
    annual_fee_chf: float = 0.0
    features: list[str] = Field(default_factory=list)
    target_context: str = "Swiss consumer card value proposition"


class ResearchRunRequest(BaseModel):
    survey_text: str = Field(
        ...,
        description="Flexible survey, interview guide, or proposition test text.",
        min_length=8,
    )
    concepts: list[ConceptPayload] | None = None
    micro_population_n: int = Field(12, ge=6, le=96)
    consistency_runs: int = Field(1, ge=1, le=3)
    response_mode: Literal["summary", "full"] = "summary"


app = FastAPI(
    title="Visa Synthetic Research Copilot API",
    version="0.1.0",
    description=(
        "HTTP interface for running benchmark-grounded Swiss synthetic survey research. "
        "The Streamlit app remains the primary consultant cockpit; this API is intended "
        "for IBM Code Engine, watsonx Orchestrate tools, and integration tests."
    ),
)


def _orchestrator() -> SyntheticResearchOrchestrator:
    return SyntheticResearchOrchestrator(
        llm=get_llm(),
        persona_path="data/swiss_archetypes.yaml",
        benchmark_path="data/benchmark_snb_2025.yaml",
    )


@app.get("/health")
def health() -> dict[str, object]:
    wx_status = watsonx_config_status()
    provider = "watsonx" if wx_status["configured"] else "mock"
    return {
        "status": "ok",
        "service": "visa-synthetic-research-copilot",
        "active_provider_if_auto": provider,
        "watsonx_configured": wx_status["configured"],
        "watsonx_missing": wx_status["missing"],
        "watsonx_model_id": wx_status["model_id"],
    }


@app.post("/run")
def run_research(request: ResearchRunRequest) -> dict[str, object]:
    concepts = [Concept(**concept.model_dump()) for concept in request.concepts] if request.concepts else None
    run = _orchestrator().run(
        raw_survey=request.survey_text,
        concepts=concepts,
        micro_population_n=request.micro_population_n,
        consistency_runs=request.consistency_runs,
        input_source={
            "source": "api",
            "file_name": None,
            "file_type": "text",
            "char_count": len(request.survey_text),
        },
    )
    wx_status = watsonx_config_status()
    provider_setting = os.getenv("MODEL_PROVIDER", "auto").lower()
    active_provider = "watsonx" if provider_setting == "watsonx" or (provider_setting == "auto" and wx_status["configured"]) else "mock"
    run.aggregate["provider"] = active_provider
    run.aggregate["model_id"] = wx_status["model_id"] if active_provider == "watsonx" else "MockLLM"
    run.aggregate["decision_brief"] = build_decision_brief(run, default_research_brief(), provider=active_provider)
    payload = run.asdict()
    if request.response_mode == "full":
        return payload

    return {
        "run_id": payload["run_id"],
        "concepts": payload["concepts"],
        "questions": payload["questions"],
        "aggregate": payload["aggregate"],
        "validation": payload["validation"],
        "sample_responses": payload["responses"][: min(12, len(payload["responses"]))],
        "response_count": len(payload["responses"]),
    }
