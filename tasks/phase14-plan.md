# Plano — Fase 14: Observability, Telemetry & Diagnostics

Aprovado em 2026-08-30. Spec: `docs/phases/14-Fase-14-Observability-Telemetry-Diagnostics.md`.

## Premissas validadas contra o código real

- `ModuleExecutionContext` (`app/module_runtime/context.py`) já tem `context.logger` e gera um `runtime_id` (UUID) por execução — base do tracing já existe, falta estruturar.
- `SecretRedactionFilter` (`app/security/redaction.py`, Fase 12 §28) já redige **valores conhecidos** registrados no SecretStore, mas não por **padrão de chave genérico** (`password=`, `token=` não registrados passam direto).
- `ModuleExecutionResult` (`app/module_runtime/execution.py`) já tem a forma exata que o spec pede para Execution History (`status/data/warnings/errors/duration_seconds/metadata`), mas é descartado após cada chamada — nunca persistido.
- `TechForgeRuntime` (`app/runtime/__init__.py`) já tem `RuntimeEvent`, estado `DEGRADED`, buffer dos últimos 20 eventos — protótipo natural do `SystemDiagnosticService`.
- `NotificationService` (`app/services/notifications.py`, tabela SQLite real) é o alvo de integração do §31.
- `/platform/health` e `/platform/status` (Fase 1 §5) já cobrem o que §17 pede sob o nome (incorreto) de "Health da Fase 13" — Fase 13 foi adiada e nunca implementou nada disso.
- **Existem hoje 4 sistemas de eventos paralelos** sem unificação: `logging` stdlib puro (19 arquivos), `RuntimeEvent` (runtime, cap 20), `OperationLog` (package_manager, cap 500), `LoaderJournal` (module_engine, single-slot). Exatamente o que o §12 do spec proíbe criar — esta fase é o ponto de unificação.
- Não existe rotação de log hoje — só `logging.basicConfig`, saída pro stdout/stderr capturada pelo launcher em `logs/*.log` sem limite de tamanho nem retenção.
- Não existe nenhuma métrica medida hoje em lugar nenhum.
- `psutil` não é dependência hoje — será adicionada (13ª dependência do backend).
- Frontend não tem lib de charting — mini gráficos do card de recursos serão SVG feito à mão, sem dependência nova.

## Decisões arquiteturais confirmadas (2026-08-30)

1. **Unificar os 4 sistemas de eventos** num `EventBus` in-process único (spec não exige fila externa). `RuntimeEvent`, `OperationLog` e `LoaderJournal` passam a publicar nele, mantendo suas APIs de leitura atuais como fachada (evita quebrar consumidores existentes).
2. **Métricas e Execution History em SQLite**, tabelas dedicadas por domínio (`execution_history`, `error_registry`, etc.) — não uma tabela genérica de eventos. Mesmo padrão de `module_kv_store`/`Notification`.
3. **`runtime_id` mantido como está; `execution_id` novo é adicionado** — evita renomear campo já usado em testes das Fases 9/12. Diferença documentada no Developer Center.
4. **Log estruturado**: arquivo em **JSON-lines** (parseável por qualquer ferramenta externa: `jq`, log viewers, etc.); console continua em formato humano legível. Sem trocar de biblioteca de logging — formatter customizado sobre o `logging` stdlib.
5. **Nível mínimo configurável** (ex: `LOG_LEVEL` em `settings.py`, junto dos outros env vars centralizados) — por padrão INFO+, ajustável sem recompilar.
6. **Retenção por nível é configurável** (não hardcoded) — valores default do próprio spec como sugestão inicial (DEBUG 7d / INFO-WARNING 30d / ERROR 90d), mas expostos como config real (provavelmente `platform_config`, mesmo mecanismo da Fase 12).
7. **Rotação via `RotatingFileHandler`** (stdlib, sem dependência nova); cleanup de retenção por nível roda de forma síncrona no startup (sem agendador — overkill pro Desktop).
8. **Sem endpoint `GET /logs`** — spec explicitamente pede "evitar expor logs completos sem limites" (§34). Leitura externa é via arquivo em disco (JSON-lines) + `techforge logs tail` + export pontual via `/diagnostics/export`.
9. **Sem `/ready`** — não se aplica a Desktop single-instância (readiness é conceito de orquestração multi-processo). `SystemDiagnosticService` consolida o Health já existente da Fase 1 + Storage + Runtime + Module Health.
10. **Frontend fatiado**: página `System → Diagnostics` entra nesta fase; seção de diagnóstico dentro da página do módulo (`get_diagnostics()` por módulo) fica de fora do frontend desta fase — o backend/contrato entra, a UI fica pra depois.
11. **Diagnostic Codes**: começar só com códigos reais já existentes como enums (`RemoveStatus.BLOCKED`, `InstallStatus.INCOMPATIBLE`, etc.), não inventar catálogo extenso especulativo.
12. **Dashboard incrementado** (§32, mantendo "simples, não-NOC"):
    - Cards de **Module Failures**, **Blocked Dependencies**, **Recent Critical Events** navegam para a seção correspondente de `Diagnostics` ao serem clicados (sem UI de detalhe duplicada).
    - Novo **card de recursos** (CPU/memória via `psutil`, disco via `shutil.disk_usage` stdlib), refresh a cada 20s (não real-time), expande **inline** ao clicar (mini gráfico de barras/pizza em SVG feito à mão).
    - Novo **card "módulo mais pesado"** usa proxy real e barato — espaço em disco por módulo (`os.walk` simples) + duração média de execução + taxa de falha (dados já coletados pelo Execution History, slice 8) — não tenta atribuir CPU/memória por módulo (módulos rodam no mesmo processo/heap/GIL do Core; profiling per-módulo exigiria reabrir o `module_runtime` inteiro, fora de escopo).
    - **Reordenação manual dos cards** (drag-and-drop) — HTML5 nativo (`draggable`/`onDragStart`/`onDrop`, sem lib nova), ordem persistida via Zustand `persist` (localStorage), mesmo padrão já usado por `app.ts`/`devmode.ts` para preferências de UI.
    - **Ícone de engrenagem no canto** abre um popover simples com checkbox por card (mostrar/ocultar) — mesmo store de layout do drag-and-drop, só mais um campo (`visible: Set<CardId>`). Usuário pode ocultar todos os cards e deixar a Dashboard vazia se quiser — é preferência dele, não validamos um mínimo obrigatório.
13. **Fora de escopo** (§39 do próprio spec): SIEM, telemetria SaaS obrigatória, OpenTelemetry/Prometheus obrigatórios, APM comercial, log infinito, coleta externa automática. `trace_id`/`span_id` existem como campos vazios/opcionais preparatórios, sem propagação distribuída real (processo único).

## Slices

1. **Logger central + Log Context** — formatter JSON-lines para arquivo, formato humano no console; contexto propagável via `contextvars` (`platform_version`, `module_id`, `execution_id`, `runtime_id`, `request_id`, `deployment_mode` — nenhum campo obrigatório).
2. **Nível mínimo configurável** — `LOG_LEVEL` em `settings.py`; nível padrão por handler (arquivo vs. console podem divergir).
3. **Redação por padrão de chave** — generaliza `SecretRedactionFilter` (hoje só cobre valor conhecido) para também mascarar por nome de campo (`password`, `token`, `secret`, `api_key`, `credential`, etc.), sem depender só de disciplina do desenvolvedor.
4. **Rotação + retenção configurável de log** — `RotatingFileHandler` (tamanho); retenção por nível configurável via `platform_config`; cleanup síncrono no startup.
5. **`EventBus` unificado** — publish/subscribe in-process; migração de `RuntimeEvent`, `OperationLog`, `LoaderJournal` para publicarem nele mantendo suas APIs de leitura como fachada.
6. **`MetricEmitter`** — Counter/Gauge/Histogram/Timer, armazenamento em memória + snapshot.
7. **Métricas iniciais instrumentadas** — `platform_startups`, `module_loads`, `module_executions`, `execution_duration`, `execution_failures`, `dependency_failures`, `runtime_errors`.
8. **`execution_id` + correlação básica** — novo campo em `ModuleExecutionContext`, propagado no log context.
9. **Execution History persistida** — tabela SQLite dedicada, `ModuleExecutionResult` passa a ser salvo (hoje é descartado); retenção configurável.
10. **Error Registry** — tabela dedicada, `ErrorRecord`; captura automática nos pontos-chave já existentes (falha de execução, falha de dependência, runtime error).
11. **Diagnostic Codes** — catálogo inicial mapeando enums já existentes (`RemoveStatus.BLOCKED`, `InstallStatus.INCOMPATIBLE`, etc.) para códigos estáveis (`TF-RUNTIME-001` etc.) + doc no Developer Center.
12. **`SystemDiagnosticService`** — consolida `/platform/health` (Fase 1) + Storage + Runtime + Module Health num serviço único.
13. **Failure correlation** — Error → Module → Execution → Dependency → eventos recentes do EventBus.
14. **Startup diagnostics** — duração por etapa do lifespan (reaproveita hooks de startup já existentes).
15. **Diagnostic snapshot + export** — JSON/TXT via `/diagnostics/export` e `techforge diagnostics export`.
16. **Support Bundle sanitizado** — conceito preparado (versões, config sanitizada, snapshot, logs recentes, registry, dependency graph); nunca inclui segredos/credenciais.
17. **Notifications integration + API/CLI** — eventos críticos do EventBus → `NotificationService` (com dedup); `GET /diagnostics*`, `GET /modules/{id}/diagnostics|executions`, `techforge diagnostics*`, `techforge logs tail`.
18. **Dashboard incrementado** — cards de Module Failures / Blocked Dependencies / Recent Critical Events (navegam pra Diagnostics); card de recursos (psutil + disco, refresh 20s, expande inline com mini SVG); card "módulo mais pesado" (disco + duração + falhas); reordenação manual dos cards via drag-and-drop HTML5 nativo (sem lib nova), ordem persistida em Zustand `persist` (mesmo padrão de `app.ts`/`devmode.ts`, preferência client-only em localStorage — não é dado de negócio, não precisa de round-trip ao backend).
19. **Frontend: página `System → Diagnostics`** — Health, Errors, Executions, export; reaproveita padrões visuais já usados em Marketplace/Módulos.
20. **Developer Center + AI Context + fechamento** — documentar logging/levels/structured fields/sensitive data/metrics/events/diagnostics/diagnostic codes/execution tracing com exemplos para módulos; AI Context com convenções obrigatórias; relatório de fechamento.

## Known issues a monitorar

- Diagnóstico por módulo (`get_diagnostics()` opcional, contrato exposto pro módulo implementar) fica só no backend nesta fase — sem UI dedicada na página do módulo. Candidato a sub-fase/slice futuro se houver necessidade real.
- Migração dos 3 sistemas de eventos antigos (`RuntimeEvent`/`OperationLog`/`LoaderJournal`) pro `EventBus` é reescrita interna sensível — precisa rodar a suíte completa após cada migração individual, não só no final.
- `psutil` é dependência nova (13ª do backend) — avaliar se todas as plataformas-alvo (Windows/Linux/Mac, per CI) instalam sem problema de wheel/compilação antes de travar a versão no CI.
