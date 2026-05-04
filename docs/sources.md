# Public Data Sources

The PoC uses public Swiss demographic and payment behavior anchors. The values are deliberately transparent so consultants can adjust calibration later.

## Swiss Federal Statistical Office / FSO

Source: Population 2024 key figures.

Values used:

- permanent resident population: 9,051,029 at 31 December 2024
- private households: 4.1 million

Link: <https://dam-api.bfs.admin.ch/hub/api/dam/assets/36074226/master>

## Swiss National Bank

Source: Payment Methods Survey of Private Individuals in Switzerland 2025.

Values used for the SNB point-of-sale benchmark:

- cash: 30 percent
- debit card: 37 percent
- credit card: 13 percent
- mobile payment apps: 17 percent

Link: <https://www.snb.ch/dam/jcr%3A66f0422b-7961-45d9-8ce3-3d05a9dc0a06/paytrans_survey_report_2025.en.pdf>

## Swiss Payment Monitor

Source: Swiss Payment Monitor 1/2026, ZHAW and University of St.Gallen.

Values used for the all-transaction benchmark:

- mobile devices: 31.4 percent
- debit cards: 23.8 percent
- cash: 23.0 percent
- credit cards: 17.2 percent

Values used for the in-store benchmark:

- debit cards: 27.1 percent
- cash: 26.5 percent
- mobile devices: 24.8 percent
- credit cards: 18.7 percent

Links:

- <https://en.swisspaymentmonitor.ch/>
- <https://www.zhaw.ch/storage/hochschule/medien/news/2026/Press_Release_Swiss_Payment_Monitor_2026_EN.pdf>

## Case Brief

The repo does not include any partner-provided PDF or internal source material. The implementation reflects the public-facing project framing: persona design, multi-agent respondent simulation, validation and insight, persona-level responses, aggregated consultant insights, and public Swiss data grounding.
