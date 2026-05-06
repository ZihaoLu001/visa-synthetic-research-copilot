from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .llm import BaseLLM
from .prompts import persona_response_prompt, survey_parser_prompt
from .schemas import Concept, Persona, PersonaResponse, SurveyQuestion


class SurveyParserAgent:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def parse(self, raw_survey: str) -> list[SurveyQuestion]:
        rows = self.llm.generate_json(survey_parser_prompt(raw_survey))
        if isinstance(rows, dict):
            rows = rows.get("questions") or rows.get("items") or []
        questions: list[SurveyQuestion] = []
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            qtype = _normalise_question_type(row.get("type", "open"), row.get("text", ""))
            qid = str(row.get("id") or f"Q{i}")
            if qid.isdigit():
                qid = f"Q{qid}"
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            questions.append(SurveyQuestion(
                id=qid,
                text=text,
                type=qtype,
                options=row.get("options") or [],
                measures=row.get("measures") or "general feedback",
            ))
        if not questions and raw_survey.strip():
            questions.append(SurveyQuestion(id="Q1", text=raw_survey.strip(), type="open", measures="general feedback"))
        return questions


class PersonaAgent:
    def __init__(self, llm: BaseLLM, benchmark_context: str):
        self.llm = llm
        self.benchmark_context = benchmark_context

    def answer(
        self,
        run_id: str,
        persona: Persona,
        concept: Concept,
        question: SurveyQuestion,
        prior_answers: list[PersonaResponse] | None = None,
    ) -> PersonaResponse:
        prior_json = [r.asdict() for r in (prior_answers or [])]
        data = self.llm.generate_json(persona_response_prompt(
            persona=persona,
            concept=concept,
            question=question,
            benchmark_context=self.benchmark_context,
            prior_answers=prior_json,
        ))
        return PersonaResponse(
            run_id=run_id,
            persona_id=persona.id,
            persona_name=persona.name,
            persona_weight=persona.weight,
            concept_id=concept.id,
            question_id=question.id,
            question_type=question.type,
            answer_value=_to_float_or_none(data.get("answer_value")),
            answer_label=data.get("answer_label"),
            answer_text=str(data.get("answer_text", "")),
            rationale=str(data.get("rationale", "")),
            confidence=float(data.get("confidence", 0.7)),
        )


class InsightAnalystAgent:
    """Lightweight deterministic analyst. Can be replaced by an LLM analyst prompt."""

    @staticmethod
    def summarize(aggregate: dict[str, Any]) -> dict[str, Any]:
        by_concept = aggregate.get("concept_summary", {})
        if not by_concept:
            return {}
        best_id, best_summary = max(by_concept.items(), key=lambda kv: kv[1].get("mean_likert", 0.0))
        barriers = [name for name, _ in aggregate.get("top_barrier_signals", [])[:4]]
        labels_by_concept = aggregate.get("top_answer_labels_by_concept", {})
        price = aggregate.get("price_summary", {}).get(best_id, {})
        segment_fit = aggregate.get("segment_fit", {})
        strongest_segments = [
            key for key, _ in sorted(segment_fit.items(), key=lambda kv: kv[1] or 0, reverse=True)[:3]
            if key.startswith(f"{best_id}:")
        ]
        return {
            "recommendation": f"Use concept {best_id} as the leading proposition for the next validation round, subject to benchmark and human validation.",
            "why": f"It has the highest weighted adoption index ({best_summary.get('adoption_index_0_100')}/100) in the synthetic panel.",
            "strongest_segments": strongest_segments,
            "pricing_signal": (
                f"Mean acceptable fee is about CHF {int(price['weighted_mean_chf'])}."
                if price.get("weighted_mean_chf") is not None
                else "No price question detected in this run."
            ),
            "top_signals": [name for name, _ in labels_by_concept.get(best_id, [])[:5]],
            "watchouts": barriers or ["synthetic outputs require real customer validation"],
            "next_test": [
                "Run the same survey with one fee or feature changed to stress-test sensitivity.",
                "Use the highest-variance questions as candidates for real customer interviews.",
                "Compare segment-level findings with Visa internal studies once available.",
            ],
            "do_not_overclaim": "Synthetic responses are directional; they should complement, not replace, real customer evidence for final decisions.",
        }


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalise_question_type(raw_type: Any, text: Any = "") -> str:
    qtype = str(raw_type or "open").strip().lower().replace("-", "_")
    question_text = str(text or "").lower()
    if qtype in {"likert", "scale", "rating", "ordinal"}:
        return "likert"
    if qtype in {"price", "numeric", "number", "currency", "willingness_to_pay"}:
        return "price"
    if qtype in {"choice", "multiple_choice", "single_choice", "select", "categorical"}:
        return "choice"
    if qtype in {"open", "open_text", "free_text", "text"}:
        return "open"
    if any(token in question_text for token in ["fee", "chf", "price", "willingness to pay", "pay per year"]):
        return "price"
    if any(token in question_text for token in ["likely", "trust", "relevant", "satisfied", "appealing", "rate"]):
        return "likert"
    return "open"
