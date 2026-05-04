from __future__ import annotations

import copy
import math
import random
from pathlib import Path
from typing import Any

import yaml

from .schemas import Persona


def load_yaml(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_personas(path: str | Path) -> list[Persona]:
    rows = load_yaml(path)["personas"]
    return [Persona(**row) for row in rows]


def expand_to_micro_population(archetypes: list[Persona], target_n: int = 96, seed: int = 42) -> list[Persona]:
    """Expand weighted archetypes into a deterministic micro-population.

    Each micro-persona keeps the same demographic profile but receives a stable ID and
    slight attitude variation, so the final demo can show many synthetic respondents
    without pretending to have real customer data.
    """
    if target_n <= len(archetypes):
        return archetypes[:target_n]
    rng = random.Random(seed)
    total = sum(max(p.weight, 0.0) for p in archetypes)
    if total <= 0:
        raise ValueError("Persona weights must be positive")

    counts = []
    remainder = []
    allocated = 0
    for p in archetypes:
        raw = p.weight / total * target_n
        c = max(1, int(math.floor(raw)))
        counts.append(c)
        remainder.append(raw - c)
        allocated += c
    while allocated < target_n:
        idx = max(range(len(remainder)), key=lambda i: remainder[i])
        counts[idx] += 1
        remainder[idx] = 0
        allocated += 1
    while allocated > target_n:
        idx = max(range(len(counts)), key=lambda i: counts[i])
        counts[idx] -= 1
        allocated -= 1

    population: list[Persona] = []
    for p, count in zip(archetypes, counts):
        micro_weight = p.weight / count
        for i in range(count):
            attitudes = copy.deepcopy(p.attitudes)
            for key, value in attitudes.items():
                if isinstance(value, (int, float)):
                    attitudes[key] = round(min(1.0, max(0.0, value + rng.uniform(-0.05, 0.05))), 3)
            population.append(Persona(
                id=f"{p.id}_{i+1:02d}",
                name=f"{p.name} #{i+1}",
                weight=micro_weight,
                age_band=p.age_band,
                region=p.region,
                language_region=p.language_region,
                income_band=p.income_band,
                household=p.household,
                education=p.education,
                lifestyle=p.lifestyle,
                payment_profile=p.payment_profile,
                attitudes=attitudes,
                source_notes=p.source_notes,
            ))
    return population


def load_benchmark_context(path: str | Path) -> str:
    data = load_yaml(path)
    lines = []
    for item in data.get("anchors", []):
        url = item.get("url")
        suffix = f" ({item['source']}; {url})" if url else f" ({item['source']})"
        lines.append(f"- {item['name']}: {item['value']}{suffix}")
    for profile in data.get("benchmark_profiles", {}).values():
        mix = ", ".join(f"{k} {v}%" for k, v in profile.get("payment_mix", {}).items())
        lines.append(f"- {profile['label']}: {mix} ({profile['source']})")
    return "\n".join(lines)


def load_benchmark_data(path: str | Path) -> dict[str, Any]:
    return load_yaml(path)
