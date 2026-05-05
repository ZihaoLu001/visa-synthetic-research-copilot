from pathlib import Path

from synthetic_researcher.consulting import build_decision_brief, default_research_brief, format_decision_brief_markdown
from synthetic_researcher.llm import MockLLM
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.reporting import build_markdown_report

ROOT = Path(__file__).resolve().parents[1]


def test_offline_run_completes():
    orch = SyntheticResearchOrchestrator(
        llm=MockLLM(),
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orch.run(
        survey_path=ROOT / "data" / "sample_survey_card.yaml",
        concepts_path=ROOT / "data" / "sample_concepts.yaml",
        micro_population_n=12,
        consistency_runs=2,
    )
    assert run.responses
    assert run.aggregate["concept_summary"]
    assert run.validation["benchmark_alignment"]["score"] is not None
    assert run.validation["benchmark_alignment"]["profiles"]
    assert run.validation["overall"]["score"] >= 80
    assert run.validation["realism_rubric"]["score"] >= 85
    assert run.validation["question_coverage"]["score"] == 100
    assert run.aggregate["price_summary"]
    assert run.aggregate["runtime"]["json_parse_success_rate"] == 100.0
    report = build_markdown_report(run)
    assert report.startswith("# Visa Synthetic Research Copilot Report")
    assert "## Input Source" in report
    assert "## KPI Evidence" in report

    brief = default_research_brief()
    run.aggregate["provider"] = "mock"
    run.aggregate["research_brief"] = brief
    run.aggregate["decision_brief"] = build_decision_brief(run, brief, provider="mock")
    assert run.aggregate["decision_brief"]["concept_matrix"]
    assert "Decision Brief" in build_markdown_report(run)
    assert "Methodology Snapshot" in format_decision_brief_markdown(run)


def test_parser_handles_new_survey_text():
    llm = MockLLM()
    questions = llm.generate_json(
        "Parse the raw survey into JSON.\nRAW_SURVEY:\n"
        "1. Would you trust a card that suggests the cheapest payment method at checkout?\n"
        "2. What annual fee in CHF would you pay?\n"
        "3. What concern would stop you from using it?"
    )
    assert [q["type"] for q in questions] == ["likert", "price", "open"]
    assert questions[2]["measures"] == "barriers"


def test_parser_recognizes_concept_test_rating_language():
    llm = MockLLM()
    questions = llm.generate_json(
        "Parse the raw survey into JSON.\nRAW_SURVEY:\n"
        "1. How appealing is this card concept overall?\n"
        "2. How often would you use it for everyday payments?\n"
        "3. How innovative is the product?"
    )

    assert [q["type"] for q in questions] == ["likert", "likert", "likert"]
    assert all(q["measures"] == "adoption likelihood" for q in questions)


def test_parser_extracts_external_concept_test_options():
    llm = MockLLM()
    questions = llm.generate_json(
        "Parse the raw survey into JSON.\nRAW_SURVEY:\n"
        "Source: Public payment survey example.\n"
        "URL: https://example.com/survey\n"
        "Use in this demo: metadata only.\n"
        "Scenario: Early-stage Swiss card value proposition concept test.\n"
        "1. Which benefit would make you switch first? "
        "Options: cashback; travel insurance; purchase protection; mobile wallet; none\n"
        "2. Rank the following features: FX waiver / lounge access / fraud alerts / grocery cashback\n"
        "3. Which of the following would be your biggest concern: privacy, annual fee, setup effort, no clear need"
    )

    assert [q["type"] for q in questions] == ["choice", "choice", "choice"]
    assert len(questions) == 3
    assert questions[0]["options"] == [
        "cashback",
        "travel insurance",
        "purchase protection",
        "mobile wallet",
        "none",
    ]
    assert questions[1]["options"] == ["FX waiver", "lounge access", "fraud alerts", "grocery cashback"]
    assert questions[2]["measures"] == "barriers"


def test_parser_keeps_pdf_wrapped_question_lines_together():
    llm = MockLLM()
    questions = llm.generate_json(
        "Parse the raw survey into JSON.\nRAW_SURVEY:\n"
        "1. How confident are you in your ability to understand and navigate the technology and features\n"
        "of your mobile phone?\n"
        "Options: very confident; somewhat confident; not confident\n"
        "2. Have you made a mobile payment in the past 12 months?\n"
        "Options: yes; no"
    )

    assert len(questions) == 2
    assert questions[0]["text"].endswith("of your mobile phone?")
    assert questions[0]["options"] == ["very confident", "somewhat confident", "not confident"]


def test_choice_agent_uses_real_options_instead_of_generic_labels():
    llm = MockLLM()
    prompt = """
You are not an assistant. You are a synthetic survey respondent.
PERSONA:
Persona A4_01 - Geneva Premium Frequent Traveler
CONCEPT:
Name: Premium Travel Card
Description: Travel card for Swiss consumers
Annual fee CHF: 120
Features: ['travel insurance', 'FX waiver', 'lounge vouchers', 'purchase protection']
Target context: Swiss consumer card value proposition
QUESTION:
ID: Q1
Type: choice
Text: Which benefit would make you switch first?
Options: ['cashback', 'travel insurance', 'purchase protection', 'mobile wallet', 'none']
Measures: feature preference
"""

    answer = llm.generate_json(prompt)

    assert answer["answer_label"] in {"travel insurance", "purchase protection"}
    assert answer["answer_label"] not in {"Concept A", "Concept B", "Neither"}
