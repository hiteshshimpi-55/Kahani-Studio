# Kissa

Audio-first storytelling production monorepo (base infrastructure only).

## Stack

| Service | Role |
|---------|------|
| `web` | Vite + React SPA (nginx) |
| `api` | FastAPI |
| `worker` | ARQ generation worker |
| `redis` | Redis 7 (job queue) |

Postgres is external via `DATABASE_URL` in `.env` (e.g. Databricks). No local Postgres container.

## Frontend → backend

Browser calls `${VITE_API_BASE_URL}/api/...` (see `web/src/lib/env.ts` + `features/*/api`).

Set in root [`.env`](.env):

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Rebuild web after changing it (Vite bakes the value at build time):

```bash
docker compose up --build -d web
```

- App: http://localhost:5173  
- API: http://localhost:8000/api/health  

Smoke checks from the UI:

1. Health panel should show Postgres + Redis **ok**
2. **Enqueue ping job** — worker appends to `/data/worker_ping.txt` in the `kissa_data` volume

```bash
docker compose exec worker cat /data/worker_ping.txt
```

Stop:

```bash
docker compose down
```

## Layout

```
web/        Vite React (TCC-style feature modules)
  src/app/         App, providers, router
  src/components/  shared layout/ui
  src/features/    domain modules (api/components/hooks/pages)
  src/lib/         env, utils, query-keys
  src/pages/       thin page re-exports
backend/    FastAPI + ARQ worker (Synqed-style modules)
docs/       PRD
```
