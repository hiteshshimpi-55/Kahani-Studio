"""Episode visual plan — output of the Director agent.

The unit of work is a SHOT: one still image shown for [t_start, t_end)
of the audio timeline, framed by film grammar (establishing wide, OTS
pairs, close-ups on emotional beats, group shots for 3+, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SHOT_SIZES = ("establishing_wide", "wide", "medium", "two_shot", "ots", "close_up", "extreme_close_up", "insert", "group")


class StyleSpec(BaseModel):
    """Series-level look — derived from the STORY (genre/tone), not defaults."""

    genre: str = "drama"
    era_setting: str = "modern-day India"
    film_look: str = "cinematic photorealistic, 35mm film, shallow depth of field"
    palette: str = "true-to-life natural colors"
    lighting: str = "natural, motivated by the real time of day of each scene"
    negative: str = "cartoon, anime, illustration, text, watermark, extra fingers, deformed face"


class CharacterLook(BaseModel):
    """Locked identity for one character — same face/body everywhere."""

    id: str
    name: str
    appearance: str = Field(description="Face, age, build, hair — permanent traits")
    wardrobe: dict[str, str] = Field(
        default_factory=dict,
        description="story_day (e.g. 'day1') → detailed outfit; clothes change when the day changes",
    )
    reference_image: str | None = None  # lookbook path once generated
    facing: str = Field(
        default="right",
        description="180-degree rule: keep this character facing the same screen direction in a scene",
    )


class SceneSpec(BaseModel):
    scene_id: str
    location: str
    time_of_day: str = "day"
    story_day: str = "day1"
    weather: str | None = None
    mood: str = "neutral"


class ShotSpec(BaseModel):
    shot_id: str
    scene_id: str
    t_start: float
    t_end: float
    shot_size: str = "medium"
    characters_on_screen: list[str] = Field(default_factory=list)
    action: str = Field(description="What is visibly happening in this frame")
    camera_motion: str = Field(
        default="slow_push_in",
        description="ken burns motion: slow_push_in | slow_pull_out | pan_left | pan_right | static",
    )
    camera_angle: str = Field(
        default="eye",
        description="camera angle: eye | low | high | overhead | pov | dutch",
    )
    expression: str = Field(
        default="",
        description="Visible facial emotion of each on-screen character in this beat",
    )
    seq_ids: list[str] = Field(default_factory=list, description="Audio stems this shot covers")

    @property
    def duration(self) -> float:
        return max(0.5, self.t_end - self.t_start)


class EpisodeVisualPlan(BaseModel):
    series_id: str
    title: str | None = None
    language: str = "hi"
    style: StyleSpec = Field(default_factory=StyleSpec)
    characters: list[CharacterLook] = Field(default_factory=list)
    scenes: list[SceneSpec] = Field(default_factory=list)
    shots: list[ShotSpec] = Field(default_factory=list)

    def scene(self, scene_id: str) -> SceneSpec | None:
        return next((s for s in self.scenes if s.scene_id == scene_id), None)

    def character(self, char_id: str) -> CharacterLook | None:
        cid = char_id.upper()
        return next((c for c in self.characters if c.id.upper() == cid), None)
