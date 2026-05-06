from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience, not a runtime requirement
    pass

WATSONX_DEFAULT_MODEL_ID = "ibm/granite-4-h-small"
WATSONX_REQUIRED_ENV = ("WATSONX_URL", "WATSONX_PROJECT_ID", "WATSONX_APIKEY")


class LLMError(RuntimeError):
    pass


class BaseLLM(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str) -> Any:
        last_text = ""
        for attempt in range(2):
            active_prompt = prompt if attempt == 0 else _json_repair_prompt(prompt, last_text)
            text = self.generate_text(active_prompt)
            last_text = text
            try:
                return _loads_json_from_text(text)
            except json.JSONDecodeError:
                continue
        raise LLMError(f"Model did not return JSON: {last_text[:500]}")


class MockLLM(BaseLLM):
    """Deterministic offline provider for rehearsal and fallback demos."""

    def generate_text(self, prompt: str) -> str:
        if "synthetic survey respondent" in prompt:
            return json.dumps(self._persona_answer(prompt), ensure_ascii=False)
        if "Visa Consulting & Analytics insight analyst" in prompt:
            return json.dumps(self._analyst_summary(), ensure_ascii=False)
        if "Parse the raw survey" in prompt or "<raw_survey>" in prompt or "JSON extraction engine" in prompt:
            return json.dumps(self._parse_survey(prompt), ensure_ascii=False)
        return json.dumps({"message": "MockLLM fallback"})

    def _parse_survey(self, prompt: str) -> list[dict[str, Any]]:
        raw_matches = re.findall(r"^\s*<raw_survey>\s*(.*?)\s*^\s*</raw_survey>", prompt, flags=re.S | re.I | re.M)
        raw = raw_matches[-1] if raw_matches else prompt.split("RAW_SURVEY:", 1)[-1]
        blocks = self._survey_blocks(raw)
        questions = []
        qid = 1
        for block in blocks:
            line = " ".join(block)
            if len(line) < 8:
                continue
            text = re.sub(r"^\d+[\).:-]?\s*", "", line)
            text = re.sub(r"^Q\d+[\).:-]?\s*", "", text, flags=re.I).strip()
            if re.match(
                r"^(?:scenario|context|background|instructions?|intro|stimulus|source|url|use in this demo)\s*:",
                text,
                flags=re.I,
            ):
                continue
            options = self._extract_choice_options(text)
            text = self._strip_inline_options(text)
            lower = text.lower()
            if options:
                qtype = "choice"
            elif ("feature" in lower or "benefit" in lower) and "why" in lower:
                qtype = "open"
            elif any(k in lower for k in ["choose", "select", "prefer", "rank", "pick"]):
                qtype = "choice"
            elif any(k in lower for k in [
                "likely",
                "likelihood",
                "adopt",
                "attractive",
                "appeal",
                "appealing",
                "relevant",
                "trust",
                "value",
                "quality",
                "innovative",
                "satisfaction",
                "ease",
                "how often",
                "frequency",
            ]):
                qtype = "likert"
            elif re.search(r"\b(price|fee|fees|pay|chf|willingness)\b", lower):
                qtype = "price"
            else:
                qtype = "open"
            questions.append({
                "id": f"Q{qid}",
                "text": text,
                "type": qtype,
                "options": options or (["Concept A", "Concept B", "Neither"] if qtype == "choice" else []),
                "measures": self._measure(lower),
            })
            qid += 1
        if not questions:
            questions = [{"id": "Q1", "text": raw.strip(), "type": "open", "options": [], "measures": "general feedback"}]
        return questions

    @staticmethod
    def _survey_blocks(raw: str) -> list[list[str]]:
        blocks: list[list[str]] = []
        current: list[str] = []
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            is_numbered = bool(re.match(r"^(?:Q\d+|\d+)[\).:-]\s+", line, flags=re.I))
            is_option = bool(re.match(r"^(?:[-*•]|[A-Ha-h][\).])\s+", line))
            is_inline_options = bool(re.match(r"^(?:options?|choices?|answers?|response options?)\s*[:\-]", line, flags=re.I))
            starts_like_question = bool(
                re.match(
                    r"^(?:how|what|which|why|when|where|would|do|does|did|have|has|are|is|can|could|should|"
                    r"please|rate|rank|choose|select|in the past)\b",
                    line,
                    flags=re.I,
                )
            )
            looks_like_new_question = bool(
                current
                and line.endswith("?")
                and len(line) >= 16
                and starts_like_question
                and not is_option
                and not is_inline_options
            )
            if current and (is_numbered or looks_like_new_question):
                blocks.append(current)
                current = [line]
            elif not current:
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append(current)
        return blocks

    @classmethod
    def _extract_choice_options(cls, text: str) -> list[str]:
        option_texts: list[str] = []
        for pattern in [
            r"(?:options?|choices?|answers?|response options?)\s*[:\-]\s*(.+)$",
            r"(?:choose one|select one|pick one|choose from|select from)\s*[:\-]\s*(.+)$",
            r"(?:rank|rate|compare)\s+the\s+following(?:\s+\w+)?\s*[:\-]\s*(.+)$",
            r"which\s+of\s+the\s+following.*?[:\-]\s*(.+)$",
        ]:
            match = re.search(pattern, text, flags=re.I)
            if match:
                option_texts.append(match.group(1))

        parenthetical = re.search(r"\(([^()]{12,180})\)", text)
        if parenthetical and re.search(r"[,;/|]|\bor\b", parenthetical.group(1), flags=re.I):
            option_texts.append(parenthetical.group(1))

        bullet_options = re.findall(r"(?:^|\s)(?:[-*•]|[A-Ha-h][\).])\s*([^;,.?]+)", text)
        if len(bullet_options) >= 2:
            option_texts.append("; ".join(bullet_options))

        for option_text in option_texts:
            options = cls._split_options(option_text)
            if len(options) >= 2:
                return options[:8]
        return []

    @staticmethod
    def _split_options(option_text: str) -> list[str]:
        cleaned = re.sub(r"\band why\b.*$", "", option_text, flags=re.I).strip()
        cleaned = re.sub(r"\.$", "", cleaned)
        parts = re.split(r"\s*(?:;|\||/|,)\s*", cleaned, flags=re.I)
        options = []
        for part in parts:
            option = re.sub(r"^(?:[-*•]|[A-Ha-h][\).])\s*", "", part).strip(" .:;\"'")
            if 1 < len(option) <= 60 and option.lower() not in {"why", "please specify", "other please specify"}:
                options.append(option)
        deduped: list[str] = []
        for option in options:
            if option.lower() not in {x.lower() for x in deduped}:
                deduped.append(option)
        return deduped

    @staticmethod
    def _strip_inline_options(text: str) -> str:
        text = re.sub(r"\s*(?:options?|choices?|answers?|response options?)\s*[:\-].*$", "", text, flags=re.I)
        text = re.sub(r"\s*(?:choose one|select one|pick one|choose from|select from)\s*[:\-].*$", "", text, flags=re.I)
        text = re.sub(r"(\b(?:rank|rate|compare)\s+the\s+following(?:\s+\w+)?)\s*[:\-].*$", r"\1", text, flags=re.I)
        text = re.sub(r"(\bwhich\s+of\s+the\s+following.*?)\s*[:\-].*$", r"\1", text, flags=re.I)
        return text.strip()

    @staticmethod
    def _measure(lower: str) -> str:
        if "barrier" in lower or "concern" in lower or "prevent" in lower:
            return "barriers"
        if any(k in lower for k in [
            "likely",
            "adopt",
            "trust",
            "value",
            "appeal",
            "appealing",
            "quality",
            "innovative",
            "satisfaction",
            "ease",
            "how often",
            "frequency",
        ]):
            return "adoption likelihood"
        if re.search(r"\b(price|fee|fees|pay|chf|willingness)\b", lower):
            return "price sensitivity"
        if any(k in lower for k in ["feature", "benefit", "prefer", "message", "convincing"]):
            return "feature preference"
        return "general feedback"

    def _persona_answer(self, prompt: str) -> dict[str, Any]:
        persona_id = self._extract(prompt, r"Persona ([A-Z0-9_\-]+)") or "P"
        qtype = self._extract(prompt, r"Type: ([a-z]+)") or "open"
        question = self._extract(prompt, r"Text: (.*?)\nOptions:") or ""
        options = self._extract_prompt_options(prompt)
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
            label = self._choose_option(persona_id, concept, features, options, score)
            return {
                "answer_value": score,
                "answer_label": label,
                "answer_text": f"I would choose {label} because it fits my payment habits and budget better.",
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

    @classmethod
    def _extract_prompt_options(cls, prompt: str) -> list[str]:
        raw = cls._extract(prompt, r"Options: (.*?)\nMeasures:")
        if not raw or raw.strip() in {"[]", "None"}:
            return []
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", raw)
        options = [a or b for a, b in quoted]
        if not options:
            options = cls._split_options(raw.strip("[]"))
        return [option for option in options if option]

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

    @classmethod
    def _choose_option(cls, persona_id: str, concept: str, features: str, options: list[str], score: float) -> str:
        if not options:
            return "Concept A" if score >= 4.0 else "Concept B" if score >= 2.8 else "Neither"
        persona_root = persona_id.split("_")[0]
        lower_context = (concept + " " + features).lower()
        option_scores: list[tuple[float, str]] = []
        for option in options:
            lower = option.lower()
            option_score = 0.0
            if persona_root in {"A2", "A4", "A6"}:
                option_score += _contains_any(lower, ["travel", "insurance", "fx", "foreign", "lounge", "premium", "cross-border"]) * 3
                option_score += _contains_any(lower, ["security", "protection", "fraud", "receipt"]) * 1
            elif persona_root in {"A1", "A3", "A7"}:
                option_score += _contains_any(lower, ["cashback", "grocery", "family", "discount", "mobile", "wallet", "protection"]) * 3
                option_score += _contains_any(lower, ["simple", "fee", "transparent"]) * 1
            elif persona_root == "A5":
                option_score += _contains_any(lower, ["cash", "transparent", "control", "privacy", "security", "simple", "fraud"]) * 3
                option_score -= _contains_any(lower, ["digital", "mobile", "wallet", "automatic"]) * 1
            else:
                option_score += _contains_any(lower, ["protection", "receipt", "fx", "business", "expense"]) * 3
            option_score += _contains_any(lower_context, lower.split()) * 0.1
            if score < 2.7 and any(k in lower for k in ["none", "neither", "would not", "no option"]):
                option_score += 5
            option_scores.append((option_score, option))
        return max(option_scores, key=lambda item: item[0])[1]


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

        status = watsonx_config_status()
        url = os.getenv("WATSONX_URL")
        api_key = os.getenv("WATSONX_APIKEY")
        project_id = os.getenv("WATSONX_PROJECT_ID")
        model_id = status["model_id"]
        if not url or not api_key or not project_id:
            missing = ", ".join(status["missing"])
            raise LLMError(f"Missing watsonx.ai configuration: {missing}. Set these in .env or Code Engine env/secrets.")

        self.model_id = model_id
        self.url = url
        self.chat_params = {"temperature": 0.1, "max_tokens": 900}
        self.text_params = {"decoding_method": "greedy", "max_new_tokens": 900}
        credentials = Credentials(url=url, api_key=api_key)
        self.model = ModelInference(
            model_id=model_id,
            credentials=credentials,
            project_id=project_id,
            params=self.text_params,
        )

    def generate_text(self, prompt: str) -> str:  # pragma: no cover - cloud call
        try:
            chat_response = self.model.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an enterprise assistant for a Visa Consulting & Analytics PoC. "
                            "Follow the requested output format exactly. If JSON is requested, return valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                params=self.chat_params,
            )
            return chat_response["choices"][0]["message"]["content"]
        except Exception as exc:
            try:
                return self.model.generate_text(prompt=prompt, params=self.text_params)
            except Exception as text_exc:
                raise _watsonx_error(self.model_id, text_exc) from text_exc


def watsonx_config_status() -> dict[str, Any]:
    missing = [key for key in WATSONX_REQUIRED_ENV if not os.getenv(key)]
    return {
        "configured": not missing,
        "missing": missing,
        "url": os.getenv("WATSONX_URL", ""),
        "project_id_set": bool(os.getenv("WATSONX_PROJECT_ID")),
        "api_key_set": bool(os.getenv("WATSONX_APIKEY")),
        "model_id": os.getenv("WATSONX_MODEL_ID", WATSONX_DEFAULT_MODEL_ID),
    }


def get_llm(provider: str | None = None) -> BaseLLM:
    provider = (provider or os.getenv("MODEL_PROVIDER", "auto")).lower()
    if provider == "auto":
        provider = "watsonx" if watsonx_config_status()["configured"] else "mock"
    if provider == "watsonx":
        return WatsonxLLM()
    return MockLLM()


def _contains_any(text: str, needles: list[str]) -> int:
    return int(any(needle and needle in text for needle in needles))


def _json_repair_prompt(original_prompt: str, bad_text: str) -> str:
    return (
        "The previous response was not valid JSON. Return only the JSON required by the original task. "
        "Do not include explanations, markdown fences, commentary, or extra generated questions.\n\n"
        f"ORIGINAL_TASK:\n{original_prompt}\n\n"
        f"PREVIOUS_RESPONSE:\n{bad_text[:1200]}\n\n"
        "VALID_JSON_ONLY:"
    )


def _loads_json_from_text(text: str) -> Any:
    cleaned = text.strip()
    if not cleaned:
        raise json.JSONDecodeError("empty response", text, 0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        payload = _extract_json_payload(cleaned)
        if payload is None:
            raise
        return json.loads(payload)


def _extract_json_payload(text: str) -> str | None:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.I)
    if fence:
        text = fence.group(1).strip()

    for start, open_char, close_char in ((text.find("["), "[", "]"), (text.find("{"), "{", "}")):
        if start < 0:
            continue
        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(text)):
            char = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return text[start:idx + 1]
    return None


def _watsonx_error(model_id: str, exc: Exception) -> LLMError:
    message = str(exc)
    if "token_quota_reached" in message:
        return LLMError(
            "watsonx.ai authentication succeeded, but the IBM Runtime token quota is exhausted for this account/project. "
            "Ask IBM to restore or increase quota, or switch to the deterministic mock provider only for rehearsal."
        )
    if "not supported for this environment" in message or "model_no_support" in message:
        return LLMError(
            f"watsonx.ai model '{model_id}' is not available for the current Frankfurt project. "
            "Set WATSONX_MODEL_ID to a model listed as supported in this environment."
        )
    return LLMError(f"watsonx.ai generation failed: {message}")
