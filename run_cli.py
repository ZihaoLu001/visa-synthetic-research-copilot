from __future__ import annotations

import json
from pathlib import Path

from synthetic_researcher.consulting import build_decision_brief, default_research_brief
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
        raw_survey=(
            "1. How relevant is this value proposition for your everyday payment or banking needs?\n"
            "2. What annual fee or monthly price in CHF would feel acceptable, if any?\n"
            "3. Which benefit, service or message feels most valuable to you, and why?\n"
            "4. What is the main barrier or concern that would stop you from using it?"
        ),
        micro_population_n=48,
        consistency_runs=2,
    )
    brief = default_research_brief()
    run.aggregate["provider"] = "mock"
    run.aggregate["research_brief"] = brief
    run.aggregate["decision_brief"] = build_decision_brief(run, brief, provider="mock")
    print(json.dumps({
        "run_id": run.run_id,
        "aggregate": run.aggregate,
        "validation": run.validation,
        "first_5_responses": [r.asdict() for r in run.responses[:5]],
        "markdown_report_preview": build_markdown_report(run).splitlines()[:18],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
