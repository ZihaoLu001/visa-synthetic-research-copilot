from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any


class LLMError(RuntimeError):
    pass


class BaseLLM(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str) -> Any:
        text = self.generate_text(prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
            if not match:
                raise LLMError(f"Model did not return JSON: {text[:500]}")
            return json.loads(match.group(1))


class MockLLM(BaseLLM):
    """Deterministic offline provider for rehearsal and fallback demos."""

    def generate_text(self, prompt: str) -> str:
        if "Parse the raw survey" in prompt:
            return json.dumps(self._parse_survey(prompt), ensure_ascii=False)
        if "synthetic survey respondent" in prompt:
            return json.dumps(self._persona_answer(prompt), ensure_ascii=False)
        if "Visa Consulting & Analytics insight analyst" in prompt:
            return json.dumps(self._analyst_summary(), ensure_ascii=False)
        return json.dumps({"message": "MockLLM fallback"})

    def _parse_survey(self, prompt: str) -> list[dict[str, Any]]:
        raw = prompt.split("RAW_SURVEY:", 1)[-1]
        lines = [x.strip(" -\t") for x in raw.splitlines() if x.strip()]
        questions = []
        qid = 1
        for line in lines:
            if len(line) < 8:
                continue
            text = re.sub(r"^\d+[\).:-]?\s*", "", line)
            lower = text.lower()
            if re.search(r"\b(price|fee|fees|pay|chf|willingness)\b", lower):
                qtype = "price"
            elif ("feature" in lower or "benefit" in lower) and "why" in lower:
                qtype = "open"
            elif any(k in lower for k in ["choose", "select", "prefer"]):
                qtype = "choice"
            elif any(k in lower for k in ["likely", "likelihood", "adopt", "attractive", "relevant", "trust", "value"]):
                qtype = "likert"
            else:
                qtype = "open"
            questions.append({
                "id": f"Q{qid}",
                "text": text,
                "type": qtype,
                "options": ["Concept A", "Concept B", "Neither"] if qtype == "choice" else [],
                "measures": self._measure(lower),
            })
            qid += 1
        if not questions:
            questions = [{"id": "Q1", "text": raw.strip(), "type": "open", "options": [], "measures": "general feedback"}]
        return questions

    @staticmethod
    def _measure(lower: str) -> str:
        if re.search(r"\b(price|fee|fees|pay|chf|willingness)\b", lower):
            return "price sensitivity"
        if "feature" in lower or "benefit" in lower or "prefer" in lower:
            return "feature preference"
        if "barrier" in lower or "concern" in lower or "prevent" in lower:
            return "barriers"
        if "likely" in lower or "adopt" in lower or "trust" in lower or "value" in lower:
            return "adoption likelihood"
        return "general feedback"

    def _persona_answer(self, prompt: str) -> dict[str, Any]:
        persona_id = self._extract(prompt, r"Persona ([A-Z0-9_\-]+)") or "P"
        qtype = self._extract(prompt, r"Type: ([a-z]+)") or "open"
        question = self._extract(prompt, r"Text: (.*?)\nOptions:") or ""
        measures = self._extract(prompt, r"Measures: (.*?)(?:\n|$)") or ""
        fee = float(self._extract(prompt, r"Annual fee CHF: ([0-9.]+)") or 0)
        concept = self._extract(prompt, r"Name: (.*?)\nDescription:") or "concept"
        features = self._extract(prompt, r"Features: (.*?)\nTarget context:") or ""
        score = self._base_score(persona_id, concept, features, fee)
        question_lower = question.lower()
        measures_lower = measures.lower()

        if qtype == "price" or re.search(r"\b(price|fee|fees|pay|chf|willingness)\b", question_lower):
            value = self._acceptable_fee(persona_id, features)
            return {
                "answer_value": value,
                "answer_label": f"CHF {int(value)}",
                "answer_text": f"I would consider paying around CHF {int(value)} per year if the benefits are clear.",
                "rationale": self._rationale(persona_id, concept, fee, features),
                "confidence": 0.78,
            }
        if qtype == "choice":
            label = "Concept A" if score >= 4.0 else "Concept B" if score >= 2.8 else "Neither"
            return {
                "answer_value": score,
                "answer_label": label,
                "answer_text": f"I would lean toward {label} because it fits my payment habits and budget better.",
                "rationale": self._rationale(persona_id, concept, fee, features),
                "confidence": 0.76,
            }
        if qtype == "likert":
            return {
                "answer_value": score,
                "answer_label": f"{score}/5",
                "answer_text": self._human_quote(score, concept, fee),
                "rationale": self._rationale(persona_id, concept, fee, features),
                "confidence": 0.80,
            }
        if "feature" in question_lower or "benefit" in question_lower or "feature preference" in measures_lower:
            feature = self._feature_signal(persona_id, features)
            return {
                "answer_value": None,
                "answer_label": feature,
                "answer_text": f"The most valuable element for me would be {feature}, because it is the part I can imagine using regularly.",
                "rationale": self._rationale(persona_id, concept, fee, features),
                "confidence": 0.77,
            }
        if "barrier" in question_lower or "prevent" in question_lower or "concern" in question_lower or "barrier" in measures_lower:
            barrier = self._barrier_signal(persona_id, concept, fee, features)
            return {
                "answer_value": None,
                "answer_label": barrier,
                "answer_text": f"The main barrier would be {barrier}; I would need proof that this card is better than what I already use.",
                "rationale": self._rationale(persona_id, concept, fee, features),
                "confidence": 0.76,
            }
        return {
            "answer_value": None,
            "answer_label": self._feature_signal(persona_id, features) if score >= 3.2 else self._barrier_signal(persona_id, concept, fee, features),
            "answer_text": self._human_quote(score, concept, fee),
            "rationale": self._rationale(persona_id, concept, fee, features),
            "confidence": 0.74,
        }

    @staticmethod
    def _extract(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, re.S)
        return match.group(1).strip() if match else None

    @staticmethod
    def _base_score(persona_id: str, concept: str, features: str, fee: float) -> float:
        persona_root = persona_id.split("_")[0]
        premium_ids = {"A2", "A4", "A6"}
        everyday_ids = {"A1", "A3", "A5"}
        nudge = ((sum(ord(ch) for ch in persona_id) % 7) - 3) * 0.05
        score = 3.0
        lower = (concept + " " + features).lower()
        if persona_root in premium_ids:
            score += 0.8 if any(k in lower for k in ["travel", "lounge", "fx", "premium", "insurance"]) else -0.1
            score -= max(0, fee - 120) / 120
        elif persona_root in everyday_ids:
            score += 0.8 if any(k in lower for k in ["cashback", "everyday", "budget", "family", "protection"]) else -0.2
            score -= max(0, fee - 60) / 80
        else:
            score += 0.3 if "protection" in lower else 0.0
            score -= max(0, fee - 80) / 100
        return round(max(1.0, min(5.0, score + nudge)), 1)

    @staticmethod
    def _acceptable_fee(persona_id: str, features: str) -> float:
        persona_root = persona_id.split("_")[0]
        base = {"A1": 25, "A2": 90, "A3": 45, "A4": 150, "A5": 20, "A6": 85, "A7": 55}.get(persona_root, 60)
        lower = features.lower()
        if "cashback" in lower:
            base += 10
        if "travel" in lower or "insurance" in lower:
            base += 15
        if "protection" in lower:
            base += 8
        return float(base)

    @staticmethod
    def _human_quote(score: float, concept: str, fee: float) -> str:
        if score >= 4.2:
            return f"This feels useful for me. I can see clear occasions where I would use {concept}, and the CHF {int(fee)} fee can be justified if the benefits are easy to understand."
        if score >= 3.2:
            return f"I see some value in {concept}, but I would compare it with my current card first. The fee and the real monthly benefit need to be very clear."
        return f"I am not convinced yet. Some features are interesting, but CHF {int(fee)} feels high for what I would actually use."

    @staticmethod
    def _feature_signal(persona_id: str, features: str) -> str:
        persona_root = persona_id.split("_")[0]
        lower = features.lower()
        if persona_root in {"A2", "A4", "A6"}:
            for label in ["FX fee reduction", "travel insurance", "lounge vouchers", "purchase protection"]:
                if label.lower() in lower:
                    return label
        if persona_root in {"A1", "A3", "A7"}:
            for label in ["grocery cashback", "family offers", "mobile wallet", "purchase protection"]:
                if label.lower() in lower:
                    return label
        if persona_root == "A5":
            for label in ["transparent fees", "purchase protection", "simple onboarding", "cashback"]:
                if label.lower() in lower:
                    return label
        for label in re.findall(r"[A-Za-z][A-Za-z /-]+", features):
            cleaned = label.strip(" '\"")
            if len(cleaned) > 3 and cleaned.lower() not in {"features", "target context"}:
                return cleaned
        return "clear, practical everyday value"

    @staticmethod
    def _barrier_signal(persona_id: str, concept: str, fee: float, features: str) -> str:
        persona_root = persona_id.split("_")[0]
        lower = (concept + " " + features).lower()
        if persona_root in {"A1", "A3", "A5"} and fee >= 60:
            return "annual fee sensitivity"
        if persona_root == "A5" and any(k in lower for k in ["mobile", "digital", "wallet"]):
            return "digital trust and control concerns"
        if persona_root in {"A2", "A4", "A6"} and not any(k in lower for k in ["travel", "fx", "insurance", "lounge"]):
            return "limited travel or premium relevance"
        if "cashback" not in lower and persona_root in {"A1", "A3", "A7"}:
            return "unclear everyday value"
        return "unclear incremental value versus current card"

    @staticmethod
    def _rationale(persona_id: str, concept: str, fee: float, features: str) -> str:
        lower = features.lower()
        persona_root = persona_id.split("_")[0]
        if persona_root in {"A1", "A3", "A5"}:
            return "Price-sensitive segment; everyday value, cashback, family usefulness, and trust messaging matter more than premium travel benefits."
        if persona_root in {"A2", "A4", "A6"}:
            return "Travel- or card-oriented segment; insurance, FX savings, convenience, and premium service can justify a higher fee."
        if "protection" in lower:
            return "Protection messaging improves trust, but the proposition still needs simple proof points."
        return "Response reflects the persona's payment habits, income band, and stated attitudes."

    @staticmethod
    def _analyst_summary() -> dict[str, Any]:
        return {
            "executive_summary": "The synthetic panel indicates which concept is directionally stronger by segment, but the result should be treated as hypothesis support rather than final customer evidence.",
            "adoption_drivers": ["clear monthly value", "trust and purchase protection", "travel/FX benefits for frequent travelers"],
            "barriers": ["annual fee", "unclear benefit usage", "low relevance for non-travel segments"],
            "segment_recommendations": ["Use everyday-value positioning for families and students", "Use premium travel positioning for frequent travelers", "Use cash/control reassurance for older or privacy-sensitive customers"],
            "next_test_questions": ["What annual fee feels acceptable?", "Which benefit would trigger switching?", "Which current card or payment method would this replace?"],
        }


class WatsonxLLM(BaseLLM):
    """IBM watsonx.ai provider. Requires ibm-watsonx-ai and environment variables."""

    def __init__(self):
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference
        except Exception as exc:  # pragma: no cover - optional dependency
            raise LLMError("Install ibm-watsonx-ai to use WatsonxLLM") from exc

        url = os.getenv("WATSONX_URL")
        api_key = os.getenv("WATSONX_APIKEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
        if not url or not api_key or not project_id:
            raise LLMError("Missing WATSONX_URL, WATSONX_APIKEY, or WATSONX_PROJECT_ID")

        credentials = Credentials(url=url, api_key=api_key)
        self.model = ModelInference(
            model_id=model_id,
            credentials=credentials,
            project_id=project_id,
            params={"decoding_method": "sample", "temperature": 0.25, "max_new_tokens": 900, "top_p": 0.9},
        )

    def generate_text(self, prompt: str) -> str:  # pragma: no cover - cloud call
        return self.model.generate_text(prompt=prompt)


def get_llm(provider: str | None = None) -> BaseLLM:
    provider = (provider or os.getenv("MODEL_PROVIDER", "mock")).lower()
    if provider == "watsonx":
        return WatsonxLLM()
    return MockLLM()
