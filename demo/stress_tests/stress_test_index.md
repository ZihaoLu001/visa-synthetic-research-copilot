# Public Input Stress Tests

These artifacts pressure-test the VCA Multi-Agent Synthetic Researcher against public survey/questionnaire inputs that a Visa/VCA team might use as proxy material for early product and value proposition research.

| Case | Public source | Input PDF | Output PDF | Model | Responses | Validation |
| --- | --- | --- | --- | --- | ---: | ---: |
| ECB SPACE 2024 payment attitudes questionnaire slice | [source](https://www.ecb.europa.eu/stats/ecb_surveys/space/shared/pdf/ecb.space2024_annex_a.en.pdf) | `demo\stress_tests\run_inputs\01_ecb_space_payment_attitudes_input.pdf` | `demo\stress_tests\outputs\01_ecb_space_payment_attitudes_output_watsonx.pdf` | ibm/granite-4-h-small | 24 | 87.2 |
| Federal Reserve mobile financial services questionnaire slice | [source](https://www.federalreserve.gov/consumerscommunities/files/mobilefinancial_2014questionnaire.pdf) | `demo\stress_tests\run_inputs\02_federal_reserve_mobile_payments_input.pdf` | `demo\stress_tests\outputs\02_federal_reserve_mobile_payments_output_watsonx.pdf` | ibm/granite-4-h-small | 30 | 91.5 |
| FCA Financial Lives 2024 payments and digital trust questionnaire slice | [source](https://www.fca.org.uk/publication/financial-lives/financial-lives-survey-2024-questionnaire.pdf) | `demo\stress_tests\run_inputs\03_fca_financial_lives_payments_trust_input.pdf` | `demo\stress_tests\outputs\03_fca_financial_lives_payments_trust_output_watsonx.pdf` | ibm/granite-4-h-small | 18 | 92.3 |

The raw downloaded public PDFs are saved under `demo/stress_tests/inputs_raw/`. The run inputs are shorter source-derived slices to keep watsonx quota use reasonable while still exercising PDF upload, parsing, synthetic persona responses, aggregation, validation and report generation.
