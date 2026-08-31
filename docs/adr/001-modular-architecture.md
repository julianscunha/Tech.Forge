---
title: "ADR-001: Modular Architecture"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-001: Modular Architecture

**Status**: Accepted

## Context

Uma plataforma de ferramentas internas precisa suportar funcionalidades de
domínio muito diferentes entre si (diagnóstico de sistema, sizing de
backup, monitoramento, etc.) sem que cada nova funcionalidade exija tocar
no núcleo da plataforma. Um monólito com toda lógica de negócio embutida
acopla o ritmo de evolução de cada funcionalidade ao ritmo de evolução do
Core, e torna arriscado adicionar/remover funcionalidade sem afetar o
resto.

## Decision

O Core não contém lógica de negócio nenhuma. Toda funcionalidade de
domínio vive em módulos `.mod` instalados independentemente, carregados
dinamicamente via um contrato de manifest + backend/frontend entry point.
O Core só provê: registry de módulos, runtime de execução, storage
isolado por módulo, observability, segurança/trust, e a UI de shell que
monta módulos dentro de si.

## Consequences

- Adicionar/remover funcionalidade nunca exige alterar o Core — só
  instalar/desinstalar um `.mod`.
- Um módulo com bug não derruba a plataforma (isolamento de falha via
  contrato de execução e ErrorBoundary no frontend).
- Em contrapartida, qualquer necessidade genuinamente transversal
  (ex: um novo tipo de storage, um novo mecanismo de trust) precisa
  virar uma mudança de contrato do Core, não um workaround dentro de
  um módulo — disciplina que exige revisão deliberada antes de mudar o
  Core.

## Alternatives Considered

- **Monólito único**: mais simples de começar, mas acopla toda
  funcionalidade futura ao mesmo ciclo de deploy/teste/versão — rejeitado
  por não escalar com o número de ferramentas internas planejadas.
- **Plugins carregados só via processo separado (microserviços)**: isola
  mais, mas adiciona complexidade operacional (múltiplos processos,
  comunicação de rede) desproporcional ao contexto Desktop single-user —
  rejeitado por ora.
