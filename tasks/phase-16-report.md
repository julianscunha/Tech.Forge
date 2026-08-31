# Relatório — Fase 16: Desktop Distribution & User Experience

Status: EM ANDAMENTO.
Plano: `tasks/phase16-plan.md`.

## Slices

### Slice 1 — Paths oficiais por SO (platformdirs)

**Arquivos**: `core/backend/app/core/paths.py` (novo), `core/backend/app/core/settings.py` (modificado), `core/backend/tests/test_phase16_paths.py` (novo), `core/backend/requirements.txt` (+ `platformdirs==4.3.6`).

**O quê**: `install_dir()` (código, cálculo idêntico ao antigo `BASE_DIR`) e `user_data_dir()` — resolve em ordem: env var `TECHFORGE_DATA_DIR` (override explícito) → mesmo diretório do código se houver `.git` (árvore de dev, preserva 100% do comportamento atual) → `platformdirs.user_data_dir("TechForge", "TechForge")` (produção instalada, ex. `%LOCALAPPDATA%\TechForge\TechForge` no Windows). `settings.py` passou a derivar `DATABASE_URL`, `MODULES_INSTALLED_PATH`, `MODULES_REPOSITORY_PATH`, `MODULES_CACHE_PATH`, `LOGS_PATH` e o `.env` de `USER_DATA_DIR` em vez de `BASE_DIR`; `FRONTEND_DIST_PATH` continua em `BASE_DIR` (é artefato de código, não dado do usuário).

**Decisão-chave**: detecção de dev tree via presença de `.git` (não uma env var manual) — mantém `pytest`/`techforge start` local funcionando sem nenhuma configuração nova, e só desvia pro diretório de dados do SO quando o app estiver realmente instalado fora do repositório (sem `.git` no diretório de instalação).

**Aceite**: em árvore de dev, `USER_DATA_DIR == BASE_DIR` (confirmado manualmente); fora dela (simulado via monkeypatch), resolve para o diretório `platformdirs`; env var sempre vence, dentro ou fora da dev tree.

**Teste**: `pytest tests -q` → 866 passed, 3 skipped (era 861 — 5 testes novos). `ruff check core/backend/app cli sdk` limpo.

**Commit**: `d9fa3a6`

