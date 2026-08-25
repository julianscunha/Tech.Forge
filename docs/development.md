---
title: Guia de Desenvolvimento — TechForge Core
category: governanca-setup
domain: [governanca-setup]
---

# TechForge — Development Guide

> Documento exigido pela Fase 1 (docs/phases/01 §16). Guia completo do Developer
> Center em `docs/developer-center/guides/development-guide.md`.

## Requisitos

- Python 3.11 (venv em `core/backend/.venv`)
- Node.js (frontend em `core/frontend/`)

## Setup

```bash
# Backend
cd core/backend
.venv/Scripts/pip install -r requirements.txt   # ou uv pip install

# Frontend
cd core/frontend
npm install
```

## Executar em desenvolvimento

```bash
# Backend — SEMPRE a partir de core/backend/ (DB path é relativo ao CWD)
cd core/backend
.venv/Scripts/python.exe run.py          # http://127.0.0.1:8000

# Frontend — outro terminal
cd core/frontend
npm run dev                              # http://localhost:5173

# Ou tudo via launcher/CLI:
pip install -e cli && techforge platform start
```

## Testes

```bash
cd core/backend
.venv/Scripts/python.exe -m pytest tests -q        # suíte completa
.venv/Scripts/python.exe -m pytest tests/test_phase1_health.py -q   # arquivo único
```

## Build & lint do frontend

```bash
cd core/frontend
npm run build      # tsc -b && vite build
npm run lint       # eslint --max-warnings 0 (qualquer warning falha)
```

## Convenções

- Configuração somente via `app/core/settings.py` / env vars (`config/.env`) — nunca hardcode.
- Rotas novas em `app/api/routes/`, schemas em `app/schemas/`, registradas no `api_router`.
- Testes em `core/backend/tests/test_<escopo>.py`, estilo sync + `asyncio.run()` ou `TestClient`.
- Commits: mensagens descritivas no padrão existente do log (`feat: Phase N — …`, `docs: …`).
- Não antecipar features de fases futuras; hooks marcados com comentários "Phase N".
