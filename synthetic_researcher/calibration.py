from __future__ import annotations

from collections import defaultdict
from typing import Any

from .sampler import expand_to_micro_population
from .schemas import Persona


CALIBRATION_FIELDS = [
    "age_band",
    "language_region",
    "income_band",
    "household",
    "education",
]


def build_panel_calibration(
    archetypes: list[Persona],
    benchmark_data: dict[str, Any],
    target_n: int = 96,
) -> dict[str, Any]:
    """Build a transparent calibration snapshot for the synthetic Swiss panel.

    This is not a claim that the synthetic panel is a fully representative survey
    sample. It exposes the weights and public benchmark anchors so consultants can
    inspect whether the panel is plausible enough for early-stage hypothesis work.
    """
    micro_panel = expand_to_micro_population(archetypes, target_n=target_n)
    synthetic_payment_mix = _weighted_payment_mix(micro_panel)
    benchmark_profiles = _benchmark_profiles(benchmark_data)

    return {
        "target_n": target_n,
        "archetype_count": len(archetypes),
        "micro_population_count": len(micro_panel),
        "persona_weights": _persona_weights(archetypes),
        "demographic_distributions": {
            field: _weighted_distribution(micro_panel, field)
            for field in CALIBRATION_FIELDS
        },
        "synthetic_payment_mix": synthetic_payment_mix,
        "benchmark_profiles": benchmark_profiles,
        "payment_comparison": _payment_comparison_rows(synthetic_payment_mix, benchmark_profiles),
        "public_anchors": benchmark_data.get("anchors", []),
        "interpretation": (
            "Use this table as a calibration surface. If Visa has internal customer "
            "research, compare it here and adjust persona weights before production use."
        ),
    }


def _persona_weights(archetypes: list[Persona]) -> list[dict[str, Any]]:
    total = sum(max(p.weight, 0.0) for p in archetypes) or 1.0
    return [
        {
            "persona_id": p.id,
            "persona": p.name,
            "weight_share_pct": round(p.weight / total * 100, 1),
            "age_band": p.age_band,
            "language_region": p.language_region,
            "income_band": p.income_band,
            "household": p.household,
            "region": p.region,
        }
        for p in archetypes
    ]


def _weighted_distribution(personas: list[Persona], field: str) -> list[dict[str, Any]]:
    totals: dict[str, float] = defaultdict(float)
    total_weight = sum(max(p.weight, 0.0) for p in personas) or 1.0
    for persona in personas:
        label = str(getattr(persona, field))
        totals[label] += max(persona.weight, 0.0)
    return [
        {"segment": key, "share_pct": round(value / total_weight * 100, 1)}
        for key, value in sorted(totals.items(), key=lambda item: item[0])
    ]


def _weighted_payment_mix(personas: list[Persona]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    total_weight = sum(max(p.weight, 0.0) for p in personas) or 1.0
    for persona in personas:
        for method, share in persona.payment_profile.items():
            totals[method] += max(persona.weight, 0.0) * float(share)
    return {
        method: round(value / total_weight * 100, 1)
        for method, value in sorted(totals.items())
    }


def _benchmark_profiles(benchmark_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for profile_id, profile in (benchmark_data.get("benchmark_profiles") or {}).items():
        rows.append(
            {
                "profile_id": profile_id,
                "label": profile.get("label"),
                "context": profile.get("context"),
                "source": profile.get("source"),
                "url": profile.get("url"),
                "payment_mix": profile.get("payment_mix", {}),
            }
        )
    return rows


def _payment_comparison_rows(
    synthetic_payment_mix: dict[str, float],
    benchmark_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    methods = set(synthetic_payment_mix)
    for profile in benchmark_profiles:
        methods.update(profile.get("payment_mix", {}))

    rows: list[dict[str, Any]] = []
    for method in sorted(methods):
        row: dict[str, Any] = {
            "method": method,
            "synthetic_panel_pct": synthetic_payment_mix.get(method, 0.0),
        }
        for profile in benchmark_profiles:
            label = str(profile.get("label") or profile.get("profile_id"))
            row[label] = profile.get("payment_mix", {}).get(method)
        rows.append(row)
    return rows
