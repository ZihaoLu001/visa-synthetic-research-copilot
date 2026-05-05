from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synthetic_researcher.llm import LLMError, get_llm, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.reporting import build_markdown_report
from synthetic_researcher.schemas import Concept


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that the project can call a real IBM watsonx.ai model.")
    parser.add_argument(
        "--mini-run",
        action="store_true",
        help="Run a very small end-to-end synthetic survey through watsonx.ai. This uses multiple model calls.",
    )
    args = parser.parse_args()

    status = watsonx_config_status()
    print("watsonx configuration:")
    print(json.dumps(_public_status(status), indent=2))
    if not status["configured"]:
        print("\nMissing required watsonx configuration. Add these to .env or environment variables:")
        for key in status["missing"]:
            print(f"- {key}")
        return 2

    try:
        llm = get_llm("watsonx")
        prompt = (
            "Return one short JSON object only, with keys provider, model_check, and message. "
            "The provider must be 'watsonx'. The message should say this is a live IBM Granite smoke test."
        )
        text = llm.generate_text(prompt)
        print("\nLive watsonx response:")
        print(text.strip()[:1200])

        if args.mini_run:
            _mini_run(llm)
    except LLMError as exc:
        print(f"\nwatsonx smoke test failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - cloud/network failure path
        print(f"\nUnexpected watsonx smoke test failure: {exc}")
        return 1
    return 0


def _mini_run(llm) -> None:
    orchestrator = SyntheticResearchOrchestrator(
        llm=llm,
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    concept = Concept(
        id="A",
        name="Everyday Cashback Card",
        description="A Swiss everyday card with transparent annual fee, grocery cashback and purchase protection.",
        annual_fee_chf=60,
        features=["grocery cashback", "purchase protection", "mobile wallet", "transparent fees"],
        target_context="Swiss consumer card value proposition",
    )
    run = orchestrator.run(
        raw_survey=(
            "1. How likely would you be to adopt this card if it were offered by your bank?\n"
            "2. What annual fee in CHF would feel acceptable for this card?"
        ),
        concepts=[concept],
        micro_population_n=6,
        consistency_runs=1,
        input_source={
            "source": "watsonx_smoke_test",
            "file_name": None,
            "file_type": "text",
            "char_count": 139,
        },
    )
    run.aggregate["provider"] = "watsonx"
    print("\nMini synthetic run:")
    print(json.dumps({
        "run_id": run.run_id,
        "questions": [q.__dict__ for q in run.questions],
        "response_count": len(run.responses),
        "concept_summary": run.aggregate.get("concept_summary"),
        "validation": run.validation.get("overall"),
        "report_preview": build_markdown_report(run).splitlines()[:12],
    }, indent=2, ensure_ascii=False))


def _public_status(status: dict[str, object]) -> dict[str, object]:
    return {
        "configured": status["configured"],
        "missing": status["missing"],
        "url": status["url"],
        "project_id_set": status["project_id_set"],
        "api_key_set": status["api_key_set"],
        "model_id": status["model_id"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
