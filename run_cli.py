from __future__ import annotations

import json
from pathlib import Path

from synthetic_researcher.llm import get_llm
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.reporting import build_markdown_report

ROOT = Path(__file__).resolve().parent


def main() -> None:
    llm = get_llm()
    orchestrator = SyntheticResearchOrchestrator(
        llm=llm,
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orchestrator.run(
        survey_path=ROOT / "data" / "sample_survey_card.yaml",
        concepts_path=ROOT / "data" / "sample_concepts.yaml",
        micro_population_n=48,
        consistency_runs=2,
    )
    print(json.dumps({
        "run_id": run.run_id,
        "aggregate": run.aggregate,
        "validation": run.validation,
        "first_5_responses": [r.asdict() for r in run.responses[:5]],
        "markdown_report_preview": build_markdown_report(run).splitlines()[:18],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
