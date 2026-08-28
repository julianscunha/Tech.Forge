# Phase 09 Report — Module Runtime & Execution

## Slice 1 — Loader único (refactor mecânico)
- `app/module_runtime/loader.py::load_module_file()` consolida o padrão
  `importlib.util.spec_from_file_location` → `exec_module` que estava
  duplicado em `module_engine/plugin_loader.py`,
  `service_registry/invoker.py` e
  `package_manager/manager.py::_call_uninstall_hook`. Mesma semântica
  observável nos 3 pontos — nenhum teste existente mudou de comportamento.

## Slice 2 — Runtime State separado do Administrative State
- `app/module_runtime/state.py::RuntimeState` (READY/INITIALIZING/
  EXECUTING/DEGRADED/FAILED/STOPPED — efêmero, nunca persistido) +
  `ModuleRuntimeRegistry` in-memory (mesmo padrão de fonte única de
  verdade do `ServiceRegistry`, Fase 8).
- `rebuild()` só cria entrada para módulos administrativamente
  `INSTALLED`; preserva `last_error`/`last_execution` entre rebuilds do
  mesmo módulo. Conectado no `lifespan` (`main.py`): `rebuild()` após o
  boot do Module Loader, `clear_transient_state()` no shutdown.

## Slice 3 — Lifecycle hooks reais
- `app/module_runtime/lifecycle.py` conecta de verdade `enable()`/
  `disable()`/`health_check()` do `ModuleContract` — declarados desde a
  Fase 3, nunca chamados por nada do Core até aqui (só `uninstall()` já
  era invocado, desde a Fase 4).
- Best-effort: falha em qualquer hook marca Runtime State `FAILED`/
  `DEGRADED` com `last_error`, nunca bloqueia a transição administrativa
  em si (Error Boundary backend — §15).
- **Correção descoberta durante o teste integrado do Slice 7**: o loader
  do Slice 1, usado ingenuamente, recarregava e reexecutava o arquivo do
  módulo a cada chamada — perdendo o estado da instância entre
  `enable()`/`health_check()`/`disable()` (ex: um contador ou flag
  interna do módulo não sobrevivia à próxima chamada). Corrigido com um
  cache `_instances: dict[module_id, instance]` em `lifecycle.py` — a
  mesma instância persiste enquanto o módulo estiver ativo, descartada
  só em `discard_instance()` (chamado na remoção física do módulo,
  `manager.py::remove()`). O `invoker.py` da Fase 8 continua recarregando
  a cada chamada deliberadamente — invocação de capability é stateless
  por natureza, não representa "uma instância rodando".

## Slice 4 — ExecutionContext + SDK extension
- `app/module_runtime/context.py::ModuleExecutionContext.build()`: forma
  oficial (lado Core) de descrever a que recursos uma execução de módulo
  tem acesso — identidade, Service Registry, logger, paths, `runtime_id`
  novo a cada chamada (§8, literal da spec).
- `sdk.services` (`ServicesSDK`) e `sdk.runtime` (`RuntimeSDK`) novos no
  SDK Python — proxies finos, somente leitura, via HTTP local pro Core
  (mesmo padrão de isolamento de `sdk.notifications`: o pacote SDK nunca
  importa `app.*` diretamente, mesmo rodando no mesmo processo).

## Slice 5 — ModuleExecutionResult + cancellation/progress (esqueleto)
- `app/module_runtime/execution.py`: `ModuleExecutionResult` (envelope,
  não payload de negócio) com factories `success()`/`failure()`;
  `CancellationToken` (sinalização cooperativa, nunca mata a execução à
  força) + `ExecutionCancelledError`; `ProgressPhase`
  (PREPARING/RUNNING/FINALIZING) + `ProgressReport` (percentual 0-100
  validado).
- Decisão do usuário: só os tipos, testados unitariamente — sem fluxo
  real de longa duração pra exercitar, já que nenhum módulo hoje tem uma
  operação que justifique isso de verdade.

## Slice 6 — API + CLI
- Rotas novas no mesmo router `/runtime` já existente (Fase 6):
  `GET /runtime/modules`, `GET /runtime/modules/{id}`,
  `POST /runtime/modules/{id}/initialize` (reroda `health_check()` sob
  demanda, reusa o Slice 3 — não duplica).
- `techforge runtime status|modules|module <id>|initialize <id>` — mesmo
  padrão HTTP-only de `services.py`/`modules.py`.
- `POST .../execute` e `.../cancel` (spec §26) ficam fora do escopo desta
  fase (ver Known Issues).

## Slice 7 — Frontend + Developer Center + AI Context + regra final
- **Focus Mode** (`useFocusModeStore`, zustand, não persistido): botão em
  `ModuleHost.tsx` recolhe `Sidebar`/`Header` via `AppShell.tsx`,
  escopado à rota `/modules/:id` — sair do módulo limpa o estado
  automaticamente. Validado no navegador (Playwright): recolhe/expande
  sem nova aba, zero erros de console.
- `ModuleHost.tsx` exibe badge de Runtime State (`GET
  /runtime/modules/{id}`) ao lado da versão do módulo.
- `docs/developer-center/core/module-runtime.md` (novo) +
  `docs/INDEX.md` atualizado.
- `AIContextExporter`: seção "Module Runtime Context" — Runtime State
  atual de cada módulo instalado, só aparece se houver ao menos um
  módulo com Runtime State (mesmo padrão condicional da seção
  "Dependency Governance").
- Teste integrado completo (§31, tudo em `tmp_path`): instalar módulo
  fictício → `activate` real via API interna (`enable()` de verdade,
  cache de instância do Slice 3) → `READY` → `GET
  /runtime/modules/{id}` via API → simular falha (`health_check()`
  reporta unhealthy usando a MESMA instância) → `POST .../initialize` →
  `DEGRADED` → Core continua respondendo normalmente
  (`/api/v1/platform/status` 200) → `deactivate` real (`disable()` de
  verdade) → `STOPPED` → `clear_transient_state()` prova que Runtime
  State nunca sobrevive a um shutdown.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)
1. Escopo de execução para Application Modules: esqueleto do envelope +
   conectar os hooks mortos do `ModuleContract`, sem inventar uma
   "execução" fictícia de negócio em `hello_world`/`veeam_m365`.
2. Cancellation/progress: esqueleto de tipos, sem fluxo real pra
   exercitar.
3. Health check: sob demanda, sem cache.
4. Consolidação dos 3 loaders duplicados: sim, dentro desta fase.
5. Pacote novo `app/module_runtime/` (evita colisão de nome com
   `app/runtime`, que já existia e é o runtime **da plataforma**, não
   por módulo).

## Decisão de implementação (não perguntada, resolvida durante o Slice 7)
`POST /runtime/modules/{id}/initialize` chama `health_check()`, não
`enable()`. A spec (§26/§27) usa a palavra "initialize" de forma
ambígua — mas re-chamar `enable()` num módulo já ativo não é
necessariamente idempotente (o contrato só garante idempotência
explícita pra `install()`), enquanto `health_check()` foi desenhado no
Slice 3 exatamente pra ser chamado repetidamente sob demanda. `enable()`
continua reservado ao momento real de ativação administrativa
(`activate_module`).

## Tests
431 passed, 3 skipped (suíte completa `core/backend/tests`) + 79 CLI
(inalterado — cobertura do `techforge runtime` via integração no
backend, mesmo padrão de `techforge dependencies`). Arquivo novo:
`test_phase9_module_runtime.py` (60 casos cobrindo as 7 slices);
`test_phase7_ai_context.py` ganhou 2 casos para "Module Runtime Context".

## Backend / Frontend / API / Database
Nenhuma tabela nova — Runtime State é 100% in-memory, por design (§29).
Frontend: `npm run build` limpo (`tsc -b && vite build`), nenhuma
dependência nova.

## Build
`npm run build` ✅. `npm run lint` continua não rodando neste ambiente —
mesmo problema pré-existente já documentado nos relatórios das Fases 8 e
8.1 (`eslint` ausente como devDependency), não introduzido por esta fase.

## Known Issues
- `POST /runtime/modules/{id}/execute` e `/cancel` (spec §26) não foram
  implementados — sem uma ação de execução de negócio real declarada por
  nenhum módulo hoje, um endpoint genérico seria vazio (não prova nada)
  ou arbitrário (risco de segurança que a própria spec pede pra evitar).
  Fica para quando um módulo real precisar.
- `BLOCKED`/Runtime State não são recalculados automaticamente no boot
  para módulos cuja dependência ficou insatisfeita enquanto a plataforma
  estava desligada — só reavaliados numa tentativa explícita de
  `activate` ou `initialize`. Candidato natural pra uma fase futura de
  runtime execution mais avançada, se necessário.
- `CancellationToken`/`ProgressReport` existem só como tipos testados —
  nenhum módulo real os usa ainda (decisão do usuário, ver acima).
