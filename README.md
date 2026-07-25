# Kissa

Audio-first storytelling production monorepo (base infrastructure only).

## Stack

| Service | Role |
|---------|------|
| `web` | Vite + React SPA (nginx) |
| `api` | FastAPI |
| `worker` | ARQ generation worker |
| `postgres` | Postgres 16 (local Compose) |
| `redis` | Redis 7 (job queue) |

Postgres runs in Compose (`kissa` / `kissa` @ `localhost:5432`). Override with a remote `DATABASE_URL` in `.env` if needed.

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

| Path | Role |
|------|------|
| `web/` | Vite React SPA (deploy to Vercel) |
| `backend/` | FastAPI + ARQ worker (same image) |
| `terraform/` | AWS: RDS, Redis, S3, ALB, ECS api+worker |
| `.github/workflows/` | CI/CD for backend (ECR/ECS) and frontend (Vercel) |

See [terraform/README.md](terraform/README.md) for Cloudflare `api.uselamp.app` DNS and apply steps.

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
