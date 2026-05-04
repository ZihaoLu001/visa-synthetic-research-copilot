from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .schemas import Concept, Persona, PersonaResponse, SurveyQuestion


def benchmark_alignment(personas: list[Persona], benchmark_data: dict[str, Any]) -> dict[str, Any]:
    """Compare persona payment-method mix with public benchmark anchors.

    Returns a transparent score, not a claim of real-world accuracy.
    """
    keys = ["cash", "debit_card", "credit_card", "mobile_payment_apps"]
    total_w = sum(p.weight for p in personas)
    if total_w <= 0:
        return {"score": None, "message": "No benchmark target available"}

    synthetic = {}
    for key in keys:
        synthetic[key] = sum(p.payment_profile.get(key, 0.0) * p.weight for p in personas) / total_w * 100

    raw_profiles = benchmark_data.get("benchmark_profiles") or {
        "snb_pos_2025": {
            "label": "SNB 2025 point-of-sale transactions",
            "context": "in-person payments by private individuals",
            "source": "Swiss National Bank Payment Methods Survey of Private Individuals 2025",
            "payment_mix": benchmark_data.get("payment_mix_pos_2025", {}),
        }
    }
    if not raw_profiles:
        return {"score": None, "message": "No benchmark target available"}

    profile_scores: dict[str, dict[str, Any]] = {}
    for profile_id, profile in raw_profiles.items():
        target = profile.get("payment_mix", {})
        if not target:
            continue
        diffs = {k: abs(synthetic.get(k, 0.0) - float(target.get(k, 0.0))) for k in keys}
        mae = sum(diffs.values()) / len(keys)
        score = max(0.0, 100 - mae * 4)
        profile_scores[profile_id] = {
            "label": profile.get("label", profile_id),
            "context": profile.get("context", ""),
            "source": profile.get("source", ""),
            "url": profile.get("url", ""),
            "score": round(score, 1),
            "mae_percentage_points": round(mae, 2),
            "benchmark_mix": target,
            "diffs_percentage_points": {k: round(v, 1) for k, v in diffs.items()},
        }

    if not profile_scores:
        return {"score": None, "message": "No benchmark target available"}

    primary_profile_id = (
        "spm_all_transactions_2026_1"
        if "spm_all_transactions_2026_1" in profile_scores
        else next(iter(profile_scores))
    )
    primary = profile_scores[primary_profile_id]
    best_profile_id, best = max(profile_scores.items(), key=lambda kv: kv[1]["score"])
    return {
        "score": primary["score"],
        "primary_profile_id": primary_profile_id,
        "primary_profile_label": primary["label"],
        "primary_mae_percentage_points": primary["mae_percentage_points"],
        "best_profile_id": best_profile_id,
        "best_profile_label": best["label"],
        "best_score": best["score"],
        "synthetic_mix": {k: round(v, 1) for k, v in synthetic.items()},
        "profiles": profile_scores,
        "interpretation": "Green >= 85, Amber 70-85, Red < 70. Use as a grounding check, not as proof of validity.",
    }


def internal_consistency(responses_by_run: list[list[PersonaResponse]]) -> dict[str, Any]:
    """Compute repeated-run variance for numeric answers by persona/concept/question."""
    values = defaultdict(list)
    for run in responses_by_run:
        for r in run:
            if r.answer_value is not None and r.question_type == "likert":
                values[(r.persona_id, r.concept_id, r.question_id)].append(r.answer_value)
    stds = []
    for arr in values.values():
        if len(arr) < 2:
            continue
        mean = sum(arr) / len(arr)
        stds.append(math.sqrt(sum((x - mean) ** 2 for x in arr) / len(arr)))
    avg_std = sum(stds) / len(stds) if stds else 0.0
    score = max(0.0, 100 - avg_std * 35)
    stability_label = "stable"
    if avg_std > 0.5:
        stability_label = "unstable"
    elif avg_std < 0.05 and len(responses_by_run) > 1:
        stability_label = "very stable / deterministic"
    return {
        "score": round(score, 1),
        "avg_likert_std": round(avg_std, 3),
        "tested_items": len(stds),
        "stability_label": stability_label,
        "interpretation": "Low variance suggests persona responses are stable across repeated runs; too-low variance may also indicate insufficient diversity in a deterministic fallback provider.",
    }


def coverage_check(personas: list[Persona]) -> dict[str, Any]:
    roots = {p.id.split("_")[0] for p in personas}
    income = {p.income_band for p in personas}
    age = {p.age_band for p in personas}
    household = {p.household for p in personas}
    language_regions = {p.language_region for p in personas}
    return {
        "archetype_count": len(roots),
        "micro_persona_count": len(personas),
        "income_bands": sorted(income),
        "age_bands": sorted(age),
        "household_types": sorted(household),
        "language_regions": sorted(language_regions),
        "score": 100 if len(roots) >= 6 and len(income) >= 3 and len(household) >= 3 and len(language_regions) >= 3 else 75,
        "interpretation": "Checks whether the synthetic panel covers the Swiss dimensions requested by Visa: age, income, household, region/language and lifestyle.",
    }


def question_coverage_check(questions: list[SurveyQuestion], responses: list[PersonaResponse]) -> dict[str, Any]:
    measures = {q.measures.lower() for q in questions}
    types = {q.type for q in questions}
    expected_constructs = {
        "adoption": "likert" in types or any("adoption" in m or "trust" in m or "relevance" in m for m in measures),
        "price": "price" in types or any("price" in m for m in measures),
        "feature": any("feature" in m for m in measures),
        "barrier": any("barrier" in m for m in measures),
    }
    detected = [name for name, ok in expected_constructs.items() if ok]
    response_types = {r.question_type for r in responses}
    score = 100 if len(detected) >= 4 else 85 if len(detected) >= 3 else 70 if len(detected) >= 2 else 50
    return {
        "score": score,
        "question_count": len(questions),
        "response_type_count": {kind: sum(1 for r in responses if r.question_type == kind) for kind in sorted(response_types)},
        "detected_constructs": detected,
        "missing_constructs": [name for name in expected_constructs if name not in detected],
        "interpretation": "Checks whether the survey covers the consultant constructs Visa asked for: adoption, pricing, feature preference and barriers.",
    }


def realism_rubric(
    responses: list[PersonaResponse],
    personas: list[Persona],
    concepts: list[Concept],
    questions: list[SurveyQuestion],
) -> dict[str, Any]:
    """Deterministic judge-style realism check.

    This is intentionally transparent. A future watsonx judge agent can replace or
    augment it, but the same rubric should remain visible to consultants.
    """
    persona_by_id = {p.id: p for p in personas}
    concept_by_id = {c.id: c for c in concepts}
    question_by_id = {q.id: q for q in questions}
    flags: list[dict[str, Any]] = []

    grouped: dict[tuple[str, str], list[PersonaResponse]] = defaultdict(list)
    for response in responses:
        grouped[(response.persona_id, response.concept_id)].append(response)
        persona = persona_by_id.get(response.persona_id)
        concept = concept_by_id.get(response.concept_id)
        question = question_by_id.get(response.question_id)
        text = (response.answer_text or "").strip()
        lower = text.lower()

        if not text or len(text) < 12:
            flags.append(_flag(response, "empty_or_too_short", "Answer text is too short to be useful."))
        if len(text) > 450:
            flags.append(_flag(response, "too_long", "Answer is too long for survey-style feedback."))
        if "as an ai" in lower or "language model" in lower or "real person" in lower:
            flags.append(_flag(response, "role_leakage", "Response leaks model identity or overclaims real-person status."))
        if question and question.type == "likert" and response.answer_value is not None:
            if response.answer_value < question.scale_min or response.answer_value > question.scale_max:
                flags.append(_flag(response, "likert_out_of_range", "Likert value is outside the configured scale."))
        if question and question.type == "price":
            if response.answer_value is None or response.answer_value < 0:
                flags.append(_flag(response, "invalid_price", "Price question did not return a non-negative CHF amount."))
        if persona and concept and question and question.type == "price" and response.answer_value is not None:
            sensitivity = persona.attitudes.get("price_sensitivity", 0.5)
            if sensitivity >= 0.75 and response.answer_value > max(90, concept.annual_fee_chf):
                flags.append(_flag(response, "price_alignment", "Highly price-sensitive persona returned an unexpectedly high willingness-to-pay."))
            if sensitivity <= 0.35 and response.answer_value < 20 and concept.annual_fee_chf >= 60:
                flags.append(_flag(response, "price_alignment", "Low price-sensitivity persona returned an unexpectedly low willingness-to-pay."))

    contradiction_flags = _contradiction_flags(grouped, question_by_id, concept_by_id)
    flags.extend(contradiction_flags)

    total = max(1, len(responses))
    structural_penalty = min(35.0, 100 * sum(1 for f in flags if f["category"] in {"empty_or_too_short", "too_long", "role_leakage"}) / total)
    numeric_penalty = min(25.0, 100 * sum(1 for f in flags if f["category"] in {"likert_out_of_range", "invalid_price"}) / total)
    alignment_penalty = min(25.0, 100 * sum(1 for f in flags if f["category"] == "price_alignment") / total)
    contradiction_penalty = min(25.0, 100 * len(contradiction_flags) / max(1, len(grouped)))
    score = max(0.0, 100 - structural_penalty - numeric_penalty - alignment_penalty - contradiction_penalty)

    return {
        "score": round(score, 1),
        "sampled_items": len(responses),
        "flag_count": len(flags),
        "flags_by_category": _count_flags(flags),
        "sample_flags": flags[:12],
        "rubric": [
            "Answer is concise and survey-like.",
            "No model identity leakage or real-person overclaim.",
            "Numeric answers respect question type and scale.",
            "Price sensitivity roughly matches persona income/attitudes.",
            "Adoption and willingness-to-pay are not obviously contradictory.",
        ],
        "interpretation": "Judge-style realism check for demo governance. It is a transparent heuristic baseline, not a substitute for Visa's human/customer validation.",
    }


def overall_validation_score(validation: dict[str, Any]) -> dict[str, Any]:
    weights = {
        "benchmark_alignment": 0.25,
        "internal_consistency": 0.20,
        "coverage": 0.15,
        "question_coverage": 0.15,
        "realism_rubric": 0.25,
    }
    weighted = 0.0
    used = 0.0
    components = {}
    for key, weight in weights.items():
        value = validation.get(key, {}).get("score")
        components[key] = value
        if value is not None:
            weighted += float(value) * weight
            used += weight
    score = round(weighted / used, 1) if used else None
    return {
        "score": score,
        "components": components,
        "interpretation": "Weighted validation confidence across benchmark alignment, stability, coverage, survey construct coverage and judge-style realism.",
    }


def _contradiction_flags(
    grouped: dict[tuple[str, str], list[PersonaResponse]],
    question_by_id: dict[str, SurveyQuestion],
    concept_by_id: dict[str, Concept],
) -> list[dict[str, Any]]:
    flags = []
    for responses in grouped.values():
        likert_values = [
            r.answer_value
            for r in responses
            if r.answer_value is not None and question_by_id.get(r.question_id, None) and question_by_id[r.question_id].type == "likert"
        ]
        price_values = [
            r.answer_value
            for r in responses
            if r.answer_value is not None and question_by_id.get(r.question_id, None) and question_by_id[r.question_id].type == "price"
        ]
        if not likert_values or not price_values:
            continue
        concept = concept_by_id.get(responses[0].concept_id)
        if not concept:
            continue
        mean_likert = sum(likert_values) / len(likert_values)
        mean_price = sum(price_values) / len(price_values)
        if mean_likert <= 2.3 and mean_price >= concept.annual_fee_chf * 1.15 and concept.annual_fee_chf > 0:
            flags.append(_flag(responses[0], "contradiction", "Low adoption but willingness-to-pay is above concept fee."))
        if mean_likert >= 4.2 and mean_price <= concept.annual_fee_chf * 0.35 and concept.annual_fee_chf >= 60:
            flags.append(_flag(responses[0], "contradiction", "High adoption but willingness-to-pay is far below concept fee."))
    return flags


def _flag(response: PersonaResponse, category: str, message: str) -> dict[str, Any]:
    return {
        "category": category,
        "message": message,
        "persona_id": response.persona_id,
        "concept_id": response.concept_id,
        "question_id": response.question_id,
    }


def _count_flags(flags: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for flag in flags:
        counts[flag["category"]] += 1
    return dict(sorted(counts.items()))
