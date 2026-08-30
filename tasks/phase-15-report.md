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

**Commit**: (a seguir)

**Commit**: (a seguir)
