# Visual generation — from-scratch plan

> Status: **implemented (v1 vertical slice)**. Provider decision: **Gemini** —
> text model as the Director agent, Nano Banana (`gemini-3.1-flash-image`,
> fallback `gemini-2.5-flash-image`) for lookbook + scene stills with character
> reference images ($0.039/image); **ffmpeg Ken Burns** turns timed stills into
> a 9:16 1080×1920 MP4 muxed with the audiobook mix. ElevenLabs has no
> image/video API (audio only). Requires `GEMINI_API_KEY` in `.env`.
>
> Implementation map:
> - `backend/app/integrations/gemini/` — client, JSON text, image gen with refs
> - `backend/app/schemas/visuals/plan.py` — StyleSpec / CharacterLook / SceneSpec / ShotSpec
> - `backend/app/services/visuals/` — `prompts.py` (film-grammar rules), `director.py`
>   (Gemini plan + heuristic fallback), `lookbook.py`, `renderer.py`, `video.py`, `service.py`
> - `AudiobookService.render_preview` now returns `timeline` (per-stem/SFX t_start/t_end) + `duration_sec`
> - API: `POST /api/v1/visuals/render` (ARQ job `visual_episode_job`), `GET /api/v1/visuals/{series_id}`
> - CLI: `python -m scripts.render_visual_episode app/fixtures/script_crime_mystery.json --series-id crime_v1`

## Why the old approach was wrong

1. **Disconnected from audio** — visuals were a parallel API (`/identity`, `/visual/plan`, `/visual/render`) with no handoff from ScriptPackage → audiobook → stills.
2. **Heuristic "director"** — rule-based shot triggers (emotion keywords, density timers) produced generic frames, not story-driven scenes.
3. **Identity bolted on** — face sheets + PuLID were a separate product surface; characters did not flow from the script bible the way voices do.
4. **No UI wiring** — Projects Visuals page was a stub; assets lived only on disk/DB.
5. **Wrong unit of work** — "shots" floated free of screenplay events. We need **one visual beat per story beat**, locked to the audio timeline.

## Goal

Pocket FM–style companion visuals for Hindi (default) audio dramas:

- After a part's **audio** exists, generate **scene images** that sync to narration/dialogue.
- Same characters look like the same people across the episode.
- Quality bar: cinematic stills that feel directed, not stock AI wallpaper.

## Locked product decisions (v1)

| Decision | Choice |
|----------|--------|
| Language | Hindi default (same as audio) |
| Unit | One still per **visual beat** derived from screenplay events |
| Sync | `t_start` / `t_end` from audiobook stem/SFX timeline |
| Aspect | 9:16 mobile-first (Pocket FM) |
| Video / clips | Out of scope for v1 (stills + Ken Burns in the player later) |
| Provider | Decide at implementation kickoff (Replicate Flux family, Fal, or similar) — **not** wired until plan is approved |
| Orchestration | Project → ScriptPackage → Audiobook preview → **Visual plan + render** (one pipeline) |

## Pipeline (new)

```text
ScriptPackage (screenplay + bible)
        │
        ▼
AudiobookService.render_preview  →  stems + SFX + bed + seq_timings
        │
        ▼
VisualBeatPlanner (NEW)
  - Walk ordered screenplay events (LINE / SFX / scene breaks)
  - Emit VisualBeat { beat_id, t_start, t_end, location, characters[], mood, framing, prompt_brief }
  - Density: ~1 still / 8–12s of audio (budget-capped per part)
        │
        ▼
CharacterLookbook (NEW) — once per series/part cast
  - From bible voice/appearance notes → locked reference portrait per character
  - Stored under DATA_DIR/visual/{project_or_series}/lookbook/
        │
        ▼
SceneStillRenderer (NEW)
  - For each VisualBeat: compile prompt (location + action + mood + style bible)
  - Face-lock when ≤1 hero character on screen; wide plates when establish / crowd
  - Write parts/p{N}/{beat_id}.webp + DB rows
        │
        ▼
Timeline API + Project Visuals UI
  - Player: audio scrub + still crossfade on beat boundaries
```

## Data model (replace orphaned tables)

Keep Alembic history (`001_visual_identity`); add a **new** migration that drops unused tables and creates:

- `visual_series` — style bible, linked to `project_id` (not a free-floating Series)
- `character_look` — locked portrait path + appearance tokens
- `visual_part` — part number, duration, plan JSON
- `visual_beat_asset` — beat_id, t_start, t_end, file_path, prompt, seed

Orphaned tables from the old stack (`series`, `characters`, `locations`, `visual_tracks`, …) should be dropped in that migration.

## API sketch (new, not the old routes)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/visuals/plan` | ScriptPackage + audiobook timings → beat plan |
| `POST` | `/api/v1/visuals/lookbook` | Generate/lock character looks from bible |
| `POST` | `/api/v1/visuals/render` | Render stills for a part (sync or ARQ) |
| `GET` | `/api/v1/visuals/{project_id}/parts/{n}/timeline` | Timed stills for UI |

Mount under `visuals` (plural) so we never collide with deleted `/visual` / `/identity` semantics.

## Services layout (proposed)

```text
backend/app/services/visuals/
  planner.py      # screenplay + timings → VisualBeat list
  lookbook.py     # character reference images
  renderer.py     # provider calls + disk write
  prompts.py      # prompt compiler (mood, framing, negative)
backend/app/integrations/<provider>/
  client.py
  stills.py
```

Reuse patterns from audiobook: thin routes → services → integrations; ARQ for long renders; assets under `DATA_DIR`.

## What we keep from the old world (ideas only)

- 9:16 companion stills as the product form
- Face reference for close-ups (mechanism TBD with new provider)
- Budget / density caps so a 60s part does not spawn 40 images
- Optional vector priors later (style/mood), **not** required for v1

## Explicit non-goals (v1)

- LLM "Visual Director" agent (start with script-structure planner; add LLM later if needed)
- I2V / clips
- Standalone Series entity decoupled from Project
- Regenerating looks every render (lookbook is lock-once)

## Implementation phases

1. **Schema + empty services** — migration, DTOs, `/visuals/*` stubs returning 501
2. **Planner** — crime-mystery + Dandi fixtures → beat JSON with timings from a real audiobook render
3. **Lookbook** — one provider call per character; lock + reuse
4. **Renderer** — batch stills; ARQ job; disk + DB
5. **UI** — Project Visuals page consumes timeline; scrub with audio preview
6. **Polish** — prompt style bible, negative prompts, regenerate-one-beat

## Acceptance test (first vertical slice)

1. Render `script_crime_mystery.json` audio with ElevenLabs (existing path).
2. Plan beats from that screenplay + measured stem timings.
3. Generate lookbook for Inspector / Vikram / Dr Kapoor / Narrator (narrator may be off-screen).
4. Render ≤8 stills for the ~90s part.
5. Open timeline JSON and confirm each still's `t_start` lands on a dialogue or SFX beat.

## Removed code (do not restore)

- `app/api/v1/{visual,identity,timeline}.py`
- `app/services/{visual,identity}/`
- `app/integrations/replicate/`
- `app/schemas/{visual,identity}/`
- `app/repository/models/{series,visual}.py` (ORM only; tables dropped later)
- `shot_templates` catalog + seed path
- `e2e_visual_horror.py`, `rerender_cinematic.py`, `visual_horror_30s.json`
- `docs/visual-director-research.md`
