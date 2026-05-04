from __future__ import annotations

import uuid
from dataclasses import asdict
from pathlib import Path

from .agents import InsightAnalystAgent, PersonaAgent, SurveyParserAgent
from .analytics import aggregate_responses
from .llm import BaseLLM
from .sampler import expand_to_micro_population, load_benchmark_context, load_benchmark_data, load_personas, load_yaml
from .schemas import Concept, PersonaResponse, SurveyQuestion, SurveyRun
from .validation import benchmark_alignment, coverage_check, internal_consistency


def load_concepts(path: str | Path) -> list[Concept]:
    return [Concept(**row) for row in load_yaml(path)["concepts"]]


def load_survey(path: str | Path, parser: SurveyParserAgent) -> list[SurveyQuestion]:
    data = load_yaml(path)
    if "questions" in data:
        return [SurveyQuestion(**row) for row in data["questions"]]
    return parser.parse(data["raw_survey"])


class SyntheticResearchOrchestrator:
    def __init__(self, llm: BaseLLM, persona_path: str | Path, benchmark_path: str | Path):
        self.llm = llm
        self.persona_path = persona_path
        self.benchmark_path = benchmark_path
        self.benchmark_context = load_benchmark_context(benchmark_path)
        self.benchmark_data = load_benchmark_data(benchmark_path)

    def run(
        self,
        raw_survey: str | None = None,
        survey_path: str | Path | None = None,
        concepts_path: str | Path | None = None,
        concepts: list[Concept] | None = None,
        micro_population_n: int = 48,
        consistency_runs: int = 2,
    ) -> SurveyRun:
        run_id = str(uuid.uuid4())[:8]
        parser = SurveyParserAgent(self.llm)
        questions = load_survey(survey_path, parser) if survey_path else parser.parse(raw_survey or "")
        concepts = concepts or load_concepts(concepts_path or "data/sample_concepts.yaml")
        archetypes = load_personas(self.persona_path)
        personas = expand_to_micro_population(archetypes, target_n=micro_population_n, seed=42)

        all_runs: list[list[PersonaResponse]] = []
        for repeat in range(max(1, consistency_runs)):
            repeat_run_id = f"{run_id}_r{repeat+1}"
            responses: list[PersonaResponse] = []
            agent = PersonaAgent(self.llm, self.benchmark_context)
            for persona in personas:
                prior_for_persona: list[PersonaResponse] = []
                for concept in concepts:
                    for question in questions:
                        r = agent.answer(repeat_run_id, persona, concept, question, prior_for_persona)
                        responses.append(r)
                        prior_for_persona.append(r)
            all_runs.append(responses)

        primary_responses = all_runs[0]
        aggregate = aggregate_responses(primary_responses)
        aggregate["analyst"] = InsightAnalystAgent.summarize(aggregate)
        validation = {
            "benchmark_alignment": benchmark_alignment(personas, self.benchmark_data),
            "internal_consistency": internal_consistency(all_runs),
            "coverage": coverage_check(personas),
        }
        return SurveyRun(
            run_id=run_id,
            concepts=concepts,
            questions=questions,
            personas=personas,
            responses=primary_responses,
            aggregate=aggregate,
            validation=validation,
        )
