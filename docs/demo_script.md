# Demo Script

Target length: 6-7 minutes.

## 1. Business Context

VCA consultants need fast early-stage customer input for value proposition design. Traditional surveys and interviews are useful but slower and more expensive, so many assumptions around pricing, benefits, needs, and messaging remain untested until late.

## 2. Input A Flexible Survey Or File

Paste a short survey:

```text
1. How likely would you be to adopt this card if it were offered by your bank?
2. What annual fee in CHF would feel acceptable for this card?
3. Which benefit or feature feels most valuable to you, and why?
4. What is the main barrier that would prevent you from using this card?
```

Then say the stronger version can also accept a real research artifact from Visa: TXT, MD, PDF, DOCX, CSV, or XLSX. Open the Question Parser tab after a run and show the input-source audit: file name, type, extracted character count, extraction notes, and whether the text was edited before execution.

Explain that the system is not limited to predefined questions. It ingests survey files or pasted survey/interview text, parses the content at runtime, and then routes the parsed questions to persona agents.

## 3. Show Concepts

Use the default concepts:

- Concept A: Premium Travel Card, CHF 120, travel insurance, FX fee reduction, lounge vouchers, purchase protection.
- Concept B: Everyday Cashback Card, CHF 60, grocery cashback, family offers, simple onboarding, purchase protection.

## 4. Run Synthetic Respondents

Run 48 or 96 respondents in mock mode. Point out that the respondents are expanded from high-quality Swiss archetypes rather than hardcoded one-off answers.

## 5. Show Outputs

Cover these tabs:

- Consultant Summary: adoption index, acceptable fee, top signals, recommendation.
- Question Parser: parsed question types, measured constructs and input-source audit.
- Segment Explorer: which Swiss archetypes fit each concept.
- Persona Responses: individual responses with rationale and confidence.
- Validation: benchmark alignment, consistency, coverage, construct coverage and realism rubric.
- Scorecard: direct mapping to the final grading criteria and KPI evidence.
- Downloads: CSV persona responses, Markdown consultant report and full run JSON for partner-side testing.

## 6. Live Sensitivity Test

Change Concept A fee from CHF 120 to CHF 60, or add stronger purchase protection messaging. Rerun and explain the directional movement:

```text
The premium card becomes less niche when price friction drops, but family and student segments still need everyday-value proof.
```

## 7. Close With Guardrail

This is not a final market research replacement. It is a transparent, benchmark-grounded synthetic research layer for screening hypotheses, improving survey design, and prioritizing real customer validation.
