# Phase 05 Report — Developer Center (fechamento das lacunas)

## Documentation Engine
Já implementado (busca, contratos, AI context, completeness). Nenhuma alteração.

## CLI docs (§20, novo)
`techforge docs list | search <q> | get <path> | export-context [--scope]`.
Consome exclusivamente a API `/api/v1/docs/*` — zero duplicação de lógica.

## Help contextual (§13, novo)
- Mapping declarativo: `docs/context-map.yaml` (context_id → doc_id)
- API: `GET /api/v1/docs/context/{context_id}` (404 p/ ID desconhecido ou artigo ausente)
- UI: botão "Ajuda" no breadcrumb das páginas mapeadas (dashboard, modules,
  marketplace, developer-center, settings) abre drawer lateral com o artigo

## Versionamento documental (§17, novo)
Manifest aceita bloco opcional:

```yaml
documentation:
  version: 1.1.0            # semver obrigatório quando presente
  applies_to:
    techforge: ">=1.0.0,<2.0.0"
```

Parser expõe `documentation_version`/`documentation_applies_to`. Sem resolvedor
de versão (vedado pela spec nesta fase).

## Tests
287 passed, 3 skipped.
Novos: cli/tests/test_docs_command.py (6), core/backend/tests/test_phase5_context.py (4),
core/backend/tests/test_phase5_docversion.py (3).

## Build
Frontend OK (tsc + vite).

## Browser E2E (2026-08-25)
- Botão "Ajuda" visível na página Dashboard ✅
- Drawer abre com conteúdo de core/app-shell ✅
- context_id desconhecido → 404 limpo ✅

## Known Issues
- ESLint ausente no frontend (pré-existente — Fase 15)
