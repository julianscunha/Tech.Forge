# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Regras obrigatórias deste repositório

- **Busca de código**: sempre usar skill `ast*` em vez de grep/regex textual ad-hoc — escolher a melhor pro caso: `ast-grep-outline` pra mapa estrutural barato (arquivos/imports/exports/membros antes de ler fonte completa); `ast-grep` pra busca/regra estrutural via AST (achar padrão, símbolo, chamada específica).
- **Skills de workflow**: sempre invocar a skill `using-agent-skills` antes de começar a codar (para escolher a skill de fase correta) e depois de codar (para revisão/fechamento). Obrigatório, não opcional.

## Comandos

```bash
# Backend — SEMPRE a partir de core/backend/ (DB path e imports dependem do CWD)
cd core/backend
.venv/Scripts/python.exe -m pytest tests -q          # suíte completa
.venv/Scripts/python.exe -m pytest tests/path/test_x.py::test_nome -q   # teste único
.venv/Scripts/python.exe run.py                       # uvicorn em 127.0.0.1:8000

# Frontend — a partir de core/frontend/
npm run dev        # vite :5173
npm run build      # tsc -b && vite build
npm run lint        # eslint, --max-warnings 0 (qualquer warning falha)

# CLI
pip install -e cli && techforge --help
techforge platform start|status|stop   # sobe/verifica/derruba backend+frontend via launcher
```

## Arquitetura

TechForge é uma plataforma core (FastAPI + React/TS + SQLite), local-first, extensível por módulos `.mod`. **O Core não contém lógica de negócio** — toda funcionalidade de domínio vive em módulos instalados em `modules/installed/`.

```
core/backend/app/
  api/routes/       rotas FastAPI (/api/v1/*)
  core/             settings centralizado (env vars), database
  db/               engine async + session factory + migração leve de colunas
  models/ schemas/  SQLAlchemy / pydantic (contratos de API)
  services/         serviços do Core (registry CRUD, notifications, registry_sync)
  module_engine/    manifest, validator, registry, loader, journal, navigation, plugin_loader
  package_manager/  install/remove/update/import, activate/deactivate, compatibility, operation_log
  runtime/          estado runtime da plataforma (status, eventos)
  doc_engine/       indexação, busca, contratos, completeness, AI context
core/frontend/src/  components/ pages/ store/ lib/ hooks/ contexts/
modules/{repository,installed,cache}/   pacotes .mod e módulos instalados
launcher/  cli/techforge_cli/  sdk/python/  config/  logs/
```

### Fonte única de verdade — Registry de módulos

O registry in-memory (`app/module_engine/registry.py`, singleton `registry`) é a fonte única de verdade sobre módulos em runtime.

1. `modules/installed/` — verdade física (disco)
2. `ModuleLoader.scan_installed()` → popula o registry in-memory
3. `registry` in-memory — fonte de leitura para TODAS as APIs e UI
4. `sync_registry_to_db()` espelha para a tabela `modules` apenas para contadores do Dashboard/persistência — nunca fonte primária de listagem

APIs de listagem (`/registry/modules`, `/marketplace/installed`, `/health`, navegação) leem do registry in-memory global. `PackageManager.list_installed()/list_available()` não cria registries locais paralelos. Após qualquer mutação: `scan_installed()` + `sync_registry_to_db()`.

### Module lifecycle (activate/deactivate)

Desativar = poupar recursos, não remover.

```
INSTALLED ⇄ DISABLED   (activate / deactivate)
DISABLED  → REMOVED    (remove — ação explícita)
```

Deactivate marca `<module>/data/state.json` + `is_enabled=false` no DB; o Loader não monta `entry_backend` de módulos DISABLED no boot; NavigationBuilder os exclui da navegação. Desativação não descarrega módulo já montado em runtime (requer restart — hot-unload é Fase 9).

### Module frontend contract

`entry_frontend` aponta para um módulo JS (ESM) compilado, servido via `GET /api/v1/modules/{id}/assets/{path}`:

```js
// frontend/main.js
export default {
  render(container) { /* desenha a UI dentro do container */ },
};
```

`ModuleHost.tsx` importa dinamicamente e chama `render(el)` dentro de um ErrorBoundary — falha do módulo nunca derruba o Core.

### Modos de execução

| Modo | Comando | Backend | Frontend |
|---|---|---|---|
| Desktop (default c/ build) | `techforge start` | uvicorn sem reload, `SERVE_STATIC_FRONTEND=true` | backend serve `core/frontend/dist` (SPA fallback), sem processo node |
| Dev | `techforge dev` | uvicorn com reload | vite dev server (:5173) |

O launcher escolhe o modo automaticamente: desktop se `dist/index.html` existir; `--dev` força desenvolvimento.

## Convenções

- Extensibilidade por hooks marcados: comentários "PLUGIN LOADER HOOK" / "Phase N" indicam pontos de extensão futuros.
- Config centralizada em `app/core/settings.py` (HOST, PORT, FRONTEND_PORT, DATABASE_URL, CORS_ORIGINS) — nunca hardcodar URLs/portas/caminhos.
- SQLite via SQLAlchemy async (aiosqlite); código específico de SQLite fica isolado em `app/db/` (migração futura p/ PostgreSQL).
- Docs canônicos em português; cada fase (`docs/phases/`) define escopo, "o que não implementar" e critérios de aceitação + relatório final.
- Não antecipar features de fases futuras (marketplace server, auth, etc.) antes da fase correspondente.

## Pitfalls

- O caminho do DB é relativo ao CWD: rodar uvicorn/pytest sempre de `core/backend/`, senão o banco falha ("unable to open database file").
- Não confiar na numeração de `docs/phases/*` como progresso — a ordem de implementação divergiu; verificar hooks vazios e testes reais antes de afirmar o que falta (ver `tasks/phase-audit.md`).
- Frontend lint falha com qualquer warning (`--max-warnings 0`).

## Documentação

- [`docs/INDEX.md`](docs/INDEX.md) — índice categorizado de toda a documentação
- [`docs/architecture.md`](docs/architecture.md) — arquitetura do Core
- [`docs/phases/`](docs/phases/) — specs das fases (escopo + critérios de aceitação)
- [`tasks/phase-audit.md`](tasks/phase-audit.md) — status real de implementação por fase
