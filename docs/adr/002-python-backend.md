---
title: "ADR-002: Python Backend"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-002: Python Backend (FastAPI + SQLAlchemy async)

**Status**: Accepted

## Context

O Core precisa de um backend que sirva API HTTP pra UI, execute código de
módulo dinamicamente carregado, e persista estado — rodando tanto em modo
Desktop empacotado (PyInstaller) quanto em desenvolvimento local, sem
depender de infraestrutura externa (banco de dados gerenciado, containers).

## Decision

Backend em Python com FastAPI (framework HTTP async) e SQLAlchemy async
(ORM) sobre SQLite (aiosqlite). Módulos de terceiros também são carregados
como código Python (`importlib`), o que unifica a linguagem do Core e do
ecossistema de módulos.

## Consequences

- Import dinâmico de módulo (`load_module_file`) é direto em Python, sem
  precisar de um runtime separado ou sandbox de linguagem cruzada.
- FastAPI dá tipagem de request/response (Pydantic) e docs automáticas
  (`api.yaml`/OpenAPI) de graça.
- SQLite elimina a necessidade de instalar/gerenciar um servidor de banco
  separado — essencial pro modo Desktop local-first.
- Em contrapartida, código de módulo malicioso/com bug roda no mesmo
  processo Python do Core (mitigado por module_trust/integrity, não por
  isolamento de processo) — trade-off aceito conscientemente pelo
  contexto atual (módulos internos, não marketplace público aberto).
- SQLite tem limites conhecidos de concorrência de escrita — aceitável
  pro perfil de uso single-user; migração pra PostgreSQL fica isolada em
  `app/db/` caso um cenário multi-usuário real apareça no futuro.

## Alternatives Considered

- **Node.js/TypeScript no backend** (unificando com o frontend): rejeitado
  porque o tipo de funcionalidade esperada dos módulos (scripts de
  sistema, integrações, cálculos) é mais natural em Python, e o
  ecossistema de bibliotecas de sistema (psutil, keyring, etc.) já é
  usado no Core.
- **PostgreSQL desde o início**: rejeitado por exigir um processo de
  banco separado rodando, incompatível com o objetivo de "baixar e
  rodar" do modo Desktop.
