# External Survey Testing Evidence

This note records the extra acceptance tests added after reviewing public concept-testing and payment-survey examples. The goal is to prove that the prototype can process realistic, flexible survey inputs, not only the built-in Visa demo questions.

## Public References Used

- Qualtrics describes concept tests as early-stage research and highlights liking, follow-up, purchase intent, frequency of use, replacement/addition, product attribute assessment, ranking, rating, and open-field questions.
- SurveyMonkey concept-development guidance lists sample product-concept questions around first reaction, quality, innovation, need, value for money, use intent, replacement, and liked features.
- SurveyMonkey idea-screening guidance describes fast early-stage testing and industry-standard questions such as 5-point purchase intent and open-ended likes.
- The Federal Reserve mobile financial services questionnaire shows payment-behavior survey structures around banking, mobile payments, security, shopping behavior, and payment usage.
- The Federal Reserve 2023 consumer payments brief highlights payment-method usage, digital wallet growth, convenience, fraud concern, and trust in traditional banks as useful payment-behavior themes.

## Test Files

| File | Purpose | Key question types |
| --- | --- | --- |
| `demo/external_survey_tests/concept_test_qualtrics_surveymonkey_style.txt` | Concept-test acceptance survey | appeal, adoption intent, explicit feature choices, ranking, price, replacement/addition, barriers |
| `demo/external_survey_tests/payment_behavior_federal_reserve_style.txt` | Payment-behavior and trust interview guide | payment method choice, mobile-wallet trust, pain points, privacy/control concerns, fee acceptance |
| `demo/external_survey_tests/pricing_message_value_proposition_test.txt` | Pricing and message sensitivity test | relevance/adoption, acceptable fee, message preference, use case fit, barrier, live fee-change sensitivity |

## What Was Improved

The deterministic fallback parser now handles externally sourced survey patterns more realistically:

- `Options: ...` / `Choices: ...` inline options.
- `Which of the following ...:` option lists.
- `Rank the following ...:` feature lists.
- Persona agents now answer choice questions using the provided options instead of generic placeholder labels.

This matters for final-demo reliability because the Visa team may paste a marketing research survey with explicit feature, barrier, or payment-method choices.

## How To Run

Local tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Cloud API stress tests:

```powershell
.\scripts\run_external_survey_tests.ps1
```

The script posts each survey to the deployed FastAPI endpoint and checks that questions, synthetic responses, validation scores, and JSON success evidence are returned.

## Latest Verification

Local current-code verification:

| Survey | Questions parsed | Responses | Overall validation | Question coverage |
| --- | ---: | ---: | ---: | ---: |
| `pricing_message_value_proposition_test.txt` | 8 | 384 | 90.5 | 100 |
| `concept_test_qualtrics_surveymonkey_style.txt` | 8 | 384 | 96.8 | 100 |
| `payment_behavior_federal_reserve_style.txt` | 8 | 384 | 94.5 | 85 |

Cloud API smoke verification before forcing a Code Engine container restart:

| Survey | Run id | Questions parsed | Responses | Overall validation | Question coverage | JSON success |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `pricing_message_value_proposition_test.txt` | `88be89e7` | 9 | 432 | 94.5 | 85 | 100.0 |
| `concept_test_qualtrics_surveymonkey_style.txt` | `ffce1a94` | 9 | 432 | 94.5 | 85 | 100.0 |
| `payment_behavior_federal_reserve_style.txt` | `a917a360` | 9 | 432 | 94.5 | 85 | 100.0 |

The cloud count was 9 because that deployed runtime counted the leading scenario/context line as a question. The current code filters those background lines, so the intended final count is 8 questions per file after the cloud app restarts from the latest GitHub source.
