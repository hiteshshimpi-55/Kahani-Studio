"""Generate structured edit patches from simulation results.

Each patch maps to a beat_id and proposes a concrete edit type
with expected metric delta and confidence level.
"""

from __future__ import annotations

from app.worker.audience.audit.models import StructuralAuditResult
from app.worker.audience.engagement.models import EngagementReport
from app.worker.audience.patches.models import PatchProposal, PatchSet


# ---------------------------------------------------------------------------
# Patch generation rules
# ---------------------------------------------------------------------------


def _patches_from_audit(audit: StructuralAuditResult) -> list[PatchProposal]:
    """Generate patches from structural audit failures."""
    patches: list[PatchProposal] = []

    if audit.hook_score.score < 0.5:
        patches.append(
            PatchProposal(
                beat_id="p1_b01",
                part=1,
                patch_type="shorten_cold_open",
                rationale=f"Hook too slow ({audit.hook_score.comment}). "
                "Shorten or front-load tension in first 8 seconds.",
                expected_delta={"p_continue_p1": "+0.05", "confidence": "low"},
            )
        )

    if audit.cliffhanger_score.score < 0.5:
        patches.append(
            PatchProposal(
                beat_id="p1_b_last",
                part=1,
                patch_type="cliff_rewrite",
                rationale=f"Weak cliffhanger diversity ({audit.cliffhanger_score.comment}). "
                "Vary cliff types across parts.",
                expected_delta={"p_continue_avg": "+0.04", "confidence": "low"},
            )
        )

    if audit.pacing_score.score < 0.5:
        patches.append(
            PatchProposal(
                beat_id="p2_b01",
                part=2,
                patch_type="rebalance_pacing",
                rationale=f"Uneven pacing ({audit.pacing_score.comment}). "
                "Redistribute content for more even part lengths.",
                expected_delta={"drop_rate_reduction": "+0.03", "confidence": "low"},
            )
        )

    if audit.dialogue_score.score < 0.5:
        patches.append(
            PatchProposal(
                beat_id="p1_b03",
                part=1,
                patch_type="adjust_dialogue_ratio",
                rationale=f"Dialogue balance off ({audit.dialogue_score.comment}). "
                "Add or reduce dialogue to hit 20-45% sweet spot.",
                expected_delta={"engagement_lift": "+0.02", "confidence": "low"},
            )
        )

    return patches


def _patches_from_engagement(report: EngagementReport) -> list[PatchProposal]:
    """Generate patches from persona simulation engagement report."""
    patches: list[PatchProposal] = []

    for part_funnel in report.funnel:
        # Low P(continue) → investigate and patch
        if part_funnel.p_continue < 0.5:
            # Identify primary drop reason
            primary_reason = part_funnel.drop_reasons[0] if part_funnel.drop_reasons else "low_engagement"
            fragile = part_funnel.fragile_beats[0] if part_funnel.fragile_beats else f"p{part_funnel.part}_b01"

            patch_type = _drop_reason_to_patch_type(primary_reason)
            patches.append(
                PatchProposal(
                    beat_id=fragile,
                    part=part_funnel.part,
                    patch_type=patch_type,
                    rationale=f"Part {part_funnel.part} P(continue)={part_funnel.p_continue:.2f}. "
                    f"Primary drop reason: {primary_reason}. "
                    f"Fragile beat: {fragile}.",
                    expected_delta={
                        "p_continue": f"+{0.08 - part_funnel.p_continue * 0.05:.2f}",
                        "confidence": "low",
                    },
                )
            )

        # Cohort disagreements → targeted patches
        if part_funnel.cohort_disagreements:
            patches.append(
                PatchProposal(
                    beat_id=part_funnel.fragile_beats[0] if part_funnel.fragile_beats else f"p{part_funnel.part}_b01",
                    part=part_funnel.part,
                    patch_type="resolve_cohort_split",
                    rationale=f"Cohort split on part {part_funnel.part}: {part_funnel.cohort_disagreements[0]}",
                    expected_delta={"cohort_alignment": "+0.10", "confidence": "low"},
                )
            )

    return patches


def _drop_reason_to_patch_type(reason: str) -> str:
    """Map simulation drop reasons to patch operation types."""
    mapping = {
        "attention_exhausted": "raise_stakes",
        "skip_impulse_too_high": "add_tension_beat",
        "content_intent_mismatch": "realign_genre_signals",
        "weak_cold_open": "strengthen_cold_open",
        "gradual_disengagement": "add_open_loop",
    }
    return mapping.get(reason, "raise_stakes")


def generate_patches(
    sim_run_id: str,
    audit: StructuralAuditResult,
    engagement: EngagementReport,
) -> PatchSet:
    """Generate full PatchSet from audit + engagement results."""
    patches = _patches_from_audit(audit) + _patches_from_engagement(engagement)
    return PatchSet(sim_run_id=sim_run_id, patches=patches)
