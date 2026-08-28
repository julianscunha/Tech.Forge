# Plano — Fase 9: Module Runtime & Execution

> Spec: docs/phases/09-Fase-09-Module-Runtime-Execution.md
> Pré-requisito: Fase 8 (Service Registry) + Fase 8.1 (Dependency Governance) ✅ fechadas.

## Premissas validadas (investigação de código real)

1. ✅ `app/runtime/__init__.py::TechForgeRuntime` já existe, mas é o runtime **da
   plataforma inteira** (BOOTSTRAPPING/READY/DEGRADED/SHUTTING_DOWN/STOPPED,
   uptime, eventos startup/shutdown) — não por módulo. A própria docstring já
   avisa "Future phases will extend this to own the module execution
   lifecycle" — a Fase 9 é essa extensão, não um sistema paralelo. Pra evitar
   colisão de nome/namespace, o pacote novo se chama `app/module_runtime/`
   (não `app/runtime2` nem reaproveitar `app/runtime`).
2. ✅ Há **3 implementações duplicadas** do mesmo padrão de carregamento
   dinâmico (`importlib.util.spec_from_file_location` → `exec_module` →
   `getattr(mod, "module", None)` → `getattr(instance, method)`):
   `module_engine/plugin_loader.py` (monta router), `service_registry/invoker.py`
   (chama export), `package_manager/manager.py::_call_uninstall_hook`. Nenhuma
   abstração comum hoje.
3. ✅ `sdk/python/techforge_sdk/contracts/__init__.py::ModuleContract` já
   declara `install/enable/disable/upgrade/health_check/uninstall` como
   abstratos — só `uninstall()` é de fato chamado pelo Core
   (`manager.py:274`). `install()`, `enable()`, `disable()`, `health_check()`
   são contrato morto. A Fase 9 conecta isso.
4. ✅ `sdk/python/techforge_sdk/` já expõe `sdk.database/storage/logger/
   settings/notifications` via `create_sdk(module_id)` — é praticamente o §9
   da spec; falta `sdk.services` (Service Registry) e `sdk.runtime`.
5. ✅ `ModuleHost.tsx` já cobre a maior parte do §11/§15 frontend: dynamic
   `import()` do `entry_frontend`, `render(container)`, `ErrorBoundary` de
   classe, fallback sem derrubar o Core. Rota `/modules/:moduleId/*`
   (`AppRouter.tsx`) já monta isso — "abrir sem nova aba" (§1) já satisfeito.
   Falta: Focus Mode, Workspace como conceito consolidado (hoje é só o
   layout padrão do `AppShell`).
6. ✅ `HealthResult` (SDK) já modela `ok()`/`fail()` mas nada chama
   `health_check()` hoje.
7. ✅ Nenhum mecanismo de progresso/cancelamento existe (`operation_log.py`
   é só ring-buffer síncrono de eventos install/update/remove, sem %).
8. ✅ Nenhum módulo real (`hello_world`/`veeam_m365`) tem hoje uma ação de
   "executar" além de abrir UI ou chamar endpoint HTTP direto — não há caso
   de uso real pra validar um `ModuleExecutionResult` de negócio.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)

1. **Escopo de execução para Application Modules**: esqueleto do envelope
   (`ModuleExecutionResult`) + conectar de verdade os hooks hoje mortos do
   `ModuleContract` (`install/enable/disable/health_check`) nos pontos certos
   do lifecycle já existente. Sem inventar uma "execução" fictícia de
   negócio em `hello_world`/`veeam_m365`.
2. **Cancellation/progress (§16/§21)**: esqueleto de tipos
   (`CancellationToken`, enum de progresso `PREPARING/RUNNING/FINALIZING`)
   testado unitariamente, sem um fluxo real de longa duração pra exercitar
   — não há hoje operação do Core que justifique isso de verdade.
3. **Health check (§18)**: sob demanda, sem cache — `GET
   /runtime/modules/{id}` chama `health_check()` na hora da requisição.
4. **Consolidação dos 3 loaders duplicados**: sim, dentro desta fase —
   `module_runtime/loader.py` novo, reusado por `plugin_loader.py`,
   `service_registry/invoker.py` e `package_manager/manager.py`
   (refactor mecânico, cada ponto já tem teste cobrindo o comportamento
   observável, que não muda).

## Novo pacote

```
core/backend/app/module_runtime/
  state.py       # RuntimeState (enum efêmero) + ModuleRuntimeRegistry in-memory
  loader.py      # load_module_instance() único — consolida os 3 duplicados
  context.py     # ModuleExecutionContext (services, runtime, logger, paths, config, cancellation)
  lifecycle.py   # wiring: chama install/enable/disable/health_check nos pontos certos
  execution.py   # ModuleExecutionResult, CancellationToken, ProgressState
```

## Slices

### Slice 1 — Loader único (refactor mecânico, TDD) — §10
- `module_runtime/loader.py::load_module_instance(module_dir, entry_backend)
  -> object | None`: consolida o padrão `importlib.util` hoje duplicado em
  3 lugares. Mesma semântica observável (nenhum teste existente pode mudar
  de comportamento).
- `plugin_loader.py`, `service_registry/invoker.py`,
  `package_manager/manager.py::_call_uninstall_hook` passam a usar o loader
  novo.

**Aceite:** suíte completa (Fases 1-8.1) continua 100% verde sem alteração;
novos testes unitários do loader isolado (módulo válido, módulo sem
`module` attribute, arquivo ausente, erro de import).

### Slice 2 — Runtime State (separado do Administrative State) — §4/§5/§29
- `module_runtime/state.py::RuntimeState` (READY/INITIALIZING/EXECUTING/
  DEGRADED/FAILED/STOPPED — efêmero, nunca persistido em DB).
- `ModuleRuntimeRegistry`: in-memory, mesmo padrão de `ServiceRegistry`
  (singleton, `get(module_id)`, `set_state(module_id, state, **meta)`,
  `clear_transient_state()` no shutdown). Guarda `last_error`,
  `last_execution`, `uptime` desde a última transição pra READY.
- Reconstruído a partir do `ModuleRegistry` (Administrative State) no boot —
  módulo `INSTALLED` começa `READY`; `DISABLED`/`BLOCKED`/`INVALID` não
  entram no Runtime State (não fazem sentido como "prontos pra executar").

**Aceite:** transição administrativa (activate/deactivate) não pisa no
Runtime State diretamente — só o Lifecycle Manager (Slice 3) que traduz uma
mudança administrativa em atualização de Runtime State.

### Slice 3 — Lifecycle hooks reais (TDD) — §10/§18
- `module_runtime/lifecycle.py`: `on_activate(module_id)` chama
  `enable()` do `ModuleContract` (via loader do Slice 1) depois que o
  `activate_module` administrativo já validou dependências (Fase 8.1);
  `on_deactivate(module_id)` chama `disable()`; falha em qualquer hook
  vira `RuntimeState.FAILED` + `last_error`, nunca derruba a
  ativação/desativação administrativa em si (Error Boundary backend —
  §15: hook é best-effort, não bloqueia o lifecycle administrativo).
- `health_check(module_id)`: chama `ModuleContract.health_check()` sob
  demanda (decisão do usuário — sem cache), mapeia `HealthResult` pra
  `RuntimeState` (`ok=True` → `READY`, `ok=False` → `DEGRADED`).
- Wiring em `package_manager/lifecycle.py::activate_module/deactivate_module`
  (chamada best-effort, logada, não derruba a resposta HTTP em caso de erro
  do hook do módulo).

**Aceite:** módulo cujo `enable()` levanta exceção ainda fica
administrativamente `INSTALLED` (a ativação não falha), mas Runtime State
vira `FAILED` com `last_error` preenchido — teste explícito disso.

### Slice 4 — ExecutionContext + SDK extension — §8/§9
- `module_runtime/context.py::ModuleExecutionContext` (module_id,
  module_version, runtime_id, services, logger, paths, config,
  cancellation, metadata — §8, literal da spec).
- `sdk/python/techforge_sdk/`: `sdk.services` (proxy fino pro
  `service_registry.find_capability`/`find_service` — só leitura, sem
  reimplementar discovery) e `sdk.runtime` (proxy fino pro
  `ModuleRuntimeRegistry.get(module_id)` — só leitura do próprio estado).

**Aceite:** um módulo em `tmp_path` consegue ler `sdk.runtime.state` e
`sdk.services.find("capability.x")` sem importar nada de `app.*`
diretamente (mesma garantia de isolamento que `sdk.logger`/`sdk.storage`
já dão hoje).

### Slice 5 — ModuleExecutionResult + cancellation/progress (esqueleto) — §16/§19/§21
- `module_runtime/execution.py`: `ModuleExecutionResult` (status, data,
  warnings, errors, duration, metadata — envelope, não payload de
  negócio), `CancellationToken` (`is_cancelled`, `cancel()`), `ProgressState`
  (enum `PREPARING/RUNNING/FINALIZING` + percentual opcional).
- Sem endpoint de execução de negócio fictício — só os tipos, testados
  unitariamente (cancelamento antes/depois de setar, progresso avançando
  em ordem válida).

**Aceite:** cobertura unitária dos 3 tipos; nenhum módulo real precisa
implementar isso ainda (documentado como "disponível para quando um módulo
de longa duração existir" — mesma ressalva já usada nos Known Issues da
Fase 8.1 pra CONFLICT).

### Slice 6 — API + CLI — §26/§27
- `GET /api/v1/runtime/modules` (lista todos com Runtime State),
  `GET /api/v1/runtime/modules/{id}` (estado + last_error + last_execution
  + uptime), `POST /api/v1/runtime/modules/{id}/initialize` (chama
  `enable()`/health sob demanda, mesmo caminho do Slice 3 — não duplica).
- `techforge runtime status|modules|module <id>|initialize <id>` — mesmo
  padrão HTTP-only de `services.py`/`modules.py`.
- `POST .../execute` e `.../cancel` do §26 ficam **fora desta fase**: exigem
  uma ação de execução real que nenhum módulo declara hoje (documentar como
  Known Issue, não implementar endpoint vazio).

**Aceite:** rotas e comandos testados; `GET /runtime/modules/{id}` de um
módulo `DISABLED` retorna Runtime State ausente/None (não é `READY` nem
`EXECUTING` — coerente com "nem todo estado precisa existir pra módulo
inativo").

### Slice 7 — Frontend (Focus Mode) + Developer Center + AI Context + regra final
- **Focus Mode**: botão em `ModuleHost.tsx`/`AppShell` que recolhe
  sidebar/topbar e maximiza a área do módulo — puramente CSS/estado local,
  sem dependência de backend (baixo risco, confirmado na investigação).
- `ModuleHost.tsx` exibe badge de Runtime State (reusa o padrão de
  `ModuleStatusBadge`/`ServiceStatusBadge` já existentes) e chama
  `GET /runtime/modules/{id}` ao montar.
- `docs/developer-center/core/module-runtime.md` (novo): Runtime Lifecycle,
  Module SDK (`sdk.services`/`sdk.runtime`), ExecutionContext, entrypoints,
  Focus Mode, cancellation/progress (como esqueleto disponível), o que foi
  deliberadamente deixado fora (`/execute`/`/cancel` reais).
- `AIContextExporter`: seção "Module Runtime Context" — Runtime State atual
  de cada módulo instalado (mesmo padrão condicional da seção "Dependency
  Governance": só aparece se houver algo relevante a mostrar).
- Teste integrado completo (§31 regra final, tudo em `tmp_path` — mesmo
  padrão de isolamento da Fase 8.1): instalar módulo fictício → Runtime
  State `READY` → simular falha em `enable()` → `FAILED` com `last_error`
  → `health_check()` reavalia → `READY` de novo → shutdown limpa estado
  transiente.
- `tasks/phase-09-report.md` + `phase-audit.md` atualizado.
- Validar no navegador (Playwright): abrir módulo, Focus Mode, badge de
  Runtime State, zero erros de console.

**Aceite:** critérios §33 aplicáveis ao escopo decidido (1-12, 15-23;
13/14 ficam como esqueleto não-exercitado por decisão do usuário) +
suíte completa + `npm run build` limpos.

## Fora de escopo (spec §32, reafirmado)
Containers obrigatórios por módulo, sandbox de segurança completo,
execução distribuída, fila corporativa, multiusuário, autenticação,
Marketplace remoto.

## Fora de escopo (decisão desta fase, documentar como Known Issue)
`POST /runtime/modules/{id}/execute` e `/cancel` (§26) — sem uma ação de
execução de negócio real declarada por nenhum módulo hoje, um endpoint
genérico seria ou vazio (não prova nada) ou arbitrário (risco de segurança
que a própria spec pede pra evitar: "não criar endpoint genérico inseguro
capaz de executar qualquer função privada" — §26). Fica para quando um
módulo real precisar.

## Ordem
1 → 2 → 3 → 4 → 5 → 6 → 7; rodar suíte completa
(`pytest tests -q` + `npm run build`) após cada slice; commit/push por slice.
