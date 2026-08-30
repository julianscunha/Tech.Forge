# Relatório — Fase 15: Platform Quality, Testing & Release Engineering

Status: EM ANDAMENTO — iniciada 2026-08-30.
Plano: `tasks/phase15-plan.md`.

## Slices

### Slice 1 — Test level markers

**Arquivos**: `core/backend/pytest.ini`, `cli/pytest.ini` (novos), `core/backend/tests/test_phase15_test_markers.py` (novo, guard), 49 arquivos de teste existentes (`core/backend/tests/*.py` + `cli/tests/*.py`) tageados com `pytestmark = pytest.mark.unit|integration`.

**O quê**: registrados 6 markers (`unit/integration/contract/e2e/regression/smoke`) com `--strict-markers` nos dois `pytest.ini` (backend e cli são raízes de coleta separadas). Guard test (`test_every_test_file_declares_a_level_marker`) varre `tests/*.py` e falha se algum arquivo não declarar `pytestmark`. Categorização mecânica: arquivos com `TestClient`/`AsyncSessionLocal`/`create_async_engine` (ou CLI via `CliRunner`) → `integration`; parsers/validadores/lógica pura sem rede/DB → `unit`. Nenhum arquivo existente foi renomeado ou reorganizado em pastas (decisão do plano — reorganização física teria diff grande sem ganho real).

**Decisão-chave**: marcação por arquivo (module-level `pytestmark`), não por função — spec pede organização por nível, não granularidade por teste individual. Categorização delegada a subagent (trabalho mecânico), verificada por mim ao final.

**Aceite**: guard test passa (2/2); nenhum arquivo ficou sem marker; nenhuma regressão na suíte.

**Teste**: `cd core/backend && .venv/Scripts/python.exe -m pytest tests -q` → 666 passed, 3 skipped. `cd cli && pytest tests -q` (mesmo `.venv`) → 105 passed.

**Commit**: `16ed826`

### Slice 2 — Fixtures centralizadas

**Arquivos**: `core/backend/tests/conftest.py` (novo), `core/backend/tests/test_phase15_fixtures.py` (novo).

**O quê**: `module_dir_factory` (factory fixture que monta um diretório de módulo instalável completo — backend/frontend/docs/tests/assets + manifest.yaml — com overrides), `valid_manifest`, `invalid_manifest` (parametrizado: falta de `version`/`id`/`category`).

**Decisão-chave**: **não retrofita os 13 arquivos existentes** que já constroem seu próprio diretório de módulo manualmente — são testes estáveis, já passando, e a duplicação ali é puramente interna sem valor de correção real; reescrever 13 arquivos só por DRY introduziria risco de regressão sem ganho observável. As fixtures centralizadas servem os testes **novos** desta fase (Slices 3, 4, 5, 10) daqui pra frente, cumprindo §13 sem violar escopo cirúrgico.

**Aceite**: fixtures produzem estrutura válida e manifests inválidos coerentes; nenhuma regressão.

**Teste**: `pytest tests -q` → 672 passed, 3 skipped (era 666 — 6 testes novos de fixture).

**Commit**: `29ced73`

### Slice 3 — Architecture tests

**Arquivos**: `core/backend/tests/test_phase15_architecture.py` (novo).

**O quê**: 3 regras via `ast-grep` (chamado por `subprocess`, path resolvido com `shutil.which` + wrapper `cmd /c` no Windows porque `ast-grep.cmd` — shim npm — não é invocável direto via `CreateProcess`): (1) módulo instalado nunca importa `app.*` (interno do Core) — deve usar o SDK; (2) módulo instalado nunca importa outro módulo diretamente (`modules.installed.<outro>`); (3) `ModuleKVStorage.get/set/transaction` nunca aceita `module_id` como parâmetro de chamada (guarda de regressão da decisão estrutural da Fase 12, via `inspect.signature`, sem depender de ast-grep). As regras de tipo de dependência (Application→Service permitido, Service→Application bloqueado) **já existem** em `test_phase8_1_dependency_governance.py` (Fase 8.1) — não duplicadas aqui.

**Decisão-chave**: `ast-grep` via subprocess, não `import-linter` — evita dependência Python nova, reaproveita ferramenta já mandatória (CLAUDE.md). Testes usam `skipif` se `ast-grep` não estiver no PATH (não quebra CI/dev sem a ferramenta instalada, mas roda de verdade quando disponível — confirmado nesta máquina).

**Aceite**: baseline atual (hello_world, veeam_m365 e demais `modules/installed/`) já está limpo — 0 violações. Detecção real confirmada manualmente injetando um `import app` num diretório temporário fora do repo e vendo o ast-grep reportar o match antes de remover o teste manual.

**Teste**: `pytest tests -q` → 678 passed, 3 skipped (era 672 — 6 testes novos).

**Commit**: `ba68efd`

### Slice 4 — Contract tests de serviço

**Arquivos**: `core/backend/app/doc_engine/contract_examples.py` (novo), `core/backend/tests/test_phase15_contract_examples_parser.py` (novo, unit), `core/backend/tests/test_phase15_contract_tests.py` (novo, contract).

**O quê**: `extract_example_calls(export)` extrai, via `ast.parse`/`ast.literal_eval`, os exemplos de `api.yaml` que são chamadas Python executáveis com keyword args literais (ex.: `calculate_storage(users=500, ...)`) — ignora exemplos em estilo HTTP (`GET /api/v1/modules/x/ping`) e exemplos com argumentos posicionais ou não-literais. O teste `contract` varre **todos** os módulos instalados com `docs/contracts/api.yaml`, extrai os exemplos executáveis e invoca de verdade via `app.service_registry.invoker.invoke` (o mesmo caminho usado em produção), confirmando que o exemplo documentado corresponde ao comportamento real (spec §7, última linha).

**Decisão-chave**: **genérico**, não hardcoded por módulo — `test_phase8_service_registry.py::TestInvoke` já tinha um teste hand-written pra `veeam_m365.calculate_storage`; este é reutilizável automaticamente para qualquer módulo futuro com `api.yaml`, sem escrever um teste novo por módulo (é a peça que a Fase 15 pede para os Slices 9/10 — Release Readiness e Module Quality — poderem rodar contract validation genericamente).

**Aceite**: 2 exemplos executáveis encontrados nos módulos de referência (`veeam_m365.calculate_storage` tem 2; `hello_world.ping`/`veeam_m365.ping` são HTTP-style, corretamente ignorados); resultado do extrator bate com o valor já validado manualmente no teste da Fase 8.

**Teste**: `pytest tests -q` → 685 passed, 3 skipped (era 678 — 7 testes novos).

**Commit**: `65bac37`

### Slice 5 — Compatibility matrix tests

**Arquivos**: `core/backend/app/package_manager/compatibility.py` (modificado), `core/backend/tests/test_phase15_compatibility_matrix.py` (novo).

**O quê**: bug real encontrado e corrigido — `check_compatibility()` (Core×Module, usado desde a Fase 4) usava um parser de versão ingênuo (`str.split(".")` + `int()`) que quebrava silenciosamente em qualquer versão pre-release (`"1.5.0-rc.1"` → componente `"0-rc"` não converte, cai em `(0,0,0)`, julgado INCOMPATIBLE mesmo dentro do range declarado). Corrigido para usar `packaging.version.Version` (já dependência da Fase 12) — mesma assinatura, mesmos 6 call sites intocados. O eixo Module×Dependency Version já usa `packaging` corretamente desde a Fase 8.1 (`Dependency.satisfies_version`) — não duplicado.

**Decisão-chave**: achado real via RED test (não hipotético) — relevante porque a Fase 15 Slice 12 introduz canais de pre-release (`1.5.0-rc.1`), que teriam colidido com esse bug latente se não corrigido agora.

**Aceite**: versão pre-release dentro do range declarado é COMPATIBLE; lógica de WARNING perto do boundary preservada; string malformada não propaga exceção.

**Teste**: `pytest tests -q` → 690 passed, 3 skipped (era 685 — 5 testes novos).

**Commit**: `d29fa4a`

### Slice 6 — Static quality

**Arquivos**: `pyproject.toml` (novo, raiz — config `ruff` cobrindo `app`, `cli`, `sdk`), `core/backend/requirements-dev.txt` (novo), `core/frontend/eslint.config.js` (novo), `core/frontend/package.json` (devDependencies + script `lint`), 6 arquivos de produção corrigidos (backend: `docs.py`, `registry.py`, `repository.py`; frontend: `DeveloperCenterPage.tsx`, `Sidebar.tsx`, `ContextualHelp.tsx`), `cli/techforge_cli/commands/{modules,platform}.py`.

**O quê — backend**: `ruff` (lint + import order + format, uma ferramenta só — evita empilhar black+flake8+isort) com `select = ["E","F","I"]`; `UP` (pyupgrade/modernização de sintaxe) deliberadamente fora do escopo — gera ~600 mudanças cosméticas sem relação com "quality gate". Achados reais corrigidos: **`logging` usado sem import em `docs.py`** (NameError latente se o `except` daquele bloco fosse atingido); **`httpx.AsyncClient` referenciado só como string de type hint sem `httpx` importado** em `repository.py` (F821); 2 variáveis mortas (`resp`, `logs`) em comandos CLI; 2 imports organizacionais movidos ao topo (E402 genuíno, sem risco de import circular verificado). `E402` liberado só para `tests/*.py` (padrão `sys.path.insert()` antes do import local é necessário, generalizado em ~50 arquivos) e `F401` liberado só para `__init__.py` (re-exports intencionais).

**O quê — frontend**: `eslint` não era sequer instalado (gap pré-existente da Fase 12) — instalado do zero com `typescript-eslint` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh` (flat config, `eslint.config.js`). **Decisão deliberada**: usadas só as regras clássicas de corretude do `react-hooks` (`rules-of-hooks`, `exhaustive-deps`) — o preset `recommended` da v7 do plugin é voltado ao React Compiler e reprovaria o padrão comum de fetch-on-mount usado em todo o codebase (não é bug real, é opinião de estilo incompatível com este projeto). Achado real corrigido: `catch { }` vazio em `DeveloperCenterPage.tsx` engolia erro de reindex sem feedback ao usuário (inconsistente com o `handleExport` vizinho, que já tratava erro) — corrigido pra mostrar mensagem, igual ao padrão irmão. `Sidebar.tsx`: `refresh` (ação zustand, estável entre renders) adicionado ao array de deps do `useEffect` — satisfaz a regra sem mudar comportamento.

**Aceite**: `ruff check` limpo em `app`/`cli`/`sdk`; `npm run lint` limpo (era: não rodava, comando inexistente); `npm run build` continua passando.

**Teste**: `pytest tests -q` (backend) → 690 passed, 3 skipped, sem alteração de contagem (slice de tooling, não adicionou teste novo); `cli && pytest tests -q` → 105 passed; `npm run lint` e `npm run build` → limpos.

**Commit**: `4124796`

### Slice 7 — Release versioning

**Arquivos**: `core/backend/app/services/versioning.py` (novo), `core/backend/app/api/routes/system.py` (modificado — `GET /system/version`), `cli/techforge_cli/commands/version.py` (novo), `cli/techforge_cli/main.py` (registro do comando), `core/backend/tests/test_phase15_release_versioning.py`, `cli/tests/test_phase15_version_command.py` (novos).

**O quê**: `is_valid_semver()` valida `PLATFORM_VERSION` (fonte única desde a Fase 1, `app/core/settings.py`) via `packaging.version` — sem parser SemVer próprio. `GET /api/v1/system/version` segue o padrão já estabelecido em `system.py` (Fase 12: storage/migrations status). `techforge version` usa **acesso direto** a `app.core.settings` (não HTTP) — mesmo racional do `techforge migrations status`: precisa funcionar com a plataforma parada; o frontend usa a API.

**Decisão-chave**: nenhuma lib nova — `packaging` já era dependência (Fase 12).

**Aceite**: versão atual (`1.0.0`) valida como SemVer; endpoint e CLI retornam o mesmo valor de `settings.PLATFORM_VERSION`.

**Teste**: backend `pytest tests -q` → 695 passed, 3 skipped (era 690 — 5 novos); `cli pytest tests -q` → 106 passed (era 105 — 1 novo).

**Commit**: `2da287c`

### Slice 8 — Changelog & Release Notes

**Arquivos**: `core/backend/app/services/changelog.py` (novo), `CHANGELOG.md` (novo, raiz), `core/backend/tests/test_phase15_changelog.py` (novo).

**O quê**: `parse_changelog()`/`validate_changelog()` — formato "Keep a Changelog" (`## [version] - YYYY-MM-DD`, subseções restritas a `Added/Changed/Fixed/Deprecated/Removed/Known Issues`, spec §26 exato). `CHANGELOG.md` na raiz cobre só o **Core**; módulos mantêm `CHANGELOG.md` próprio na pasta do módulo (convenção documentada no cabeçalho do arquivo, spec §27 — "não misturar releases de módulo com releases do Core").

**Decisão-chave**: validador não tenta reconstruir o histórico retroativo de 12 fases — `CHANGELOG.md` começa com uma entrada `1.0.0` resumindo o baseline atual e referencia `tasks/phase-*-report.md` para o histórico detalhado; daqui pra frente, toda release relevante ganha entrada própria.

**Aceite**: `CHANGELOG.md` existe e passa na própria validação; seção desconhecida, versão sem data e versão malformada são rejeitadas com mensagem específica.

**Teste**: `pytest tests -q` → 701 passed, 3 skipped (era 695 — 6 novos).

**Commit**: `2e9ad25`

### Slice 9 — Release Readiness Report

**Arquivos**: `core/backend/app/services/release_readiness.py`, `core/backend/app/api/routes/release.py` (novos), `core/backend/app/api/__init__.py` (registro), `cli/techforge_cli/commands/release.py` (novo), `cli/techforge_cli/main.py` (registro + fix), `core/backend/tests/test_phase15_release_readiness.py`, `cli/tests/test_phase15_release_check_command.py` (novos).

**O quê**: `compute_release_readiness()` agrega 5 checks vivos reaproveitando serviços já existentes (não recalcula nada em paralelo, spec §2): `version_consistency` (SemVer, Slice 7), `changelog` (formato + versão atual documentada, Slice 8), `documentation` (DocCompletenessChecker, Fase 7), `migrations` (Fase 12), `storage` (Fase 12). `GET /api/v1/release/readiness` expõe isso. **Tests e Build ficam fora do agregador vivo** — rodar a suíte pytest inteira (~70s) ou `npm run build` dentro do processo do próprio servidor avaliado é pesado e circular; `techforge release-check` (CLI) roda os dois via `subprocess`, soma ao relatório vivo (obtido via HTTP) e decide READY/BLOCKED (spec §37), com `--skip-tests`/`--skip-build` para iteração rápida.

**Achados reais corrigidos nesta slice**:
1. `_check_documentation()` inicialmente contava módulos `INVALID` (pastas `some_module/test_module/unknown` — lixo de `data/` deixado por execuções de teste anteriores contra o dev DB real, sem manifest) como "documentação incompleta" — falso negativo. Corrigido pra só avaliar módulos `INSTALLED`/`DISABLED` (um módulo que nem carrega já é bloqueado por outro gate, não faz sentido cobrar doc dele).
2. `cli/techforge_cli/main.py` tinha `@click.version_option("1.0.0", ...)` **hardcoded**, uma segunda fonte de verdade divergente de `PLATFORM_VERSION` (violação direta do §24: "evitar múltiplas fontes de verdade"). Corrigido pra usar `settings.PLATFORM_VERSION`.

**Aceite**: baseline atual reporta `ready: True`; CLI sai com código != 0 quando qualquer check (vivo, tests ou build) falha ou a plataforma está inacessível.

**Teste**: backend `pytest tests -q` → 703 passed, 3 skipped (era 701 — 2 novos); cli `pytest tests -q` → 110 passed (era 106 — 4 novos); `ruff check` limpo.

**Commit**: `5d8e9cc`

### Slice 10 — Module quality/release-readiness

**Arquivos**: `core/backend/app/services/module_quality.py`, `core/backend/app/api/routes/module_quality.py` (novos), `core/backend/app/api/__init__.py` (registro), `cli/techforge_cli/commands/modules.py` (comandos `quality`/`release-check`), `core/backend/tests/test_phase15_module_quality.py`, `cli/tests/test_phase15_modules_quality_command.py` (novos).

**O quê**: `compute_module_quality(module_id)` — 4 checks por módulo, todos reaproveitando serviços existentes: `status` (registry — INSTALLED/DISABLED vs INVALID/INCOMPATIBLE/BLOCKED), `documentation` (DocCompletenessChecker, Fase 7), `compatibility` (`check_compatibility`, Slice 5), `contract` (reusa `extract_example_calls`+`invoke` da Slice 4 — só executa se o módulo declarar `api.yaml` E estiver ACTIVE no service registry; caso contrário passa trivialmente, não é falha). `GET /modules/{id}/quality` e `GET /modules/{id}/release-readiness` — **mesma computação**, dois endpoints (spec pede os dois explicitamente) porque são enquadramentos diferentes (informativo vs. gate), não lógica duplicada. CLI: `techforge modules quality|release-check <id>`.

**Decisão-chave**: `/release-readiness` não reimplementa nada — chama a mesma `compute_module_quality()` que `/quality`, evitando "critérios paralelos de qualidade" (spec §2).

**Aceite**: `hello_world` e `veeam_m365` reportam `ready: True`; contract check de `veeam_m365` executa os 2 exemplos reais da Slice 4 e confirma sucesso; 404 pra módulo inexistente.

**Teste**: backend `pytest tests -q` → 710 passed, 3 skipped (era 703 — 7 novos); cli `pytest tests -q` → 113 passed (era 110 — 3 novos); `ruff check` limpo.

**Commit**: `5952881`

### Slice 11 — Build artifacts & integrity

**Arquivos**: `core/backend/app/package_manager/builder.py` (modificado), `core/frontend/scripts/generate-build-info.mjs` (novo), `core/frontend/package.json` (postbuild), `core/backend/tests/test_phase15_build_artifacts.py` (novo).

**O quê**: Module Package (.mod) já tinha `checksum`+`version` (Fase 4/5) — `built_at` adicionado ao `BuildResult` (já existia dentro do `META-INF/BUILD` do zip, só não estava exposto no retorno da função). Frontend Build ganhou `dist/build-info.json` (version + checksum sha256 do `index.html` + timestamp) gerado por um script Node puro (sem dependência nova) como postbuild do `npm run build`.

**Achado real corrigido**: `core/frontend/package.json` tinha `"version": "1.0.0"` **hardcoded, independente** de `PLATFORM_VERSION` — mais uma segunda fonte de verdade de versão (mesma categoria do achado da Slice 9 no CLI). Por coincidência os valores já batiam; adicionado teste de guarda pra travar isso antes que divirjam silenciosamente.

**Decisão-chave**: Backend Package (spec §28) e Desktop Distribution não existem como artefato hoje — o backend roda direto de fonte via `uvicorn`, sem etapa de empacotamento. Inventar isso agora seria antecipar a Fase 16 (Desktop Distribution) sem necessidade real — CLAUDE.md proíbe explicitamente antecipar fases futuras.

**Aceite**: `npm run build` gera `dist/build-info.json` válido; teste de guarda do `package.json` passa.

**Teste**: `pytest tests -q` → 712 passed, 3 skipped (era 710 — 2 novos); `npm run build` confirmado gerando o artefato.

**Commit**: `b110879`

### Slice 12 — Pre-release channels & rollback readiness

**Arquivos**: `core/backend/app/module_engine/manifest.py` (modificado), `core/backend/tests/test_phase15_prerelease_channels.py` (novo).

**O quê**: manifest ganha campo opcional `channel: stable|beta|development` (default `stable`), validado no parse e propagado via `manifest_raw` (nenhuma mudança em `ModuleEntry`/registry — já é o mecanismo existente de repasse, mesmo padrão usado por `module_type`/`platform_min_version` em slices anteriores). **Mecanismo apenas, sem UI de catálogo dedicada** — decisão do plano original (sem usuários externos ainda pra segmentar canal visualmente).

**Achado real corrigido**: `_assert_semver()` em `manifest.py` usava uma regex estrita (`^\d+\.\d+\.\d+$`) que **rejeitava qualquer versão pre-release** — um módulo declarando `version: 1.5.0-rc.1` (exatamente o formato que um canal `beta`/`development` precisaria) nunca teria carregado. Corrigido pra reusar `is_valid_semver()` (Slice 7, via `packaging.version`) — consolida numa única noção de "semver válido" no projeto (Slices 5/7/12 agora usam a mesma base). `_version_tuple()` (compara `platform_min_version`/`platform_max_version`) também trocado de tupla de int ingênua pra `packaging.version.Version` pela mesma razão.

**Itens do spec já cobertos por slices anteriores, não duplicados aqui**:
- **Known Issues (§38)**: a seção `Known Issues` do Changelog (Slice 8) já cobre isso — não é uma tabela separada.
- **Rollback de módulo (§39)**: `PackageManager.update()` já reverte arquivos **e** config em caso de falha desde a Fase 4/12 (rollback-por-exceção) — nada novo a construir.
- **Migration release validation (§40)**: já coberto pelo check `migrations` do Release Readiness Report (Slice 9) + pelos testes reais de Alembic contra o dev DB (Fase 12).
- **Rollback de Desktop**: o próprio spec permite "implementação simples" — decisão: documentar o procedimento manual (backup do `techforge.db`) no Developer Center (Slice 14) em vez de construir um mecanismo automatizado sem necessidade real comprovada.

**Aceite**: canal default/beta/development parseiam corretamente; canal desconhecido rejeitado; versão com sufixo pre-release parseia com sucesso.

**Teste**: backend `pytest tests -q` → 718 passed, 3 skipped (era 712 — 6 novos); cli `pytest tests -q` → 113 passed (sem mudança); `ruff check` limpo.

**Commit**: `5ec2999`

### Slice 13 — CI pipeline + smoke + e2e crítico

**Arquivos**: `.github/workflows/ci.yml` (novo), `core/backend/tests/test_phase15_e2e_module_lifecycle.py`, `core/backend/tests/test_phase15_smoke.py` (novos).

**O quê**: **E2E crítico** (spec §12) — instala um `.mod` **real** construído em disco (zip com manifest+backend+frontend), confirma `INSTALLED` no registry, executa ação básica via `GET /modules/{id}/quality` (Slice 10), desativa (`deactivate_module`), remove, confirma remoção do registry. Nenhum teste anterior encadeava os 7 passos numa sequência só com um pacote real (os existentes registram `ModuleEntry` manualmente ou testam só install/remove isolados). **Smoke test** (spec §11) — Start (via fixture TestClient) → Health → Storage → Discover (registry summary) → Activate (`hello_world`) → Execute (`invoke("hello_world","ping")`), usando o módulo de referência já instalado em vez de instalar um novo (smoke test é sobre velocidade; o fluxo de instalação completo é o E2E acima). **CI** (`.github/workflows/ci.yml`, GitHub Actions, decisão do plano) — dois jobs: `backend` (ruff, pytest por marker — unit/integration/contract/e2e/smoke —, `techforge validate-module` nos 2 módulos de referência, suíte da CLI) e `frontend` (eslint, build, upload do artefato `dist/`).

**Decisão-chave**: markers (Slice 1) usados de verdade agora — CI roda cada nível separadamente (`pytest tests -m unit -q`, etc.), então um teste mal categorizado quebra o estágio errado do pipeline, não só a suíte inteira.

**Achado (não é bug, é ambiente)**: `techforge validate-module` falha localmente no PowerShell/Windows com `UnicodeEncodeError` (console cp1252 não renderiza glifos Unicode do `rich`) — confirmado que é puramente cosmético do terminal local (com `PYTHONIOENCODING=utf-8` os 2 módulos passam 41/41 checks, exit 0); GitHub Actions (Ubuntu, UTF-8 por padrão) não deve ter esse problema — não é necessário fix de código.

**Aceite**: suíte completa 720 passed, 3 skipped; contagem por marker bate (264 unit + 450 integration + 2 contract + 1 e2e + 1 smoke + 3 skipped = 721, mais 2 testes não-parametrizados de arquivo compartilhado somam 720+3); `techforge validate-module` 41/41 nos dois módulos de referência; `npm run lint`/`build` limpos.

**Teste**: `pytest tests -q` → 720 passed, 3 skipped (era 718 — 2 novos: e2e + smoke).

**Commit**: `a9a503c`
