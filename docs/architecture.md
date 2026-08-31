---
title: Arquitetura — TechForge Core
category: governanca-setup
domain: [governanca-setup]
---

# TechForge — Architecture

> Documento de arquitetura viva do Core. Conteúdo detalhado por domínio
> vive em `docs/INDEX.md` e `docs/developer-center/`.

## Visão geral

TechForge é uma plataforma core (FastAPI + React/TS + SQLite) executada localmente,
extensível por módulos. O Core não contém lógica de negócio — toda funcionalidade
de domínio vive em módulos instalados em `modules/installed/`.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 async (aiosqlite), pydantic-settings |
| Frontend | React 18, TypeScript, Vite, Tailwind, Radix (shadcn-style), zustand |
| Banco | SQLite (isolado em `app/db/` — migração futura p/ PostgreSQL sem espalhar dependências) |
| Distribuição | launcher desktop, CLI (`cli/techforge_cli`), SDK Python |

## Estrutura

```text
core/backend/app/
  api/routes/     rotas FastAPI (/api/v1/*)
  core/           settings centralizado (env vars), database
  db/             engine async + session factory + migração leve de colunas
  models/         modelos SQLAlchemy
  schemas/        schemas pydantic (contratos de API)
  services/       serviços do Core (registry CRUD, notifications, registry_sync)
  module_engine/  manifest, validator, registry, loader, journal, navigation, plugin_loader
  package_manager/ install/remove/update/import, activate/deactivate, compatibility, operation_log
  runtime/        estado runtime da plataforma (status, eventos)
  doc_engine/     indexação, busca, contratos, completeness, AI context
core/frontend/src/
  components/ pages/ store/ lib/ hooks/ contexts/
modules/{repository,installed,cache}/   pacotes .mod e módulos instalados
launcher/  cli/  sdk/  config/  logs/
```

## Princípios

- **Core mínimo**: estável, leve, sem domínios de negócio; extensão via hooks marcados no código ("PLUGIN LOADER HOOK") indicando pontos de extensão futuros.
- **Modularidade**: manifest.yaml → validação → registro → navegação por metadados → montagem de routers.
- **Configuração centralizada**: `app/core/settings.py`; nada de URLs/portas/caminhos hardcoded.
- **Local First, Server Ready**: single-process hoje; sem decisões que impeçam servidor multiusuário no futuro.

## Modos de Execução

| Modo | Comando | Backend | Frontend |
|---|---|---|---|
| **Desktop** (default c/ build) | `techforge start` | uvicorn sem reload, `SERVE_STATIC_FRONTEND=true` | backend serve `core/frontend/dist` (SPA fallback) — nenhum processo node |
| **Dev** | `techforge dev` | uvicorn com reload | vite dev server (:5173) |

Decisão documentada: o próprio backend serve os assets estáticos (menor nº
de processos, menor consumo — diretriz "extremamente leve"). O launcher escolhe
o modo automaticamente: desktop se `dist/index.html` existir; `--dev` força
desenvolvimento. CLI: `techforge logs [--backend|--frontend|--launcher]`.

## Fonte Única de Verdade — Registry de Módulos

Regra (2026-08-25, decisão do usuário): o registry in-memory
(`app/module_engine/registry.py`, singleton `registry`) é a FONTE ÚNICA DE
VERDADE sobre módulos em runtime. Toda leitura de estado parte dele.

Hierarquia:
1. `modules/installed/` — verdade física (disco)
2. `ModuleLoader.scan_installed()` → popula o registry in-memory
3. `registry` in-memory — fonte de leitura para TODAS as APIs e UI
4. `sync_registry_to_db()` espelha para a tabela `modules` APENAS para
   contadores do Dashboard e persistência — nunca fonte primária de listagem

Regras:
- APIs de listagem (`/registry/modules`, `/marketplace/installed`, `/health`,
  navegação) leem do registry in-memory global.
- `PackageManager.list_installed()/list_available()` NÃO cria registries
  locais paralelos — usa `_read_registry` (global; isolado apenas em testes).
- Módulos INVALID/INCOMPATIBLE ficam no registry com status próprio; a UI
  decide como exibir. Não filtrar na fonte.
- Após qualquer mutação: `scan_installed()` + `sync_registry_to_db()`.

## Module Lifecycle — Activate / Deactivate

Semântica (diretriz do produto): **desativar = poupar recursos**.

```text
INSTALLED ⇄ DISABLED   (activate / deactivate)
DISABLED  → REMOVED    (remove — ação explícita)
```

- **Deactivate**: flag em `<module>/data/state.json` + `is_enabled=false` no DB.
  O Loader não monta entry_backend de DISABLED no boot; NavigationBuilder os
  exclui da navegação. Arquivos e metadados preservados.
- **Activate**: limpa a flag, restaura INSTALLED e faz hot-mount das rotas.
- Cada transição registra operation_log + notificação (Notification Foundation).
- Guard de instalação: ID já registrado como INVALID/INCOMPATIBLE é rejeitado.
- Limitação conhecida: desativação não descarrega módulo já montado em runtime
  (requer restart). Hot-unload ainda não implementado.

APIs: `POST /api/v1/marketplace/activate/{id}` · `/deactivate/{id}`
CLI: `techforge modules activate|deactivate|remove <id>`

## Module Frontend Contract

`entry_frontend` aponta para um módulo JS (ESM) **compilado**, servido via
`GET /api/v1/modules/{id}/assets/{path}`. Contrato micro-frontend:

```js
// frontend/main.js
export default {
  render(container) { /* desenha a UI dentro do container */ },
};
```

O host (`ModuleHost.tsx`) importa dinamicamente e chama `render(el)` dentro de
um ErrorBoundary — falha do módulo nunca derruba o Core.
Extensões servidas: whitelist (.js/.css/.svg/.png/...); path traversal bloqueado.

## Notification Foundation

Notificações são **dado legítimo do Core** (data ownership) — nunca dados
de negócio de módulos. APIs:

```text
GET  /api/v1/notifications?unread_only=&limit=
POST /api/v1/notifications                        {level: info|warning|error|success, title, message?, module_id?}
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/{id}/read · /read-all
```

Backend: `app/models/notifications.py` + `app/services/notifications.py` +
`app/api/routes/notifications.py`. Frontend: store zustand com polling leve (30s)
e `NotificationBell` no Header. Novos módulos/serviços devem usar `NotificationService.create()`.
O SDK entrega via `NotificationsSDK.push()` com fallback silencioso para fila local.

## Pontos de extensão pendentes

- activate/deactivate quente em runtime (hot-unload)
- RemoteRepositoryProvider (NotImplementedError)
- dynamic import de entry_frontend já feito; restam refinamentos de empacotamento
