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
