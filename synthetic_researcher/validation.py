from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .schemas import Persona, PersonaResponse


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
    return {
        "score": round(score, 1),
        "avg_likert_std": round(avg_std, 3),
        "tested_items": len(stds),
        "interpretation": "Low variance suggests persona responses are stable across repeated runs; too-low variance may also indicate insufficient diversity.",
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
