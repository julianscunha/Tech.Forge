---
title: UI API CLI Consolidation
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — UI + API + CLI Consolidation

> Inventário construído a partir do código real (`ast-grep outline` sobre
> `core/backend/app/api/routes/` e `cli/techforge_cli/`). Ver também
> [`core-inventory.md`](core-inventory.md), [`dependency-map.md`](dependency-map.md)
> (Achados 2 e 3, resolvidos/reavaliados aqui) e
> [`storage-configuration.md`](storage-configuration.md) (já
> consolidou `CORE_BASE_URL` no CLI).

## API routes inventory (§21-22)

23 arquivos de rota em `core/backend/app/api/routes/`, um por área.
Padrão de erro confirmado consistente: `HTTPException(status_code, detail)`
do FastAPI em todos os arquivos revisados, sem formato de erro customizado
divergente. Response models via Pydantic (`BaseModel`) em praticamente
todos os endpoints — os poucos que retornam `dict` cru (`platform_config.py`,
partes de `diagnostics.py`, `registry.py::rescan_registry`) são
deliberadamente schema-less (config bruta, ação de comando), não uma
inconsistência de padrão.

| Arquivo | Endpoints | Propósito |
|---|---|---|
| `categories.py` | 3 (list/create/get) | CRUD de categorias |
| `system.py` | 3 (version/storage/migrations) | Info de sistema |
| `module_quality.py` | 2 | Quality report + release readiness por módulo |
| `publishers.py` | 2 | Leitura de Publisher Registry |
| `platform_config.py` | 1 | Config bruta da plataforma (dict) |
| `module_config.py` | 3 | Config declarada por módulo (get/put/validate) |
| `services.py` | 6 | Service Registry: listar, capabilities, contrato, invoke |
| `platform.py` | 3 | Status/health/ready da plataforma |
| `module_assets.py` | 1 | Serve assets estáticos de `entry_frontend` |
| `security.py` | 2 | Agregação de trust/publisher sob `/security` (ver achado 3 abaixo) |
| `notifications.py` | 5 | CRUD de notificações |
| `modules.py` | 3 | CRUD básico de módulo no DB espelhado |
| `release.py` | 1 | Release readiness geral |
| `catalog.py` | 10 | Catálogo remoto, fontes, favoritos, updates |
| `module_verification.py` | 5 | Integrity/Trust/SBOM por módulo |
| `registry.py` | 6 | Registry in-memory: summary, list, journal, rescan, navegação |
| `dependencies.py` | 4 | Grafo/validação de dependências |
| `docs_context.py` | 1 | AI Context por id de contexto |
| `docs.py` | 9 | Developer Center: busca, contratos, compliance, AI export |
| `health.py` | 2 | Health check plataforma/módulo |
| `diagnostics.py` | 8 | Snapshot de diagnóstico, erros, execuções, recursos |
| `marketplace.py` | 13 | Ciclo de vida de pacote via API (install/remove/update/import/activate) |

Nenhum endpoint duplicado com o mesmo propósito e payload encontrado
entre arquivos — `security.py` é uma agregação declarada (docstring
própria admite: "Agrega dados já expostos por outras rotas... nenhuma
lógica de trust/publisher duplicada aqui"), não uma reimplementação.

## Achados corrigidos

### Achado 2 (de `core-inventory.md`) — `select()` direto em `Notification` fora do serviço

**Corrigido nesta slice.** `NotificationService` (`services/notifications.py`)
ganhou 2 métodos novos: `get(db, notification_id)` e
`exists_with_title(db, title, *, module_id=None, message=None)`. Os 3
call-sites que faziam `select()`/`func.count()` direto no model agora
chamam o serviço:

- `api/routes/docs.py::run_compliance_check` — dedupe por
  `title + module_id` → `NotificationService.exists_with_title(db, title, module_id=module_id)`.
  Import morto de `Notification` removido.
- `api/routes/notifications.py::mark_read` — re-fetch por id →
  `NotificationService.get(db, notification_id)`.
- `api/routes/marketplace.py::_notify_installation` — dedupe por
  `title + message` → `NotificationService.exists_with_title(db, title, message=message)`.

Mudança puramente mecânica (mesma query, mesmo comportamento) — nenhum
teste de comportamento de notificação mudou. Suíte completa continua
949 passed, 3 skipped.

### Achado 3 (de `dependency-map.md`) — `security.py` importa `list_modules_trust` de `module_verification.py`

**Reavaliado, não corrigido — mantido como débito técnico.** Investigação
mostrou que `list_modules_trust` chama `get_module_trust`
(`module_verification.py:102`), que por sua vez: consulta
`PublisherService`, verifica assinatura via `default_signature_provider`,
publica eventos (`security.signature_valid/invalid`,
`security.module_trust_changed`) e **muta um cache in-memory a nível de
módulo** (`_last_known_trust`, comentário próprio: "Fase 17 §36 — cache
in-memory do último Trust Level resolvido... não persiste entre restarts").

Extrair isso para um serviço é uma refatoração legítima, mas não é
"consolidação óbvia de baixo risco" — envolve mover estado mutável e
efeitos colaterais de eventos entre módulos, com risco real de mudar
comportamento sutil (timing de `_last_known_trust`, por exemplo, se a
extração alterar quando/quantas vezes a função é chamada). Mantido como
item de débito técnico no Technical Debt Registry, consistente com a classificação
original ("achado real, baixo risco, registrado como débito técnico") —
"baixo risco de existir", não "baixo risco de corrigir às pressas".

## CLI commands inventory (§23)

24 arquivos de comando em `cli/techforge_cli/` (+ `main.py` como
entrypoint Typer). `storage-configuration.md` já consolidou a URL do Core
(`CORE_BASE_URL`, `cli/techforge_cli/config.py`) — confirmado aqui que
todos os 11 arquivos que fazem chamada HTTP ao Core (`catalog.py`,
`config.py`, `diagnostics.py`, `docs.py`, `module_trust.py`,
`modules.py`, `release.py`, `runtime.py`, `security.py`, `services.py`,
`storage.py`) importam de lá, sem regressão.

| Arquivo | Comandos | Propósito |
|---|---|---|
| `version.py` | `version` | Versão da plataforma |
| `validate_module.py` | `validate` | Valida manifest de módulo local |
| `storage.py` | `storage`, `status` | Storage health via API |
| `module_trust.py` | `verify`, `integrity`, `integrity-check`, `publishers`, `publishers-list`, `publishers-show`, `trust`, `trust-publishers`, `generate-keypair`, `sign` | Trust/integrity/publisher via API |
| `diagnostics.py` | `diagnostics`, `health`, `errors`, `security`, `export` | Diagnóstico via API |
| `services.py` | `services`, `list`, `show`, `search`, `capabilities`, `contract`, `status` | Service Registry via API |
| `security.py` | `security`, `status` | Security overview via API |
| `release.py` | `release-check` | Readiness + testes locais |
| `create_module.py` | `create` | Scaffold de módulo novo (usa `templates/generator.py`) |
| `config.py` | `config`, `export` | Config da plataforma via API |
| `platform.py` | `start`, `stop`, `status`, `logs`, `dev`, `safe-mode` | Launcher (start/stop/status do processo) |
| `runtime.py` | `runtime`, `status`, `modules`, `module`, `initialize` | Runtime state via API |
| `repair.py` | `repair-check` | Diagnóstico de instalação local (sem API) |
| `package_module.py` | `package` | Empacota módulo em `.mod` (usa `packager/builder.py`) |
| `migrations.py` | `migrations`, `status`, `run` | Migração de DB local (import direto do backend, sem API) |
| `docs.py` | `docs`, `list`, `search`, `get`, `export-context` | Developer Center via API |
| `modules.py` | `modules`, `list`, `show`, `validate`, `activate`, `deactivate`, `remove`, `dependencies`, `dependents`, `validate-dependencies`, `graph`, `config`, `quality`, `diagnostics`, `release-check`, `config-validate` | Comando mais amplo — cobre módulo instalado ponta a ponta via API |
| `catalog.py` | `catalog`, `list`, `search`, `show`, `sources`, `build-index` | Catálogo remoto via API |

Nenhum comando duplicado com o mesmo propósito encontrado. Observação
sem correção (fora do escopo desta slice, não é URL): 6 arquivos
(`main.py`, `packager/builder.py`, `module_trust.py`, `version.py`,
`migrations.py`, `repair.py`/`modules.py`) ainda calculam
`_CORE_BACKEND`/`_CORE` como **path de disco** (pra inserir
`core/backend` no `sys.path` e importar código Python do backend
diretamente, não uma URL) com a mesma lógica repetida
(`Path(__file__).resolve().parents[N] / "core" / "backend"`, N variando
por profundidade do arquivo). É uma duplicação menor e de propósito
diferente da URL (já resolvida, ver `storage-configuration.md`) — candidato a um helper
único em `techforge_cli/config.py` (`resolve_core_backend_path()`) numa
limpeza futura; registrado como observação, não corrigido aqui por não
estar no escopo explícito desta slice (rotas/comandos redundantes) e
por não ser um comando/endpoint duplicado propriamente dito.

## Navigation / Module Workspace / Dashboard review (§24)

- **Navegação** (`components/layout/Sidebar.tsx`): confirmado — renderiza
  a árvore de navegação inteira a partir de `GET /api/v1/registry/navigation`
  (comentário próprio do arquivo: "The Core owns all navigation
  composition (§7.1 restriction)"). Nenhum item de menu hardcoded.
- **Module Workspace** (`components/modules/ModuleWorkspace.tsx`):
  confirmado, não alterado — mantém todas as abas de módulo montadas
  simultaneamente (uma `ModuleHost` por aba, escondida via `display:none`),
  independente de slot, preservando o design documentado nas Slices
  anteriores e no `ModuleTabStrip.tsx`.
- **Dashboard** (`pages/DashboardPage.tsx`): não duplica lógica de
  contagem do backend — `serviceCounts` é um `.filter().length` sobre o
  array já retornado por `GET /services` (agregação trivial de UI sobre
  dado já buscado, não uma reimplementação de regra de negócio do
  backend). Sem achado.

## Resumo

| Área | Resultado |
|---|---|
| API routes (§21-22) | 23 arquivos, ~90 endpoints, padrão de erro consistente, nenhum endpoint duplicado |
| Achado 2 (Notification direto) | **Corrigido** — 2 métodos novos no `NotificationService`, 3 call-sites migrados |
| Achado 3 (security→module_verification) | **Não corrigido** — envolve estado mutável + eventos, mantido como débito técnico no Technical Debt Registry |
| CLI commands (§23) | 24 arquivos, nenhum comando duplicado; observação menor sobre `_CORE_BACKEND` (path, não URL) repetido em 6 arquivos, registrada sem correção |
| Navigation/Workspace/Dashboard (§24) | Confirmados corretos, sem achado |

**Pytest**: suíte completa `949 passed, 3 skipped` após a correção do
Achado 2 — sem regressão. Suíte do CLI não re-executada nesta slice
(nenhum arquivo do CLI foi alterado; `storage-configuration.md` já confirmou 130 passed).
