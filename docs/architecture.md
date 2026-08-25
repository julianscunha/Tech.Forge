---
title: Arquitetura — TechForge Core
category: governanca-setup
domain: [governanca-setup]
---

# TechForge — Architecture

> Documento exigido pela Fase 1 (docs/phases/01 §16). Conteúdo detalhado por domínio
> vive em `docs/INDEX.md`, `docs/developer-center/` e `docs/phases/`.

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
  db/             engine async + session factory
  models/         modelos SQLAlchemy
  schemas/        schemas pydantic (contratos de API)
  services/       serviços de domínio do Core (registry CRUD)
  module_engine/  manifest, validator, registry, loader, journal, navigation, plugin_loader
  package_manager/ install/remove/update/import, compatibility, operation_log
  runtime/        estado runtime da plataforma (status, eventos)
  doc_engine/     indexação, busca, contratos, completeness, AI context
core/frontend/src/
  components/ pages/ store/ lib/ hooks/ contexts/
modules/{repository,installed,cache}/   pacotes .mod e módulos instalados
launcher/  cli/  sdk/  config/  logs/
```

## Princípios (Fase 1 §1)

- **Core mínimo**: estável, leve, sem domínios de negócio; extensão via hooks marcados ("PLUGIN LOADER HOOK", "Phase N").
- **Modularidade**: manifest.yaml → validação → registro → navegação por metadados → montagem de routers.
- **Configuração centralizada**: `app/core/settings.py`; nada de URLs/portas/caminhos hardcoded.
- **Local First, Server Ready**: single-process hoje; sem decisões que impeçam servidor multiusuário no futuro.

## Fluxo principal

```text
Launcher → backend (:8000) → scan modules/installed/ → validator → registry
        → NavigationBuilder → frontend (:5173) via /api/v1/registry/navigation
Package Manager: .mod (ZIP+manifest+checksum) → validate → install atômico
Plugin Loader: mount_module_routers() injeta entry_backend; ModuleHost serve o shell do módulo
```

## Pontos de extensão pendentes (auditoria 2026-08)

- activate/deactivate no ciclo de módulos
- RemoteRepositoryProvider (NotImplementedError)
- dynamic import de entry_frontend no ModuleHost

## Notification Foundation (Fase 2, spec §10/§13)

Notificações são **dado legítimo do Core** (data ownership §13) — nunca dados de
negócio de módulos. Contrato:

```text
GET  /api/v1/notifications?unread_only=&limit=   lista (mais recentes primeiro)
POST /api/v1/notifications                        cria {level: info|warning|error|success, title, message?, module_id?}
GET  /api/v1/notifications/unread-count           {count}
POST /api/v1/notifications/{id}/read              marca uma
POST /api/v1/notifications/read-all               marca todas
```

Backend: `app/models/notifications.py` + `app/services/notifications.py` +
`app/api/routes/notifications.py`. Frontend: store zustand com polling leve (30s)
e `NotificationBell` no Header. Fases futuras (compatibilidade, integridade,
eventos da plataforma) devem usar `NotificationService.create()`.
