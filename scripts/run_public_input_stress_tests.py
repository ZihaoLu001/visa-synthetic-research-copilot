from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synthetic_researcher.consulting import build_decision_brief, default_research_brief
from synthetic_researcher.ingestion import extract_survey_text
from synthetic_researcher.llm import get_llm, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.pdf_report import build_consultant_pdf_report
from synthetic_researcher.schemas import Concept

STRESS_DIR = ROOT / "demo" / "stress_tests"
RAW_DIR = STRESS_DIR / "inputs_raw"
INPUT_DIR = STRESS_DIR / "run_inputs"
OUTPUT_DIR = STRESS_DIR / "outputs"
INDEX_MD = STRESS_DIR / "stress_test_index.md"
INDEX_JSON = STRESS_DIR / "stress_test_index.json"

VISA_BLUE = colors.HexColor("#1434cb")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#64748b")


@dataclass(frozen=True)
class StressCase:
    case_id: str
    title: str
    source_name: str
    source_url: str
    raw_file: str
    run_input_file: str
    output_file: str
    proposition: Concept
    survey_excerpt: str
    why_vca_might_use_it: str


CASES = [
    StressCase(
        case_id="01_ecb_space_payment_attitudes",
        title="ECB SPACE 2024 payment attitudes questionnaire slice",
        source_name="European Central Bank, Study on the payment attitudes of consumers in the euro area (SPACE) 2024, Annex A",
        source_url="https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_a.en.pdf",
        raw_file="ecb_space_2024_annex_a_survey_questionnaire.pdf",
        run_input_file="01_ecb_space_payment_attitudes_input.pdf",
        output_file="01_ecb_space_payment_attitudes_output_watsonx.pdf",
        proposition=Concept(
            id="P1",
            name="Swiss Payment Choice Companion",
            description=(
                "A bank-issued Visa payment companion that helps Swiss consumers understand payment-method acceptance, "
                "avoid failed checkout moments, compare cash/card/mobile choices, and keep final control over how they pay."
            ),
            annual_fee_chf=0.0,
            features=[
                "payment-method acceptance guidance",
                "backup method suggestions when cash/card/mobile is not accepted",
                "technical-issue fallback prompts",
                "customer keeps final choice",
            ],
            target_context="Swiss consumers across payment-method preference, age, income and language-region segments",
        ),
        survey_excerpt=dedent(
            """
            Source-derived survey module: payment method availability, acceptance and friction.

            Q1. Which of the following do you have?
            Options: bank account from which you can make payments; payment card; mobile phone or wearable from which you can make payments through an app; none of the above.

            Q2. Think about payments made during the past month at physical locations. Did the merchant or payee always offer the payment method that you wanted to use?
            Options: wanted cash but it was not accepted; wanted card or mobile payment but it was not accepted; card/mobile accepted only above a certain amount; yes; no payments at physical locations.

            Q3. While paying at a physical location in the past month, have you had any technical issues with the payment methods used?
            Options: issue with card payment; issue with mobile phone payment; issue paying cash at self-service cash register; no issues.

            Q4. How important is it to you that your preferred payment method is accepted when you shop in physical locations?
            Scale: 1 not important to 5 very important.

            Q5. What is the main reason you would or would not trust a payment companion that recommends a suitable payment method at checkout?
            """
        ).strip(),
        why_vca_might_use_it=(
            "Tests whether the app can process a central-bank payment-attitudes questionnaire and convert acceptance, "
            "friction and trust questions into segment-level guidance for a payment value proposition."
        ),
    ),
    StressCase(
        case_id="02_federal_reserve_mobile_payments",
        title="Federal Reserve mobile financial services questionnaire slice",
        source_name="US Federal Reserve, Consumers and Mobile Financial Services, 2014 questionnaire",
        source_url="https://www.federalreserve.gov/consumerscommunities/files/mobilefinancial_2014questionnaire.pdf",
        raw_file="federal_reserve_2014_mobile_financial_services_questionnaire.pdf",
        run_input_file="02_federal_reserve_mobile_payments_input.pdf",
        output_file="02_federal_reserve_mobile_payments_output_watsonx.pdf",
        proposition=Concept(
            id="P1",
            name="Mobile Payment Confidence Proposition",
            description=(
                "A Visa-enabled mobile payment support layer that explains security, supports person-to-person and online payments, "
                "surfaces fees/protection before checkout, and reduces uncertainty for mobile-first and hesitant customers."
            ),
            annual_fee_chf=0.0,
            features=[
                "mobile payment security explanation",
                "P2P and online checkout support",
                "fee and protection transparency",
                "privacy and fraud-control messaging",
            ],
            target_context="Swiss consumers with different mobile-payment adoption, security concern and digital-openness profiles",
        ),
        survey_excerpt=dedent(
            """
            Source-derived survey module: mobile payment activity, barriers and security perception.

            Q1. Have you made a mobile payment in the past 12 months?
            Options: yes; no.

            Q2. Using your mobile phone, which activities have you done in the past 12 months?
            Options: transferred money to another person; sent a remittance; received money from another person; paid for a product or service; paid a bill; made a charitable donation.

            Q3. What is the main reason you started using or would start using mobile payments?
            Options: convenience; bank offered the service; security confidence; fraud alerts/control; no nearby branch or ATM; other.

            Q4. What is the main concern that could prevent you from using mobile payments more often?
            Options: security of personal information; privacy; setup complexity; lack of merchant acceptance; no clear need; fear of errors.

            Q5. How safe do you believe your personal information is when using mobile banking or mobile payments?
            Scale: 1 not safe to 5 very safe.
            """
        ).strip(),
        why_vca_might_use_it=(
            "Stress-tests a mobile-payment survey input, especially trust, security, mobile wallet and transaction-use cases "
            "that are common in payment proposition design."
        ),
    ),
    StressCase(
        case_id="03_fca_financial_lives_payments_trust",
        title="FCA Financial Lives 2024 payments and digital trust questionnaire slice",
        source_name="UK Financial Conduct Authority, Financial Lives 2024 survey questionnaire",
        source_url="https://www.fca.org.uk/publication/financial-lives/financial-lives-survey-2024-questionnaire.pdf",
        raw_file="fca_financial_lives_2024_questionnaire.pdf",
        run_input_file="03_fca_financial_lives_payments_trust_input.pdf",
        output_file="03_fca_financial_lives_payments_trust_output_watsonx.pdf",
        proposition=Concept(
            id="P1",
            name="Financial Decision Support Proposition",
            description=(
                "A Visa/VCA early-stage proposition for a bank-side financial decision support tool that helps consumers compare "
                "payment choices, understand fees and risk, and decide when they need human support instead of automated guidance."
            ),
            annual_fee_chf=0.0,
            features=[
                "plain-language payment and fee explanations",
                "confidence support for complex financial choices",
                "human-support escalation when trust is low",
                "cash and digital payment inclusion messaging",
            ],
            target_context="Swiss consumers with varying financial confidence, cash preference, digital trust and support needs",
        ),
        survey_excerpt=dedent(
            """
            Source-derived survey module: cash use, payment trust, digital decision support and financial confidence.

            Q1. How often have you used cash rather than other payment methods in your day-to-day life in the last 12 months?
            Options: pay for everything in cash; pay for most things in cash; use cash and other methods equally; occasionally use cash; almost always use other payment methods.

            Q2. If you use cash often, why do you use cash in day-to-day life?
            Options: accepted everywhere; helps budgeting; avoid debt; local businesses prefer cash; avoid extra charges; trust cash more; routine; convenience; privacy; independence; poor internet connection; electronic-payment interruptions.

            Q3. To what extent would you trust computer decision-making to complete financial tasks without human interaction?
            Scale: 0 do not trust at all to 10 trust completely.

            Q4. Thinking about money and financial matters, do any of the following apply to you?
            Options: hard to find suitable financial products; unable to shop around; overwhelmed or stressed; nervous speaking to providers; do not understand products taken out; put off financial decisions.

            Q5. Which financial decisions could you make yourself without support, as opposed to needing expert advice or impartial guidance?
            Options: choosing insurance; building savings buffer; deciding whether to invest; choosing where to invest; taking out or switching a mortgage; none of these.
            """
        ).strip(),
        why_vca_might_use_it=(
            "Stress-tests whether the app handles a broader financial-services questionnaire, where the output should identify "
            "trust, support needs and inclusion risks rather than only card/payment feature preferences."
        ),
    ),
]


def download_sources() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        path = RAW_DIR / case.raw_file
        if path.exists() and path.stat().st_size > 0:
            continue
        response = requests.get(case.source_url, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        path.write_bytes(response.content)


def build_input_pdf(case: StressCase) -> Path:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = INPUT_DIR / case.run_input_file
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("VisaTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=VISA_BLUE))
    styles.add(ParagraphStyle("BodySmall", parent=styles["BodyText"], fontSize=9, leading=12, textColor=INK))
    styles.add(ParagraphStyle("Meta", parent=styles["BodyText"], fontSize=8, leading=10, textColor=MUTED))
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=case.title,
        author="VCA Multi-Agent Synthetic Researcher stress test",
    )
    story = [
        Paragraph(case.title, styles["VisaTitle"]),
        Spacer(1, 5 * mm),
        Paragraph(f"<b>Public source:</b> {case.source_name}", styles["Meta"]),
        Paragraph(f"<b>Source URL:</b> {case.source_url}", styles["Meta"]),
        Paragraph(f"<b>Why VCA might use it:</b> {case.why_vca_might_use_it}", styles["Meta"]),
        Spacer(1, 7 * mm),
        Paragraph("<b>Uploaded input artifact for synthetic respondent agents</b>", styles["Heading2"]),
        Paragraph(case.survey_excerpt.replace("\n", "<br/>"), styles["BodySmall"]),
        Spacer(1, 6 * mm),
        Paragraph(
            "Note: this pressure-test artifact is a short, source-derived slice used to conserve classroom watsonx quota. "
            "The original public PDF is preserved in inputs_raw.",
            styles["Meta"],
        ),
    ]
    doc.build(story)
    return path


def run_case(case: StressCase, respondents: int, provider: str) -> dict[str, object]:
    input_pdf = build_input_pdf(case)
    extracted = extract_survey_text(input_pdf.name, input_pdf.read_bytes())

    llm = get_llm(provider)
    orchestrator = SyntheticResearchOrchestrator(
        llm=llm,
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orchestrator.run(
        raw_survey=extracted.text,
        concepts=[case.proposition],
        micro_population_n=respondents,
        consistency_runs=1,
        input_source={
            **extracted.metadata(),
            "case_id": case.case_id,
            "source_name": case.source_name,
            "source_url": case.source_url,
            "raw_source_file": str((RAW_DIR / case.raw_file).relative_to(ROOT)),
            "why_vca_might_use_it": case.why_vca_might_use_it,
        },
    )
    wx_status = watsonx_config_status()
    active_provider = provider
    run.aggregate["provider"] = active_provider
    run.aggregate["model_id"] = wx_status["model_id"] if active_provider == "watsonx" else "MockLLM"
    run.aggregate["research_brief"] = {
        **default_research_brief(),
        "project_objective": "Stress-test whether the VCA Multi-Agent Synthetic Researcher can process realistic public payment and financial-services survey inputs.",
        "client_decision": "Identify whether the uploaded input can generate useful synthetic Swiss customer perspectives, segment evidence and validation signals.",
        "decision_rule": "Treat outputs as directional if question coverage, persona coverage and realism checks are acceptable, then use the strongest signals to design real customer validation.",
    }
    run.aggregate["decision_brief"] = build_decision_brief(
        run,
        run.aggregate["research_brief"],
        provider=active_provider,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_pdf = OUTPUT_DIR / case.output_file
    output_pdf.write_bytes(build_consultant_pdf_report(run))
    run_json = OUTPUT_DIR / f"{case.case_id}_run.json"
    run_json.write_text(json.dumps(run.asdict(), indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "case_id": case.case_id,
        "title": case.title,
        "source_name": case.source_name,
        "source_url": case.source_url,
        "raw_source_file": str((RAW_DIR / case.raw_file).relative_to(ROOT)),
        "input_pdf": str(input_pdf.relative_to(ROOT)),
        "output_pdf": str(output_pdf.relative_to(ROOT)),
        "run_json": str(run_json.relative_to(ROOT)),
        "provider": active_provider,
        "model_id": run.aggregate["model_id"],
        "run_id": run.run_id,
        "questions_parsed": len(run.questions),
        "responses": len(run.responses),
        "validation_score": run.validation.get("overall", {}).get("score"),
        "question_coverage": run.validation.get("question_coverage", {}).get("score"),
        "realism_score": run.validation.get("realism_rubric", {}).get("score"),
    }


def write_index(results: list[dict[str, object]]) -> None:
    STRESS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Public Input Stress Tests",
        "",
        "These artifacts pressure-test the VCA Multi-Agent Synthetic Researcher against public survey/questionnaire inputs that a Visa/VCA team might use as proxy material for early product and value proposition research.",
        "",
        "| Case | Public source | Input PDF | Output PDF | Model | Responses | Validation |",
        "| --- | --- | --- | --- | --- | ---: | ---: |",
    ]
    for item in results:
        lines.append(
            "| {title} | [source]({source_url}) | `{input_pdf}` | `{output_pdf}` | {model_id} | {responses} | {validation_score} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "The raw downloaded public PDFs are saved under `demo/stress_tests/inputs_raw/`. The run inputs are shorter source-derived slices to keep watsonx quota use reasonable while still exercising PDF upload, parsing, synthetic persona responses, aggregation, validation and report generation.",
        ]
    )
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public survey inputs and generate watsonx PDF reports.")
    parser.add_argument("--respondents", type=int, default=6, help="Synthetic respondents per case; keep small for quota-safe stress tests.")
    parser.add_argument("--provider", choices=["watsonx", "mock"], default="watsonx")
    parser.add_argument("--case", choices=[case.case_id for case in CASES], action="append", help="Run only selected case id(s).")
    args = parser.parse_args()

    os.environ.setdefault("MODEL_PROVIDER", args.provider)
    if args.provider == "watsonx":
        status = watsonx_config_status()
        if not status["configured"]:
            raise RuntimeError(f"watsonx is not configured. Missing: {status['missing']}")

    download_sources()
    selected = [case for case in CASES if not args.case or case.case_id in args.case]
    results = [run_case(case, respondents=args.respondents, provider=args.provider) for case in selected]
    write_index(results)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nIndex: {INDEX_MD}")


if __name__ == "__main__":
    main()
