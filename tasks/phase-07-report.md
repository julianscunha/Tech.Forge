# Phase 07 Report — Documentation Compliance Checker

## Já existia (fechamento original, sem relatório na época)
`DocCompletenessChecker` (Implementation/Contract/Documentation/Example),
`APIYamlParser` (normaliza `returns: str` e `{type: X}`), API
`GET /docs/completeness` + `/completeness/{id}`, `POST /docs/compliance/check/{id}`
notifica com dedupe (§15), CLI `validate-module` reutiliza o Checker na seção
"Documentation Compliance" (§12), frontend `CompletenessBadge` em `ModuleCard`
com fetch em lote, `TemplateGenerator` já gera scaffold compliant, governança
documentada em `docs/developer-center/governance/documentation-first-principle.md`,
módulos existentes (`hello_world`, `veeam_m365`) já 100% compliant.

## Slice 1 — Quality gate (§9) — NOVO
- `_quality_checks()` em `completeness.py`: reutiliza `_parse_frontmatter`
  (markdown_parser) para isolar o corpo do texto, remove linhas de heading e
  mede o conteúdo restante.
  - `overview.md`: exige ≥40 caracteres de corpo real (era só
    `len(strip()) > 40` no texto bruto, sem descontar heading/frontmatter).
  - Cada tier de exemplo presente (`basic.md`/`advanced.md`/`integration.md`):
    exige corpo não-vazio além do heading.
  - TODO não resolvido em qualquer um desses arquivos → check `required=False`
    (mesmo padrão já usado para "recomendado"), não bloqueia `is_complete`.
- Nenhuma mudança de schema: `DoDCheckRead` já expunha `passed`+`required`,
  então o novo check WARNING chega à API/CLI/frontend sem tocar em mais nada.

## Slice 2 — Exemplo verificável (§10) — NOVO
- `test_hello_world_ping_matches_documented_example`: executa
  `hello_world/backend/main.py::ping()` e compara com o JSON documentado em
  `docs/examples/basic.md`. `veeam_m365` já tinha o equivalente
  (`calculate_storage`) desde o fechamento original da fase.

## Slice 3 — CLI/API refletindo WARNING (§12)
Nenhum código necessário — o CLI (`validate_module.py`) já renderiza
`⚠ WARN` para `not passed and not required`, e o badge do frontend só lê
`score`/`is_complete` (que ignoram checks não-obrigatórios). O novo check de
TODO já flui pelo caminho existente.

## Achado não corrigido nesta fase (fora do escopo aprovado)
`cli/techforge_cli/validators/module_validator.py::_check_documentation_first`
mantém uma segunda implementação própria dos checks §16 (paralela ao
`DocCompletenessChecker`), usada na tabela "Results" do `validate-module` —
duplica parcialmente a lógica que a tabela "Documentation Compliance" (mesma
tela) já mostra corretamente via `DocCompletenessChecker`. Não foi
consolidado agora para não ampliar o escopo aprovado deste plano; candidato a
uma limpeza futura pontual.

## Tests
255 passed, 3 skipped (suíte completa `core/backend/tests`). Novos: 6 casos
em `TestContentQuality` + `test_hello_world_ping_matches_documented_example`
em `test_documentation_first.py`.

## Backend / Frontend / API / Database
Sem mudança de schema, rota ou modelo — só regra de validação em
`completeness.py`. Frontend intocado (badge já agrega corretamente).

## Build
Não roda `npm run build`/`lint` — nenhuma mudança de frontend nesta fase.

## Known Issues
- Duplicação `module_validator.py` vs `DocCompletenessChecker` (ver acima).
- Exemplo verificável (§10) cobre só os 2 módulos de referência
  (`hello_world`, `veeam_m365`); não é um mecanismo genérico — por decisão
  de escopo original da spec (§10 explicitamente proíbe execução genérica de
  Markdown).
