from __future__ import annotations

from datetime import datetime, timezone

from .schemas import SurveyRun


def build_markdown_report(run: SurveyRun) -> str:
    """Create a consultant-readable report that can be pasted into a deck or email."""
    aggregate = run.aggregate
    validation = run.validation
    analyst = aggregate.get("analyst", {})
    lines = [
        "# Visa Synthetic Research Copilot Report",
        "",
        f"Run ID: `{run.run_id}`",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Executive Recommendation",
        "",
        analyst.get("recommendation", "No recommendation generated."),
        "",
        analyst.get("why", ""),
        "",
        "## Concept Summary",
        "",
        "| Concept | Adoption index | Mean Likert | Respondents |",
        "| --- | ---: | ---: | ---: |",
    ]
    for concept_id, summary in aggregate.get("concept_summary", {}).items():
        lines.append(
            f"| {concept_id} | {summary.get('adoption_index_0_100')} | "
            f"{summary.get('mean_likert')} | {summary.get('respondents')} |"
        )

    lines.extend([
        "",
        "## Pricing Signals",
        "",
        "| Concept | Weighted mean acceptable fee | Range |",
        "| --- | ---: | --- |",
    ])
    for concept_id, price in aggregate.get("price_summary", {}).items():
        lines.append(
            f"| {concept_id} | CHF {price.get('weighted_mean_chf')} | "
            f"CHF {price.get('min_chf')} to CHF {price.get('max_chf')} |"
        )

    lines.extend([
        "",
        "## Segment Fit",
        "",
        "| Concept:Segment | Mean Likert |",
        "| --- | ---: |",
    ])
    for key, value in sorted(aggregate.get("segment_fit", {}).items()):
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Validation Snapshot",
        "",
        f"- Benchmark alignment: {validation.get('benchmark_alignment', {}).get('score')}",
        f"- Consistency score: {validation.get('internal_consistency', {}).get('score')}",
        f"- Coverage score: {validation.get('coverage', {}).get('score')}",
        "",
        "## Guardrail",
        "",
        analyst.get(
            "do_not_overclaim",
            "Synthetic responses are directional and should complement, not replace, real customer research.",
        ),
    ])
    return "\n".join(line for line in lines if line is not None)
