from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .schemas import Concept, Persona, PersonaResponse, SurveyRun


def build_synthetic_customer_lens(run: SurveyRun, decision_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Translate survey-agent output into a synthetic-customer workbench view.

    Visa's brief and the Bain reference are about getting closer to customer
    perspectives for early product and value proposition decisions. This lens
    reframes the same evidence as customer-segment intelligence rather than a
    narrow survey-processing artifact.
    """
    decision = decision_context or run.aggregate.get("decision_brief", {})
    aggregate = run.aggregate
    validation = run.validation
    lead_id = decision.get("lead_concept_id")
    runtime = aggregate.get("runtime", {})
    return {
        "positioning": (
            "Synthetic customers are used as an early learning layer for value proposition design: "
            "they help teams explore customer reactions, sharpen hypotheses and design better real "
            "surveys or interviews. They do not replace final customer validation."
        ),
        "bain_alignment": [
            "Start from a real product decision, not from a generic chatbot conversation.",
            "Simulate a portfolio of customer perspectives instead of averaging one generic respondent.",
            "Use synthetic responses to learn faster, then validate the highest-risk assumptions with real customers.",
            "Keep the evidence auditable: personas, benchmarks, input artifact, response rows and validation checks are visible.",
        ],
        "value_proposition_questions": _value_proposition_questions(run),
        "use_case_fit": _use_case_fit(run),
        "scenario_design_check": _scenario_design_check(run),
        "synthetic_customer_board": _segment_board(run),
        "decision_drivers": _decision_drivers(run),
        "scenario_planning_moves": _scenario_planning_moves(run),
        "time_cost_advantage": _time_cost_advantage(runtime, aggregate),
        "real_customer_bridge": _real_customer_bridge(validation, lead_id, aggregate),
    }


def _segment_board(run: SurveyRun) -> list[dict[str, Any]]:
    concept_lookup = {concept.id: concept for concept in run.concepts}
    root_personas = _root_personas(run.personas)
    responses_by_segment: dict[str, list[PersonaResponse]] = defaultdict(list)
    for response in run.responses:
        responses_by_segment[response.persona_id.split("_")[0]].append(response)

    rows: list[dict[str, Any]] = []
    for persona_id, persona in root_personas.items():
        rows.append(_segment_card(persona_id, persona, responses_by_segment.get(persona_id, []), concept_lookup, run.aggregate))
    return rows


def _segment_card(
    root_persona_id: str,
    persona: Persona,
    responses: list[PersonaResponse],
    concept_lookup: dict[str, Concept],
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    concept_scores = {
        concept_lookup.get(concept_id, Concept(concept_id, concept_id, "")).name: score
        for key, score in aggregate.get("segment_fit", {}).items()
        for concept_id, _, segment_id in [key.partition(":")]
        if segment_id == root_persona_id and score is not None
    }
    winner = _best_fit_label(concept_scores, persona)
    label_counts = Counter(str(response.answer_label) for response in responses if response.answer_label)
    rationale_text = " ".join(response.rationale.lower() for response in responses)
    answer_text = " ".join(response.answer_text.lower() for response in responses)
    return {
        "segment": _segment_name(persona),
        "customer_reality": _customer_reality(persona),
        "likely_best_fit": winner,
        "need_state": _need_state(persona),
        "decision_drivers": _top_terms(label_counts, rationale_text, answer_text),
        "objections_to_probe": _objections(persona, rationale_text, answer_text),
        "message_to_test": _message_to_test(persona, winner),
    }


def _best_fit_label(concept_scores: dict[str, float], persona: Persona) -> str:
    if not concept_scores:
        return "No clear winner"
    ranked = sorted(concept_scores.items(), key=lambda item: item[1], reverse=True)
    winner, winner_score = ranked[0]
    if len(ranked) > 1:
        runner_up, runner_up_score = ranked[1]
        gap = winner_score - runner_up_score
        if gap < 0.35:
            return f"Toss-up: {winner} vs {runner_up}"
        if (
            "Travel" in winner
            and "Cashback" in runner_up
            and persona.attitudes.get("price_sensitivity", 0) > 0.7
            and gap < 0.75
        ):
            return f"{winner} only if fee/value proof beats {runner_up}"
    return winner


def _decision_drivers(run: SurveyRun) -> list[dict[str, Any]]:
    labels = run.aggregate.get("top_answer_labels", [])[:6]
    barriers = run.aggregate.get("top_barrier_signals", [])[:6]
    rows = []
    for label, count in labels:
        rows.append({"type": "positive signal", "driver": label, "evidence_count": count})
    for label, count in barriers:
        rows.append({"type": "watchout", "driver": label, "evidence_count": count})
    return rows


def _use_case_fit(run: SurveyRun) -> list[dict[str, str]]:
    question_text = " ".join(question.text.lower() for question in run.questions)
    has_price = any(term in question_text for term in ["fee", "price", "chf", "pay", "willing"])
    has_message = any(term in question_text for term in ["feature", "benefit", "message", "why", "valuable"])
    has_sentiment = any(term in question_text for term in ["likely", "recommend", "satisfied", "nps", "adopt", "trust"])
    has_barrier = any(term in question_text for term in ["barrier", "prevent", "concern", "risk", "trust", "privacy"])
    return [
        {
            "use_case": "Value proposition design",
            "fit": "Strong",
            "how_this_run_supports_it": "Compares feature, fee and benefit reactions across Swiss synthetic customer segments.",
        },
        {
            "use_case": "Persona development and segmentation",
            "fit": "Strong",
            "how_this_run_supports_it": "Turns archetypes into a synthetic customer board with segment need states, objections and messages to test.",
        },
        {
            "use_case": "Marketing and message testing",
            "fit": "Strong" if has_message or has_barrier else "Partial",
            "how_this_run_supports_it": "Identifies the messages, proof points and objections that should be turned into copy cells.",
        },
        {
            "use_case": "Predictive NPS / sentiment proxy",
            "fit": "Partial" if has_sentiment else "Not the primary use in this run",
            "how_this_run_supports_it": "Provides directional adoption/trust sentiment, but should not be read as a final NPS forecast.",
        },
        {
            "use_case": "Frontline objection training",
            "fit": "Partial" if has_barrier else "Next-step opportunity",
            "how_this_run_supports_it": "Uses barrier rationales to prepare objection-handling prompts for advisors or sales teams.",
        },
        {
            "use_case": "Pricing sensitivity",
            "fit": "Strong" if has_price else "Needs explicit pricing cells",
            "how_this_run_supports_it": "Estimates directional fee acceptance and recommends cells for real customer validation.",
        },
    ]


def _scenario_design_check(run: SurveyRun) -> list[dict[str, str]]:
    response_count = len(run.responses)
    persona_roots = len(_root_personas(run.personas))
    question_count = len(run.questions)
    return [
        {
            "principle": "Start from a real decision",
            "status": "Met",
            "evidence": "The run asks which card proposition, fee and messages should advance to real validation.",
        },
        {
            "principle": "Design the bots for the goal",
            "status": "Met",
            "evidence": f"{persona_roots} Swiss archetypes are expanded into micro-personas with demographics, payment behavior and attitudes.",
        },
        {
            "principle": "Use a realistic scenario artifact",
            "status": "Met" if question_count else "Needs survey input",
            "evidence": f"{question_count} parsed survey/interview questions were used as the customer-reaction scenario.",
        },
        {
            "principle": "Make evidence inspectable",
            "status": "Met",
            "evidence": f"{response_count} persona-level responses, segment tables, validation scores and input-source audit are exported.",
        },
        {
            "principle": "Recognize AI limits",
            "status": "Met",
            "evidence": "The report separates directional synthetic learning from real Visa customer validation and calibration.",
        },
    ]


def _value_proposition_questions(run: SurveyRun) -> list[str]:
    question_text = " ".join(question.text.lower() for question in run.questions)
    questions = [
        "Which concept should anchor the next real validation round?",
        "Which Swiss customer segments show the strongest fit or resistance?",
        "Which benefit messages and barriers should be tested with real customers?",
    ]
    if any(term in question_text for term in ["fee", "price", "chf", "pay"]):
        questions.append("Which annual-fee range should be tested in pricing cells?")
    if any(term in question_text for term in ["trust", "privacy", "control", "recommendation"]):
        questions.append("What trust, control or privacy language is needed before launch testing?")
    return questions


def _scenario_planning_moves(run: SurveyRun) -> list[dict[str, str]]:
    concept_names = [concept.name for concept in run.concepts]
    concept_a = concept_names[0] if concept_names else "Concept A"
    concept_b = concept_names[1] if len(concept_names) > 1 else "challenger concept"
    return [
        {
            "move": "Price cell simulation",
            "what_to_change_next": f"Rerun {concept_a} at lower annual-fee cells and compare segment movement against {concept_b}.",
            "why_it_matters": "Separates dislike of the proposition from rejection of the price point.",
        },
        {
            "move": "Message cell simulation",
            "what_to_change_next": "Swap in stronger proof for protection, control, privacy, travel value or everyday CHF savings.",
            "why_it_matters": "Finds which message deserves expensive real-world copy testing.",
        },
        {
            "move": "Segment focus simulation",
            "what_to_change_next": "Run the same concept against family, traveler, digital-native and cash-trusting segments separately.",
            "why_it_matters": "Shows whether the product is broad enough or should be positioned to a narrower segment.",
        },
        {
            "move": "Real research design",
            "what_to_change_next": "Convert objections and weak evidence areas into screener, interview and quantitative survey modules.",
            "why_it_matters": "Uses synthetic customers to improve the real customer study rather than replacing it.",
        },
    ]


def _time_cost_advantage(runtime: dict[str, Any], aggregate: dict[str, Any]) -> dict[str, Any]:
    elapsed = runtime.get("elapsed_seconds", "n/a")
    responses = aggregate.get("response_count", "n/a")
    return {
        "synthetic_run": f"{responses} persona-question responses in {elapsed} seconds.",
        "traditional_research_comparison": "A comparable real survey or interview sprint would usually take days to weeks including recruitment, fielding and synthesis.",
        "best_use": "Use the synthetic layer to remove weak concepts early, sharpen survey wording and decide which segments deserve real research spend.",
        "do_not_use_for": "Do not use synthetic output as a final demand forecast, market-size estimate or replacement for Visa validation.",
    }


def _real_customer_bridge(validation: dict[str, Any], lead_id: str | None, aggregate: dict[str, Any]) -> list[dict[str, str]]:
    concept_summary = aggregate.get("concept_summary", {})
    lead = concept_summary.get(lead_id, {}) if lead_id else {}
    return [
        {
            "stage": "Synthetic learning",
            "purpose": "Explore broad customer reactions quickly and identify weak assumptions.",
            "evidence": f"Current lead adoption index: {lead.get('adoption_index_0_100', 'n/a')}/100; validation: {validation.get('overall', {}).get('score', 'n/a')}/100.",
        },
        {
            "stage": "Real qualitative validation",
            "purpose": "Check whether synthetic rationales sound plausible in customer language.",
            "evidence": "Use the strongest and weakest persona quotes as interview probes.",
        },
        {
            "stage": "Real quantitative validation",
            "purpose": "Confirm adoption, price sensitivity and feature trade-offs with a Swiss sample.",
            "evidence": "Compare real distributions against synthetic response distributions and recalibrate personas.",
        },
    ]


def _root_personas(personas: list[Persona]) -> dict[str, Persona]:
    roots: dict[str, Persona] = {}
    for persona in personas:
        roots.setdefault(persona.id.split("_")[0], persona)
    return roots


def _customer_reality(persona: Persona) -> str:
    return f"{persona.age_band}, {persona.region}, {persona.household}, {persona.income_band} income; {persona.lifestyle}"


def _segment_name(persona: Persona) -> str:
    return persona.name.rsplit(" #", 1)[0]


def _need_state(persona: Persona) -> str:
    attitudes = persona.attitudes
    if attitudes.get("travel_orientation", 0) > 0.75:
        return "Travel value, insurance confidence, FX clarity and premium service proof."
    if attitudes.get("price_sensitivity", 0) > 0.75:
        return "Low friction, transparent fees, tangible everyday value and control."
    if attitudes.get("digital_openness", 0) > 0.8:
        return "Simple mobile-first onboarding, wallet compatibility and useful digital guidance."
    if attitudes.get("privacy_concern", 0) > 0.7:
        return "Trust, privacy, control and non-intrusive defaults."
    return "Balanced everyday value, reliability and clear reason to switch."


def _top_terms(label_counts: Counter[str], rationale_text: str, answer_text: str) -> list[str]:
    terms = [label for label, _ in label_counts.most_common(3)]
    text = f"{rationale_text} {answer_text}"
    for term in ["cashback", "travel", "protection", "fee", "privacy", "mobile", "control", "trust", "insurance", "family"]:
        if term in text and term not in terms:
            terms.append(term)
    return terms[:5] or ["general proposition fit"]


def _objections(persona: Persona, rationale_text: str, answer_text: str) -> list[str]:
    text = f"{rationale_text} {answer_text}"
    objections = []
    for term, label in [
        ("fee", "annual fee/value proof"),
        ("privacy", "privacy and data use"),
        ("control", "loss of control"),
        ("wrong recommendation", "wrong recommendation risk"),
        ("travel", "limited travel relevance"),
        ("digital", "digital setup complexity"),
    ]:
        if term in text:
            objections.append(label)
    if persona.attitudes.get("price_sensitivity", 0) > 0.7 and "annual fee/value proof" not in objections:
        objections.append("annual fee/value proof")
    if persona.attitudes.get("privacy_concern", 0) > 0.7 and "privacy and data use" not in objections:
        objections.append("privacy and data use")
    return objections[:4] or ["reason to switch is not yet sharp enough"]


def _message_to_test(persona: Persona, winner: str) -> str:
    if "Cashback" in winner or persona.attitudes.get("reward_orientation", 0) > 0.75:
        return "Show concrete monthly CHF value from groceries, family offers and purchase protection."
    if "Travel" in winner or persona.attitudes.get("travel_orientation", 0) > 0.75:
        return "Make travel insurance, FX savings and premium benefits tangible against the annual fee."
    if persona.attitudes.get("privacy_concern", 0) > 0.7:
        return "Emphasize control, opt-out, privacy and clear decision logic."
    return "Explain the everyday job-to-be-done and why switching is worth the effort."
