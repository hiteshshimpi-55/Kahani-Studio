# Kissa — agent context

Audio-first AI storytelling / production studio (hackathon monorepo).
PRD: [docs/PRD.md](docs/PRD.md)

## Product snapshot

Pipeline (high level): Discovery → Script → Cliffhangers → **Narration Director** → Voice → SFX → Visuals (companion) → Web editor → Structural audit + persona sim → human publish.

Locked decisions:

- Audio-primary + companion visuals; **wow audio** demo bet
- Languages v1: Hindi + English (one language per series)
- Narration modes configurable (`narration_only` default)
- Library voices only (no cloning); **no auth** for now
- Sim v1: structural audit + personas (uncalibrated until retention logs)
- Run **only via Docker Compose**
- Entry entity: **Project** (prompt + attachments → LangGraph → Script Writer)

## Repo layout

```
web/                 Vite + React + TS + Tailwind (TCC-style feature modules)
backend/             FastAPI + ARQ worker (Synqed-style modules, same image)
docs/PRD.md
docker-compose.yml   web, api, worker, redis (+ kissa_data volume)
.env                 local secrets (gitignored) — copy from .env.example
```

### Backend (`backend/app/`)

Layering (Synqed pattern):

- `api/` — thin routes (`health`, `v1/…`); `dependencies/`, `error_handlers`
- `services/` — business logic
- `repository/` — ORM models + data access (**no `commit`** in repos)
- `schemas/` — request/response DTOs
- `core/` — `config`, `logging`, `db/session` (request boundary commits)
- `integrations/` — Redis/ARQ, Databricks AI Search, later TTS/LLM
- `middleware/`, `errors/`, `agents/` (LangGraph + Script Writer), `domain/`
- `workers/` — ARQ job implementations; `worker/` — `WorkerSettings` entry

Routes → services → repository/integrations. Do not put business logic in route handlers.

### Frontend (`web/src/`)

TCC-style + Pocket FM primary `#E6194D`:

- `app/` — `App.tsx`, `providers.tsx`, `router.tsx`
- `features/projects/` — list, detail (prompt + Context attachments), script review
- `features/system/` — health smoke at `/system`
- `components/` — `layout/AppShell`, `ui/` (Button, Input, Textarea, Dialog, Badge)
- `lib/` — `env.ts`, `api-client.ts`, `utils.ts` (`cn`), `query-keys.ts`
- `pages/` — thin re-exports only

UI never calls `fetch` ad hoc in components — go through `features/*/api/`.

## Runtime

```bash
docker compose up --build
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web (Projects home) |
| http://localhost:8000/api/health | API |
| http://localhost:8000/docs | OpenAPI |

Env (root `.env`):

- `VITE_API_BASE_URL` — browser-facing API origin (baked into web **build**)
- `DATABASE_URL` — external Postgres (`postgresql+asyncpg://…?ssl=require`); no local Postgres container
- `REDIS_URL`, `DATA_DIR`
- `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_AI_SEARCH_ENDPOINT`, `DATABRICKS_AI_SEARCH_INDEX` — AI Search Direct Access (optional; local chunk fallback if unset)
- `LLM_PROVIDER` (`openai` | `anthropic`), `LLM_API_KEY`, `LLM_MODEL` — Script Writer (stub if key unset; default provider `openai` / `gpt-4o`)

After changing `VITE_API_BASE_URL`, rebuild web: `docker compose up --build -d web`.

## Conventions

1. **No auth** — do not add Clerk/JWT/login unless explicitly requested.
2. **No secrets in git** — never commit `.env`; use `.env.example` placeholders only.
3. **Compose-only** — prefer documenting `docker compose` over host `uvicorn`/`npm run dev` as the happy path.
4. **DB commits** — one transaction per request at `get_db_session`; repos flush only.
5. **Jobs** — enqueue via ARQ from services; workers live in `backend/worker` + `app/workers`.
6. **API versioning** — product routes under `/api/v1/…`; health at `/api/health`.
7. **Projects first** — generation starts from Project → attachments → prompt → LangGraph run.

## Do not

- Reintroduce local Postgres container without asking
- Add Next.js, Temporal, K8s, or voice cloning for v1
- Claim calibrated “Pocket FM prediction” — sim is uncalibrated until retention logs exist
- Commit Databricks tokens / API keys
- Provision AI Search endpoints/indexes inside the app (pre-create in Databricks)

## Cursor rules

See [`.cursor/rules/`](.cursor/rules/) for always-on and path-scoped guidance.
