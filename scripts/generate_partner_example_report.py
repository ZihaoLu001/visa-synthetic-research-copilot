from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synthetic_researcher.consulting import build_decision_brief, default_research_brief
from synthetic_researcher.ingestion import extract_survey_text
from synthetic_researcher.llm import get_llm, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator, load_concepts
from synthetic_researcher.pdf_report import build_consultant_pdf_report

OUT_DIR = ROOT / "demo" / "partner_examples"
SOURCE_INPUT_PDF = ROOT / "demo" / "public_survey_uploads" / "federal_reserve_mobile_payments_excerpt.pdf"
INPUT_PDF = OUT_DIR / "visa_example_input_public_mobile_payments_survey.pdf"
OUTPUT_PDF = OUT_DIR / "visa_example_output_consultant_report_watsonx.pdf"


def prepare_input_pdf(path: Path) -> None:
    """Copy the public-source survey excerpt into a Slack-ready example folder."""
    if not SOURCE_INPUT_PDF.exists():
        raise FileNotFoundError(f"Missing public survey sample: {SOURCE_INPUT_PDF}")
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_INPUT_PDF, path)


def select_payment_relevant_questions(raw_survey: str, max_questions: int) -> str:
    """Keep the survey preamble and the payment/card-relevant tail questions.

    The input PDF still contains the full public excerpt. The partner example runs a
    quota-friendly slice focused on payment activities, card trust, barriers and fee
    sensitivity so the output report reads like a Visa/VCA proposition test.
    """
    if max_questions <= 0:
        return raw_survey

    import re

    lines = raw_survey.splitlines()
    preamble: list[str] = []
    blocks: list[list[str]] = []
    current: list[str] = []
    seen_question = False

    for line in lines:
        stripped = line.strip()
        is_question_start = bool(re.match(r"^(?:Q\d+|\d+)[\).:-]\s+", stripped, flags=re.I))
        if is_question_start:
            seen_question = True
            if current:
                blocks.append(current)
            current = [line]
        elif seen_question and current:
            current.append(line)
        else:
            preamble.append(line)

    if current:
        blocks.append(current)
    if not blocks:
        return raw_survey

    selected = blocks[-max_questions:]
    return "\n".join(preamble + [line for block in selected for line in block]).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Slack-ready input survey PDF and output consultant PDF report.")
    parser.add_argument("--respondents", type=int, default=12)
    parser.add_argument("--questions", type=int, default=4)
    parser.add_argument("--allow-mock", action="store_true", help="Allow deterministic fallback if watsonx credentials are missing.")
    args = parser.parse_args()

    os.environ.setdefault("MODEL_PROVIDER", "watsonx")
    prepare_input_pdf(INPUT_PDF)
    extracted = extract_survey_text(INPUT_PDF.name, INPUT_PDF.read_bytes())
    raw_survey = select_payment_relevant_questions(extracted.text, args.questions)
    wx_status = watsonx_config_status()
    if not wx_status["configured"] and not args.allow_mock:
        raise RuntimeError(f"watsonx is not configured. Missing: {wx_status['missing']}")

    provider = "watsonx" if wx_status["configured"] else "mock"
    llm = get_llm(provider)
    orchestrator = SyntheticResearchOrchestrator(
        llm=llm,
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orchestrator.run(
        raw_survey=raw_survey,
        concepts=load_concepts(ROOT / "data" / "sample_concepts.yaml"),
        micro_population_n=args.respondents,
        consistency_runs=1,
        input_source={
            **extracted.metadata(),
            "char_count": len(raw_survey),
            "question_limit": args.questions,
            "question_window": "payment_relevant_tail",
            "note": "Partner example generated from the public mobile-finance survey excerpt PDF.",
        },
    )
    brief = default_research_brief()
    run.aggregate["provider"] = provider
    run.aggregate["model_id"] = wx_status["model_id"] if provider == "watsonx" else "MockLLM"
    run.aggregate["research_brief"] = brief
    run.aggregate["decision_brief"] = build_decision_brief(run, brief, provider=provider)
    OUTPUT_PDF.write_bytes(build_consultant_pdf_report(run))
    print(INPUT_PDF)
    print(OUTPUT_PDF)
    print(f"provider={provider} model={run.aggregate['model_id']} responses={run.aggregate.get('response_count')} validation={run.validation.get('overall', {}).get('score')}")


if __name__ == "__main__":
    main()
