## O que muda e por quê

<!-- Descreva a mudança e a motivação. Se for mudança ao Core (não um
módulo novo), inclua a justificativa arquitetural — ver CONTRIBUTING.md. -->

## Tipo de mudança

- [ ] Módulo novo ou alteração em módulo existente
- [ ] Mudança no Core (backend/frontend/CLI/SDK)
- [ ] Documentação apenas

## Checklist

- [ ] `cd core/backend && .venv/Scripts/python.exe -m pytest tests -q` passa
- [ ] `cd core/frontend && npm run lint && npm run build` passa sem warnings
- [ ] Se é um módulo: `GET /api/v1/docs/completeness/<módulo>` passa
- [ ] Documentação atualizada, se o comportamento público mudou
