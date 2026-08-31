---
title: "ADR-005: Local-first Desktop"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-005: Local-first Desktop

**Status**: Accepted

## Context

O público inicial da plataforma é single-user, rodando localmente, sem
necessidade comprovada de acesso remoto multi-usuário. Construir para
multi-tenant desde o início (autenticação, isolamento por usuário,
servidor central) adicionaria complexidade sem um caso de uso real
puxando essa necessidade.

## Decision

TechForge roda local-first: modo Desktop serve o frontend já compilado
(`core/frontend/dist/`) diretamente do próprio backend Python (sem
processo Node.js separado), com SQLite local e paths por SO via
`platformdirs`. Não há autenticação nem conceito de usuário multi-tenant
hoje. Um modo Server centralizado multi-usuário foi deliberadamente
adiado (ver Fase 13 do histórico do projeto) até haver necessidade real.

## Consequences

- "Baixar e rodar" — sem dependência de infraestrutura externa (banco
  gerenciado, servidor de autenticação).
- Superfície de ataque menor no cenário atual (sem rede exposta por
  padrão, `127.0.0.1` apenas).
- Boa parte do código já evita acoplamento impossível de migrar (paths
  via `platformdirs`/settings, não hardcoded; storage via SQLAlchemy
  isolado em `app/db/`) — confirmado nas revisões de arquitetura, o que
  deixa a porta aberta pra um Server futuro sem reescrita completa.
- Em contrapartida, alguns pontos assumem processo único hoje (ex: job
  tracking de instalação remota em dict in-memory) — documentados como
  dívida técnica a resolver só se/quando um modo multi-worker for
  decidido.

## Alternatives Considered

- **Servidor central desde o início**: rejeitado — adicionaria
  autenticação, multi-tenancy e infraestrutura de deploy sem um usuário
  real pedindo isso agora.
- **Aplicação Electron completa** (processo Node embutido): rejeitado —
  o backend Python já provê tudo que a UI precisa; adicionar um runtime
  Node só pra empacotar a UI seria peso extra sem ganho, dado que o
  próprio backend já serve os arquivos estáticos.
