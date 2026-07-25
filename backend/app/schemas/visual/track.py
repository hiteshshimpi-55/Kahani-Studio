"""Visual Director contracts — PRD §6.7 VisualTrack.

Planner emits a typed shot list on the beat clock; renderer compiles each shot
into still (primary) or short clip (secondary) prompts with character identity refs.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ShotSize(StrEnum):
    ECU = "ecu"  # extreme close-up
    CU = "cu"
    MCU = "mcu"
    MS = "ms"  # medium
    MLS = "mls"
    LS = "ls"
    ELS = "els"  # extreme long / establishing


class CameraAngle(StrEnum):
    OVERHEAD = "overhead"
    HIGH = "high"
    NEUTRAL = "neutral"
    LOW = "low"
    DUTCH = "dutch"


class CameraLevel(StrEnum):
    AERIAL = "aerial"
    EYE = "eye"
    SHOULDER = "shoulder"
    HIP = "hip"
    KNEE = "knee"
    GROUND = "ground"


class CameraMovement(StrEnum):
    STATIC = "static"
    PUSH_IN = "push_in"
    PULL_OUT = "pull_out"
    PAN_L = "pan_l"
    PAN_R = "pan_r"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    HANDHELD = "handheld"
    ORBIT = "orbit"


class Framing(StrEnum):
    SINGLE = "single"
    TWO_SHOT = "two_shot"
    GROUP = "group"
    OTS = "over_the_shoulder"
    POV = "pov"
    INSERT = "insert"


class MediaKind(StrEnum):
    STILL = "still"
    CLIP = "clip"


class DensityMode(StrEnum):
    """How many stills to plan per part."""

    SPARSE = "sparse"  # ~1 / 40s → ~3–4 per 150s (MVP default)
    NORMAL = "normal"  # ~1 / 25s → ~5–6
    DENSE = "dense"  # ~1 / 15s (Visibl-like; costlier)


class AspectRatio(StrEnum):
    PORTRAIT = "9:16"
    SQUARE = "1:1"
    LANDSCAPE = "16:9"


class CharacterOnScreen(BaseModel):
    """One cast slot in a shot — identity locked via sheet / face ref."""

    character_id: str = Field(..., min_length=1, max_length=64)
    expression: str = Field(..., min_length=1, max_length=128)
    pose: str | None = Field(default=None, max_length=256)
    screen_position: Literal["left", "center", "right", "bg_left", "bg_right"] | None = None
    facing: Literal["camera", "profile_l", "profile_r", "away", "three_quarter"] | None = None
    identity_sheet_id: str | None = Field(
        default=None,
        description="Ref to locked face/turnaround sheet for this character",
    )
    face_ref_url: str | None = None


class ShotView(BaseModel):
    """Ken Burns / crop hint for stills (Open Illuminations-style view)."""

    start: dict[str, float] = Field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        description="Normalized crop at t_start",
    )
    end: dict[str, float] = Field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        description="Normalized crop at t_end (Ken Burns)",
    )


class VisualShot(BaseModel):
    """One companion still or short clip on the beat clock."""

    shot_id: str = Field(..., min_length=1, max_length=64)
    beat_ids: list[str] = Field(default_factory=list)
    seq_ids: list[str] = Field(
        default_factory=list,
        description="NarrationPlan seq_ids this shot covers",
    )
    t_start_sec: float = Field(..., ge=0)
    t_end_sec: float = Field(..., gt=0)
    media_kind: MediaKind = MediaKind.STILL

    shot_size: ShotSize = ShotSize.MS
    camera_angle: CameraAngle = CameraAngle.NEUTRAL
    camera_level: CameraLevel = CameraLevel.EYE
    camera_movement: CameraMovement = CameraMovement.STATIC
    framing: Framing = Framing.SINGLE

    characters: list[CharacterOnScreen] = Field(default_factory=list, max_length=3)
    location_id: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    lighting: str | None = None
    mood: str | None = None

    visual_intent: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Human/director intent before prompt compile",
    )
    compiled_prompt: str | None = Field(
        default=None,
        description="Filled by prompt compiler from shot + style bible + identity sheets",
    )
    negative_prompt: str | None = None

    view: ShotView | None = None
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    asset_url: str | None = None
    trigger_reason: str | None = Field(
        default=None,
        description="location_change | character_enter | emotion_spike | cliff | establish | …",
    )


class CharacterIdentitySheet(BaseModel):
    """Locked face identity for series-long consistency."""

    character_id: str
    display_name: str
    identity_tokens: str = Field(
        ...,
        description="Locked look description (age, ethnicity, hair, bone structure…)",
    )
    turnaround_urls: dict[str, str] = Field(
        default_factory=dict,
        description="front | three_quarter | side | full_body → URL",
    )
    expression_grid_urls: dict[str, str] = Field(
        default_factory=dict,
        description="neutral | fear | anger | whisper | gasp | … → URL",
    )
    lora_id: str | None = None
    voice_provider_id: str | None = Field(
        default=None,
        description="Optional link to ElevenLabs voice_id from CastReport",
    )


class LocationSheet(BaseModel):
    location_id: str
    name: str
    description: str
    ref_urls: list[str] = Field(default_factory=list)


class StyleBible(BaseModel):
    series_id: str
    look: str = Field(..., description="e.g. cinematic thriller, muted teal-orange, film still")
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    avoid: list[str] = Field(default_factory=list)
    density: DensityMode = DensityMode.SPARSE
    allow_clips: bool = False
    max_stills_per_part: int = Field(default=5, ge=1, le=40)
    max_on_screen_characters: int = Field(default=3, ge=1, le=5)


class VisualDirectorInput(BaseModel):
    """Inputs to the Visual Director agent (after audio timings exist)."""

    series_id: str
    part: int = Field(..., ge=1)
    language: str = "hi"
    style_bible: StyleBible
    identity_sheets: list[CharacterIdentitySheet] = Field(default_factory=list)
    location_sheets: list[LocationSheet] = Field(default_factory=list)
    # Script beats with visual_cues + emotion (from ScriptPackage)
    beats: list[dict] = Field(default_factory=list)
    # NarrationPlan sequence for this part
    narration_sequence: list[dict] = Field(default_factory=list)
    # Real timings after TTS / forced alignment: seq_id → {t_start, t_end}
    seq_timings: dict[str, dict[str, float]] = Field(default_factory=dict)
    part_duration_sec: float = Field(..., gt=0)


class VisualTrack(BaseModel):
    """PRD agent output — companion visuals for one series part."""

    series_id: str
    part: int
    density: DensityMode
    aspect_ratio: AspectRatio
    shots: list[VisualShot] = Field(default_factory=list)
    identity_sheet_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
