from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .consulting import build_decision_brief
from .insight_quality import build_consultant_quality_layer
from .schemas import SurveyRun

VISA_BLUE = colors.HexColor("#1a1f71")
VISA_ELECTRIC = colors.HexColor("#1434cb")
VISA_GOLD = colors.HexColor("#f7b600")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#64748b")
LINE = colors.HexColor("#dbe3ef")
WASH = colors.HexColor("#f5f7fb")


def build_consultant_pdf_report(run: SurveyRun) -> bytes:
    """Render a VCA-style PDF report for the exact synthetic research run."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=14 * mm,
        title=f"VCA Synthetic Research Report {run.run_id}",
        author="VCA Multi-Agent Synthetic Researcher",
    )
    styles = _styles()
    story: list[Any] = []

    story.extend(_cover(run, styles))
    story.append(PageBreak())
    story.extend(_executive_summary(run, styles))
    story.extend(_quality_layer(run, styles))
    story.extend(_synthetic_customer_board(run, styles))
    story.extend(_proposition_matrix(run, styles))
    story.extend(_signals_and_segments(run, styles))
    story.append(PageBreak())
    story.extend(_persona_evidence(run, styles))
    story.extend(_validation(run, styles))
    story.extend(_methodology(run, styles))

    doc.build(story, onFirstPage=_draw_page_frame, onLaterPages=_draw_page_frame)
    return buffer.getvalue()


def _cover(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    aggregate = run.aggregate
    validation = run.validation
    source = aggregate.get("input_source", {})
    decision = _decision(run)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return [
        Spacer(1, 34 * mm),
        Paragraph("VISA", styles["brand"]),
        Spacer(1, 18 * mm),
        Paragraph("VCA Multi-Agent Synthetic Researcher Report", styles["cover_title"]),
        Spacer(1, 4 * mm),
        Paragraph("Multi-agent synthetic customers for early-stage value proposition decisions", styles["cover_subtitle"]),
        Spacer(1, 14 * mm),
        _info_table(
            [
                ("Run ID", run.run_id),
                ("Generated", generated),
                ("Input survey", source.get("file_name") or source.get("source") or "pasted text"),
                ("LLM provider", f"{aggregate.get('provider', 'mock')} / {aggregate.get('model_id', 'n/a')}"),
                ("Synthetic panel", f"{aggregate.get('respondent_count', 'n/a')} respondents, {aggregate.get('response_count', 'n/a')} persona-question responses"),
                ("Validation", f"{validation.get('overall', {}).get('score', 'n/a')}/100"),
                ("Decision posture", decision.get("decision_posture", "n/a")),
            ],
            styles,
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "This report is directional early-stage evidence. It is designed to complement real customer research, "
            "not replace Visa final validation.",
            styles["guardrail"],
        ),
    ]


def _executive_summary(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    decision = _decision(run)
    aggregate = run.aggregate
    research = aggregate.get("research_brief", {})
    items: list[Any] = [
        Paragraph("Executive Answer", styles["h1"]),
        Paragraph(_clean(decision.get("executive_answer", "No decision brief was generated.")), styles["body"]),
        Spacer(1, 4 * mm),
        _kpi_strip(run, styles),
        Spacer(1, 7 * mm),
        Paragraph("Research Brief", styles["h2"]),
        _bullet("Objective", research.get("project_objective", "n/a"), styles),
        _bullet("Client decision", research.get("client_decision", "n/a"), styles),
        _bullet("Decision rule", research.get("decision_rule", "n/a"), styles),
        Spacer(1, 5 * mm),
        Paragraph("Customer Perspective Board", styles["h2"]),
        Paragraph(_clean((decision.get("synthetic_customer_lens") or {}).get("positioning", "Synthetic customers provide directional early-stage customer intuition.")), styles["body"]),
        Spacer(1, 2.5 * mm),
        _table(
            [
                ["Value proposition questions", "Time/cost advantage", "Real customer bridge"],
                [
                    _para(_join_lines((decision.get("synthetic_customer_lens") or {}).get("value_proposition_questions", [])), styles),
                    _para(_join_lines((decision.get("synthetic_customer_lens") or {}).get("time_cost_advantage", {}).values()), styles),
                    _para(_join_lines([f"{item.get('stage')}: {item.get('purpose')}" for item in (decision.get("synthetic_customer_lens") or {}).get("real_customer_bridge", [])]), styles),
                ],
            ],
            [62 * mm, 62 * mm, 62 * mm],
            font_size=7.4,
        ),
        Spacer(1, 5 * mm),
        Paragraph("Why This Matches The Visa Brief", styles["h2"]),
        Paragraph(
            "The survey or interview guide is treated as the input artifact. The product output is the synthetic customer layer: "
            "segment perspectives, need states, objections, messages to test, validation checks and the bridge to real research.",
            styles["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("So What For VCA", styles["h2"]),
    ]
    items.extend(_bullet_list(decision.get("so_what", []), styles))
    items.extend([Spacer(1, 5 * mm), Paragraph("Recommended Real Research", styles["h2"])])
    items.extend(_bullet_list(decision.get("recommended_real_research", []), styles))
    return items


def _proposition_matrix(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    decision = _decision(run)
    rows = [["Proposition", "Adoption", "Mean Likert", "Price signal", "Recommended action"]]
    for row in decision.get("concept_matrix", []):
        rows.append(
            [
                _para(row.get("concept_name") or row.get("concept_id"), styles),
                row.get("adoption_index", "n/a"),
                row.get("mean_likert", "n/a"),
                _para(row.get("price_signal", "n/a"), styles),
                _para(row.get("recommended_action", "n/a"), styles),
            ]
        )
    if len(rows) == 1:
        rows.append(["n/a", "n/a", "n/a", "No adoption question parsed", "Inspect survey parser"])
    return [
        Spacer(1, 7 * mm),
        Paragraph("Proposition Evidence Readout", styles["h1"]),
        _table(rows, [42 * mm, 25 * mm, 25 * mm, 48 * mm, 45 * mm]),
    ]


def _quality_layer(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    decision = _decision(run)
    quality = decision.get("consultant_quality_layer") or build_consultant_quality_layer(run, decision)
    segment = quality.get("segment_differentiation", {})
    rows = [
        ["Evidence grade", f"{quality.get('evidence_grade', 'n/a')} ({quality.get('evidence_score', 'n/a')}/100)", _para(quality.get("evidence_label", "n/a"), styles)],
        ["Decision risk", _clean(quality.get("decision_risk")), _para(quality.get("lead_margin_interpretation", "n/a"), styles)],
        ["Segment differentiation", _clean(segment.get("spread")), _para(segment.get("interpretation", "n/a"), styles)],
    ]
    story: list[Any] = [
        Spacer(1, 7 * mm),
        Paragraph("Consultant Quality Layer", styles["h1"]),
        _table([["Dimension", "Signal", "Interpretation"], *rows], [44 * mm, 42 * mm, 99 * mm], font_size=8),
        Spacer(1, 5 * mm),
        Paragraph("Top Consultant Actions", styles["h2"]),
    ]
    story.extend(_bullet_list(quality.get("top_consultant_actions", []), styles))

    risk_rows = [["Severity", "Risk flag", "Why it matters"]]
    for flag in quality.get("risk_flags", [])[:6]:
        risk_rows.append([flag.get("severity", "n/a"), _para(flag.get("title", "n/a"), styles), _para(flag.get("detail", "n/a"), styles)])
    story.extend([Spacer(1, 4 * mm), Paragraph("Evidence Risks", styles["h2"]), _table(risk_rows, [25 * mm, 45 * mm, 115 * mm], font_size=7.8)])

    repair_rows = [["Priority", "Survey module", "Suggested next question"]]
    for item in quality.get("survey_repair_plan", [])[:5]:
        repair_rows.append([item.get("priority", "n/a"), _para(item.get("module", "n/a"), styles), _para(item.get("suggested_question", "n/a"), styles)])
    story.extend([Spacer(1, 4 * mm), Paragraph("Survey Repair Plan", styles["h2"]), _table(repair_rows, [24 * mm, 43 * mm, 118 * mm], font_size=7.4)])
    return story


def _synthetic_customer_board(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    lens = _decision(run).get("synthetic_customer_lens", {})
    rows = [["Segment", "Proposition fit", "Need state", "Objections to probe", "Message to test"]]
    for item in lens.get("synthetic_customer_board", [])[:7]:
        rows.append([
            _para(item.get("segment", "n/a"), styles),
            _para(item.get("likely_best_fit", "n/a"), styles),
            _para(item.get("need_state", "n/a"), styles),
            _para(", ".join(item.get("objections_to_probe", [])), styles),
            _para(item.get("message_to_test", "n/a"), styles),
        ])
    if len(rows) == 1:
        rows.append(["n/a", "n/a", "n/a", "n/a", "n/a"])
    return [
        Spacer(1, 7 * mm),
        Paragraph("Customer Perspective Board", styles["h1"]),
        _table(rows, [34 * mm, 32 * mm, 45 * mm, 37 * mm, 37 * mm], font_size=7.2),
    ]



def _signals_and_segments(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    aggregate = run.aggregate
    story = [Spacer(1, 7 * mm), Paragraph("Signals And Segment Fit", styles["h1"])]
    labels = aggregate.get("top_answer_labels", [])[:8]
    barriers = aggregate.get("top_barrier_signals", [])[:8]
    signal_rows = [["Signal", "Count"], *[[label, count] for label, count in labels or [("n/a", "n/a")]]]
    barrier_rows = [["Barrier / Watchout", "Count"], *[[label, count] for label, count in barriers or [("n/a", "n/a")]]]
    story.append(_two_tables(signal_rows, barrier_rows, styles))

    segment_rows = [["Proposition:Segment", "Mean Likert"]]
    segment_items = sorted(
        aggregate.get("segment_fit", {}).items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else -1,
        reverse=True,
    )
    for key, value in segment_items[:18]:
        segment_rows.append([_para(_format_segment_key(key, run), styles), value])
    if len(segment_rows) == 1:
        segment_rows.append(["n/a", "No Likert segment fit available"])
    story.extend([Spacer(1, 5 * mm), Paragraph("Segment Fit Snapshot", styles["h2"]), _table(segment_rows, [122 * mm, 40 * mm])])
    return story


def _persona_evidence(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    concept_lookup = {concept.id: concept.name for concept in run.concepts}
    question_lookup = {question.id: question.text for question in run.questions}
    rows = [["Persona", "Proposition", "Question", "Answer", "Rationale"]]
    for response in run.responses[:18]:
        rows.append(
            [
                _para(response.persona_name, styles),
                _para(concept_lookup.get(response.concept_id, response.concept_id), styles),
                _para(question_lookup.get(response.question_id, response.question_id), styles),
                _para(_answer(response.answer_value, response.answer_label, response.answer_text), styles),
                _para(response.rationale, styles),
            ]
        )
    return [
        Paragraph("Persona-Level Evidence", styles["h1"]),
        Paragraph(
            "Representative rows from the persona response table. The app and delivery pack include the full CSV.",
            styles["small"],
        ),
        Spacer(1, 3 * mm),
        _table(rows, [34 * mm, 31 * mm, 43 * mm, 38 * mm, 39 * mm], font_size=7.4),
    ]


def _validation(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    validation = run.validation
    benchmark = validation.get("benchmark_alignment", {})
    consistency = validation.get("internal_consistency", {})
    coverage = validation.get("coverage", {})
    question_coverage = validation.get("question_coverage", {})
    realism = validation.get("realism_rubric", {})
    rows = [
        ["Validation check", "Score / Metric", "Interpretation"],
        ["Overall", f"{validation.get('overall', {}).get('score', 'n/a')}/100", _para(validation.get("overall", {}).get("interpretation", ""), styles)],
        ["Benchmark alignment", f"{benchmark.get('score', 'n/a')}/100; MAE {benchmark.get('primary_mae_percentage_points', 'n/a')}pp", _para(benchmark.get("primary_profile_label", "public Swiss benchmark alignment"), styles)],
        ["Internal consistency", f"{consistency.get('score', 'n/a')}/100; avg std {consistency.get('avg_likert_std', 'n/a')}", _para(consistency.get("interpretation", ""), styles)],
        ["Persona coverage", f"{coverage.get('score', 'n/a')}/100", _para(f"{coverage.get('archetype_count', 'n/a')} archetypes; {coverage.get('micro_persona_count', 'n/a')} micro-personas", styles)],
        ["Question coverage", f"{question_coverage.get('score', 'n/a')}/100", _para("Detected: " + ", ".join(question_coverage.get("detected_constructs", [])), styles)],
        ["Realism rubric", f"{realism.get('score', 'n/a')}/100", _para(f"{realism.get('flag_count', 'n/a')} flag(s) across {realism.get('sampled_items', 'n/a')} sampled responses", styles)],
    ]
    return [Spacer(1, 7 * mm), Paragraph("Validation And Confidence", styles["h1"]), _table(rows, [42 * mm, 43 * mm, 100 * mm], font_size=8)]


def _methodology(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> list[Any]:
    decision = _decision(run)
    story: list[Any] = [Spacer(1, 7 * mm), Paragraph("Methodology And Governance", styles["h1"])]
    story.extend(_bullet_list(decision.get("methodology", []), styles))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Limitations", styles["h2"]))
    story.extend(_bullet_list(decision.get("limitations", []), styles))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            "Final decisions should be validated with real Swiss customers and, when allowed, calibrated against Visa internal research.",
            styles["guardrail"],
        )
    )
    return story


def _decision(run: SurveyRun) -> dict[str, Any]:
    decision = run.aggregate.get("decision_brief")
    if decision:
        return decision
    return build_decision_brief(
        run,
        run.aggregate.get("research_brief", {}),
        provider=str(run.aggregate.get("provider", "mock")),
    )


def _kpi_strip(run: SurveyRun, styles: dict[str, ParagraphStyle]) -> Table:
    aggregate = run.aggregate
    validation = run.validation
    runtime = aggregate.get("runtime", {})
    rows = [
        [
            _metric_cell("Proposition", (_decision(run).get("lead_concept_id") or "n/a"), styles),
            _metric_cell("Responses", str(aggregate.get("response_count", "n/a")), styles),
            _metric_cell("Validation", f"{validation.get('overall', {}).get('score', 'n/a')}/100", styles),
            _metric_cell("Runtime", f"{runtime.get('elapsed_seconds', 'n/a')}s", styles),
        ]
    ]
    table = Table(rows, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), WASH), ("BOX", (0, 0), (-1, -1), 0.6, LINE), ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return table


def _metric_cell(label: str, value: str, styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [Paragraph(label, styles["metric_label"]), Paragraph(value, styles["metric_value"])]


def _info_table(rows: list[tuple[str, Any]], styles: dict[str, ParagraphStyle]) -> Table:
    data = [[Paragraph(str(k), styles["info_key"]), Paragraph(_clean(v), styles["info_value"])] for k, v in rows]
    return _table(data, [45 * mm, 115 * mm], header=False)


def _two_tables(left: list[list[Any]], right: list[list[Any]], styles: dict[str, ParagraphStyle]) -> Table:
    return Table(
        [[_table(left, [58 * mm, 22 * mm]), _table(right, [58 * mm, 22 * mm])]],
        colWidths=[88 * mm, 88 * mm],
        style=[("VALIGN", (0, 0), (-1, -1), "TOP")],
    )


def _table(rows: list[list[Any]], col_widths: list[float], header: bool = True, font_size: float = 8.2) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
    ]
    if header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), VISA_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(style))
    return table


def _bullet(title: str, value: Any, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"<b>{_escape(title)}:</b> {_escape(_clean(value))}", styles["body"])


def _bullet_list(items: Iterable[Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    rows: list[Any] = []
    for item in items:
        rows.append(Paragraph(f"- {_escape(_clean(item))}", styles["body"]))
    if not rows:
        rows.append(Paragraph("- n/a", styles["body"]))
    return rows


def _format_segment_key(key: str, run: SurveyRun) -> str:
    concept_lookup = {concept.id: concept.name for concept in run.concepts}
    persona_lookup: dict[str, str] = {}
    for persona in run.personas:
        root_id = persona.id.split("_")[0]
        persona_lookup[root_id] = persona.name.split(" #")[0]

    concept_id, _, segment_id = key.partition(":")
    concept_name = concept_lookup.get(concept_id, concept_id)
    segment_name = persona_lookup.get(segment_id, segment_id)
    return f"{concept_name}: {segment_name}"


def _answer(value: Any, label: Any, text: str) -> str:
    parts = []
    if value is not None:
        parts.append(str(value))
    if label:
        parts.append(str(label))
    if text:
        parts.append(text)
    return " | ".join(parts) or "n/a"


def _para(value: Any, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(_escape(_clean(value)), styles["table_cell"])


def _clean(value: Any) -> str:
    if value is None:
        return "n/a"
    text = str(value).replace("\n", " ").strip()
    return text if text else "n/a"


def _join_lines(items: list[Any]) -> str:
    return " | ".join(f"- {str(item)}" for item in items) if items else "n/a"


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle("Brand", parent=base["Normal"], textColor=VISA_ELECTRIC, fontSize=34, leading=34, fontName="Helvetica-BoldOblique", alignment=TA_LEFT),
        "cover_title": ParagraphStyle("CoverTitle", parent=base["Title"], textColor=VISA_BLUE, fontSize=28, leading=32, fontName="Helvetica-Bold", spaceAfter=4),
        "cover_subtitle": ParagraphStyle("CoverSubtitle", parent=base["Normal"], textColor=MUTED, fontSize=12.5, leading=17),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], textColor=VISA_BLUE, fontSize=17, leading=21, fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=5),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], textColor=VISA_BLUE, fontSize=12, leading=15, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=3),
        "body": ParagraphStyle("Body", parent=base["BodyText"], textColor=INK, fontSize=9.5, leading=13, spaceAfter=3),
        "small": ParagraphStyle("Small", parent=base["BodyText"], textColor=MUTED, fontSize=8.2, leading=11),
        "guardrail": ParagraphStyle("Guardrail", parent=base["BodyText"], textColor=INK, backColor=colors.HexColor("#fff8db"), borderColor=VISA_GOLD, borderWidth=0.7, borderPadding=7, fontSize=9.2, leading=12),
        "table_cell": ParagraphStyle("TableCell", parent=base["BodyText"], textColor=INK, fontSize=7.5, leading=9.5),
        "info_key": ParagraphStyle("InfoKey", parent=base["BodyText"], textColor=VISA_BLUE, fontSize=8.5, leading=11, fontName="Helvetica-Bold"),
        "info_value": ParagraphStyle("InfoValue", parent=base["BodyText"], textColor=INK, fontSize=8.5, leading=11),
        "metric_label": ParagraphStyle("MetricLabel", parent=base["BodyText"], textColor=MUTED, fontSize=7.5, leading=9),
        "metric_value": ParagraphStyle("MetricValue", parent=base["BodyText"], textColor=VISA_BLUE, fontSize=16, leading=18, fontName="Helvetica-Bold"),
    }


def _draw_page_frame(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(16 * mm, height - 10 * mm, width - 16 * mm, height - 10 * mm)
    canvas.setFillColor(VISA_BLUE)
    canvas.setFont("Helvetica-BoldOblique", 13)
    canvas.drawRightString(width - 16 * mm, height - 8 * mm, "VISA")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(16 * mm, 8 * mm, "VCA Multi-Agent Synthetic Researcher - VCA pilot report")
    canvas.drawRightString(width - 16 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()
