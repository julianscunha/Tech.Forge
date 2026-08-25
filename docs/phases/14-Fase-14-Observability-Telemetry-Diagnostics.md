# TechForge — Fase 14
## Observability, Telemetry & Diagnostics

> **Status:** Prompt de implementação consolidado
>
> **Objetivo:** Consolidar a observabilidade do Core e dos módulos, fornecendo logs estruturados, telemetria operacional, métricas, diagnósticos e ferramentas de troubleshooting, mantendo o TechForge leve e respeitando a privacidade do ambiente corporativo interno.

---

# 1. Contexto

O TechForge será uma plataforma modular.

Com o crescimento:

```text
Core
+
Service Modules
+
Application Modules
+
Dependencies
+
Runtime
```

diagnosticar problemas apenas por logs soltos será insuficiente.

O sistema precisa responder:

```text
O que aconteceu?
Onde aconteceu?
Qual módulo foi afetado?
Qual execução falhou?
Qual dependência estava envolvida?
Quanto tempo levou?
O que mudou?
```

---

# 2. Princípio central

Observabilidade não significa enviar dados automaticamente para serviços externos.

O padrão inicial deve ser:

```text
LOCAL-FIRST
```

A arquitetura pode preparar:

```text
EXTERNAL OBSERVABILITY
```

para futuro, mas não deve transmitir telemetria sem configuração explícita.

---

# 3. Observability domains

Separar:

```text
Logs
Metrics
Events
Diagnostics
Traces
```

Não misturar tudo em um único arquivo ou serviço.

---

# 4. Logging architecture

Criar uma arquitetura central.

Exemplo:

```text
Observability
├── Logger
├── Log Context
├── Log Storage
├── Metrics
├── Events
├── Diagnostics
└── Exporters
```

Todos os módulos devem utilizar o logger oficial via:

```text
ModuleExecutionContext
```

Evitar:

```python
print()
```

como mecanismo operacional.

---

# 5. Structured logging

Preferir logs estruturados.

Exemplo conceitual:

```json
{
  "timestamp": "...",
  "level": "ERROR",
  "component": "module_runtime",
  "module_id": "veeam_m365",
  "execution_id": "abc123",
  "message": "Sizing calculation failed"
}
```

Formato deve ser consistente.

O sistema pode apresentar uma visualização humana dos logs.

---

# 6. Log context

Todo log relevante deve poder carregar contexto.

Exemplo:

```text
platform_version
module_id
module_version
runtime_id
execution_id
request_id
deployment_mode
```

Não obrigar todos os campos em todos os logs.

Utilizar contexto disponível.

---

# 7. Log levels

Padronizar:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Documentar quando usar cada nível.

Exemplo:

```text
DEBUG
→ detalhe técnico

INFO
→ evento operacional esperado

WARNING
→ situação incomum, execução continua

ERROR
→ operação falhou

CRITICAL
→ componente essencial comprometido
```

---

# 8. Sensitive data

Nunca registrar:

```text
password
API key
token
secret
private key
credential
```

Implementar:

```text
redaction
```

quando possível.

Exemplo:

```text
aws_key=****
```

Não depender apenas da disciplina do desenvolvedor.

---

# 9. Log retention

Definir política configurável.

Exemplo:

```text
DEBUG logs → 7 days
INFO/WARNING → 30 days
ERROR → 90 days
```

Valores reais podem ser configuráveis.

Evitar crescimento infinito.

Para Desktop:

- rotação simples;
- limite de tamanho;
- retenção local.

---

# 10. Metrics

Definir uma interface:

```text
MetricEmitter
```

Métricas iniciais:

```text
platform_startups
module_loads
module_executions
execution_duration
execution_failures
dependency_failures
runtime_errors
```

Não medir tudo.

Foco em métricas úteis.

---

# 11. Metric types

Suportar conceitualmente:

```text
Counter
Gauge
Histogram
Timer
```

Exemplo:

```text
Counter
→ executions_total

Gauge
→ active_modules

Histogram
→ execution_duration
```

No Desktop, a implementação pode ser local e simples.

---

# 12. Events

Criar eventos operacionais.

Exemplos:

```text
MODULE_INSTALLED
MODULE_ACTIVATED
MODULE_FAILED
MODULE_UPDATED
DEPENDENCY_BLOCKED
INTEGRITY_CHANGED
```

Eventos devem ser reutilizáveis por:

- Notifications;
- Diagnostics;
- Audit;
- Metrics.

Não criar múltiplos sistemas de eventos paralelos.

---

# 13. Execution tracing

Criar um conceito leve de trace.

Exemplo:

```text
Request
  └── Execution
       ├── Dependency Resolve
       ├── Service Call
       ├── Module Task
       └── Result
```

Cada execução deve possuir:

```text
execution_id
```

Para integrações mais profundas, preparar:

```text
trace_id
span_id
```

Não implementar OpenTelemetry completo obrigatoriamente se não houver necessidade.

Mas não impedir integração futura.

---

# 14. Diagnostic snapshots

Permitir gerar um diagnóstico do sistema.

Exemplo:

```text
TechForge Diagnostic Snapshot
├── Platform Version
├── Deployment Mode
├── Runtime Status
├── Active Modules
├── Module Versions
├── Dependency Status
├── Storage Health
├── Recent Errors
└── Environment Summary
```

Não incluir:

```text
secrets
credentials
private user data
```

---

# 15. System diagnostics

Criar:

```text
SystemDiagnosticService
```

Responsabilidades:

- coletar status;
- verificar componentes;
- consolidar falhas;
- gerar relatório.

Exemplo:

```text
Platform       HEALTHY
Storage        HEALTHY
Runtime        HEALTHY
Modules        12 ACTIVE
Dependencies   0 BLOCKED
Recent Errors  1
```

---

# 16. Module diagnostics

Cada módulo pode fornecer diagnóstico opcional.

Interface conceitual:

```text
get_diagnostics()
```

Resultado padronizado:

```text
status
checks
warnings
errors
metadata
```

Não obrigar módulos simples a implementar diagnósticos complexos.

---

# 17. Health integration

Reutilizar:

```text
Health
Ready
```

da Fase 13.

Não criar endpoint duplicado.

O Diagnostic Service consolida:

```text
Core
+
Storage
+
Runtime
+
Module Health
```

---

# 18. Failure correlation

Quando um erro ocorrer, relacionar quando possível:

```text
Error
↓
Module
↓
Execution
↓
Dependency
↓
Recent events
```

Exemplo:

```text
AWS Sizing failed
because
AWS Cost Service unavailable
```

O objetivo é reduzir troubleshooting manual.

---

# 19. Error registry

Criar um registro estruturado de erros relevantes.

Exemplo:

```text
ErrorRecord
├── id
├── timestamp
├── component
├── module_id
├── execution_id
├── severity
├── message
├── cause
└── metadata
```

Não duplicar o log completo no banco sem necessidade.

Registrar referências e resumos.

---

# 20. Diagnostic codes

Criar códigos estáveis para erros importantes.

Exemplo:

```text
TF-RUNTIME-001
TF-MODULE-004
TF-DEPENDENCY-002
TF-INTEGRITY-003
```

Isso facilita:

- documentação;
- suporte;
- IA;
- troubleshooting.

Cada código deve possuir descrição no Developer Center.

---

# 21. Troubleshooting UI

Criar uma área simples:

```text
System
→ Diagnostics
```

Mostrar:

- saúde geral;
- módulos com problema;
- erros recentes;
- dependências bloqueadas;
- ações sugeridas;
- gerar diagnóstico.

Não criar um SIEM.

---

# 22. Module diagnostics UI

Na página do módulo:

```text
Status
Health
Recent Executions
Recent Errors
Dependencies
Diagnostics
```

Manter informações técnicas acessíveis sem poluir a tela principal.

---

# 23. Execution history

Manter histórico limitado.

Exemplo:

```text
Execution
├── timestamp
├── duration
├── status
├── warnings
└── error reference
```

Configurar retenção.

Não armazenar automaticamente payloads grandes.

---

# 24. Performance diagnostics

Registrar dados mínimos:

```text
startup duration
module load duration
execution duration
storage operation duration
```

Usar esses dados para identificar:

```text
slow module
slow startup
dependency bottleneck
```

Não criar profiling contínuo pesado.

---

# 25. Startup diagnostics

Ao iniciar:

```text
Launcher
↓
Core
↓
Storage
↓
Modules
↓
Dependencies
↓
Runtime
```

Registrar duração e resultado de cada etapa.

Isso ajuda a explicar:

```text
Why did TechForge start slowly?
```

---

# 26. Module lifecycle telemetry

Registrar eventos:

```text
DISCOVERED
INSTALLED
ACTIVATED
INITIALIZED
READY
EXECUTED
FAILED
DEACTIVATED
REMOVED
```

Reutilizar lifecycle existente.

Não criar estados paralelos.

---

# 27. Dependency telemetry

Registrar:

```text
DEPENDENCY_RESOLVED
DEPENDENCY_MISSING
DEPENDENCY_BLOCKED
DEPENDENCY_CONFLICT
DEPENDENCY_CYCLE
```

Integrar ao Dependency Governance.

---

# 28. Runtime telemetry

Registrar:

```text
RUNTIME_START
RUNTIME_READY
EXECUTION_START
EXECUTION_PROGRESS
EXECUTION_COMPLETE
EXECUTION_CANCELLED
RUNTIME_ERROR
```

Evitar registrar progresso excessivamente granular.

---

# 29. Export diagnostics

Permitir exportar:

```text
Diagnostic Report
```

Formato inicial:

```text
JSON
TXT
```

Futuramente:

```text
ZIP support bundle
```

Se gerar pacote, incluir apenas dados permitidos.

---

# 30. Support bundle

Preparar conceito:

```text
TechForge Support Bundle
```

Pode incluir:

- versões;
- configuração sanitizada;
- diagnostic snapshot;
- logs recentes;
- module registry;
- dependency graph.

Nunca incluir automaticamente:

- secrets;
- credenciais;
- private keys;
- arquivos de dados sensíveis.

---

# 31. Notifications integration

Eventos críticos devem alimentar Notifications.

Exemplo:

```text
CRITICAL runtime failure
↓
Notification
```

Não notificar cada log.

Definir severidade e deduplicação.

---

# 32. Dashboard

O Dashboard simples pode mostrar:

```text
Platform Health
Active Modules
Module Failures
Blocked Dependencies
Recent Critical Events
```

Manter o objetivo original:

> Dashboard simples e operacional.

Não transformar em NOC.

---

# 33. Developer Center

Documentar:

- logging;
- log levels;
- structured fields;
- sensitive data;
- metrics;
- events;
- diagnostics;
- diagnostic codes;
- module diagnostics;
- execution tracing.

Adicionar exemplos para módulos.

O AI Context deve incluir as convenções obrigatórias.

---

# 34. API

Criar APIs:

```text
GET /api/v1/diagnostics
GET /api/v1/diagnostics/health
GET /api/v1/diagnostics/errors
GET /api/v1/diagnostics/executions
GET /api/v1/modules/{id}/diagnostics
GET /api/v1/modules/{id}/executions
POST /api/v1/diagnostics/export
```

Evitar expor logs completos sem limites.

Implementar paginação quando necessário.

---

# 35. CLI

Adicionar:

```bash
techforge diagnostics
techforge diagnostics health
techforge diagnostics errors
techforge diagnostics export
techforge modules diagnostics <module>
techforge logs tail
```

O CLI deve utilizar os mesmos serviços.

---

# 36. Privacy policy

Como o sistema é interno:

```text
No external telemetry by default
```

Qualquer exporter externo futuro deve ser:

```text
explicitly configured
```

Documentar claramente.

---

# 37. Performance

A observabilidade não deve comprometer o sistema.

Evitar:

- logs síncronos bloqueando execução;
- métricas com I/O excessivo;
- tracing detalhado permanente;
- snapshots automáticos gigantes.

Preferir:

```text
buffered
bounded
event-driven
configurable
```

---

# 38. Testes

Criar testes para:

- structured log;
- context propagation;
- log levels;
- redaction;
- retention;
- rotation;
- metrics counter;
- gauge;
- histogram/timer;
- events;
- event correlation;
- execution ID;
- trace readiness;
- diagnostic snapshot;
- system diagnostics;
- module diagnostics;
- error registry;
- diagnostic codes;
- health integration;
- failure correlation;
- execution history;
- performance metrics;
- startup diagnostics;
- export;
- support bundle sanitization;
- notifications;
- API;
- CLI;
- frontend.

Teste integrado:

```text
Module Execution
↓
Execution ID
↓
Logs
↓
Metrics
↓
Event
↓
Result
```

Também:

```text
Dependency failure
↓
Module error
↓
Correlation
↓
Diagnostic report
↓
Suggested action
```

---

# 39. O que não implementar

Não implementar nesta fase:

- SIEM;
- observabilidade SaaS obrigatória;
- coleta externa automática;
- OpenTelemetry obrigatório;
- Prometheus obrigatório;
- APM comercial;
- armazenamento infinito de logs.

A arquitetura deve permitir integrações futuras.

---

# 40. Critérios de aceitação

A fase estará concluída quando:

1. Logging central existir.
2. Logs estruturados funcionarem.
3. Log Context propagar Module e Execution IDs.
4. Dados sensíveis forem redigidos.
5. Rotação/retenção existir.
6. Metrics abstraction existir.
7. Eventos operacionais existirem.
8. Lifecycle reutilizar eventos.
9. Execution correlation existir.
10. Diagnostic Snapshot funcionar.
11. System Diagnostics funcionar.
12. Module Diagnostics existir.
13. Error Registry existir.
14. Diagnostic Codes existirem.
15. Health e Readiness forem reutilizados.
16. Failure correlation funcionar.
17. Execution History existir.
18. Performance diagnostics existirem.
19. Startup diagnostics existirem.
20. Export diagnostics funcionar.
21. Support bundle for sanitizado.
22. Notifications integrar eventos relevantes.
23. Dashboard permanecer simples.
24. APIs funcionarem.
25. CLI funcionar.
26. Developer Center documentar observabilidade.
27. AI Context incluir convenções.
28. Telemetria externa não ocorrer por padrão.
29. Todos os testes passarem.
30. Core continuar leve.

---

# Regra final

Antes de finalizar:

- iniciar TechForge;
- analisar startup diagnostics;
- executar módulo;
- localizar execution ID;
- verificar logs;
- verificar métricas;
- provocar warning;
- provocar erro;
- verificar redaction;
- provocar falha de dependência;
- gerar diagnóstico;
- verificar correlação;
- exportar relatório;
- gerar support bundle sanitizado;
- verificar UI de Diagnostics;
- executar CLI;
- executar todos os testes;
- executar build do Frontend.

Apresentar:

```text
Logging:
Structured Logging:
Log Context:
Sensitive Data:
Retention:
Metrics:
Events:
Execution Correlation:
Tracing Readiness:
System Diagnostics:
Module Diagnostics:
Error Registry:
Diagnostic Codes:
Health Integration:
Failure Correlation:
Execution History:
Performance Diagnostics:
Startup Diagnostics:
Diagnostic Export:
Support Bundle:
Notifications:
Dashboard:
API:
CLI:
Developer Center:
AI Context:
Privacy:
Tests:
Build:
Known Issues:
```
