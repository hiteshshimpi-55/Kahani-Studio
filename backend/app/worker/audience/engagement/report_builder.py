"""Build EngagementReport by orchestrating simulation + aggregation."""

from __future__ import annotations

from app.worker.audience.engagement.aggregator import aggregate
from app.worker.audience.engagement.models import EngagementReport
from app.worker.audience.personas.models import Persona
from app.worker.audience.simulation.simulator import AudienceSimulator


def build_engagement_report(
    personas: list[Persona],
    script: str,
    part_count: int,
) -> EngagementReport:
    """Run simulation for all personas and build aggregated report."""
    simulator = AudienceSimulator()
    results = simulator.simulate(personas, script, part_count)
    return aggregate(results, part_count)
