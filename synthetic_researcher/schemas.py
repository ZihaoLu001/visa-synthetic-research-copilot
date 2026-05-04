from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

QuestionType = Literal["likert", "choice", "open", "price"]


@dataclass(frozen=True)
class Concept:
    id: str
    name: str
    description: str
    annual_fee_chf: float = 0.0
    features: list[str] = field(default_factory=list)
    target_context: str = "Swiss consumer card value proposition"


@dataclass(frozen=True)
class SurveyQuestion:
    id: str
    text: str
    type: QuestionType = "open"
    options: list[str] = field(default_factory=list)
    scale_min: int = 1
    scale_max: int = 5
    measures: str = "general feedback"


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    weight: float
    age_band: str
    region: str
    language_region: str
    income_band: str
    household: str
    education: str
    lifestyle: str
    payment_profile: dict[str, float]
    attitudes: dict[str, float]
    source_notes: list[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        return (
            f"Persona {self.id} - {self.name}\n"
            f"Weight: {self.weight}\n"
            f"Age: {self.age_band}; region: {self.region}; language region: {self.language_region}\n"
            f"Income: {self.income_band}; household: {self.household}; education: {self.education}\n"
            f"Lifestyle: {self.lifestyle}\n"
            f"Payment profile: {self.payment_profile}\n"
            f"Attitudes: {self.attitudes}\n"
            f"Source anchors: {self.source_notes}"
        )


@dataclass
class PersonaResponse:
    run_id: str
    persona_id: str
    persona_name: str
    persona_weight: float
    concept_id: str
    question_id: str
    question_type: QuestionType
    answer_value: float | None
    answer_label: str | None
    answer_text: str
    rationale: str
    confidence: float

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SurveyRun:
    run_id: str
    concepts: list[Concept]
    questions: list[SurveyQuestion]
    personas: list[Persona]
    responses: list[PersonaResponse]
    aggregate: dict[str, Any]
    validation: dict[str, Any]

    def asdict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "concepts": [asdict(c) for c in self.concepts],
            "questions": [asdict(q) for q in self.questions],
            "personas": [asdict(p) for p in self.personas],
            "responses": [r.asdict() for r in self.responses],
            "aggregate": self.aggregate,
            "validation": self.validation,
        }
