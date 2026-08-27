# Plano — Fase 7: Documentation Compliance Checker (fechamento das lacunas §9/§10)

> Spec: docs/phases/07-Fase-07-Documentation-Compliance-Checker.md
> Auditoria: phase-audit.md — Fase 7 ✅ fechada (checker, API, CLI, frontend badge,
> notificações §15, governança documentada, módulos existentes já compliant).
> Este plano fecha as lacunas reais de qualidade estrutural (§9/§10) e o
> relatório final que faltava (todas as outras fases fechadas têm um).

## Premissas validadas

1. ✅ `DocCompletenessChecker` existe (`app/doc_engine/completeness.py`) — Implementation/Contract/Documentation/Example, application vs service.
2. ✅ `APIYamlParser` normaliza `returns: str` e `returns: {type: ...}` (§7/§8).
3. ✅ `GET /docs/completeness` e `/completeness/{module_id}` — batch sem N+1, relatório individual.
4. ✅ `POST /docs/compliance/check/{id}` notifica (dedupe) — §15.
5. ✅ CLI `validate-module` mostra checks prefixados `§16`.
6. ✅ Frontend `CompletenessBadge.tsx` em `ModuleCard.tsx`, fetch em lote via `completenessApi.all()`.
7. ✅ `TemplateGenerator` já gera scaffold compliant (overview + examples/basic.md; service ganha advanced/integration + contrato).
8. ✅ Governança documentada em `docs/developer-center/governance/documentation-first-principle.md`.
9. ✅ Módulos existentes (`hello_world`, `veeam_m365`) já 100% compliant — nenhuma correção de conteúdo necessária (§18 satisfeito).
10. ❌ §9 (qualidade estrutural): overview só checa `len(strip()) > 40` — não pega "só título sem conteúdo" nem placeholder de scaffold não editado.
11. ❌ §9: nenhum check de TODO não resolvido em módulo publicado.
12. ❌ §9: exemplos (`basic.md`/`advanced.md`/`integration.md`) só checam existência do arquivo, não conteúdo mínimo.
13. ❌ §10: nenhum exemplo verificado contra comportamento real (hello_world é candidato óbvio — determinístico e simples).
14. ❌ `tasks/phase-07-report.md` não existe (fases 02–06 têm relatório final; Fase 7 não).

## Decisão de escopo

Não recriar checks já cobertos (Implementation/Contract/exports/tiers) — só
adicionar validação de **qualidade de conteúdo** (§9) onde hoje só existe
checagem de presença de arquivo, e o exemplo verificável (§10) para o módulo
de referência. Regras continuam determinísticas e auditáveis — sem IA
avaliando semântica (§20 fora de escopo, reafirmado).

## Slices

### Slice 1 — Quality gate no `DocCompletenessChecker` (TDD) — spec §9
- Novo helper `_content_quality(path) -> DoDCheck` em `completeness.py`:
  - arquivo vazio → FAIL
  - só heading (`# Título` e nada mais após strip) → FAIL
  - contém `TODO` não resolvido → WARNING (não bloqueia `is_complete`, mas aparece no relatório — precisa de um terceiro estado além de `passed: bool`; avaliar se basta `required=False` + `detail` explicando, ou se vale introduzir `DoDCheck.severity: PASS|FAIL|WARNING` mínimo para não estourar o modelo existente)
- Aplicar em `overview.md` e em cada tier de exemplo presente (`basic.md`, `advanced.md`, `integration.md`).
- Testes novos: overview vazio, overview só título, exemplo vazio, TODO em exemplo publicado, mistura de PASS/FAIL/WARNING no mesmo relatório.

**Aceite:** `pytest core/backend/tests/test_documentation_first.py -q` cobre os casos novos; `score`/`is_complete` continuam corretos (WARNING não derruba completude).

### Slice 2 — Exemplo verificável para hello_world (TDD) — spec §10
- `modules/installed/hello_world/tests/`: teste que executa a função/endpoint documentado em `docs/examples/basic.md` e compara com o resultado esperado documentado (cadeia Implementation → Execute → Expected → Compare).
- Não criar mecanismo genérico de execução de Markdown (§10 explícito) — só o teste pontual do módulo de referência.

**Aceite:** teste roda dentro da suíte do módulo (ou via pytest do backend se o módulo for coletado), falha se exemplo documentado divergir do código real.

### Slice 3 — CLI/API refletindo WARNING — spec §12
- `module_validator.py`: renderizar estado WARNING dos novos checks §16 sem tratá-lo como FAIL (hoje só PASS/FAIL).
- `CompletenessReportRead` (schema da API): expor o novo estado se o modelo mudar no Slice 1.
- Frontend `CompletenessBadge.tsx`: se badge hoje só distingue completo/incompleto, decidir se WARNING muda a cor/label ou fica agregado em "Incomplete" (menor escopo: manter agregado, documentar a decisão).

**Aceite:** `techforge validate-module` mostra WARNING distinto de FAIL; build/lint do frontend sem quebrar contrato de `CompletenessReportRead`.

### Slice 4 — Relatório final
- `tasks/phase-07-report.md` no padrão de `tasks/phase-06-report.md`: Tests/Backend/Frontend/API/Database/Build/Known Issues.
- Atualizar `tasks/phase-audit.md` linha da Fase 7 se o texto de lacunas mudar.

## Fora de escopo (spec §20, reafirmado)
IA avaliando semântica da documentação, geração automática de docs por IA,
Service Registry, Dependency Governance, assinatura digital, Marketplace
remoto, sistema de permissões.

## Ordem
1 → 2 → 3 → 4; rodar suíte completa (`pytest tests -q` + `npm run lint`/`build`) após cada slice.
