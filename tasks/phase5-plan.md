# Plano — Fase 5: Developer Center (fechamento das lacunas)

> Spec: docs/phases/05-Fase-05-Developer-Center.md
> Auditoria: phase-audit.md — Fase 5 ~85%. Documentation Engine completo
> (busca, contratos, AI context, completeness). Este plano fecha as 3 lacunas.

## Premissas validadas

1. ✅ APIs do doc engine existem: /docs/list, /docs/article, /docs/search,
   /docs/contracts, /docs/export/ai-context, /docs/completeness
2. ✅ CLI tem create/validate/package/modules/platform — NADA de docs
3. ❌ Help contextual (context_id → rota) não existe (spec §13)
4. ❌ Versionamento documental (documentation.version/applies_to no manifest)
   não existe (spec §17)
5. ✅ Frontend DeveloperCenterPage já consome o doc engine

## Slices

### Slice 1 — CLI `techforge docs` reutilizando o Doc Engine (TDD) — spec §20
- Grupo `cli/commands/docs.py`:
  - `docs list` — GET /api/v1/docs/list (fallback: scan local docs/ se offline)
  - `docs search <query>` — GET /api/v1/docs/search?q=
  - `docs get <path>` — GET /api/v1/docs/article/:path (bônus barato)
  - `docs export-context [--scope X]` — GET /docs/export/ai-context
- Sem duplicar lógica: só consome a API do Core

**Aceite:** testes com CliRunner + mock/fallback; comandos funcionam.

### Slice 2 — Help contextual context_id (TDD) — spec §13
- Rota `GET /api/v1/docs/context/{context_id}` no doc engine:
  mapping declarativo context_id → article path (dicionário em settings ou yaml)
- Contrato simples primeiro: mapa fixo core (dashboard→overview, modules→modules-guide...)
- Frontend: botão "?" nas páginas principais abre o artigo mapeado

**Aceite:** testes do mapping; navegação help funciona na UI.

### Slice 3 — Versionamento documental (§17) + relatório
- Parser aceita bloco opcional `documentation.version/applies_to` no manifest
- Exposto nos metadados (/registry/modules); sem resolvedor de versão (spec veda)
- Browser E2E dos 3 slices + tasks/phase-05-report.md + auditoria → Fase 5 ✅

## Fora de escopo
Documentation Engine completo já existe; compliance (Fase 7 feita).

## Ordem
1 → 2 → 3; commit/push por slice após validação.
