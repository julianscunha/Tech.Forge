---
title: "ADR-003: React TypeScript Frontend"
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, adr]
---

# ADR-003: React + TypeScript Frontend

**Status**: Accepted

## Context

A UI do Core precisa montar dinamicamente interfaces de módulos de
terceiros dentro de si mesma (micro-frontends), sem que um módulo com bug
de renderização derrube a shell inteira, e sem forçar módulos a usar
exatamente o mesmo framework/versão do Core.

## Decision

Shell do Core em React + TypeScript (Vite). Módulos expõem seu frontend
como um módulo JS/ESM compilado (`export default { render(container) }`),
servido via `GET /api/v1/modules/{id}/assets/{path}` e importado
dinamicamente (`import()`) pelo `ModuleHost`, dentro de um ErrorBoundary.

## Consequences

- Tipagem estática (TypeScript) reduz classe inteira de bug em contratos
  de API consumidos pela UI (schemas Pydantic → tipos TS).
- O contrato de módulo frontend (`render(container)`) é agnóstico à
  tecnologia interna do módulo — um módulo pode usar Preact, vanilla JS,
  ou até outro framework, desde que compile pra um `render()` válido.
- ErrorBoundary garante que falha de um módulo não derruba a shell —
  confirmado em runtime real.
- Em contrapartida, o contrato de módulo frontend não dá tipagem
  compartilhada automática entre Core e módulo — o módulo precisa aderir
  ao contrato por convenção, não por compilador.

## Alternatives Considered

- **Iframe por módulo**: isola completamente, mas complica compartilhamento
  de tema/autenticação/navegação com o shell — rejeitado pelo custo de UX.
- **Module Federation (Webpack)**: dá integração mais rica entre Core e
  módulo, mas exige alinhamento de versão de bundler entre Core e todos
  os módulos — rejeitado por acoplar demais o ciclo de build de módulos
  de terceiros ao do Core.
