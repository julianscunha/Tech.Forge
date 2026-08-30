# Relatório — Fase 14: Observability, Telemetry & Diagnostics

Status: FECHADA — 2026-08-30.
Plano: `tasks/phase14-plan.md`.

## Slices

### Slice 1 — Logger central + Log Context

**Arquivos**: `core/backend/app/observability/{__init__,context,logging_setup}.py` (novos), `core/backend/app/main.py`, `core/backend/app/core/settings.py`, `core/backend/tests/test_phase14_logging.py` (novo).

**O quê**: `configure_logging()` substitui `logging.basicConfig` — console em formato humano (inalterado, capturado pelo launcher em `logs/backend.log`) + novo handler gravando `logs/backend.jsonl` em JSON-lines. Log Context via `contextvars` (`bind_log_context`/`get_log_context`) propaga `module_id`/`execution_id`/etc. sem exigir `extra=` manual em todo call site.

**Decisão-chave**: dois canais paralelos (console humano + arquivo estruturado) em vez de escolher um só — preserva a experiência de debug local existente enquanto entrega o formato parseável por ferramenta externa que a fase pede.

**Teste**: `pytest tests -q` → 741 passed, 3 skipped (era 730).

**Commit**: `52f26e3`

### Slice 2 — Nível mínimo de log configurável

**Arquivos**: `core/backend/app/observability/logging_setup.py`, `core/backend/app/core/settings.py`.

**O quê**: `configure_logging()` aceita `level` (console) e `file_level` (arquivo) independentes — `LOG_LEVEL`/`LOG_FILE_LEVEL` em `settings.py`.

**Teste**: `pytest tests -q` → 743 passed, 3 skipped.

**Commit**: `bea58e2`

### Slice 3 — Redação por padrão de chave

**Arquivos**: `core/backend/app/security/redaction.py`, `core/backend/tests/test_phase14_redaction.py` (novo).

**O quê**: `SecretRedactionFilter` (Fase 12 §28) só mascarava valor **já conhecido** registrado no SecretStore. Generalizado pra também mascarar por **nome de campo** (`password`, `api_key`, `token`, `secret`, `private_key`, `credential`) em formato `key=value` ou JSON-style, case-insensitive — não depende mais só da disciplina do desenvolvedor de registrar o valor primeiro.

**Teste**: `pytest tests -q` → 752 passed, 3 skipped.

**Commit**: `83dbafe`

### Slice 4 — Rotação + retenção configurável de log

**Arquivos**: `core/backend/app/observability/{logging_setup,retention}.py`, `core/backend/app/core/settings.py`, `core/backend/app/main.py`.

**O quê**: `backend.jsonl` passa a usar `RotatingFileHandler` (`LOG_MAX_BYTES`/`LOG_BACKUP_COUNT`, default 10MB × 5). Retenção por nível (`LOG_RETENTION_DAYS`, default DEBUG 7d / INFO-WARNING 30d / ERROR-CRITICAL 90d, tudo configurável) aplicada por `cleanup_old_logs()` no startup, síncrono — sem agendador.

**Teste**: `pytest tests -q` → 757 passed, 3 skipped.

**Commit**: `28795f0`

### Slice 5 — EventBus unificado

**Arquivos**: `core/backend/app/observability/events.py` (novo), `core/backend/app/runtime/__init__.py`, `core/backend/app/package_manager/operation_log.py`, `core/backend/app/module_engine/journal.py`.

**O quê**: existiam 4 sistemas de evento paralelos sem unificação (`logging` solto, `RuntimeEvent`, `OperationLog`, `LoaderJournal`) — exatamente o que o spec (§12) pede pra não repetir. `EventBus` é pub/sub in-process, síncrono, sem histórico próprio de propósito: os 3 sistemas existentes continuam sendo a fonte de leitura de cada domínio, só ganharam uma chamada adicional de `publish()` no próprio write path — APIs de leitura 100% inalteradas.

**Decisão-chave**: não guardar histórico no bus em si — reaproveitar o que já existe evita uma 5ª ferramenta paralela.

**Teste**: `pytest tests -q` → 766 passed, 3 skipped.

**Commit**: `68c7ea0`

### Slice 6 — MetricEmitter

**Arquivos**: `core/backend/app/observability/metrics.py` (novo).

**O quê**: Counter/Gauge/Histogram/Timer em memória, sem I/O, sem dependência nova. Histogram usa janela limitada de amostras (`deque(maxlen=1000)`) pra min/max/avg — count/sum continuam exatos; bounded por design (spec §37).

**Teste**: `pytest tests -q` → 777 passed, 3 skipped.

**Commit**: `cff865c`

### Slice 7 — Métricas iniciais instrumentadas

**Arquivos**: `core/backend/app/runtime/__init__.py`, `core/backend/app/module_engine/journal.py`, `core/backend/app/dependency_engine/validator.py`, `core/backend/app/service_registry/invoker.py`.

**O quê**: as 7 métricas do spec (§10) conectadas nos pontos reais: `platform_startups` (fire_startup), `runtime_errors` (transição DEGRADED), `module_loads` (loader_journal.store), `dependency_failures` (DependencyValidator.validate), `module_executions`/`execution_duration`/`execution_failures` (invoker.invoke — único ponto real de chamada de capacidade hoje).

**Teste**: `pytest tests -q` → 785 passed, 3 skipped.

**Commit**: `4292b8b`

### Slice 8 — execution_id + correlação básica

**Arquivos**: `core/backend/app/module_runtime/context.py`, `core/backend/app/service_registry/invoker.py`, `core/backend/tests/test_phase14_correlation.py` (novo).

**O quê**: `execution_id` adicionado a `ModuleExecutionContext` como campo **novo**, separado de `runtime_id` (mantido como estava — spec usa nomes diferentes do que já existia no código; decisão foi não renomear pra não quebrar chamadores/testes da Fase 9/12). Correlação real fica em `invoker.invoke()`: `module_id`/`execution_id` amarrados via `bind_log_context()` durante toda a chamada (sucesso e falha).

**Teste**: `pytest tests -q` → 789 passed, 3 skipped.

**Commit**: `d124764`

### Slice 9 — Execution History persistida

**Arquivos**: `core/backend/app/models/execution_history.py`, `core/backend/app/services/execution_history.py`, `core/backend/alembic/versions/0004_execution_history.py` (novos), `core/backend/app/service_registry/invoker.py`, `core/backend/app/main.py`.

**O quê**: `ModuleExecutionResult` (Fase 9) descrevia a forma certa mas nunca era persistido. Tabela dedicada + retenção configurável (`EXECUTION_HISTORY_RETENTION_DAYS`, default 90d). Persistência ligada em `invoker.invoke()` — como a função é síncrona por design (chamada direta entre módulos, sem round-trip HTTP), a escrita usa `asyncio.run()` num helper isolado, com guarda pra nunca tentar isso se já estiver dentro de um event loop rodando (observability nunca pode quebrar a execução real, spec §37).

**Achado durante o slice**: `test_phase12_migrations_status_api.py` tinha `"0003"` hardcoded como head/current esperado — precisou virar `"0004"`.

**Teste**: `pytest tests -q` → 797 passed, 3 skipped.

**Commit**: `efb7b50`

### Slice 10 — Error Registry

**Arquivos**: `core/backend/app/models/error_registry.py`, `core/backend/app/services/error_registry.py`, `core/backend/app/observability/errors.py` (novos), `core/backend/alembic/versions/0005_error_registry.py`, `core/backend/app/service_registry/invoker.py`, `core/backend/app/runtime/__init__.py`, `core/backend/app/package_manager/manager.py`.

**O quê**: captura automática nos 3 pontos-chave (§19/§25): falha de execução, falha de dependência, erro de runtime. `capture_error()` (sync) e `capture_error_async()` (pra quem já está numa função async, como `PackageManager.install()`) — os dois nunca lançam.

**Achado durante o slice**: mesma situação do slice anterior, migration nova exigiu bump de `"0004"` → `"0005"` no teste de migrations status; e um teste próprio (`test_records_duration_into_histogram`) que usava `time.sleep(0.01)` real ficou instável sob carga — trocado por `time.monotonic` mockado.

**Teste**: `pytest tests -q` → 805 passed, 3 skipped.

**Commit**: `ee95590`

### Slice 11 — Diagnostic Codes

**Arquivos**: `core/backend/app/observability/diagnostic_codes.py` (novo), `core/backend/app/models/error_registry.py`, `core/backend/app/services/error_registry.py`, `core/backend/alembic/versions/0006_error_registry_code.py`.

**O quê**: catálogo inicial mapeando as 3 origens já capturadas (`execution`/`dependency`/`runtime`) pra códigos estáveis (`TF-EXECUTION-001`, `TF-DEPENDENCY-001`, `TF-RUNTIME-001`). Deliberadamente pequeno — só origens reais.

**Correção de raiz**: `test_migrations_status_reports_head_and_current_up_to_date` já tinha precisado de bump 2 vezes nesta fase (0003→0004→0005→0006) — trocado o valor hardcoded por comparação contra `head_revision()` real. Nunca mais precisa ser editado ao adicionar uma migration.

**Teste**: `pytest tests -q` → 811 passed, 3 skipped.

**Commit**: `33cb698`

### Slice 12 — SystemDiagnosticService

**Arquivos**: `core/backend/app/services/system_diagnostics.py` (novo).

**O quê**: consolida Health (Fase 1) + Storage (Fase 12) + Runtime (Fase 6) + Module Health (Fase 9, `module_runtime_registry.list_all()`) num serviço único — reaproveita `ModuleService`/`CategoryService`/`storage_provider` existentes, nenhuma lógica duplicada. Sem `/ready` novo — não se aplica a Desktop single-instância.

**Teste**: `pytest tests -q` → 813 passed, 3 skipped.

**Commit**: `3da7420`

### Slice 13 — Failure correlation

**Arquivos**: `core/backend/app/services/failure_correlation.py` (novo).

**O quê**: `correlate(error_id)` monta a cadeia Error → Module → Execution → Dependency → eventos recentes, reaproveitando Execution History, `module_runtime_registry`, `dependency_engine._dependents_of`, `OperationLog` e `RuntimeEvent`.

**Achado durante o slice**: teste próprio usava `execution_id` fixo contra o banco real da app (`client` fixture não isola DB) — rodar o teste 2x colidia com a constraint `unique`. Trocado por `uuid4()` por execução.

**Teste**: `pytest tests -q` → 816 passed, 3 skipped.

**Commit**: `3c05df0`

### Slice 14 — Startup diagnostics

**Arquivos**: `core/backend/app/observability/startup_diagnostics.py` (novo), `core/backend/app/main.py`.

**O quê**: `time_step()` (context manager) mede a duração de cada etapa do lifespan — `database_init`, `history_cleanup`, `module_loader_scan`, `plugin_loader_mount`, `doc_indexer`, `registry_sync_and_integrity`, `service_registry_sync`, `runtime_state_rebuild`. Estado do boot mais recente apenas, não histórico.

**Teste**: `pytest tests -q` → 822 passed, 3 skipped.

**Commit**: `d93738a`

### Slice 15 — Diagnostic snapshot + export

**Arquivos**: `core/backend/app/services/diagnostic_export.py` (novo).

**O quê**: `DiagnosticExportService` monta um snapshot completo (System Diagnostics + startup diagnostics + últimos 20 erros + últimas 20 execuções) e formata em JSON ou TXT.

**Teste**: `pytest tests -q` → 825 passed, 3 skipped.

**Commit**: `dfbf2cb`

### Slice 16 — Support Bundle sanitizado

**Arquivos**: `core/backend/app/services/support_bundle.py` (novo).

**O quê**: ZIP com `diagnostic_snapshot.json` + `platform_config.json` + `module_registry.json` + `dependency_graph.mmd` + `recent_logs.jsonl` (500 últimas linhas). Nunca inclui secrets/credenciais/private keys/dados de módulo: `platform_config` vem do mesmo `settings.model_dump()` já seguro pra `GET /api/v1/config` (Fase 12 §9); logs já saem redigidos em tempo de escrita, não precisa redigir de novo na leitura.

**Teste**: `pytest tests -q` → 830 passed, 3 skipped.

**Commit**: `5390735`

### Slice 17 — Notifications integration + API/CLI

**Arquivos**: `core/backend/app/observability/notifications_bridge.py`, `core/backend/app/api/routes/diagnostics.py` (novos), `core/backend/app/api/__init__.py`, `core/backend/app/main.py`, `cli/techforge_cli/commands/diagnostics.py` (novo), `cli/techforge_cli/commands/{modules,platform}.py`, `cli/techforge_cli/main.py`.

**O quê**:
- Notifications (§31): `EventBus` → `NotificationService` só pra evento crítico de verdade (hoje: `runtime.degraded`). Dedup por título numa janela de 15min.
- API (§34): `GET /diagnostics`, `/diagnostics/health`, `/diagnostics/errors`, `/diagnostics/executions`, `POST /diagnostics/export`, `GET /modules/{id}/diagnostics|executions` — tudo reaproveitando os services dos slices anteriores.
- CLI (§35): `techforge diagnostics [health|errors|export]`, `techforge modules diagnostics <id>`, `techforge logs --follow/-f`.

**Decisão-chave**: `techforge logs --follow` em vez de restruturar `logs` num grupo com subcomando `tail` — não quebra a interface existente (`techforge logs --backend -n 50`).

**Aceite**: testado de ponta a ponta contra o sistema real rodando (start/diagnostics health/errors/export json+zip/modules diagnostics/stop).

**Teste**: `pytest tests -q` → 845 passed, 3 skipped; `cli pytest tests -q` → 113 passed.

**Commit**: `9e9075c`

### Slice 18 — Dashboard incrementado

**Arquivos**: `core/backend/requirements.txt` (+ `psutil`), `core/backend/app/services/{resource_usage,heaviest_modules}.py` (novos), `core/backend/app/api/routes/diagnostics.py`, 8 arquivos novos em `core/frontend/src/components/dashboard/`, `core/frontend/src/store/dashboardLayout.ts` (novo), `core/frontend/src/pages/DashboardPage.tsx`, `core/frontend/src/lib/{api,utils}.ts`, `core/frontend/src/types/index.ts`.

**O quê**: Dashboard ganha 5 cards novos — Module Failures, Blocked Dependencies, Recent Critical Events (navegam pra `/diagnostics`), Resources (CPU/memória via `psutil` nova dependência + disco via `shutil.disk_usage`, refresh 20s, expande inline com mini gráfico de barra/pizza em SVG feito à mão, sem lib de charting nova) e Heaviest Module (disco + duração média + taxa de falha — proxy real, não tenta CPU/memória por módulo). Customização: drag-and-drop HTML5 nativo pra reordenar todos os 9 cards, engrenagem com popover pra mostrar/ocultar — persistido via Zustand `persist`.

**Achado durante o slice**: CI quebrou no `ruff` (import não ordenado em `api/__init__.py`) — corrigido com `--fix` num commit separado (`d3ca672`).

**Teste**: `pytest tests -q` → 850 passed, 3 skipped; `npm run lint`/`build` limpos; CI verde (confirmado `psutil` instala corretamente no runner Ubuntu).

**Commit**: `d574de1` (+ fix `d3ca672`)

### Slice 19 — Frontend página System > Diagnostics

**Arquivos**: `core/frontend/src/pages/DiagnosticsPage.tsx` (novo), `core/frontend/src/AppRouter.tsx`, `core/frontend/src/components/layout/{Sidebar,AppShell}.tsx`, `core/frontend/src/lib/api.ts`, `core/frontend/src/types/index.ts`.

**O quê**: página `/diagnostics` — Health (banco/storage/runtime), Erros recentes, Execuções recentes, export (JSON/TXT/Support Bundle ZIP via download real de blob). Rota registrada, item "Diagnostics" na Sidebar (grupo Plataforma) e no mapa de help contextual.

**Teste**: `npm run lint`/`build` limpos; rota `/diagnostics` confirmada servindo 200 com o sistema real rodando; CI verde.

**Commit**: `44b6751`

### Slice 20 — Developer Center + AI Context + fechamento

**Arquivos**: `docs/developer-center/core/observability.md` (novo), `tasks/phase-audit.md`, `tasks/phase-14-report.md` (este documento).

**O quê**: documentação cobrindo logging/níveis/campos estruturados/dados sensíveis/métricas/eventos/diagnósticos/diagnostic codes/execution tracing, com exemplos de módulo. `category: arquitetura-core` (pasta `core/`) é suficiente pro `DocIndexer` auto-indexar — confirmado via `GET /api/v1/docs/list?category=architecture` com o sistema real rodando, artigo `core/observability` aparece com `order: 7`. AI Context (`GET /api/v1/docs/export/ai-context`) é gerado dinamicamente a partir de todos os docs por categoria — inclui o novo artigo automaticamente, sem arquivo manual.

**Regra final (spec) — verificação de ponta a ponta**:

| Item | Verificado |
|---|---|
| Logging | ✅ console humano + `logs/backend.jsonl` |
| Structured Logging | ✅ JSON-lines válido, `jq`-parseável |
| Log Context | ✅ `module_id`/`execution_id` propagados via contextvars durante `invoker.invoke()` |
| Sensitive Data | ✅ redação por valor conhecido + por padrão de chave (testes unitários dedicados) |
| Retention | ✅ `cleanup_old_logs()`/`ExecutionHistoryService.cleanup_old()`/`ErrorRegistryService.cleanup_old()`, todos rodando no startup real |
| Metrics | ✅ `metric_emitter.snapshot()` com as 7 métricas instrumentadas |
| Events | ✅ `EventBus` confirmado propagando `runtime.degraded`/`package_manager.*`/`module_loader.scan` |
| Diagnostic Snapshot | ✅ `GET /api/v1/diagnostics` real, dados reais (8 módulos instalados) |
| Module Diagnostics | ✅ `GET /api/v1/modules/hello_world/diagnostics` |
| Error Registry | ✅ entradas reais com `TF-EXECUTION-001`/`TF-RUNTIME-001` confirmadas via `techforge diagnostics errors` |
| Failure correlation | ✅ testado com dados reais (execution + module_runtime + dependents) |
| Export | ✅ JSON/TXT/ZIP baixados e inspecionados via CLI e curl |
| Support bundle sanitizado | ✅ ZIP confirmado sem `data/` de módulo, config sem chaves suspeitas |
| UI de Diagnostics | ✅ rota `/diagnostics` servindo 200 com o sistema real rodando |
| CLI | ✅ `techforge diagnostics health/errors/export`, `techforge modules diagnostics` — todos testados contra o servidor real |
| Todos os testes | ✅ 850 backend + 113 CLI passed |
| Build do Frontend | ✅ `npm run lint`/`build` limpos |

**Auditoria contra os 30 critérios do spec §40**:

| # | Critério | Status |
|---|---|---|
| 1 | Logging central existir | ✅ `configure_logging()` |
| 2 | Logs estruturados funcionarem | ✅ JSON-lines |
| 3 | Log Context propagar Module e Execution IDs | ✅ |
| 4 | Dados sensíveis forem redigidos | ✅ valor conhecido + padrão de chave |
| 5 | Rotação/retenção existir | ✅ log + execution history + error registry |
| 6 | Metrics abstraction existir | ✅ `MetricEmitter` |
| 7 | Eventos operacionais existirem | ✅ `EventBus` |
| 8 | Lifecycle reutilizar eventos | ✅ `RuntimeEvent`/`OperationLog`/`LoaderJournal` publicam no bus |
| 9 | Execution correlation existir | ✅ `execution_id` + Log Context |
| 10 | Diagnostic Snapshot funcionar | ✅ |
| 11 | System Diagnostics funcionar | ✅ |
| 12 | Module Diagnostics existir | ✅ |
| 13 | Error Registry existir | ✅ |
| 14 | Diagnostic Codes existirem | ✅ 3 códigos reais |
| 15 | Health e Readiness forem reutilizados | ✅ Health da Fase 1; sem `/ready` (decisão — não se aplica a Desktop) |
| 16 | Failure correlation funcionar | ✅ |
| 17 | Execution History existir | ✅ |
| 18 | Performance diagnostics existirem | ✅ métricas de duração + resource usage (CPU/mem/disco) |
| 19 | Startup diagnostics existirem | ✅ |
| 20 | Export diagnostics funcionar | ✅ JSON/TXT/ZIP |
| 21 | Support bundle for sanitizado | ✅ |
| 22 | Notifications integrar eventos relevantes | ✅ com dedup |
| 23 | Dashboard permanecer simples | ✅ 5 cards novos, sem virar NOC |
| 24 | APIs funcionarem | ✅ 9 endpoints novos |
| 25 | CLI funcionar | ✅ |
| 26 | Developer Center documentar observabilidade | ✅ `core/observability.md` |
| 27 | AI Context incluir convenções | ✅ auto-indexado, confirmado |
| 28 | Telemetria externa não ocorrer por padrão | ✅ nenhum exporter externo implementado |
| 29 | Todos os testes passarem | ✅ 850 + 113 |
| 30 | Core continuar leve | ✅ 1 dependência nova (`psutil`), zero no frontend |

**Limitações conhecidas**:
1. Diagnóstico por módulo (`get_diagnostics()` opcional, contrato pro módulo implementar) existe só no backend — sem seção dedicada na página do próprio módulo (ficou fora de escopo desta fase, ver decisão registrada no plano).
2. `techforge logs --follow` é polling simples (0.5s), não inotify/similar — suficiente pro volume de log de um Desktop, não pretende ser um `tail -f` de alta frequência.
3. `runtime_id` (Fase 9) e `execution_id` (Fase 14) coexistem como conceitos parecidos mas distintos — nomenclatura herdada, documentada mas não unificada (decisão consciente, ver plano).

**Teste final**: `pytest tests -q` → 850 passed, 3 skipped; `cli pytest tests -q` → 113 passed; `ruff check` limpo; `npm run lint`/`build` limpos; CI verde em todos os pushes.
