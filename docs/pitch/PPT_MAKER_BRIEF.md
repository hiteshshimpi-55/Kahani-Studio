# PPT BRIEF — Kahani (product-first)

Copy everything below into Claude / Gamma / Beautiful.ai / any PPT maker.

---

## ROLE

Senior presentation designer. Judge-facing hackathon deck for **Zero to One × Pocket FM**. Serious, enterprise, dark theme with Pocket FM red `#E6194D`. Exactly **8 slides**. No purple AI clichés. No overlapping text. Product name: **Kahani**.

## NARRATIVE ORDER (IMPORTANT)

Start with **what we built** and **tech stack** (including Databricks), then **problem**, then **how it works** and **agents**. Do not open with a long problem lecture.

## BRAND

- Accent `#E6194D` · BG `#0F0F12` · Cards `#18181F` · Text `#F4F4F5` · Muted `#A1A1AA`
- Footer: `Kahani · Zero to One × Pocket FM · IIM Bangalore` + `0N / 08`
- Fonts: Calibri / Inter / clean sans

---

## SLIDE 1 — Cover

Eyebrow: ZERO TO ONE · POCKET FM × OPENAI × LIGHTSPEED · IIM BANGALORE  
Title: Kahani  
Subtitle: Multi-agent production studio for serialized audio entertainment.  
Line: What we built · how the agents work · Databricks-backed context & cast retrieval.  
Chips: Theme T-04 (+ T-01/T-02) · 7 specialized agents · Listen → simulate → human publish

## SLIDE 2 — What we built

Title: An end-to-end studio — from story hook to publishable episode package  
Subtitle: Not a chat wrapper: human-gated production stages with agent orchestration.

Left — Shipped surfaces:
- Project workspace with context attachments
- Agent chat: discover, pitch, generate, approve
- LangGraph run → structured script package
- Voice + SFX mix (ElevenLabs / Sarvam)
- Companion visuals + cover art
- Web timeline editor (stems, markers, listen)
- Audience simulation (audit + personas + patches)
- Episode assembly → S3 artifact package

Right cards:
- Entry — Project + prompt + attachments
- Gates — Script → Audio → Visuals → Cover → Assembly
- Languages — Hindi + English (library voices)
- Runtime — Docker Compose · API · Worker · Redis

## SLIDE 3 — Tech stack

Title: Production stack — including Databricks for vector retrieval  

Three columns:

**Application** — React 19 · TypeScript · Vite · Tailwind · FastAPI · SQLAlchemy async · Alembic · ARQ on Redis · LangGraph + Postgres checkpointer

**AI & media** — LLM OpenAI/Anthropic · TTS ElevenLabs + Sarvam · Images OpenAI/Gemini · Research Tavily

**Data & infra** — Postgres 16 · Redis 7 · Databricks AI Search (project RAG) · Databricks Vector Search (cast catalog) · S3 · Docker · AWS/Terraform

Bottom callout — Databricks in the loop: AI Search indexes story attachments for grounded scripting. Vector Search retrieves cast/voice assets and shot templates.

## SLIDE 4 — Problem

Title: Serial audio wins on part-to-part retention. Production is still fragmented.

Six cards:
1. Idea → script is slow — regional authenticity is the moat
2. Episodes don’t chain — weak cliffhangers → drop-off
3. Audio assembly is manual — voice/SFX/visuals synced by hand
4. No pre-publish signal — teams guess cohort continuation
5. No closed loop — wins don’t improve the next story
6. Tool sprawl — briefing/writing/casting/mix/QA in five apps

## SLIDE 5 — How it works

Title: One orchestrated pipeline — agents specialize, humans gate quality cliffs  
Subtitle: Auto-run generation. Never auto-publish.

Pipeline row: Discover → Research → Script → Narrate → Voice → Visuals → Edit → Simulate

Four bands:
1. Ground — Attachments → Databricks AI Search; cast/templates → Vector Search; optional Tavily
2. Write — Storytelling + Script Writer → structured multi-part package
3. Produce — Voice TTS+SFX; Director + Image for visuals/cover
4. Assure — Editor listen; Audience Sim patches; human approvals

## SLIDE 6 — Agents (seven)

Title: Seven specialized agents — one production studio

1. **Storytelling Agent** — Series brief, plot pitches, creative direction in chat  
2. **Scripting & Search Agent** — Databricks project context + Tavily research/extraction  
3. **Narrative Agent** — Narration mode (narration-led, dialogue inserts, multi-narrator, framed)  
4. **Script Writer Agent** — Structured multi-part script package + screenplay  
5. **Director Agent** — Visual shot plan / lookbook / scene direction  
6. **Voice Agent** — Cast library voices; TTS + SFX (ElevenLabs / Sarvam)  
7. **Image Agent** — Companion stills, cover art, visual track assets  

## SLIDE 7 — Agent handoff

Title: Who does what in sequence

| Agent | Output | Detail |
|-------|--------|--------|
| Storytelling | Chat director | Pitches, series intent, route generate/rewrite |
| Scripting & Search | RAG + crawl | Databricks chunks · Tavily · SOURCE assembly |
| Narrative + Script Writer | Script package | Narration config + screenplay + cliffs |
| Voice | Audio stems | Cast (Vector Search) · TTS · SFX mix |
| Director + Image | Visual track | Shot plan · lookbook · stills · cover |
| Human + Audience Sim | Quality gate | Approve · listen · patches |

## SLIDE 8 — Close

Title: Kahani  
Line: Seven agents. One timeline. Human publish. Built for Pocket FM–scale serial production.  
Cards: Ask (pilot) · Proof (generate → listen → simulate) · Contact [fill]  
Stack highlight: LangGraph · FastAPI · React · ElevenLabs/Sarvam · Gemini/OpenAI · Tavily · Databricks AI Search & Vector Search · S3 · Docker

---

## RULES

- Exactly 8 slides. Kahani not Kissa on slides.
- Include Databricks AI Search + Vector Search on stack slide.
- List all 7 agents with the names above.
- No calibrated “Pocket FM prediction” claims.
- Screenshot placeholders optional on slide 2 if images exist.

Generate the deck now.
