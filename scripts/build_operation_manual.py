from __future__ import annotations

import argparse
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "demo" / "manuals"
ASSET_DIR = MANUAL_DIR / "assets"
HTML_PATH = MANUAL_DIR / "visa_synthetic_research_copilot_operation_manual.html"
PDF_PATH = MANUAL_DIR / "visa_synthetic_research_copilot_operation_manual.pdf"
APP_URL = "https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud"
REPO_URL = "https://github.com/ZihaoLu001/visa-synthetic-research-copilot"
SOURCE_URL = (
    "https://www.federalreserve.gov/econresdata/mobile-devices/"
    "2015-appendix-2-survey-of-consumers-use-of-mobile-financial-services-2014-questionnaire.htm"
)


def image(name: str, alt: str) -> str:
    path = ASSET_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing manual screenshot: {path}")
    return f'<img class="shot" src="assets/{html.escape(name)}" alt="{html.escape(alt)}" />'


def callouts(items: list[tuple[str, str]]) -> str:
    rows = []
    for title, body in items:
        rows.append(
            f"""
            <div class="callout">
              <div class="callout-title">{html.escape(title)}</div>
              <div>{html.escape(body)}</div>
            </div>
            """
        )
    return "\n".join(rows)


def page(title: str, eyebrow: str, body: str, classes: str = "") -> str:
    return f"""
    <section class="page {classes}">
      <div class="page-top">
        <div>
          <div class="eyebrow">{html.escape(eyebrow)}</div>
          <h1>{title}</h1>
        </div>
        <div class="brand">VISA</div>
      </div>
      {body}
      <div class="footer">
        <span>VCA Multi-Agent Synthetic Researcher - Group 28</span>
        <span>Public-data operating guide</span>
      </div>
    </section>
    """


def manual_html() -> str:
    css = """
    :root {
      --visa-blue: #1a1f71;
      --visa-electric: #1434cb;
      --visa-gold: #f7b600;
      --ink: #111827;
      --muted: #5b6475;
      --line: #d7dfed;
      --wash: #f3f6fb;
      --success: #0f7a45;
    }
    @page {
      size: A4 landscape;
      margin: 10mm;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "IBM Plex Sans", "Inter", "Segoe UI", Arial, sans-serif;
      background: white;
      font-size: 12px;
      line-height: 1.42;
    }
    .page {
      position: relative;
      min-height: 188mm;
      page-break-after: always;
      padding: 10mm 11mm 13mm;
      background:
        linear-gradient(180deg, rgba(20, 52, 203, 0.035), rgba(20, 52, 203, 0) 42mm),
        white;
      overflow: hidden;
    }
    .cover {
      background:
        radial-gradient(circle at 80% 20%, rgba(247, 182, 0, 0.15), transparent 26%),
        linear-gradient(135deg, #1434cb 0%, #1a1f71 100%);
      color: white;
    }
    .page-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      border-bottom: 1px solid rgba(26, 31, 113, 0.16);
      padding-bottom: 6mm;
      margin-bottom: 6mm;
    }
    .cover .page-top { border-bottom-color: rgba(255, 255, 255, 0.22); }
    .eyebrow {
      color: var(--visa-electric);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-weight: 800;
      font-size: 9px;
      margin-bottom: 3mm;
    }
    .cover .eyebrow { color: rgba(255, 255, 255, 0.78); }
    h1 {
      color: var(--visa-blue);
      font-size: 26px;
      line-height: 1.05;
      margin: 0;
      letter-spacing: 0;
    }
    .cover h1 {
      color: white;
      font-size: 40px;
      max-width: 178mm;
    }
    h2 {
      color: var(--visa-blue);
      font-size: 17px;
      margin: 0 0 3mm;
      line-height: 1.15;
    }
    h3 {
      color: var(--visa-blue);
      font-size: 12px;
      margin: 0 0 2mm;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    p { margin: 0 0 3mm; }
    .brand {
      color: var(--visa-electric);
      font-weight: 950;
      font-style: italic;
      font-size: 26px;
      line-height: 1;
      white-space: nowrap;
    }
    .cover .brand { color: white; }
    .subtitle {
      font-size: 16px;
      line-height: 1.45;
      max-width: 188mm;
      color: rgba(255, 255, 255, 0.86);
      margin-top: 9mm;
    }
    .cover-grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 14mm;
      margin-top: 16mm;
      align-items: end;
    }
    .cover-card {
      border: 1px solid rgba(255, 255, 255, 0.25);
      background: rgba(255, 255, 255, 0.08);
      padding: 8mm;
      border-radius: 4mm;
      min-height: 62mm;
    }
    .cover-card strong { color: white; }
    .cover-note {
      color: rgba(255, 255, 255, 0.76);
      font-size: 11px;
      margin-top: 4mm;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 0.9fr 1.45fr;
      gap: 7mm;
      align-items: start;
    }
    .grid-2.even { grid-template-columns: 1fr 1fr; }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 5mm;
    }
    .box {
      border: 1px solid var(--line);
      border-radius: 3mm;
      padding: 5mm;
      background: white;
      min-height: 25mm;
    }
    .box.blue {
      background: #f4f7ff;
      border-color: #cbd8ff;
    }
    .box.green {
      background: #eefaf3;
      border-color: #bfe3cf;
    }
    .step-list {
      counter-reset: step;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4mm;
      margin-top: 4mm;
    }
    .step {
      border: 1px solid var(--line);
      border-radius: 3mm;
      padding: 4mm;
      background: white;
      min-height: 31mm;
    }
    .step::before {
      counter-increment: step;
      content: counter(step);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 7mm;
      height: 7mm;
      border-radius: 999px;
      background: var(--visa-electric);
      color: white;
      font-weight: 800;
      margin-bottom: 3mm;
    }
    .shot {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 3mm;
      box-shadow: 0 5mm 13mm rgba(26, 31, 113, 0.10);
      display: block;
    }
    .shot.tall { max-height: 122mm; object-fit: contain; }
    .callout-stack {
      display: grid;
      gap: 3mm;
    }
    .callout {
      border-left: 3px solid var(--visa-electric);
      background: #f8fafc;
      padding: 3mm 3.5mm;
      border-radius: 1.5mm;
    }
    .callout-title {
      font-weight: 800;
      color: var(--visa-blue);
      margin-bottom: 1mm;
    }
    .metric-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4mm;
      margin: 4mm 0 7mm;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 3mm;
      padding: 4mm;
      background: white;
    }
    .metric .num {
      color: var(--visa-blue);
      font-size: 22px;
      font-weight: 850;
      line-height: 1;
    }
    .metric .label {
      color: var(--muted);
      font-size: 10px;
      margin-top: 2mm;
    }
    ul, ol { margin: 0; padding-left: 4.5mm; }
    li { margin-bottom: 1.8mm; }
    .small {
      color: var(--muted);
      font-size: 10.5px;
    }
    .source {
      font-size: 9.5px;
      color: var(--muted);
      word-break: break-word;
      margin-top: 3mm;
    }
    .question-list li {
      margin-bottom: 2.4mm;
    }
    .footer {
      position: absolute;
      left: 11mm;
      right: 11mm;
      bottom: 6mm;
      display: flex;
      justify-content: space-between;
      color: #7b8495;
      font-size: 9px;
      border-top: 1px solid rgba(26, 31, 113, 0.12);
      padding-top: 2mm;
    }
    .cover .footer {
      color: rgba(255, 255, 255, 0.70);
      border-top-color: rgba(255, 255, 255, 0.18);
    }
    .check {
      color: var(--success);
      font-weight: 800;
    }
    .warn {
      color: #9a5b00;
      font-weight: 800;
    }
    .page:last-child { page-break-after: auto; }
    """

    pages = []
    pages.append(
        page(
            "VCA Multi-Agent Synthetic Researcher",
            "PDF operation manual",
            f"""
            <div class="subtitle">
              How a Visa/VCA reviewer can upload a real survey/interview PDF as the input artifact,
              run Swiss synthetic customer agents with IBM watsonx.ai / Granite, and interpret segment
              perspectives, aggregate insights, persona-level responses, validation checks and a consultant
              decision brief.
            </div>
            <div class="cover-grid">
              <div class="cover-card">
                <h2 style="color:white;">What this proves</h2>
                <ul>
                  <li>Flexible survey/interview input: no fixed question set.</li>
                  <li>PDF upload and extraction audit for realistic partner testing.</li>
                  <li>Swiss public-data-grounded synthetic customer simulation.</li>
                  <li>Customer board, aggregate insights and individual response traceability.</li>
                  <li>Benchmark, consistency, coverage and realism validation.</li>
                  <li>Real-model proof path using IBM watsonx.ai / Granite 4 H Small, configured locally and in Code Engine.</li>
                </ul>
              </div>
              <div class="cover-card">
                <h2 style="color:white;">Review artifacts</h2>
                <p><strong>Application:</strong><br>{APP_URL}</p>
                <p><strong>Repository:</strong><br>{REPO_URL}</p>
                <p><strong>Sample PDF:</strong><br>Federal Reserve mobile-payments survey excerpt adapted for public-data review use.</p>
                <p><strong>Live model:</strong><br>IBM watsonx.ai in eu-de, default model ibm/granite-4-h-small. Code Engine health reports watsonx_configured=true.</p>
                <p class="cover-note">Public-data prototype. No Visa internal or client-sensitive data is used.</p>
              </div>
            </div>
            """,
            classes="cover",
        )
    )

    pages.append(
        page(
            "Reviewer Workflow At A Glance",
            "Start here",
            """
            <div class="grid-2 even">
              <div>
                <h2>Who should use this?</h2>
                <p>Visa Consulting & Analytics reviewers, IBM mentors, or student evaluators who want to test the prototype with a survey/interview artifact instead of a hardcoded prompt.</p>
                <div class="metric-row">
                  <div class="metric"><div class="num">12</div><div class="label">Default live Granite proof respondents</div></div>
                  <div class="metric"><div class="num">96</div><div class="label">Full synthetic panel available</div></div>
                  <div class="metric"><div class="num">PDF</div><div class="label">Recommended partner-review upload format</div></div>
                  <div class="metric"><div class="num">C</div><div class="label">Latest watsonx example evidence grade</div></div>
                </div>
                <div class="box green">
                  <h3>Positioning</h3>
                  <p>This is an early-stage multi-agent synthetic research workbench. It helps consultants identify promising propositions, weak assumptions, message risks and real-research priorities before commissioning real customer research.</p>
                </div>
              </div>
              <div>
                <h2>Four-step operation</h2>
                <div class="step-list">
                  <div class="step"><h3>Upload</h3><p>Attach a PDF survey/interview guide or use the sample public survey.</p></div>
                  <div class="step"><h3>Review</h3><p>Check extracted scenario text and edit questions if needed.</p></div>
                  <div class="step"><h3>Configure</h3><p>Set target market and define the client value proposition.</p></div>
                  <div class="step"><h3>Run</h3><p>Generate synthetic customer lens, insights, persona responses and validation evidence.</p></div>
                </div>
                <div class="box blue" style="margin-top:5mm;">
                  <h3>Recommended reviewer setting</h3>
                  <p>Use <strong>Model provider = watsonx</strong> for the final real-model proof. Keep <strong>mock</strong> only as a fallback for rehearsal or quota issues. Use <strong>Quick real-model proof</strong> for a fast live run, then move to <strong>Full survey</strong> and <strong>96 respondents</strong> when quota/time allows.</p>
                </div>
              </div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Model, Algorithm And Delivery Stack",
            "Delivery architecture",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Real LLM path", "IBM watsonx.ai is the primary provider. The app calls Granite through the ibm-watsonx-ai ModelInference abstraction, defaulting to ibm/granite-4-h-small in eu-de."),
                    ("Fallback path", "MockLLM is deterministic and exists only for CI, rehearsal and classroom quota contingency. It is not presented as real customer intelligence."),
                    ("Core algorithm", "Extract survey/interview text, parse structured questions, normalize key constructs, sample Swiss micro-personas, run one synthetic customer agent per persona, aggregate weighted results, validate, and synthesize a VCA decision brief."),
                    ("Customer perspective board", "The survey is the input artifact; the product output is a customer board with need states, objections, message tests, decision drivers, time/cost advantage and real-customer bridge."),
                    ("Consultant quality layer", "The app adds evidence grade, decision risk, lead-margin interpretation, risk flags, survey repair plan and real-customer validation plan so the output is actionable rather than decorative."),
                    ("Consultant deliverable", "Each run exports a polished PDF report and a delivery pack with a decision brief, customer perspective JSON, quality layer JSON, consultant report, persona CSV, validation JSON, full run JSON, source audit and governance notes."),
                    ("Consulting guardrail", "Synthetic results are directional. They help screen propositions and design better real customer research; they do not replace final Visa validation."),
                ])}
              </div>
              <div>{image("01_start.png", "Workbench start screen showing real-model workflow controls")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Step 1 - Upload A Real Survey PDF",
            "Input artifact",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Preferred format", "Use PDF for partner review because it matches how survey decks and interview guides are usually shared."),
                    ("Sample file", "The right panel lets reviewers download the included public PDF survey excerpt and upload it immediately."),
                    ("Extraction proof", "After upload, the app shows file name, file type and extracted character count before any agent run."),
                    ("Data guardrail", "The sample comes from a public Federal Reserve questionnaire; no Visa internal data is required."),
                ])}
                <div class="source">Public source: {SOURCE_URL}</div>
              </div>
              <div>{image("02_upload_pdf.png", "PDF upload step with extraction confirmation")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Step 2 - Review Or Adjust Questions",
            "Survey parser input",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Editable extracted text", "The textarea is the exact survey text sent to the parser agent. Reviewers can leave it unchanged or edit wording."),
                    ("Why this matters", "This directly addresses the Visa clarification that the system should answer survey questions without a fixed limitation."),
                    ("Supported artifacts", "The same ingestion layer accepts PDF, DOCX, XLSX, CSV, TXT and Markdown."),
                    ("Audit trail", "If the extracted text is edited, the run records that fact in the Question Parser tab."),
                ])}
              </div>
              <div>{image("03_review_questions.png", "Review extracted survey questions")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Step 3 - Define Proposition And Run",
            "Agent workflow",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Proposition testing", "Paste the client value proposition that Visa/VCA wants synthetic customers to react to."),
                    ("Live sensitivity", "Change the price, benefit or trust message, rerun, and compare movement in segment fit and adoption index."),
                    ("Panel scale", "The quick watsonx proof starts small to conserve quota. The full 96-persona run expands seven Swiss archetypes into a weighted micro-population."),
                    ("Run button", "The button launches survey parsing, persona respondent agents, analytics, validation and decision-brief synthesis in one workflow."),
                ])}
              </div>
              <div>{image("04_run_complete_kpis.png", "Run complete with KPI cards")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Step 4 - Read Consultant-Level Insights",
            "Aggregated output",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Recommendation", "The first tab summarizes the proposition signal and the reason behind the result."),
                    ("Adoption index", "The bar chart shows proposition fit across the synthetic Swiss panel."),
                    ("Pricing signal", "Acceptable fee ranges help frame a real customer price-sensitivity test."),
                    ("Feature and barrier signals", "Top labels surface recurring needs, trust drivers and objections."),
                ])}
              </div>
              <div>{image("05_consultant_summary.png", "Consultant summary with adoption and pricing output")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Confirm The Survey Was Parsed From PDF",
            "Question Parser tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Input Source Audit", "Shows Source = uploaded_file, File type = pdf, character count and extraction notes."),
                    ("No hardcoding", "The parsed table lists question id, type, construct and options generated from the uploaded survey."),
                    ("Review expectation", "Open this tab during review to prove the app can accept a new survey artifact."),
                    ("Quality fix", "The parser handles PDF line wrapping so wrapped questions stay together."),
                ])}
              </div>
              <div>{image("06_question_parser_pdf_audit.png", "Question Parser tab showing uploaded PDF audit")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Inspect Segment Differences",
            "Segment Explorer tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Why segments matter", "Visa asked for different personas or demographic groups, not one generic customer."),
                    ("What to look for", "Compare how students, family budget parents, travelers, retirees and SME owners respond differently."),
                    ("Consultant use", "Segment variation helps decide which customer group deserves real follow-up research."),
                ])}
              </div>
              <div>{image("07_segment_explorer.png", "Segment Explorer tab")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Inspect Persona-Level Traceability",
            "Persona Responses tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Individual responses", "Every row stores persona id, persona name, proposition, question, answer, rationale and confidence."),
                    ("Filter workflow", "Filter by proposition, archetype or question to inspect why a segment is driving the aggregate result."),
                    ("Reviewer value", "This satisfies the Visa request for both aggregated insights and persona-level survey responses."),
                    ("Export", "Download the filtered response table as CSV for analysis or appendix material."),
                ])}
              </div>
              <div>{image("08_persona_responses.png", "Persona Responses table")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Check Validation Confidence",
            "Validation tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Benchmark alignment", "Compares synthetic payment behavior mix against public Swiss payment survey anchors."),
                    ("Internal consistency", "Checks repeated persona runs for response variance."),
                    ("Coverage", "Confirms the panel covers the Swiss archetypes and the survey covers key constructs."),
                    ("Interpretation", "This is directional evidence, not a claim that synthetic respondents replace real Visa validation."),
                ])}
              </div>
              <div>{image("09_validation.png", "Validation tab with benchmark and consistency checks")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Read The Customer Perspective Board",
            "Decision Brief tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Why this matters", "This is the core Visa output: synthetic customer perspectives for early-stage value proposition decisions."),
                    ("Customer board", "Summarizes each Swiss segment's reality, proposition fit, need state, objections to probe and message to test."),
                    ("Decision drivers", "Shows the positive signals and watchouts that explain the aggregate recommendation."),
                    ("Time and cost advantage", "Shows why the synthetic layer is useful before commissioning real surveys or interviews."),
                    ("Real-customer bridge", "Keeps the governance clear: synthetic learning first, qualitative validation next, quantitative calibration after that."),
                ])}
              </div>
              <div>{image("11_synthetic_customer_lens.png", "Decision Brief tab showing Customer Perspective Board")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Read The Consultant Quality Layer",
            "Decision Brief tab",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Evidence grade", "Summarizes whether the synthetic run is strong enough for directional prioritization or still needs major repair."),
                    ("Decision risk", "Combines validation, lead margin and segment differentiation so consultants do not over-read a narrow synthetic lead."),
                    ("Risk flags", "Calls out weak lead, construct gaps, realism issues or price-value mismatch in plain business language."),
                    ("Survey repair plan", "Recommends exact modules to add before a real Swiss customer survey, such as choice-based validation, price sensitivity, feature trade-off and barrier/trust questions."),
                    ("Real validation plan", "Turns the output into the next consulting action: interviews, Swiss pulse survey, pricing cell test and calibration loop."),
                ])}
              </div>
              <div>{image("12_consultant_quality_layer.png", "Decision Brief tab showing Consultant Quality Layer")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Use The Scorecard In The Final Presentation",
            "Evaluation mapping",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Pilot readiness gate", "The top of the Scorecard tab shows which checks are ready for partner review and which need attention."),
                    ("Real model status", "For final proof, Evidence mode should show Real IBM watsonx.ai and ibm/granite-4-h-small."),
                    ("Live product proof", "Running app, PDF upload, parser, agents, results and validation are all live."),
                    ("Architecture", "UI, ingestion, parser, persona store, orchestrator, respondent agents, analytics and validator are visible."),
                    ("KPIs", "Runtime, response count, parse success, consistency and benchmark scores are quantified."),
                    ("Business value", "Position the system as early-stage proposition screening and better real-survey design."),
                ])}
              </div>
              <div>{image("10_scorecard.png", "Scorecard tab mapped to grading criteria")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Export PDF Report And Delivery Pack",
            "Portable partner artifact",
            f"""
            <div class="grid-2">
              <div class="callout-stack">
                {callouts([
                    ("Why this matters", "VCA reviewers should not need to trust only the live screen. They can download a consultant-style PDF report and inspect the evidence offline."),
                    ("PDF report", "The report includes executive answer, Customer Perspective Board, consultant quality layer, proposition decision matrix, segment fit, persona evidence, validation confidence, methodology and limitations."),
                    ("Included files", "The ZIP contains the PDF report, decision brief, customer perspective JSON, quality layer JSON, consultant report, persona-level CSV, validation JSON, full run JSON, input-source audit, methodology/governance notes and pilot-readiness gate."),
                    ("Review workflow", "Send the input PDF survey plus output PDF report together with the app URL so IBM/Visa can check recommendation logic, persona traceability and validation evidence."),
                    ("No secrets", "The delivery pack contains run evidence, not watsonx API keys or local credentials."),
                ])}
              </div>
              <div>{image("13_delivery_pack.png", "Decision Brief tab showing PDF Report and Consultant Delivery Pack downloads")}</div>
            </div>
            """,
        )
    )

    pages.append(
        page(
            "Suggested Slack Message To Visa / IBM",
            "Partner alignment",
            """
            <div class="grid-2 even">
              <div class="box blue">
                <h2>Message draft</h2>
                <p>Hi Visa / IBM team,</p>
                <p>We prepared a short operation manual and a sample input/output pair for the current prototype. It shows a real PDF survey/interview artifact upload, dynamic parsing, IBM watsonx/Granite model path, Swiss synthetic customer responses, a segment customer board, aggregated consultant insights, a Consultant Quality Layer, validation checks, and a generated consultant PDF report.</p>
                <p>Attached are the input PDF survey and the generated output PDF report from the same flow.</p>
                <p>Could you please let us know whether this matches your expected direction for the final Visa use case?</p>
                <ol class="question-list">
                  <li>Is the Multi-Agent Synthetic Researcher framing aligned with your intended use case?</li>
                  <li>Is the flexible PDF survey/interview upload flow aligned with your expectation as the input artifact?</li>
                  <li>Should the final output emphasize aggregate insights, persona-level responses, synthetic customer segment cards, or all three?</li>
                  <li>Is the evidence grade / decision risk / survey repair layer useful for VCA consultants?</li>
                  <li>Are the benchmark, consistency, coverage and realism validation checks useful enough for VCA consultants?</li>
                  <li>Is there any missing Visa requirement we should address before finals?</li>
                </ol>
                <p>Thank you!</p>
              </div>
              <div>
                <h2>What to emphasize verbally</h2>
                <ul>
                  <li><span class="check">Flexible input:</span> The system is not a fixed Q&A bot.</li>
                  <li><span class="check">Public-data grounding:</span> Personas are used because internal Visa customer data is unavailable.</li>
                  <li><span class="check">Consultant value:</span> It produces early directional evidence, a decision posture, evidence quality and better real survey design.</li>
                  <li><span class="check">Validation discipline:</span> The app exposes limitations through benchmark and consistency checks.</li>
                </ul>
                <div class="box green" style="margin-top:6mm;">
                  <h3>Best channel</h3>
                  <p>Use the Visa-specific Slack channel for use-case/product feedback. Use the general guest channel for deployment or IBM platform issues.</p>
                </div>
              </div>
            </div>
            """,
        )
    )

    return f"""<!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>VCA Multi-Agent Synthetic Researcher Operation Manual</title>
        <style>{css}</style>
      </head>
      <body>
        {"".join(pages)}
      </body>
    </html>
    """


def build_html() -> None:
    MANUAL_DIR.mkdir(parents=True, exist_ok=True)
    html_text = "\n".join(line.rstrip() for line in manual_html().splitlines()) + "\n"
    HTML_PATH.write_text(html_text, encoding="utf-8")


def build_pdf() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF export requires Playwright. Install with: python -m pip install playwright") from exc

    build_html()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(HTML_PATH.resolve().as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Visa operation manual HTML/PDF.")
    parser.add_argument("--html-only", action="store_true", help="Only generate the HTML source.")
    args = parser.parse_args()
    if args.html_only:
        build_html()
    else:
        build_pdf()
    print(HTML_PATH)
    if PDF_PATH.exists():
        print(PDF_PATH)


if __name__ == "__main__":
    main()
