from __future__ import annotations

from datetime import datetime, timezone

from .schemas import SurveyRun


def build_markdown_report(run: SurveyRun) -> str:
    """Create a consultant-readable report that can be pasted into a deck or email."""
    aggregate = run.aggregate
    validation = run.validation
    analyst = aggregate.get("analyst", {})
    research = aggregate.get("research_brief", {})
    decision = aggregate.get("decision_brief", {})
    lines = [
        "# Visa Synthetic Customer Lab Report",
        "",
        f"Run ID: `{run.run_id}`",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Time to insight: {aggregate.get('runtime', {}).get('elapsed_seconds', 'n/a')} seconds",
        f"Synthetic responses: {aggregate.get('response_count', 'n/a')}",
        f"Provider: {aggregate.get('provider', 'mock')}",
        "",
        "## Input Source",
        "",
        f"- Source: {aggregate.get('input_source', {}).get('source', 'n/a')}",
        f"- File: {aggregate.get('input_source', {}).get('file_name') or 'pasted text'}",
        f"- File type: {aggregate.get('input_source', {}).get('file_type', 'text')}",
        f"- Characters analyzed: {aggregate.get('input_source', {}).get('char_count', 'n/a')}",
        "",
        "## Research Brief",
        "",
        f"- Objective: {research.get('project_objective', 'n/a')}",
        f"- Client decision: {research.get('client_decision', 'n/a')}",
        f"- Decision rule: {research.get('decision_rule', 'n/a')}",
        "",
        "## Decision Brief",
        "",
        decision.get("executive_answer", "Decision brief was not generated for this run."),
        "",
        f"Decision posture: {decision.get('decision_posture', 'n/a')}",
        f"Validation posture: {decision.get('validation_band', 'n/a')} ({decision.get('validation_score', 'n/a')}/100)",
        "",
        "### Synthetic Customer Lens",
        "",
        f"- Positioning: {(decision.get('synthetic_customer_lens') or {}).get('positioning', 'n/a')}",
        *[f"- Value proposition question: {item}" for item in (decision.get("synthetic_customer_lens") or {}).get("value_proposition_questions", [])],
        *[
            f"- Use-case fit: {item.get('use_case')} = {item.get('fit')} ({item.get('how_this_run_supports_it')})"
            for item in (decision.get("synthetic_customer_lens") or {}).get("use_case_fit", [])
        ],
        *[
            f"- Segment: {item.get('segment')} | best fit: {item.get('likely_best_fit')} | need: {item.get('need_state')} | message: {item.get('message_to_test')}"
            for item in (decision.get("synthetic_customer_lens") or {}).get("synthetic_customer_board", [])
        ],
        *[
            f"- Scenario move: {item.get('move')} | {item.get('what_to_change_next')} | {item.get('why_it_matters')}"
            for item in (decision.get("synthetic_customer_lens") or {}).get("scenario_planning_moves", [])
        ],
        "",
        "### So What for VCA",
        "",
        *[f"- {item}" for item in decision.get("so_what", [])],
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
        f"- Overall validation confidence: {validation.get('overall', {}).get('score')}",
        f"- Benchmark alignment: {validation.get('benchmark_alignment', {}).get('score')}",
        f"- Consistency score: {validation.get('internal_consistency', {}).get('score')}",
        f"- Coverage score: {validation.get('coverage', {}).get('score')}",
        f"- Question coverage score: {validation.get('question_coverage', {}).get('score')}",
        f"- Realism rubric score: {validation.get('realism_rubric', {}).get('score')}",
        "",
        "## KPI Evidence",
        "",
        f"- Time to first synthetic insight target < 2 min: {aggregate.get('runtime', {}).get('elapsed_seconds', 'n/a')}s",
        f"- Number of synthetic responses: {aggregate.get('response_count', 'n/a')}",
        f"- JSON parse success target > 95%: {aggregate.get('runtime', {}).get('json_parse_success_rate', 'n/a')}%",
        f"- Internal consistency target Likert std < 0.5: {validation.get('internal_consistency', {}).get('avg_likert_std')}",
        f"- Benchmark alignment target MAE < 10pp: {validation.get('benchmark_alignment', {}).get('primary_mae_percentage_points')}",
        "",
        "## Guardrail",
        "",
        analyst.get(
            "do_not_overclaim",
            "Synthetic responses are directional and should complement, not replace, real customer research.",
        ),
    ])
    return "\n".join(line for line in lines if line is not None)
