# Agent guidelines (Kissa)

Read **[CLAUDE.md](CLAUDE.md)** for full project context (stack, layouts, env, do-nots).

PRD: [docs/PRD.md](docs/PRD.md)

## Quick commands

```bash
make run                 # hot-reload stack (preferred while developing)
make prod                # production-like images (rebuild on FE/BE image changes)
curl -s http://localhost:8000/api/health
make down
```

## Rules

Path-scoped Cursor rules live in [`.cursor/rules/`](.cursor/rules/).
