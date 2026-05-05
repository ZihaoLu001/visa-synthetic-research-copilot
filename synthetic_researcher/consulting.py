from __future__ import annotations

from typing import Any

from .schemas import Concept, SurveyRun


def default_research_brief() -> dict[str, str]:
    return {
        "project_objective": (
            "Stress-test two early-stage Visa card value propositions for Swiss consumers before investing "
            "in a full real-customer survey."
        ),
        "client_decision": (
            "Decide which proposition, price point and benefit message should advance to focused customer "
            "validation."
        ),
        "hypotheses": (
            "H1: Premium travel benefits are attractive to frequent travelers but weak for everyday segments.\n"
            "H2: Annual fee level is the largest barrier for students, families and cash-trusting retirees.\n"
            "H3: Purchase protection and transparent fee messaging can increase trust outside premium segments."
        ),
        "decision_rule": (
            "Advance a concept only if it leads on adoption, has a credible segment fit, and the validation "
            "score is amber or green."
        ),
        "stakeholder_output": (
            "A consultant-ready decision brief with directional recommendation, segment differences, key "
            "barriers, price sensitivity, evidence quality and next real-research actions."
        ),
    }


def build_decision_brief(run: SurveyRun, research_brief: dict[str, str], provider: str = "mock") -> dict[str, Any]:
    aggregate = run.aggregate
    validation = run.validation
    concept_summary = aggregate.get("concept_summary", {})
    concept_lookup = {concept.id: concept for concept in run.concepts}
    ranked = _rank_concepts(concept_summary)
    lead_id = ranked[0]["concept_id"] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    lead_summary = concept_summary.get(lead_id, {}) if lead_id else {}
    lead_concept = concept_lookup.get(lead_id) if lead_id else None
    overall_score = validation.get("overall", {}).get("score")
    validation_band = _validation_band(overall_score)
    adoption_gap = (
        round((lead_summary.get("adoption_index_0_100") or 0) - (second.get("adoption_index_0_100") or 0), 1)
        if second
        else None
    )

    concept_matrix = [
        _concept_decision_row(
            concept=concept_lookup.get(row["concept_id"]),
            concept_id=row["concept_id"],
            adoption_index=row.get("adoption_index_0_100"),
            mean_likert=row.get("mean_likert"),
            aggregate=aggregate,
            validation_score=overall_score,
        )
        for row in ranked
    ]

    executive_answer = _executive_answer(lead_concept, lead_summary, adoption_gap, validation_band)
    so_what = _so_what(lead_id, aggregate)
    hypotheses = _hypothesis_readout(research_brief.get("hypotheses", ""), aggregate, validation)

    return {
        "executive_answer": executive_answer,
        "decision_posture": _decision_posture(lead_summary, overall_score, adoption_gap),
        "lead_concept_id": lead_id,
        "lead_concept_name": lead_concept.name if lead_concept else None,
        "adoption_gap_vs_next": adoption_gap,
        "validation_band": validation_band,
        "validation_score": overall_score,
        "concept_matrix": concept_matrix,
        "so_what": so_what,
        "hypothesis_readout": hypotheses,
        "recommended_real_research": _recommended_real_research(lead_id, aggregate),
        "methodology": methodology_snapshot(provider),
        "limitations": [
            "Synthetic output is directional and should not be used as final market-size or revenue evidence.",
            "Public Swiss benchmarks ground population/payment behavior, but Visa internal calibration is still required.",
            "The offline mock provider is deterministic for demo reliability; watsonx mode should be used for a stronger pilot run when credentials/quota are available.",
            "A human consultant should review the extracted survey text, parsed question types and any unusual persona answers before sharing insights externally.",
        ],
    }


def methodology_snapshot(provider: str = "mock") -> list[str]:
    provider_line = (
        "LLM provider: IBM watsonx.ai through ibm-watsonx-ai ModelInference, default model ibm/granite-3-8b-instruct."
        if provider == "watsonx"
        else "LLM provider: deterministic MockLLM fallback for reliable offline and classroom demos; switch MODEL_PROVIDER=watsonx for IBM Granite calls."
    )
    return [
        provider_line,
        "Survey ingestion: PDF/DOCX/XLSX/CSV/TXT extraction, editable text review and structured question parsing.",
        "Persona sampling: public-data-grounded Swiss archetypes expanded into a weighted micro-population with stable seeded variation.",
        "Persona response layer: one agent answers as one persona, with concept context, public benchmark context and prior answers for consistency.",
        "Analytics: weighted adoption index, acceptable-fee signal, feature/barrier labels, segment fit and traceable persona quotes.",
        "Validation: payment benchmark MAE, repeated-run Likert variance, persona coverage, question construct coverage and realism rubric flags.",
    ]


def format_decision_brief_markdown(run: SurveyRun) -> str:
    brief = run.aggregate.get("decision_brief", {})
    research = run.aggregate.get("research_brief", {})
    lines = [
        "# VCA Synthetic Research Decision Brief",
        "",
        f"Run ID: `{run.run_id}`",
        "",
        "## Research Brief",
        "",
        f"- Objective: {research.get('project_objective', 'n/a')}",
        f"- Client decision: {research.get('client_decision', 'n/a')}",
        f"- Decision rule: {research.get('decision_rule', 'n/a')}",
        "",
        "## Executive Answer",
        "",
        brief.get("executive_answer", "No decision brief generated."),
        "",
        f"Decision posture: **{brief.get('decision_posture', 'n/a')}**",
        f"Validation: **{brief.get('validation_band', 'n/a')}** ({brief.get('validation_score', 'n/a')}/100)",
        "",
        "## Concept Decision Matrix",
        "",
        "| Concept | Adoption | Price signal | Strongest fit | Primary action |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in brief.get("concept_matrix", []):
        strongest = ", ".join(row.get("strongest_segments", [])[:3]) or "n/a"
        lines.append(
            f"| {row.get('concept_name') or row.get('concept_id')} | {row.get('adoption_index')} | "
            f"{row.get('price_signal')} | {strongest} | {row.get('recommended_action')} |"
        )
    lines.extend(["", "## So What", ""])
    lines.extend(f"- {item}" for item in brief.get("so_what", []))
    lines.extend(["", "## Hypothesis Readout", ""])
    for item in brief.get("hypothesis_readout", []):
        lines.append(f"- {item.get('hypothesis')}: {item.get('status')} - {item.get('evidence')}")
    lines.extend(["", "## Recommended Real Research", ""])
    lines.extend(f"- {item}" for item in brief.get("recommended_real_research", []))
    lines.extend(["", "## Methodology Snapshot", ""])
    lines.extend(f"- {item}" for item in brief.get("methodology", []))
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in brief.get("limitations", []))
    return "\n".join(lines)


def _rank_concepts(concept_summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for concept_id, values in concept_summary.items():
        rows.append({"concept_id": concept_id, **values})
    return sorted(rows, key=lambda row: row.get("adoption_index_0_100") or 0, reverse=True)


def _concept_decision_row(
    concept: Concept | None,
    concept_id: str,
    adoption_index: float | None,
    mean_likert: float | None,
    aggregate: dict[str, Any],
    validation_score: float | None,
) -> dict[str, Any]:
    price = aggregate.get("price_summary", {}).get(concept_id, {})
    strongest, weakest = _segment_extremes(concept_id, aggregate.get("segment_fit", {}))
    top_signals = [label for label, _ in aggregate.get("top_answer_labels_by_concept", {}).get(concept_id, [])[:5]]
    fee = concept.annual_fee_chf if concept else None
    acceptable_fee = price.get("weighted_mean_chf")
    price_gap = round(acceptable_fee - fee, 0) if acceptable_fee is not None and fee is not None else None
    price_signal = (
        f"Mean acceptable CHF {int(acceptable_fee)}; gap vs fee {int(price_gap):+d}"
        if acceptable_fee is not None and price_gap is not None
        else "No explicit price question detected"
    )
    return {
        "concept_id": concept_id,
        "concept_name": concept.name if concept else concept_id,
        "adoption_index": adoption_index,
        "mean_likert": mean_likert,
        "price_signal": price_signal,
        "strongest_segments": strongest,
        "weakest_segments": weakest,
        "top_signals": top_signals,
        "recommended_action": _recommended_action(adoption_index, validation_score, price_gap),
    }


def _segment_extremes(concept_id: str, segment_fit: dict[str, float | None]) -> tuple[list[str], list[str]]:
    rows = []
    for key, value in segment_fit.items():
        if not key.startswith(f"{concept_id}:") or value is None:
            continue
        _, segment = key.split(":", 1)
        rows.append((segment, value))
    rows.sort(key=lambda item: item[1], reverse=True)
    return [segment for segment, _ in rows[:3]], [segment for segment, _ in rows[-3:]]


def _validation_band(score: float | None) -> str:
    if score is None:
        return "not available"
    if score >= 85:
        return "green - suitable for directional consulting discussion"
    if score >= 70:
        return "amber - usable with clear caveats"
    return "red - recalibrate before sharing"


def _executive_answer(
    lead: Concept | None,
    lead_summary: dict[str, Any],
    adoption_gap: float | None,
    validation_band: str,
) -> str:
    if not lead:
        return "No lead concept could be selected because no adoption-style question was parsed."
    gap_text = f" by {adoption_gap} points versus the next concept" if adoption_gap is not None else ""
    return (
        f"{lead.name} is the directional lead in this synthetic panel, with adoption index "
        f"{lead_summary.get('adoption_index_0_100')}/100{gap_text}. Treat this as early-stage evidence: "
        f"the current validation posture is {validation_band}."
    )


def _decision_posture(
    lead_summary: dict[str, Any],
    validation_score: float | None,
    adoption_gap: float | None,
) -> str:
    adoption = lead_summary.get("adoption_index_0_100") or 0
    score = validation_score or 0
    gap = adoption_gap if adoption_gap is not None else 0
    if adoption >= 65 and score >= 85 and gap >= 5:
        return "Advance lead concept to focused real-customer validation"
    if adoption >= 50 and score >= 70:
        return "Refine proposition and run a targeted validation sprint"
    return "Recalibrate personas/survey or redesign proposition before using for decisions"


def _recommended_action(adoption_index: float | None, validation_score: float | None, price_gap: float | None) -> str:
    adoption = adoption_index or 0
    validation = validation_score or 0
    if price_gap is not None and price_gap < -20:
        return "Retest with lower fee or stronger value proof"
    if adoption >= 65 and validation >= 80:
        return "Advance to focused customer validation"
    if adoption >= 50:
        return "Refine messaging, then rerun sensitivity test"
    return "Deprioritize or redesign before spending on field research"


def _so_what(lead_id: str | None, aggregate: dict[str, Any]) -> list[str]:
    if not lead_id:
        return ["No clear lead concept was identified; first inspect the parsed survey questions."]
    matrix_barriers = [label for label, _ in aggregate.get("top_barrier_signals", [])[:4]]
    signals = [label for label, _ in aggregate.get("top_answer_labels_by_concept", {}).get(lead_id, [])[:4]]
    items = [
        f"Use concept {lead_id} as the anchor for the next validation round, but keep at least one challenger concept to test fee and messaging sensitivity.",
        "Prioritize segment-specific messaging; the synthetic panel is most useful when it shows which archetypes diverge, not when it averages everyone together.",
    ]
    if signals:
        items.append("Feature/message signals to carry into the next survey: " + ", ".join(signals) + ".")
    if matrix_barriers:
        items.append("Primary watchouts to resolve before a real survey: " + ", ".join(matrix_barriers) + ".")
    items.append("Use the persona-level table to turn vague averages into interview prompts and recruiter screeners for real validation.")
    return items


def _hypothesis_readout(
    hypothesis_text: str,
    aggregate: dict[str, Any],
    validation: dict[str, Any],
) -> list[dict[str, str]]:
    hypotheses = [line.strip(" -") for line in hypothesis_text.splitlines() if line.strip()]
    if not hypotheses:
        hypotheses = ["Synthetic responses should reveal adoption, price, feature and barrier differences by segment."]
    construct_score = validation.get("question_coverage", {}).get("score")
    has_price = bool(aggregate.get("price_summary"))
    has_segments = bool(aggregate.get("segment_fit"))
    rows = []
    for hyp in hypotheses:
        lower = hyp.lower()
        if any(term in lower for term in ["price", "fee", "chf"]) and has_price:
            status = "directionally tested"
            evidence = "Price questions produced acceptable-fee signals by concept."
        elif any(term in lower for term in ["segment", "traveler", "family", "student", "retiree", "premium"]) and has_segments:
            status = "directionally tested"
            evidence = "Segment Explorer shows archetype-level fit differences."
        elif construct_score == 100:
            status = "covered by current survey"
            evidence = "Parsed questions cover the core adoption, price, feature and barrier constructs."
        else:
            status = "partially covered"
            evidence = "Add a more explicit survey question before treating this as tested."
        rows.append({"hypothesis": hyp, "status": status, "evidence": evidence})
    return rows


def _recommended_real_research(lead_id: str | None, aggregate: dict[str, Any]) -> list[str]:
    segments = []
    for key, value in sorted(aggregate.get("segment_fit", {}).items(), key=lambda item: item[1] or 0, reverse=True):
        if lead_id and key.startswith(f"{lead_id}:"):
            segments.append(key.split(":", 1)[1])
    priority_segments = ", ".join(segments[:3]) if segments else "highest-fit synthetic segments"
    return [
        f"Run 8-12 qualitative interviews in {priority_segments} to validate the main adoption drivers and language.",
        "Run a short quantitative survey with a real Swiss sample to validate adoption, acceptable fee and feature trade-offs.",
        "Compare real responses with this synthetic run; use large deviations to recalibrate persona weights, payment profiles and prompts.",
        "Feed Visa internal customer insight back into the benchmark layer only after confirming data-sharing and confidentiality constraints.",
    ]
