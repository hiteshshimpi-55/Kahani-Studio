"""ffmpeg assembly — Ken Burns motion per still, hard cuts, audio mux.

Each shot still becomes a clip of exactly (t_end - t_start) seconds with
subtle motion (push-in / pull-out / pan). Clips are concatenated with
hard cuts (drama convention) and muxed with the rendered audiobook mix.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from app.core.config import settings
from app.schemas.visuals import EpisodeVisualPlan, ShotSpec

log = logging.getLogger(__name__)

# Upscale before zoompan to avoid sub-pixel jitter
_SUPERSAMPLE_W = 2160


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-600:]}")


def _kenburns_filter(shot: ShotSpec, frames: int, w: int, h: int) -> str:
    """zoompan expression per camera motion."""
    zoom_step = 0.10 / max(frames, 1)  # ~10% zoom over the clip
    centre = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    motion = shot.camera_motion
    if motion == "slow_pull_out":
        z = f"z='max(1.001,1.10-{zoom_step}*on)'"
        zp = f"zoompan={z}:{centre}"
    elif motion == "pan_left":
        zp = f"zoompan=z='1.12':x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)'"
    elif motion == "pan_right":
        zp = f"zoompan=z='1.12':x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)'"
    elif motion == "static":
        zp = f"zoompan=z='min(1.001+{zoom_step / 3}*on,1.04)':{centre}"
    else:  # slow_push_in (default)
        zp = f"zoompan=z='min(1.001+{zoom_step}*on,1.12)':{centre}"
    return (
        f"scale={_SUPERSAMPLE_W}:-2,"
        f"{zp}:d={frames}:s={w}x{h}:fps={settings.visual_video_fps},"
        f"format=yuv420p"
    )


def assemble_episode_video(
    plan: EpisodeVisualPlan,
    stills: dict[str, str],
    audio_path: str | None,
    out_dir: Path,
) -> Path:
    w, h = settings.visual_video_width, settings.visual_video_height
    fps = settings.visual_video_fps
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths: list[Path] = []
    last_still: str | None = None
    for shot in plan.shots:
        still = stills.get(shot.shot_id) or last_still
        if not still:
            log.warning("no still for %s and no previous frame — skipping", shot.shot_id)
            continue
        last_still = still
        frames = max(int(round(shot.duration * fps)), fps // 2)
        clip = clips_dir / f"{shot.shot_id}.mp4"
        _run([
            "ffmpeg", "-y", "-loop", "1", "-i", still,
            "-vf", _kenburns_filter(shot, frames, w, h),
            "-frames:v", str(frames),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-an", str(clip),
        ])
        clip_paths.append(clip)
        log.info("clip_ok %s %.1fs motion=%s", shot.shot_id, shot.duration, shot.camera_motion)

    if not clip_paths:
        raise RuntimeError("no clips produced — cannot assemble video")

    concat_list = clips_dir / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in clip_paths))
    silent = out_dir / "episode_silent.mp4"
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy", str(silent),
    ])

    final = out_dir / "episode.mp4"
    if audio_path and Path(audio_path).exists():
        _run([
            "ffmpeg", "-y", "-i", str(silent), "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final),
        ])
    else:
        final.write_bytes(silent.read_bytes())
    log.info("episode_video_ok %s shots=%d", final, len(clip_paths))
    return final
