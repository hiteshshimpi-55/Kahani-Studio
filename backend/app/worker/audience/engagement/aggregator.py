"""Aggregate PersonaSimResults into per-part PartFunnel metrics."""

from __future__ import annotations

from collections import defaultdict

from app.worker.audience.engagement.models import EngagementReport, PartFunnel
from app.worker.audience.personas.models import PersonaSimResult


def aggregate(results: list[PersonaSimResult], part_count: int) -> EngagementReport:
    """Aggregate raw persona sim results into an EngagementReport."""
    by_part: dict[int, list[PersonaSimResult]] = defaultdict(list)
    for r in results:
        by_part[r.part].append(r)

    persona_ids = {r.persona_id for r in results}
    persona_count = len(persona_ids)

    funnels: list[PartFunnel] = []
    surviving = persona_count  # personas that haven't dropped yet

    for part_num in range(1, part_count + 1):
        part_results = by_part.get(part_num, [])
        if not part_results:
            funnels.append(PartFunnel(part=part_num, start_rate=0.0, p_continue=0.0))
            continue

        start_rate = surviving / persona_count if persona_count > 0 else 0.0
        avg_p_continue = sum(r.p_continue for r in part_results) / len(part_results)

        # Drop reasons
        drop_reasons_counter: dict[str, int] = defaultdict(int)
        for r in part_results:
            if r.drop_reason:
                drop_reasons_counter[r.drop_reason] += 1
        top_drop_reasons = sorted(drop_reasons_counter, key=drop_reasons_counter.get, reverse=True)[:3]

        # Fragile beats
        fragile_counter: dict[str, int] = defaultdict(int)
        for r in part_results:
            if r.fragile_beat_id:
                fragile_counter[r.fragile_beat_id] += 1
        top_fragile = sorted(fragile_counter, key=fragile_counter.get, reverse=True)[:3]

        # Cohort disagreements — find dimensions where p_continue variance is high
        disagreements = _find_disagreements(part_results)

        funnels.append(
            PartFunnel(
                part=part_num,
                start_rate=round(start_rate, 3),
                p_continue=round(avg_p_continue, 3),
                drop_reasons=top_drop_reasons,
                fragile_beats=top_fragile,
                cohort_disagreements=disagreements,
            )
        )

        # Update surviving count for next part
        dropped = sum(1 for r in part_results if r.p_continue < 0.4)
        surviving = max(0, surviving - dropped)

    return EngagementReport(
        persona_count=persona_count,
        calibration_status="UNCALIBRATED",
        funnel=funnels,
    )


def _find_disagreements(results: list[PersonaSimResult]) -> list[str]:
    """Identify cohort segments that diverge from mean p_continue."""
    if len(results) < 4:
        return []

    # We don't have persona detail here — just flag when variance is high
    p_values = [r.p_continue for r in results]
    mean_p = sum(p_values) / len(p_values)
    variance = sum((p - mean_p) ** 2 for p in p_values) / len(p_values)

    disagreements: list[str] = []
    if variance > 0.04:  # std dev > 0.2
        # High variance means cohorts disagree
        high = [r for r in results if r.p_continue > mean_p + 0.15]
        low = [r for r in results if r.p_continue < mean_p - 0.15]
        if high and low:
            disagreements.append(
                f"High variance (σ²={variance:.3f}): {len(high)} personas love it, {len(low)} want to drop"
            )
    return disagreements
