from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .schemas import PersonaResponse


def weighted_mean(values: list[tuple[float, float]]) -> float | None:
    total_w = sum(w for _, w in values)
    if total_w == 0:
        return None
    return sum(v * w for v, w in values) / total_w


def aggregate_responses(responses: list[PersonaResponse]) -> dict[str, Any]:
    concept_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    question_values: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    price_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    choice_values: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    adoption_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    barriers: Counter[str] = Counter()
    answer_labels: Counter[str] = Counter()
    answer_labels_by_concept: dict[str, Counter[str]] = defaultdict(Counter)
    quotes: dict[str, list[str]] = defaultdict(list)
    segment_fit: dict[str, list[tuple[float, float]]] = defaultdict(list)
    confidence_values: list[float] = []
    respondent_ids = set()

    for r in responses:
        respondent_ids.add(r.persona_id)
        confidence_values.append(r.confidence)
        if r.answer_value is not None and r.question_type == "likert":
            concept_values[r.concept_id].append((r.answer_value, r.persona_weight))
            question_values[(r.concept_id, r.question_id)].append((r.answer_value, r.persona_weight))
            root_persona = r.persona_id.split("_")[0]
            segment_fit[f"{r.concept_id}:{root_persona}"].append((r.answer_value, r.persona_weight))
            adoption_buckets[r.concept_id][_bucket_likert(r.answer_value)] += 1
        if r.answer_value is not None and r.question_type == "price":
            price_values[r.concept_id].append((r.answer_value, r.persona_weight))
        if r.answer_label:
            label = str(r.answer_label)
            answer_labels[label] += 1
            answer_labels_by_concept[r.concept_id][label] += 1
            if r.question_type == "choice":
                choice_values[(r.concept_id, r.question_id)][label] += 1
        if r.answer_text:
            quotes[r.concept_id].append(f"{r.persona_name}: {r.answer_text}")
        rationale = (r.rationale or "").lower()
        for term in [
            "annual fee",
            "fee",
            "unclear",
            "trust",
            "privacy",
            "digital",
            "travel",
            "premium",
            "everyday",
            "cashback",
            "protection",
            "switching",
        ]:
            if term in rationale:
                barriers[term] += 1

    concept_summary = {}
    for concept_id, vals in concept_values.items():
        mean = weighted_mean(vals)
        concept_summary[concept_id] = {
            "mean_likert": round(mean, 2) if mean is not None else None,
            "adoption_index_0_100": round(((mean or 1) - 1) / 4 * 100, 1) if mean is not None else None,
            "respondents": len(vals),
            "bucket_counts": dict(adoption_buckets.get(concept_id, {})),
        }

    question_summary = {}
    for (concept_id, question_id), vals in question_values.items():
        mean = weighted_mean(vals)
        question_summary[f"{concept_id}:{question_id}"] = round(mean, 2) if mean is not None else None

    price_summary = {}
    for concept_id, vals in price_values.items():
        mean = weighted_mean(vals)
        raw_values = [v for v, _ in vals]
        price_summary[concept_id] = {
            "weighted_mean_chf": round(mean, 0) if mean is not None else None,
            "min_chf": round(min(raw_values), 0) if raw_values else None,
            "max_chf": round(max(raw_values), 0) if raw_values else None,
            "responses": len(raw_values),
        }

    segment_summary = {}
    for key, vals in segment_fit.items():
        mean = weighted_mean(vals)
        segment_summary[key] = round(mean, 2) if mean is not None else None

    return {
        "respondent_count": len(respondent_ids),
        "response_count": len(responses),
        "avg_confidence": round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else None,
        "concept_summary": concept_summary,
        "question_summary": question_summary,
        "price_summary": price_summary,
        "choice_summary": {f"{c}:{q}": counter.most_common() for (c, q), counter in choice_values.items()},
        "segment_fit": segment_summary,
        "top_barrier_signals": barriers.most_common(8),
        "top_answer_labels": answer_labels.most_common(10),
        "top_answer_labels_by_concept": {
            concept_id: counter.most_common(8)
            for concept_id, counter in answer_labels_by_concept.items()
        },
        "sample_quotes": {k: v[:5] for k, v in quotes.items()},
    }


def _bucket_likert(value: float) -> str:
    if value >= 4.0:
        return "promoter"
    if value >= 3.0:
        return "considerer"
    return "skeptic"
