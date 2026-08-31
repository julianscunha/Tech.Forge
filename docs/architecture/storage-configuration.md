---
title: Storage & Configuration Consolidation
category: governanca-setup
domain: [governanca-setup]
tags: [architecture, consolidation]
---

# TechForge Core — Storage & Configuration Consolidation

> Suíte completa (backend + CLI) validada como checkpoint ao final desta
> revisão. Ver também [`core-inventory.md`](core-inventory.md) e
> [`public-contracts.md`](public-contracts.md) (já documentam
> `StorageProvider`/`ModuleSecretStore` como contratos Stable).

## Platform Storage vs Module Storage (§15)

Ownership confirmado sem sobreposição:

- **Platform Storage** — DB compartilhado do Core (`techforge.db`, via
  `db.database`), dono exclusivo dos modelos em `models/` (Category,
  Module, Publisher, Notification, CatalogSourceConfig, etc.).
- **Module Storage** — `ModuleKVStoreRow` (Storage API do
  `ModuleExecutionContext.storage`), isolada por `module_id` — nenhum
  módulo lê/grava a linha de outro módulo (chave primária composta
  `module_id + key`, filtro obrigatório em toda query, confirmado em
  `module_runtime/context.py`).
- Nenhum módulo ou serviço do Core acessa a tabela `module_kv_store` de
  outro módulo diretamente — único ponto de acesso é a Storage API
  injetada no `ModuleExecutionContext`.

**Conclusão**: ownership claro, sem achado.

## Settings / Configuration (§16)

Grep completo em `core/backend/app/`, `launcher/`, `cli/` por URLs,
portas e paths literais:

| Local | Achado | Ação |
|---|---|---|
| `core/backend/app/**/*.py` | Nenhum hardcode fora de `core/settings.py` (único `127.0.0.1`/`localhost` do backend é a própria definição de `HOST`/`CORS_ORIGINS`) | Nenhuma — já consolidado |
| `launcher/techforge_launcher/__init__.py:47` | `BACKEND_HOST = "127.0.0.1"` — launcher é processo separado do backend (spawna o uvicorn), não importa `app.core.settings`; valor consistente com o default do backend | Nenhuma — não é duplicação de fonte de verdade, é o mesmo valor em dois processos que não compartilham import (aceitável, registrado como observação, não corrigido — mudar exigiria acoplar launcher a settings do backend, fora de escopo desta slice) |
| `cli/techforge_cli/commands/*.py` (11 arquivos) | **Achado real** — `_CORE`/`_BASE = "http://127.0.0.1:8000/api/v1"` duplicado literalmente em `catalog.py`, `config.py`, `diagnostics.py`, `docs.py`, `module_trust.py`, `release.py`, `runtime.py`, `security.py`, `services.py`, `storage.py`, e mais 5 ocorrências inline em `modules.py` | **Corrigido nesta slice** — ver abaixo |

### Correção aplicada: URL do Core duplicada no CLI

Criado `cli/techforge_cli/config.py`:

```python
CORE_BASE_URL = "http://127.0.0.1:8000/api/v1"
```

Os 11 arquivos de comando passaram a importar essa constante única em
vez de redeclarar o literal (`from techforge_cli.config import
CORE_BASE_URL as _CORE`, preservando o nome local onde já era usado
para não alterar o corpo das funções; em `modules.py`, onde `_CORE` já
denotava outra coisa — o path do `core/backend` adicionado ao
`sys.path` — a constante foi importada como `CORE_BASE_URL` e usada nas
5 f-strings que antes hardcodavam a URL). Correção puramente mecânica,
sem mudança de valor nem de comportamento — verificada com a suíte de
testes do CLI (130 passed) e um grep final confirmando que
`127.0.0.1:8000` só aparece mais em `cli/techforge_cli/config.py`
(definição) e `cli/tests/test_catalog_commands.py` (valor esperado
fixo num teste, não precisa importar a constante).

**Fora de escopo desta correção**: adicionar override via variável de
ambiente (ex: `TECHFORGE_CORE_URL`) — não pedido pela spec §16
("eliminar duplicação", não "adicionar configurabilidade nova") e seria
feature nova, não consolidação.

## Cache (§15)

`app/storage/cache.py::TTLCache` é a única implementação genérica de
cache com TTL. `app/package_manager/catalog_cache.py::CatalogCache` é
uma subclasse vazia, documentada explicitamente como "alias de
compatibilidade" da Fase 11 (pré-extração da lógica genérica na Fase
12) — não é uma segunda implementação, é o mesmo código reexportado sob
o nome antigo pra não quebrar `CatalogAggregator`/testes existentes.

**Conclusão**: única implementação real, sem duplicação.

## Logs (§15)

`observability/logging_setup.py` é o único ponto de configuração de
logging — a própria docstring do módulo declara "substitui
`logging.basicConfig`". Grep por `logging.basicConfig`,
`getLogger().setLevel` e `logging.config` em `core/backend/app/` não
retornou nenhuma outra ocorrência de configuração de logger fora deste
arquivo.

**Conclusão**: fonte única confirmada, sem achado.

## Secrets (§15/§16)

`security/secret_store.py` (`ModuleSecretStore`, backend `keyring`) é o
único caminho para persistir segredo. Único outro consumidor
encontrado é `module_runtime/context.py` (injeta o secret store no
`ModuleExecutionContext.secrets`) — nenhum serviço ou módulo grava
segredo em texto plano em coluna de banco, arquivo `.env` ou config
JSON.

**Conclusão**: fonte única confirmada, sem achado.

## Config files overlap (§16)

- `config/.env.example` (raiz do repo) — template versionado, sem
  valores reais; não sobrepõe `core/settings.py`, que já lê de
  `USER_DATA_DIR/config/.env` em runtime (arquivo real, fora do repo,
  confirmado pelo `.gitignore`).
- `config/techforge.db` (raiz, presente localmente) — dado de runtime,
  **não rastreado pelo git** (`git ls-files config/` só lista
  `.env.example`; `*.db` está no `.gitignore`) — não é um artefato de
  configuração do repositório, é estado local do desenvolvedor.
- Nenhum outro `config.yaml`/`settings.json` encontrado no repositório
  que duplique responsabilidade com `core/backend/app/core/settings.py`.

**Conclusão**: sem sobreposição de arquivos de configuração.

## Resumo — Checkpoint 1

| Área | Resultado |
|---|---|
| Platform vs Module Storage | Ownership claro, sem achado |
| Settings/Configuration | 1 achado real (URL duplicada em 11 arquivos do CLI) — **corrigido** nesta slice |
| Cache | Única implementação (`TTLCache`), sem achado |
| Logs | Fonte única de configuração, sem achado |
| Secrets | Fonte única (`ModuleSecretStore`/keyring), sem achado |
| Config files overlap | Sem sobreposição |

**Suíte completa (Checkpoint 1)**:
- Backend: `949 passed, 3 skipped` (`cd core/backend && pytest tests -q`) — mesmo número das slices anteriores, sem regressão.
- CLI: `130 passed` (`cd cli && pytest tests -q`) — primeira vez que a suíte do CLI é rodada nesta fase; sem regressão após a correção da URL duplicada.
