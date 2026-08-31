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

### Slice 2 — `/ready` + erro de startup amigável

**Arquivos**: `core/backend/app/api/routes/platform.py` (modificado), `core/backend/app/observability/diagnostic_codes.py` (modificado, +`TF-STARTUP-001`/`TF-STARTUP-002`), `core/backend/tests/test_phase16_ready.py` (novo), `launcher/techforge_launcher/__init__.py` (modificado), `core/backend/tests/test_phase6_launcher.py` (modificado).

**O quê**: `GET /api/v1/platform/ready` — distinto de `/health` (só confirma que o processo responde): fica 503 até `RuntimeState.READY` (boot completo: DB + Module Loader + Service Registry), 200 depois. `wait_backend()` do launcher passou a fazer polling de `/ready` em vez de `/platform/status`. Mensagens de falha de startup (backend/frontend) agora usam `_startup_failure_message()`: separa mensagem de usuário de detalhe técnico, sempre inclui um Diagnostic Code (reaproveita o catálogo da Fase 14, `TF-STARTUP-001`/`002`, fallback `TF-STARTUP-000` se o import do backend falhar) e nunca mostra stack trace — detalhe técnico completo vai só pro `launcher.log`.

**Decisão-chave**: achado real durante o TDD — o teste inicial de `/ready` dependia da ordem de execução da suíte (`runtime` é singleton global; `fire_shutdown` de um teste anterior deixava `state=STOPPED`, e `fire_startup` só promove `BOOTSTRAPPING→READY`, nunca `STOPPED→READY`). Corrigido fixando o estado via `monkeypatch` em vez de assumir a ordem — evita um teste flaky, não mexe no `TechForgeRuntime` (fora de escopo desta fase).

**Aceite**: `/ready` 503 fora do estado READY, 200 dentro; launcher para de tentar erroneamente contra `/platform/status`; mensagem de erro inclui código e nunca traceback.

**Teste**: `pytest tests -q` → 870 passed, 3 skipped (era 866 — 4 testes novos). `ruff check core/backend/app cli sdk` limpo. Verificado ao vivo: `techforge start` real → `curl /api/v1/platform/ready` → `{"ready":true,"state":"ready"}` HTTP 200.

**Commit**: `a55bd4d`

### Slice 3 — Single instance: focus existing

**Arquivos**: `launcher/techforge_launcher/__init__.py` (modificado), `core/backend/tests/test_phase6_launcher.py` (modificado).

**O quê**: `_focus_existing_instance()` — ao detectar instância viva, reabre a URL correta (`BACKEND_URL` em modo desktop/estático, `FRONTEND_URL` em modo dev, lido do `frontend_mode` persistido em `state.json`) em vez de só logar/retornar "já está em execução". Sem janela nativa própria, "focar" = reabrir a mesma URL — o browser/SO tipicamente reaproveita a aba já aberta.

**Decisão-chave**: nenhuma — implementação direta conforme decidido no plano (a decisão de não usar WebView shell já tinha sido tomada antes do slice).

**Aceite**: `start()` com instância viva chama `webbrowser.open` com a URL certa pro modo ativo (estático ou dev), sem tentar subir um segundo backend.

**Teste**: `pytest tests -q` → 872 passed, 3 skipped (era 870 — 2 testes novos). `ruff check core/backend/app cli sdk` limpo. Verificado ao vivo: `techforge start` duas vezes seguidas com a plataforma real rodando → segunda chamada loga "focusing existing instance" e não sobe segundo backend (`launcher.log` real).

**Checkpoint 1**: suíte completa ✅ + `techforge start/stop/status` manual com os paths novos em uso ✅ (dev tree, sem regressão).

**Commit**: _(pendente)_

