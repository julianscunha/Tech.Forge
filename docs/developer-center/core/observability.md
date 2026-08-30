---
title: Observability & Diagnostics
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, logging, metrics, events, diagnostics, error-registry]
order: 7
---

# Observability & Diagnostics

Consolida logs estruturados, métricas, eventos e diagnósticos do Core e
dos módulos — troubleshooting sem depender de telemetria externa
(nenhuma coleta sai da máquina por padrão).

## Logging

Todo módulo já recebe um logger próprio (`techforge.module.<id>`) via
`ModuleExecutionContext.logger` — nunca usar `print()` como mecanismo
operacional.

```python
def calculate(context, **kwargs):
    context.logger.info("Iniciando cálculo de tamanho")
    ...
    context.logger.warning("Fonte de dados incompleta, usando fallback")
```

O mesmo registro sai por dois canais:

- **Console** — formato humano (`timestamp [LEVEL] logger: mensagem`), o
  que você vê em `techforge logs --backend`.
- **Arquivo** — `logs/backend.jsonl`, uma linha JSON por registro,
  parseável por qualquer ferramenta externa (`jq`, log viewers) sem
  depender de um formato proprietário:

```json
{"timestamp": "2026-08-30T16:38:26+00:00", "level": "ERROR", "component": "techforge.module.veeam_m365", "message": "Sizing calculation failed", "module_id": "veeam_m365", "execution_id": "abc123"}
```

### Log Context

Campos de contexto (`module_id`, `execution_id`, etc.) são propagados
automaticamente via `contextvars` — nenhum módulo precisa passar
`extra=` manualmente. O Core já amarra isso ao redor de toda invocação
de capacidade (`service_registry.invoker.invoke()`).

### Níveis

| Nível | Quando usar |
|---|---|
| `DEBUG` | Detalhe técnico, só útil investigando algo específico |
| `INFO` | Evento operacional esperado |
| `WARNING` | Situação incomum, execução continua |
| `ERROR` | Operação falhou |
| `CRITICAL` | Componente essencial comprometido |

Nível mínimo configurável via `LOG_LEVEL`/`LOG_FILE_LEVEL` (`settings.py`)
— podem divergir (ex: console em `WARNING`, arquivo em `DEBUG`).

### Dados sensíveis

Nunca logar `password`, `api key`, `token`, `secret`, `private key`,
`credential` em texto puro. Dois mecanismos de redação coexistem,
instalados no Handler (não no Logger — registros propagados de loggers
filhos só passam pelos filtros do Handler):

1. **Por valor conhecido** — qualquer valor já gravado via `context.secrets`
   (SecretStore) é mascarado onde quer que apareça.
2. **Por padrão de chave** — `password=...`, `"token": "..."` são
   mascarados mesmo que o valor nunca tenha sido registrado. Não depende
   da disciplina do desenvolvedor.

```text
password=hunter2         → password=***REDACTED***
"token": "sk-abc123"     → "token": "***REDACTED***"
```

### Retenção e rotação

`logs/backend.jsonl` rotaciona por tamanho (`LOG_MAX_BYTES`/`LOG_BACKUP_COUNT`,
default 10MB × 5 arquivos). Retenção por nível é configurável
(`LOG_RETENTION_DAYS`, default `DEBUG` 7d / `INFO`-`WARNING` 30d /
`ERROR`-`CRITICAL` 90d) — aplicada de forma síncrona no startup.

## Metrics

`MetricEmitter` (`app/observability/metrics.py`) expõe Counter, Gauge,
Histogram e Timer, em memória, sem I/O:

```python
from app.observability.metrics import metric_emitter

metric_emitter.counter("module_executions").inc()
with metric_emitter.timer("execution_duration"):
    do_work()
```

Métricas hoje instrumentadas: `platform_startups`, `module_loads`,
`module_executions`, `execution_duration`, `execution_failures`,
`dependency_failures`, `runtime_errors`. Deliberadamente poucas — "não
medir tudo".

## Events

Um `EventBus` in-process (`app/observability/events.py`) unifica os
sistemas de evento que existiam espalhados (`RuntimeEvent`,
`OperationLog`, `LoaderJournal`) — cada um continua sendo a fonte de
leitura do próprio domínio, mas também publica no bus. Novos
consumidores (Notifications, Diagnostics) assinam o bus em vez de
inventar mais um buffer:

```python
from app.observability.events import event_bus

def on_event(event):
    if event.type == "runtime.degraded":
        ...

event_bus.subscribe(on_event)
```

Um assinante que falha nunca derruba quem publicou.

## Diagnostics

`SystemDiagnosticService` consolida Health (Fase 1) + Storage + Runtime
+ Module Health num snapshot único — sem endpoint `/ready` (não se
aplica a Desktop single-instância).

### Error Registry

Captura automática de erro nos 3 pontos-chave do Core: falha de
execução, falha de dependência, erro de runtime. Cada `ErrorRecord`
ganha um **Diagnostic Code** estável, resolvido a partir da origem:

| Código | Origem |
|---|---|
| `TF-EXECUTION-001` | Falha de execução de módulo |
| `TF-DEPENDENCY-001` | Dependência declarada inválida |
| `TF-RUNTIME-001` | Componente de runtime parou de responder |

Catálogo deliberadamente pequeno — só origens reais, não uma lista
extensa especulativa.

### Execution History

Toda chamada via `service_registry.invoker.invoke()` grava um registro
em `execution_history` (execution_id, module_id, status,
duration_seconds), com retenção configurável
(`EXECUTION_HISTORY_RETENTION_DAYS`).

### Execution tracing

`execution_id` é gerado por chamada e amarrado ao Log Context durante
toda a invocação (sucesso ou falha) — qualquer log emitido nesse
intervalo carrega a correlação automaticamente. `ModuleExecutionContext`
(Fase 9) tem seu próprio `runtime_id`, mantido como estava; `execution_id`
é um campo novo e independente, não uma renomeação.

### Failure correlation

`FailureCorrelationService.correlate(error_id)` monta a cadeia
`Error → Module → Execution → Dependency → eventos recentes`,
reaproveitando Execution History, `module_runtime_registry`,
`dependency_engine` e o histórico de operações/eventos já existentes.

### Export

```bash
techforge diagnostics export --format json   # Diagnostic Report
techforge diagnostics export --format txt
techforge diagnostics export --format zip    # Support Bundle
```

O Support Bundle empacota snapshot + config da plataforma + registry de
módulos + grafo de dependências + logs recentes — **nunca** inclui
segredos, credenciais, private keys ou dados de módulo (`data/`).

## API

```text
GET  /api/v1/diagnostics
GET  /api/v1/diagnostics/health
GET  /api/v1/diagnostics/errors?limit=N
GET  /api/v1/diagnostics/executions?limit=N
GET  /api/v1/diagnostics/resources
GET  /api/v1/diagnostics/heaviest-modules?limit=N
POST /api/v1/diagnostics/export?format=json|txt|zip
GET  /api/v1/modules/{id}/diagnostics
GET  /api/v1/modules/{id}/executions
```

## CLI

```bash
techforge diagnostics health
techforge diagnostics errors
techforge diagnostics export --format zip
techforge modules diagnostics <module_id>
techforge logs --backend --follow   # tail ao vivo
```

## Notifications integration

Eventos verdadeiramente críticos (hoje: `runtime.degraded`) viram
Notification — não cada log. Dedup por título dentro de uma janela de
15 minutos evita spam se um componente ficar oscilando.

## Fora de escopo

SIEM, telemetria SaaS obrigatória, OpenTelemetry/Prometheus obrigatórios,
APM comercial, coleta externa automática. Nenhuma telemetria sai da
máquina por padrão; qualquer exporter externo futuro precisa ser
explicitamente configurado.
