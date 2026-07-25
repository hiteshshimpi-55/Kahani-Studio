# Visual Director Research — Companion Stills for Kissa Audiobooks

**Status:** Working research / design discussion (not a final build plan)  
**Last updated:** 2026-07-25  
**Owners:** Voice + visuals / casting track  
**Related:** `docs/PRD.md` §6.7–6.8 · `backend/app/schemas/visual/track.py` · cast/TTS work already in repo  

> Continue this file as we decide. Mark decisions with `DECISION:` and open questions with `OPEN:`.

---

## 1. Problem we are solving

After **script is locked** and **voices are cast + audio timed**, we need a **director agent** that behaves like a TV-serial / short-drama director — but for **images first** (short video only after stills are correct).

For each moment of the audiobook it must decide:

1. **What should be on screen** (who, where, expression, camera)
2. **How long** that image stays (seconds on the beat clock)
3. **How faces stay the same person** across the whole series while expression / pose / background change
4. **How scenes discover and change** (house exterior → interior → upstairs) without breaking continuity
5. **How the producer stays interactive** (approve / regen one shot, not re-run the whole movie)

Audio remains the product people finish. Visuals are the companion picture plane for the **web editor** and share cards — same philosophy as Pocket FM / Kuku FM (audio-primary), but with **timed cinematic stills** more like Visibl / Open Illuminations / micro-drama storyboards.

---

## 2. What we already have (context)

| Piece | State |
|--------|--------|
| PRD Visual generation (§6.7) | Spec: stills default, light I2V optional, identity consistency |
| Cast recommend API | Script → voice + SFX candidates (vector search) |
| TTS by `seq_id` | Stems under `/data`; regen one line |
| Voice bank (current key) | Free tier → **21 TTS-verified premades** (English). Hindi library voices need Creator+ |
| SFX prompt catalog | ~143 beds/spots in Databricks |
| `VisualTrack` Pydantic schema | Landed in `backend/app/schemas/visual/track.py` |
| Visual Director agent / image gen | **Not built yet** |
| Web timeline editor | Not built yet |

**Important coupling:** Cast report `voice_provider_id` should later link to the same character’s **identity sheet** (face), so audio cast and visual cast stay one “actor.”

---

## 3. Mental model: you are directing a micro-serial

Think in **three layers of “cast”**, not one:

```text
① STORY CAST (from script)
   Characters: NARRATOR, RIYA, ARJUN, THE_VOICE, …
   Locations: old house front, interior hall, upstairs

② AUDIO CAST (done / in progress)
   character_id → ElevenLabs voice_id + emotion delivery tags

③ VISUAL CAST (this challenge)
   character_id → locked face/body identity sheet
   location_id  → locked location sheet / background refs
   shot_id      → camera + who’s on screen + expression + duration
```

The **Visual Director** does not invent story. It **stages** the locked script + real audio timings into a shot list (`VisualTrack`), then a **renderer** turns each shot into an image.

Videos later = same shot list, different render path (`media_kind: clip`).

---

## 4. End-to-end pipeline (proposed)

```text
ScriptPackage (beats, visual_cues, bible)
        │
        ▼
NarrationPlan (seq_ids, speakers, emotions)
        │
        ▼
Cast + TTS  ──► stems + seq_timings {seq_id → t_start, t_end}
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
Character / Location bible               Style bible
        │                                      │
        ▼                                      │
IDENTITY LOCK (once per series)                │
  · Character identity sheets (face+body)      │
  · Location sheets (background refs)          │
        │                                      │
        └──────────────┬───────────────────────┘
                       ▼
            VISUAL DIRECTOR AGENT
            (script + timings + sheets → VisualTrack)
                       │
                       ▼
            Human interactive review
            (approve / tweak / regen shot)
                       │
                       ▼
            IMAGE RENDERER (stills)
            identity refs + ControlNet pose + location
                       │
                       ▼
            Timeline markers on beat clock
            (editor: VO / SFX / visuals)
                       │
                       ▼  (later, gated)
            Optional I2V on approved stills
```

**DECISION (proposed default):** Planner agent **before** any GPU image spend. Never freeform “generate pretty picture from whole script.”

---

## 5. Phase A — Select characters & lock identity (series bible)

### 5.1 Discover cast from script

Agent (or deterministic extract) walks the full script and builds:

- `character_id`, display name, role (narrator / lead / support / entity)
- Soft attributes: age band, gender, personality traits from dialogue + stage directions
- Screen weight: how often they speak / appear in `visual_cues`
- Relationships (for two-shots / OTS framing later)

For the sample horror beat:

| ID | Role | Visual needs |
|----|------|----------------|
| NARRATOR | Often **off-screen / atmospheric** | May be faceless VO; optional silhouette or none |
| RIYA | Lead | Full identity sheet + expression grid |
| ARJUN | Lead | Full identity sheet + expression grid |
| THE_VOICE | Entity | Distorted / partial face / shadow — still locked silhouette rules |

**OPEN:** Is the narrator ever shown? Pocket-FM style often = VO only. Recommend: `narrator_on_screen: false` by default unless style bible says otherwise.

### 5.2 Character identity sheet (face + body — series-long)

Generated **once** (or regen with version bump), then **reused every shot**:

1. **Identity tokens (text)** — bone structure, skin, hair, age, clothing baseline, ethnicity, “do not change across episodes”
2. **Turnaround set** — front, ¾, side, full body (same person)
3. **Expression grid** — neutral, nervous whisper, dismissive smile, gasp/panic, menace, etc. (same bone structure, different face muscles)
4. **Optional LoRA / embedding** — stronger lock for multi-part serials
5. **Link** `voice_provider_id` from CastReport

**Tech (2026 practical stack):** text bible → Flux/SDXL stills → InstantID / PuLID / IP-Adapter FaceID on every later shot; OpenPose ControlNet for multi-person blocking.

**Rule:** Never rely on the model “remembering” Riya from prompt prose alone. Always pass `face_ref_url` / sheet id.

### 5.3 Location / background sheets

Same idea for places:

- `location_id` (e.g. `old_house_exterior`, `old_house_hall`, `old_house_stairs`)
- Description + 2–4 reference stills (day/night variants if needed)
- Continuity notes: “same blue door,” “same cracked verandah”

When the script moves **inside**, director switches `location_id` — backgrounds change **on purpose**, but within one location they stay locked.

### 5.4 Style bible (series look)

One look for the whole movie/serial slice:

- Aspect (default **9:16** for share; 16:9 for editor optional)
- Palette / lens language (“cinematic thriller, muted, film still, no text”)
- Density mode: sparse / normal / dense
- `allow_clips: false` until stills are good
- Max stills per part (PRD: ~3–5 MVP)

---

## 6. Phase B — Visual Director: line / beat walk

### 6.1 What it reads

- Script beats (text, speaker, emotion, `visual_cues`, sfx)
- NarrationPlan `seq_id`s
- **Real audio timings** after TTS (forced alignment or stem durations)
- Identity + location + style bibles

### 6.2 What it does *not* do first

It does **not** immediately call an image model with a paragraph of the whole scene.

It emits a typed **`VisualTrack`**: ordered `shots[]` with camera language + cast slots + durations (see schema in repo).

### 6.3 Shot discovery — when do we cut to a new image?

Not “one image per line” and not “one image per 30s fixed.” Hybrid triggers (serial director logic):

| Trigger | Example from horror beat | Typical shot |
|---------|--------------------------|--------------|
| **Establish location** | Four friends outside old house | LS / ELS exterior night |
| **Location change** | Cut inside | New location sheet, door creak insert |
| **Emotion spike** | RIYA gasp / panic | CU / ECU Riya fear expression |
| **Dialogue peak / conflict** | ARJUN dismissive vs RIYA nervous | Two-shot or OTS |
| **Reveal / supernatural** | THE_VOICE whispers name | Low angle, dutch, shadow entity |
| **Time budget** | Cap stills | Merge quiet narration into held wide |

**MVP density (proposed):** `sparse` ≈ **1 still per 20–40s** → **~3–5 images per ~150s part** (matches PRD grind).  
Interactive mode later can densify “action beats” only.

### 6.4 How long should one image stay?

```text
shot.t_start_sec / t_end_sec  ← snapped to seq_timings / beat clock
duration = t_end - t_start
```

Heuristics:

- **Establish:** longer (8–20s) while narrator sets place
- **Dialogue two-shot:** hold across a short exchange if blocking doesn’t change
- **Emotion spike / shout:** shorter, punchier (2–5s), maybe ECU
- **Never shorter than ~1.5s** (slideshow flicker) unless intentional flash
- **Ken Burns** optional inside one still (`ShotView` start/end crop) so a 12s hold still feels alive — without true video yet

**OPEN:** Exact min/max duration knobs per genre (horror vs romance).

### 6.5 Camera language (director brain)

Per shot, decide enums (already in schema — CineScale-inspired):

- **Shot size:** ECU → ELS  
- **Angle:** overhead / high / neutral / low / dutch  
- **Level:** aerial → ground  
- **Movement:** `static` for stills; pan/push reserved for Ken Burns metadata or later I2V  
- **Framing:** single / two-shot / group / OTS / POV / insert  

“Roll the camera through each expression” in **image mode** means:

> Sequence of stills that track emotional beats — not one frozen face for the whole scene.

Example for RIYA in the sample:

1. Nervous whisper at door (MCU, soft key)  
2. Gasp ECU when name is spoken  
3. Panic pull-back two-shot as she grabs Arjun  

Same `identity_sheet_id`, different `expression` + `shot_size`.

### 6.6 Multi-character in one frame

- Cap **≤ 2–3 on-screen** for MVP (schema `max_length=3`) even if 5 exist in bible  
- Each on-screen character = slot: `character_id`, expression, pose, screen_position, face_ref  
- Use pose control so faces don’t melt together  
- Narrator usually off; THE_VOICE may be shadow / back-turned / distorted crop

### 6.7 Continuity / “everything linked”

Maintain a **continuity ledger** the director updates as it walks:

```json
{
  "active_location_id": "old_house_exterior",
  "time_of_day": "night",
  "weather": "clear_or_light_wind",
  "on_screen": ["RIYA", "ARJUN"],
  "wardrobe_lock": {"RIYA": "yellow_dupatta_v1", "ARJUN": "grey_shirt_v1"},
  "last_shot_id": "p1_sh03",
  "mood": "uneasy"
}
```

Rules:

- Same location → same location sheet refs  
- Location change only when script/stage direction implies it  
- Wardrobe / props persist unless beat says otherwise  
- Lighting/mood can shift with emotion but palette stays in style bible  

---

## 7. Phase C — Interactive producer loop (must be strong)

Serial production is **not** one-shot generation. UX goals:

1. Play audio with stills on a timeline (scrub to shot)  
2. Click a shot → see director rationale (`visual_intent`, `trigger_reason`)  
3. **Regen one shot** (new angle / expression) without touching others  
4. Pin / lock identity sheets so regen can’t swap faces  
5. Adjust density (“more coverage on panic beat”) and re-plan **only unpinned** shots  
6. Approve part → freeze `VisualTrack` version for publish  

Maps to PRD web editor: regen-by-`seq_id` / beat; visuals should regen-by-`shot_id`.

---

## 8. Phase D — Render stills (after plan approved)

For each `VisualShot`:

1. Compile prompt from: style bible + location sheet + character slots + camera enums + `visual_intent`  
2. Attach face refs for every on-screen character  
3. Attach location ref / depth if available  
4. Optional OpenPose from `pose`  
5. Write `asset_url` back onto the shot  
6. Place marker on beat clock `[t_start, t_end]`

**Failure mode to avoid:** Beautiful but inconsistent faces → audiobook feels like random stock. Prefer fewer shots with locked identity over dense inconsistent coverage.

---

## 9. Phase E — Short video (secondary, later)

Only after still pipeline is trusted:

- Same `VisualTrack`  
- `media_kind: clip` on selected shots  
- I2V from **approved still** (Seedance / Kling / etc.) 2–5s  
- Gate with `style_bible.allow_clips` (PRD: visuals can explode cost)

---

## 10. How this differs from Pocket FM / Kuku FM

| | Pocket / Kuku app | Kissa target |
|--|-------------------|--------------|
| In-player visuals | Mostly **none** (audio) | Timed companion stills |
| Discovery art | Series thumbnails | Can reuse establish still |
| “Cinematic AI” | Often **off-app marketing** / Kuku TV separate | In-product editor track |
| What we steal | Serial hooks, short parts, cliff economy | Visibl/OIS shot timing + micro-drama identity sheets |

---

## 11. Datasets & vocab (for director language, not day-0 training)

| Resource | Use for us |
|----------|------------|
| **CineScale / CineScale2** | Shot size + angle + level **enums** (already mirrored in schema) |
| **ShotBench / ShotQA** | Few-shot examples for LLM director prompts |
| **MovieNet** | Place / scene priors (research license care) |
| **No public “Pocket FM timed stills” dataset** | We define our own `VisualTrack` corpus from our outputs over time |

We keep **our** data: bibles, sheets, tracks, approved stills, regen history — first-party serial memory.

---

## 12. Worked example — sample Hindi horror beat

Script beats (compressed):

1. NARRATOR — midnight, four friends outside old house  
2. RIYA — door already open, doesn’t want to enter  
3. ARJUN — dismissive, it’ll be fine  
4. NARRATOR — silence inside feels wrong  
5. THE_VOICE — “Riya… come upstairs…”  
6. RIYA — gasp, panic, let’s go  

**Proposed sparse `VisualTrack` (~4 stills):**

| shot | time (approx) | framing | on screen | expression / note |
|------|----------------|---------|-----------|-------------------|
| sh01 | 0–narr end | ELS exterior night | Riya+Arjun small in frame | establish house + door ajar |
| sh02 | Riya+Arjun exchange | MS / two-shot at door | Riya nervous, Arjun amused | dialogue conflict |
| sh03 | silence / voice | insert + shadow / dutch | entity suggestion, no full face | supernatural |
| sh04 | gasp → panic | CU Riya → pull to two-shot | Riya fear→panic, Arjun react | emotion roll |

Durations snap to real TTS timings when stems exist.  
SFX from cast catalog underpins (door creak, house bed, whisper echo) — separate audio lane.

---

## 13. Agent responsibilities split (clean boundaries)

| Agent / service | Owns | Does not own |
|-----------------|------|----------------|
| Script | Story, cues, bible text | Pixels |
| Narration Director | Spoken performance map | Pictures |
| Cast (voices) | `voice_id` per character | Faces |
| **Visual Director** | Shot list, camera, durations, expressions, continuity ledger | Final pixels (optional: can call renderer) |
| Identity sheet gen | Face/body/location refs | Timeline |
| Image renderer | Pixels from locked shot | Story changes |
| Editor | Human interactivity | Silent auto-publish |

---

## 14. Recommended build order (discussion baseline)

1. **Freeze contracts** — `VisualTrack` schema (done) + sample JSON for horror beat  
2. **Visual Director v0 (no GPU)** — heuristics + LLM → shot list from script + fake/real timings  
3. **API** — `POST /api/v1/visual/plan` (mirror cast)  
4. **Identity sheet generator** — 2 leads first (Riya, Arjun) + 1 location  
5. **Still renderer** — Replicate/Flux + face lock; store URLs on shots  
6. **Editor markers** — scrub audio ↔ stills  
7. **Interactive regen-by-shot_id**  
8. **Optional I2V**  

**DECISION (proposed):** Do **not** start with video models. Images must earn trust first.

---

## 15. Risks & honesty

1. **Character consistency** across 5 people + multi-shot is still hard — PRD already warns; cap on-screen cast.  
2. **Hindi visual + Hindi voice** — voice library API needs paid tier; faces are a separate provider.  
3. **Cost** — dense stills + I2V can dominate budget; density modes + human approve gate.  
4. **Over-directing** — cutting every line creates a music-video, not a serial; prefer emotion/location triggers.  
5. **Narrator visualization** — easy to make cheesy; default off-screen.

---

## 16. Open questions (discuss next)

- [ ] **OPEN:** Narrator on-screen policy (never / silhouette / full)?  
- [ ] **OPEN:** Default density for thriller vs romance?  
- [ ] **OPEN:** Image provider for MVP (Replicate Flux vs fal vs local)?  
- [ ] **OPEN:** Do we generate identity sheets automatically from traits, or human picks from a face library?  
- [ ] **OPEN:** Store sheets/tracks in Databricks UC vs Postgres Lakebase vs object storage?  
- [ ] **OPEN:** Should Visual Director run before TTS (estimated timings) or **only after** real stems (preferred for accuracy)?  
- [ ] **OPEN:** Multi-part continuity store format (bible versioning)?  

---

## 17. What we are “going ahead with” (current recommendation)

Until we change this file:

1. **Images-first companion track** on the beat clock (not in-player video product).  
2. **Bible → identity/location sheets → Visual Director shot list → human review → still render.**  
3. **Continuity ledger** so backgrounds/faces stay linked across the serial.  
4. **Interactive regen by shot**, densify only on shouts / reveals / location changes.  
5. **Video later** as optional I2V on approved stills.  
6. **Keep research + decisions in this document**; implement against `schemas/visual/track.py`.

---

## 18. Decision log

| Date | Decision | Notes |
|------|----------|-------|
| 2026-07-25 | Research file created | Sync with PRD + prior Visibl/OIS/CineScale research |
| 2026-07-25 | Schema `VisualTrack` exists in code | Enums for camera language |
| 2026-07-25 | §20 web deep-dive added | Camera Artist + CineScale/MovieNet/ShotBench/Visibl/OIS; clarify we don’t import movie pixels into product |
| 2026-07-25 | §21 storage/search/accuracy | Databricks limits, filtered ANN, multi-person horror walkthrough |
| 2026-07-25 | §22 identity-first + image providers | Postgres+files for sheets; Replicate PuLID recommended; Gemini for planning |
| | | |

---

## 19. Next discussion agenda

1. Agree narrator on-screen policy  
2. Agree density defaults for MVP demo (horror Hindi beat)  
3. Choose image provider + where sheets are stored  
4. Green-light Visual Director v0 (plan-only API) before any face generation  

*Append notes below as we discuss.*

---

## 20. Web deep-dive — where does “director knowledge” come from?
**(Camera Artist, real movie scenes, what we import vs keep ourselves)**  
*Researched 2026-07-25 via live web/arXiv/HF/GitHub sources.*

### 20.1 Why the first draft of this file felt “fast”

Honesty: that first pass was **synthesis**, not a full crawl.

- PRD §6.7 + our `VisualTrack` schema already locked the product shape  
- Prior conversation already named Visibl / OIS / CineScale / Camera Artist  
- Cast/TTS constraints were already proven in-repo  

This section is the **actual web deep-dive** on data sources and Camera Artist.

> Typo note: **“Casino artist” → Camera Artist**  
> Paper: *Camera Artist: A Multi-Agent Framework for Cinematic Language Storytelling Video Generation* (arXiv:2604.09195, 2026).

---

### 20.2 Critical distinction — three different “data” kinds

People mix these up. For Kissa they must stay separate:

| Kind | What it is | Do we “import movie scenes”? | Use for Kissa |
|------|------------|------------------------------|---------------|
| **A. Taxonomy / vocab** | Enums: CU, dutch, eye-level, two-shot… | No pixels required | **Yes — hardcode into `VisualTrack`** (already started) |
| **B. Teaching corpora** | Labeled frames/QA from real films so models learn “what a low angle looks like” | Often research-only / fair-use frames | **Optional** — few-shot prompts, eval, or LoRA for CLI; **not** shipped as product assets |
| **C. Our series assets** | Script, bible, identity sheets, location sheets, `VisualTrack`, stills we generate | **No — we create & own these** | **Primary production data** |

**We are not going to paste Scorsese frames into the audiobook.**  
We steal **how directors talk** (shot language) and optionally **train/eval** on research sets. The pictures on the timeline are **generated for our script**, locked by **our** character/location sheets.

---

### 20.3 Camera Artist — how a “director” system is built (2026)

**Source:** [arXiv HTML](https://arxiv.org/html/2604.09195) · [HF paper page](https://huggingface.co/papers/2604.09195)

**What it is:** Multi-agent filmmaking workflow for **narrative video**, not a Pocket FM player.

| Agent | Job |
|-------|-----|
| **Director Agent** | Global plan: scenes, structured assets, character/scene references |
| **Cinematography Shot Agent** | Shot-by-shot storyboard with **cinematic language** |
| **Video Generation Agent** | Multi-ref I2V (they use MAGREF + Flux refs), stitch long form |

**Two ideas we should steal for Kissa (images-first):**

1. **Recursive Shot Generation (RSG)**  
   Each next shot is conditioned on **global script + previous shots** (not independent LLM calls). That is how continuity (“same house, tighter on Riya’s fear”) survives.

2. **Cinematic Language Injection (CLI)**  
   Ordinary plot caption → film language (lens, angle, lighting, composition).  
   Camera Artist fine-tunes a small LLM (Qwen3-4B LoRA) on **~580 pairs** built from **ShotBench** annotations:  
   - VLM writes plain caption `x` (objects/actions, no cine jargon)  
   - ShotBench provides annotation `d` (shot size, angle, framing, motion, lighting)  
   - GPT-4o builds cinematic target `y`  
   - LoRA learns `x → y`  

**Eval / prompts:** MoviePrompts (plot + character profiles from professional films) + custom story outlines.  
**Refs:** Flux-generated character/scene references (or reference-free text-only mode).

**Kissa mapping:**

```text
Camera Artist Director     →  our Visual Director (plan VisualTrack)
Camera Artist Cine Shot    →  same agent’s shot enums + RSG continuity
Camera Artist Video Gen    →  later I2V; for now still renderer
ShotBench-trained CLI      →  optional later; MVP can use prompt + enums without LoRA
```

---

### 20.4 Real movie scene datasets — what exists on the web

#### A) CineScale / CineScale2 — camera grammar from real films

- Site: [cinescale.github.io](https://cinescale.github.io/)  
- **CineScale** ([Data in Brief 2021](https://doi.org/10.1016/j.dib.2021.107002)): **~792K frames**, 124 movies (full filmographies: Scorsese, Godard, Tarr, Fellini, Antonioni, Bergman), 1 fps JPEGs, human-annotated **shot scale** (ECU→ELS, insert, foreground…).  
- **CineScale2** ([Data in Brief 2023](https://doi.org/10.1016/j.dib.2023.109627)): **~25K frames** annotated for  
  - **Angle:** Overhead, High, Neutral, Low, Dutch  
  - **Level:** Aerial, Eye, Shoulder, Hip, Knee, Ground  
- Frames available **upon request for research / fair use** — not a free CDN of movie stills for commercial apps.

**Import for us:** the **class names** (already in `schemas/visual/track.py`). Optionally train a classifier later to audit our generated stills (“did we actually get a CU?”).

#### B) MovieNet — holistic movie understanding (CUHK MMLab)

- Site: [movienet.github.io](https://movienet.github.io/) · ECCV 2020 paper  
- **~1,100 movies**, trailers, photos, plots, meta  
- Annotations include: **~42K scene boundaries**, place tags (~90 classes), action tags (~80), **~1.1M character boxes/IDs**, **~92K cinematic style tags** (shot scale + camera movement)  
- Hierarchy they document: `frame → shot → scene → movie`  
- Download via OpenDataLab with license/agreement — research-oriented.

**Import for us:** scene/place **priors** and few-shot examples (“abandoned house at night → LS establish”). Not our product pixels.

#### C) ShotBench + ShotQA — teach models to speak cinematography

- Project: [vchitect.github.io/ShotBench-project](https://vchitect.github.io/ShotBench-project/)  
- GitHub: [Vchitect/ShotBench](https://github.com/Vchitect/ShotBench)  
- HF: [Vchitect/ShotBench](https://huggingface.co/datasets/Vchitect/ShotBench), ShotQA ~70k  
- Paper: [arXiv:2506.21356](https://arxiv.org/abs/2506.21356)  
- **ShotBench:** ~3.5k expert QA from **200+ acclaimed films** (many Oscar cinematography noms), **8 cine dimensions**  
- **ShotQA:** ~70k QA for training VLMs (ShotVL)  
- **Camera Artist** explicitly uses ShotBench annotations to build CLI fine-tune pairs  

**Import for us:**  
- Few-shot examples in the Visual Director system prompt  
- Optional: fine-tune / use ShotVL-like skill for “plain scene → cine language”  
- Eval: does our director pick sensible angles for fear vs comedy?

#### D) Typed “director intent” schemas (no movie pixels)

| Project | What | Link |
|---------|------|------|
| **Baton Scene Description (BSD)** | Session bible + per-tick director intent (camera, lighting, emotion, flow) ~every 3s | [digital-rain-tech/baton-scene-description](https://github.com/digital-rain-tech/baton-scene-description) |
| **FilmGraph** | Pydantic JSON: scenes → shots → cinematography + dialogue timings | [Chapter-41/filmgraph](https://github.com/Chapter-41/filmgraph) |
| **Video Notation Schema** | Structured AI video prompts (camera, lighting, characters, scenes) | [context-notation/video-notation-schema](https://github.com/context-notation/video-notation-schema) |

**Import for us:** schema ideas. Our `VisualTrack` is already in this family (closer to FilmGraph/BSD than to raw MovieNet frames).

#### E) Audiobook-timed visuals (closest product cousins)

| Project | Data / method | Link |
|---------|---------------|------|
| **Visibl** | Decomposes fiction into **~15s scenes** (camera, lighting, mood, blocking, location); RAG + graph for prompts; sync to narration; open-source pipeline | [visibl-ai/visibl-audiobooks](https://github.com/visibl-ai/visibl-audiobooks) · [visibl.ai](https://visibl.ai/) |
| **Open Illuminations (OIS)** | ZIP of images + `manifest.json` keyframes: `start` timestamp, `image`, `view` (Ken Burns crop) | [neshani/open-illuminations-standard](https://github.com/neshani/open-illuminations-standard) |

**Import for us:**  
- Visibl → **scene decomposition + sync philosophy**  
- OIS → **timeline delivery format** (maps cleanly to our `t_start`/`t_end` + `ShotView`)  

Neither gives us Pocket FM’s internal scene DB — that doesn’t exist as a public timed-stills dataset.

---

### 20.5 So where do *our* scenes come from?

```text
REAL FILMS (CineScale, MovieNet, ShotBench)
        │
        │  (optional) vocab + few-shots + CLI LoRA + eval
        ▼
DIRECTOR BRAIN (LLM + rules + RSG continuity)
        │
        │  reads OUR script + OUR timings + OUR bibles
        ▼
VisualTrack shots[]     ← this is “the scene list”
        │
        ▼
GENERATED STILLS (Flux/etc + identity/location refs)
        │
        ▼
OUR object storage / Databricks / editor timeline
```

**Scene discovery for Kissa is not “download movie scene #42.”**  
It is:

1. Parse **our** `ScriptPackage` beats + `visual_cues`  
2. Align to **our** `seq_timings` after TTS  
3. Director cuts shots on location / emotion / reveal / density budget (RSG-style)  
4. Each shot references **our** `character_id` / `location_id` sheets  

Over time, **our approved VisualTracks + stills** become the proprietary dataset (best data we can own).

---

### 20.6 License & product caution

- CineScale frames: research / fair use on request — **don’t ship in the app**  
- MovieNet: OpenDataLab terms — research use; check before any commercial training  
- ShotBench/ShotQA: check HF licenses before fine-tune + redistribute  
- Generating stills that **imitate a living actor’s likeness** → clearance / style-bible avoid list (PRD already flags this)

---

### 20.7 Practical recommendation for Kissa (updated)

| Phase | Use external movie data? | What we do |
|-------|--------------------------|------------|
| MVP director | **Enums only** (+ maybe 8–20 ShotBench-style few-shots in prompt) | Plan `VisualTrack` from script+timings |
| MVP images | **No** | Generate with our identity/location sheets |
| v1.5 quality | Optional ShotQA/ShotBench CLI LoRA (Camera Artist pattern) | Better cine language without copying frames |
| Eval | CineScale classifiers or ShotBench questions | “Is this shot actually a CU?” |
| Forever | Accumulate **our** tracks | First-party serial memory |

**Aligned with Camera Artist:** Director + recursive shot agent + (later) generation agent.  
**Different from Camera Artist:** Images-first on audiobook beat clock; video secondary; Pocket-FM economics.

---

### 20.8 Source index (for continuing research)

| Source | URL |
|--------|-----|
| Camera Artist paper | https://arxiv.org/html/2604.09195 |
| CineScale project | https://cinescale.github.io/ |
| CineScale2 DOI | https://doi.org/10.1016/j.dib.2023.109627 |
| MovieNet | https://movienet.github.io/ |
| ShotBench project | https://vchitect.github.io/ShotBench-project/ |
| ShotBench paper | https://arxiv.org/abs/2506.21356 |
| Visibl audiobooks | https://github.com/visibl-ai/visibl-audiobooks |
| Open Illuminations | https://github.com/neshani/open-illuminations-standard |
| Baton Scene Description | https://github.com/digital-rain-tech/baton-scene-description |
| FilmGraph | https://github.com/Chapter-41/filmgraph |

---

## 21. Storage, search, scale, accuracy — how retrieval works for scenes
*(Including 2–3 people arguing in a horror beat)*

### 21.1 What we store (layers — not one giant pile)

| Layer | What | Rough size | Where |
|-------|------|------------|--------|
| **A. Catalog (reusable)** | Voices, SFX prompts, shot-vocab examples, style templates | Thousands → low hundreds of thousands of rows | Unity Catalog Delta + **AI Search** index (what we use today for cast) |
| **B. Series bible** | Character identity sheets, location sheets, style bible, wardrobe locks | Tens–hundreds of objects + image blobs per series | Object storage (S3/Volume) + Postgres/Lakebase metadata |
| **C. Episode artifacts** | `NarrationPlan`, stems, `VisualTrack`, generated stills, continuity ledger | MBs–GBs audio; stills ~0.5–5 MB each × 3–20/part | `/data` or cloud object store; JSON in DB |
| **D. Optional teach set** | ShotBench-style few-shots / CLI pairs | Optional; not required for MVP | Prompt pack or separate index |

**Rule:** Vector search is for **finding candidates** (voice / sfx / “similar past horror two-shot”).  
**Exact IDs** (this series’ Riya face, this house location) are **keyed lookups**, not fuzzy search.

### 21.2 How much can we store? (Databricks reality)

**Paid / standard AI Search (platform docs):**

- ~**320M vectors** @ 768-dim per standard endpoint (scales down at higher dims)  
- Storage-optimized: ~**1B** @ 768-dim  
- Per row: **≤100 KB**; embedding source column **≤32,764 bytes**  
- Up to **50 indexes** / endpoint  

**Our Free Edition workspace (current hackathon constraint):**

- **1 AI Search endpoint**, **1 search unit**  
- Delta Sync only (no Direct Vector Access)  
- Practical: start with **thousands–tens of thousands** of catalog rows (we already proved 164 indexed; 15k voices was API-usability limited, not search limited)  
- Sync/provisioning can get slow if you dump huge tables at once — batch + triggered sync  

**Blob images/audio** are not “rows in the vector index.” Store URLs in Delta/Postgres; index only **text descriptions** (or short captions).

For Kissa MVP volumes (catalog ~10³–10⁴, series assets per title ~10²), we are **nowhere near** platform caps. Accuracy and filtering matter more than raw capacity.

### 21.3 How search works (fast path)

We already use this for cast; visuals extend it:

```text
Query text (from script beat)
    → embedding model (databricks-qwen3-embedding-0-6b)
    → ANN / hybrid search in AI Search
    → FILTER by metadata (asset_type, language, gender, genre, location_id, …)
    → top-k (usually 2–8)
    → deterministic re-rank / assign (unique voices, gender match, continuity)
```

**Why filters keep accuracy when data grows:**

| Without filters | With filters |
|-----------------|--------------|
| 50k mixed rows; “scared woman” might return male horror VO or rain SFX | `asset_type=character_voice` + `gender=female` + prefer `language=hi` → small candidate pool |

**Speed:** ANN is sub-second for catalog sizes we care about. Latency budget:

1. 1–N vector queries per beat/shot plan (**parallel**) ≈ 50–300 ms each on warm endpoint  
2. Re-rank in Python ≈ milliseconds  
3. Image **generation** is the slow part (seconds), not search  

So: **search stays fast even if catalog grows**; don’t embed every PNG pixel — embed rich text descriptions.

### 21.4 Accuracy — what “correct selection” means

Vector similarity alone is **not** enough for casting or directing. Stack:

| Stage | Job | Accuracy lever |
|-------|-----|----------------|
| 1. Query writing | Emotion + role + genre into text | Better queries → better hits |
| 2. Metadata filter | Narrow universe | Stops nonsense modalities |
| 3. Top-k retrieve | Semantic near-neighbors | Embedding quality |
| 4. Re-rank / constraints | Unique cast, gender, continuity ledger | Prevents Callum-on-everyone |
| 5. TTS / identity verify | Optional verify usable voice / pinned face | Free-tier lesson: never index unusable IDs |
| 6. Human pin | Producer locks shot / face | Interactive ground truth |

Expected realism:

- **Voice/SFX catalog search:** “good enough” top-2 with scores ~0.45–0.65 today; improves with richer descriptions + Hindi usable bank  
- **Face for a series character:** **not** “search random faces every shot” — **pin identity sheet** after one selection  
- **Shot template search** (optional): retrieve “horror two-shot argue doorway” examples → director copies camera enums, not pixels  

### 21.5 Too much data — how we still search correctly

When catalogs grow:

1. **Partition indexes or tables by type**  
   - `cast_voices_index`  
   - `sfx_index`  
   - `shot_templates_index` (optional)  
   - Never one undifferentiated soup  

2. **Always filter** before trusting rank  

3. **Series scope for bibles**  
   - `WHERE series_id = ?` for identity/location — exact SQL, not ANN  

4. **Don’t index raw frames from MovieNet/CineScale into prod**  
   - If used at all: distill to **template rows** (text + enums), tiny compared to millions of JPEGs  

5. **Cap top-k**; never “return 500 and let the LLM pick” in hot path  

6. **Hybrid search** (keyword + vector) when names matter (“Riya”, “abandoned house”)  

### 21.6 Worked example — horror, 2–3 people arguing

Script moment:

> Outside old house at night. RIYA nervous whisper — door is open. ARJUN dismissive/amused — nothing will happen. (Optional third friend silent in frame.) Mood: horror unease.

#### Step 1 — Director (not search) decides structure

```text
shot_type: two_shot (or group if 3)
location_id: old_house_exterior   ← KEYED from bible (not fuzzy)
characters_on_screen: [RIYA, ARJUN] (+ FRIEND_C if present)
expressions: RIYA=nervous_whisper, ARJUN=dismissive_amused
camera: MS, eye-level, slight high optional
duration: snap to seq_timings of their dialogue exchange (~6–12s)
```

#### Step 2 — What we search vs what we look up

| Need | Method |
|------|--------|
| Riya’s locked face | `identity_sheets[RIYA]` **exact** |
| Arjun’s locked face | `identity_sheets[ARJUN]` **exact** |
| House background | `location_sheets[old_house_exterior]` **exact** |
| Riya’s **voice** (if not cast yet) | Vector: query “young woman scared whisper Hindi horror” + `gender=female` |
| Arjun’s **voice** | Vector: “young man dismissive casual Hindi” + `gender=male` + **exclude Riya’s voice_id** |
| Door / night bed SFX | Vector: `asset_type=sfx` + “abandoned house night door ajar” |
| Optional shot template | Vector: “horror doorway two-shot argue night” in templates index |

#### Step 3 — Multi-person assignment (critical)

```text
for each speaking role in priority order (leads first):
  candidates = vector_search(role_query, filters)
  pick = first candidate whose provider_id NOT IN used_ids
       AND gender matches
       AND (optional) language preference
  used_ids.add(pick)
```

Same pattern we used when Callum was wrongly reused: **greedy unique assignment after top-k**.

For **images**, people are slots in one frame:

```json
"characters": [
  {"character_id": "RIYA", "expression": "nervous_whisper", "screen_position": "left",
   "face_ref_url": "…/riya_sheet_front.webp"},
  {"character_id": "ARJUN", "expression": "dismissive_amused", "screen_position": "right",
   "face_ref_url": "…/arjun_sheet_front.webp"}
]
```

Renderer gets **both refs** + pose layout. Search does not “find a stock photo of two people arguing”; it finds **assets that compose** the directed shot.

#### Step 4 — Emotion roll (same people, new search only for templates/SFX)

Next beat: THE_VOICE calls; Riya gasps.

- **Do not** re-search a new face for Riya  
- **Do** change expression → `gasp` / `panic` from her **expression grid** (keyed)  
- **Do** maybe search SFX: “corridor whisper echo”  
- **Do** change camera enum to ECU (director rule), optionally retrieve a “horror ECU fear” **template**

Continuity ledger keeps `active_location`, wardrobe, on_screen set.

### 21.7 End-to-end latency picture (one part)

| Stage | Typical |
|-------|---------|
| Cast recommend (4 characters × 1–2 queries) | ~1–3 s |
| SFX per scene (2–3 queries) | ~0.5–1 s |
| Visual plan (LLM + rules, no GPU) | ~2–8 s |
| Still render × 4 shots | **tens of seconds–minutes** (bottleneck) |
| Vector search itself | **not** the bottleneck |

Optimize search with caching (same query hash), parallel requests, warm endpoint. Optimize UX with plan-first, render async, regen-by-`shot_id`.

### 21.8 What we recommend storing in the vector index vs not

| Index | Yes | No |
|-------|-----|----|
| Voices | Rich description, gender, language, use_case, **TTS-verified only** | Unusable library IDs on free tier |
| SFX | Prompt + when-to-use text | Binary audio |
| Shot templates (optional) | “horror two-shot doorway argue” + enums | Full MovieNet frames |
| Identity sheets | Optional caption for “find similar look” | Must still pin by `character_id` for a series |
| Generated episode stills | Usually **don’t** index every still | Store by `shot_id`; search templates instead |

### 21.9 Bottom line

- **Capacity:** Fine for hackathon/MVP on Free Edition at thousands of catalog rows; platform can go to hundreds of millions later.  
- **Search:** Filtered ANN + re-rank; series bibles are exact keys.  
- **Accuracy:** Filters + unique assignment + pinned faces >> raw similarity.  
- **Speed:** Search is fast; generation is slow — design interactive plan/approve around that.  
- **2–3 people arguing in horror:** Director sets framing; search fills voices/SFX/templates; faces/locations come from pinned sheets; expressions change per beat without new identity search.

---

## 22. Identity-first pipeline — where to save faces, Postgres vs vectors, image providers
*(Hackathon: 30s → ~2 min correctness demo)*

### 22.1 Order of operations (what you asked for)

```text
1. Receive ScriptPackage
2. Extract characters + locations (+ style bible)
3. GENERATE IDENTITY SHEETS  ← faces + body structure FIRST
4. Human quick approve / pin sheets (optional but wise for demo)
5. Cast voices + TTS (or parallel after sheets start)
6. Visual Director → VisualTrack (timings + camera + expressions)
7. Scene stills: ALWAYS condition on pinned face/location refs
8. (Later) short clips from approved stills
```

**Never** generate story stills before faces exist. That is how identity drifts.

### 22.2 Postgres vs Vector Search — which for faces?

| Store | Use for identity? | Why |
|-------|-------------------|-----|
| **Postgres / Lakebase** | **YES — primary** | Exact rows: `character_id`, tokens, URLs, version, `locked=true` |
| **Object files** (`DATA_DIR` / Volume / S3) | **YES — image bytes** | Turnaround PNGs, expression grid |
| **AI Search / vectors** | **NO for “same face every shot”** | Fuzzy neighbors ≠ identity lock. Optional only to *propose* looks when creating a sheet |
| **Databricks Delta** | Optional mirror of catalog | Fine for voices/SFX; sheets can live in Postgres for transactional app UX |

**Recommended schema (Postgres):**

```text
series (id, title, style_bible jsonb, …)
characters (id, series_id, name, role, identity_tokens, voice_provider_id, locked bool)
character_assets (
  id, character_id,
  kind: turnaround_front | turnaround_side | full_body | expr_neutral | expr_fear | …,
  file_path / url,
  seed, model, prompt,
  created_at
)
locations (id, series_id, name, description, locked)
location_assets (id, location_id, kind: day|night|rain|…, file_path / url, …)
visual_tracks / visual_shots (plan JSON + asset urls)
```

**Today’s blocker:** `.env` `DATABASE_URL` still has `REPLACE_ME` for Lakebase password.  
Until fixed: use **local Docker Postgres** from Compose, or put sheets under `DATA_DIR/identity/{series_id}/…` + JSON sidecar — then migrate to Postgres when URL works.

**Vector search stays for:** voices, SFX, optional shot templates — **not** as the source of truth for Riya’s face.

### 22.3 Zero face/body drift — how we enforce it

1. **Generate sheet once** (or version bump `v2` only on purpose)  
2. Set `characters.locked = true`  
3. Every story still call passes **the same** `main_face_image` / refs (PuLID / InstantID / IP-Adapter)  
4. Prompt may change: expression, wardrobe layer, **background**, time-of-day, camera  
5. Prompt must **not** re-describe bone structure freely (“maybe different nose”) — identity comes from the ref image  
6. Continuity ledger: wardrobe + location_id; when **day changes**, swap **location_asset** variant (`night` → `dawn`) but keep same `character_id` refs  

Day/weather change ≠ new face. It is a **location/lighting variant**, not a new identity.

### 22.4 Hackathon time budgets (correctness over length)

| Milestone | Audio length | Visual target |
|-----------|--------------|---------------|
| **T0** | ~30s | 1–2 leads identity sheets + 1 location + **2–3 stills** |
| **T1** | ~60–90s | + expressions grid + **3–5 stills** on beat clock |
| **Demo** | **≤ 2 min** (stretch 3–5 only if T0/T1 perfect) | Sparse stills, pinned faces, working scrub in editor or simple player |

PRD already says cut visuals before VO quality. For hackathon: **nail 30s → 2 min**, don’t chase 5 min with drifting faces.

### 22.5 What to use for image generation (given your keys)

You have: **ElevenLabs** (audio/SFX — not faces), **Gemini** (great for **director text / planning**). No OpenAI.

| Option | Role | Face lock? | Cost / free | Verdict |
|--------|------|------------|-------------|---------|
| **Gemini text** (Flash/Pro) | Script → identity tokens, VisualTrack planning | N/A | Free tier often OK for text | **Use for director brain** |
| **Gemini image** (Imagen / Nano Banana family) | Stills | Native edit/ref improving, but **image routes are paid** (free tier “Not available” on pricing) | Need billing; multi-key ≠ more free quota | OK if team enables **one** billed Google project |
| **Replicate `bytedance/flux-pulid`** | Story stills + **face ref** | **Yes** (~$0.02/run) | Free trial credit common; then cheap | **Best hackathon pick for identity** |
| **Replicate InstantID** | Alternative face lock | Yes (~$0.018) | Same | Backup |
| **fal.ai / Together** | Similar Flux+ID | Yes | Credits vary | Fine alternatives |
| **ElevenLabs** | TTS + SFX only | No | Your key | Keep for audio |

**Recommendation for demo:**

1. **Gemini (text)** → character identity tokens + shot plan  
2. **Replicate Flux + PuLID** → (a) create sheet from tokens, (b) every scene still with `main_face_image=sheet`  
3. Enable **Gemini billing only if** you prefer all-Google stack — still use a **reference image** path for consistency, don’t rely on text alone  

**About 4 emails / “free quotas”:**  
Google/Replicate quotas are usually **per billing account / ToS**, not “4 emails = 4× free.” Use **one** team project with a small prepaid credit for the demo. Splitting keys is fragile and can violate provider terms.

### 22.6 Minimal demo flow (30 seconds)

```text
Script (horror beat, ~30s audio)
  → Gemini: extract RIYA, ARJUN + identity_tokens + old_house_night
  → Replicate: generate riya_front.webp, arjun_front.webp, house_night.webp
  → Save Postgres (or DATA_DIR JSON) + lock
  → Cast voices (verified bank) + TTS stems
  → VisualTrack: 3 shots (establish, two-shot argue, ECU gasp)
  → Replicate PuLID ×3 with pinned faces + location in prompt/ref
  → Play audio + flip stills on t_start/t_end
```

Success metric: **same Riya face in all 3 stills**, background can change, expressions change.

### 22.7 DECISION (proposed — confirm in discussion)

- [ ] **DECISION:** Identity sheets **before** any story stills  
- [ ] **DECISION:** Metadata in **Postgres**; image files on disk/object store; **not** vector-as-identity  
- [ ] **DECISION:** Image gen = **Replicate Flux-PuLID** for demo; Gemini text for planning  
- [ ] **DECISION:** Demo length target **≤ 2 minutes** after a perfect **~30s** slice  

---

## Appendix A — Pointers in repo

- PRD visuals: `docs/PRD.md` §6.7  
- Schema: `backend/app/schemas/visual/track.py`  
- Cast API: `backend/app/api/v1/cast.py`  
- TTS: `backend/app/api/v1/tts.py`  
- Canvas contract: Cursor canvas `visual-director-contract.canvas.tsx`
- Vector search client: `backend/app/integrations/databricks/vector_search.py`
