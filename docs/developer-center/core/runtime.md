---
title: Runtime
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, runtime, phase-6, lifecycle]
---

# Runtime

Fundação mínima do runtime da plataforma. Localização:
`core/backend/app/runtime/`.

## Responsabilidade atual

- Conhecer o estado da plataforma: `bootstrapping → ready → shutting_down → stopped`
- Receber eventos de startup/shutdown (com timestamp e histórico dos últimos 20)
- Expor estado via `GET /api/v1/runtime/status`

## Integração

O FastAPI lifespan (`app/main.py`) dispara:

```python
await runtime.fire_startup("platform ready")   # após loaders/doc engine
...
await runtime.fire_shutdown("backend stopped") # no teardown
```

Handlers podem ser registrados com `runtime.on_startup(fn)` e
`runtime.on_shutdown(fn)`. Falha em um handler nunca bloqueia o shutdown.

## O que NÃO faz nesta fase

- Dependências entre módulos
- Service Registry
- Ativação dinâmica de módulos
- Hot reload de módulos

Estes serão implementados em fases futuras sobre esta fundação, sem alterar
o contrato atual (`state`, `events`, `/api/v1/runtime/status`).

## Consumo pelo Dashboard

`GET /api/v1/runtime/status` retorna:

```json
{
  "state": "ready",
  "started_at": "2026-08-24T13:00:00",
  "events": [...]
}
```

Mesmo formato consumido pelo comando `techforge status`.
