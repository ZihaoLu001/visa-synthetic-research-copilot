from __future__ import annotations

from typing import Any

from .schemas import SurveyRun


def build_consultant_quality_layer(
    run: SurveyRun,
    decision_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a consultant-facing quality layer for interpreting synthetic evidence.

    The goal is to prevent overclaiming. A synthetic run is most useful when it says:
    what seems directionally true, how strong that evidence is, what could be wrong,
    and what the next real-customer study should test.
    """
    decision = decision_context or run.aggregate.get("decision_brief", {})
    validation = run.validation
    aggregate = run.aggregate

    lead_gap = _as_float(decision.get("adoption_gap_vs_next"))
    validation_score = _as_float(validation.get("overall", {}).get("score"))
    question_score = _as_float(validation.get("question_coverage", {}).get("score"))
    realism_score = _as_float(validation.get("realism_rubric", {}).get("score"))
    benchmark_mae = _as_float(validation.get("benchmark_alignment", {}).get("primary_mae_percentage_points"))
    segment_spread = _segment_spread(aggregate.get("segment_fit", {}))
    worst_price_gaps = _price_gap_watchouts(run)
    proposition_count = len(aggregate.get("concept_summary", {}))

    risk_flags = _risk_flags(
        lead_gap=lead_gap,
        validation_score=validation_score,
        question_score=question_score,
        realism_score=realism_score,
        segment_spread=segment_spread,
        worst_price_gaps=worst_price_gaps,
        proposition_count=proposition_count,
    )
    evidence_score = _evidence_strength_score(
        validation_score=validation_score,
        lead_gap=lead_gap,
        question_score=question_score,
        realism_score=realism_score,
        segment_spread=segment_spread,
        benchmark_mae=benchmark_mae,
        proposition_count=proposition_count,
    )
    grade, grade_label = _evidence_grade(evidence_score)
    missing_constructs = validation.get("question_coverage", {}).get("missing_constructs", [])
    detected_constructs = validation.get("question_coverage", {}).get("detected_constructs", [])

    return {
        "evidence_grade": grade,
        "evidence_score": evidence_score,
        "evidence_label": grade_label,
        "decision_risk": _decision_risk(lead_gap, validation_score, risk_flags),
        "lead_margin_interpretation": _lead_margin_interpretation(lead_gap),
        "segment_differentiation": {
            "spread": segment_spread,
            "interpretation": _segment_spread_interpretation(segment_spread),
        },
        "risk_flags": risk_flags,
        "top_consultant_actions": _top_consultant_actions(risk_flags, decision),
        "survey_repair_plan": _survey_repair_plan(missing_constructs, detected_constructs),
        "recommended_validation_plan": _recommended_validation_plan(decision, aggregate),
        "calibration_thresholds": [
            "Advance a proposition only when synthetic segment fit and validation confidence are strong enough to justify real customer testing.",
            "Recalibrate persona weights if payment benchmark MAE exceeds 10 percentage points.",
            "Treat realism score below 80 as a review trigger for prompt, parser, or survey wording changes.",
            "Treat missing adoption, price, feature, or barrier constructs as a survey-design gap before partner sign-off.",
        ],
    }


def _risk_flags(
    *,
    lead_gap: float | None,
    validation_score: float | None,
    question_score: float | None,
    realism_score: float | None,
    segment_spread: float | None,
    worst_price_gaps: list[dict[str, Any]],
    proposition_count: int,
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if lead_gap is None:
        if proposition_count > 1:
            flags.append(_flag("No clear lead proposition", "Add a direct adoption/appeal question before using this run for proposition selection.", "high"))
    elif lead_gap < 3:
        flags.append(_flag("Narrow proposition lead", f"Lead is only {lead_gap} points; present the result as a toss-up in the next real survey.", "medium"))
    elif lead_gap < 5:
        flags.append(_flag("Moderate proposition lead", f"Lead is {lead_gap} points; useful directionally, but not enough for a final go/no-go decision.", "low"))

    if validation_score is not None and validation_score < 85:
        flags.append(_flag("Validation below green threshold", f"Overall validation is {validation_score}/100; review caveats before partner sharing.", "medium"))
    if question_score is not None and question_score < 85:
        flags.append(_flag("Survey construct gap", f"Question coverage is {question_score}/100; add missing proposition-testing constructs.", "medium"))
    if realism_score is not None and realism_score < 80:
        flags.append(_flag("Realism review needed", f"Realism score is {realism_score}/100; inspect persona rows for odd price or adoption rationales.", "medium"))
    if segment_spread is not None and segment_spread < 0.35:
        flags.append(_flag("Low segment differentiation", "Most segment Likert scores are close together; add forced trade-off and ranking questions to expose sharper differences.", "medium"))

    for price_gap in worst_price_gaps[:2]:
        flags.append(
            _flag(
                "Price-value mismatch",
                f"{price_gap['concept_name']} acceptable-fee signal is CHF {abs(int(price_gap['gap']))} below current fee; test lower fee or stronger value proof.",
                "medium",
            )
        )
    if not flags:
        flags.append(_flag("No major evidence risk detected", "Current synthetic run is suitable for directional consulting discussion with normal governance caveats.", "low"))
    return flags


def _survey_repair_plan(missing_constructs: list[str], detected_constructs: list[str]) -> list[dict[str, str]]:
    plan = [
        {
            "module": "Adoption and current behavior",
            "priority": "High" if "adoption" in missing_constructs else "Medium",
            "why": "Grounds synthetic adoption in a realistic current-behavior baseline.",
            "suggested_question": "How likely would you be to use this proposition if offered by your main bank, and what current payment or banking behavior would it replace?",
        },
        {
            "module": "Price sensitivity",
            "priority": "High" if "price" in missing_constructs else "Medium",
            "why": "Visa explicitly asked for price sensitivity and value proposition testing.",
            "suggested_question": "At which annual fee or monthly price in CHF would this proposition feel too expensive, acceptable, and clearly good value?",
        },
        {
            "module": "Feature trade-off",
            "priority": "High" if "feature" in missing_constructs else "Medium",
            "why": "Ranking or forced choice exposes what benefit actually drives switching.",
            "suggested_question": "Please rank the top three benefits, services or messages that would make this proposition more useful to you.",
        },
        {
            "module": "Barrier and trust",
            "priority": "High" if "barrier" in missing_constructs else "Medium",
            "why": "Identifies what must be fixed before a real launch or real survey.",
            "suggested_question": "What is the main reason you would not use this proposition: fee, privacy, loss of control, unclear benefit, setup complexity, or lack of trust?",
        },
        {
            "module": "Segment screener",
            "priority": "Medium",
            "why": "Allows Visa to compare synthetic segment signals against real Swiss respondents.",
            "suggested_question": "Which best describes you: age band, language region, household type, monthly card spend, travel frequency, and mobile wallet usage?",
        },
    ]
    if set(detected_constructs) >= {"adoption", "price", "feature", "barrier"}:
        plan.insert(
            0,
            {
                "module": "Choice-based validation",
                "priority": "High",
                "why": "The base constructs are present; the next improvement is a sharper preference test.",
                "suggested_question": "If you had to decide today, would this proposition advance to real customer testing, and what one change would improve it most?",
            },
        )
    return plan


def _top_consultant_actions(risk_flags: list[dict[str, str]], decision: dict[str, Any]) -> list[str]:
    lead_name = decision.get("lead_concept_name") or decision.get("lead_concept_id") or "the current proposition"
    actions = [
        f"Position {lead_name} as a directional anchor, not a final decision, unless real survey evidence confirms the signal.",
        "Use the risk flags as the opening slide for partner discussion: what we know, what could be wrong, and what to validate next.",
    ]
    titles = {flag["title"] for flag in risk_flags}
    if "Narrow proposition lead" in titles:
        actions.append("Run a forced-choice or control-cell question and a fee sensitivity variant before recommending a single proposition.")
    if "Survey construct gap" in titles:
        actions.append("Add the missing survey modules before using the output as a consultant recommendation.")
    if "Low segment differentiation" in titles:
        actions.append("Use ranking, max-diff, or forced trade-off questions to create clearer segment separation.")
    if "Realism review needed" in titles:
        actions.append("Review persona-level outliers and rerun the affected questions after tightening prompts or answer rules.")
    actions.append("Convert the strongest persona rationales into interview prompts for the next real Swiss customer validation sprint.")
    return actions[:6]


def _recommended_validation_plan(decision: dict[str, Any], aggregate: dict[str, Any]) -> list[str]:
    lead_id = decision.get("lead_concept_id")
    priority_segments = _priority_segments(lead_id, aggregate.get("segment_fit", {}))
    return [
        f"Qualitative sprint: run 8-12 interviews with {priority_segments} to test language, trust, perceived value, and switching barriers.",
        "Quantitative pulse: run a short real Swiss sample survey with quota controls for language region, age band, household type, travel frequency, and mobile wallet usage.",
        "Pricing cell test: test at least three annual-fee points and one stronger protection-message variant.",
        "Calibration loop: compare real adoption, feature ranking, and barrier distributions to the synthetic run; update persona weights and prompts where the gap is large.",
    ]


def _priority_segments(lead_id: str | None, segment_fit: dict[str, float | None]) -> str:
    rows = []
    for key, value in segment_fit.items():
        if value is None:
            continue
        if lead_id and not key.startswith(f"{lead_id}:"):
            continue
        _, _, segment = key.partition(":")
        rows.append((segment, value))
    rows.sort(key=lambda item: item[1], reverse=True)
    if not rows:
        return "the highest-fit synthetic segments"
    return ", ".join(segment for segment, _ in rows[:3])


def _evidence_strength_score(
    *,
    validation_score: float | None,
    lead_gap: float | None,
    question_score: float | None,
    realism_score: float | None,
    segment_spread: float | None,
    benchmark_mae: float | None,
    proposition_count: int,
) -> float:
    score = validation_score if validation_score is not None else 60.0
    if lead_gap is None and proposition_count > 1:
        score -= 18
    elif lead_gap is not None and lead_gap < 3:
        score -= 10
    elif lead_gap is not None and lead_gap < 5:
        score -= 5
    if question_score is not None and question_score < 85:
        score -= 6
    if realism_score is not None and realism_score < 80:
        score -= 6
    if segment_spread is not None and segment_spread < 0.35:
        score -= 5
    if benchmark_mae is not None and benchmark_mae > 10:
        score -= 10
    return round(max(0.0, min(100.0, score)), 1)


def _evidence_grade(score: float) -> tuple[str, str]:
    if score >= 88:
        return "A", "Strong directional evidence; ready for partner discussion with normal caveats."
    if score >= 78:
        return "B", "Useful directional evidence; needs targeted real-customer validation before final decision."
    if score >= 65:
        return "C", "Promising but incomplete; improve survey design or calibration before relying on the result."
    return "D", "Do not use for decision support until survey, persona, or validation issues are fixed."


def _decision_risk(lead_gap: float | None, validation_score: float | None, risk_flags: list[dict[str, str]]) -> str:
    high_or_medium = [flag for flag in risk_flags if flag.get("severity") in {"high", "medium"}]
    if lead_gap is not None and lead_gap < 3:
        return "Toss-up: keep the result directional until real respondents confirm the difference."
    if validation_score is not None and validation_score >= 85 and not high_or_medium:
        return "Low: suitable for directional consulting discussion."
    if validation_score is not None and validation_score >= 70:
        return "Medium: usable with explicit caveats and a targeted validation sprint."
    return "High: recalibrate before partner-facing recommendation."


def _lead_margin_interpretation(lead_gap: float | None) -> str:
    if lead_gap is None:
        return "Single proposition read; no head-to-head lead calculated."
    if lead_gap < 3:
        return "Very narrow lead; interpret as a tie unless confirmed by real respondents."
    if lead_gap < 5:
        return "Moderate but not decisive lead; use for prioritization, not final selection."
    return "Clear directional lead for an early-stage synthetic run."


def _segment_spread(segment_fit: dict[str, float | None]) -> float | None:
    values = [float(value) for value in segment_fit.values() if value is not None]
    if not values:
        return None
    return round(max(values) - min(values), 2)


def _segment_spread_interpretation(spread: float | None) -> str:
    if spread is None:
        return "No segment fit could be calculated."
    if spread < 0.35:
        return "Low differentiation; ask sharper trade-off questions."
    if spread < 0.75:
        return "Moderate differentiation; useful for selecting interview segments."
    return "Strong differentiation; prioritize divergent segments in validation."


def _price_gap_watchouts(run: SurveyRun) -> list[dict[str, Any]]:
    concept_lookup = {concept.id: concept for concept in run.concepts}
    rows: list[dict[str, Any]] = []
    for concept_id, price in run.aggregate.get("price_summary", {}).items():
        concept = concept_lookup.get(concept_id)
        acceptable = price.get("weighted_mean_chf")
        if not concept or acceptable is None:
            continue
        gap = float(acceptable) - float(concept.annual_fee_chf)
        if gap < -10:
            rows.append({"concept_id": concept_id, "concept_name": concept.name, "gap": round(gap, 0)})
    return sorted(rows, key=lambda row: row["gap"])


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _flag(title: str, detail: str, severity: str) -> dict[str, str]:
    return {"title": title, "detail": detail, "severity": severity}
