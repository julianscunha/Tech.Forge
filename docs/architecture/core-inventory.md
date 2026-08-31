---
title: Core Inventory
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — Inventário de Componentes

> Construído a partir do código real (`ast-grep outline` sobre
> `core/backend/app/`), não de memória/spec. Ver também
> [`dependency-map.md`](dependency-map.md) para o mapa de dependências.

Cada componente = uma pasta de `core/backend/app/`. "Tests" indica se
existe suíte correspondente em `core/backend/tests/` (não lista
arquivo por arquivo). "Docs" indica se há artigo dedicado em
`docs/developer-center/core/`.

| Componente | Purpose | Interface pública principal | Depende de | Persistência | Tests | Docs |
|---|---|---|---|---|---|---|
| `module_engine` | Manifest, validação, registry in-memory (fonte única de verdade), loader, navegação, plugin mount | `registry` (singleton), `ModuleLoader`, `ManifestParser`, `NavigationBuilder`, `mount_module_routers` | `module_trust`, `package_manager` (via journal/status) | Nenhuma direta (espelha pra `models.registry` via `services.registry_sync`) | ✅ | ✅ |
| `module_runtime` | Runtime State separado do Administrative State; `ModuleExecutionContext`; lifecycle hooks (activate/deactivate/health_check) | `module_runtime_registry`, `ModuleExecutionContext`, `on_activate`/`on_deactivate`/`health_check` | `module_engine.enums`, `observability` | `ModuleKVStoreRow` (Storage API) | ✅ | ✅ |
| `package_manager` | Ciclo de vida do pacote `.mod`: acquire/inspect/validate/verify/stage/install/register/activate; catálogo remoto; compatibilidade | `PackageManager`/`package_manager` (singleton), `activate_module`/`deactivate_module`, `CatalogAggregator` | `module_engine`, `module_trust`, `dependency_engine`, `service_registry`, `module_runtime`, **`app.main`** (import deferido, ver dependency-map) | `CatalogSourceConfig`, `CatalogFavorite` | ✅ | ✅ |
| `dependency_engine` | Parser de `dependencies:` do manifest, grafo, resolver, validador de direção (Application→Service), lifecycle guards | `DependencyParser`, `DependencyGraph`, `DependencyResolver`, `DependencyValidator`, `check_can_activate/deactivate/remove` | `module_engine.enums`, `service_registry.descriptor` | Nenhuma (computado on-demand) | ✅ | ✅ |
| `service_registry` | Discovery/invocação de Service Modules, conflito de capability (reportado, não resolvido — débito conhecido) | `service_registry` (singleton `ServiceRegistry`), `invoke()` | `module_engine.enums`, `doc_engine.models.ServiceContract`, `observability` | Nenhuma direta (persiste execução via `ExecutionHistoryService`) | ✅ | ✅ |
| `module_trust` | Integrity manifest, Publisher Registry, `TrustResolver`, `SignatureProvider` (Ed25519 real), `SecurityPolicy` | `TrustResolver`, `Ed25519SignatureProvider`/`default_signature_provider`, `DesktopSecurityPolicy`/`default_security_policy`, `verify_module_integrity` | Nenhuma de outro componente do Core (camada de baixo nível) | `Publisher` (model) | ✅ | ✅ |
| `security` | `ModuleSecretStore` (cofre via `keyring`, isolado por module_id), redação de log por padrão de chave | `ModuleSecretStore`, `SecretRedactionFilter` | Nenhuma | Nenhuma (SO keyring, fora do DB) | ✅ | ✅ |
| `observability` | Logger central JSON, `EventBus` genérico, `MetricEmitter`, Diagnostic Codes, notification bridge, startup diagnostics | `event_bus`, `metric_emitter`, `configure_logging`, `wire_notifications`, `StartupDiagnostics` | Nenhuma (infraestrutura transversal, todos os outros dependem dele) | Nenhuma direta (Execution History/Error Registry ficam em `models/`) | ✅ | ✅ |
| `doc_engine` | Indexação/busca de docs, `AIContextExporter`, Documentation Compliance Checker, parser de `api.yaml` | `doc_indexer`, `doc_search`, `AIContextExporter`, `DocCompletenessChecker` | `models.notifications` (só pra `docs.py` via API, não o engine em si) | Nenhuma (índice em memória, fonte é o filesystem) | ✅ | ✅ |
| `runtime` | Estado runtime da PLATAFORMA (não do módulo — ver nota de colisão de nome no dependency-map): boot/ready/degraded/shutdown, `TechForgeRuntime` | `runtime` (singleton), `RuntimeState` (enum de plataforma), `RuntimeEvent` | `observability` (via eventos) | Nenhuma | ✅ | ✅ |
| `db` | Engine async (aiosqlite), session factory, migração leve, `StorageProvider` (espaço em disco) | `get_db`, `init_db`, `AsyncSessionLocal`, `storage_provider` | Nenhuma (infraestrutura de base) | É a própria camada de persistência | ✅ | ✅ |
| `core` | Settings centralizado (env vars), paths oficiais por SO (`platformdirs`) | `settings`, `install_dir()`, `user_data_dir()` | Nenhuma | Nenhuma | ✅ | ✅ |
| `storage` | `TTLCache` genérico (extraído do Catálogo na Fase 12) | `TTLCache` | Nenhuma | Nenhuma | ✅ | — (utilitário, sem artigo próprio) |
| `services` | Camada de aplicação: `CategoryService`/`ModuleService` (CRUD registry↔DB), `NotificationService`, `PublisherService`, `SystemDiagnosticService`, `ReleaseReadinessReport`, etc. | Um serviço por arquivo — ver `dependency-map.md` §API layer | `db`, `models`, `module_engine`, `module_trust` | Via `models/*` (SQLAlchemy) | ✅ | parcial (alguns serviços não têm artigo dedicado, cobertos pelo componente que os usa) |
| `api/routes` | Camada HTTP (FastAPI routers), um arquivo por área | Ver inventário de rotas no `dependency-map.md` | `services`, `module_engine`, `package_manager`, `module_trust`, `dependency_engine`, `service_registry`, `doc_engine`, **e em 3 pontos, `models.*` direto (ver achado no dependency-map)** | N/A (camada de transporte) | ✅ (via TestClient) | N/A |
| `models` | SQLAlchemy ORM: `Category`, `Module`, `Publisher`, `Notification`, `CatalogSourceConfig`, `CatalogFavorite`, `ModuleConfiguration`, `ModuleKVStoreRow`, `ExecutionHistory`, `ErrorRecord` | Uma classe por arquivo | `db.database.Base` | É o schema | ✅ (via services/routes) | N/A |
| `schemas` | Pydantic — contratos de API (`ModuleRead`, `PublisherRead`, `NotificationRead`, etc.) | Um schema por domínio | Nenhuma | N/A | ✅ (via routes) | N/A |

## Fronteiras confirmadas

- **Core → Module**: nenhum módulo instalado (`modules/installed/hello_world`,
  `system_health_check`, `system_information_service`) importa `app.*`
  diretamente — confirmado via grep nos 3 arquivos `backend/main.py`
  existentes. Fronteira respeitada.
- **Module SDK** (`sdk/python/`) não foi auditado nesta revisão (fora do
  escopo de `core/backend/app/`) — candidato a uma revisão dedicada se o
  SDK crescer.
- **UI** (`core/frontend/src/`): não auditado componente-a-componente
  aqui (ver [`ui-api-cli-consolidation.md`](ui-api-cli-consolidation.md)).

## Gap conhecido, já corrigido

`modules/installed/hello_world/frontend/` só tinha `index.tsx` (não
compilado) — o contrato de Module Frontend exige JS/ESM compilado, o que
fazia o dynamic import falhar em runtime. Corrigido (ver
[`documentation-consolidation.md`](documentation-consolidation.md)).
`system_information_service` tem o mesmo padrão de `.tsx` não servível,
mas com UI mínima — registrado no [Technical Debt Registry](technical-debt-registry.md)
em vez de corrigido junto.
