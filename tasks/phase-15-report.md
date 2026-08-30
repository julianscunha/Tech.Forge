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

**Commit**: (a seguir)
