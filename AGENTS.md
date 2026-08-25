# TechForge

Plataforma core (FastAPI + React/TS + SQLite) para instalação/execução de módulos. Fases 1–6 implementadas (specs em `docs/phases/`, índice em `docs/INDEX.md`). Sem lógica de negócio no Core.

## Dev environment

- Backend: Python 3.11, deps via `core/backend/requirements.txt` (venv já existe em `core/backend/.venv`).
- Frontend: Node + Vite (`core/frontend/`, deps em node_modules).
- CLI: `pip install -e cli/` (click + rich). SDK: `sdk/python/`.

## Build & test

```bash
# Backend — SEMPRE a partir de core/backend/ (DB path e imports dependem do CWD)
cd core/backend
.venv/Scripts/python.exe -m pytest tests -q          # 192 testes
.venv/Scripts/python.exe run.py                       # uvicorn em 127.0.0.1:8000

# Frontend — a partir de core/frontend/
npm run dev        # vite :5173
npm run build      # tsc -b && vite build
npm run lint       # eslint, max-warnings 0

# CLI
pip install -e cli && techforge --help
```

## Layout

- `core/backend/app/`: api/routes, core (settings/database), db, models, schemas, services, module_engine (manifest, validator, registry, loader, plugin_loader), runtime, doc_engine, package_manager.
- `core/frontend/src/`: React 18 + react-router + zustand + Tailwind + shadcn-style components (Radix).
- `modules/{repository,installed,cache}/`, `launcher/techforge_launcher/`, `cli/techforge_cli/`, `sdk/`.

## Conventions

- Extensibilidade por hooks marcados: comentários "PLUGIN LOADER HOOK" / "Phase N" indicam pontos de extensão futuros; ver seções "Pontos de Extensão" nos docs.
- Config centralizada em `app/core/settings.py` (env vars: HOST, PORT, FRONTEND_PORT, DATABASE_URL, CORS_ORIGINS) — nunca hardcodar URLs/portas.
- SQLite via SQLAlchemy async (aiosqlite); manter código específico de SQLite isolado (migração futura p/ PostgreSQL).
- Docs canônicos em português; cada fase define escopo, "o que não implementar" e critérios de aceitação + relatório final (Tests/Backend/Frontend/API/Database/Build/Known Issues).
- Não antecipar features de fases futuras (marketplace server, auth, etc.) antes da fase correspondente.

## Pitfalls

- O caminho do DB é relativo ao CWD: rodar uvicorn/pytest sempre de `core/backend/`, senão o banco falha ("unable to open database file").
- Não confiar na numeração de `docs/phases/*` como progresso — a ordem de implementação divergiu; verificar hooks vazios e testes reais antes de afirmar o que falta.
- Frontend lint falha com qualquer warning (`--max-warnings 0`).
