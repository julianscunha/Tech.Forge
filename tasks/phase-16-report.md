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

**Commit**: `d93c5b8`

### Slice 4 — Safe Mode

**Arquivos**: `core/backend/app/module_engine/plugin_loader.py` (modificado), `core/backend/app/schemas/registry.py` (modificado, +`safe_mode`), `core/backend/app/api/routes/platform.py` (modificado), `core/backend/tests/test_phase16_safe_mode.py` (novo), `launcher/techforge_launcher/__init__.py` (modificado, `start(safe_mode=...)`), `launcher/techforge_launcher/__main__.py` (modificado, `--safe-mode`), `cli/techforge_cli/commands/platform.py` (modificado, `safe_mode_cmd`), `cli/techforge_cli/main.py` (modificado), `core/backend/tests/test_phase6_launcher.py` / `cli/tests/test_phase6_logs_dev.py` (modificados), `core/frontend/src/types/index.ts` + `core/frontend/src/pages/DashboardPage.tsx` (badge de Safe Mode).

**O quê**: `TECHFORGE_SAFE_MODE=true` faz `mount_module_routers()` (não `ModuleLoader.scan_installed()` — correção em relação ao plano original, ver decisão-chave) retornar cedo sem montar nenhum `entry_backend`, mas o registry continua populado normalmente (módulos aparecem em `/platform/status`/Dashboard como instalados, só sem rota própria respondendo). `GET /platform/status` ganhou `safe_mode: bool`. `techforge safe-mode` (CLI) → launcher `start --safe-mode` → propaga `TECHFORGE_SAFE_MODE=true` só pro processo do backend spawnado (não para o processo do launcher). Dashboard mostra um badge "Safe Mode — nenhum módulo carregado" quando ativo.

**Decisão-chave**: o plano original apontava `ModuleLoader.scan_installed()` como o lugar a gatear — errado. `scan_installed()` só popula o registry (metadados); quem de fato importa e monta `entry_backend` como rota FastAPI é `plugin_loader.mount_module_routers()`, chamado depois no `lifespan()`. Gatear ali (não no loader) é o que permite exatamente o comportamento pedido pelo spec: módulos continuam visíveis/gerenciáveis (desativar/remover) mas nenhum código de módulo roda.

**Aceite**: com Safe Mode, nenhum módulo monta rota (verificado: `hello_world/ping` → 404), mas aparece no registry (`modules_installed` > 0); sem a flag, tudo volta ao normal num restart simples.

**Teste**: `pytest tests -q` (backend) → 877 passed, 3 skipped (era 872 — 5 novos). `pytest tests -q` (cli) → 114 passed (era 113 — 1 novo). `ruff check core/backend/app cli sdk` limpo (1 import mal ordenado auto-corrigido pelo próprio ruff). `npm run lint`/`npm run build` (frontend) limpos. Verificado ao vivo: `techforge safe-mode` real → `curl /platform/status` → `safe_mode: true`, `modules_installed: 3`; `curl /modules/hello_world/ping` → 404; `techforge stop` + `techforge start` normal → `safe_mode: false`, `ping` → 200 de novo.

**Commit**: `2c79c5b`

### Slice 5 — `techforge repair-check`

**Arquivos**: `core/backend/app/module_trust/integrity.py` (modificado, extraído `diff_manifests()`), `core/backend/app/module_trust/core_repair.py` (novo), `core/backend/tests/test_phase16_repair_check.py` (novo), `cli/techforge_cli/commands/repair.py` (novo), `cli/tests/test_phase16_repair_check.py` (novo), `cli/techforge_cli/main.py` (modificado), `.gitignore` (+ `/core-integrity.json`).

**O quê**: reaproveita o integrity manifest da Fase 10 (hash SHA-256 por arquivo) aplicado ao próprio código do Core, não a módulos. `techforge repair-check --generate` grava `core-integrity.json` na raiz da instalação a partir do estado atual de `core/backend/app`, `cli/techforge_cli`, `sdk/python/techforge_sdk`, `launcher/techforge_launcher` (não a árvore inteira — excluiria `.venv`, `node_modules`, `.git`, `modules/installed`, que não são código distribuído). `techforge repair-check` (sem flag) compara o manifesto contra o disco agora e reporta OK, ou lista arquivo por arquivo o que está faltando/modificado/inesperado. Só verifica — nunca tenta restaurar nada (spec §33).

**Decisão-chave**: extraí `diff_manifests(expected, current)` de dentro de `verify_integrity()` (Fase 10) em vez de duplicar a lógica de prioridade de status (MISSING > MODIFIED > UNEXPECTED > VALID) — `core_repair.py` reusa a mesma função para o caso "Core inteiro" (múltiplos diretórios compostos num único mapa de arquivos), sem reescrever a comparação. Manifesto do Core é gerado a frio (`--generate`, tipicamente no packaging/Slice 7), nunca implicitamente em runtime — gerar automaticamente permitiria a um código já adulterado "aprovar a si mesmo".

**Aceite**: sem manifesto → aviso amigável + exit code 2; manifesto válido → OK + exit 0; arquivo alterado → reporta `MODIFIED` + exit 1; arquivo removido → reporta `MISSING_FILE`.

**Teste**: `pytest tests -q` (backend) → 881 passed, 3 skipped (era 877 — 4 novos). `pytest tests -q` (cli) → 118 passed (era 114 — 4 novos). `ruff check core/backend/app cli sdk` limpo. Verificado ao vivo no repo real: gerei o manifesto real, rodei `repair-check` (OK), adulterei `app/main.py` de propósito → detectou `MODIFIED` com o caminho exato, restaurei via `git checkout` → voltou a OK. Manifesto de teste removido do disco depois (é artefato local, agora no `.gitignore`).

**Nota**: reproduzido de novo o bug conhecido (`tasks/phase-audit.md`, Fase 15) de encoding cp1252 do `rich` no console PowerShell/Windows ao imprimir `⚠`/`✗` — não é regressão desta fase, usei o mesmo workaround (`PYTHONIOENCODING=utf-8`) já documentado.

**Commit**: `6d8dc58`

### Slice 6 — Developer Mode real (frontend)

**Arquivos**: `core/backend/app/services/system_diagnostics.py` (modificado, +`paths`), `core/backend/app/api/routes/registry.py` (modificado, +`POST /registry/rescan`), `core/backend/tests/test_phase16_developer_mode.py` (novo), `core/frontend/src/types/index.ts` (modificado), `core/frontend/src/lib/api.ts` (modificado, +`registryApi.rescan`), `core/frontend/src/pages/SettingsPage.tsx` (modificado, card "Developer Mode").

**O quê**: `SystemDiagnosticService.snapshot()` (Fase 14) ganhou `platform.paths.{install_dir,user_data_dir}` (Slice 1), já reexposto de graça em `/diagnostics/health`. `POST /api/v1/registry/rescan` — reusa `PackageManager._hot_reload()` (scan + doc reindex + service registry sync, mesmo caminho corrigido nesta sessão pro bug de reinstalação sem restart) e depois `mount_module_routers(app)` pra montar routers de módulos ainda não montados. `SettingsPage` ganhou um card "Developer Mode" com toggle (mesmo `devmode.ts`, agora consumido também fora de `ModulesPage`) — quando ativo, mostra os dois paths reais e um botão "Recarregar módulos" que chama o rescan e mostra o resultado.

**Decisão-chave**: nenhuma API de dados nova de verdade — `/diagnostics/health` já existia e só ganhou um campo; o único endpoint genuinamente novo é o rescan, que não duplica lógica (reusa `_hot_reload` + `mount_module_routers`, ambos já existentes de fases anteriores).

**Aceite**: com Developer Mode desligado (padrão), nenhuma seção de paths/reload aparece; ligado, mostra os paths reais e o rescan funciona sem reiniciar o processo.

**Teste**: `pytest tests -q` → 883 passed, 3 skipped (era 881 — 2 novos). `ruff check core/backend/app cli sdk` limpo. `npm run lint`/`npm run build` limpos. Verificado ao vivo: `techforge start` real → `curl /diagnostics/health` → paths reais retornados; `curl -X POST /registry/rescan` → `{"scanned":6,"installed":3,"invalid":3,"routers_mounted":[]}` (idempotente, nenhum router novo pois já estavam todos montados).

**Commit**: _(pendente)_

