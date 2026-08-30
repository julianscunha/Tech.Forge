---
title: Platform Quality, Testing & Release Engineering
category: core-architecture
domain: [core]
---

# Platform Quality, Testing & Release Engineering

> Quality pipeline, níveis de teste, contract tests, versionamento,
> changelog, Release Readiness Report, CI e checklist de release de módulo.

## Definition of Done

Nenhuma funcionalidade é considerada pronta só porque "funciona na minha
máquina" (spec §2). Antes de considerar um slice/feature fechado:

- [ ] **Implementation** — código completo, sem TODO pendente no caminho crítico.
- [ ] **Tests** — cada comportamento novo tem teste correspondente, marcado
      com o nível certo (`unit`/`integration`/`contract`/`e2e`/`smoke`/`regression`).
- [ ] **Documentation** — `DocCompletenessChecker` passa para o módulo/feature.
- [ ] **Compatibility** — `techforge modules quality <id>` reporta `ready: true`
      (status, documentação, compatibilidade de versão, contrato de serviço).
- [ ] **Build** — `npm run build` (frontend) e suíte pytest completa (backend) passam.
- [ ] **Validation** — `techforge validate-module` (para módulos) ou
      `techforge release-check` (para o Core) não bloqueia.

Reusa o **Documentation Compliance Checker** e os validadores já existentes
— não há critérios de qualidade paralelos (spec §2).

---

## Estratégia de testes

### Níveis (spec §4)

Registrados como `pytest` markers (`core/backend/pytest.ini`, `cli/pytest.ini`,
`--strict-markers`) — um marker desconhecido falha a coleta, não passa
silenciosamente:

| Marker | O que cobre | Exemplo |
|---|---|---|
| `unit` | Lógica pura, sem rede/DB/TestClient | parsers, validadores, `packaging.version` |
| `integration` | TestClient + DB real + filesystem multi-etapa | Package Manager + Registry |
| `contract` | Exemplo documentado (`api.yaml`) executa de verdade | `test_phase15_contract_tests.py` |
| `e2e` | Fluxo crítico ponta a ponta | install→validate→activate→execute→deactivate→remove |
| `smoke` | Verificação rápida pós-build | start→health→storage→discover→activate→execute |
| `regression` | Reproduz um bug corrigido, retido como guarda | — |

Os ~600 testes anteriores a esta categorização **não foram reorganizados fisicamente**
— cada arquivo ganhou `pytestmark = pytest.mark.X` no topo (module-level),
categorizado pela presença de `TestClient`/DB (→ `integration`) vs. lógica
pura (→ `unit`). Testes novos já nascem marcados.

Rodar por nível:
```bash
pytest tests -m unit -q
pytest tests -m integration -q
```

### Fixtures centralizadas

`core/backend/tests/conftest.py` — `module_dir_factory`, `valid_manifest`,
`invalid_manifest` — servem testes **novos**; os 13 arquivos que já
construíam seu próprio fixture de módulo não foram retrofitados (duplicação
interna sem valor de correção real, spec §13 cumprido sem reescrever
histórico estável).

### Architecture tests

`test_phase15_architecture.py` — via `ast-grep` (ferramenta mandatória do
projeto, não uma lib nova tipo `import-linter`): módulo instalado nunca
importa `app.*` (Core interno) nem outro módulo diretamente; `ModuleKVStorage`
nunca aceita `module_id` como parâmetro de chamada (guarda estrutural).
Regras de tipo de dependência (Service × Application) já existiam
antes — não duplicadas.

### Contract tests genéricos

`app/doc_engine/contract_examples.py::extract_example_calls()` extrai, via
`ast.parse`/`ast.literal_eval`, os exemplos de `api.yaml` que são chamadas
Python executáveis (`calculate_storage(users=500, ...)`) — ignora exemplos
HTTP-style. O teste roda contra **todos** os módulos instalados
automaticamente, invocando via `service_registry.invoker.invoke` (o mesmo
caminho de produção) — não é um teste hand-written por módulo.

---

## Static quality

Backend: `ruff` (`pyproject.toml` na raiz) — `select = ["E","F","I"]`;
`pyupgrade` (`UP`) deliberadamente fora do escopo (modernização cosmética
sem relação com quality gate). `E402` liberado só em `tests/*.py` (padrão
`sys.path.insert()` necessário); `F401` liberado só em `__init__.py`
(re-exports intencionais).

Frontend: `eslint` (flat config, `eslint.config.js`) — só as regras
clássicas de corretude do `react-hooks` (`rules-of-hooks`, `exhaustive-deps`);
o preset `recommended` da v7 do plugin é voltado ao React Compiler e
reprovaria o padrão de fetch-on-mount usado em todo o codebase.

---

## Versionamento

`app/services/versioning.py::is_valid_semver()` — via `packaging.version`
(sem parser próprio). Fonte única: `PLATFORM_VERSION`
(`app/core/settings.py`) — exposta em `GET /api/v1/system/version` e
`techforge version` (acesso direto, funciona com a plataforma parada).

**Multiple-sources-of-truth eliminadas nesta fase**: CLI tinha
`click.version_option("1.0.0")` hardcoded; `core/frontend/package.json`
tinha `"version"` independente. Ambos agora derivam de/são travados contra
`PLATFORM_VERSION`.

### Canais de pre-release (§35)

Manifest aceita `channel: stable|beta|development` (default `stable`),
validado no parse, propagado via `manifest_raw`. **Mecanismo apenas** — sem
UI de catálogo dedicada (sem usuários externos ainda pra segmentar canal
visualmente).

---

## Changelog & Release Notes

`CHANGELOG.md` (raiz) cobre só o **Core** — formato
[Keep a Changelog](https://keepachangelog.com/), seções restritas a
`Added/Changed/Fixed/Deprecated/Removed/Known Issues`
(`app/services/changelog.py::validate_changelog()`). Módulos mantêm
`CHANGELOG.md` próprio na pasta do módulo — nunca misturar releases.

### Processo padrão de release (GitHub Releases)

Passo a passo pra cortar uma release nova do Core:

1. Mover o conteúdo acumulado em `## [Unreleased]` do `CHANGELOG.md` para
   uma seção nova `## [X.Y.Z] - YYYY-MM-DD`, categorizado em
   `Added`/`Changed`/`Fixed`/`Deprecated`/`Removed` (só o que houver —
   não força seção vazia) + `Known Issues` com as limitações que
   realmente importam pra quem vai usar a release (não é o lugar pra
   despejar todo débito técnico interno — isso fica em
   `tasks/phase-audit.md`). **Cada bullet/parágrafo numa linha só, sem
   quebra manual no meio do texto** — o corpo do GitHub Release usa o
   modo "gfm" de renderização (igual issue/PR/comentário), onde toda
   quebra de linha simples vira `<br>` literal; isso NÃO acontece com
   arquivos do repositório (README, Developer Center — esses usam outro
   modo, quebra de linha é só espaço). Wrap manual no `CHANGELOG.md` faz
   o texto do release aparecer com linhas curtas paradas no meio da tela.
2. Atualizar `PLATFORM_VERSION` em `app/core/settings.py` e `"version"`
   em `core/frontend/package.json` pro mesmo valor (§24 — fonte única;
   há um teste de guarda que trava se divergirem).
3. `techforge release-check` — precisa reportar `Release: READY` antes
   de seguir.
4. Validar o changelog: `validate_changelog()` deve retornar sem erros
   (seção, data e versão bem formadas) — já roda como teste automatizado.
5. Commit da atualização de versão/changelog, depois:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <(sed -n '/## \[X.Y.Z\]/,/## \[/p' CHANGELOG.md | sed '$d')
   ```
   Ou, mais simples: copiar manualmente o bloco da versão nova do
   `CHANGELOG.md` (sem o cabeçalho `## [X.Y.Z] - data`) como corpo do
   `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file -`.
6. Versionamento segue [SemVer](https://semver.org/): `MAJOR` = breaking
   change, `MINOR` = funcionalidade nova compatível, `PATCH` = correção
   compatível — mesma regra do `is_valid_semver()`.

Módulo segue o mesmo princípio (`CHANGELOG.md` próprio + tag no repositório
onde o módulo vive), mas não usa GitHub Releases do Core — cada catálogo de
módulos define seu próprio processo de publicação.

---

## Release Readiness Report

`GET /api/v1/release/readiness` agrega 5 checks vivos reaproveitando
serviços existentes: `version_consistency`, `changelog`, `documentation`,
`migrations`, `storage`. **Tests e Build ficam fora do agregador vivo** —
rodar a suíte inteira ou `npm run build` dentro do processo do próprio
servidor avaliado é pesado e circular.

```bash
techforge release-check              # roda os 5 checks vivos + pytest + npm build
techforge release-check --skip-tests --skip-build   # só os checks vivos
```

Sai com código != 0 se qualquer coisa falhar (`Release: BLOCKED`).

### Por módulo

```bash
techforge modules quality <id>         # informativo
techforge modules release-check <id>   # mesmo dado, framing de gate
```

4 checks: `status` (registry), `documentation`, `compatibility`, `contract`
(só executa se o módulo declarar `api.yaml` e estiver `ACTIVE`).

---

## Module Release Checklist

Antes de publicar uma nova versão de módulo:

1. `techforge validate-module <path>` — manifest, estrutura, dependências, integridade.
2. `techforge modules quality <id>` (módulo já instalado) — `ready: true`.
3. `CHANGELOG.md` do módulo atualizado (seção da nova versão).
4. Se o módulo declarar `configuration.fields` e mudar entre versões:
   implementar `migrate_config(old_version, old_config)` no `entry_backend`
   — testado com uma config real da versão anterior.
5. Se o módulo declarar `docs/contracts/api.yaml`: todo exemplo documentado
   deve executar sem erro (`extract_example_calls` + `invoke`).

---

## CI

`.github/workflows/ci.yml` (GitHub Actions) — dois jobs:

- **backend**: `ruff check`, pytest por marker (`unit`/`integration`/
  `contract`/`e2e`/`smoke`), `techforge validate-module` nos módulos de
  referência, suíte da CLI.
- **frontend**: `eslint`, `npm run build`, upload do artefato `dist/`.

Sem CI comercial obrigatório, sem deploy automático, sem GitOps — só o que
já roda localmente, automatizado (spec §48).

---

## Rollback readiness

**Desktop**: sem mecanismo automatizado (spec permite "implementação
simples") — procedimento manual antes de uma atualização do Core:
```bash
copy config\techforge.db config\techforge.db.bak
```
Restaurar o `.bak` reverte o estado caso a migration/atualização falhe.

**Módulo**: `PackageManager.update()` já reverte arquivos **e** configuração
em caso de falha (rollback-por-exceção) — comportamento já existente,
nada novo construído aqui.

---

## Limitações conhecidas

1. Backend Package / Desktop Distribution não existem como artefato
   rastreável (`version+checksum+build metadata`) — o backend roda direto
   de fonte via `uvicorn`, sem etapa de empacotamento. Pertence à Desktop
   Distribution, não antecipado aqui.
2. Rollback de Desktop é manual (cópia de arquivo), não automatizado.
3. `techforge validate-module` falha no console PowerShell/Windows com
   `UnicodeEncodeError` (cp1252 não renderiza glifos do `rich`) — cosmético
   do terminal local, não reproduzido em CI (Ubuntu, UTF-8).

---

Veja também:
- [Module Lifecycle](module-lifecycle.md)
- [Module Trust](module-trust.md)
- [Persistence](persistence.md)
- [Dependency Governance](dependency-governance.md)
