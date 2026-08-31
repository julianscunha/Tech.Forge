---
title: Module Runtime
category: arquitetura-core
domain: [arquitetura-core]
tags: [core, runtime, lifecycle, sdk, execution-context]
order: 5
---

# Module Runtime

Consolida o ciclo de execução de módulos ativos: separa o estado
**administrativo** (decisão do usuário/operador) do estado **runtime**
(efêmero, de execução), conecta de verdade os hooks de lifecycle do
`ModuleContract` (antes declarados no SDK mas nunca chamados) e define a
forma oficial de um módulo acessar recursos permitidos.

## Administrative State vs. Runtime State

```text
Administrative State (ModuleStatus)     Runtime State (RuntimeState)
─────────────────────────────────       ────────────────────────────
INSTALLED / DISABLED / BLOCKED /        READY / INITIALIZING / EXECUTING /
INVALID / INCOMPATIBLE                  DEGRADED / FAILED / STOPPED
(persistido, decisão do operador)       (em memória, nunca sobrevive a restart)
```

Um módulo pode estar administrativamente `INSTALLED` e, ao mesmo tempo,
com Runtime State `FAILED` — significa que a ativação foi aceita, mas o
hook `enable()` do módulo falhou. A ativação administrativa nunca é
bloqueada por uma falha de runtime (Error Boundary backend — a falha de
um módulo nunca derruba o Core nem a operação do usuário).

## Lifecycle hooks reais

`ModuleContract` (SDK) já declarava `install/enable/disable/upgrade/
health_check/uninstall` desde sempre — só `uninstall()` era de fato
chamado. O Module Runtime conecta os demais:

| Hook | Quando roda | Efeito no Runtime State |
|---|---|---|
| `enable()` | Depois que `activate_module` já validou dependências | sucesso → `READY`; exceção → `FAILED` + `last_error` |
| `disable()` | Depois que `deactivate_module` já validou dependentes | sempre → `STOPPED` (best-effort, falha não bloqueia) |
| `health_check()` | Sob demanda, via `POST /runtime/modules/{id}/initialize` — sem cache | `is_healthy=True` → `READY`; `False` → `DEGRADED`; exceção → `FAILED` |

Todos os três são **best-effort**: uma falha no hook do módulo nunca
impede a transição administrativa em si.

## ExecutionContext

`ModuleExecutionContext` (`app/module_runtime/context.py`) é a forma
oficial (lado Core) de descrever a que recursos uma execução de módulo
tem acesso — identidade, Service Registry, logger, caminhos, configuração
e um slot de cancelamento:

```python
from app.module_runtime.context import ModuleExecutionContext

ctx = ModuleExecutionContext.build("hello_world", module_registry)
# ctx.module_id, ctx.module_version, ctx.runtime_id (novo a cada build),
# ctx.services (Service Registry), ctx.logger, ctx.paths
```

Não é injetado como parâmetro nos hooks do `ModuleContract` (assinatura
fixa desde sempre) — é a estrutura que o Runtime usa internamente.

## Module SDK — sdk.services / sdk.runtime

Um módulo acessa recursos do Core sempre pelo SDK, nunca importando
`app.*` diretamente (mesma fronteira de `sdk.notifications`):

```python
from techforge_sdk import create_sdk
sdk = create_sdk("my_module")

providers = sdk.services.find_capability("aws.cost.read")  # Service Registry
state = sdk.runtime.state()  # {"state": "READY", "last_error": None, ...}
```

Ambos são proxies finos, somente leitura, via HTTP local pro Core — nunca
importam internals do Core (mesmo padrão de isolamento de `sdk.storage`/
`sdk.settings`/`sdk.notifications`).

## ModuleExecutionResult, Cancellation, Progress (esqueleto)

Envelope padronizado de resultado — só a forma, não o payload de negócio:

```python
from app.module_runtime.execution import ModuleExecutionResult

ModuleExecutionResult.success(data={"count": 3})
ModuleExecutionResult.failure(errors=["timeout"])
```

`CancellationToken` (sinalização cooperativa — o módulo decide quando
checar, o Runtime nunca mata a execução à força) e `ProgressReport`
(`PREPARING/RUNNING/FINALIZING` + percentual 0-100) também existem como
tipos testados, **sem um fluxo real de longa duração pra exercitar** —
decisão deliberada: nenhum módulo hoje tem uma operação longa que
justifique isso de verdade. Disponíveis para quando um módulo real
precisar (ex: coleta AWS, health check VMware).

## Focus Mode

Botão "Focus Mode" no workspace do módulo (`ModuleHost.tsx`) recolhe
sidebar e topbar, maximizando a área do módulo — sem abrir nova aba, sem
dependência de backend. Estado de sessão (`useFocusModeStore`, zustand,
não persistido), escopado à rota `/modules/:id` — sair do módulo limpa o
estado automaticamente.

## API

```bash
GET  /api/v1/runtime/modules              # Runtime State de todo módulo INSTALLED
GET  /api/v1/runtime/modules/{id}         # estado + last_error + last_execution + uptime
POST /api/v1/runtime/modules/{id}/initialize  # reroda health_check() sob demanda
```

## CLI

```bash
techforge runtime status              # runtime da plataforma
techforge runtime modules             # Runtime State de todo módulo
techforge runtime module <id>
techforge runtime initialize <id>
```

## O que foi deliberadamente deixado fora de escopo

- `POST /runtime/modules/{id}/execute` e `/cancel`: sem uma
  ação de execução de negócio real declarada por nenhum módulo hoje, um
  endpoint genérico seria vazio (não prova nada) ou arbitrário (a própria
  spec pede pra evitar "endpoint genérico inseguro capaz de executar
  qualquer função privada").
- Recálculo automático de `BLOCKED`/Runtime State no boot para módulos
  cuja dependência ficou insatisfeita enquanto a plataforma estava
  desligada — só é reavaliado numa tentativa explícita de `activate` ou
  `initialize`.
- Containers, sandbox de segurança completo, execução distribuída, fila
  corporativa, multiusuário, autenticação, Marketplace remoto.
