from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from .consulting import format_decision_brief_markdown
from .pdf_report import build_consultant_pdf_report
from .reporting import build_markdown_report
from .schemas import SurveyRun


def build_consultant_delivery_pack(run: SurveyRun) -> bytes:
    """Build a portable consultant delivery pack without exposing credentials."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("README.md", _delivery_readme(run))
        bundle.writestr("01_decision_brief.md", format_decision_brief_markdown(run))
        bundle.writestr("02_consultant_report.md", build_markdown_report(run))
        bundle.writestr("03_persona_responses.csv", _responses_csv(run))
        bundle.writestr("04_validation.json", _safe_json(run.validation))
        bundle.writestr("05_full_run.json", _safe_json(run.asdict()))
        bundle.writestr("06_input_source_audit.json", _safe_json(run.aggregate.get("input_source", {})))
        bundle.writestr("07_methodology_and_governance.md", _methodology_and_governance(run))
        bundle.writestr("08_pilot_readiness_gate.json", _safe_json(build_pilot_readiness_gate(run)))
        bundle.writestr("09_consultant_report.pdf", build_consultant_pdf_report(run))
    return buffer.getvalue()


def build_pilot_readiness_gate(run: SurveyRun) -> list[dict[str, str]]:
    """Return a concise readiness checklist for partner review."""
    aggregate = run.aggregate
    validation = run.validation
    provider = str(aggregate.get("provider", "mock"))
    runtime = aggregate.get("runtime", {})
    input_source = aggregate.get("input_source", {})
    readiness = [
        _gate_row(
            "Real IBM model proof",
            provider == "watsonx",
            f"Provider recorded for this run: {provider}; model: {aggregate.get('model_id', 'n/a')}.",
            "Run with MODEL_PROVIDER=watsonx and configured Code Engine/local secrets before partner sign-off.",
        ),
        _gate_row(
            "Flexible survey ingestion",
            bool(run.questions)
            and input_source.get("source")
            in {
                "api",
                "direct_text",
                "direct_text_after_failed_upload",
                "edited_preset_or_direct_text",
                "sample_pdf",
                "uploaded_file",
                "uploaded_file_edited_text",
                "watsonx_smoke_test",
                "yaml_file",
            },
            f"{len(run.questions)} parsed question(s); source={input_source.get('source', 'n/a')}; file_type={input_source.get('file_type', 'n/a')}.",
            "Upload or paste a real survey/interview guide and confirm parser output before running.",
        ),
        _gate_row(
            "Persona-level traceability",
            bool(run.responses) and aggregate.get("respondent_count", 0) > 0,
            f"{aggregate.get('respondent_count', 0)} synthetic respondent(s), {aggregate.get('response_count', 0)} persona-question response(s).",
            "Increase respondent count or inspect errors if no traceable persona rows are returned.",
        ),
        _gate_row(
            "Aggregated consultant insight",
            bool(aggregate.get("concept_summary")) and bool(aggregate.get("decision_brief")),
            f"{len(aggregate.get('concept_summary', {}))} concept summary block(s) plus VCA decision brief.",
            "Add at least one adoption/appeal question and one concept before treating output as decision evidence.",
        ),
        _gate_row(
            "Validation confidence",
            (validation.get("overall", {}).get("score") or 0) >= 70,
            f"Overall validation score {validation.get('overall', {}).get('score', 'n/a')}/100.",
            "Recalibrate persona weights, survey constructs, or model settings before partner sharing.",
        ),
        _gate_row(
            "Benchmark transparency",
            bool(validation.get("benchmark_alignment", {}).get("profiles")),
            f"Primary benchmark MAE {validation.get('benchmark_alignment', {}).get('primary_mae_percentage_points', 'n/a')} percentage points.",
            "Add or update public benchmark anchors before using claims about Swiss market behavior.",
        ),
        _gate_row(
            "Consultant export pack and PDF report",
            True,
            "ZIP pack includes decision brief, PDF report, Markdown report, CSV responses, full JSON, validation and governance notes.",
            "No action needed.",
        ),
        _gate_row(
            "Governance caveat",
            bool((aggregate.get("decision_brief") or {}).get("limitations")),
            "Decision brief includes limitations and real-customer validation guardrails.",
            "Add a human-review caveat before external sharing.",
        ),
        _gate_row(
            "Runtime usability",
            (runtime.get("elapsed_seconds") or 9999) < 120 or provider == "mock",
            f"Elapsed seconds: {runtime.get('elapsed_seconds', 'n/a')}.",
            "Use quick proof scope for live watsonx demo, then run full scope asynchronously if needed.",
        ),
    ]
    return readiness


def readiness_status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {"Ready": 0, "Needs attention": 0}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def _gate_row(check: str, passed: bool, evidence: str, action_if_not_ready: str) -> dict[str, str]:
    return {
        "check": check,
        "status": "Ready" if passed else "Needs attention",
        "evidence": evidence,
        "action_if_not_ready": action_if_not_ready if not passed else "",
    }


def _responses_csv(run: SurveyRun) -> str:
    output = io.StringIO()
    fieldnames = [
        "run_id",
        "persona_id",
        "persona_name",
        "persona_weight",
        "concept_id",
        "concept_name",
        "question_id",
        "question",
        "question_type",
        "answer_value",
        "answer_label",
        "answer_text",
        "rationale",
        "confidence",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    concept_lookup = {concept.id: concept.name for concept in run.concepts}
    question_lookup = {question.id: question.text for question in run.questions}
    for response in run.responses:
        row = response.asdict()
        row["concept_name"] = concept_lookup.get(response.concept_id, response.concept_id)
        row["question"] = question_lookup.get(response.question_id, response.question_id)
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    return output.getvalue()


def _delivery_readme(run: SurveyRun) -> str:
    aggregate = run.aggregate
    validation = run.validation
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join(
        [
            "# VCA Synthetic Research Delivery Pack",
            "",
            f"Run ID: `{run.run_id}`",
            f"Generated: {generated}",
            f"Provider: {aggregate.get('provider', 'mock')}",
            f"Model: {aggregate.get('model_id', 'n/a')}",
            f"Synthetic respondents: {aggregate.get('respondent_count', 'n/a')}",
            f"Persona-question responses: {aggregate.get('response_count', 'n/a')}",
            f"Overall validation score: {validation.get('overall', {}).get('score', 'n/a')}/100",
            "",
            "## Files",
            "",
            "- `01_decision_brief.md`: executive answer, decision posture, hypotheses, next real research.",
            "- `02_consultant_report.md`: longer consultant-readable report with KPI and validation evidence.",
            "- `03_persona_responses.csv`: traceable persona-level answers for appendix analysis.",
            "- `04_validation.json`: benchmark, consistency, coverage and realism checks.",
            "- `05_full_run.json`: complete structured run artifact for reproducibility.",
            "- `06_input_source_audit.json`: survey upload/extraction audit.",
            "- `07_methodology_and_governance.md`: model, algorithm, limitation and human-review notes.",
            "- `08_pilot_readiness_gate.json`: readiness checklist for partner review.",
            "- `09_consultant_report.pdf`: polished PDF report for partner sharing.",
            "",
            "## Guardrail",
            "",
            "This pack is directional early-stage evidence. It is designed to complement real surveys and interviews, not replace final customer validation.",
        ]
    )


def _methodology_and_governance(run: SurveyRun) -> str:
    aggregate = run.aggregate
    decision = aggregate.get("decision_brief", {})
    lines = [
        "# Methodology And Governance",
        "",
        "## Algorithm Stack",
        "",
        "1. Normalize uploaded or pasted survey text from PDF, DOCX, XLSX, CSV, TXT or Markdown.",
        "2. Parse arbitrary survey/interview questions into structured question types and measured constructs.",
        "3. Expand public-data-grounded Swiss archetypes into a weighted synthetic micro-population.",
        "4. Run persona-conditioned respondent agents independently across concepts and questions.",
        "5. Aggregate weighted adoption, pricing, feature, barrier and segment-fit signals.",
        "6. Validate with benchmark alignment, repeated-run consistency, coverage and realism checks.",
        "7. Synthesize a VCA-style decision brief with caveats and recommended real research.",
        "",
        "## Model Stack",
        "",
        f"- Provider recorded for this run: `{aggregate.get('provider', 'mock')}`.",
        f"- Model recorded for this run: `{aggregate.get('model_id', 'n/a')}`.",
        "- IBM watsonx.ai / Granite is the intended real-model path for partner proof.",
        "- MockLLM exists only for CI, rehearsal and quota-contingency reliability.",
        "",
        "## Governance",
        "",
        "- No Visa internal or client-sensitive data is required by the base prototype.",
        "- Public Swiss payment and demographic benchmarks are used as calibration anchors.",
        "- A consultant should review extracted questions, parsed types and persona-level outliers before external sharing.",
        "- Final validation should be conducted by Visa using internal surveys and customer insight data when available.",
        "",
        "## Run Limitations",
        "",
    ]
    limitations = decision.get("limitations") or [
        "Synthetic output is directional and must not be treated as real customer truth."
    ]
    lines.extend(f"- {item}" for item in limitations)
    return "\n".join(lines)


def _safe_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
