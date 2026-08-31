---
title: "ADR-004: Service/Application Modules"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-004: Service / Application Module Distinction

**Status**: Accepted

## Context

Nem todo módulo precisa de UI — alguns só oferecem uma capacidade
(export) pra outros módulos consumirem (ex: um serviço de informação de
sistema), enquanto outros são pensados pra interação direta do usuário. Sem
essa distinção, todo módulo teria que declarar UI mesmo sem sentido, e
não haveria uma regra clara sobre quem pode depender de quem.

## Decision

Todo módulo declara `module_type: service | application` no manifest.
Service Modules expõem `exports` (capabilities invocáveis por outros
módulos, via `service_registry.invoke()`), tipicamente sem UI obrigatória.
Application Modules são voltados a interação direta do usuário e podem
depender de Service Modules. A direção de dependência é sempre
Application → Service, nunca o inverso — validado por
`DependencyValidator._check_direction`.

## Consequences

- Módulos que são puro backend (ex: coleta de dados de sistema) não
  precisam forçar uma UI artificial.
- A regra de direção evita ciclos de dependência conceituais entre
  módulos de UI e módulos de infraestrutura.
- Descoberta e invocação de capability passam por um caminho único
  (`service_registry`), o que dá rastreabilidade (Execution History,
  métricas) de toda invocação entre módulos.
- Em contrapartida, hoje não há política de precedência automática
  quando dois Service Modules declaram a mesma capability — conflito é
  apenas reportado, não resolvido (ver Technical Debt Registry).

## Alternatives Considered

- **Todo módulo é igual, sem distinção de tipo**: mais simples, mas não
  dá nenhuma garantia sobre direção de dependência nem sobre o que é
  "serviço reutilizável" vs "ferramenta com tela" — rejeitado por perder
  uma regra de design útil desde o início.
