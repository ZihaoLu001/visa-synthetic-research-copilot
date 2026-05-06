from synthetic_researcher.survey_scope import limit_survey_questions


def test_limit_survey_questions_preserves_preamble_and_first_questions():
    raw = """Source: public questionnaire
URL: https://example.com

1. How likely are you to adopt this card?
Options: very likely; somewhat likely; not likely
2. What annual fee would be acceptable?
3. What is the main barrier?
4. Which feature is most valuable?"""

    scoped = limit_survey_questions(raw, 2)

    assert "Source: public questionnaire" in scoped
    assert "1. How likely" in scoped
    assert "2. What annual fee" in scoped
    assert "3. What is the main barrier" not in scoped


def test_limit_survey_questions_returns_original_when_no_numbered_questions():
    raw = "How likely are you to adopt this card?\nWhat fee is acceptable?"

    assert limit_survey_questions(raw, 2) == raw
