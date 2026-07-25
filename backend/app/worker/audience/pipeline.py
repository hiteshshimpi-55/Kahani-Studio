"""Audience Simulation Pipeline — orchestrates the full PRD §6.9 flow.

Steps:
  1. Structural audit (Layer A — deterministic)
  2. Generate persona cohort
  3. Run persona simulation (Layer B)
  4. Aggregate into EngagementReport
  5. Generate PatchSet
  6. Return combined results
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.worker.audience.audit.models import StructuralAuditResult
from app.worker.audience.audit.structural_audit import run_structural_audit
from app.worker.audience.engagement.models import EngagementReport
from app.worker.audience.engagement.report_builder import build_engagement_report
from app.worker.audience.patches.models import PatchSet
from app.worker.audience.patches.patch_generator import generate_patches
from app.worker.audience.personas.persona_generator import generate_personas

log = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Complete output of one audience simulation pipeline run."""

    sim_run_id: str
    audit: StructuralAuditResult
    engagement: EngagementReport
    patches: PatchSet


def run_audience_simulation(
    sim_run_id: str,
    script: str,
    part_count: int = 5,
    genre: str = "thriller",
    language: str = "hindi",
    persona_count: int = 24,
) -> SimulationResult:
    """Execute the full audience simulation pipeline.

    This is the main entry point called by the ARQ worker task.
    """
    log.info("sim_pipeline_start", extra={"sim_run_id": sim_run_id})

    # Step 1: Structural audit (Layer A)
    log.info("running_structural_audit", extra={"sim_run_id": sim_run_id})
    audit = run_structural_audit(script, part_count)

    # Step 2: Generate persona cohort
    log.info("generating_personas", extra={"sim_run_id": sim_run_id, "count": persona_count})
    personas = generate_personas(
        genre=genre,
        language=language,
        target_count=persona_count,
    )

    # Step 3 + 4: Simulate & aggregate
    log.info("running_persona_simulation", extra={"sim_run_id": sim_run_id, "personas": len(personas)})
    engagement = build_engagement_report(personas, script, part_count)

    # Step 5: Generate patches
    log.info("generating_patches", extra={"sim_run_id": sim_run_id})
    patches = generate_patches(sim_run_id, audit, engagement)

    log.info(
        "sim_pipeline_complete",
        extra={"sim_run_id": sim_run_id, "patch_count": len(patches.patches)},
    )

    return SimulationResult(
        sim_run_id=sim_run_id,
        audit=audit,
        engagement=engagement,
        patches=patches,
    )
