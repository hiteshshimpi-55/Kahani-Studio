"""Domain models for structured edit patches proposed by simulation."""

from pydantic import BaseModel, Field


class PatchProposal(BaseModel):
    """One structured edit proposal with expected metric delta."""

    beat_id: str
    part: int
    patch_type: str = Field(
        ...,
        description="e.g. shorten_cold_open, move_reveal, raise_stakes, add_open_loop, cliff_rewrite",
    )
    rationale: str
    suggested_text: str | None = None
    expected_delta: dict = Field(
        default_factory=dict,
        description="{'p_continue': +0.05, 'confidence': 'low'}",
    )


class PatchSet(BaseModel):
    """Collection of patches from a single simulation run."""

    sim_run_id: str
    patches: list[PatchProposal] = Field(default_factory=list)
