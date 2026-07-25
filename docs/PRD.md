# Kissa — Product Requirements Document

**Version:** 0.4 (Draft)  
**Date:** 2026-07-25  
**Status:** Pre-build / architecture lock  
**Codename:** Kissa (किस्सा) — end-to-end AI storytelling production for short-form serial audio (+ companion visuals)

---

## 0a. Decisions locked (2026-07-25)

| Decision | Choice | Implication |
|----------|--------|-------------|
| Surface | **Audio-primary + companion visuals** | Stills/light motion for editor + share; audio is what people finish |
| Languages v1 | **Hindi + English** | Dual script/TTS; Hinglish = Hindi-mode register; one language per series |
| Editor | **In-house web editor** | Timeline, markers, regen-by-beat; export secondary |
| Voices | **Library voices only** | No cloning in v1; curated Hindi + English banks with emotion styles |
| Publish | **Human approve always** | Auto-run pipeline OK; G5 Publish is always a person |
| Demo strategy | **Wow audio** | One undeniable listen in the web editor; agents are the “how,” not the hero |
| Simulation v1 | **Structural audit + persona sims** | Both ship; persona scores labeled **uncalibrated** until retention data exists |
| Retention | **Build first-party listen logs** | Instrument web player (preview + test publish) so sims can calibrate over time |
| Narration | **Configurable modes via Narration Director** | Default narration-led; dialogue inserts / multi-narrator turns / framed as explicit modes before TTS |

---

## 0. One-line pitch

Kissa is an agentic production studio that takes a discovery signal (regional trend, news hook, historical beat, biopic angle) and ships a multi-part 2–3 minute serial episode package — script, cliffhangers, narration/dialogue audio, SFX bed, visuals, editor-ready timeline — then stress-tests it against simulated Pocket FM-style listeners and proposes engagement edits before human publish.

---

## 1. Problem statement

Short-form serial storytelling (Pocket FM / Audible / YouTube Shorts narrative) wins on **retention between parts**, not on single-episode craft. Today production is fragmented:

| Pain | Why it hurts |
|------|----------------|
| Idea → script is slow and culturally thin | Regional / vernacular authenticity is the moat; generic LLM stories sound “AI Hindi” |
| Episodes don’t chain | Weak cliffhangers → drop-off after part 1 |
| Audio + SFX + (optional) visual sync is manual | Editors spend hours aligning timelines |
| Creators guess what will retain | No pre-publish signal for age / city-tier / intent cohorts |
| No closed loop | Wins on one story don’t systematically improve the next |

**Kissa’s bet:** an orchestrated multi-agent pipeline + synthetic audience simulator can compress production from days to hours *and* raise part-to-part continuation — *if* humans stay in the loop at the right gates.

---

## 2. Product principles (non-negotiable)

1. **Audio is the primary product.** Visuals are a layer, not the spine. If audio fails, visuals won’t save it.
2. **Narration-led by default.** Most series are narrator-driven; dialogue is an explicit mode, not an accident in TTS.
3. **Serials > one-shots.** Default output is an N-part arc (N = 3–7 for MVP), each 90–180s.
4. **Human gates at quality cliffs.** Auto-run is allowed; auto-publish is not (v1).
5. **Cultural specificity beats generic polish.** Prefer a sharp Pune / Patna / Kochi voice over “pan-India bland.”
6. **Simulation informs; it does not dictate.** Synthetic users propose deltas; creators accept/reject.
7. **Every asset is timeline-addressable.** Script beats, narration turns, VO lines, SFX, and shots share one clock.

---

## 3. Corrected pipeline

| # | Phase | Job | Primary output |
|---|--------|-----|----------------|
| 1 | **Discovery** | Find / rank storyable hooks | `StoryBrief` |
| 2 | **Script** | Write full multi-part serial script | `ScriptPackage` |
| 3 | **Cliffhanger optimizer** | Split + tune part endings / openings | `SerialStructure` |
| 4 | **Narration director** | Choose narration mode; plan narrator turns + dialogue inserts | `NarrationPlan` |
| 5 | **Voice / performance audio** | TTS for narration + dialogue per plan | `AudioStems` |
| 6 | **SFX / ambience** | Winds, rain, crowd, foley beds | `MixStem` |
| 7 | **Visual generation** | Keyframes / clips aligned to beats | `VisualTrack` |
| 8 | **Assembly → Editor** | Mux into editable web project | `EditorProject` |
| 9 | **Audience simulation + rewrite** | Structural audit + persona sims → patches | `EngagementReport` + `PatchSet` |

Phases 5–7 parallelize after phase 4 locks the **spoken performance map** (who speaks when). Phase 9 can run on script-only (cheap) *and* again on audio mix.

```
Discovery → Script → Cliffhangers → Narration Director
                                              ↓
                                    Performance Map (locked)
                                    ↙     ↓      ↘
                                 Voice   SFX   Visuals
                                    ↘     ↓      ↙
                                      Web Editor
                                          ↓
                          Simulation → Patch → (re-enter Script / Cliff / Narration)
```

**Default content shape:** most series are **narration-led** (Pocket FM style). Dialogue is optional seasoning — not the default spine. Producers configure mode per series (and can override per part).

---

## 4. Goals & non-goals

### 4.1 Goals (MVP → 90 days)

- Produce a **complete 5-part serial package** (script + VO + SFX + rough visuals + editor project) from a discovery brief in **< 4 hours** wall-clock with ≤ 2 human review gates.
- Simulation suite covering **≥ 24 cohort personas** (age × gender × city-tier × intent) with ranked risk of drop-off per part.
- Emit **concrete, diff-style rewrite suggestions** (not vibes): “Shorten cold open by 8s”, “Move reveal from P3→P2”, “Raise antagonist threat line before fade.”
- Full asset lineage: every line/clip traceable to agent + model + prompt version.

### 4.2 Non-goals (v1)

- Live interactive / choose-your-own-adventure.
- Full automated legal clearance for news/biopic (flag only).
- Photoreal celebrity likeness without rights.
- Replacing Pocket FM’s ranking algorithm — we *simulate* listeners, we don’t ship to their CDN.
- Real-time conversational co-writing IDE (batch + review gates first).

---

## 5. Users & jobs-to-be-done

| Persona | JTBD |
|---------|------|
| **Series producer** | “Give me 5 regional hooks that can become a 5-part serial this week.” |
| **Writer / showrunner** | “Draft the full arc; I’ll punch up dialect and motive.” |
| **Audio producer** | “Cast voices, lock emotion takes, drop SFX on the beat map.” |
| **Editor** | “Open a timeline with markers, stems, and temp visuals already laid.” |
| **Growth / content ops** | “Tell me which parts will bleed 18–24 Tier-2 female romance listeners.” |

Primary buyer (hackathon framing): content studio building for Pocket FM–like distribution.  
Primary end listener: *not* a Kissa user — they hear the finished serial on a consumer app.

---

## 6. Functional requirements by phase

### 6.1 Discovery Agent

**Inputs:** region, language, genre rails (romance / thriller / biopic / historical / news-adjacent), quota, brand safety policy.

**Does:**
- Ingest signals: regional news APIs, trend scrapes (YouTube/Reddit/X where licensed), festival calendars, public-domain history corpora, existing IP catalog tags.
- Score candidates on: **storyability**, **serial potential**, **controversy risk**, **freshness**, **audience fit**, **rights risk**.
- Output top-K `StoryBrief`s with: logline, why-now, target cohorts, tone, must-avoid list, source citations.

**Acceptance:**
- ≥ 70% of producer-approved briefs proceed past Script without “wrong idea” kill.
- Every brief cites ≥ 1 primary source URL or corpus ID.
- News/biopic briefs carry `rights_risk: low|med|high` and block auto-advance on high.

**Grind:** Discovery without rights and brand-safety is a lawsuit machine. Treat “trending news → fiction” as a **transformation** pipeline (inspired-by, not recreation), not copy-paste dramatization.

---

### 6.2 Script Writing Agent

**Inputs:** approved `StoryBrief`, part count, duration target (90–180s/part), cast list (optional), dialect pack, **preferred narration mode** (or `auto`).

**Does:**
- Write full serial: cold open, scenes, **narration turns**, dialogue (when mode allows), stage directions, emotion tags, SFX cues, visual cues.
- Tag every spoken beat as `narration` | `dialogue` | `inner_monologue` so the Narration Director can reshape without rewriting the whole plot.
- Maintain character bible + continuity ledger across parts.
- Emit structured JSON + human-readable screenplay.

**Schema sketch (`ScriptPackage`):**

```json
{
  "series_id": "kissa_...",
  "narration_mode_hint": "narration_with_dialogue",
  "parts": [
    {
      "part": 1,
      "target_duration_sec": 150,
      "beats": [
        {
          "beat_id": "p1_b03",
          "t_start_hint": 42,
          "type": "dialogue",
          "speaker": "MEERA",
          "text": "...",
          "emotion": "suppressed_anger",
          "sfx_cues": ["distant_train"],
          "visual_cues": ["close_hands_clenching_ticket"]
        }
      ],
      "cliff_out": { "type": "reveal_partial", "hook": "..." }
    }
  ],
  "bible": { "characters": [], "locations": [], "timeline": [] }
}
```

**Acceptance:**
- Word budget fits TTS duration estimate ±10%.
- Continuity checker finds 0 hard contradictions (dead character speaking, location teleport).
- Dialect pack applied (glossary + few-shot) — producer scores “sounds local” ≥ 4/5 on sample set.
- Beat `type` tags present on 100% of spoken lines.

**Grind:** A “whole script” that is actually a monologue with fake dialogue will fail audio casting. Under `narration_only`, force clean narrator prose. Under dialogue modes, force **≥ 25–35% spoken dialogue** unless brief says essay/narration.

---

### 6.3 Cliffhanger Optimization Agent

**Inputs:** full arc script, retention priors, genre playbook.

**Does:**
- Propose part boundaries if not fixed.
- Score each part ending: information gap, emotional unfinishedness, threat escalation, relationship open loop.
- Rewrite last 15–25s of each part and first 10–15s of next for **handoff continuity**.
- Avoid cheap tricks that tank trust (fake death every episode).

**Outputs:** `SerialStructure` + diff against original script + predicted continuation lift per cohort.

**Acceptance:**
- Every part ends with exactly one primary open loop tagged.
- No part ends mid-sentence / mid-word (unless stylistic and flagged).
- Simulator shows ≥ X% relative lift in P(continue) vs unoptimized baseline on held-out briefs (define X after calibration — start with 8%).

**Grind:** Optimizing cliffhangers *after* a fixed script often means you’re polishing a weak arc. Better: **outline → cliff map → script**, then a light cliff polish. Put a coarse cliff agent *before* full script in v1.5.

---

### 6.4 Narration Director Agent (configurable performance mode)

**Why this exists:** Most Kissa stories are **narration-led** (Pocket FM style). Some need dialogue inserts; a few are dialogue-forward radio plays. Mixing this into raw TTS without a plan produces either endless monologue or chaotic cast stacks. This agent **chooses / applies a narration mode** and emits a spoken performance map before audio gen.

**When it runs:** After cliffhangers lock story structure; before voice TTS. Producer can set mode at series create, or accept the agent’s recommendation.

#### Narration modes (v1)

| Mode ID | Shape | When to use |
|---------|--------|-------------|
| `narration_only` | Single narrator carries 100% of spoken audio | Default for most serials |
| `narration_with_dialogue` | Narrator is spine; character dialogue inserts between narration turns | Drama / romance / thriller with key spoken moments |
| `dialogue_forward` | Characters carry scenes; short narrator bridges | Radio-play / heist / courtroom energy |
| `multi_narrator` | Two+ narrators in **turns** (POV A / POV B, or frame + inner) | Dual POV, “he said / she said,” anthology frame |
| `framed` | Outer narrator sets scene → dramatized dialogue block → narrator closes | Biopic / “true story” framing |

**Configurable knobs (per series, overridable per part):**

```json
{
  "narration_config": {
    "mode": "narration_with_dialogue",
    "narrators": [
      { "id": "NARR_A", "role": "primary", "voice_library_id": "hi_female_warm_01", "pov": "third_limited_meera" }
    ],
    "dialogue_policy": {
      "allowed": true,
      "max_dialogue_share_pct": 35,
      "min_narration_share_pct": 55,
      "insert_pattern": "narration_turn → optional_dialogue_beat(s) → narration_turn"
    },
    "turn_policy": {
      "multi_narrator_alt": "by_scene",
      "max_narration_turns_per_part": 12,
      "min_turn_duration_sec": 4
    },
    "attribution": {
      "say_speaker_names": false,
      "use_voice_contrast_instead": true
    }
  }
}
```

#### What the agent does

1. **Recommend mode** from brief + genre + cast size (or honor producer lock).
2. **Rewrite / retag beats** into an ordered `performance_sequence`:
   - `narration_turn` — one continuous narrator segment (a “term” / turn)
   - `dialogue_beat` — character line(s) nested between narration turns
   - `bridge` — 1–2 sentence narrator glue after a dialogue burst
3. For `multi_narrator`: assign turn ownership (who narrates which stretch) and handoff lines.
4. **Fix bad mixes** automatically:
   - Dialogue dumped as narrator paraphrase → split into real `dialogue_beat`s *or* fold back to narration if mode is `narration_only`
   - Orphan one-line “he said” spam → collapse into narration
   - Too many tiny turns → merge under `min_turn_duration_sec`
   - Dialogue share outside policy → trim or expand with producer-facing warning
5. Emit `NarrationPlan` consumed by Voice Audio + shown in web editor as labeled lanes.

**Output sketch (`NarrationPlan`):**

```json
{
  "series_id": "kissa_...",
  "mode": "narration_with_dialogue",
  "parts": [
    {
      "part": 1,
      "sequence": [
        {
          "seq_id": "p1_s01",
          "kind": "narration_turn",
          "narrator_id": "NARR_A",
          "text": "Meera clutched the ticket until the edges went soft.",
          "emotion": "tense_quiet",
          "source_beats": ["p1_b01", "p1_b02"]
        },
        {
          "seq_id": "p1_s02",
          "kind": "dialogue_beat",
          "speaker": "RAHUL",
          "text": "You're not getting on that train.",
          "emotion": "cold",
          "source_beats": ["p1_b03"]
        },
        {
          "seq_id": "p1_s03",
          "kind": "narration_turn",
          "narrator_id": "NARR_A",
          "text": "She didn't look up. The platform loudspeaker crackled her name.",
          "emotion": "resolute",
          "source_beats": ["p1_b04"]
        }
      ],
      "metrics": {
        "narration_share_pct": 72,
        "dialogue_share_pct": 28,
        "narration_turn_count": 8
      }
    }
  ]
}
```

**Producer UX:**
- Mode picker at series create + again before audio gen (with live share % preview).
- “Fix narration mix” button → re-run director without full script rewrite.
- Diff view: script beats ↔ performance sequence.

**Acceptance:**
- 100% of spoken audio maps to a `seq_id` in `NarrationPlan`.
- Mode constraints enforced (e.g. `narration_only` ⇒ zero dialogue stems).
- Multi-narrator handoffs never overlap; each turn has exactly one `narrator_id`.
- Human can override mode and regenerate plan in &lt; 2 minutes.

**Grind:** Don’t let “multi-narrator” become gimmick switching every sentence — enforce min turn length. Don’t TTS dialogue attribution (“Rahul said”) when voice contrast already IDs the speaker.

---

### 6.5 Voice / performance audio

**Inputs:** locked `NarrationPlan`, library voice map, language/TTS engine map.

**Does:**
- Cast library voices to each `narrator_id` + dialogue `speaker`.
- Generate audio **in sequence order** (narration turns and dialogue beats interleaved as planned).
- Multi-take generation; pick or blend takes.
- Align to beat/sequence timestamps; export stems + rough VO mix.
- Stem layout: `VO_narr_{id}`, `VO_cast_{speaker}`, roomtone.

**Tech notes:**
- Prefer phoneme/viseme timestamps for later lip-sync if visuals need mouths.
- Emotion: SSML / style tokens / reference-audio conditioning depending on vendor.
- Loudness: target podcast LUFS (−16 or platform spec).
- Respect `attribution.say_speaker_names` from narration config.

**Acceptance:**
- WER / listening QA sample: critical mispronunciations of names &lt; 1 per part after glossary pass.
- Timing drift vs performance map &lt; 300ms average after aligner.
- No dialogue stems when mode is `narration_only`.

**Grind:** Vendor TTS “emotions” are shallow. Budget for **performance direction** that rewrites delivery tags and regenerates weak lines — not one-shot TTS. Regenerate by `seq_id`, not whole part.

---

### 6.6 Sound & FX

**Inputs:** SFX cue list from script + duration map.

**Does:**
- Retrieve or generate ambiences/foley; duck under VO; respect perspective (interior/exterior).
- Build beds + spot FX; export `MixStem` + markers.

**Acceptance:**
- No SFX masking dialogue (sidechain / ducking rules).
- Cue hit within ±200ms of beat marker.
- License metadata on every sample (CC0 / purchased / generated).

**Grind:** Generated SFX often sound “game-y.” Prefer a **licensed library + generative fill** hybrid. Pure gen-SFX will date your product fast.

---

### 6.7 Visual generation (companion — not video-first)

**Product role:** Still images / light motion locked to the beat clock so the **web editor** and share artifacts have a picture plane. Audio remains the product people finish.

**Inputs:** visual cues, style bible, aspect ratio (9:16 / 1:1 / 16:9).

**Does:**
- Generate stills (default) or short clips per beat; maintain character consistency (IP-Adapter / character ref / LoRA).
- Light motion (Ken Burns / short I2V) only where it helps editor preview — not a full animated episode.

**Acceptance:**
- Character identity consistency score above threshold across parts (human or embedding).
- No disallowed likeness / logo / trademark without clearance flag.
- Timeline markers match audio beats.

**Grind:** Cap visual spend (e.g. ≤ N keyframes/part). If GPU budget fights VO quality, **cut visuals first**.

---

### 6.8 Assembly → Web Editor

**Inputs:** all stems + visuals + markers.

**Does:**
- Open series in **in-house web editor** (primary): multi-track timeline (VO / cast / SFX / visuals), chapter markers, script sidebar synced to playhead, version stack, regen-by-beat.
- Optional secondary export (OTIO / FFmpeg package) later — not MVP-critical.

**Acceptance:**
- Producer can play full part mix, scrub to beat, replace one VO take / one shot without re-running the whole pipeline.
- Markers from beat clock survive refresh / version bump.

---

### 6.9 Audience simulation & engagement rewrite

**v1 ships two layers (both required):**

| Layer | What it is | Honesty label in UI |
|-------|------------|---------------------|
| **A. Structural audit** | Deterministic + rubric checks (hook ≤8s, open loop, dialogue ratio, cliff diversity, cold-open clarity) | “Craft checklist” |
| **B. Persona simulation** | Synthetic listeners across age × gender × city-tier × intent run part-level drop/continue judgments | “Uncalibrated cohort model” until retention volume is enough |

**Inputs:** script and/or audio; cohort graph; retention priors (empty at first, then filled from first-party logs).

**Does:**
1. Run structural audit → hard fails + soft warnings.
2. Instantiate N synthetic listeners (personas) and run **part-level listen simulation**: attention decay, skip impulse, P(continue), share impulse, drop reasons.
3. Aggregate to `EngagementReport`: funnel per part, fragile beats, cohort disagreements.
4. Propose `PatchSet`: structured edits with expected metric deltas + confidence (`low` until calibrated).
5. Queue all patches for human accept/reject (no auto-apply on publish path).

**Persona dimensions (MVP):**
- Age band: 16–20, 21–24, 25–34, 35–44
- Gender: as relevant to catalog (prior, not stereotype destiny)
- City tier: Tier-1 / Tier-2 / Tier-3
- Intent: romance escape, thriller binge, “true story” curiosity, commute pass-time, share-with-friends
- Language comfort: Hindi / Hinglish / English

**Acceptance:**
- Every finding maps to `beat_id` + patch type.
- UI never says “will perform on Pocket FM” until calibration gates pass.
- Once retention logs exist: Spearman ρ ≥ 0.3 between sim rank-order and real continuation; raise over time.

---

### 6.10 Retention logging (first-party flywheel)

**Why:** Persona sims without real listen data stay uncalibrated. You chose to **build the logs**, not wait for a Pocket FM partnership.

**Where logs come from (v1):**
1. **Editor preview player** — producers / reviewers listening while QA’ing.
2. **Test publish links** — shareable listen URLs (password or expiring) for panel / friends / soft launch.
3. Later: any consumer surface Kissa owns.

**Events to capture (minimum):**

```json
{
  "listen_id": "...",
  "series_id": "...",
  "part": 1,
  "listener": { "anon_id": "...", "cohort_tags": ["optional"] },
  "events": [
    { "t": 0, "type": "play" },
    { "t": 42.1, "type": "pause" },
    { "t": 42.1, "type": "seek", "to": 10 },
    { "t": 148.0, "type": "complete" },
    { "t": 148.5, "type": "next_part", "to_part": 2 },
    { "t": 30.0, "type": "drop" }
  ],
  "derived": {
    "pct_complete": 0.99,
    "continued_next": true,
    "max_position_sec": 148.0
  }
}
```

**Derived metrics per part:** start rate, median % complete, drop-off curve (deciles), P(next part | complete), replay rate.

**Privacy:** anon IDs by default; no PII required for calibration; cohort tags only if listener opts in on test links.

**Calibration loop:**
1. Collect N listens per part (target: dozens → hundreds).
2. Fit / refresh persona priors so sim P(continue) tracks observed continuation.
3. Flip UI badge from **Uncalibrated** → **Calibrated (n=…, updated …)** when thresholds met.

**Grind:** Early logs will be biased (producers + friends). Still useful for relative ranking; don’t overclaim absolute Pocket FM numbers.
---

## 7. Cross-cutting requirements

### 7.1 Orchestration

- Workflow engine (Temporal / Inngest / custom DAG) with retries, idempotency, human approval tasks.
- Artifact store (S3/GCS) + metadata DB (Postgres).
- Event log for every agent I/O (replayable).

### 7.2 Evaluation & QA gates

| Gate | When | Fail condition |
|------|------|----------------|
| G0 Brief | After Discovery | rights_risk=high, brand safety fail |
| G1 Bible | After outline/cliff map | incoherent arc |
| G2 Script | After Script+Cliff | continuity fail, duration fail |
| G2b Narration | After Narration Director | mode constraints broken / share % out of policy |
| G3 Audio | After VO+SFX | loudness / WER / ducking fail |
| G4 Sim | After Sim | critical drop predicted on P1 cold open |
| G5 Publish | **Always human** | Taste / legal — no auto-ship in v1 |

### 7.3 Safety, rights, brand

- PII scrub on news sources.
- Biopic: living persons → fictionalization mode + disclaimer template.
- Child safety: block sexual/violent content involving minors.
- Prompt injection from scraped news text: treat sources as untrusted data.

### 7.4 Localization

- v1 languages: **Hindi** (incl. Hinglish register) + **English**.
- Each series picks a primary language; bilingual series are out of scope for v1 (pick one).
- Dialect packs (Hindi) + tone packs (English) as versioned JSON + few-shot corpora, not one mega-prompt.
- Architecture ready later for Tamil/Telugu/Bengali.

### 7.5 Observability

- Cost per series (tokens, TTS chars, GPU-seconds).
- Latency per phase.
- Human edit distance (how much producers rewrite) — **north-star quality proxy**.
- **Listen retention** — play, complete, next-part, drop curves from web player (§6.10).

---

## 8. Technical architecture

### 8.1 High-level

```
┌────────────┐   ┌─────────────┐   ┌──────────────────┐
│  Web App   │──▶│  API / BFF  │──▶│  Orchestrator    │
│  (Vite)    │   │  (FastAPI)  │   │  (ARQ workers)  │
└────────────┘   └─────────────┘   └────────┬─────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              ▼                             ▼                             ▼
       ┌────────────┐              ┌────────────┐               ┌────────────────┐
       │ Agent      │              │ Media      │               │ Simulation     │
       │ Workers    │              │ Workers    │               │ Workers        │
       │ (LLM)      │              │ (TTS/SFX/  │               │ (cohort sims)  │
       │            │              │  Vision)   │               │                │
       └─────┬──────┘              └─────┬──────┘               └───────┬────────┘
             │                           │                              │
             └───────────────────────────┼──────────────────────────────┘
                                         ▼
                              ┌────────────────────┐
                              │ Postgres + Object  │
                              │ Store + Vector DB  │
                              └────────────────────┘
```

### 8.2 Locked stack (Compose-only monorepo)

| Layer | Choice | Why |
|-------|--------|-----|
| Run | **Docker Compose only** | `web`, `api`, `worker`, `postgres`, `redis` |
| Frontend | **Vite + React + TypeScript + Tailwind** | SPA producer UI + future audio/frame editor |
| API | **FastAPI + Pydantic v2** | Agents/media-friendly Python surface |
| Workers | **ARQ + Redis** (same backend image) | Generation queue; scale `worker` |
| DB | **Postgres 16 + JSONB** | Series/artifacts/approvals/retention |
| Files | Compose volume `/data` | Stems, mixes, frames (no S3 day-0) |
| Auth | **None (for now)** | Approve gates later via UI |
| LLM / TTS / align | LiteLLM + ElevenLabs + WhisperX + FFmpeg *(not wired yet)* | Wow-audio path after base setup |

Repo: `web/`, `backend/` (API + worker), `docs/`. See root `README.md`.

### 8.3 Agent design pattern

Each agent is a **typed contract**, not a vibes prompt:

```
AgentSpec {
  name, version
  input_schema, output_schema
  tools[]          // search, retrieve dialect, continuity check
  model_policy     // which model, temp, max tokens
  evaluators[]     // auto checks before emit
  human_gate?      // optional approval
}
```

Shared services:
- **Continuity service** — entity graph over series
- **Duration estimator** — text → sec given voice rate
- **Beat clock** — single source of truth for t=0…T
- **Prompt/registry** — versioned prompts; never edit prod prompts in place
- **Media aligner** — forced alignment (WhisperX / Montreal Forced Aligner)

### 8.4 Simulation engine (technical)

**v1 — Structural audit + persona sims (both ship):**

*Structural:*
- Deterministic heuristics: hook within 8s, open loop at end, dialogue ratio, name density, cold-open clarity, cliff type diversity.
- Lightweight LLM judge with **rubric**, multiple samples, disagreement flagged.

*Personas:*
- Cohort agents score each part → P(complete), P(next), drop_reason, fragile_beat_ids.
- Multi-sample + show disagreement; confidence = `low` until calibrated.
- UI copy: “Uncalibrated cohort estimate — improving as listen logs grow.”

**Retention → calibration path (built in parallel):**
- Ingest `listen_events` from editor preview + test publish (§6.10).
- Nightly/on-demand job: update persona priors / isotonic calibration so sim ranks track observed continuation.
- Gate: badge flips to Calibrated only when n and ρ thresholds pass.

**v2 — Fully calibrated cohort model:**
- Features from script/audio → P(listen_to_end), P(next_part) per persona with uncertainty bands.
- Primary training signal = first-party retention; optional partner logs later.

**v3 — Generative beat-by-beat listeners (optional):**
- Only after v2 is stable; otherwise theater.

Patch language (example):

```json
{
  "patches": [
    {
      "id": "pt_014",
      "target": "p2_b11",
      "op": "rewrite_line",
      "rationale": "Tier-2 F 21-24 romance: motivation unclear → drop risk",
      "expected": { "metric": "P_continue_p2_p3", "delta": "+0.04", "confidence": "low" },
      "diff": { "before": "...", "after": "..." }
    }
  ]
}
```

### 8.5 Data model (core tables)

- `series`, `parts`, `beats`
- `artifacts` (uri, type, parent_id, agent_version)
- `approvals` (gate, user, decision) — G5 always required
- `voice_library` (no clone assets in v1)
- `sim_runs`, `sim_cohort_results`
- `patches`, `patch_applications`
- `narration_plans`, `narration_configs`
- `listen_sessions`, `listen_events`, `retention_aggregates`
- `calibration_snapshots` (model version, n, ρ, calibrated_at)
- `style_bibles`, `cost_events`

### 8.6 Cost model (order-of-magnitude — validate!)

Assume 5 parts × 150s, Hindi, 2 cast voices + narrator:

| Item | Rough cost/series |
|------|-------------------|
| LLM script+cliff+sim | $1–8 |
| TTS | $3–25 (vendor dependent) |
| SFX licensing amortized | $0–5 |
| Visuals (optional, 20 keyframes + light I2V) | $5–80 |
| GPU align/ffmpeg | low |
| **Total** | **~$10–120** |

At $50 average, you need clear willingness-to-pay from studios or take-rate on catalog. **Visual-heavy mode can 5× cost** — gate it.

### 8.7 Latency budget

| Phase | Target p50 |
|-------|------------|
| Discovery | 2–5 min |
| Script + cliff | 8–20 min |
| Audio | 15–40 min |
| SFX | 5–15 min |
| Visuals (optional) | 20–90 min |
| Sim (structural + personas) | 5–12 min |
| Assembly | 3–8 min |

Parallelize audio/SFX/visuals off locked beat map.

---

## 9. UX outline (producer)

1. **New series** — region, language, genre, constraints.
2. **Discovery board** — cards with scores; approve one.
3. **Arc view** — outline + cliff map; drag part boundaries.
4. **Script review** — screenplay + beat inspector; inline comments.
5. **Narration mode** — pick mode; preview turn/dialogue mix; “Fix narration mix.”
6. **Cast & generate audio** — library voice picker; regenerate by `seq_id`.
7. **Mix** — simple ducking preview.
8. **Visuals** (toggle) — style lock; reject/regen shot.
9. **Simulator** — structural checklist + persona heatmap; patch tray; **Uncalibrated** badge.
10. **Test publish** — share listen link; retention events flow back.
11. **Versions** — compare audits + observed retention when available.

---

## 10. Success metrics

### Product
- Time-to-first-export (median)
- Human edit distance (lower over time *without* quality drop)
- % series completing all gates first pass
- Producer NPS / “would ship this”

### Quality proxies
- Continuity fail rate
- Dialect rating (blind human panel)
- Cliff diversity (not same trick every part)

### Simulation honesty
- Calibration slope / rank correlation when real outcomes exist
- % of accepted patches that improve subsequent human scores

### Business
- Cost per publishable minute
- Series/week per producer

---

## 11. MVP scope (hackathon-realistic)

**Must:**
- Discovery (mock + 1–2 live sources) → StoryBrief
- Script agent for 3-part × ~2 min — **Hindi or English** (demo one language end-to-end; both wired)
- Cliff polish on endings
- **Narration Director** with mode picker (`narration_only` + `narration_with_dialogue` minimum; others if time)
- TTS narration + optional dialogue voices per plan
- Basic SFX bed from library
- Companion stills (≤ 3–5/part), not heavy video
- **Web editor** skeleton: play mix, scrub, beat markers, regen one line
- Structural engagement audit **+** persona simulation + sample patches
- Web player emits listen events (even if calibration UI is stubbed)
- Approve/reject gates; **G5 always human**
- Library voices only (Hindi + English banks)

**Skip for hackathon:**
- Full Temporal (use a linear job runner)
- Calibrated ML claims without enough listen n
- Voice cloning
- Heavy I2V / full visual episodes
- Regional languages beyond Hindi/English
- Real Pocket FM API integration
- CapCut/Premiere export
- Auto-publish

**Demo story:** one locked thriller (Hindi *or* English) that **sounds** undeniable in the web editor — wow audio wins the room.

---

## 12. Roadmap

| Phase | Time | Focus |
|-------|------|--------|
| M0 | Hackathon | Vertical slice: brief → script → audio → audit → export |
| M1 | +4 weeks | Continuity service, dialect packs, human gates UX |
| M2 | +8 weeks | SFX smart ducking, OTIO export, cost dashboards |
| M3 | +12 weeks | Calibrated sim v2, optional visuals track |
| M4 | +16 weeks | Multi-language, partner retention feedback loop |

---

## 13. Risks & open questions (the grind)

### Product risks
1. **Wrong primary surface.** If Pocket FM users mostly *listen*, shipping a “visual platform” is a distraction. Decide: audio studio with optional visual companion, or video-native TikTok serials? These are different companies.
2. **Agent theater.** Eight agents that all call the same LLM with different system prompts is not a platform — it’s a folder of prompts. Without schemas, evals, and gates, quality won’t compound.
3. **Cliffhanger addiction.** Maximizing continuation can destroy word-of-mouth (“manipulative”). Track trust/regret, not only P(next).
4. **Discovery legality.** News and biopic are the juiciest and the most radioactive. What’s your fictionalization policy?
5. **Who is the customer?** Studio tool (seat license) vs API for platforms vs consumer app? Pricing and UX diverge hard.

### Technical risks
6. **Beat clock drift** between script estimate, TTS reality, and visuals — will haunt you. Invest in forced alignment early.
7. **Character consistency** in visuals across 5 parts is still unsolved-ish; don’t promise it.
8. **Simulation validity.** Without labels, you’re optimizing for the judge model’s taste. Say so in the UI.
9. **Cost blowups** on regen loops (“fix emotion on line 40” × 50). Cap regenerations; batch critiques.
10. **Orchestration complexity** — don’t build Kubernetes-for-stories before one linear pipeline works.

### Content risks
11. **Dialect authenticity** — urban LLM Hindi ≠ Bhojpuri / Haryanvi / Hyderabadi. Hire native reviewers or you ship parody.
12. **Gender/city stereotypes in personas** — encoding Tier-2 women as “only romance” is both unethical and bad modeling. Use intents and catalog affinities, not caricatures.
13. **SFX uncanny valley** — bad rain under good VO makes the whole episode feel cheap.

### Decisions closed (this round)

| # | Answer |
|---|--------|
| Narration modes | **Configurable** via Narration Director (default narration-led) |
| Narration modes | **Configurable** via Narration Director (default narration-led) |
| Retention logs | **Yes — build first-party** via editor preview + test publish (§6.10) |
| Demo | **Wow audio** |
| Publish | **Always human** |
| Voices | **Library only** |
| Sim v1 | **Structural audit + persona simulation** (uncalibrated badge until logs calibrate) |

### Still open (non-blocking)
1. Demo language for the hero serial: Hindi or English?
2. How many personas in the hackathon heatmap (e.g. 8 vs 24)?
3. Test-publish: public link, password, or invite-only?

---

## 14. Recommendations (my takes)

1. **9-stage DAG** — Narration Director sits between cliffhangers and TTS.
2. **Wow audio** is the demo north star — protect mix quality over agent slides.
3. **Default `narration_only` / narration-led**; dialogue is a mode, not an accident.
4. **Sim v1 = audit + personas**, always show **Uncalibrated** until retention n/ρ gates pass.
5. **Instrument the player on day one** — logs are the path to real prediction.
6. **Library voices** — casting UX + emotion takes, not cloning.
7. **G5 always human** — no auto-ship.
8. **Companion visuals budget-capped**; web editor scrub + regen-by-`seq_id` early.
9. **One language end-to-end** for the live demo.

---

## 15. Appendix — glossary

| Term | Meaning |
|------|---------|
| Beat | Smallest timed unit of story/audio intent |
| Cliff out / cliff in | Ending hook of part N / opening re-hook of N+1 |
| Stem | Isolated audio track |
| Cohort | Persona slice for simulation |
| PatchSet | Structured proposed edits from sim |
| Beat clock | Shared timeline for all modalities |
| Narration turn | Continuous narrator segment (“term”) in the performance sequence |
| NarrationPlan | Mode + ordered narration/dialogue sequence before TTS |
| Gate | Human or auto quality checkpoint |
| Retention log | First-party play/complete/next/drop events from the web player |
| Calibration | Adjusting persona sims so scores match observed retention |

---

## Document history

| Ver | Date | Notes |
|-----|------|-------|
| 0.1 | 2026-07-25 | Initial PRD + architecture + grind |
| 0.2 | 2026-07-25 | Locked: audio+companion visuals, HI+EN, web editor; clarified sim + demo questions |
| 0.3 | 2026-07-25 | Locked: wow audio, library voices, always-human publish, structural+persona sim, first-party retention logs |
| 0.4 | 2026-07-25 | Added Narration Director: configurable modes, multi-turn narration, dialogue inserts |
