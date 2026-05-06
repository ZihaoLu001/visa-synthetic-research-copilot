from __future__ import annotations

import re


def limit_survey_questions(raw_survey: str, max_questions: int | None) -> str:
    """Keep the first N numbered survey questions while preserving source preamble.

    This is used only as an optional live-model proof control. Reviewers can upload
    a full PDF survey, inspect the full extracted text, then run a smaller first
    slice through watsonx.ai to conserve quota during presentations.
    """
    if max_questions is None or max_questions <= 0:
        return raw_survey

    lines = raw_survey.splitlines()
    preamble: list[str] = []
    blocks: list[list[str]] = []
    current: list[str] = []
    seen_question = False

    for line in lines:
        stripped = line.strip()
        is_question_start = bool(re.match(r"^(?:Q\d+|\d+)[\).:-]\s+", stripped, flags=re.I))

        if is_question_start:
            seen_question = True
            if current:
                blocks.append(current)
            current = [line]
            continue

        if not seen_question:
            preamble.append(line)
        elif current:
            current.append(line)

    if current:
        blocks.append(current)

    if not blocks:
        return raw_survey

    scoped_lines = preamble + [line for block in blocks[:max_questions] for line in block]
    return "\n".join(scoped_lines).strip()
