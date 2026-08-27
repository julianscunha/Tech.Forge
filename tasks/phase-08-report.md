# Phase 08 Report — Service Registry

## Slice 1 — Fundação (module_type + capabilities + ServiceDescriptor)
- `ParsedManifest`/`ModuleEntry` ganham `module_type` de primeira classe
  (default `"application"`), consolidando o parse de `manifest_raw` que se
  repetia em vários lugares.
- `ServiceContract`/`APIYamlParser` ganham `capabilities: list[str]`,
  declaradas dentro do próprio `docs/contracts/api.yaml` — zero parser novo,
  zero segundo lugar de metadados (spec §5/§10).
- `app/service_registry/descriptor.py`: `ServiceDescriptor` + `ServiceStatus`
  (REGISTERED/ACTIVE/UNAVAILABLE/DISABLED/FAILED/REMOVED — §8), serializável.

## Slice 2 — Registry core (discovery + lifecycle + conflito)
- `app/service_registry/registry.py::ServiceRegistry`: in-memory, singleton,
  `rebuild()` reconstrói a partir do `ModuleRegistry` + `doc_indexer`
  (mesmo padrão de fonte única de verdade — §25). Serviço sem contrato
  válido vira `FAILED` sem derrubar o rebuild inteiro (§26).
- Discovery: `find_service`/`find_by_module`/`find_capability`/
  `list_services`/`list_capabilities`. `list_conflicts()` detecta capability
  duplicada entre serviços `ACTIVE` (§17).
- `sync()` plugado no boot (`main.py`, após `doc_indexer.rebuild()`), em
  `activate_module`/`deactivate_module` e em `manager._hot_reload()`
  (install/update/remove). Shutdown limpa estado transiente (§27).

## Slice 3 — Invocação + erros
- `app/service_registry/invoker.py::invoke(service_id, export_name, **kwargs)`:
  chamada direta de função Python (import dinâmico do `backend/main.py`,
  reconhece função de módulo e método de instância `ModuleContract`) — sem
  round-trip HTTP interno (decisão do plano).
- Valida contrato antes de invocar: export existe, argumentos obrigatórios,
  tipos básicos, sem argumento desconhecido (§14, reusa
  `ServiceExport.parameters`).
- `app/service_registry/errors.py`: 7 erros tipados do §15. Falha da função
  invocada nunca vaza stack trace — vira `ServiceExecutionFailedError`.

## Slice 4 — API + CLI
- `GET /api/v1/services`, `/services/{id}`, `/services/{id}/contract`,
  `/services/capabilities`, `/services/capabilities/{capability}` —
  somente consulta (§23).
- `techforge services list|show|capabilities|contract|status` — zero lógica
  própria, mesmo padrão de `docs.py`.
- `hello_world`/`veeam_m365` ganharam capabilities reais
  (`hello_world.ping`/`.info`, `veeam.m365.calculate` — este último é o
  próprio exemplo do spec §6).

## Slice 5 — Frontend
- `ServiceContractPanel`: badge de status + lista de capabilities.
- `DashboardPage`: card "Serviços Ativos" (contagem ativos/indisponíveis —
  §19, escopo mínimo, sem monitoramento novo).
- `/docs/contracts` (Fase 7) passou a expor `capabilities` — lacuna que o
  painel precisava para renderizar.
- **Validado no navegador real** (Playwright headless, backend servindo
  `dist/`): Dashboard mostra "Serviços Ativos: 2"; Developer Center →
  `hello_world` exibe badge `● ACTIVE` + capabilities `hello_world.ping`/
  `hello_world.info`; zero erros de console.

## Slice 6 — AI Context + notificações
- `AIContextExporter`: seção "Service Contracts" ganha `Status` e
  `Capabilities` por serviço (§22).
- Conflito de capability notifica via `NotificationService` com dedupe
  (mesmo padrão de `docs.py::run_compliance_check`) — não repete a cada
  chamada.

## Slice 7 — Regra final
- Teste integrado completo: activate → registry descobre → capability
  disponível → invoke real (`hello_world.ping`) → argumento inválido
  rejeitado → deactivate → invoke bloqueado (`ServiceDisabledError`) →
  reactivate → invoke funciona de novo.
- Teste de conflito: dois serviços com a mesma capability — reportado,
  ambos continuam descobríveis (nenhuma escolha silenciosa — §17).
- `docs/developer-center/core/service-registry.md` (novo, mesmo padrão de
  `module-registry.md`) + `docs/INDEX.md` atualizado.

## Decisões arquiteturais (confirmadas com o usuário antes do plano)
1. Capabilities declaradas dentro do `api.yaml` (não manifest, não derivado
   automaticamente dos exports).
2. Registry in-memory, reconstruível — sem tabela nova no DB.
3. `module_type` de primeira classe em `ModuleEntry`.
4. Invocação por chamada direta de função Python, não HTTP interno.

## Decisão de implementação (não perguntada, resolvida durante o Slice 3)
`invoke()` recebe `service_id` + `export_name` explícitos, não a string de
capability diretamente — a spec não define um mapeamento capability→export
(capabilities e exports podem ter nomes completamente diferentes, ex:
`aws.cost.read` → export `get_cost_summary`). `find_capability()` continua
sendo o mecanismo de discovery (retorna o(s) descriptor(es) que oferecem
aquela capability); a invocação em si usa o contrato do serviço já resolvido.

## Tests
296 passed, 3 skipped (suíte completa `core/backend/tests`) + 77 CLI
(`cli/tests`, incluindo os 7 novos de `techforge services`). Arquivo novo:
`test_phase8_service_registry.py` (40 casos cobrindo os 7 slices).

## Backend / Frontend / API / Database
Nenhuma tabela nova. Nenhum schema quebrado (campos novos são aditivos,
default seguro). Frontend: `npm run build` limpo (tsc + vite).

## Build
`npm run build` ✅. `npm run lint` **não roda neste ambiente** — `eslint`
não está instalado como devDependency do projeto (`node_modules/.bin/eslint`
ausente); problema pré-existente, não introduzido por esta fase. O `tsc -b`
do build já faz o type-check estrito.

## Known Issues
- `cli/techforge_cli/validators/module_validator.py` ainda duplica parte da
  lógica §16 (achado já registrado no relatório da Fase 7, não tocado aqui).
- Toolchain de lint do frontend quebrada (ver "Build" acima) — candidato a
  correção pontual futura, fora do escopo desta fase.
- Conflito de capability é **reportado**, não resolvido — política de
  precedência fica para fase futura (spec §17 explícito).
- "Remove" do ciclo completo (§28) não foi testado destrutivamente contra
  `hello_world`/`veeam_m365` por serem módulos de referência usados por toda
  a suíte — a limpeza do registry na remoção está coberta unitariamente
  (`test_rebuild_clears_previous_state`, Slice 2) e pelo hook em
  `manager.py::remove()` → `_hot_reload()` → `sync_service_registry()`.
- ~~**Discovery em escala**: `/services` sem busca~~ — **resolvido**:
  `ServiceRegistry.search()` + `GET /api/v1/services?q=` +
  `techforge services search <termo>` (busca por `service_id`,
  capabilities, nome/descrição de export, category-agnóstico — ver
  `tasks/phase8-followup-capability-search.md`).
