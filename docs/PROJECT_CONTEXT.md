# Kahani Studio - Full Project Context

**Last updated:** 2026-07-26  
**Hackathon:** Zero to One · Pocket FM × OpenAI × Lightspeed · IIM Bangalore (36 hours)  
**Repo:** hackathon monorepo (`web/` + `backend/` + `docs/`)  
**UI brand:** **Kahani Studio** · **Repo / PRD codename:** **Kissa** (किस्सा)

---

## 1. One-line pitch

Kahani is an **agentic production studio** that takes a discovery signal (regional trend, news hook, historical beat, biopic angle) and ships a **multi-part short serial audio package** — script, cliffhangers, narration/dialogue audio, SFX, companion visuals, editor-ready timeline — then **stress-tests it against simulated Pocket FM–style listeners** and proposes engagement edits **before human publish**.

---

## 2. Hackathon framing

| Item | Detail |
|------|--------|
| Event | Zero to One — generative media hackathon |
| Partners | Pocket FM, OpenAI, Lightspeed (+ Databricks / HackCulture) |
| Venue | IIM Bangalore · 25–26 July 2026 |
| Primary theme | **T-04 Creator Tools & Copilots** |
| Also covers | T-01 Generative Storytelling · T-02 Voice & Audio AI |
| Judging | Innovation · technical execution · use of AI · real-world impact · **working demo** |
| Demo bet | **Wow audio** — one undeniable listen in the web editor; agents are the *how*, not the hero |

Pitch deck: `docs/pitch/Kahani_ZeroToOne_Pitch.pptx` (8 slides) · outline: `docs/pitch/OUTLINE.md`

---

## 3. Problem

Short-form serial storytelling (Pocket FM / vernacular audio) wins on **retention between parts**, not single-episode craft. Production today is fragmented:

| Pain | Why it hurts |
|------|----------------|
| Idea → script is slow and culturally thin | Regional / vernacular authenticity is the moat; generic LLM stories sound “AI Hindi” |
| Episodes don’t chain | Weak cliffhangers → drop-off after part 1 |
| Audio + SFX + visuals sync is manual | Editors burn hours aligning timelines |
| Creators guess retention | No pre-publish signal for age / city-tier / intent cohorts |
| No closed loop | Wins on one story don’t systematically improve the next |

**Bet:** orchestrated multi-agent pipeline + synthetic audience simulator can compress **days → hours** *and* raise part-to-part continuation — **if humans stay at the right gates**.

---

## 4. Product principles (non-negotiable)

1. **Audio is the primary product.** Visuals are companion, not spine.
2. **Narration-led by default.** Dialogue is an explicit mode, not an accident in TTS.
3. **Serials > one-shots.** Default: N-part arc (3–7 MVP), 90–180s per part.
4. **Human gates at quality cliffs.** Auto-run OK; **auto-publish is not** (v1).
5. **Cultural specificity beats generic polish.** Prefer sharp regional voice over pan-India bland.
6. **Simulation informs; it does not dictate.** Creators accept/reject patches.
7. **Every asset is timeline-addressable.** Script, VO, SFX, shots share one clock.

---

## 5. Locked product decisions

| Decision | Choice |
|----------|--------|
| Surface | Audio-primary + companion visuals |
| Languages v1 | Hindi + English (one language per series; Hinglish = Hindi-mode register) |
| Editor | In-house web timeline editor |
| Voices | Library voices only — **no cloning** in v1 |
| Publish | Human approve always |
| Simulation | Structural audit + persona sims (**uncalibrated** until retention logs) |
| Runtime | **Docker Compose only** |
| Auth | **None** for now |
| Entry entity | **Project** (prompt + attachments → LangGraph → Script Writer) |

---

## 6. Production pipeline

| # | Phase | Job | Primary output |
|---|--------|-----|----------------|
| 1 | Discovery | Find / rank storyable hooks | `StoryBrief` |
| 2 | Script | Multi-part serial script | `ScriptPackage` |
| 3 | Cliffhanger optimizer | Part endings / openings | `SerialStructure` |
| 4 | Narration Director | Mode + who speaks when | `NarrationPlan` / performance map |
| 5 | Voice | TTS for narration + dialogue | `AudioStems` |
| 6 | SFX / ambience | Beds, foley | `MixStem` |
| 7 | Visuals | Keyframes / clips on beats | `VisualTrack` |
| 8 | Assembly → Editor | Editable web project | `EditorProject` |
| 9 | Audience sim + rewrite | Audit + personas → patches | `EngagementReport` + `PatchSet` |

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

Phases **5–7 parallelize** after phase 4 locks the spoken performance map. Phase 9 can run on script-only (cheap) and again on audio mix.

### Narration modes (v1)

| Mode | Shape |
|------|--------|
| `narration_only` | Single narrator (default) |
| `narration_with_dialogue` | Narrator spine + dialogue inserts |
| `dialogue_forward` | Characters carry scenes; short narrator bridges |
| `multi_narrator` | Two+ narrators in turns |
| `framed` | Outer narrator → dramatized block → narrator closes |

---

## 7. Goals & non-goals

### Goals (MVP → 90 days)

- Complete **5-part serial package** (script + VO + SFX + rough visuals + editor) from brief in **&lt; 4 hours**, ≤ 2 human review gates
- ≥ **24 cohort personas** with ranked drop-off risk per part
- **Diff-style** rewrite suggestions (not vibes)
- Full asset lineage (agent + model + prompt version)

### Non-goals (v1)

- Live interactive / choose-your-own-adventure
- Full automated legal clearance (flag only)
- Photoreal celebrity likeness without rights
- Replacing Pocket FM’s ranking algorithm
- Real-time co-writing IDE (batch + review gates first)
- Voice cloning

---

## 8. Users (JTBD)

| Persona | Job to be done |
|---------|----------------|
| Series producer | Regional hooks → serial this week |
| Writer / showrunner | Full arc draft; punch dialect & motive |
| Audio producer | Cast, emotion takes, SFX on beat map |
| Editor | Timeline with markers, stems, temp visuals |
| Growth / content ops | Which parts bleed which cohorts |

Primary buyer (hackathon): content studio building for Pocket FM–like distribution.  
End listener is **not** a Kahani user — they hear the finished serial on a consumer app.

---

## 9. Product surfaces (what exists in the app)

UI brand: **Kahani** · Pocket FM primary `#E6194D`

| Surface | Path / feature | Role |
|---------|----------------|------|
| Projects | `/` · create / list | Entry: series project |
| Project chat | `/projects/:id/chat` | Agent copilot, pipeline, approvals |
| Context / story bible | project context page | Attachments + extracted context |
| Script review | latest script / drafts | Structured package review |
| Visuals | project visuals | Companion shot / lookbook track |
| Timeline editor | `/editor` | Stems, markers, listen |
| Audience Sim | `/audience` (or feature route) | Structural audit + personas + patches |
| Library | library page | Assets / saved work |
| Discover | discover page | Discovery-oriented UI |
| System | `/system` | Health smoke |

### Frontend features (`web/src/features/`)

- `projects/` — list, detail, context, drafts, visuals, script
- `chat/` — sessions, streaming, pipeline stepper, approval panel, production cards, script result cards
- `editor/` — timeline engine, command bar, stems
- `audience/` — simulate form, audit card, engagement, persona graph, patch list
- `library/`, `discover/`, `settings/`, `system/`

**Rule:** UI never calls `fetch` ad hoc — go through `features/*/api/`.

---

## 10. Backend architecture

Layering (Synqed pattern):

```
api/ (thin routes) → services/ → repository/ | integrations/
schemas/  ·  core/ (config, db session)  ·  agents/  ·  workers/
```

| Layer | Responsibility |
|-------|----------------|
| `api/` | Routes under `/api/v1/…`; `/api/health` for probes |
| `services/` | Business logic (chat orchestrator, projects, visuals, audience…) |
| `repository/` | ORM + data access — **flush only, never commit** |
| `schemas/` | Request/response DTOs |
| `integrations/` | LLM, Gemini, Tavily, S3, TTS (ElevenLabs/Sarvam), Redis/ARQ, Databricks |
| `agents/` | LangGraph project graph + Script Writer |
| `workers/` | ARQ job implementations |

**DB rule:** one transaction per request at `get_db_session`; repos do not commit.

### LangGraph (current core path)

`retrieve_context` → `discover_research` → `build_source` → `script_writer` → persist  

- Checkpointer: Postgres  
- Cancellable runs with thread id  
- Chat orchestrator streams activity to the web client  

Related nodes also exist for visuals / discovery expansion as the full PRD pipeline is wired through chat + workers.

---

## 11. Repo layout

```
web/                  Vite + React + TS + Tailwind
backend/              FastAPI + ARQ worker (same image)
docs/                 PRD, narration, audience analytics, visuals, pitch, ElevenLabs notes
terraform/            Cloud infra (ECS, S3, secrets sync, etc.)
docker-compose.yml    web, api, worker, redis (+ data volume)
docker-compose.dev.yml hot-reload overlays
.env                  local secrets (gitignored)
.env.example          placeholders only
Makefile              make run | prod | down | logs
```

---

## 12. Runtime & commands

```bash
make run    # preferred: hot-reload FE + API + worker
make prod   # production-like images (rebuild for FE image changes)
make down
make logs
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web |
| http://localhost:8000/api/health | API health |
| http://localhost:8000/docs | OpenAPI |

After first `make run`, normal source edits hot-reload — no rebuild unless deps/Dockerfiles change.

**Compose-only** — do not prefer host `uvicorn` / `npm run dev` for day-to-day.

---

## 13. Environment (high level)

From `.env.example` (never commit real `.env`):

| Area | Keys (examples) |
|------|-----------------|
| Frontend | `VITE_API_BASE_URL` (prod build; empty in `make run` — Vite proxies `/api`) |
| Data | `DATABASE_URL`, `REDIS_URL`, `DATA_DIR` |
| Artifacts | `ARTIFACTS_BUCKET`, AWS region/creds (S3 for visuals / episode media) |
| Databricks | AI Search + cast vector search / catalog (optional; local fallback) |
| LLM | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` (stub screenplay if unset) |
| Images | `IMAGE_PROVIDER` openai \| gemini; Gemini models for director + image fallback |
| Research | `TAVILY_API_KEY` |
| TTS | `TTS_PROVIDER` sarvam \| elevenlabs; Sarvam / ElevenLabs keys (server-only) |

---

## 14. Integrations (intent)

| Integration | Use |
|-------------|-----|
| OpenAI / Anthropic | Script Writer / LLM |
| Gemini | Director text + image fallback |
| Tavily | Web research / discovery crawl |
| ElevenLabs / Sarvam | TTS (library voices; Hindi-capable via Sarvam) |
| S3 | Lookbook, shots, episode MP4 — not app disk |
| Databricks AI Search | Team/project context retrieval (optional) |
| Databricks vector search | Cast catalog |
| Redis + ARQ | Job queue for long-running generation |

---

## 15. Audience simulation (differentiator)

- **Structural audit** — pacing, cold open, cliff strength, etc.
- **Persona sims** — cohorts across age × gender × city-tier × intent (target ≥ 24)
- **Outputs** — ranked drop-off risk per part + **concrete patches** (“Shorten cold open by 8s”)
- **Honesty** — persona scores labeled **uncalibrated** until first-party listen logs exist
- **Does not** claim to replace Pocket FM ranking; informs creator decisions

Market / persona research notes: `docs/Audience_Analytics.md`

---

## 16. Conventions & do-nots

### Do

1. No auth unless explicitly requested  
2. No secrets in git — placeholders in `.env.example` only  
3. Compose-only development  
4. Repos flush; session commits  
5. Enqueue jobs from services; implement in workers  
6. API versioning under `/api/v1/…`  
7. Start from **Project** → attachments → prompt → graph run  

### Do not

- Reintroduce local Postgres container without asking  
- Add Next.js, Temporal, K8s, or voice cloning for v1  
- Claim calibrated “Pocket FM prediction”  
- Commit API keys / Databricks tokens  
- Provision AI Search indexes inside the app (pre-create in Databricks)  

Path-scoped Cursor rules: `.cursor/rules/`  
Agent entry docs: `CLAUDE.md`, `AGENTS.md`

---

## 17. Key docs map

| Doc | Contents |
|-----|----------|
| `CLAUDE.md` | Agent runtime context (stack, layout, commands) |
| `docs/PRD.md` | Full product requirements (pipeline, modes, acceptance) |
| `docs/Narration.md` | Narration Director detail |
| `docs/visual-generation-plan.md` | Visuals plan |
| `docs/Audience_Analytics.md` | Pocket FM / vernacular market & personas |
| `docs/elevenlabs/*` | TTS / SFX / stitching references |
| `docs/pitch/*` | Judge deck + outline + screenshot assets |
| `terraform/README.md` | Cloud deploy notes |

---

## 18. Demo narrative (for judges)

1. **Brief** — Create series from regional hook + context  
2. **Generate** — Discovery → script → cliff → narration  
3. **Approve** — Human gate before costly audio  
4. **Listen** — Wow-audio moment in web editor  
5. **Simulate** — Persona risk + accept one patch  
6. **Decide** — Human publish intent  

Spoken pitch flow: Cover → Problem/Insight → Solution → **live listen** → Differentiator → Close.

---

## 19. Naming cheat sheet

| Name | Where used |
|------|------------|
| **Kahani** / Kahani Studio | Product UI, pitch deck, user-facing brand |
| **Kissa** | Repo, PRD codename, some internal package names (`KissaLoader`, docker defaults) |
| **Zero to One** | Hackathon name |
| **Pocket FM** | Presenting partner / distribution analogy — we simulate listeners, we don’t ship to their CDN |

---

*This file is a consolidated context brief for humans and agents. Authoritative product detail remains in `docs/PRD.md`; runtime conventions in `CLAUDE.md`.*
