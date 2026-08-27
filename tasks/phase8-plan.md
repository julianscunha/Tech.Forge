# Plano — Fase 8: Service Registry

> Spec: docs/phases/08-Fase-08-Service-Registry.md
> Auditoria: phase-audit.md — Fase 8 ❌ (`app/services/registry.py` é CRUD de
> Category/Module, sem relação com Service Registry). Fase 8.1 (Dependency
> Governance) fica fora deste plano — spec §29 e §4 são explícitas.

## Premissas validadas (investigação de código real)

1. ❌ Não existe Service Registry — `app/services/registry.py` (`CategoryService`/
   `ModuleService`) é CRUD SQLAlchemy sobre tabelas `Category`/`Module`, sem
   relação nenhuma com descoberta de serviços. Nome colide; novo código NÃO
   entra aí.
2. ✅ `ModuleRegistry` in-memory (`app/module_engine/registry.py`) já é a
   fonte única de verdade documentada — Service Registry deve seguir o
   mesmo padrão (singleton in-memory, reconstruível no boot).
3. ⚠️ `ModuleEntry` não tem `module_type` de primeira classe — cada
   consumidor (`docs.py::_get_module_type`, `lifecycle.py`) reparseia
   `manifest_raw` na mão. Será consolidado neste plano (decisão do usuário).
4. ✅ `ServiceContract`/`ServiceExport` (`app/doc_engine/models.py`) e
   `APIYamlParser` (Fase 7) já validam contratos completos — reuso
   obrigatório (spec §10), zero parser novo.
5. ✅ `ServiceContract.dependencies: list[str]` já existe no modelo mas não é
   usado em lugar nenhum — pertence à Fase 8.1, não tocar aqui.
6. ✅ `hello_world` e `veeam_m365` já são `module_type: service`, com
   `docs/contracts/api.yaml` completo e testado (Fase 7) — servem como os
   "Service Modules reais de teste" da regra final, sem precisar criar módulo
   novo.
7. ✅ `package_manager/lifecycle.py` (`activate_module`/`deactivate_module`) e
   `manager.py::remove()` já são os pontos de gancho corretos pro ciclo
   registrar/desregistrar (spec §7/§26/§27).
8. ✅ `plugin_loader.py::mount_module_routers()` roda no `lifespan` do
   `main.py` e no hot-activate — ponto natural pra "Discover Service Modules
   → Register Services" (§26), rodando depois dele e depois de
   `doc_indexer.rebuild()` (contratos já parseados, reusar
   `doc_indexer.all_contracts()`).
9. ✅ `ServiceContractPanel.tsx` já existe e já é usado em
   `DeveloperCenterPage.tsx` — cobre boa parte do §20/§21 (exports/params/
   returns/examples). Falta só "Capabilities" e status do serviço.
10. ✅ `AIContextExporter` já tem seção "## Service Contracts" completa
    (service_id/module_id/version/description/dependencies/exports) — §22
    está ~90% coberto, falta só capabilities/status.
11. ✅ `cli/techforge_cli/commands/docs.py` é o padrão a copiar pra CLI nova:
    zero lógica própria, só HTTP GET pro Core + `rich.Table`.
12. ✅ `NotificationService.create()` com dedupe (padrão já usado em
    `docs.py`) serve pra notificar `CAPABILITY_CONFLICT`.

## Decisões arquiteturais (confirmadas com o usuário)

1. **Capabilities**: declaradas dentro de `docs/contracts/api.yaml` (mesmo
   arquivo já parseado pelo `APIYamlParser`) — lista de strings no topo do
   yaml (`capabilities: [aws.cost.read, aws.cost.summary]`). Zero segundo
   sistema de metadados (spec §5 proíbe explicitamente).
2. **Persistência**: in-memory, reconstruível no boot — mesmo padrão do
   `ModuleRegistry`. Nenhuma tabela nova no DB nesta fase (spec §25).
3. **`ModuleEntry.module_type`**: campo novo de primeira classe (default
   `"application"`), populado no `ModuleLoader.scan_installed()` a partir do
   manifest. Consolida o parse hoje espalhado.
4. **Invocação**: chamada direta de função Python via import dinâmico (mesmo
   mecanismo do `plugin_loader`) — sem round-trip HTTP interno.

## Novo módulo

`core/backend/app/service_registry/` (paralelo a `module_engine/`,
`package_manager/`, `doc_engine/`):
```
service_registry/
  __init__.py       # singleton `service_registry` + API pública
  descriptor.py      # ServiceDescriptor, ServiceStatus (enum)
  errors.py           # SERVICE_NOT_FOUND, CAPABILITY_NOT_FOUND, etc. (§15)
  invoker.py          # invoke() — resolve + valida argumentos + chama função
```

## Slices

### Slice 1 — ModuleEntry.module_type + ServiceDescriptor + capabilities no contrato (TDD)
- `ModuleEntry`: campo `module_type: str = "application"`, populado em
  `ModuleLoader.scan_installed()`.
- `ServiceContract`/`APIYamlParser`: campo `capabilities: list[str]`
  (default `[]`), parseado do topo do `api.yaml`.
- `service_registry/descriptor.py`: `ServiceStatus` (REGISTERED, ACTIVE,
  UNAVAILABLE, DISABLED, FAILED, REMOVED — §8) e `ServiceDescriptor`
  (service_id, module_id, module_version, service_version, capabilities,
  contract, status, metadata — §11), serializável (dataclass + `to_dict()`).
- Testes: `module_type` default e lido do manifest; `capabilities` parseadas
  do yaml (string simples e lista); `ServiceDescriptor` serializa.

**Aceite:** `hello_world`/`veeam_m365` continuam 100% compliant (Fase 7 não
regride); `ModuleEntry` de um módulo application tem `module_type="application"`.

### Slice 2 — Service Registry core: discovery + lifecycle (TDD) — §2/§7/§8/§9/§17/§26/§27
- `service_registry/__init__.py`: singleton `service_registry`
  (`dict[str, ServiceDescriptor]` por `service_id`), API:
  `register(module_entry, contract)`, `deregister(module_id)`,
  `find_service(service_id)`, `find_capability(capability)`,
  `list_services()`, `list_capabilities()`.
- Detecção de conflito (§17): se duas capabilities colidem entre serviços
  ativos, `register()` marca ambos com um flag de conflito e loga —
  `CAPABILITY_CONFLICT` (sem escolher silenciosamente).
- Hook de inicialização (§26): em `main.py::lifespan`, depois de
  `mount_module_routers()` + `doc_indexer.rebuild()`, iterar módulos
  `module_type == "service"` com status INSTALLED, carregar contrato via
  `doc_indexer.all_contracts()` (não reparsear) e `register()`.
- Hooks de lifecycle: `lifecycle.py::activate_module`/`deactivate_module` e
  `manager.py::remove()` chamam `register()`/`deregister()` no serviço
  correspondente, se o módulo for `service`.
- Shutdown (§27): `service_registry.clear_transient_state()` chamado no
  shutdown do `lifespan` — não apaga metadados de instalação, só o estado
  in-memory.
- Testes: registro no boot; deactivate → `find_service` retorna UNAVAILABLE;
  reactivate → ACTIVE de novo; remove → desaparece de `list_services()`;
  dois serviços com capability igual → conflito reportado; reconstrução do
  zero a partir dos módulos instalados (sem depender de estado anterior).

**Aceite:** teste integrado do §28 "Install → Activate → discover → capability
available → deactivate → unavailable" passa com `hello_world` real.

### Slice 3 — Invocação + validação de argumentos + erros (TDD) — §12/§13/§14/§15
- `service_registry/errors.py`: exceptions tipadas (`ServiceNotFoundError`,
  `CapabilityNotFoundError`, `ServiceDisabledError`, `ServiceUnavailableError`,
  `ContractViolationError`, `InvalidArgumentsError`, `ServiceExecutionFailedError`).
- `service_registry/invoker.py::invoke(capability, **kwargs)`: resolve serviço
  via `find_capability`, valida `kwargs` contra `parameters` do export
  (obrigatórios presentes, tipos básicos — reusa `ServiceExport.parameters`,
  sem schema paralelo — spec §14), importa dinamicamente o módulo
  (`backend/main.py`) e chama a função pelo nome do export, captura exceção
  da função em `ServiceExecutionFailedError` (sem vazar stack trace de outro
  módulo — spec §15).
- Testes: invocação bem-sucedida (`hello_world.ping` real); argumento
  obrigatório faltando → `InvalidArgumentsError`; capability inexistente →
  `CapabilityNotFoundError`; serviço desativado → `ServiceDisabledError`;
  exceção interna da função → `ServiceExecutionFailedError` sem stack trace
  do módulo vazando pro chamador.

**Aceite:** regra final da spec — "consumir a capability por outro módulo de
teste" — validada chamando `invoke()` a partir de um teste que simula um
Application Module consumidor (sem precisar criar módulo novo instalado).

### Slice 4 — APIs + CLI (TDD) — §23/§24
- `api/routes/services.py` (`prefix="/services"`, registrado em
  `api/__init__.py` como os demais):
  - `GET /services` → `list_services()`
  - `GET /services/{service_id}` → `find_service()`
  - `GET /services/{service_id}/contract` → contrato do serviço
  - `GET /services/capabilities` → `list_capabilities()`
  - `GET /services/capabilities/{capability}` → `find_capability()`
  - Somente consulta (spec §23) — nenhuma rota genérica de invocação pública.
- `cli/techforge_cli/commands/services.py`: `techforge services list|show
  <id>|capabilities|contract <id>|status` — segue o padrão de `docs.py`
  (HTTP GET pro Core, zero lógica própria).
- Testes: cada rota (schema Pydantic próprio, tipo `ServiceDescriptorRead`),
  CLI com `CliRunner` (mock do HTTP).

**Aceite:** `techforge services list` mostra `hello_world`/`veeam_m365`
depois de `techforge platform start`.

### Slice 5 — Frontend: Capabilities + status do serviço — §20/§21
- `ServiceContractPanel.tsx`: adicionar seção "Capabilities" (lista de
  badges) e indicador de `status` (REGISTERED/ACTIVE/UNAVAILABLE/...).
- `lib/api.ts`: `servicesApi.list()/get()/capabilities()` (fetch em lote,
  mesmo padrão de `completenessApi`).
- Developer Center: navegação Service → Contract → Capabilities → Examples
  (§21) já existe via `ServiceContractPanel`; só estender com capabilities.
- Dashboard (§19, escopo mínimo): contador simples "N serviços ativos / M
  indisponíveis" — não criar monitoramento novo, reusar componente de
  contador já existente no Dashboard.

**Aceite:** `npm run build && npm run lint` limpos; UI mostra capabilities de
`hello_world` e `veeam_m365` no Developer Center.

### Slice 6 — AI Context + notificações de conflito — §17/§22
- `AIContextExporter`: seção "## Service Contracts" ganha `capabilities` e
  `status` por serviço (dado já existente no `ServiceDescriptor`, sem
  reparsear nada).
- `POST` interno (chamado do Slice 2, não uma rota nova): ao detectar
  `CAPABILITY_CONFLICT`, notificar via `NotificationService.create()` com
  dedupe (mesmo padrão de `docs.py::run_compliance_check`) — não notificar
  a cada verificação repetida, só na mudança de estado.

**Aceite:** teste de conflito do Slice 2 também verifica notificação criada
(dedupe em chamadas repetidas).

### Slice 7 — Regra final + docs + relatório
- Teste integrado completo do §28 (rodando via `hello_world` real): install →
  activate → registry descobre → capability disponível → outro "consumidor"
  de teste resolve e invoca → resultado → deactivate → indisponível →
  reactivate → remove → confirma limpeza do registry → conflito
  (`veeam_m365` + um contrato de teste com capability duplicada em `tmp_path`).
- `docs/developer-center/core/` novo doc `service-registry.md` (mesmo padrão
  de `module-registry.md`) — arquitetura, discovery, invocação, erros.
- `tasks/phase-07-report.md`-style: `tasks/phase-08-report.md` com o formato
  pedido pela "Regra final" da spec (Service Registry / Service Discovery /
  Capabilities / Contracts / Invocation / Errors / Lifecycle Integration /
  Developer Center / AI Context / API / CLI / Tests / Build / Known Issues).
- `tasks/phase-audit.md`: atualizar linha da Fase 8.

**Aceite:** todos os critérios de aceitação §30 (1–17) marcados, suíte
completa + `npm run build` + `npm run lint` limpos.

## Fora de escopo (spec §29, reafirmado)
Dependency Governance completo (Fase 8.1), resolvedor automático de grafo,
múltiplas versões simultâneas, marketplace remoto, assinatura digital,
multiusuário, autenticação, workflow engine complexo.

## Ordem
1 → 2 → 3 → 4 → 5 → 6 → 7; rodar suíte completa (`pytest tests -q` +
`npm run lint`/`build`) após cada slice; commit/push por slice.
