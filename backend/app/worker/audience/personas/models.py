"""Persona domain models — synthetic listener cohort dimensions (PRD §6.9)."""

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """A synthetic listener with demographic + behavioral dimensions."""

    id: str
    age_band: str = Field(
        ..., description="16-20 | 21-24 | 25-34 | 35-44"
    )
    gender: str = Field(..., description="male | female | non_binary")
    city_tier: str = Field(..., description="tier_1 | tier_2 | tier_3")
    intent: str = Field(
        ...,
        description="romance_escape | thriller_binge | true_story_curiosity | commute_passtime | share_with_friends",
    )
    language_comfort: str = Field(
        ..., description="hindi | hinglish | english"
    )

    # Behavioral priors (overridden during calibration)
    attention_span_sec: float = Field(default=120.0, description="baseline attention span")
    skip_threshold: float = Field(
        default=0.3, ge=0, le=1, description="boredom threshold before skip impulse fires"
    )
    share_propensity: float = Field(
        default=0.1, ge=0, le=1, description="likelihood to share if engaged"
    )


class PersonaSimResult(BaseModel):
    """Result of simulating one persona against one part."""

    persona_id: str
    part: int
    attention_decay: float = Field(ge=0, le=1, description="normalized attention remaining at end")
    skip_impulse: float = Field(ge=0, le=1, description="peak skip impulse during part")
    p_continue: float = Field(ge=0, le=1, description="probability of continuing to next part")
    share_impulse: float = Field(ge=0, le=1)
    drop_reason: str | None = None
    fragile_beat_id: str | None = None
