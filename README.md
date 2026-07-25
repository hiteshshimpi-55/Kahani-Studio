# Kissa

Audio-first storytelling production monorepo (base infrastructure only).

## Stack

| Service | Role |
|---------|------|
| `web` | Vite + React SPA (nginx) |
| `api` | FastAPI |
| `worker` | ARQ generation worker |
| `postgres` | Postgres 16 |
| `redis` | Redis 7 (job queue) |

## Run (Docker Compose only)

```bash
docker compose up --build
```

- App: http://localhost:5173
- API health: http://localhost:8000/api/health

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
web/        Vite React frontend
backend/    FastAPI + ARQ worker (same image)
docs/       PRD
```
