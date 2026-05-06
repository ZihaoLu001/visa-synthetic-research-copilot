from pathlib import Path
from zipfile import ZipFile
import io

from synthetic_researcher.consulting import build_decision_brief, default_research_brief, format_decision_brief_markdown
from synthetic_researcher.agents import SurveyParserAgent
from synthetic_researcher.delivery import build_consultant_delivery_pack, build_pilot_readiness_gate
from synthetic_researcher.llm import BaseLLM, MockLLM, watsonx_config_status
from synthetic_researcher.orchestrator import SyntheticResearchOrchestrator
from synthetic_researcher.pdf_report import build_consultant_pdf_report
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


def test_generate_json_extracts_payload_from_model_commentary():
    class MessyJSONLLM(BaseLLM):
        def generate_text(self, prompt: str) -> str:
            return 'Sure, here is the JSON:\n```json\n{"answer_value": 4, "answer_label": "4/5"}\n```'

    data = MessyJSONLLM().generate_json("Return JSON")

    assert data == {"answer_value": 4, "answer_label": "4/5"}


def test_survey_parser_normalises_real_model_type_labels():
    class CapitalisedTypeLLM(BaseLLM):
        def generate_text(self, prompt: str) -> str:
            return """
            [
              {"id": "1", "text": "How likely would you be to adopt it?", "type": "Likert", "options": null, "measures": null},
              {"id": "2", "text": "What annual fee in CHF is acceptable?", "type": "Numeric", "options": null, "measures": null}
            ]
            """

    questions = SurveyParserAgent(CapitalisedTypeLLM()).parse("ignored")

    assert [question.id for question in questions] == ["Q1", "Q2"]
    assert [question.type for question in questions] == ["likert", "price"]


def test_watsonx_config_status_redacts_secret(monkeypatch):
    monkeypatch.setenv("WATSONX_URL", "https://eu-de.ml.cloud.ibm.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "project-123")
    monkeypatch.setenv("WATSONX_APIKEY", "secret-value-that-must-not-leak")
    monkeypatch.setenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")

    status = watsonx_config_status()

    assert status["configured"] is True
    assert status["missing"] == []
    assert status["api_key_set"] is True
    assert "secret-value" not in str(status)


def test_consultant_delivery_pack_contains_partner_artifacts():
    orch = SyntheticResearchOrchestrator(
        llm=MockLLM(),
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orch.run(
        survey_path=ROOT / "data" / "sample_survey_card.yaml",
        concepts_path=ROOT / "data" / "sample_concepts.yaml",
        micro_population_n=12,
        consistency_runs=1,
    )
    brief = default_research_brief()
    run.aggregate["provider"] = "mock"
    run.aggregate["model_id"] = "MockLLM"
    run.aggregate["research_brief"] = brief
    run.aggregate["decision_brief"] = build_decision_brief(run, brief, provider="mock")

    pack = build_consultant_delivery_pack(run)
    readiness = build_pilot_readiness_gate(run)

    assert any(row["check"] == "Real IBM model proof" for row in readiness)
    with ZipFile(io.BytesIO(pack)) as bundle:
        names = set(bundle.namelist())
        assert {
            "README.md",
            "01_decision_brief.md",
            "02_consultant_report.md",
            "03_persona_responses.csv",
            "04_validation.json",
            "05_full_run.json",
            "06_input_source_audit.json",
            "07_methodology_and_governance.md",
            "08_pilot_readiness_gate.json",
            "09_consultant_report.pdf",
        }.issubset(names)
        csv_text = bundle.read("03_persona_responses.csv").decode("utf-8")
        assert "persona_id" in csv_text
        assert "secret-value" not in bundle.read("05_full_run.json").decode("utf-8")
        assert bundle.read("09_consultant_report.pdf").startswith(b"%PDF")


def test_consultant_pdf_report_is_valid_pdf():
    orch = SyntheticResearchOrchestrator(
        llm=MockLLM(),
        persona_path=ROOT / "data" / "swiss_archetypes.yaml",
        benchmark_path=ROOT / "data" / "benchmark_snb_2025.yaml",
    )
    run = orch.run(
        survey_path=ROOT / "data" / "sample_survey_card.yaml",
        concepts_path=ROOT / "data" / "sample_concepts.yaml",
        micro_population_n=12,
        consistency_runs=1,
    )
    brief = default_research_brief()
    run.aggregate["provider"] = "mock"
    run.aggregate["model_id"] = "MockLLM"
    run.aggregate["research_brief"] = brief
    run.aggregate["decision_brief"] = build_decision_brief(run, brief, provider="mock")

    pdf = build_consultant_pdf_report(run)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 10_000
