---
title: Registry Consolidation
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, fase-18, consolidation]
---

# TechForge Core — Registry / Package / Dependency / Runtime Consolidation

> Fase 18 (Platform Finalization & Architecture Consolidation), Slice 3.
> Verificação empírica contra o código real (`ast-grep outline` + grep de
> chamadas), não confirmação por memória do CLAUDE.md. Ver também
> [`core-inventory.md`](core-inventory.md), [`dependency-map.md`](dependency-map.md)
> (já continha achados prévios reaproveitados aqui) e
> [`public-contracts.md`](public-contracts.md).

## §11 — Registry consolidation

A spec pede fonte única de verdade para: Installed Modules, Active Modules,
Versions, States, Dependencies, Trust, Integrity.

| Dado | Fonte única confirmada | Evidência |
|---|---|---|
| Installed Modules | `module_engine.registry.registry` (singleton `ModuleRegistry`) | `registry.all()` — nenhum outro dict/lista paralela de módulos instalados encontrado em `api/routes` ou `services` (reconfirma achado da Slice 1) |
| Active Modules | `ModuleEntry.is_active` / `registry.by_status(ModuleStatus.INSTALLED)` | Mesmo objeto do registry, não uma segunda lista |
| Versions | `ModuleEntry.version` (campo do próprio registry entry) | Não há tabela/cache de versão separada; `PackageInfo.installed_version` (package_manager) é lido do mesmo registry, não duplicado |
| States | `ModuleEntry.status` (`ModuleStatus` enum) | Único enum administrativo; ver nota de fatiamento em 3 camadas já documentada em `public-contracts.md` (§10) — não é duplicação, é fatiamento por responsabilidade (Administrative vs Runtime vs Package job) |
| Dependencies | `ModuleEntry.manifest_raw["dependencies"]`, parseado on-demand por `DependencyParser.parse()` | Confirmado: todos os 5 call-sites (`validator.py:41`, `resolver.py:28`, `lifecycle.py:35`, `graph.py:33`, `api/routes/module_verification.py:169`) parseiam do `raw` do manifest — nenhuma cópia persistida separada dos dados de dependência |
| Trust | `TrustResolver.resolve()` (computado on-demand a partir de `IntegrityResult` + `Publisher` + `SignatureStatus`) | Não é "registrado" em lugar nenhum como estado persistente — computado sob demanda em `doc_engine/__init__.py:237` e `api/routes/module_verification.py:127`. Sem duplicação porque não há armazenamento primário a duplicar |
| Integrity | `integrity.json` por módulo (filesystem, escrito em `write_integrity_manifest`) + `verify_module_integrity()` (compara hash atual vs. manifest) | Fonte única = arquivo em disco por módulo; único ponto de verificação (`module_trust/verification.py:22`), chamado no boot (`main.py:114`) e sob demanda (`module_verification.py:64`) |

**Conclusão §11**: nenhum registry/estado paralelo encontrado. Confirma e
reforça o achado já registrado na Slice 1 ("Nenhum resolver/registry
duplicado encontrado").

## §12 — Package lifecycle consolidation

Fluxo oficial da spec (install): `Acquire → Inspect → Validate → Verify
Trust → Stage → Install → Register → Activate`.

Fluxo real em `package_manager/manager.py::install()` (docstring própria,
linhas 133-262): `1. Archive integrity → 2. Read manifest → 3.
Compatibility → 3.5 Guard de estado inválido → 4. Duplicate check → 4.5
Dependency governance → 5. Extract (+ write integrity manifest) → 6.
Hot-reload registry`.

**Achado 5 — "Verify Trust" não é um gate no fluxo de install real.**
`install()` não chama `TrustResolver.resolve()`, `SignatureProvider.verify()`
nem `SecurityPolicy.allows_install()` em nenhum ponto — grep confirma que
`allows_install()`/`requires_warning()` (`module_trust/security_policy.py:28,32`)
são definidos e exportados mas **nunca chamados** em lugar nenhum do
código (`core/backend/app`). Verificação de integridade só acontece
**depois** da instalação (escreve o `integrity.json`) e a checagem de
trust/assinatura só roda no boot (`main.py:114`, para módulos já
instalados) ou sob demanda via `/module-verification` (API consumida pela
UI para exibir badge de trust) — nunca como portão que bloqueia ou avisa
antes de instalar.

Isso é consistente com a decisão documentada em
`docs/developer-center/core/module-trust.md:169-172`: *"`DesktopSecurityPolicy`
(default) nunca bloqueia instalação por Trust Level isolado (`allows_install`
sempre `True`) ... mas sinaliza aviso (`requires_warning`)"* — ou seja, o
comportamento de não-bloquear é intencional, mas o mecanismo de aviso
(`requires_warning`) que a doc descreve como existente **não está de fato
conectado a nenhum call-site** — é uma função pronta e correta, mas morta.

**Classificação**: não é duplicação, é uma lacuna de integração (contrato
existe, decisão de produto existe, ligação entre os dois nunca foi feita).
Não corrigido nesta slice — decisão de UX (`requires_warning` deveria virar
um campo no response de install/`PackageInfo` consumido pela UI?) não é
"consolidação óbvia de baixo risco", registrado como item de débito técnico
para a Slice 9.

O fluxo de **update** (`manager.py::update()`) segue o mesmo padrão —
não verificado com o mesmo detalhe nesta slice por já compartilhar a
mesma lacuna de trust-gate do install (mesma causa raiz, não duplicar o
achado).

## §13 — Dependency system consolidation

Verificado: `DependencyResolver`, `DependencyGraph`, `DependencyValidator`
são cada um uma única classe, usados consistentemente:

- `api/routes/dependencies.py` — `get_dependencies` usa `DependencyResolver.resolve()`;
  `validate_all` usa `DependencyValidator.validate()`; `get_graph` usa
  `DependencyGraph.build()`. Nenhuma lógica de resolução reimplementada na
  rota.
- `package_manager/manager.py:211` (install) e `lifecycle.py` (activate/deactivate)
  chamam os mesmos `DependencyValidator`/`check_can_activate`/`check_can_deactivate`
  do `dependency_engine` — nenhum resolver paralelo para o Installer.
- Nenhuma lógica de resolução de dependência encontrada no lado do
  frontend (`core/frontend/src`) além de exibir o que a API já resolveu —
  não há resolver duplicado para UI.

**Conclusão §13**: confirmado, sem achado novo. Nenhum resolver paralelo
para UI, Runtime ou Installer — reforça o achado da Slice 1.

## §14 — Runtime consolidation

Verificado que existe um único mecanismo de carregamento dinâmico de
código de módulo: `module_runtime/loader.py::load_module_file()`
(`importlib.util.spec_from_file_location` + `exec_module`) — é o **único**
lugar do código com essa chamada (grep por `importlib.util`/`import_module`
não retornou nenhuma outra ocorrência fora deste arquivo).

Todos os 5 consumidores importam desse único loader, sem cópia própria:
`service_registry/invoker.py`, `module_runtime/lifecycle.py`,
`module_engine/plugin_loader.py`, `package_manager/config_migration.py`,
`package_manager/manager.py` (hook de desinstalação).

`service_registry/invoker.py::invoke()` é o caminho oficial de execução de
Service Module exports — carrega via `load_module_file`, valida
argumentos (`_validate_arguments`), gera `execution_id`, persiste
`ExecutionHistory` (`_persist_execution_history`) e emite métricas/eventos
via `observability`. Nenhuma rota de API chama `load_module_file` ou
executa código de módulo diretamente — todas passam por `invoke()` ou pelo
lifecycle hooks (`on_activate`/`on_deactivate`/`health_check` em
`module_runtime/lifecycle.py`).

**Conclusão §14**: confirmado — execução de módulo sempre passa pelo
Runtime oficial (loader único + `ModuleExecutionContext` + lifecycle
hooks + observability). Nenhuma rota improvisada executando módulo
diretamente.

## Resumo

| Área | Resultado |
|---|---|
| Registry (§11) | Fonte única confirmada para todos os 7 itens pedidos pela spec — nenhuma correção necessária |
| Package lifecycle (§12) | Fluxo real difere do fluxo de 8 passos da spec (sem "Verify Trust" como gate); **achado real novo** (Achado 5) registrado como débito técnico — não corrigido nesta slice (decisão de UX/produto) |
| Dependency system (§13) | Único resolver/graph/validator confirmado, sem achado novo |
| Runtime (§14) | Único loader e caminho de execução oficial confirmado, sem achado novo |

**Pytest**: suíte completa rodada como sanity check antes de escrever este
documento — nenhuma alteração de código foi feita nesta slice (achado
registrado como débito, não corrigido às cegas), portanto sem
regressão esperada.
