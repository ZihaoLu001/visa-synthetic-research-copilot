from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .schemas import Concept, Persona, PersonaResponse, SurveyRun


def build_synthetic_customer_lens(run: SurveyRun, decision_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Translate survey-agent output into the customer view Visa asked for.

    Keep this layer intentionally narrow: customer perspectives, decision
    drivers, consultant output and validation bridge. Broader synthetic-customer
    use cases are out of scope for the Visa prototype.
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
        "value_proposition_questions": _value_proposition_questions(run),
        "synthetic_customer_board": _segment_board(run),
        "decision_drivers": _decision_drivers(run),
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


def _value_proposition_questions(run: SurveyRun) -> list[str]:
    question_text = " ".join(question.text.lower() for question in run.questions)
    questions = [
        "Is the client value proposition relevant enough to take into real validation?",
        "Which Swiss customer segments show the strongest fit or resistance?",
        "Which benefit messages and barriers should be tested with real customers?",
    ]
    if any(term in question_text for term in ["fee", "price", "chf", "pay"]):
        questions.append("Which annual-fee range should be tested in pricing cells?")
    if any(term in question_text for term in ["trust", "privacy", "control", "recommendation"]):
        questions.append("What trust, control or privacy language is needed before launch testing?")
    return questions


def _time_cost_advantage(runtime: dict[str, Any], aggregate: dict[str, Any]) -> dict[str, Any]:
    elapsed = runtime.get("elapsed_seconds", "n/a")
    responses = aggregate.get("response_count", "n/a")
    return {
        "synthetic_run": f"{responses} persona-question responses in {elapsed} seconds.",
        "traditional_research_comparison": "A comparable real survey or interview sprint would usually take days to weeks including recruitment, fielding and synthesis.",
        "best_use": "Use the synthetic layer to identify weak assumptions early, sharpen survey wording and decide which segments deserve real research spend.",
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
    for term in ["savings", "travel", "protection", "fee", "privacy", "mobile", "control", "trust", "insurance", "family", "transparency"]:
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
    if persona.attitudes.get("reward_orientation", 0) > 0.75:
        return "Show concrete monthly CHF value, practical savings and protection proof."
    if "Travel" in winner or persona.attitudes.get("travel_orientation", 0) > 0.75:
        return "Make cross-border, travel, insurance and service benefits tangible against the fee."
    if persona.attitudes.get("privacy_concern", 0) > 0.7:
        return "Emphasize control, opt-out, privacy and clear decision logic."
    return "Explain the everyday job-to-be-done and why switching is worth the effort."
