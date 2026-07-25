# Kahani Studio — backend

FastAPI API + ARQ worker (same Docker image, different command).

## Layout

```
app/
  api/           # routes (health, v1/…)
  services/      # business logic
  repository/    # ORM + data access (flush only; no commit)
  schemas/       # request/response DTOs
  agents/        # LangGraph + Script Writer
  workers/       # ARQ job implementations
  integrations/  # Redis, LLM, Databricks AI Search
  core/          # config, logging, DB session
worker/          # WorkerSettings entrypoint
```

## Run (Compose only)

From the **repo root**:

```bash
make run
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/api/health | Health |
| http://localhost:8000/docs | OpenAPI |

Env lives in the root `.env` (see `.env.example`). Do not commit secrets.

## Production

- Image: built from `backend/Dockerfile`, pushed to ECR
- ECS services: `api` (uvicorn) + `worker` (ARQ)
- Secrets: AWS Secrets Manager (`…/app/secrets`) — `DATABASE_URL`, `LLM_API_KEY`, `ELEVENLABS_API_KEY`
- Deploy: `.github/workflows/backend.yml` (OIDC → ECR → ECS)

## Local checks

```bash
pip install -e .
python -m compileall app worker routes
```
