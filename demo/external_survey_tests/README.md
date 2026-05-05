# External Survey Stress Tests

These surveys are original, Visa-relevant stress tests inspired by public concept-testing and payment-survey guidance. They are not copied templates.

## Why These Tests Matter

- Concept testing platforms commonly test appeal, purchase or adoption intent, feature preference, replacement/addition behavior, open-ended likes/dislikes, and price or value perception.
- Payment surveys commonly ask about current payment methods, mobile wallet behavior, trust, security, convenience, privacy, and payment pain points.
- The Visa brief asks the prototype to accept flexible survey or interview inputs, not only hardcoded questions. These files are therefore used as acceptance tests for flexible parsing, persona-level response generation, aggregated insights, and validation checks.

## Source Inspiration

- Qualtrics concept-testing guidance: https://www.qualtrics.com/articles/strategy-research/concept-testing-questions/
- SurveyMonkey concept-development guidance: https://www.surveymonkey.com/market-research/resources/concept-development-guide/
- SurveyMonkey idea-screening guidance: https://help.surveymonkey.com/en/surveymonkey/solutions/idea-screening/
- Federal Reserve mobile financial services questionnaire: https://www.federalreserve.gov/econresdata/mobile-devices/2015-appendix-2-survey-of-consumers-use-of-mobile-financial-services-2014-questionnaire.htm
- Federal Reserve 2023 consumer payments insight brief: https://fedpaymentsimprovement.org/wp-content/uploads/042624-consumer-brief.pdf

## Expected Result

Each file should parse into multiple survey questions, produce synthetic responses for the configured Swiss persona panel, and return:

- adoption or trust Likert signals,
- price sensitivity where applicable,
- feature or payment-method preference choices using the provided options,
- barriers and open-ended qualitative feedback,
- validation scores for benchmark alignment, internal consistency, coverage, and realism.
