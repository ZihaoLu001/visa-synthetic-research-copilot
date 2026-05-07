# Demo Script

Target length: 6-7 minutes.

## 1. Business Context

VCA consultants need fast early-stage customer input for value proposition design. Traditional surveys and interviews are useful but slower and more expensive, so many assumptions around pricing, benefits, needs, and messaging remain untested until late.

## 2. Input A Flexible Survey Or File

Paste a short survey:

```text
1. How relevant is this value proposition for your everyday payment or banking needs?
2. What annual fee or monthly price in CHF would feel acceptable, if any?
3. Which benefit, service or message feels most valuable to you, and why?
4. What is the main barrier or concern that would stop you from using it?
```

Then say the stronger version can also accept a real research artifact from Visa: TXT, MD, PDF, DOCX, CSV, or XLSX. Open the Question Parser tab after a run and show the input-source audit: file name, type, extracted character count, extraction notes, and whether the text was edited before execution.

Explain that the system is not limited to predefined questions. It ingests survey files or pasted survey/interview text, parses the content at runtime, and then routes the parsed questions to persona agents. The stronger framing is: the survey is the input artifact, but the product is a multi-agent synthetic researcher for value proposition decisions.

## 3. Define The Client Proposition

Paste the proposition Visa/VCA wants to test. The prototype no longer depends on fixed A/B demo options; it is designed for a consultant to bring any payment, banking or value-proposition stimulus.

For the partner example, use the editable sample proposition:

```text
Swiss Payment Assistant Proposition: a bank-issued Visa payment assistant that helps Swiss consumers choose a suitable payment method at checkout, highlights fees and protections, supports mobile-wallet usage, and keeps the customer in control of the final payment choice.
```

## 4. Run Synthetic Respondents

For the real-model proof, use `watsonx`, `12` respondents, `1` consistency run, and `Quick real-model proof (first 2 questions)`. This demonstrates the live IBM Granite path without wasting classroom quota. For the full presentation run, switch to `Full survey` and `96` respondents if quota/time allows. Point out that the respondents are expanded from high-quality Swiss archetypes rather than hardcoded one-off answers. Keep mock mode ready only as a fallback if classroom quota is exhausted.

## 5. Show Outputs

Cover these tabs:

- Consultant Summary: adoption index, acceptable fee, top signals, recommendation.
- Decision Brief: proposition readout, customer perspective board, decision posture, Consultant Quality Layer, hypothesis readout, VCA "so what" and next real-research actions.
- Question Parser: parsed question types, measured constructs and input-source audit.
- Segment Explorer: which Swiss archetypes fit or resist the proposition.
- Persona Responses: individual responses with rationale and confidence.
- Validation: benchmark alignment, consistency, coverage, construct coverage and realism rubric.
- Scorecard: direct mapping to the final grading criteria and KPI evidence.
- Downloads: polished PDF Report, Consultant Delivery Pack, CSV persona responses, Markdown consultant report and full run JSON for partner-side testing.

In the Consultant Quality Layer, say:

```text
This is the consulting control layer: it tells us whether the synthetic evidence is strong enough to use directionally, what could be wrong, how the survey should be repaired, and what real-customer validation should happen next.
```

In the customer perspective board, say:

```text
This is the Visa-required customer layer: it shows which Swiss customer perspectives we simulated, what each segment needs, what objections to probe, which message to test, and how the synthetic run bridges into real customer validation.
```

For Slack partner feedback before the final presentation, attach `demo/partner_examples/visa_example_input_public_mobile_payments_survey.pdf` and `demo/partner_examples/visa_example_output_consultant_report_watsonx.pdf`. The second file is a real watsonx/Granite-generated report from the uploaded PDF flow, so it demonstrates the product output without asking the partner to run the app immediately.

## 6. Live Sensitivity Test

Change the proposition price, benefit wording, or control/privacy message. Rerun and explain the directional movement:

```text
The proposition becomes more credible when the value proof and control language are clearer, but real Swiss customer validation is still needed.
```

## 7. Close With Guardrail

This is not a final market research replacement. It is a transparent, benchmark-grounded synthetic research layer for screening hypotheses, improving survey design, and prioritizing real customer validation.
