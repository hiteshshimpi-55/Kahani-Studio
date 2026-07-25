# Agent guidelines (Kissa)

Read **[CLAUDE.md](CLAUDE.md)** for full project context (stack, layouts, env, do-nots).

PRD: [docs/PRD.md](docs/PRD.md)

## Quick commands

```bash
docker compose up --build
curl -s http://localhost:8000/api/health
docker compose up --build -d web   # after changing VITE_API_BASE_URL
```

## Rules

Path-scoped Cursor rules live in [`.cursor/rules/`](.cursor/rules/).
